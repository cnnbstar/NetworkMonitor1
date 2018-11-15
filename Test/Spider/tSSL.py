#!/usr/bin/env python27
# -*- coding: utf-8 -*-

'''
爬HTTPS网站
'''
import urllib2
import ssl



context = ssl._create_unverified_context()
url = 'https://www.12306.cn/mormhweb/'
request = urllib2.Request(url)
response = urllib2.urlopen(url = request, context=context)
print (response.read().decode('utf-8'))


