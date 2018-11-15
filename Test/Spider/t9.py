#!/usr/bin/env python27
# -*- coding: utf-8 -*-

import ssl
import urllib2
import urllib
ssl._create_default_https_context = ssl._create_unverified_context

user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
headers = {'User-Agent':user_agent}
values = {'usernameInput':'administrator','passwordInput':'HAYYY404'}
data = urllib.urlencode(values)
url = "https://10.15.0.106"


req = urllib2.Request(url,data=data,headers=headers,unverifiable=True)
data = urllib2.urlopen(req).read()
print(data)