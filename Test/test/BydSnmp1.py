#!/usr/bin/env python27
# -*- coding:utf-8 -*-

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
    import WxWeather
except ImportError:
    print 'ImportError'

__all__ = [
    "WxSnmp","WxMessage"
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

class WxSnmp():
    '''
    BYD Snmp,Base on PySNMP
    MIB:Management Information Base
    SMI:Structure of Management Information

    SNMPv2-MIB::sysUpTime.0 = 1115361613
    异常：
        无效主机：No SNMP response received before timeout
        无效MIB对象：SmiError
    '''
    def __init__(self):
        '''
        初始化BydSnmp
        读取同目录下'config_snmp.ini'配置常量信息
        初始化PySNMP常用对象
        :exception 读取config_snmp.ini异常时，报：'ReadConfigFileError'
        '''
        self.myWxMessage = WxMessage()
        config = ConfigParser.ConfigParser()
        try:
            #获取BydSNMP.py执行时的绝对路径
            self.mainPath = os.path.dirname(os.path.realpath(__file__))
            configFile = os.path.join(self.mainPath,'config_snmp.ini')
            config.readfp(open(configFile, "rb"))
            self.configIniDict = dict(config._sections)
            for k in self.configIniDict:
                self.configIniDict[k] = dict(self.configIniDict[k])

            #SNMP配置信息
            self.snmp_port = int(self.configIniDict['Global']['port'])#端口号161
            self.snmp_version = int(self.configIniDict['Global']['version'])#版本v2c
            self.snmp_communication = self.configIniDict['Global']['communication']#public@byd

            #Huawei
            self.hwSwitchTemperatureThreshold = int(self.configIniDict['Huawei']['hwSwitchTemperatureThreshold'.lower()])#交换机处理器温度
            self.hwRouterTemperatureThreshold = int(self.configIniDict['Huawei']['hwRouterTemperatureThreshold'.lower()])#路由器处理器
            self.hwEntityOpticalTxPowerThreshold = int(self.configIniDict['Huawei']['hwEntityOpticalTxPowerThreshold'.lower()])#多模SPF模块功率
            self.hwEntitySOpticalTxPowerThreshold = int(self.configIniDict['Huawei']['hwEntitySOpticalTxPowerThreshold'.lower()])#单模SPF模块功率

            #DellCMC
            self.drsCMCAmbientTemperatureThreshold = int(self.configIniDict['Dell']['drsCMCAmbientTemperatureThreshold'.lower()])#CMC环境温度
            self.iDRAC6ServerDict =  self.configIniDict['Dell_iDRAC6_Servers'] #iDrac 6 Server lists
            self.iDRAC8ServerDict =  self.configIniDict['Dell_iDRAC8_Servers'] #iDrac 8 Server lists

            #360TD
            self.systemTemperatureThreshold = int(self.configIniDict['360TD']['systemTemperatureThreshold'.lower()])#设备温度
            self.fanSpeedSpeedSysThreshold = int(self.configIniDict['360TD']['fanSpeedSpeedSysThreshold'.lower()])#系统风扇转速
            self.fanSpeedSpeedCpuThreshold = int(self.configIniDict['360TD']['fanSpeedSpeedCpuThreshold'.lower()])#CPU风扇转速
            self.sessionCurrentNumberThreshold = int(self.configIniDict['360TD']['sessionCurrentNumberThreshold'.lower()])#当前会话数

            #SangforSG
            self.sfSysCpuCostRateThreshold = int(self.configIniDict['SangforSG']['sfSysCpuCostRateThreshold'.lower()]) #CPU使用率
            self.numOfCurOnlinThreshold = int(self.configIniDict['SangforSG']['numOfCurOnlinThreshold'.lower()]) #在线用户数
            self.numOfSessionThreshold = int(self.configIniDict['SangforSG']['numOfSessionThreshold'.lower()])#当前会话数

            #WLAN
            self.hwStaGlobalWirelessPacketDropRateThreshold = int(self.configIniDict['Huawei']['hwStaGlobalWirelessPacketDropRateThreshold'.lower()])#终端丢包率
            self.hwWlanStaComplianceRateThreshold = int(self.configIniDict['Huawei']['hwWlanStaComplianceRateThreshold'.lower()])#终端达成率
            self.hwWlanApComplianceRateThreshold = int(self.configIniDict['Huawei']['hwWlanApComplianceRateThreshold'.lower()])#AP达成率
            self.hwWlanRfComplianceRateThreshold = int(self.configIniDict['Huawei']['hwWlanRfComplianceRateThreshold'.lower()])#射频达成率
            self.hwWlanCurJointApNumThreshold = int(self.configIniDict['Huawei']['hwWlanCurJointApNumThreshold'.lower()])#在线终端数

            #初始化PySNMP常用对象
            self.snmpEngine = SnmpEngine()
            self.contextData = ContextData()  #ContextData用于SNMP v3版本
            self.communityData = CommunityData(self.snmp_communication,mpModel=self.snmp_version) #Model=SNMP v2c
        except IOError:
            print 'ReadConfigFileError'

    def __getUdpTransportTarget(self,address):
        '''
        设置传输曾和目标
        默认端口：161
        :param address:目标设备的IP地址或者主机名
        :return 返回网络传输层目标
        '''
        return UdpTransportTarget((address,self.snmp_port))

    def __getObjectType(self,oid):
        '''
        ObjectIdentity类负责MIB对象标识
        ObjectType(ObjectIdentity('1.3.6.1.2.1.1.1.0'))
        :param oid:OID
        :return ObjectType类实例代表PySNMP里构造OBJECT-TYPE SMI
        '''
        return ObjectType(ObjectIdentity(oid))

    def getSnmpValue(self,address,oid):
        '''
        返回唯一OID对应的value
        :param address: 设备IP或者主机名
        :param oid: OID
        :return:MIB对象值
        '''
        try:
            iterrator = getCmd(
                self.snmpEngine,
                self.communityData,
                self.__getUdpTransportTarget(address),
                self.contextData,
                self.__getObjectType(oid)
            )
            errorIndication,errorStatus,errorIndex,varBinds = next(iterrator)
            if errorIndication:
                print (errorIndication)
            else:
                if errorStatus:
                    print('%s at %s' % (errorStatus.prettyPrint(),varBinds[int(errorIndex)-1] if errorIndex else '?'))
                else:
                    for varBind in varBinds:
                        if( not varBind[1]):  #当OID错误或者不存在时，报错：'No Such Instance currently exists at this OID'
                            return '-1'
                        else:
                            mibValue = [x.prettyPrint() for x in varBind][1] #S5700-52P-LI-AC
                            #只返回第一行（当字符串有多行时，仅返回第一行）
                            return mibValue[:].split('\r')[0]
        except Exception as e:
            print 'Error'

    def getSangforSG(self):
        '''
        #深信服SG SANGFOR-GENERAL-MIB.mib
        #管理地址：10.15.1.253
        :return:
        '''
         #获取常用配置信息
        address = '10.15.1.253'
        sfSysCpuCostRate = self.getSnmpValue(address, '.1.3.6.1.4.1.35047.1.3.0') #当前CPU使用率
        numOfCurOnlin = self.getSnmpValue(address, '.1.3.6.1.4.1.35047.2.1.1.1.0') #在线用户数
        numOfSession = self.getSnmpValue(address, '.1.3.6.1.4.1.35047.2.1.1.6.0') #当前会话数
        ifTxKBs = int(self.getSnmpValue(address, '.1.3.6.1.4.1.35047.2.1.2.1.7.1'))/1024 #Eth0端口发送速率
        ifRxKBs = int(self.getSnmpValue(address, '.1.3.6.1.4.1.35047.2.1.2.1.8.1'))/1024 #Eth0端口接收速率

        if( int(sfSysCpuCostRate) < self.sfSysCpuCostRateThreshold and
            int(numOfCurOnlin) < self.numOfCurOnlinThreshold and int(numOfSession) < self.numOfSessionThreshold ):
            globalStatus = 'ok'
        else:
            globalStatus = 'fault'

        return ['SangforSG',globalStatus,
                    {
                    '1.CPU使用率':sfSysCpuCostRate,
                    '2.在线用户数':numOfCurOnlin,
                    '3.当前会话数':numOfSession,
                    '4.发送速率(KB/s)':str(ifTxKBs),
                    '5.接收速率(KB/s)':str(ifRxKBs)
                    }
                ]

    def get360TD(self):
        '''
        #360天堤防火墙
        #管理地址：10.15.1.251
        :return:
        '''
         #获取常用配置信息
        address = '10.15.5.251'
        systemTemperature = self.getSnmpValue(address, '.1.3.6.1.4.1.32328.6.1.8.0')#设备温度
        cpuPercentUsage = self.getSnmpValue(address, '.1.3.6.1.4.1.32328.6.1.10.1.2.0')#CPU使用率
        memoryPercentUsage = self.getSnmpValue(address, '.1.3.6.1.4.1.32328.6.1.10.3.2.0')#内存使用率
        CFDiskPrcentUsage = self.getSnmpValue(address, '.1.3.6.1.4.1.32328.6.1.10.2.2.0')#系统盘使用率
        fanSpeedSpeed1 = self.getSnmpValue(address, '.1.3.6.1.4.1.32328.6.1.10.5.1.1.3.1')#系统风扇转速
        fanSpeedSpeed2 = self.getSnmpValue(address, '.1.3.6.1.4.1.32328.6.1.10.5.1.1.3.2') #CPU风扇转速
        sessionCurrentNumber = self.getSnmpValue(address, '.1.3.6.1.4.1.32328.6.2.1.2.0')#当前会话数
        #ifInBps5 = int(self.getSnmpValue(address, '.1.3.6.1.4.1.32328.6.2.3.1.1.3.5'))/1024*8 #进系统速率(惠州到宁波）bps/s
        #ifOutBps5 = int(self.getSnmpValue(address, '.1.3.6.1.4.1.32328.6.2.3.1.1.4.5'))/1024*8 #出系统速率（宁波到惠州）bps/s

        ifInBps5 = round(float(self.getSnmpValue(address, '.1.3.6.1.4.1.32328.6.2.3.1.1.3.5'))/1024*8,1) #进系统速率(惠州到宁波）bps/s
        ifOutBps5 = round(float(self.getSnmpValue(address, '.1.3.6.1.4.1.32328.6.2.3.1.1.4.5'))/1024*8,1) #出系统速率（宁波到惠州）bps/s
        ifInBps2 = round(float(self.getSnmpValue(address, '.1.3.6.1.4.1.32328.6.2.3.1.1.3.2'))/1024*8,1) #进系统速率(奉化到北仑）bps/s
        ifOutBps2 = round(float(self.getSnmpValue(address, '.1.3.6.1.4.1.32328.6.2.3.1.1.4.2'))/1024*8,1) #出系统速率（北仑到奉化）bps/s

        if( int(systemTemperature) < self.systemTemperatureThreshold and
            int(fanSpeedSpeed1) > self.fanSpeedSpeedSysThreshold and int(fanSpeedSpeed2) > self.fanSpeedSpeedCpuThreshold and
            int(sessionCurrentNumber) < self.sessionCurrentNumberThreshold ):
            globalStatus = 'ok'
        else:
            globalStatus = 'fault'

        return ['360TD',globalStatus,
                    {
                    '1.设备温度':systemTemperature,
                    '2.CPU使用率':cpuPercentUsage,
                    '3.内存使用率':memoryPercentUsage,
                    '4.系统盘使用率':CFDiskPrcentUsage,
                    '5.系统风扇转速':fanSpeedSpeed1,
                    '6.CPU风扇转速':fanSpeedSpeed2,
                    '7.当前会话数':sessionCurrentNumber,
                    '8.惠州到宁波流量(KB/s)':str(ifInBps5),
                    '8.宁波到惠州流量(KB/s)':str(ifOutBps5),
                    '9.奉化到北仑流量(KB/s)':str(ifInBps2),
                    '9.北仑到奉化流量(KB/s)':str(ifOutBps2)
                    }
                ]

    def getDellCMC(self):
        '''
        #Dell e1000刀框
        #管理地址：10.15.0.200
        :return:
        '''
        #获取常用配置信息
        address = '10.15.0.200'
        drsCMCAmbientTemperatur = self.getSnmpValue(address, '.1.3.6.1.4.1.674.10892.2.3.1.10.0') #环境温度
        drsGlobalSystemStaus = self.getSnmpValue(address, '.1.3.6.1.4.1.674.10892.2.2.1.0') #全局状态,3表示OK

        if( int(drsCMCAmbientTemperatur) < self.drsCMCAmbientTemperatureThreshold and
            int(drsGlobalSystemStaus) == 3 ):
            globalStatus = 'ok'
            drsGlobalSystemStaus = 'ok'
        else:
            globalStatus = 'fault'
            drsGlobalSystemStaus = 'fault'

        return ['DellCMC',globalStatus,
                    {
                    '1.环境温度':drsCMCAmbientTemperatur,
                    '2.全局状态':drsGlobalSystemStaus
                    }
                ]

    def getHW_BL_LJ_1(self):
        '''
        #连接交换机
        #S5700-28P,单机双电口上行链路
        :return:
        '''
        address = '10.15.0.252'
        hwEntityTemperature = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67108873')#MPU 温度
        hwTrunkOperstatus5 = self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.5')#Eth-Trunk端口状态 GE0/0/1
        hwTrunkOperstatus6 =self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.6')#Eth-Trunk端口状态 GE0/0/2

        if( int(hwEntityTemperature) < self.hwSwitchTemperatureThreshold and
            int(hwTrunkOperstatus5) == 1 and
            int(hwTrunkOperstatus6) == 1 ):
            globalStatus = 'ok'
        else:
            globalStatus = 'fault'

        return ['HW_BL_LJ_1',globalStatus,
                    {
                    '1.MPU温度':hwEntityTemperature,
                    '2.EthTrunk':hwTrunkOperstatus5+','+hwTrunkOperstatus6
                    }
                ]

    def getHW_BL_LJ_2(self):
        '''
        #连接交换机
        #S5700-28P,单机双电口上行链路
        :return:
        '''
        address = '10.15.0.253'
        hwEntityTemperature = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67108873')#MPU 温度
        hwTrunkOperstatus5 = self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.5')#Eth-Trunk端口状态 GE0/0/1
        hwTrunkOperstatus6 =self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.6')#Eth-Trunk端口状态 GE0/0/2

        if( int(hwEntityTemperature) < self.hwSwitchTemperatureThreshold and
            int(hwTrunkOperstatus5) == 1 and
            int(hwTrunkOperstatus6) == 1 ):
            globalStatus = 'ok'
        else:
            globalStatus = 'fault'

        return ['HW_BL_LJ_2',globalStatus,
                    {
                    '1.MPU温度':hwEntityTemperature,
                    '2.EthTrunk':hwTrunkOperstatus5+','+hwTrunkOperstatus6
                    }
                ]

    def getHW_BL_CUB3F(self):
        '''
        #OFFICE-CUB3F(SED)
        #S5700-52P,单机单光口上行链路
        :return:
        '''
        address = '10.15.2.43'
        hwEntityTemperature = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67108873')#MPU 温度
        hwEntityOpticalTxPowerThreshold = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67308622')#GE0/0/49 SPF模块功率
        hwEntityFanState = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.0.0')#MPU 风扇状态
        hwTrunkOperstatus53 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.53')#Eth-Trunk(GE0/0/49)端口状态

        if( int(hwEntityTemperature) < self.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPowerThreshold) > self.hwEntityOpticalTxPowerThreshold and
            int(hwEntityFanState) == 1 and
            int(hwTrunkOperstatus53) == 1
          ):
            globalStatus = 'ok'
        else:
            globalStatus = 'fault'

        return ['HW_BL_CUB3F',globalStatus,
                    {
                    '1.MPU温度':hwEntityTemperature,
                    '2.风扇状态':hwEntityFanState,
                    '3.SPF功率':hwEntityOpticalTxPowerThreshold,
                    '4.EthTrunk':hwTrunkOperstatus53
                    }
                ]

    def getHW_BL_OFF4FTD(self):
        '''
        #OFFICE-OFF4FTD
        #S5700-52P,单机单电口上行链路
        :return:
        '''
        address = '10.15.2.49'
        hwEntityTemperature = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67371017')#MPU 温度
        hwEntityFanState = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.0')#MPU 风扇状态
        hwTrunkOperstatus53 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.53')#Eth-Trunk(GE1/0/47)端口状态

        if( int(hwEntityTemperature) < self.hwSwitchTemperatureThreshold and
            int(hwEntityFanState) == 1 and
            int(hwTrunkOperstatus53) == 1
          ):
            globalStatus = 'ok'
        else:
            globalStatus = 'fault'

        return ['HW_BL_OFF4FTD',globalStatus,
                    {
                    '1.MPU温度':hwEntityTemperature,
                    '2.风扇状态':hwEntityFanState,
                    '3.EthTrunk':hwTrunkOperstatus53
                    }
                ]

    def getHW_BL_PUBOFF(self):
        '''
        #OFFICE-PUBOFF
        #S5700-52P,单机单光口上行链路
        :return:
        '''
        address = '10.15.2.42'
        hwEntityTemperature = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67108873')#MPU 温度
        hwEntityFanState = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.0.0')#MPU 风扇状态
        hwEntityOpticalTxPowerThreshold = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67308622')#GE0/0/49 SPF模块功率
        hwTrunkOperstatus55 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.55')#Eth-Trunk(GE0/0/49)端口状态

        if( int(hwEntityTemperature) < self.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPowerThreshold) > self.hwEntityOpticalTxPowerThreshold and
            int(hwEntityFanState) == 1 and
            int(hwTrunkOperstatus55) == 1
          ):
            globalStatus = 'ok'
        else:
            globalStatus = 'fault'

        return ['HW_BL_PUBOFF',globalStatus,
                    {
                    '1.MPU温度':hwEntityTemperature,
                    '2.风扇状态':hwEntityFanState,
                    '3.SPF功率':hwEntityOpticalTxPowerThreshold,
                    '4.EthTrunk':hwTrunkOperstatus55
                    }
                ]

    def getHW_BL_DaMen(self):
        '''
        #OFFICE-DaMen
        #S5700-28P,单机单电口上行链路
        :return:
        '''
        address = '10.15.2.44'
        hwEntityTemperature = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67108873')#MPU 温度
        hwTrunkOperstatus28 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.28')#Eth-Trunk(GE0/0/24)端口状态

        if( int(hwEntityTemperature) < self.hwSwitchTemperatureThreshold and
            int(hwTrunkOperstatus28) == 1
          ):
            globalStatus = 'ok'
        else:
            globalStatus = 'fault'

        return ['HW_BL_DaMen',globalStatus,
                    {
                    '1.MPU温度':hwEntityTemperature,
                    '2.EthTrunk':hwTrunkOperstatus28
                    }
                ]

    def getHW_BL_OFF1F_1(self):
        '''
        #OFFICE-OFF1F-1
        #S5700-52P,双机双光口上行链路单堆叠链路
        :return:
        '''
        address = '10.15.2.11'
        hwEntityTemperature1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67371017')#MPU 1温度
        hwEntityTemperature2 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67633161')#MPU 2温度
        hwEntityFanState1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.0')#MPU 1风扇状态
        hwEntityFanState2 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.0')#MPU 2风扇状态
        hwEntityOpticalTxPowerThreshold1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67570766')#GE1/0/49 SPF模块功率
        hwEntityOpticalTxPowerThreshold2 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67832910')#GE2/0/49 SPF模块功率
        hwTrunkOperstatus55 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.55')#Eth-Trunk(GE1/0/49)端口状态
        hwTrunkOperstatus107 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.107')#Eth-Trunk(GE2/0/49)端口状态
        hwStackPortStatus1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.1.0')#Stack(GE1/0/51)端口状态
        hwStackPortStatus2 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.2.1')#Stack(GE2/0/52)端口状态

        if( int(hwEntityTemperature1) < self.hwSwitchTemperatureThreshold and
            int(hwEntityTemperature2) < self.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPowerThreshold1) > self.hwEntityOpticalTxPowerThreshold and
            int(hwEntityOpticalTxPowerThreshold2) > self.hwEntityOpticalTxPowerThreshold and
            int(hwEntityFanState1) == 1 and int(hwEntityFanState2) == 1 and
            int(hwTrunkOperstatus55) == 1 and int(hwTrunkOperstatus107) == 1 and
            int(hwStackPortStatus1) == 1 and int(hwStackPortStatus2) == 1
          ):
            globalStatus = 'ok'
        else:
            globalStatus = 'fault'

        return ['HW_BL_OFF1F-1',globalStatus,
                    {
                    '1.MPU温度':hwEntityTemperature1+','+hwEntityTemperature2,
                    '2.风扇状态':hwEntityFanState1+','+hwEntityFanState2,
                    '3.SPF功率':hwEntityOpticalTxPowerThreshold1+','+hwEntityOpticalTxPowerThreshold2,
                    '4.EthTrunk':hwTrunkOperstatus55+','+hwTrunkOperstatus107,
                    '5.堆叠口状态':hwStackPortStatus1+','+hwStackPortStatus2
                    }
                ]

    def getHW_BL_OFF1F_2(self):
        '''
        #OFFICE-OFF1F-2
        #S5700-52P,双机双光口上行链路单堆叠链路
        :return:
        '''
        address = '10.15.2.12'
        hwEntityTemperature1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67371017')#MPU 1温度
        hwEntityTemperature2 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67633161')#MPU 2温度
        hwEntityFanState1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.0')#MPU 1风扇状态
        hwEntityFanState2 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.0')#MPU 2风扇状态
        hwEntityOpticalTxPowerThreshold1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67570766')#GE1/0/49 SPF模块功率
        hwEntityOpticalTxPowerThreshold2 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67832910')#GE2/0/49 SPF模块功率
        hwTrunkOperstatus55 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.55')#Eth-Trunk(GE1/0/49)端口状态
        hwTrunkOperstatus107 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.107')#Eth-Trunk(GE2/0/49)端口状态
        hwStackPortStatus1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.1.0')#Stack(GE1/0/51)端口状态
        hwStackPortStatus2 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.2.1')#Stack(GE2/0/52)端口状态

        if( int(hwEntityTemperature1) < self.hwSwitchTemperatureThreshold and
            int(hwEntityTemperature2) < self.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPowerThreshold1) > self.hwEntityOpticalTxPowerThreshold and
            int(hwEntityOpticalTxPowerThreshold2) > self.hwEntityOpticalTxPowerThreshold and
            int(hwEntityFanState1) == 1 and int(hwEntityFanState2) == 1 and
            int(hwTrunkOperstatus55) == 1 and int(hwTrunkOperstatus107) == 1 and
            int(hwStackPortStatus1) == 1 and int(hwStackPortStatus2) == 1
          ):
            globalStatus = 'ok'
        else:
            globalStatus = 'fault'

        return ['HW_BL_OFF1F-2',globalStatus,
                    {
                    '1.MPU温度':hwEntityTemperature1+','+hwEntityTemperature2,
                    '2.风扇状态':hwEntityFanState1+','+hwEntityFanState2,
                    '3.SPF功率':hwEntityOpticalTxPowerThreshold1+','+hwEntityOpticalTxPowerThreshold2,
                    '4.EthTrunk':hwTrunkOperstatus55+','+hwTrunkOperstatus107,
                    '5.堆叠口状态':hwStackPortStatus1+','+hwStackPortStatus2
                    }
                ]

    def getHW_BL_OFF1F_3(self):
        '''
        OID与其他1F2F不同
        #OFFICE-OFF1F-3
        #S5700-52P,双机双光口上行链路单堆叠链路
        :return:
        '''
        address = '10.15.2.13'
        hwEntityTemperature1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67371017')#MPU 1温度
        hwEntityTemperature2 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67633161')#MPU 2温度
        hwEntityFanState1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.0')#MPU 1风扇状态
        hwEntityFanState2 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.0')#MPU 2风扇状态
        hwEntityOpticalTxPowerThreshold1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67570766')#GE1/0/49 SPF模块功率
        hwEntityOpticalTxPowerThreshold2 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67832910')#GE2/0/49 SPF模块功率
        hwTrunkOperstatus54 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.54')#Eth-Trunk(GE1/0/49)端口状态
        hwTrunkOperstatus158 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.158')#Eth-Trunk(GE2/0/49)端口状态
        hwStackPortStatus1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.1.0')#Stack(GE1/0/51)端口状态
        hwStackPortStatus2 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.2.1')#Stack(GE2/0/52)端口状态

        if( int(hwEntityTemperature1) < self.hwSwitchTemperatureThreshold and
            int(hwEntityTemperature2) < self.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPowerThreshold1) > self.hwEntityOpticalTxPowerThreshold and
            int(hwEntityOpticalTxPowerThreshold2) > self.hwEntityOpticalTxPowerThreshold and
            int(hwEntityFanState1) == 1 and int(hwEntityFanState2) == 1 and
            int(hwTrunkOperstatus54) == 1 and int(hwTrunkOperstatus158) == 1 and
            int(hwStackPortStatus1) == 1 and int(hwStackPortStatus2) == 1
          ):
            globalStatus = 'ok'
        else:
            globalStatus = 'fault'

        return ['HW_BL_OFF1F-3',globalStatus,
                    {
                    '1.MPU温度':hwEntityTemperature1+','+hwEntityTemperature2,
                    '2.风扇状态':hwEntityFanState1+','+hwEntityFanState2,
                    '3.SPF功率':hwEntityOpticalTxPowerThreshold1+','+hwEntityOpticalTxPowerThreshold2,
                    '4.EthTrunk':hwTrunkOperstatus54+','+hwTrunkOperstatus158,
                    '5.堆叠口状态':hwStackPortStatus1+','+hwStackPortStatus2
                    }
                ]

    def getHW_BL_OFF2F_1(self):
        '''
        #OFFICE-OFF2F-1
        #S5700-52P,双机双光口上行链路单堆叠链路
        :return:
        '''
        address = '10.15.2.21'
        hwEntityTemperature1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67371017')#MPU 1温度
        hwEntityTemperature2 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67633161')#MPU 2温度
        hwEntityFanState1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.0')#MPU 1风扇状态
        hwEntityFanState2 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.0')#MPU 2风扇状态
        hwEntityOpticalTxPowerThreshold1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67570766')#GE1/0/49 SPF模块功率
        hwEntityOpticalTxPowerThreshold2 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67832910')#GE2/0/49 SPF模块功率
        hwTrunkOperstatus55 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.55')#Eth-Trunk(GE1/0/49)端口状态
        hwTrunkOperstatus107 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.107')#Eth-Trunk(GE2/0/49)端口状态
        hwStackPortStatus1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.1.0')#Stack(GE1/0/51)端口状态
        hwStackPortStatus2 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.2.1')#Stack(GE2/0/52)端口状态

        if( int(hwEntityTemperature1) < self.hwSwitchTemperatureThreshold and
            int(hwEntityTemperature2) < self.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPowerThreshold1) > self.hwEntityOpticalTxPowerThreshold and
            int(hwEntityOpticalTxPowerThreshold2) > self.hwEntityOpticalTxPowerThreshold and
            int(hwEntityFanState1) == 1 and int(hwEntityFanState2) == 1 and
            int(hwTrunkOperstatus55) == 1 and int(hwTrunkOperstatus107) == 1 and
            int(hwStackPortStatus1) == 1 and int(hwStackPortStatus2) == 1
          ):
            globalStatus = 'ok'
        else:
            globalStatus = 'fault'

        return ['HW_BL_OFF2F-1',globalStatus,
                    {
                    '1.MPU温度':hwEntityTemperature1+','+hwEntityTemperature2,
                    '2.风扇状态':hwEntityFanState1+','+hwEntityFanState2,
                    '3.SPF功率':hwEntityOpticalTxPowerThreshold1+','+hwEntityOpticalTxPowerThreshold2,
                    '4.EthTrunk':hwTrunkOperstatus55+','+hwTrunkOperstatus107,
                    '5.堆叠口状态':hwStackPortStatus1+','+hwStackPortStatus2
                    }
                ]

    def getHW_BL_OFF2F_2(self):
        '''
        #OFFICE-OFF2F-2
        #S5700-52P,双机双光口上行链路单堆叠链路
        :return:
        '''
        address = '10.15.2.22'
        hwEntityTemperature1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67371017')#MPU 1温度
        hwEntityTemperature2 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67633161')#MPU 2温度
        hwEntityFanState1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.0')#MPU 1风扇状态
        hwEntityFanState2 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.0')#MPU 2风扇状态
        hwEntityOpticalTxPowerThreshold1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67570766')#GE1/0/49 SPF模块功率
        hwEntityOpticalTxPowerThreshold2 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67832910')#GE2/0/49 SPF模块功率
        hwTrunkOperstatus105 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.105')#Eth-Trunk(GE1/0/49)端口状态
        hwTrunkOperstatus157 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.157')#Eth-Trunk(GE2/0/49)端口状态
        hwStackPortStatus1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.1.0')#Stack(GE1/0/51)端口状态
        hwStackPortStatus2 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.2.1')#Stack(GE2/0/52)端口状态

        if( int(hwEntityTemperature1) < self.hwSwitchTemperatureThreshold and
            int(hwEntityTemperature2) < self.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPowerThreshold1) > self.hwEntityOpticalTxPowerThreshold and
            int(hwEntityOpticalTxPowerThreshold2) > self.hwEntityOpticalTxPowerThreshold and
            int(hwEntityFanState1) == 1 and int(hwEntityFanState2) == 1 and
            int(hwTrunkOperstatus105) == 1 and int(hwTrunkOperstatus157) == 1 and
            int(hwStackPortStatus1) == 1 and int(hwStackPortStatus2) == 1
          ):
            globalStatus = 'ok'
        else:
            globalStatus = 'fault'

        return ['HW_BL_OFF2F-2',globalStatus,
                    {
                    '1.MPU温度':hwEntityTemperature1+','+hwEntityTemperature2,
                    '2.风扇状态':hwEntityFanState1+','+hwEntityFanState2,
                    '3.SPF功率':hwEntityOpticalTxPowerThreshold1+','+hwEntityOpticalTxPowerThreshold2,
                    '4.EthTrunk':hwTrunkOperstatus105+','+hwTrunkOperstatus157,
                    '5.堆叠口状态':hwStackPortStatus1+','+hwStackPortStatus2
                    }
                ]

    def getHW_BL_OFF2F_3(self):
        '''
        #OFFICE-OFF2F-3
        #S5700-52P,双机双光口上行链路单堆叠链路
        :return:
        '''
        address = '10.15.2.23'
        hwEntityTemperature1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67371017')#MPU 1温度
        hwEntityTemperature2 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67633161')#MPU 2温度
        hwEntityFanState1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.0')#MPU 1风扇状态
        hwEntityFanState2 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.0')#MPU 2风扇状态
        hwEntityOpticalTxPowerThreshold1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67570766')#GE1/0/49 SPF模块功率
        hwEntityOpticalTxPowerThreshold2 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67832910')#GE2/0/49 SPF模块功率
        hwTrunkOperstatus55 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.55')#Eth-Trunk(GE1/0/49)端口状态
        hwTrunkOperstatus107 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.107')#Eth-Trunk(GE2/0/49)端口状态
        hwStackPortStatus1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.1.0')#Stack(GE1/0/51)端口状态
        hwStackPortStatus2 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.2.1')#Stack(GE2/0/52)端口状态

        if( int(hwEntityTemperature1) < self.hwSwitchTemperatureThreshold and
            int(hwEntityTemperature2) < self.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPowerThreshold1) > self.hwEntityOpticalTxPowerThreshold and
            int(hwEntityOpticalTxPowerThreshold2) > self.hwEntityOpticalTxPowerThreshold and
            int(hwEntityFanState1) == 1 and int(hwEntityFanState2) == 1 and
            int(hwTrunkOperstatus55) == 1 and int(hwTrunkOperstatus107) == 1 and
            int(hwStackPortStatus1) == 1 and int(hwStackPortStatus2) == 1
          ):
            globalStatus = 'ok'
        else:
            globalStatus = 'fault'

        return ['HW_BL_OFF2F-3',globalStatus,
                    {
                    '1.MPU温度':hwEntityTemperature1+','+hwEntityTemperature2,
                    '2.风扇状态':hwEntityFanState1+','+hwEntityFanState2,
                    '3.SPF功率':hwEntityOpticalTxPowerThreshold1+','+hwEntityOpticalTxPowerThreshold2,
                    '4.EthTrunk':hwTrunkOperstatus55+','+hwTrunkOperstatus107,
                    '5.堆叠口状态':hwStackPortStatus1+','+hwStackPortStatus2
                    }
                ]

    def getHW_BL_OFF4F(self):
        '''
        #OFFICE-OFF4F
        #S5700-52P,三机双光口上行链路两两堆叠链路
        :return:
        '''
        address = '10.15.2.41'
        hwEntityTemperature1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67371017')#MPU 1温度
        hwEntityTemperature2 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67633161')#MPU 2温度
        hwEntityTemperature3 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67895305')#MPU 3温度
        hwEntityFanState1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.0')#MPU 1风扇状态
        hwEntityFanState2 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.0')#MPU 2风扇状态
        hwEntityFanState3 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.3.0')#MPU 3风扇状态
        hwEntityOpticalTxPowerThreshold1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67570766')#GE1/0/49 SPF模块功率
        hwEntityOpticalTxPowerThreshold2 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.68095054')#GE2/0/49 SPF模块功率
        hwTrunkOperstatus55 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.55')#Eth-Trunk(GE1/0/49)端口状态
        hwTrunkOperstatus159 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.159')#Eth-Trunk(GE3/0/49)端口状态
        hwStackPortStatus10 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.1.0')#Stack(GE1/0/51)端口状态
        hwStackPortStatus20 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.2.0')#Stack(GE2/0/52)端口状态
        hwStackPortStatus21 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.2.1')#Stack(GE2/0/51)端口状态
        hwStackPortStatus31 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.3.1')#Stack(GE3/0/52)端口状态

        if( int(hwEntityTemperature1) < self.hwSwitchTemperatureThreshold and
            int(hwEntityTemperature2) < self.hwSwitchTemperatureThreshold and
            int(hwEntityTemperature3) < self.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPowerThreshold1) > self.hwEntityOpticalTxPowerThreshold and
            int(hwEntityOpticalTxPowerThreshold2) > self.hwEntityOpticalTxPowerThreshold and
            int(hwEntityFanState1) == 1 and int(hwEntityFanState2) == 1 and int(hwEntityFanState3) == 1 and
            int(hwTrunkOperstatus55) == 1 and int(hwTrunkOperstatus159) == 1 and
            int(hwStackPortStatus10) == 1 and int(hwStackPortStatus20) == 1 and
            int(hwStackPortStatus21) == 1 and int(hwStackPortStatus31) == 1
          ):
            globalStatus = 'ok'
        else:
            globalStatus = 'fault'

        return ['HW_BL_OFF4F',globalStatus,
                    {
                    '1.MPU温度':hwEntityTemperature1+','+hwEntityTemperature2+','+hwEntityTemperature3,
                    '2.风扇状态':hwEntityFanState1+','+hwEntityFanState2+','+hwEntityFanState3,
                    '3.SPF功率':hwEntityOpticalTxPowerThreshold1+','+hwEntityOpticalTxPowerThreshold2,
                    '4.EthTrunk':hwTrunkOperstatus55+','+hwTrunkOperstatus159,
                    '5.堆叠口状态':hwStackPortStatus10+','+hwStackPortStatus20+','+hwStackPortStatus21+','+hwStackPortStatus31
                    }
                ]

    def getHW_BL_PUB1F(self):
        '''
        #S5700-52P,单机双光口上行链路
        :return:
        '''
        address = '10.15.0.60'
        hwEntityTemperature1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.0.0')#MPU 1温度
        hwEntityFanState1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.0.0')#MPU 1风扇状态
        hwEntityOpticalTxPowerThreshold1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67308622')#GE0/0/49 SPF模块功率
        hwEntityOpticalTxPowerThreshold2 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67308686')#GE0/0/50 SPF模块功率
        hwTrunkOperstatus160 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.160')#Eth-Trunk(GE1/0/49)端口状态
        hwTrunkOperstatus161 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.161')#Eth-Trunk(GE2/0/49)端口状态

        if( int(hwEntityTemperature1) < self.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPowerThreshold1) > self.hwEntityOpticalTxPowerThreshold and
            int(hwEntityOpticalTxPowerThreshold2) > self.hwEntityOpticalTxPowerThreshold and
            int(hwEntityFanState1) == 1 and
            int(hwTrunkOperstatus160) == 1 and int(hwTrunkOperstatus161) == 1
          ):
            globalStatus = 'ok'
        else:
            globalStatus = 'fault'

        return ['HW_BL_PUB1F',globalStatus,
                    {
                    '1.MPU温度':hwEntityTemperature1,
                    '2.风扇状态':hwEntityFanState1,
                    '3.SPF功率':hwEntityOpticalTxPowerThreshold1+','+hwEntityOpticalTxPowerThreshold2,
                    '4.EthTrunk':hwTrunkOperstatus160+','+hwTrunkOperstatus161
                    }
                ]

    def getHW_BL_PUB3F(self):
        '''
        #OFFICE-PUB3F
        #S5700-52P,双机双光口上行链路单堆叠链路
        :return:
        '''
        address = '10.15.0.63'
        hwEntityTemperature1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67371017')#MPU 1温度
        hwEntityTemperature2 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67633161')#MPU 2温度
        hwEntityOpticalTxPowerThreshold1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67570766')#GE1/0/49 SPF模块功率
        hwEntityOpticalTxPowerThreshold2 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67832910')#GE2/0/49 SPF模块功率
        hwEntityFanState1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.0')#MPU 1风扇状态
        hwEntityFanState2 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.0')#MPU 2风扇状态
        hwTrunkOperstatus55 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.55')#Eth-Trunk(GE1/0/49)端口状态
        hwTrunkOperstatus107 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.107')#Eth-Trunk(GE2/0/49)端口状态
        hwStackPortStatus10 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.1.0')#Stack(GE1/0/51)端口状态
        hwStackPortStatus11 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.1.1')#Stack(GE2/0/52)端口状态
        hwStackPortStatus20 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.2.0')#Stack(GE1/0/52)端口状态
        hwStackPortStatus21 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.2.1')#Stack(GE2/0/51)端口状态

        if( int(hwEntityTemperature1) < self.hwSwitchTemperatureThreshold and
            int(hwEntityTemperature2) < self.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPowerThreshold1) > self.hwEntityOpticalTxPowerThreshold and
            int(hwEntityOpticalTxPowerThreshold2) > self.hwEntityOpticalTxPowerThreshold and
            int(hwEntityFanState1) == 1 and int(hwEntityFanState2) == 1 and
            int(hwTrunkOperstatus55) == 1 and int(hwTrunkOperstatus107) == 1 and
            int(hwStackPortStatus10) == 1 and int(hwStackPortStatus11) == 1 and
            int(hwStackPortStatus20) == 1 and int(hwStackPortStatus21) == 1
          ):
            globalStatus = 'ok'
        else:
            globalStatus = 'fault'

        return ['HW_BL_PUB3F',globalStatus,
                    {
                    '1.MPU温度':hwEntityTemperature1+','+hwEntityTemperature2,
                    '2.风扇状态':hwEntityFanState1+','+hwEntityFanState2,
                    '3.SPF功率':hwEntityOpticalTxPowerThreshold1+','+hwEntityOpticalTxPowerThreshold2,
                    '4.EthTrunk':hwTrunkOperstatus55+','+hwTrunkOperstatus107,
                    '5.堆叠口状态':hwStackPortStatus10+','+hwStackPortStatus11+','+hwStackPortStatus20+','+hwStackPortStatus21
                    }
                ]

    def getHW_BL_SUBFAB_1(self):
        '''
        #OFFICE-SUBFAB_1
        #S5700-52P,双机双光口上行链路单堆叠链路
        :return:
        '''
        address = '10.15.0.61'
        hwEntityTemperature1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67371017')#MPU 1温度
        hwEntityTemperature2 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67633161')#MPU 2温度
        hwEntityOpticalTxPowerThreshold1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67570766')#GE1/0/49 SPF模块功率
        hwEntityOpticalTxPowerThreshold2 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67832910')#GE2/0/49 SPF模块功率
        hwEntityFanState1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.0')#MPU 1风扇状态
        hwEntityFanState2 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.0')#MPU 2风扇状态
        hwTrunkOperstatus55 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.55')#Eth-Trunk(GE1/0/49)端口状态
        hwTrunkOperstatus107 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.107')#Eth-Trunk(GE2/0/49)端口状态
        hwStackPortStatus10 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.1.0')#Stack(GE1/0/51)端口状态
        hwStackPortStatus11 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.1.1')#Stack(GE2/0/52)端口状态
        hwStackPortStatus20 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.2.0')#Stack(GE1/0/52)端口状态
        hwStackPortStatus21 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.2.1')#Stack(GE2/0/51)端口状态

        if( int(hwEntityTemperature1) < self.hwSwitchTemperatureThreshold and
            int(hwEntityTemperature2) < self.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPowerThreshold1) > self.hwEntityOpticalTxPowerThreshold and
            int(hwEntityOpticalTxPowerThreshold2) > self.hwEntityOpticalTxPowerThreshold and
            int(hwEntityFanState1) == 1 and int(hwEntityFanState2) == 1 and
            int(hwTrunkOperstatus55) == 1 and int(hwTrunkOperstatus107) == 1 and
            int(hwStackPortStatus10) == 1 and int(hwStackPortStatus11) == 1 and
            int(hwStackPortStatus20) == 1 and int(hwStackPortStatus21) == 1
          ):
            globalStatus = 'ok'
        else:
            globalStatus = 'fault'

        return ['HW_BL_SUBFAB_1',globalStatus,
                    {
                    '1.MPU温度':hwEntityTemperature1+','+hwEntityTemperature2,
                    '2.风扇状态':hwEntityFanState1+','+hwEntityFanState2,
                    '3.SPF功率':hwEntityOpticalTxPowerThreshold1+','+hwEntityOpticalTxPowerThreshold2,
                    '4.EthTrunk':hwTrunkOperstatus55+','+hwTrunkOperstatus107,
                    '5.堆叠口状态':hwStackPortStatus10+','+hwStackPortStatus11+','+hwStackPortStatus20+','+hwStackPortStatus21
                    }
                ]

    def getHW_BL_SUBFAB_2(self):
        '''
        #OFFICE-SUBFAB_2
        #S5700-52P,双机双光口上行链路单堆叠链路
        :return:
        '''
        address = '10.15.0.62'
        hwEntityTemperature1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67371017')#MPU 1温度
        hwEntityTemperature2 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67633161')#MPU 2温度
        hwEntityOpticalTxPowerThreshold1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67570766')#GE1/0/49 SPF模块功率
        hwEntityOpticalTxPowerThreshold2 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67832910')#GE2/0/49 SPF模块功率
        hwEntityFanState1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.0')#MPU 1风扇状态
        hwEntityFanState2 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.0')#MPU 2风扇状态
        hwTrunkOperstatus55 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.55')#Eth-Trunk(GE1/0/49)端口状态
        hwTrunkOperstatus107 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.107')#Eth-Trunk(GE2/0/49)端口状态
        hwStackPortStatus10 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.1.0')#Stack(GE1/0/51)端口状态
        hwStackPortStatus11 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.1.1')#Stack(GE2/0/52)端口状态
        hwStackPortStatus20 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.2.0')#Stack(GE1/0/52)端口状态
        hwStackPortStatus21 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.2.1')#Stack(GE2/0/51)端口状态

        if( int(hwEntityTemperature1) < self.hwSwitchTemperatureThreshold and
            int(hwEntityTemperature2) < self.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPowerThreshold1) > self.hwEntityOpticalTxPowerThreshold and
            int(hwEntityOpticalTxPowerThreshold2) > self.hwEntityOpticalTxPowerThreshold and
            int(hwEntityFanState1) == 1 and int(hwEntityFanState2) == 1 and
            int(hwTrunkOperstatus55) == 1 and int(hwTrunkOperstatus107) == 1 and
            int(hwStackPortStatus10) == 1 and int(hwStackPortStatus11) == 1 and
            int(hwStackPortStatus20) == 1 and int(hwStackPortStatus21) == 1
          ):
            globalStatus = 'ok'
        else:
            globalStatus = 'fault'

        return ['HW_BL_SUBFAB_2',globalStatus,
                    {
                    '1.MPU温度':hwEntityTemperature1+','+hwEntityTemperature2,
                    '2.风扇状态':hwEntityFanState1+','+hwEntityFanState2,
                    '3.SPF功率':hwEntityOpticalTxPowerThreshold1+','+hwEntityOpticalTxPowerThreshold2,
                    '4.EthTrunk':hwTrunkOperstatus55+','+hwTrunkOperstatus107,
                    '5.堆叠口状态':hwStackPortStatus10+','+hwStackPortStatus11+','+hwStackPortStatus20+','+hwStackPortStatus21
                    }
                ]

    def getHW_BL_AGG(self):
        '''
        北仑汇聚层交换机
        S5700HI 双机堆叠
        :return:返回包含主机名、全局状态及关键项状态的数据字典
        '''
        address = '10.15.2.254'
        hwEntityTemperature1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.68157449') #MPU 1温度
        hwEntityTemperature2 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.69206025') #MPU 2温度
        hwEntityFanState10 =self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.0')#MPU 10风扇状态
        hwEntityFanState11 =self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.1')#MPU 11风扇状态
        hwEntityFanState12 =self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.2')#MPU 12风扇状态
        hwEntityFanState13 =self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.3')#MPU 13风扇状态
        hwEntityFanState14 =self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.4')#MPU 14风扇状态
        hwEntityFanState20 =self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.0')#MPU 20风扇状态
        hwEntityFanState21 =self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.1')#MPU 21风扇状态
        hwEntityFanState22 =self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.2')#MPU 22风扇状态
        hwEntityFanState23 =self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.3')#MPU 23风扇状态
        hwEntityFanState24 =self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.4')#MPU 24风扇状态
        hwStackPortStatus10 =self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.1.0')#Stack(XGE1/0/3)端口状态
        hwStackPortStatus11 =self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.1.1')#Stack(XGE2/0/4)端口状态
        hwStackPortStatus20 =self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.2.0')#Stack(XGE1/0/4)端口状态
        hwStackPortStatus21 =self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.2.1')#Stack(XGE2/0/3)端口状态


        if( int(hwEntityTemperature1) < self.hwSwitchTemperatureThreshold and
            int(hwEntityTemperature2) < self.hwSwitchTemperatureThreshold and
            int(hwEntityFanState10) == 1 and int(hwEntityFanState11) == 1 and
            int(hwEntityFanState12) == 1 and int(hwEntityFanState13) == 1 and
            int(hwEntityFanState14) == 1 and int(hwEntityFanState20) == 1 and
            int(hwEntityFanState21) == 1 and int(hwEntityFanState22) == 1 and
            int(hwEntityFanState23) == 1 and int(hwEntityFanState24) == 1 and
            int(hwStackPortStatus10) == 1 and int(hwStackPortStatus11) == 1 and
            int(hwStackPortStatus20) == 1 and int(hwStackPortStatus21) == 1
          ):
            globalStatus = 'ok'
        else:
            globalStatus = 'fault'

        return ['HW_BL_AGG',globalStatus,
                    {
                    '1.MPU温度':hwEntityTemperature1+','+hwEntityTemperature2,
                    '2.风扇状态':hwEntityFanState10+','+hwEntityFanState11+','+hwEntityFanState12+','+hwEntityFanState13+','+hwEntityFanState14+','+hwEntityFanState20+','+hwEntityFanState21+','+hwEntityFanState22+','+hwEntityFanState23+','+hwEntityFanState24,
                    '3.堆叠口状态':hwStackPortStatus10+','+hwStackPortStatus11+','+hwStackPortStatus21+','+hwStackPortStatus21
                    }
                ]

    def getHW_BL_CORE(self):
        '''
        #CORE
        #S7700 CSS双机虚拟化
        :return:返回包含主机名、全局状态及关键项状态的数据字典
        '''
        address = '10.15.0.254'
        hwEntityTemperature11 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.68943881')#MPU 11温度
        hwEntityTemperature12 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.69206025')#MPU 12温度
        hwEntityTemperature21 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.69206025')#MPU 21温度
        hwEntityTemperature22 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.136314889')#MPU 22温度
        hwEntityFanState300 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.30.1')#MPU 00风扇状态
        hwEntityFanState301 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.30.2')#MPU 01风扇状态
        hwEntityFanState311 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.31.1')#MPU 11风扇状态
        hwEntityFanState312 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.31.2')#MPU 12风扇状态
        hwEntityFanState321 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.32.1')#MPU 21风扇状态
        hwEntityFanState322 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.32.2')#MPU 22风扇状态
        hwEntityFanState331 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.33.1')#MPU 31风扇状态
        hwEntityFanState332 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.33.2')#MPU 32风扇状态
        hwTrunkOperstatus240 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.5.240')#Eth-Trunk(GE 1/6/0/6)端口状态
        hwTrunkOperstatus423 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.5.423')#Eth-Trunk(GE 2/6/0/6)端口状态
        hwTrunkOperstatus10 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.6.10')#Eth-Trunk(GE 1/6/0/7)端口状态
        hwTrunkOperstatus298 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.6.298')#Eth-Trunk(GE 2/6/0/7)端口状态
        ifOperStatus241 = self.getSnmpValue(address, '.1.3.6.1.2.1.2.2.1.8.241')#Eth-Trunk(XGE 1/6/0/7) For刀片交换机 Left198 TE1/0/1 非Eth-Trunk
        ifOperStatus424 = self.getSnmpValue(address, '.1.3.6.1.2.1.2.2.1.8.424')#Eth-Trunk(XGE 2/6/0/7) For刀片交换机 Right199 TE1/0/1 非Eth-Trunk
        ifOperStatus242 = self.getSnmpValue(address, '.1.3.6.1.2.1.2.2.1.8.242')#Eth-Trunk(XGE 1/6/0/8)端口状态 ForCSS
        ifOperStatus243 = self.getSnmpValue(address, '.1.3.6.1.2.1.2.2.1.8.243')#Eth-Trunk(XGE 2/6/0/8)端口状态 ForCSS
        ifOperStatus244 = self.getSnmpValue(address, '.1.3.6.1.2.1.2.2.1.8.244')#Eth-Trunk(XGE 1/6/0/9)端口状态 ForCSS
        ifOperStatus245 = self.getSnmpValue(address, '.1.3.6.1.2.1.2.2.1.8.245')#Eth-Trunk(XGE 2/6/0/9)端口状态 ForCSS
        ifOperStatus425 = self.getSnmpValue(address, '.1.3.6.1.2.1.2.2.1.8.425')#Eth-Trunk(XGE 1/6/0/10)端口状态 ForCSS
        ifOperStatus426 = self.getSnmpValue(address, '.1.3.6.1.2.1.2.2.1.8.426')#Eth-Trunk(XGE 2/6/0/11)端口状态 ForCSS
        ifOperStatus427 = self.getSnmpValue(address, '.1.3.6.1.2.1.2.2.1.8.427')#Eth-Trunk(XGE 1/6/0/12)端口状态 ForCSS
        ifOperStatus428 = self.getSnmpValue(address, '.1.3.6.1.2.1.2.2.1.8.428')#Eth-Trunk(XGE 2/6/0/13)端口状态 ForCSS

        if( int(hwEntityTemperature11) < self.hwSwitchTemperatureThreshold and
            int(hwEntityTemperature12) < self.hwSwitchTemperatureThreshold and
            int(hwEntityTemperature21) < self.hwSwitchTemperatureThreshold and
            int(hwEntityTemperature22) < self.hwSwitchTemperatureThreshold and
            int(hwEntityFanState300) == 1 and int(hwEntityFanState301) == 1 and
            int(hwEntityFanState311) == 1 and int(hwEntityFanState312) == 1 and
            int(hwEntityFanState321) == 1 and int(hwEntityFanState322) == 1 and
            int(hwEntityFanState331) == 1 and int(hwEntityFanState332) == 1 and
            int(hwTrunkOperstatus240) == 1 and int(hwTrunkOperstatus423) == 1 and
            int(hwTrunkOperstatus10) == 1 and int(hwTrunkOperstatus298) == 1 and
            int(ifOperStatus241) == 1 and int(ifOperStatus424) == 1 and
            int(ifOperStatus242) == 1 and int(ifOperStatus243) == 1 and
            int(ifOperStatus244) == 1 and int(ifOperStatus245) == 1 and
            int(ifOperStatus425) == 1 and int(ifOperStatus426) == 1 and
            int(ifOperStatus427) == 1 and int(ifOperStatus428) == 1
          ):
            globalStatus = 'ok'
        else:
            globalStatus = 'fault'

        return ['HW_FH_CORE',globalStatus,
                    {
                    '1.MPU温度':hwEntityTemperature11+','+hwEntityTemperature12+','+hwEntityTemperature21+','+hwEntityTemperature22,
                    '2.风扇状态':hwEntityFanState300+','+hwEntityFanState301+','+hwEntityFanState311+','+hwEntityFanState312+','+hwEntityFanState321+','+hwEntityFanState322+','+hwEntityFanState331+','+hwEntityFanState332,
                    '3.EthTrunk':hwTrunkOperstatus240+','+hwTrunkOperstatus423+','+hwTrunkOperstatus10+','+hwTrunkOperstatus298,
                    '4.虚拟口状态':ifOperStatus241+','+ifOperStatus424+','+ifOperStatus242+','+','+ifOperStatus243+','+ifOperStatus244+','+ifOperStatus245+','+ifOperStatus425+','+ifOperStatus426+','+ifOperStatus427+','+ifOperStatus428
                    }
                ]

    def getHW_FH_AGG(self):
        '''
        奉化汇聚层交换机
        S5700HI 双机堆叠
        :return:返回包含主机名、全局状态及关键项状态的数据字典
        '''
        address = '10.15.255.254'
        hwEntityTemperature1 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.68157449') #MPU 1温度
        hwEntityTemperature2 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.69206025') #MPU 2温度
        hwEntityFanState10 =self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.0')#MPU 10风扇状态
        hwEntityFanState11 =self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.1')#MPU 11风扇状态
        hwEntityFanState12 =self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.2')#MPU 12风扇状态
        hwEntityFanState13 =self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.3')#MPU 13风扇状态
        hwEntityFanState14 =self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.4')#MPU 14风扇状态
        hwEntityFanState20 =self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.0')#MPU 20风扇状态
        hwEntityFanState21 =self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.1')#MPU 21风扇状态
        hwEntityFanState22 =self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.2')#MPU 22风扇状态
        hwEntityFanState23 =self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.3')#MPU 23风扇状态
        hwEntityFanState24 =self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.4')#MPU 24风扇状态
        hwStackPortStatus10 =self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.1.0')#Stack(XGE1/0/3)端口状态
        hwStackPortStatus11 =self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.1.1')#Stack(XGE2/0/4)端口状态
        hwStackPortStatus20 =self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.2.0')#Stack(XGE1/0/4)端口状态
        hwStackPortStatus21 =self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.2.1')#Stack(XGE2/0/3)端口状态


        if( int(hwEntityTemperature1) < self.hwSwitchTemperatureThreshold and
            int(hwEntityTemperature2) < self.hwSwitchTemperatureThreshold and
            int(hwEntityFanState10) == 1 and int(hwEntityFanState11) == 1 and
            int(hwEntityFanState12) == 1 and int(hwEntityFanState13) == 1 and
            int(hwEntityFanState14) == 1 and int(hwEntityFanState20) == 1 and
            int(hwEntityFanState21) == 1 and int(hwEntityFanState22) == 1 and
            int(hwEntityFanState23) == 1 and int(hwEntityFanState24) == 1 and
            int(hwStackPortStatus10) == 1 and int(hwStackPortStatus11) == 1 and
            int(hwStackPortStatus20) == 1 and int(hwStackPortStatus21) == 1
          ):
            globalStatus = 'ok'
        else:
            globalStatus = 'fault'

        return ['HW_FH_AGG',globalStatus,
                    {
                    '1.MPU温度':hwEntityTemperature1+','+hwEntityTemperature2,
                    '2.风扇状态':hwEntityFanState10+','+hwEntityFanState11+','+hwEntityFanState12+','+hwEntityFanState13+','+hwEntityFanState14+','+hwEntityFanState20+','+hwEntityFanState21+','+hwEntityFanState22+','+hwEntityFanState23+','+hwEntityFanState24,
                    '3.堆叠口状态':hwStackPortStatus10+','+hwStackPortStatus11+','+hwStackPortStatus21+','+hwStackPortStatus21
                    }
                ]

    def getHW_FH_AC1(self):
        '''
        FH AC-1 活动主机
        :return:返回包含主机名、全局状态及关键项状态的数据字典
        '''
        address = '10.15.253.251'
        #MPU 温度
        hwEntityTemperature = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.9') #CPU温度
        #Eth-Trunk端口状态 GE0/0/1
        hwTrunkOperstatus3 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.3')
        #Eth-Trunk端口状态 GE0/0/2
        hwTrunkOperstatus4 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.4')
        hwWlanCurJointApNum = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.6.139.12.1.2.1.0') #在线AP数量
        hwWlanCurAuthSuccessStaNum = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.6.139.12.1.2.3.0') #在线终端数
        hwWlanRfComplianceRate = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.6.139.12.1.4.6.0') #射频总体达标率
        hwWlanApComplianceRate = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.6.139.12.1.5.5.0') #AP总体达标率
        hwWlanStaComplianceRate = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.6.139.12.1.3.5.0') #终端总体达标率
        hwStaGlobalWirelessPacketDropRate = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.6.139.12.1.3.17.0') #终端平均丢包率

        '''
        AC1活动主机正常状态数据
        1.      MPU温度:39
        2.    EthTrunk:1,1
        3.   在线AP数量:23
        4.   在线终端数:103
        5.射频总体达标率:93
        6.  AP总体达标率:92
        7.终端总体达标率:66
        8.终端平均丢包率:0
        '''

        if( int(hwEntityTemperature) < self.hwSwitchTemperatureThreshold and
            int(hwTrunkOperstatus3) == 1 and
            int(hwTrunkOperstatus4) == 1 and
            #int(hwStaGlobalWirelessPacketDropRate) < int(self.hwStaGlobalWirelessPacketDropRateThreshold) and #终端丢包率
            int(hwWlanStaComplianceRate) > int(self.hwWlanStaComplianceRateThreshold) and #终端达成率
            int(hwWlanApComplianceRate) > int(self.hwWlanApComplianceRateThreshold) and #AP达成率
            int(hwWlanRfComplianceRate) > int(self.hwWlanRfComplianceRateThreshold) and #射频达成率
            int(hwWlanCurJointApNum) == int(self.hwWlanCurJointApNumThreshold) #在线AP数

          ):
            globalStatus = 'ok'
        else:
            globalStatus = 'fault'

        return ['HW_FH_AC1',globalStatus,
                    {
                    '1.MPU温度':hwEntityTemperature,
                    '2.EthTrunk':hwTrunkOperstatus3+','+hwTrunkOperstatus4,
                    '3.在线AP数量':hwWlanCurJointApNum,
                    '4.在线终端数':hwWlanCurAuthSuccessStaNum,
                    '5.射频总体达标率':hwWlanRfComplianceRate,
                    '6.AP总体达标率':hwWlanApComplianceRate,
                    '7.终端总体达标率':hwWlanStaComplianceRate
                    #'8.终端平均丢包率':hwStaGlobalWirelessPacketDropRate
                    }
                ]

    def getHW_FH_AC2(self):
        '''
        FH AC-2 备机主机
        :return:返回包含主机名、全局状态及关键项状态的数据字典
        '''
        address = '10.15.253.252'
        #MPU 温度
        hwEntityTemperature = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.9') #CPU温度
        #Eth-Trunk端口状态 GE0/0/1
        hwTrunkOperstatus3 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.3')
        #Eth-Trunk端口状态 GE0/0/2
        hwTrunkOperstatus4 = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.4')
        hwWlanCurJointApNum = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.6.139.12.1.2.1.0') #在线AP数量
        hwWlanCurAuthSuccessStaNum = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.6.139.12.1.2.3.0') #在线终端数
        hwWlanRfComplianceRate = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.6.139.12.1.4.6.0') #射频总体达标率
        hwWlanApComplianceRate = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.6.139.12.1.5.5.0') #AP总体达标率
        hwWlanStaComplianceRate = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.6.139.12.1.3.5.0') #终端总体达标率
        hwStaGlobalWirelessPacketDropRate = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.6.139.12.1.3.17.0') #终端平均丢包率

        '''
        AC2备机正常状态数据
        1.      MPU温度:39
        2.    EthTrunk:1,1
        3.   在线AP数量:23
        4.   在线终端数:103
        5.射频总体达标率:255
        6.  AP总体达标率:44
        7.终端总体达标率:255
        8.终端平均丢包率:4294967295
        '''

        if( int(hwEntityTemperature) < self.hwSwitchTemperatureThreshold and
            int(hwTrunkOperstatus3) == 1 and
            int(hwTrunkOperstatus4) == 1
          ):
            globalStatus = 'ok'
        else:
            globalStatus = 'fault'

        return ['HW_FH_AC2',globalStatus,
                    {
                    '1.MPU温度':hwEntityTemperature,
                    '2.EthTrunk':hwTrunkOperstatus3+','+hwTrunkOperstatus4,
                    '3.在线AP数量':hwWlanCurJointApNum,
                    '4.在线终端数':hwWlanCurAuthSuccessStaNum,
                    '5.射频总体达标率':hwWlanRfComplianceRate,
                    '6.AP总体达标率':hwWlanApComplianceRate,
                    '7.终端总体达标率':hwWlanStaComplianceRate,
                    '8.终端平均丢包率':hwStaGlobalWirelessPacketDropRate
                    }
                ]

    def getHW_FH_Router(self):
        '''
        路由器
        :return:返回包含主机名、全局状态及关键项状态的数据字典
        '''
        address = '10.15.255.250'
        hwEntityTemperature = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.9')#MPU 温度
        hwEntityFanState1 = self.getSnmpValue(address,'1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.0.1')#hwEntityFanState1
        hwEntityFanState2 = self.getSnmpValue(address,'1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.0.2')#hwEntityFanState2
        hwEntityFanState3 = self.getSnmpValue(address,'1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.0.3')#hwEntityFanState3
        ifOperStatus4 = self.getSnmpValue(address,'.1.3.6.1.2.1.2.2.1.8.4')#端口(GE0/0/1)状态 to FH LJ-1
        ifOperStatus5 = self.getSnmpValue(address,'.1.3.6.1.2.1.2.2.1.8.5')#端口(GE0/0/2)状态 to NB BL

        if( int(hwEntityTemperature) < self.hwRouterTemperatureThreshold and
            int(hwEntityFanState1) == 1 and
            int(hwEntityFanState2) == 1 and
            int(hwEntityFanState3) == 1 and
            int(ifOperStatus4) == 1 and
            int(ifOperStatus5) == 1
          ):
            globalStatus = 'ok'
        else:
            globalStatus = 'fault'

        return ['HW_FH_Router',globalStatus,
                    {
                    '1.MPU温度':hwEntityTemperature,
                    '2.风扇状态':hwEntityFanState1+','+hwEntityFanState2+','+hwEntityFanState3,
                    '3.端口(To奉化连接)':ifOperStatus4,
                    '4.端口(To北仑连接)':ifOperStatus5
                    }
                ]

    def getHW_FH_LJ_1(self):
        '''
        连接交换机,#S5700-28P,单机双电口上行链路
        :return:返回包含主机名、全局状态及关键项状态的数据字典
        '''
        address = '10.15.255.253'
        hwEntityTemperature = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67108873')#MPU 温度
        hwTrunkOperstatus5 = self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.5')#Eth-Trunk端口状态 GE0/0/1
        hwTrunkOperstatus6 =self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.6')#Eth-Trunk端口状态 GE0/0/2

        if( int(hwEntityTemperature) < self.hwSwitchTemperatureThreshold and
            int(hwTrunkOperstatus5) == 1 and
            int(hwTrunkOperstatus6) == 1 ):
            globalStatus = 'ok'
        else:
            globalStatus = 'fault'

        return ['HW_FH_LJ_1',globalStatus,
                    {
                    '1.MPU温度':hwEntityTemperature,
                    '2.EthTrunk':hwTrunkOperstatus5+','+hwTrunkOperstatus6
                    }
                ]

    def getHW_FH_1_S1(self):
        '''
        S5700-10P-PWR
        10.15.255.11 单机双上行
        :return:
        '''
        address = '10.15.255.11'
        hwEntityTemperature = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67108873')#MPU 温度
        hwEntityOpticalTxPower1 = self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67306062')#GE0/0/9 单模SPF模块功率
        hwEntityOpticalTxPower2 = self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67306126')#EGE0/0/10 单模SPF模块功率
        hwTrunkOperstatus15 = self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.15')#Eth-Trunk端口状态 GE0/0/9
        hwTrunkOperstatus16 = self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.16')#Eth-Trunk端口状态 GE0/0/10

        if( int(hwEntityTemperature) < self.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPower1) >self.hwEntitySOpticalTxPowerThreshold and
            int(hwEntityOpticalTxPower2) > self.hwEntitySOpticalTxPowerThreshold and
            int(hwTrunkOperstatus15) == 1 and int(hwTrunkOperstatus16) == 1 ):
            globalStatus = 'ok'
        else:
            globalStatus = 'fault'

        return ['HW_FH_1#S1',globalStatus,
                    {
                    '1.MPU温度':hwEntityTemperature,
                    '2.EthTrunk':hwTrunkOperstatus15+','+hwTrunkOperstatus16,
                    '3.SPF功率':hwEntityOpticalTxPower1+','+hwEntityOpticalTxPower2
                    }
                ]

    def getHW_FH_1_S2(self):
        '''
        S5700-10P-PWR
        10.15.255.12 单机双上行
        :return:
        '''
        address = '10.15.255.12'
        hwEntityTemperature = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67108873')#MPU 温度
        hwEntityOpticalTxPower1 = self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67306062')#GE0/0/9 单模SPF模块功率
        hwEntityOpticalTxPower2 = self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67306126')#EGE0/0/10 单模SPF模块功率
        hwTrunkOperstatus15 = self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.15')#Eth-Trunk端口状态 GE0/0/9
        hwTrunkOperstatus16 = self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.16')#Eth-Trunk端口状态 GE0/0/10

        if( int(hwEntityTemperature) < self.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPower1) >self.hwEntitySOpticalTxPowerThreshold and
            int(hwEntityOpticalTxPower2) > self.hwEntitySOpticalTxPowerThreshold and
            int(hwTrunkOperstatus15) == 1 and int(hwTrunkOperstatus16) == 1 ):
            globalStatus = 'ok'
        else:
            globalStatus = 'fault'

        return ['HW_FH_1#S2',globalStatus,
                    {
                    '1.MPU温度':hwEntityTemperature,
                    '2.EthTrunk':hwTrunkOperstatus15+','+hwTrunkOperstatus16,
                    '3.SPF功率':hwEntityOpticalTxPower1+','+hwEntityOpticalTxPower2
                    }
                ]

    def getHW_FH_1_S3(self):
        '''
        S5700-10P-PWR
        10.15.255.13 单机双上行
        :return:
        '''
        address = '10.15.255.13'
        hwEntityTemperature = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67108873')#MPU 温度
        hwEntityOpticalTxPower1 = self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67306062')#GE0/0/9 单模SPF模块功率
        hwEntityOpticalTxPower2 = self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67306126')#EGE0/0/10 单模SPF模块功率
        hwTrunkOperstatus15 = self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.15')#Eth-Trunk端口状态 GE0/0/9
        hwTrunkOperstatus16 = self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.16')#Eth-Trunk端口状态 GE0/0/10

        if( int(hwEntityTemperature) < self.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPower1) >self.hwEntitySOpticalTxPowerThreshold and
            int(hwEntityOpticalTxPower2) > self.hwEntitySOpticalTxPowerThreshold and
            int(hwTrunkOperstatus15) == 1 and int(hwTrunkOperstatus16) == 1 ):
            globalStatus = 'ok'
        else:
            globalStatus = 'fault'

        return ['HW_FH_1#S3',globalStatus,
                    {
                    '1.MPU温度':hwEntityTemperature,
                    '2.EthTrunk':hwTrunkOperstatus15+','+hwTrunkOperstatus16,
                    '3.SPF功率':hwEntityOpticalTxPower1+','+hwEntityOpticalTxPower2
                    }
                ]

    def getHW_FH_1_S4(self):
        '''
        S5700-10P-PWR
        10.15.255.14 单机双上行
        :return:
        '''
        address = '10.15.255.14'
        hwEntityTemperature = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67108873')#MPU 温度
        hwEntityOpticalTxPower1 = self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67306062')#GE0/0/9 单模SPF模块功率
        hwEntityOpticalTxPower2 = self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67306126')#EGE0/0/10 单模SPF模块功率
        hwTrunkOperstatus15 = self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.15')#Eth-Trunk端口状态 GE0/0/9
        hwTrunkOperstatus16 = self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.16')#Eth-Trunk端口状态 GE0/0/10

        if( int(hwEntityTemperature) < self.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPower1) >self.hwEntitySOpticalTxPowerThreshold and
            int(hwEntityOpticalTxPower2) > self.hwEntitySOpticalTxPowerThreshold and
            int(hwTrunkOperstatus15) == 1 and int(hwTrunkOperstatus16) == 1 ):
            globalStatus = 'ok'
        else:
            globalStatus = 'fault'

        return ['HW_FH_1#S4',globalStatus,
                    {
                    '1.MPU温度':hwEntityTemperature,
                    '2.EthTrunk':hwTrunkOperstatus15+','+hwTrunkOperstatus16,
                    '3.SPF功率':hwEntityOpticalTxPower1+','+hwEntityOpticalTxPower2
                    }
                ]

    def getHW_FH_1_S5(self):
        '''
        S5700-10P-PWR
        10.15.255.15 单机双上行
        :return:
        '''
        address = '10.15.255.15'
        hwEntityTemperature = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67108873')#MPU 温度
        hwEntityOpticalTxPower1 = self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67306062')#GE0/0/9 单模SPF模块功率
        hwEntityOpticalTxPower2 = self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67306126')#EGE0/0/10 单模SPF模块功率
        hwTrunkOperstatus13 = self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.13')#Eth-Trunk端口状态 GE0/0/9
        hwTrunkOperstatus14 = self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.14')#Eth-Trunk端口状态 GE0/0/10

        if( int(hwEntityTemperature) < self.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPower1) >self.hwEntitySOpticalTxPowerThreshold and
            int(hwEntityOpticalTxPower2) > self.hwEntitySOpticalTxPowerThreshold and
            int(hwTrunkOperstatus13) == 1 and int(hwTrunkOperstatus14) == 1 ):
            globalStatus = 'ok'
        else:
            globalStatus = 'fault'

        return ['HW_FH_1#S5',globalStatus,
                    {
                    '1.MPU温度':hwEntityTemperature,
                    '2.EthTrunk':hwTrunkOperstatus13+','+hwTrunkOperstatus14,
                    '3.SPF功率':hwEntityOpticalTxPower1+','+hwEntityOpticalTxPower2
                    }
                ]

    def getHW_FH_3_S1(self):
        '''
        S5700-10P-PWR
        10.15.255.31 单机双上行
        :return:
        '''
        address = '10.15.255.31'
        hwEntityTemperature = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67108873')#MPU 温度
        hwEntityOpticalTxPower1 = self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67306062')#GE0/0/9 单模SPF模块功率
        hwEntityOpticalTxPower2 = self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67306126')#EGE0/0/10 单模SPF模块功率
        hwTrunkOperstatus15 = self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.15')#Eth-Trunk端口状态 GE0/0/9
        hwTrunkOperstatus16 = self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.16')#Eth-Trunk端口状态 GE0/0/10

        if( int(hwEntityTemperature) < self.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPower1) >self.hwEntitySOpticalTxPowerThreshold and
            int(hwEntityOpticalTxPower2) > self.hwEntitySOpticalTxPowerThreshold and
            int(hwTrunkOperstatus15) == 1 and int(hwTrunkOperstatus16) == 1 ):
            globalStatus = 'ok'
        else:
            globalStatus = 'fault'

        return ['HW_FH_3#S1',globalStatus,
                    {
                    '1.MPU温度':hwEntityTemperature,
                    '2.EthTrunk':hwTrunkOperstatus15+','+hwTrunkOperstatus16,
                    '3.SPF功率':hwEntityOpticalTxPower1+','+hwEntityOpticalTxPower2
                    }
                ]

    def getHW_FH_3_S2(self):
        '''
        S5700-10P-PWR
        10.15.255.32 单机双上行
        :return:
        '''
        address = '10.15.255.32'
        hwEntityTemperature = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67108873')#MPU 温度
        hwEntityOpticalTxPower1 = self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67306062')#GE0/0/9 单模SPF模块功率
        hwEntityOpticalTxPower2 = self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67306126')#EGE0/0/10 单模SPF模块功率
        hwTrunkOperstatus15 = self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.15')#Eth-Trunk端口状态 GE0/0/9
        hwTrunkOperstatus16 = self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.16')#Eth-Trunk端口状态 GE0/0/10

        if( int(hwEntityTemperature) < self.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPower1) >self.hwEntitySOpticalTxPowerThreshold and
            int(hwEntityOpticalTxPower2) > self.hwEntitySOpticalTxPowerThreshold and
            int(hwTrunkOperstatus15) == 1 and int(hwTrunkOperstatus16) == 1 ):
            globalStatus = 'ok'
        else:
            globalStatus = 'fault'

        return ['HW_FH_3#S2',globalStatus,
                    {
                    '1.MPU温度':hwEntityTemperature,
                    '2.EthTrunk':hwTrunkOperstatus15+','+hwTrunkOperstatus16,
                    '3.SPF功率':hwEntityOpticalTxPower1+','+hwEntityOpticalTxPower2
                    }
                ]

    def getHW_FH_ZHZFang(self):
        '''
        S5700-10P-PWR 综合站房
        10.15.255.16 单机双上行
        :return:
        '''
        address = '10.15.255.16'
        hwEntityTemperature = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67108873')#MPU 温度
        hwEntityOpticalTxPower1 = self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67306062')#GE0/0/9 单模SPF模块功率
        hwTrunkOperstatus13 = self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.13')#Eth-Trunk端口状态 GE0/0/9

        if( int(hwEntityTemperature) < self.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPower1) >self.hwEntitySOpticalTxPowerThreshold and
            int(hwTrunkOperstatus13) == 1 and int(hwTrunkOperstatus13) == 1 ):
            globalStatus = 'ok'
        else:
            globalStatus = 'fault'

        return ['HW_FH_ZHZFang',globalStatus,
                    {
                    '1.MPU温度':hwEntityTemperature,
                    '2.EthTrunk':hwTrunkOperstatus13,
                    '3.SPF功率':hwEntityOpticalTxPower1
                    }
                ]

    def getHW_FH_BATing(self):
        '''
        S5700-10P-PWR 保安亭子
        10.15.255.113 单机单上行
        :return:
        '''
        address = '10.15.255.113'
        hwEntityTemperature = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67108873')#MPU 温度
        hwEntityOpticalTxPower1 = self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67305550')#GE0/0/1 单模SPF模块功率
        hwTrunkOperstatus1 = self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.31')#Eth-Trunk端口状态 GE0/0/1

        if( int(hwEntityTemperature) < self.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPower1) > -700 and  #-dBM，正常值-502
            int(hwTrunkOperstatus1) == 1 ):
            globalStatus = 'ok'
            hwEntityOpticalTxPower1 += '(ok)'
        else:
            globalStatus = 'fault'
            hwEntityOpticalTxPower1 += '(fault)'

        return ['HW_FH_BATing',globalStatus,
                    {
                    '1.MPU温度':hwEntityTemperature,
                    '2.EthTrunk':hwTrunkOperstatus1,
                    '3.SPF功率':hwEntityOpticalTxPower1
                    }
                ]

    def getHW_FH_STang(self):
        '''
        S5700-10P-PWR 食堂
        10.15.255.111 单机单上行
        :return:
        '''
        address = '10.15.255.111'
        hwEntityTemperature = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67108873')#MPU 温度
        hwEntityOpticalTxPower1 = self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67305550')#GE0/0/1 单模SPF模块功率
        hwTrunkOperstatus1 = self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.31')#Eth-Trunk端口状态 GE0/0/1

        if( int(hwEntityTemperature) < self.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPower1) > -700 and  #-dBM，正常值-602
            int(hwTrunkOperstatus1) == 1 ):
            globalStatus = 'ok'
            hwEntityOpticalTxPower1 += '(ok)'
        else:
            globalStatus = 'fault'
            hwEntityOpticalTxPower1 += '(fault)'

        return ['HW_FH_STang',globalStatus,
                    {
                    '1.MPU温度':hwEntityTemperature,
                    '2.EthTrunk':hwTrunkOperstatus1,
                    '3.SPF功率':hwEntityOpticalTxPower1
                    }
                ]

    def getHW_FH_SShe(self):
        '''
        S5700-10P-PWR 宿舍
        10.15.255.112 单机单上行
        :return:
        '''
        address = '10.15.255.112'
        hwEntityTemperature = self.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67108873')#MPU 温度
        hwEntityOpticalTxPower1 = self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67305550')#GE0/0/1 单模SPF模块功率
        hwTrunkOperstatus1 = self.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.31')#Eth-Trunk端口状态 GE0/0/1

        if( int(hwEntityTemperature) < self.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPower1) > -700 and  #-dBM，正常值-622
            int(hwTrunkOperstatus1) == 1 ):
            globalStatus = 'ok'
            hwEntityOpticalTxPower1 += '(ok)'
        else:
            globalStatus = 'fault'
            hwEntityOpticalTxPower1 += '(fault)'

        return ['HW_FH_SShe',globalStatus,
                    {
                    '1.MPU温度':hwEntityTemperature,
                    '2.EthTrunk':hwTrunkOperstatus1,
                    '3.SPF功率':hwEntityOpticalTxPower1
                    }
                ]

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
        TODO:陆续完善
        按IP地址或者主机名来匹配对应的主机
        :param name:按IP地址或者主机名
        :return:以字符串形式打印该设备状态状态
        '''
        #HW_FH_LJ_1
        if cmp(name,'10.15.255.253') ==0 or cmp(name,'fh-lj') ==0:
            return self.printStatus(self.getHW_FH_LJ_1())
        #
        elif cmp(name,'10.15.255.250') ==0 or cmp(name,'fh-router') ==0:
            return self.printStatus(self.getHW_FH_Router())
        elif cmp(name,'10.15.253.252') ==0 or cmp(name,'fh-ac2') ==0:
            return self.printStatus(self.getHW_FH_AC2())
        elif cmp(name,'10.15.253.251') ==0 or cmp(name,'fh-ac1') ==0:
            return self.printStatus(self.getHW_FH_AC1())
        elif cmp(name,'10.15.255.254') ==0 or cmp(name,'fh-agg') ==0:
            return self.printStatus(self.getHW_FH_AGG())
        elif cmp(name,'10.15.0.254') ==0 or cmp(name,'core') ==0:
            return self.printStatus(self.getHW_BL_CORE())
        elif cmp(name,'10.15.2.254') ==0 or cmp(name,'agg') ==0:
            return self.printStatus(self.getHW_BL_AGG())
        elif cmp(name,'10.15.0.63') ==0 or cmp(name,'pub3f') ==0:
            return self.printStatus(self.getHW_BL_PUB3F())
        elif cmp(name,'10.15.0.61') ==0 or cmp(name,'subfab-1') ==0:
            return self.printStatus(self.getHW_BL_SUBFAB_1())
        elif cmp(name,'10.15.0.62') ==0 or cmp(name,'subfab-2') ==0:
            return self.printStatus(self.getHW_BL_SUBFAB_2())
        elif cmp(name,'10.15.0.60') ==0 or cmp(name,'pub1f') ==0:
            return self.printStatus(self.getHW_BL_PUB1F())
        elif cmp(name,'10.15.2.41') ==0 or cmp(name,'off4f') ==0:
            return self.printStatus(self.getHW_BL_OFF4F())
        elif cmp(name,'10.15.2.23') ==0 or cmp(name,'off2f-3') ==0:
            return self.printStatus(self.getHW_BL_OFF2F_3())
        elif cmp(name,'10.15.2.22') ==0 or cmp(name,'off2f-2') ==0:
            return self.printStatus(self.getHW_BL_OFF2F_2())
        elif cmp(name,'10.15.2.21') ==0 or cmp(name,'off2f-1') ==0:
            return self.printStatus(self.getHW_BL_OFF2F_1())
        elif cmp(name,'10.15.2.13') ==0 or cmp(name,'off1f-3') ==0:
            return self.printStatus(self.getHW_BL_OFF1F_3())
        elif cmp(name,'10.15.2.12') ==0 or cmp(name,'off1f-2') ==0:
            return self.printStatus(self.getHW_BL_OFF1F_2())
        elif cmp(name,'10.15.2.11') ==0 or cmp(name,'off1f-1') ==0:
            return self.printStatus(self.getHW_BL_OFF1F_1())
        elif cmp(name,'10.15.2.44') ==0 or cmp(name,'damen') ==0:
            return self.printStatus(self.getHW_BL_DaMen())
        elif cmp(name,'10.15.2.42') ==0 or cmp(name,'puboff') ==0:
            return self.printStatus(self.getHW_BL_PUBOFF())
        elif cmp(name,'10.15.2.49') ==0 or cmp(name,'off4ftd') ==0:
            return self.printStatus(self.getHW_BL_OFF4FTD())
        elif cmp(name,'10.15.2.43') ==0 or cmp(name,'cub3f') ==0:
            return self.printStatus(self.getHW_BL_CUB3F())
        elif cmp(name,'10.15.0.252') ==0 or cmp(name,'lj-1') ==0:
            return self.printStatus(self.getHW_BL_LJ_1())
        elif cmp(name,'10.15.0.253') ==0 or cmp(name,'lj-2') ==0:
            return self.printStatus(self.getHW_BL_LJ_2())
        #Dell CMC
        elif cmp(name,'10.15.0.200') ==0 or cmp(name,'cmc') ==0:
             return self.printStatus(self.getDellCMC())
        #Sangfor SG
        elif cmp(name,'10.15.1.253') ==0 or cmp(name,'sg') ==0:
            return self.printStatus(self.getSangforSG())
        #360TD
        elif cmp(name,'10.15.1.251') ==0 or cmp(name,'td') ==0:
            return self.printStatus(self.get360TD())
        #HW_FH_1#S1
        elif cmp(name,'10.15.255.11') ==0 or cmp(name,'fh-1#s1') ==0:
            return self.printStatus(self.getHW_FH_1_S1())
        #HW_FH_1#S2
        elif cmp(name,'10.15.255.12') ==0 or cmp(name,'fh-1#s2') ==0:
            return self.printStatus(self.getHW_FH_1_S2())
        #HW_FH_1#S3
        elif cmp(name,'10.15.255.13') ==0 or cmp(name,'fh-1#s3') ==0:
            return self.printStatus(self.getHW_FH_1_S3())
        #HW_FH_1#S4
        elif cmp(name,'10.15.255.14') ==0 or cmp(name,'fh-1#s4') ==0:
            return self.printStatus(self.getHW_FH_1_S4())
        #HW_FH_1#S5
        elif cmp(name,'10.15.255.15') ==0 or cmp(name,'fh-1#s5') ==0:
            return self.printStatus(self.getHW_FH_1_S5())
        #HW_FH_3#S1
        elif cmp(name,'10.15.255.31') ==0 or cmp(name,'fh-3#s1') ==0:
            return self.printStatus(self.getHW_FH_3_S1())
        #HW_FH_3#S2
        elif cmp(name,'10.15.255.32') ==0 or cmp(name,'fh-3#s2') ==0:
            return self.printStatus(self.getHW_FH_3_S2())
        #HW_FH_ZHZFang
        elif cmp(name,'10.15.255.16') ==0 or cmp(name,'fh-zhzfang') ==0:
            return self.printStatus(self.getHW_FH_ZHZFang())
        #HW_FH_BATing
        elif cmp(name,'10.15.255.113') ==0 or cmp(name,'fh-bating') ==0:
            return self.printStatus(self.getHW_FH_BATing())
         #HW_FH_STang
        elif cmp(name,'10.15.255.111') ==0 or cmp(name,'fh-stang') ==0:
            return self.printStatus(self.getHW_FH_STang())
         #HW_FH_SShe
        elif cmp(name,'10.15.255.112') ==0 or cmp(name,'fh-sshe') ==0:
            return self.printStatus(self.getHW_FH_SShe())
        elif cmp(name,'help') ==0:
            helpContent='奉化:fh-agg,fh-ac1,fh-ac2,fh-router\n'+\
                        '北仑:core,agg,cmc,sg,td'
            return helpContent
        else:
            return 'NONE'

    def checkDellServer4iDRAC6(self):
        '''
        检查所有Dell iDrac6 服务器，如R710，M710HD
        :return:
        '''
        #遍历配置表中iDRAC6的服务器列表
        for hostname,ip in self.iDRAC6ServerDict.items():
            if (hostname != '__name__'):
                globalSystemStatus = self.getSnmpValue(ip, '.1.3.6.1.4.1.674.10892.2.2.1.0') #全局状态,3表示OK
                if(int(globalSystemStatus) == 3):
                    globalStatus = 'ok'
                else:
                    globalStatus = 'fault'
                    self.myWxMessage.wxMessage('\n'+hostname.upper()+'：'+globalStatus)

    def checkDellServer4iDRAC8(self):
        '''
        :param address: Dell R730/R630HD
        :return: OID信息
        '''
        for hostname,ip in self.iDRAC8ServerDict.items():
            if (hostname != '__name__'):
                globalSystemStatus = self.getSnmpValue(ip, '.1.3.6.1.4.1.674.10892.5.2.1.0') #全局状态,3表示OK
                if(int(globalSystemStatus) == 3):
                    globalStatus = 'ok'
                else:
                    globalStatus = 'fault'
                    self.myWxMessage.wxMessage('\n'+hostname.upper()+'：'+globalStatus)

    def checkAllDeviceStatus(self):
        '''
        TODO:陆续完善
        检查华为设备全局状态，当全局状态不为'ok'则发送微信通知
        :return:发送微信告警信息
        '''
        blWeather = WxWeather.WxWeather().get_2DaysWeathers()
        nowTime=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        self.myWxMessage.wxMessage(nowTime+' 机房温度:'+self.getDellCMC()[2]['1.环境温度']+'\n'+blWeather)

        #HW_FH_LJ_1
        if cmp(self.getHW_FH_LJ_1()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.getHW_FH_LJ_1()[0]+'：'+self.getHW_FH_LJ_1()[1]+'\n'+self.printStatus(self.getHW_FH_LJ_1()))

        #HW_FH_Router
        if cmp(self.getHW_FH_Router()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.getHW_FH_Router()[0]+'：'+self.getHW_FH_Router()[1]+'\n'+self.printStatus(self.getHW_FH_Router()))

        #HW_FH_AC2
        if cmp(self.getHW_FH_AC2()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.getHW_FH_AC2()[0]+'：'+self.getHW_FH_AC2()[1]+'\n'+self.printStatus(self.getHW_FH_AC2()))

        #HW_FH_AC1
        if cmp(self.getHW_FH_AC1()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.getHW_FH_AC1()[0]+'：'+self.getHW_FH_AC1()[1]+'\n'+self.printStatus(self.getHW_FH_AC1()))

        #HW_FH_AGG
        if cmp(self.getHW_FH_AGG()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.getHW_FH_AGG()[0]+'：'+self.getHW_FH_AGG()[1]+'\n'+self.printStatus(self.getHW_FH_AGG()))

        #HW_BL_CORE
        if cmp(self.getHW_BL_CORE()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.getHW_BL_CORE()[0]+'：'+self.getHW_BL_CORE()[1]+'\n'+self.printStatus(self.getHW_BL_CORE()))

        #HW_BL_AGG
        if cmp(self.getHW_BL_AGG()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.getHW_BL_AGG()[0]+'：'+self.getHW_BL_AGG()[1]+'\n'+self.printStatus(self.getHW_BL_AGG()))

        #HW_BL_SUBFAB_2
        if cmp(self.getHW_BL_SUBFAB_2()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.getHW_BL_SUBFAB_2()[0]+'：'+self.getHW_BL_SUBFAB_2()[1]+'\n'+self.printStatus(self.getHW_BL_SUBFAB_2()))

        #HW_BL_SUBFAB_1
        if cmp(self.getHW_BL_SUBFAB_1()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.getHW_BL_SUBFAB_1()[0]+'：'+self.getHW_BL_SUBFAB_1()[1]+'\n'+self.printStatus(self.getHW_BL_SUBFAB_1()))

        #HW_BL_PUB3F
        if cmp(self.getHW_BL_PUB3F()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.getHW_BL_PUB3F()[0]+'：'+self.getHW_BL_PUB3F()[1]+'\n'+self.printStatus(self.getHW_BL_PUB3F()))

        #HW_BL_PUB1F
        if cmp(self.getHW_BL_PUB1F()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.getHW_BL_PUB1F()[0]+'：'+self.getHW_BL_PUB1F()[1]+'\n'+self.printStatus(self.getHW_BL_PUB1F()))

        #HW_BL_OFF4F
        if cmp(self.getHW_BL_OFF4F()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.getHW_BL_OFF4F()[0]+'：'+self.getHW_BL_OFF4F()[1]+'\n'+self.printStatus(self.getHW_BL_OFF4F()))

        #HW_BL_OFF2F-3
        if cmp(self.getHW_BL_OFF2F_3()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.getHW_BL_OFF2F_3()[0]+'：'+self.getHW_BL_OFF2F_3()[1]+'\n'+self.printStatus(self.getHW_BL_OFF2F_3()))

        #HW_BL_OFF2F-2
        if cmp(self.getHW_BL_OFF2F_2()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.getHW_BL_OFF2F_2()[0]+'：'+self.getHW_BL_OFF2F_2()[1]+'\n'+self.printStatus(self.getHW_BL_OFF2F_2()))

        #HW_BL_OFF2F-1
        if cmp(self.getHW_BL_OFF2F_1()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.getHW_BL_OFF2F_1()[0]+'：'+self.getHW_BL_OFF2F_1()[1]+'\n'+self.printStatus(self.getHW_BL_OFF2F_1()))

        #HW_BL_OFF1F-3
        if cmp(self.getHW_BL_OFF1F_3()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.getHW_BL_OFF1F_3()[0]+'：'+self.getHW_BL_OFF1F_3()[1]+'\n'+self.printStatus(self.getHW_BL_OFF1F_3()))

        #HW_BL_OFF1F-2
        if cmp(self.getHW_BL_OFF1F_2()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.getHW_BL_OFF1F_2()[0]+'：'+self.getHW_BL_OFF1F_2()[1]+'\n'+self.printStatus(self.getHW_BL_OFF1F_2()))

        #HW_BL_OFF1F-1
        if cmp(self.getHW_BL_OFF1F_1()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.getHW_BL_OFF1F_1()[0]+'：'+self.getHW_BL_OFF1F_1()[1]+'\n'+self.printStatus(self.getHW_BL_OFF1F_1()))

        #HW_BL_DaMen
        if cmp(self.getHW_BL_DaMen()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.getHW_BL_DaMen()[0]+'：'+self.getHW_BL_DaMen()[1]+'\n'+self.printStatus(self.getHW_BL_DaMen()))

        #HW_BL_PUBOFF
        if cmp(self.getHW_BL_PUBOFF()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.getHW_BL_PUBOFF()[0]+'：'+self.getHW_BL_PUBOFF()[1]+'\n'+self.printStatus(self.getHW_BL_PUBOFF()))

        #HW_BL_OFF4FTD
        if cmp(self.getHW_BL_OFF4FTD()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.getHW_BL_OFF4FTD()[0]+'：'+self.getHW_BL_OFF4FTD()[1]+'\n'+self.printStatus(self.getHW_BL_OFF4FTD()))

        #HW_BL_CUB3F
        if cmp(self.getHW_BL_CUB3F()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.getHW_BL_CUB3F()[0]+'：'+self.getHW_BL_CUB3F()[1]+'\n'+self.printStatus(self.getHW_BL_CUB3F()))

        #HW_BL_LJ-2
        if cmp(self.getHW_BL_LJ_2()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.getHW_BL_LJ_2()[0]+'：'+self.getHW_BL_LJ_2()[1]+'\n'+self.printStatus(self.getHW_BL_LJ_2()))

        #HW_BL_LJ-1
        if cmp(self.getHW_BL_LJ_1()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.getHW_BL_LJ_1()[0]+'：'+self.getHW_BL_LJ_1()[1]+'\n'+self.printStatus(self.getHW_BL_LJ_1()))

        #HW_FH_1_S1
        if cmp(self.getHW_FH_1_S1()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.getHW_FH_1_S1()[0]+'：'+self.getHW_FH_1_S1()[1]+'\n'+self.printStatus(self.getHW_FH_1_S1()))

        #HW_FH_1_S2
        if cmp(self.getHW_FH_1_S2()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.getHW_FH_1_S2()[0]+'：'+self.getHW_FH_1_S2()[1]+'\n'+self.printStatus(self.getHW_FH_1_S2()))

        #HW_FH_1_S3
        if cmp(self.getHW_FH_1_S3()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.getHW_FH_1_S3()[0]+'：'+self.getHW_FH_1_S3()[1]+'\n'+self.printStatus(self.getHW_FH_1_S3()))

        #HW_FH_1_S4
        if cmp(self.getHW_FH_1_S4()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.getHW_FH_1_S4()[0]+'：'+self.getHW_FH_1_S4()[1]+'\n'+self.printStatus(self.getHW_FH_1_S4()))

        #HW_FH_1_S5
        if cmp(self.getHW_FH_1_S5()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.getHW_FH_1_S5()[0]+'：'+self.getHW_FH_1_S5()[1]+'\n'+self.printStatus(self.getHW_FH_1_S5()))

        #HW_FH_1_S1
        if cmp(self.getHW_FH_3_S1()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.getHW_FH_3_S1()[0]+'：'+self.getHW_FH_3_S1()[1]+'\n'+self.printStatus(self.getHW_FH_3_S1()))

        #HW_FH_3_S2
        if cmp(self.getHW_FH_3_S2()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.getHW_FH_3_S2()[0]+'：'+self.getHW_FH_3_S2()[1]+'\n'+self.printStatus(self.getHW_FH_3_S2()))

        #HW_FH_ZHZFang 综合站房
        if cmp(self.getHW_FH_ZHZFang()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.getHW_FH_ZHZFang()[0]+'：'+self.getHW_FH_ZHZFang()[1]+'\n'+self.printStatus(self.getHW_FH_ZHZFang()))

        #HW_FH_1_BATing 保安亭
        if cmp(self.getHW_FH_BATing()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.getHW_FH_BATing()[0]+'：'+self.getHW_FH_BATing()[1]+'\n'+self.printStatus(self.getHW_FH_BATing()))

        #HW_FH_1_STang 食堂
        if cmp(self.getHW_FH_STang()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.getHW_FH_STang()[0]+'：'+self.getHW_FH_STang()[1]+'\n'+self.printStatus(self.getHW_FH_STang()))

        #HW_FH_1_SShe 宿舍
        if cmp(self.getHW_FH_SShe()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.getHW_FH_SShe()[0]+'：'+self.getHW_FH_SShe()[1]+'\n'+self.printStatus(self.getHW_FH_SShe()))

        #SangforSG
        if cmp(self.getSangforSG()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.getSangforSG()[0]+'：'+self.getSangforSG()[1]+'\n'+self.printStatus(self.getSangforSG()))

        #360TD
        if cmp(self.get360TD()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.get360TD()[0]+'：'+self.get360TD()[1]+'\n'+self.printStatus(self.get360TD()))

        #DellCMC
        if cmp(self.getDellCMC()[1],'ok') != 0:
            self.myWxMessage.wxMessage('\n'+self.getDellCMC()[0]+'：'+self.getDellCMC()[1]+'\n'+self.printStatus(self.getDellCMC()))

        #For R710 & M710HD
        self.checkDellServer4iDRAC6()

        #For R730 & M630HD
        self.checkDellServer4iDRAC8()

def main():
    mySnmp = WxSnmp()
    mySnmp.checkAllDeviceStatus()
    #获取某台设备的状态
    #print mySnmp.getStatusByName('td')
    #print mySnmp.getStatusByName('agg')

if __name__ == '__main__':
    main()


