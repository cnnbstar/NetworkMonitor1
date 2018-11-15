#!/usr/bin/env python27
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup

url = "http://res.byd.cn/LocalWebSysC550/login.action"
UA = "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.13 Safari/537.36"

header = { "User-Agent" : UA,
           "Referer": "http://res.byd.cn/LocalWebSysC550/login.action"
           }

admin_session = requests.Session()
# f = admin_session.get(url,headers=header)

# soup = BeautifulSoup(f.content,"html.parser")
# once = soup.find('input',{'name':'once'})['value']

postData = {
        'username':'admin',
        'password':'123'
    }


admin_session.post(url,
                  data = postData,
                  headers = header)

page_NB_UPS1_AssMsg = admin_session.get('http://res.byd.cn/LocalWebSysC550/showAssMsg.action?upsName=%E5%AE%81%E6%B3%A2ups1&rtuId=356&intType=1',headers=header)
page_NB_UPS2_AssMsg = admin_session.get('http://res.byd.cn/LocalWebSysC550/showAssMsg.action?upsName=%E5%AE%81%E6%B3%A2ups2&rtuId=361&intType=1',headers=header)


print(page_NB_UPS1_AssMsg.content.decode('utf-8'))
print(page_NB_UPS2_AssMsg.content.decode('utf-8'))