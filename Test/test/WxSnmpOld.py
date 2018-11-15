# -*- coding:gbk -*-
__author__ = 'li.shida'

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
    from pysnmp.entity.rfc3413.oneliner import cmdgen
    #from pysnmp.hlapi import *
except ImportError:
    print 'ImportError'

class WxSnmp():
    def __init__(self):
        config = ConfigParser.ConfigParser()

        try:
            self.mainPath = os.path.dirname(os.path.realpath(__file__)) #��ȡWxMessage.pyִ��ʱ�ľ���·��
            configFile = os.path.join(self.mainPath,'config_oid.ini')   #�����ļ��ľ���·��
            config.readfp(open(configFile, "rb"))
            self.configIniDict = dict(config._sections)
            for k in self.configIniDict:
                self.configIniDict[k] = dict(self.configIniDict[k])

            #��ʼ��cmdgen����������
            self.cg = cmdgen.CommandGenerator()
            #��ȡ����������Ϣ
            self.port = int(self.configIniDict['Global']['port'])
            self.version = int(self.configIniDict['Global']['version'])
            self.communication = self.configIniDict['Global']['communication']
            self.agent = self.configIniDict['Global']['agent']

        except IOError:
            print 'ReadConfigFileError'

    def getSnmp(self,ip,oid):
        try:
            errorIndication, errorStatus, errorIndex, varBinds = self.cg.getCmd(
                cmdgen.CommunityData(self.agent, self.communication, self.version),
                cmdgen.UdpTransportTarget((ip, self.port)),oid)
            if errorStatus == 0:
                return str(varBinds[0][1])
        except Exception as e:
            HostError = self.configIniDict['ERROR']['hostError'.lower()]
            print HostError
        #���������򷵻�None

def main():
    myWxSnmp = WxSnmp()

    Off4FTD = myWxSnmp.configIniDict['Switch']['Off4FTD'.lower()]
    hwCpuDevDuty = myWxSnmp.configIniDict['Huawei']['hwCpuDevDuty'.lower()]
    sysDescr = myWxSnmp.configIniDict['Huawei']['sysDescr'.lower()]
    sysName = myWxSnmp.configIniDict['Huawei']['sysName'.lower()]

    x = myWxSnmp.getSnmp(Off4FTD,sysDescr)
    z = myWxSnmp.getSnmp(Off4FTD,sysName)
    y =  myWxSnmp.getSnmp(Off4FTD,hwCpuDevDuty)
    print x
    print y



if __name__ == '__main__':
    main()


