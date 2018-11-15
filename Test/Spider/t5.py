#!/usr/bin/env python27
#coding:utf-8
import urllib, urllib2

#前半部分的链接(注意是http，不是https)
url_pre = 'http://www.baidu.com/s'

#GET参数
params = {}
params['wd'] = u'测试'.encode('utf-8')
url_params = urllib.urlencode(params)

#GET请求完整链接
url = '%s?%s' % (url_pre, url_params)

user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
headers = {'User-Agent':user_agent}
data = {'username':'Admin'}

#打开链接，获取响应
#response = urllib2.urlopen(url)
request1 = urllib2.Request(url)
request2 = urllib2.Request(url,headers=headers)
#request.add_data(data)
#request.add_header(headers)
response = urllib2.urlopen(request1)

#获取响应的html
html = response.read()

# #将html保存到文件
with open('test.txt', 'w') as f:
    f.write(html)
