#!/usr/bin/env python27
# -*- coding: utf-8 -*-

try:
    import os.path
    from pysnmp.hlapi import *
    import json
    import sys
    import ssl
    import time
    import os
    import logging
    import ConfigParser
    import copy
    import argparse
    import datetime
    from urllib2 import urlopen
    from urllib2 import Request
    from BydSpider import BydUps,BydWeather
    from BydSnmp import BlHw,BlDell,BlOthers,FhHw

except ImportError:
    print 'ImportError'

__all__ = [
    "BydMonitor","WxMessage"
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

    def __getMail4LiShida(self):
        '''
        获取李世达的企业微信ID：li.shida
        :return:固定字符串'li.shida@byd.com'
        '''
        return 'li.shida@byd.com'

    def __getPhhone4Lishida(self):
        '''
        获取李世达的手机号码
        :return:固定字符串'18967892202'
        '''
        return '18967892202'

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
            if u == '18967892202':
                self.__sendMessage(msgString,self.__getMail4LiShida())
            else:
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
        if user==self.__getMail4LiShida():
            user=self.__getPhhone4Lishida()
        currentTime=time.strftime("%Y-%m-%d-%H:%M:%S",time.localtime(time.time()))
        #打印日志文件到控制台
        print currentTime+':'+user+':'+msg
        #写日志到日子文件
        try:
            with open(logFile,'a+') as f:
                f.write(currentTime+':'+user+':'+msg+'\n')
        except Exception:
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

class BydMonitor():
    def __init__(self):
        self.myWxMessage = WxMessage()
        self.myBydUps = BydUps()
        self.myBydWeather = BydWeather()
        self.myBlHw = BlHw()
        self.myBlDell = BlDell()
        self.myBlOther = BlOthers()
        self.myFhHw = FhHw()

    def printStatus(self,deviceStatResult):
        '''
        打印设备状态报表（字符串形式）
        :param deviceItemsDict:设备状态的列表 从getHWXX返回而来
        :return:以字符串形式打印该设备状态状态
        '''
        resultStr = ''
        hostname = deviceStatResult[0]  #主机名
        status = deviceStatResult[2]    #主机状态的数据字典
        print '\n***'+hostname+'***'
        for key in sorted(status):
            resultStr += key+'：'+status[key]+'\n'
        return resultStr

    def getStatusByName(self,name):
        '''
        按IP地址或者主机名来匹配对应的主机
        :param name:按IP地址或者主机名
        :return:以字符串形式打印该设备状态状态
        '''
        #FH_HW
        if cmp(name,'10.15.255.253') ==0 or cmp(name,'fh-lj') ==0:
            return self.printStatus(self.myFhHw.getHW_FH_LJ_1())
        elif cmp(name,'10.15.255.250') ==0 or cmp(name,'fh-router') ==0:
            return self.printStatus(self.myFhHw.getHW_FH_Router())
        elif cmp(name,'10.15.253.252') ==0 or cmp(name,'fh-ac2') ==0:
            return self.printStatus(self.myFhHw.getHW_FH_AC2())
        elif cmp(name,'10.15.253.251') ==0 or cmp(name,'fh-ac1') ==0:
            return self.printStatus(self.myFhHw.getHW_FH_AC1())
        elif cmp(name,'10.15.255.254') ==0 or cmp(name,'fh-agg') ==0:
            return self.printStatus(self.myFhHw.getHW_FH_AGG())
        elif cmp(name,'10.15.255.11') ==0 or cmp(name,'fh-1#s1') ==0:
            return self.printStatus(self.myFhHw.getHW_FH_1_S1())
        elif cmp(name,'10.15.255.12') ==0 or cmp(name,'fh-1#s2') ==0:
            return self.printStatus(self.myFhHw.getHW_FH_1_S2())
        elif cmp(name,'10.15.255.13') ==0 or cmp(name,'fh-1#s3') ==0:
            return self.printStatus(self.myFhHw.getHW_FH_1_S3())
        elif cmp(name,'10.15.255.14') ==0 or cmp(name,'fh-1#s4') ==0:
            return self.printStatus(self.myFhHw.getHW_FH_1_S4())
        elif cmp(name,'10.15.255.15') ==0 or cmp(name,'fh-1#s5') ==0:
            return self.printStatus(self.myFhHw.getHW_FH_1_S5())
        elif cmp(name,'10.15.255.31') ==0 or cmp(name,'fh-3#s1') ==0:
            return self.printStatus(self.myFhHw.getHW_FH_3_S1())
        elif cmp(name,'10.15.255.32') ==0 or cmp(name,'fh-3#s2') ==0:
            return self.printStatus(self.myFhHw.getHW_FH_3_S2())
        elif cmp(name,'10.15.255.16') ==0 or cmp(name,'fh-zhzfang') ==0:
            return self.printStatus(self.myFhHw.getHW_FH_ZHZFang())
        elif cmp(name,'10.15.255.113') ==0 or cmp(name,'fh-bating') ==0:
            return self.printStatus(self.myFhHw.getHW_FH_BATing())
        elif cmp(name,'10.15.255.111') ==0 or cmp(name,'fh-stang') ==0:
            return self.printStatus(self.myFhHw.getHW_FH_STang())
        elif cmp(name,'10.15.255.112') ==0 or cmp(name,'fh-sshe') ==0:
            return self.printStatus(self.myFhHw.getHW_FH_SShe())
        #BL_HW
        elif cmp(name,'10.15.0.254') ==0 or cmp(name,'core') ==0:
            return self.printStatus(self.myBlHw.getHW_BL_CORE())
        elif cmp(name,'10.15.2.254') ==0 or cmp(name,'agg') ==0:
            return self.printStatus(self.myBlHw.getHW_BL_AGG())
        elif cmp(name,'10.15.0.63') ==0 or cmp(name,'pub3f') ==0:
            return self.printStatus(self.myBlHw.getHW_BL_PUB3F())
        elif cmp(name,'10.15.0.61') ==0 or cmp(name,'subfab-1') ==0:
            return self.printStatus(self.myBlHw.getHW_BL_SUBFAB_1())
        elif cmp(name,'10.15.0.62') ==0 or cmp(name,'subfab-2') ==0:
            return self.printStatus(self.myBlHw.getHW_BL_SUBFAB_2())
        elif cmp(name,'10.15.0.60') ==0 or cmp(name,'pub1f') ==0:
            return self.printStatus(self.myBlHw.getHW_BL_PUB1F())
        elif cmp(name,'10.15.2.41') ==0 or cmp(name,'off4f') ==0:
            return self.printStatus(self.myBlHw.getHW_BL_OFF4F())
        elif cmp(name,'10.15.2.23') ==0 or cmp(name,'off2f-3') ==0:
            return self.printStatus(self.myBlHw.getHW_BL_OFF2F_3())
        elif cmp(name,'10.15.2.22') ==0 or cmp(name,'off2f-2') ==0:
            return self.printStatus(self.myBlHw.getHW_BL_OFF2F_2())
        elif cmp(name,'10.15.2.21') ==0 or cmp(name,'off2f-1') ==0:
            return self.printStatus(self.myBlHw.getHW_BL_OFF2F_1())
        elif cmp(name,'10.15.2.13') ==0 or cmp(name,'off1f-3') ==0:
            return self.printStatus(self.myBlHw.getHW_BL_OFF1F_3())
        elif cmp(name,'10.15.2.12') ==0 or cmp(name,'off1f-2') ==0:
            return self.printStatus(self.myBlHw.getHW_BL_OFF1F_2())
        elif cmp(name,'10.15.2.11') ==0 or cmp(name,'off1f-1') ==0:
            return self.printStatus(self.myBlHw.getHW_BL_OFF1F_1())
        elif cmp(name,'10.15.2.44') ==0 or cmp(name,'damen') ==0:
            return self.printStatus(self.myBlHw.getHW_BL_DaMen())
        elif cmp(name,'10.15.2.42') ==0 or cmp(name,'puboff') ==0:
            return self.printStatus(self.myBlHw.getHW_BL_PUBOFF())
        elif cmp(name,'10.15.2.49') ==0 or cmp(name,'off4ftd') ==0:
            return self.printStatus(self.myBlHw.getHW_BL_OFF4FTD())
        elif cmp(name,'10.15.2.43') ==0 or cmp(name,'cub3f') ==0:
            return self.printStatus(self.myBlHw.getHW_BL_CUB3F())
        elif cmp(name,'10.15.0.252') ==0 or cmp(name,'lj-1') ==0:
            return self.printStatus(self.myBlHw.getHW_BL_LJ_1())
        elif cmp(name,'10.15.0.253') ==0 or cmp(name,'lj-2') ==0:
            return self.printStatus(self.myBlHw.getHW_BL_LJ_2())
        #BL_Dell
        elif cmp(name,'10.15.0.200') ==0 or cmp(name,'cmc') ==0:
             return self.printStatus(self.myBlDell.getDellCMC())
        #BL_Others
        elif cmp(name,'10.15.1.253') ==0 or cmp(name,'sg') ==0:
            return self.printStatus(self.myBlOther.getSangforSG())
        elif cmp(name,'10.15.1.251') ==0 or cmp(name,'td') ==0:
            return self.printStatus(self.myBlOther.get360TD())
        #BYD_UPS
        elif cmp(name,'ups1') ==0:
            return self.myBydUps.getUpsInfo('ups1')
        elif cmp(name,'ups2') ==0:
            return self.myBydUps.getUpsInfo('ups2')
        #Help
        elif cmp(name,'help') ==0:
            helpContent='奉化:fh-agg,fh-ac1,fh-ac2,fh-router\n'+\
                        '北仑:core,agg,cmc,sg,td,ups1,ups2'
            return helpContent
        else:
            return 'NONE'

    def checkAllDeviceStatus(self):
        '''
        TODO:陆续完善
        检查华为设备全局状态，当全局状态不为'ok'则发送微信通知
        :return:发送微信告警信息
        '''
        #blWeather = WxWeather.WxWeather().get_2DaysWeathers()
        #nowTime=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        #self.myWxMessage.wxMessage(nowTime+' 机房温度:'+self.getDellCMC()[2]['1.环境温度']+'\n')
        self.myWxMessage.wxMessage(
            #'***北仑天气***\n'+self.myBydWeather.get2Days()+'\n'+\
            '电脑机房温度:'+self.myBlDell.getDellCMC()[2]['1.环境温度']+'\n'+ \
            '一楼机柜温度:'+self.myBydUps.getUpsBoxTemp('ups1')+'\n'+ \
            '一楼机柜湿度:'+self.myBydUps.getUpsBoxHumidity('ups1')
        )


        #HW_FH_LJ_1
        if cmp(self.myFhHw.getHW_FH_LJ_1()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.myFhHw.getHW_FH_LJ_1()[0]+'：'+self.myFhHw.getHW_FH_LJ_1()[1]+'\n'+self.printStatus(self.myFhHw.getHW_FH_LJ_1()))

        #HW_FH_Router
        if cmp(self.myFhHw.getHW_FH_Router()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.myFhHw.getHW_FH_Router()[0]+'：'+self.myFhHw.getHW_FH_Router()[1]+'\n'+self.printStatus(self.myFhHw.getHW_FH_Router()))

        #HW_FH_AC2
        if cmp(self.myFhHw.getHW_FH_AC2()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.myFhHw.getHW_FH_AC2()[0]+'：'+self.myFhHw.getHW_FH_AC2()[1]+'\n'+self.printStatus(self.myFhHw.getHW_FH_AC2()))

        #HW_FH_AC1
        if cmp(self.myFhHw.getHW_FH_AC1()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.myFhHw.getHW_FH_AC1()[0]+'：'+self.myFhHw.getHW_FH_AC1()[1]+'\n'+self.printStatus(self.myFhHw.getHW_FH_AC1()))

        #HW_FH_AGG
        if cmp(self.myFhHw.getHW_FH_AGG()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.myFhHw.getHW_FH_AGG()[0]+'：'+self.myFhHw.getHW_FH_AGG()[1]+'\n'+self.printStatus(self.myFhHw.getHW_FH_AGG()))

        #HW_FH_1_S1
        if cmp(self.myFhHw.getHW_FH_1_S1()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.myFhHw.getHW_FH_1_S1()[0]+'：'+self.myFhHw.getHW_FH_1_S1()[1]+'\n'+self.printStatus(self.myFhHw.getHW_FH_1_S1()))

        #HW_FH_1_S2
        if cmp(self.myFhHw.getHW_FH_1_S2()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.myFhHw.getHW_FH_1_S2()[0]+'：'+self.myFhHw.getHW_FH_1_S2()[1]+'\n'+self.printStatus(self.myFhHw.getHW_FH_1_S2()))

        #HW_FH_1_S3
        if cmp(self.myFhHw.getHW_FH_1_S3()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.myFhHw.getHW_FH_1_S3()[0]+'：'+self.myFhHw.getHW_FH_1_S3()[1]+'\n'+self.printStatus(self.myFhHw.getHW_FH_1_S3()))

        #HW_FH_1_S4
        if cmp(self.myFhHw.getHW_FH_1_S4()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.myFhHw.getHW_FH_1_S4()[0]+'：'+self.myFhHw.getHW_FH_1_S4()[1]+'\n'+self.printStatus(self.myFhHw.getHW_FH_1_S4()))

        #HW_FH_1_S5
        if cmp(self.myFhHw.getHW_FH_1_S5()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.myFhHw.getHW_FH_1_S5()[0]+'：'+self.myFhHw.getHW_FH_1_S5()[1]+'\n'+self.printStatus(self.myFhHw.getHW_FH_1_S5()))

        #HW_FH_1_S1
        if cmp(self.myFhHw.getHW_FH_3_S1()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.myFhHw.getHW_FH_3_S1()[0]+'：'+self.myFhHw.getHW_FH_3_S1()[1]+'\n'+self.printStatus(self.myFhHw.getHW_FH_3_S1()))

        #HW_FH_3_S2
        if cmp(self.myFhHw.getHW_FH_3_S2()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.myFhHw.getHW_FH_3_S2()[0]+'：'+self.myFhHw.getHW_FH_3_S2()[1]+'\n'+self.printStatus(self.myFhHw.getHW_FH_3_S2()))

        #HW_FH_ZHZFang 综合站房
        if cmp(self.myFhHw.getHW_FH_ZHZFang()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.myFhHw.getHW_FH_ZHZFang()[0]+'：'+self.myFhHw.getHW_FH_ZHZFang()[1]+'\n'+self.printStatus(self.myFhHw.getHW_FH_ZHZFang()))

        #HW_FH_1_BATing 保安亭
        if cmp(self.myFhHw.getHW_FH_BATing()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.myFhHw.getHW_FH_BATing()[0]+'：'+self.myFhHw.getHW_FH_BATing()[1]+'\n'+self.printStatus(self.myFhHw.getHW_FH_BATing()))

        #HW_FH_1_STang 食堂
        if cmp(self.myFhHw.getHW_FH_STang()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.myFhHw.getHW_FH_STang()[0]+'：'+self.myFhHw.getHW_FH_STang()[1]+'\n'+self.printStatus(self.myFhHw.getHW_FH_STang()))

        #HW_FH_1_SShe 宿舍
        if cmp(self.myFhHw.getHW_FH_SShe()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.myFhHw.getHW_FH_SShe()[0]+'：'+self.myFhHw.getHW_FH_SShe()[1]+'\n'+self.printStatus(self.myFhHw.getHW_FH_SShe()))

        #HW_BL_CORE
        if cmp(self.myBlHw.getHW_BL_CORE()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.myBlHw.getHW_BL_CORE()[0]+'：'+self.myBlHw.getHW_BL_CORE()[1]+'\n'+self.printStatus(self.myBlHw.getHW_BL_CORE()))

        #HW_BL_AGG
        if cmp(self.myBlHw.getHW_BL_AGG()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.myBlHw.getHW_BL_AGG()[0]+'：'+self.myBlHw.getHW_BL_AGG()[1]+'\n'+self.printStatus(self.myBlHw.getHW_BL_AGG()))

        #HW_BL_SUBFAB_2
        if cmp(self.myBlHw.getHW_BL_SUBFAB_2()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.myBlHw.getHW_BL_SUBFAB_2()[0]+'：'+self.myBlHw.getHW_BL_SUBFAB_2()[1]+'\n'+self.printStatus(self.myBlHw.getHW_BL_SUBFAB_2()))

        #HW_BL_SUBFAB_1
        if cmp(self.myBlHw.getHW_BL_SUBFAB_1()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.myBlHw.getHW_BL_SUBFAB_1()[0]+'：'+self.myBlHw.getHW_BL_SUBFAB_1()[1]+'\n'+self.printStatus(self.myBlHw.getHW_BL_SUBFAB_1()))

        #HW_BL_PUB3F
        if cmp(self.myBlHw.getHW_BL_PUB3F()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.myBlHw.getHW_BL_PUB3F()[0]+'：'+self.myBlHw.getHW_BL_PUB3F()[1]+'\n'+self.printStatus(self.myBlHw.getHW_BL_PUB3F()))

        #HW_BL_PUB1F
        if cmp(self.myBlHw.getHW_BL_PUB1F()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.myBlHw.getHW_BL_PUB1F()[0]+'：'+self.myBlHw.getHW_BL_PUB1F()[1]+'\n'+self.printStatus(self.myBlHw.getHW_BL_PUB1F()))

        #HW_BL_OFF4F
        if cmp(self.myBlHw.getHW_BL_OFF4F()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.myBlHw.getHW_BL_OFF4F()[0]+'：'+self.myBlHw.getHW_BL_OFF4F()[1]+'\n'+self.printStatus(self.myBlHw.getHW_BL_OFF4F()))

        #HW_BL_OFF2F-3
        if cmp(self.myBlHw.getHW_BL_OFF2F_3()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.myBlHw.getHW_BL_OFF2F_3()[0]+'：'+self.myBlHw.getHW_BL_OFF2F_3()[1]+'\n'+self.printStatus(self.myBlHw.getHW_BL_OFF2F_3()))

        #HW_BL_OFF2F-2
        if cmp(self.myBlHw.getHW_BL_OFF2F_2()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.myBlHw.getHW_BL_OFF2F_2()[0]+'：'+self.myBlHw.getHW_BL_OFF2F_2()[1]+'\n'+self.printStatus(self.myBlHw.getHW_BL_OFF2F_2()))

        #HW_BL_OFF2F-1
        if cmp(self.myBlHw.getHW_BL_OFF2F_1()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.myBlHw.getHW_BL_OFF2F_1()[0]+'：'+self.myBlHw.getHW_BL_OFF2F_1()[1]+'\n'+self.printStatus(self.myBlHw.getHW_BL_OFF2F_1()))

        #HW_BL_OFF1F-3
        if cmp(self.myBlHw.getHW_BL_OFF1F_3()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.myBlHw.getHW_BL_OFF1F_3()[0]+'：'+self.myBlHw.getHW_BL_OFF1F_3()[1]+'\n'+self.printStatus(self.myBlHw.getHW_BL_OFF1F_3()))

        #HW_BL_OFF1F-2
        if cmp(self.myBlHw.getHW_BL_OFF1F_2()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.myBlHw.getHW_BL_OFF1F_2()[0]+'：'+self.myBlHw.getHW_BL_OFF1F_2()[1]+'\n'+self.printStatus(self.myBlHw.getHW_BL_OFF1F_2()))

        #HW_BL_OFF1F-1
        if cmp(self.myBlHw.getHW_BL_OFF1F_1()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.myBlHw.getHW_BL_OFF1F_1()[0]+'：'+self.myBlHw.getHW_BL_OFF1F_1()[1]+'\n'+self.printStatus(self.myBlHw.getHW_BL_OFF1F_1()))

        #HW_BL_DaMen
        if cmp(self.myBlHw.getHW_BL_DaMen()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.myBlHw.getHW_BL_DaMen()[0]+'：'+self.myBlHw.getHW_BL_DaMen()[1]+'\n'+self.printStatus(self.myBlHw.getHW_BL_DaMen()))

        #HW_BL_PUBOFF
        if cmp(self.myBlHw.getHW_BL_PUBOFF()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.myBlHw.getHW_BL_PUBOFF()[0]+'：'+self.myBlHw.getHW_BL_PUBOFF()[1]+'\n'+self.printStatus(self.myBlHw.getHW_BL_PUBOFF()))

        #HW_BL_OFF4FTD
        if cmp(self.myBlHw.getHW_BL_OFF4FTD()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.myBlHw.getHW_BL_OFF4FTD()[0]+'：'+self.myBlHw.getHW_BL_OFF4FTD()[1]+'\n'+self.printStatus(self.myBlHw.getHW_BL_OFF4FTD()))

        #HW_BL_CUB3F
        if cmp(self.myBlHw.getHW_BL_CUB3F()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.myBlHw.getHW_BL_CUB3F()[0]+'：'+self.myBlHw.getHW_BL_CUB3F()[1]+'\n'+self.printStatus(self.myBlHw.getHW_BL_CUB3F()))

        #HW_BL_LJ-2
        if cmp(self.myBlHw.getHW_BL_LJ_2()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.myBlHw.getHW_BL_LJ_2()[0]+'：'+self.myBlHw.getHW_BL_LJ_2()[1]+'\n'+self.printStatus(self.myBlHw.getHW_BL_LJ_2()))

        #HW_BL_LJ-1
        if cmp(self.myBlHw.getHW_BL_LJ_1()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.myBlHw.getHW_BL_LJ_1()[0]+'：'+self.myBlHw.getHW_BL_LJ_1()[1]+'\n'+self.printStatus(self.myBlHw.getHW_BL_LJ_1()))

        #SangforSG
        if cmp(self.myBlOther.getSangforSG()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.myBlOther.getSangforSG()[0]+'：'+self.myBlOther.getSangforSG()[1]+'\n'+self.printStatus(self.myBlOther.getSangforSG()))

        #360TD
        if cmp(self.myBlOther.get360TD()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.myBlOther.get360TD()[0]+'：'+self.myBlOther.get360TD()[1]+'\n'+self.printStatus(self.myBlOther.get360TD()))

        #DellCMC
        if cmp(self.myBlDell.getDellCMC()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.myBlDell.getDellCMC()[0]+'：'+self.myBlDell.getDellCMC()[1]+'\n'+self.printStatus(self.myBlDell.getDellCMC()))

        #R710 & M710HD
        if cmp(self.myBlDell.getDelliDRAC6()[0],'ok') != 0:
            self.myWxMessage.wxMessage(self.myBlDell.getDelliDRAC6()[1])

        #R730 & M630HD
        if cmp(self.myBlDell.getDelliDRAC8()[0],'ok') != 0:
            self.myWxMessage.wxMessage(self.myBlDell.getDelliDRAC8()[1])

        #BYD UPS
        if cmp(self.myBydUps.getUpsStatus('ups1')[0],'ok') != 0:
            self.myWxMessage.wxMessage('***ups1***\n'+self.myBydUps.getUpsStatus('ups1')[1])
        if cmp(self.myBydUps.getUpsStatus('ups2')[0],'ok') != 0:
            self.myWxMessage.wxMessage('***ups2***\n'+self.myBydUps.getUpsStatus('ups2')[1])


def main():
    myMonitor = BydMonitor()
    myMonitor.checkAllDeviceStatus()

if __name__ == '__main__':
    main()
