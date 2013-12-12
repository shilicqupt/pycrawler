#!/usr/bin/env python
#!coding=utf-8
from Queue import Queue
from threading import Thread
import time
import json

class Content:

  def __init__(self):
    self.outputs = Queue()

    d = time.strftime('%y-%m-%d %H-%M',time.localtime())
    self.f = open( 'content.txt','a')
    self.f.write('[')
    
    t = Thread(target=self.run)
    t.setDaemon(True)
    t.start()

  def __del__(self):
    self.outputs.join()
    self.f.write(']')
    self.f.close()

  def write(self,url,dom,targets):
    result = {}
    result['url'] = url
    if dom != None:
      for t in targets:
        m = dom.xpath(t['xpath'])
        if len(m) >= 1:
          print m[0].text
          result[t['name']] = m[0].text
    output = json.dumps(result) + ',\n'
    self.outputs.put(output)

  def run(self):
    while True:
      output = self.outputs.get()
      self.f.write(output)
    self.f.close()
