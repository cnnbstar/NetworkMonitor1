#!/usr/bin/env python27
# -*- coding: utf-8 -*-


import urllib2
import cookielib

#创建cookie
cookie = cookielib.CookieJar()
handler=urllib2.HTTPCookieProcessor(cookie)

#通过handler来构建自定义opener
opener = urllib2.build_opener(handler)

#此处的open方法同urllib2的urlopen方法
request = urllib2.Request('http://www.baidu.com')
response = opener.open(request)
for item in cookie:
    print('%s = %s' % (item.name, item.value))
