#!/usr/bin/env python27
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup

def login():
    header = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding':  'gzip, deflate, sdch',
        'Accept-Language':  'zh-CN,zh;q=0.8',
        'Cache-Control':  'max-age=0',
        'Connection':  'keep-alive',
        'User-Agent':  'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.235'
    }
    session = requests.session()
    '''
    <div class="r_user_inp">
        <input id="username" name="username" class="r_user_inpbox" type="text" size="40" /></div>
    </div>
    '''
    res = session.get('http://res.byd.cn/LocalWebSysC550/loginOut.action',headers = header).content


    '''
    Test
    '''
    myLogin =  BeautifulSoup(res, "html.parser").findAll('input',attrs={'class':'r_user_inpbox'})
    print myLogin[1].string

    login_data = {
        'username':'admin',
        'password':'123'
    }
    session.post('http://res.byd.cn/LocalWebSysC550/login.action',data = login_data,headers = header)
    res = session.get('http://res.byd.cn/LocalWebSysC550/ShowUpsDevice.action')
    print res.cookies
    #print(res.text)

if __name__ == '__main__':
    login()