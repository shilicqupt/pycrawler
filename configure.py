#!/usr/bin/env python
#!coding=utf-8

#名字为config的dict会被当做当前配置文件

config = {
    # douban city
    'douban' : {
        'seeds':[{'url':'http://beijing.douban.com/','parsed':False,'depth':0}, 
                    {'url':'http://www.douban.com/location/world/','parsed':False,'depth':0},
                    {'url':'http://shanghai.douban.com/','parsed':False,'depth':0},
          ],
        'depth':1,
        #所有符合规则的item都会被抓取，按照or模式匹配
        'item_patterns':[r'http://www.douban.com/event/\d+/', r'http://www.douban.com/location/\S+/'],
        #翻页不需要计算depth，看见就抓
        'page_patterns':[r'http://search.360buy.com/Search?keyword=%C0%F1%CE%EF&area=1&qr=%40%23%24%25&page=\d+$'],
        #除了达到指定的depth，url匹配到这里也会停止抓取
        'stop_patterns':[r'http://search.360buy.com/Search?keyword=%C0%F1%CE%EF&area=1&qr=%40%23%24%25&page=10$'],
        #哪些字段需要被抓取下来
        'encoding':'gbk',
        'thread_number':5,
        'max_number':5000
    },
    'douban' : {
        'seeds':[{'url':'http://beijing.douban.com/','parsed':False,'depth':0}, 
                    {'url':'http://www.douban.com/location/world/','parsed':False,'depth':0},
                    {'url':'http://shanghai.douban.com/','parsed':False,'depth':0},
          ],
        'depth':1,
        #所有符合规则的item都会被抓取，按照or模式匹配
        'item_patterns':[r'http://www.douban.com/event/\d+/', r'http://www.douban.com/location/\S+/'],
        #翻页不需要计算depth，看见就抓
        'page_patterns':[r'http://search.360buy.com/Search?keyword=%C0%F1%CE%EF&area=1&qr=%40%23%24%25&page=\d+$'],
        #除了达到指定的depth，url匹配到这里也会停止抓取
        'stop_patterns':[r'http://search.360buy.com/Search?keyword=%C0%F1%CE%EF&area=1&qr=%40%23%24%25&page=10$'],
        #哪些字段需要被抓取下来
        'encoding':'gbk',
        'thread_number':5,
        'max_number':5000
    }
}
