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

# 自定义模块
from content import Content
from logger import Logger 
from configure import config

class Fetcher:
  # 初始化数据
  def __init__(self,cfg_name):
    self.lock = Lock()
    self.links = Queue()
    self.retry = Queue()
    self.fail = Queue()
    self.exist = set()
    self.complate = 0
    self.running = 0
    self.db = redis.StrictRedis(host='localhost', port=6379, db=0)

    # 配置信息
    self.item_patterns = config[cfg_name]['item_patterns']
    self.page_patterns = config[cfg_name]['page_patterns']
    self.stop_patterns = config[cfg_name]['stop_patterns']
    self.depth = config[cfg_name]['depth']
    self.seeds = config[cfg_name]['seeds']
    self.encoding = config[cfg_name]['encoding']
    self.thread_number = config[cfg_name]['thread_number']
    self.max_number = config[cfg_name]['max_number']

  #解构的时候不必等待队列完成
  def __del__(self):
    #self.links.join()
    pass

  #启动线程
  def start(self):
    for i in range(self.thread_number):
      t = Thread(target = self.run)
      t.setDaemon(True)
      t.start()

    for seed in self.seeds:
      self.push(seed)

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
      if self.retry.empty():
        link = self.links.get()
      else:
        link = self.retry.get()

      try:
        response = self.openUrl(link['url'])
        html = response.read()
        #给网页重新编码，默认lxml只能处理utf-8
        #if self.encoding != 'utf-8':
        #  html = html.decode(self.encoding,'ignore').encode('utf-8')
        self.extractContent(html,link['url'])
        self.extractLinks(link['url'],html,link['depth'])
        with self.lock:
          self.complate += 1
          self.exist.add(link['url'])
      except:
        if link.has_key('retry'):
          if link['retry'] >=3:
            self.fail.put(link)
          else:
            link['retry'] += 1
            self.retry.put(link)
        else:
          link['retry'] = 1
          self.retry.put(link)
        print 'Could not open %s' % link['url']
        print 'Error Info : %s ' % sys.exc_info()[1]
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
    for p in self.item_patterns:
      p = re.compile(p)
      if p.findall(url):
        match = True
    return match

  #判断链接是不是page，是的话就不需要增加depth
  def isPage(self,url):
    match = False
    for p in self.page_patterns:
      p = re.compile(p)
      if p.findall(url):
        match = True
    return match

  #判断链接是不是停止链接
  def isStop(self,url):
    match = False
    for p in self.stop_patterns:
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
    req = urllib2.Request(
            url = url,
            data = None,
            headers = headers)
    c = urllib2.urlopen(req)
    return c

  #从某个网页解析出所以符合条件的下一层链接
  def extractLinks(self,referer,html,depth):
    soup = BeautifulSoup(html)
    tags = soup('a')
    #从soup中获得所有的链接数据进行解析
    for l in tags:
      if ('href' in dict(l.attrs)):
        url = urljoin(referer,l['href'])
        url = url.split('#')[0]
        if (not self.isExist(url) 
            and self.isItem(url)
            ):
          #如果当前链接是翻页链接，则不需要增加其depth
          if self.isPage(url):
            depth = depth+1
          link = {'url':'%s' % url,'parsed':False,'depth':depth}
          #推送数据给任务队列
          self.push(link)
          #添加到已获取的链接集合中
          self.exist.add(url)

  #从某个网页解析出需要的内容 
  def extractContent(self,html,url):
    thread_name = current_thread().name
    t = time.strftime('%y-%m-%d %H:%M:%S',time.localtime())
    Logger.write('[%s][%s][finish = %s][fail = %s] : %s' % (
        t,thread_name,self.complate,self.fail.qsize(),url
        ))
    soup = BeautifulSoup(html)
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

  def printFinishLog(self):
    print 'finish items: %s' % self.complate
    print 'fail items : %s , list below :' % self.fail.qsize()
    while(not self.fail.empty()):
      print self.fail.get()['url']
    print ''
