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

import redis
import json
from mysqlclient import Connection

class Fetcher:
    def __init__(self):
        self.links = Queue()
        self.retry = Queue()
        self.fail = Queue()
        self.exist = set()
        self.res = []
        self.complate = 0
        self.running = 0
        #self.db = Connection(host="localhost", user="root", password="5238626", database="douban")
        self.db = redis.StrictRedis(host='localhost', port=6379, db=0)

    def __del__(self):
        pass

    def start(self):
        for i in range(5):
            t = Thread(target = self.run)
            t.setDaemon(True)
            t.start()    
    
        urls = ['http://www.douban.com/location/world/']
        for url in urls:
            link = {'url':'%s' % url,'parsed':False}
        
            self.push(link)       
   
    def push(self,link):
        if link['url'] not in self.exist:
            self.links.put(link)

    def isExist(self, url):
        if url in self.exist:
            return True
        return False

    def isItem(self,url):
        match = False
        item_patterns = [r'http://www.douban.com/event/\d+/$', r'http://www.douban.com/location/\S+/']
        for p in item_patterns:
            p = re.compile(p)
            if p.findall(url):
                match = True
        return match

    def openUrl(self, url):
        c = None
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
            c = urllib2.urlopen(req)
        except:
            pass
        return c

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
        self.exist.add(url)

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
    def run(self):
        while True:
            try:
                link = self.links.get()
                response = self.openUrl(link['url'])
                html = response.read()
                if self.encoding != 'utf-8':
                    html = html.decode(self.encoding,'ignore').encode('utf-8')
                soup = BeautifulSoup(html)
                self.extractContent(soup, link['url'])
                self.extractLinks(soup)
                self.exist.add(link['url'])
            except:
                continue

        self.links.task_done()

    '''def start(self):
        urls = ['http://www.douban.com/location/world/']
        for url in urls:
            link = {'url':'%s' % url,'parsed':False}
        
            self.links.put(link)
        while True:
            link = self.links.get()
            html = self.openUrl(link['url'])
            self.extractLinks(link['url'], html)
            
            self.exist.add(link['url'])
            #if len(self.exist) > 100:
            #    break
        
        self.links.task_done()'''
        
if __name__ == "__main__":
    fetcher = Fetcher()
    fetcher.start()
