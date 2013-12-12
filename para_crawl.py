#!/usr/bin/env python
#!coding=utf-8

# 系统模块
from BeautifulSoup import BeautifulSoup
from lxml import etree
from Queue import Queue
from threading import Lock,Thread,current_thread
from urlparse import urljoin

import chardet
import urllib2
import time
import re
import sys
import json
import redis

class Fetcher:
  # 初始化数据
  def __init__(self):
    self.lock = Lock()
    self.links = Queue()
    self.retry = Queue()
    self.fail = Queue()
    self.exist = set()
    self.complate = 0
    self.running = 0
    self.thread_number = 1
    self.max_number = 100000
    self.db = redis.StrictRedis(host='localhost', port=6379, db=0)

  #解构的时候不必等待队列完成
  def __del__(self):
    #self.links.join()
    pass

  #启动线程
  def start(self):
    urls = ['http://www.baidu.com/', 'http://www.taobao.com/']
    for url in urls:
        link = {'url':'%s' % url,'parsed':False}
        self.push(link)
    
    for i in range(self.thread_number):
      t = Thread(target = self.run)
      t.setDaemon(True)
      t.start()

  #终止所有线程
  def stop(self):
    pass

  #增加任务数据
  def push(self,link):
    if link['url'] not in self.exist:
      self.links.put(link)

  #获得当前运行的线程数
  def get_running_count(self):
    return self.running

  #多线程主函数
  def run(self):
    with self.lock:
      self.running += 1
    while True:
      if self.complate >= self.max_number:
        break
      link = {}
      link = self.links.get()

      try:
        response = self.openUrl(link['url'])
        html = response.read()
        print '**************'
        print html
        #给网页重新编码，默认lxml只能处理utf-8
        if self.encoding != 'utf-8':
          html = html.decode(self.encoding,'ignore').encode('utf-8')
        soup = BeautifulSoup(html)
        self.extractContent(soup,link['url'])
        self.extractLinks(soup)
        with self.lock:
          self.complate += 1
          self.exist.add(link['url'])
      except:
        continue
      self.links.task_done()
    self.running -= 1

  #判断链接是否已经被爬取过
  def isExist(self,url):
    if url in self.exist:
      return True
    return False

  #判断链接是不是一个item
  def isItem(self,url):
        match = False
        item_patterns = [r'http://www.douban.com/event/\d+/$', r'http://www.douban.com/location/\S+/']
        for p in item_patterns:
            p = re.compile(p)
            if p.findall(url):
                match = True
        return match

  #打开url链接，返回数据流
  def openUrl(self,url):
    headers = {
            'User-Agent':'Mozilla/5.0 \
                (Macintosh; Intel Mac OS X 10_6_8) \
                AppleWebKit/536.5 (KHTML, like Gecko) \
                Chrome/19.0.1084.56 Safari/536.5'
    }
    try:
      req = urllib2.Request(
        url = url,
        data = None,
        headers = headers)
      print url
      c = urllib2.urlopen(url)
      print type(c)
      print c.read()
    except:
      pass
    return c

  def extractLinks(self, soup):
        if soup == None:
            return
        #soup = BeautifulSoup(html)
        #self.extractContent(soup, url)
        tags = soup('a')
        for l in tags:
            if ('href' in dict(l.attrs)):
                url = l['href']
                url = url.split('#')[0]
                if (not self.isExist(url)  and self.isItem(url)):
                    link = {'url':'%s' %url,'parsed':False}
                    self.push(link)

  #从某个网页解析出需要的内容 
  def extractContent(self, soup, url):
        result ={}
        try:
            h1 = soup.find('h1')
            if h1 != None:
                name = h1.string
                print name
                result['title'] = name
                #self.db.set(url, str(name))
          
            desc = soup.find(id="edesc_f")
            if desc != None:
                desc = str(desc)
                #self.db.hset(url, 'content', desc)
                result['content'] = desc
        
            region = soup.find(itemprop="region")
            if region != None:
                #self.db.hset(url, "region", region.string)
                result['region'] = region.string
            locality = soup.find(itemprop="locality")
            if locality != None:
                #self.db.hset(url, "locality", locality.string)
                result['locality'] = locality.string
            street_address = soup.find(itemprop="street_address")
            if street_address != None:
                result['street_address'] = street_address.string
            eventType = soup.find(itemprop="eventType")
            if eventType != None:
                result['eventType'] = eventType.string
            organize = soup.find(itemprop="name")
            if orgnize != None:
                result['organiz'] = organiz.string
        except:
            pass
        if len(result) > 0:
            #print json.dumps(result)
            res = json.dumps(result)
            self.db.set(url, res)


if __name__ == "__main__":
    fetcher = Fetcher()
    fetcher.start()
