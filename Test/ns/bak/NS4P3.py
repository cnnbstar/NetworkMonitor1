#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#import requests
from urllib.request import Request,urlopen
import json


dazi_dict = {
    #'sender':'NS',
    'touser':'li.shida',
    #'subject':'API Test',
    'content':'Hello,NS',
    'secret':'@superman@ironman',
    'noticetype':'PC|WX',
    'import':'false',
    #'pccmd':'false'
}

dazi_json = json.dumps(dazi_dict)

myHearders = {'Content-Type':'application/json'}
myUrl = 'http://ns.nbbyd.com/NotificationSystem/send'
request = Request(url=myUrl,headers=myHearders,data=dazi_json)
response = urlopen(request)

myResult = json.loads(response.read())
print myResult
'''
{
    u'ns_errmsg': u'ok',
    u'invaliduser': u'',
    u'invalidgroup': u'',
    u'sms': None,
    u'email': None,
    u'wx': {u'invaliduser': u'', u'errmsg': u'ok'},
    u'pc': {u'invaliduser': u'', u'errmsg': u'ok', u'offlineuser': u''},
}


'''

print myResult['ns_errmsg']
#r1=Request.post('http://ns.nbbyd.com/NotificationSystem/send',data=dazi_json)
#print(r1.text)
#print(r1.status_code)
