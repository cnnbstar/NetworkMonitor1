#!/usr/bin/env python27
# -*- coding:utf-8 -*-

'''
WxMessage.py，基于Python2.7环境开发和测试，用于企业微信的信息发送
Class:

1.WxMessage -- 基于Python2.7环境开发和测试，用于企业微信的信息发送
    method:
    wxMessage()
        发送微信消息的主方法

    ....

2.
'''

try:
    import json
    import sys
    import ssl
    import time
    import os
    import logging
    import ConfigParser
    import copy
    import argparse
    from urllib2 import urlopen
    from urllib2 import Request
except ImportError:
    print 'ImportError'

__all__ = [
    "WxMessage"
]

class WxMessage():
    '''
    企业版微信API
    '''
    def __init__(self):
        '''
        初始化WxMessage
        读取同目录下'config.ini'配置常量信息
        :exception 读取config_wx.ini异常时，报：'ReadConfigFileError'
        '''
        config = ConfigParser.ConfigParser()
        try:
            self.mainPath = os.path.dirname(os.path.realpath(__file__)) #获取WxMessage.py执行时的绝对路径
            configFile = os.path.join(self.mainPath,'config_wx.ini')   #配置文件的绝对路径
            config.readfp(open(configFile, "rb"))
            self.configIniDict = dict(config._sections)
            for k in self.configIniDict:
                self.configIniDict[k] = dict(self.configIniDict[k])
        except IOError:
            print 'ReadConfigFileError'

    def getUsers(self,group):
        '''
        按组获取对应的用户List
        :param:组
        :return:userString，如18967892202,18967892188
        '''
        uDict = copy.deepcopy(self.configIniDict[group])
        del uDict['__name__']
        return ','.join(uDict.values()) #先从字典中抓取value值，形成List，最后将List转为String

    def __getToken(self,url, corpid, corpsecret):
        '''
        获取企业微信的Token
        :param url: 企业微信的API地址
        :param corpid: “比亚迪信息中心宁波信息部”企业微信的ID
        :param corpsecret: “监控报警”应用的SECRET
        :return:企业微信的Token
        '''
        token_url = '%s/cgi-bin/gettoken?corpid=%s&corpsecret=%s' % (url, corpid, corpsecret)
        token = json.loads(urlopen(token_url).read().decode())['access_token']
        return token

    def __getMessages(self,msg,user):
        '''
        获取消息对象集合
        :param msg: 消息的内容
        :param user:消息的接收人
        :return:消息对象集合
        '''
        AgentId = self.configIniDict['GLOBAL']['agentid']
        characterset = self.configIniDict['GLOBAL']['characterset']
        values = {
            "touser": user,            #消息接受对象
            "msgtype": 'text',
            "agentid": AgentId,        #应用“监控报警"的ID
            "text": {'content': msg},  #消息内容
            "safe": 0
        }
        msges=bytes(json.dumps(values)).decode(encoding=characterset)
        return msges

    def __sendMessage(self,toMsg,toUser):
        '''
        发送消息,并将消息对象在控制台打印和写入"log.txt"文本
        :param toMsg: 消息的内容
        :param toUser: 消息的接收人
        :exception 发送失败则抛异常："SendMsgError"
        '''
        Url = self.configIniDict['GLOBAL']['url']
        CorpID = self.configIniDict['GLOBAL']['corpid']
        Secret = self.configIniDict['GLOBAL']['secret']
        Error4SendMsg = self.configIniDict['ERROR']['error4sendmsg']

        ssl._create_default_https_context = ssl._create_unverified_context #全局取消证书验证
        token=self.__getToken(Url, CorpID, Secret) #应用的TOKEN
        send_url = '%s/cgi-bin/message/send?access_token=%s' % (Url,token)
        data = self.__getMessages(toMsg,toUser) #消息的对象及内容
        respone=urlopen(Request(url=send_url, data=data)).read()
        x = json.loads(respone.decode())['errcode']  #状态
        if x == 0:
            #日志记录
            self.__logMessage(toMsg,toUser)
        else:
            try:
                raise Exception(Error4SendMsg)  #消息发送失异常
            except Exception as e:
                print e

    def __sendMessage4All(self,toMsg):
        '''
        默认将发送消息给所有人@all
        :param toMsg: 消息的内容
        '''
        self.__sendMessage(toMsg,'@all')

    def __sendMessage4More(self,msgString,userString):
        '''
        按接收人集合，将消息发送给多个对象
        默认将李世达的手机号码转换为'li.shida@byd.com'，作为唯一ID发送给李世达
        :param msgString: 消息的内容,String类型
        :param userString: 消息的接收人，String类型，如'18967892202,18967892188'
        '''
        userList = userString.split(',') #转换为List，如['18967892202','18967892188']
        for u in userList:
            self.__sendMessage(msgString,u)

    def __logMessage(self,msg,user):
        '''
        消息对象的日志记录
        消息对象的控制台打印和文本记录
        :param msg:消息的内容
        :param user: 消息的接收人
        :exception 日志写入失败则抛异常："WriteLogError"
        '''
        #将李世达的邮箱转换为手机号码

        Error4WriteLog = self.configIniDict['ERROR']['error4writelog']
        logFileName = self.configIniDict['GLOBAL']['logfile']  #log.file.txt
        logFile = os.path.join(self.mainPath,logFileName)      #日志文件
        currentTime=time.strftime("%Y-%m-%d-%H:%M:%S",time.localtime(time.time()))
        #打印日志文件到控制台
        print currentTime+':'+user+':'+msg
        #写日志到日子文件
        try:
            with open(logFile,'a+') as f:
                f.write(currentTime+':'+user+':'+msg+'\n')
        except Exception:
            print "Error 1111"
            print Error4WriteLog  #日志写入异常

    def wxMessage(self,msgString,userString='@all'):
        '''
        微信发送消息的主程序
        使用方法如下：
            myMessage = wxMessage()
            myMessage.wxMessage('test message') #所有人
            myMessage.wxMessage('hello world','18967892202')
            myMessage.wxMessage('hello world','18967892202,18967892188')
        :param msgString:消息的内容，string类型
        :param userString:消息的接收人，string类型，如'18967892202,18967892188'
        '''
        ERROR4SEND = self.configIniDict['ERROR']['error4send']
        try:
            msg = msgString.strip('\'') or msgString.strip('\"')  #发送消息，去除'或者''
            if userString != '@all':
                user = userString.strip('\'') or userString.strip('\"')  #消息接收人,去除'或者''
                self.__sendMessage4More(msg,user)
            else :
                self.__sendMessage4All(msg)
        except Exception as e:
            print ERROR4SEND  #消息发送出错

def main():
    '''
    主函数
    将接收的参数除去'或者''，然后调用sendMessage
    :exception 主函数执行失败时抛异常：ExeMainError
    '''

    try:
        myMessage = WxMessage()  #初始化类

        #处理脚本方式获取的参数
        msg = sys.argv[1].strip('\'') or sys.argv[1].strip('\"')  #发送消息，取出'或者'' 支持"" 或者''
        users = sys.argv[-1].strip('\'') or sys.argv[-1].strip('\"')  #消息接收人,取出'或者'' 支持"" 或者''

        if len(sys.argv) == 3:
            myMessage.wxMessage(msg,users)
        elif len(sys.argv) == 2:
            myMessage.wxMessage(msg)
        else :
            print "WxMessage.py Usage:"
            print "Para1:Message Content,ex:'This is a Test Message' "
            print "Para2:Users Phone,ex:'18967892202,18967892188',None for @all "

    except Exception as e:
        print 'ExeMainError'  #主程序执行异常

if __name__ =='__main__':
    main()





