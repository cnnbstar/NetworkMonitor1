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
except ImportError:
    print 'ImportError'

__all__ = [
    "BlHw","BlDell","BlOthers","FhHw"
]

class SnmpUtils():
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

class BlHw():
    '''
    北仑地区华为设备
    '''
    def __init__(self):
        self.mySnmp = SnmpUtils()

    def getHW_BL_LJ_1(self):
        '''
        #连接交换机
        #S5700-28P,单机双电口上行链路
        :return:
        '''
        address = '10.15.0.252'
        hwEntityTemperature = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67108873')#MPU 温度
        hwTrunkOperstatus5 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.5')#Eth-Trunk端口状态 GE0/0/1
        hwTrunkOperstatus6 =self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.6')#Eth-Trunk端口状态 GE0/0/2

        if( int(hwEntityTemperature) < self.mySnmp.hwSwitchTemperatureThreshold and
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
        hwEntityTemperature = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67108873')#MPU 温度
        hwTrunkOperstatus5 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.5')#Eth-Trunk端口状态 GE0/0/1
        hwTrunkOperstatus6 =self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.6')#Eth-Trunk端口状态 GE0/0/2

        if( int(hwEntityTemperature) < self.mySnmp.hwSwitchTemperatureThreshold and
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
        hwEntityTemperature = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67108873')#MPU 温度
        hwEntityOpticalTxPowerThreshold = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67308622')#GE0/0/49 SPF模块功率
        hwEntityFanState = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.0.0')#MPU 风扇状态
        hwTrunkOperstatus53 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.53')#Eth-Trunk(GE0/0/49)端口状态

        if( int(hwEntityTemperature) < self.mySnmp.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPowerThreshold) > self.mySnmp.hwEntityOpticalTxPowerThreshold and
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
        hwEntityTemperature = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67371017')#MPU 温度
        hwEntityFanState = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.0')#MPU 风扇状态
        hwTrunkOperstatus53 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.53')#Eth-Trunk(GE1/0/47)端口状态

        if( int(hwEntityTemperature) < self.mySnmp.hwSwitchTemperatureThreshold and
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
        hwEntityTemperature = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67108873')#MPU 温度
        hwEntityFanState = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.0.0')#MPU 风扇状态
        hwEntityOpticalTxPowerThreshold = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67308622')#GE0/0/49 SPF模块功率
        hwTrunkOperstatus55 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.55')#Eth-Trunk(GE0/0/49)端口状态

        if( int(hwEntityTemperature) < self.mySnmp.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPowerThreshold) > self.mySnmp.hwEntityOpticalTxPowerThreshold and
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
        hwEntityTemperature = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67108873')#MPU 温度
        hwTrunkOperstatus28 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.28')#Eth-Trunk(GE0/0/24)端口状态

        if( int(hwEntityTemperature) < self.mySnmp.hwSwitchTemperatureThreshold and
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
        hwEntityTemperature1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67371017')#MPU 1温度
        hwEntityTemperature2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67633161')#MPU 2温度
        hwEntityFanState1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.0')#MPU 1风扇状态
        hwEntityFanState2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.0')#MPU 2风扇状态
        hwEntityOpticalTxPowerThreshold1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67570766')#GE1/0/49 SPF模块功率
        hwEntityOpticalTxPowerThreshold2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67832910')#GE2/0/49 SPF模块功率
        hwTrunkOperstatus55 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.55')#Eth-Trunk(GE1/0/49)端口状态
        hwTrunkOperstatus107 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.107')#Eth-Trunk(GE2/0/49)端口状态
        hwStackPortStatus1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.1.0')#Stack(GE1/0/51)端口状态
        hwStackPortStatus2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.2.1')#Stack(GE2/0/52)端口状态

        if( int(hwEntityTemperature1) < self.mySnmp.hwSwitchTemperatureThreshold and
            int(hwEntityTemperature2) < self.mySnmp.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPowerThreshold1) > self.mySnmp.hwEntityOpticalTxPowerThreshold and
            int(hwEntityOpticalTxPowerThreshold2) > self.mySnmp.hwEntityOpticalTxPowerThreshold and
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
        hwEntityTemperature1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67371017')#MPU 1温度
        hwEntityTemperature2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67633161')#MPU 2温度
        hwEntityFanState1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.0')#MPU 1风扇状态
        hwEntityFanState2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.0')#MPU 2风扇状态
        hwEntityOpticalTxPowerThreshold1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67570766')#GE1/0/49 SPF模块功率
        hwEntityOpticalTxPowerThreshold2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67832910')#GE2/0/49 SPF模块功率
        hwTrunkOperstatus55 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.55')#Eth-Trunk(GE1/0/49)端口状态
        hwTrunkOperstatus107 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.107')#Eth-Trunk(GE2/0/49)端口状态
        hwStackPortStatus1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.1.0')#Stack(GE1/0/51)端口状态
        hwStackPortStatus2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.2.1')#Stack(GE2/0/52)端口状态

        if( int(hwEntityTemperature1) < self.mySnmp.hwSwitchTemperatureThreshold and
            int(hwEntityTemperature2) < self.mySnmp.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPowerThreshold1) > self.mySnmp.hwEntityOpticalTxPowerThreshold and
            int(hwEntityOpticalTxPowerThreshold2) > self.mySnmp.hwEntityOpticalTxPowerThreshold and
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
        hwEntityTemperature1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67371017')#MPU 1温度
        hwEntityTemperature2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67633161')#MPU 2温度
        hwEntityFanState1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.0')#MPU 1风扇状态
        hwEntityFanState2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.0')#MPU 2风扇状态
        hwEntityOpticalTxPowerThreshold1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67570766')#GE1/0/49 SPF模块功率
        hwEntityOpticalTxPowerThreshold2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67832910')#GE2/0/49 SPF模块功率
        hwTrunkOperstatus54 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.54')#Eth-Trunk(GE1/0/49)端口状态
        hwTrunkOperstatus158 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.158')#Eth-Trunk(GE2/0/49)端口状态
        hwStackPortStatus1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.1.0')#Stack(GE1/0/51)端口状态
        hwStackPortStatus2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.2.1')#Stack(GE2/0/52)端口状态

        if( int(hwEntityTemperature1) < self.mySnmp.hwSwitchTemperatureThreshold and
            int(hwEntityTemperature2) < self.mySnmp.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPowerThreshold1) > self.mySnmp.hwEntityOpticalTxPowerThreshold and
            int(hwEntityOpticalTxPowerThreshold2) > self.mySnmp.hwEntityOpticalTxPowerThreshold and
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
        hwEntityTemperature1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67371017')#MPU 1温度
        hwEntityTemperature2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67633161')#MPU 2温度
        hwEntityFanState1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.0')#MPU 1风扇状态
        hwEntityFanState2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.0')#MPU 2风扇状态
        hwEntityOpticalTxPowerThreshold1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67570766')#GE1/0/49 SPF模块功率
        hwEntityOpticalTxPowerThreshold2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67832910')#GE2/0/49 SPF模块功率
        hwTrunkOperstatus55 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.55')#Eth-Trunk(GE1/0/49)端口状态
        hwTrunkOperstatus107 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.107')#Eth-Trunk(GE2/0/49)端口状态
        hwStackPortStatus1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.1.0')#Stack(GE1/0/51)端口状态
        hwStackPortStatus2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.2.1')#Stack(GE2/0/52)端口状态

        if( int(hwEntityTemperature1) < self.mySnmp.hwSwitchTemperatureThreshold and
            int(hwEntityTemperature2) < self.mySnmp.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPowerThreshold1) > self.mySnmp.hwEntityOpticalTxPowerThreshold and
            int(hwEntityOpticalTxPowerThreshold2) > self.mySnmp.hwEntityOpticalTxPowerThreshold and
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
        hwEntityTemperature1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67371017')#MPU 1温度
        hwEntityTemperature2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67633161')#MPU 2温度
        hwEntityFanState1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.0')#MPU 1风扇状态
        hwEntityFanState2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.0')#MPU 2风扇状态
        hwEntityOpticalTxPowerThreshold1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67570766')#GE1/0/49 SPF模块功率
        hwEntityOpticalTxPowerThreshold2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67832910')#GE2/0/49 SPF模块功率
        hwTrunkOperstatus105 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.105')#Eth-Trunk(GE1/0/49)端口状态
        hwTrunkOperstatus157 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.157')#Eth-Trunk(GE2/0/49)端口状态
        hwStackPortStatus1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.1.0')#Stack(GE1/0/51)端口状态
        hwStackPortStatus2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.2.1')#Stack(GE2/0/52)端口状态

        if( int(hwEntityTemperature1) < self.mySnmp.hwSwitchTemperatureThreshold and
            int(hwEntityTemperature2) < self.mySnmp.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPowerThreshold1) > self.mySnmp.hwEntityOpticalTxPowerThreshold and
            int(hwEntityOpticalTxPowerThreshold2) > self.mySnmp.hwEntityOpticalTxPowerThreshold and
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
        hwEntityTemperature1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67371017')#MPU 1温度
        hwEntityTemperature2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67633161')#MPU 2温度
        hwEntityFanState1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.0')#MPU 1风扇状态
        hwEntityFanState2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.0')#MPU 2风扇状态
        hwEntityOpticalTxPowerThreshold1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67570766')#GE1/0/49 SPF模块功率
        hwEntityOpticalTxPowerThreshold2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67832910')#GE2/0/49 SPF模块功率
        hwTrunkOperstatus55 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.55')#Eth-Trunk(GE1/0/49)端口状态
        hwTrunkOperstatus107 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.107')#Eth-Trunk(GE2/0/49)端口状态
        hwStackPortStatus1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.1.0')#Stack(GE1/0/51)端口状态
        hwStackPortStatus2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.2.1')#Stack(GE2/0/52)端口状态

        if( int(hwEntityTemperature1) < self.mySnmp.hwSwitchTemperatureThreshold and
            int(hwEntityTemperature2) < self.mySnmp.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPowerThreshold1) > self.mySnmp.hwEntityOpticalTxPowerThreshold and
            int(hwEntityOpticalTxPowerThreshold2) > self.mySnmp.hwEntityOpticalTxPowerThreshold and
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
        hwEntityTemperature1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67371017')#MPU 1温度
        hwEntityTemperature2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67633161')#MPU 2温度
        hwEntityTemperature3 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67895305')#MPU 3温度
        hwEntityFanState1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.0')#MPU 1风扇状态
        hwEntityFanState2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.0')#MPU 2风扇状态
        hwEntityFanState3 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.3.0')#MPU 3风扇状态
        hwEntityOpticalTxPowerThreshold1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67570766')#GE1/0/49 SPF模块功率
        hwEntityOpticalTxPowerThreshold2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.68095054')#GE2/0/49 SPF模块功率
        hwTrunkOperstatus55 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.55')#Eth-Trunk(GE1/0/49)端口状态
        hwTrunkOperstatus159 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.159')#Eth-Trunk(GE3/0/49)端口状态
        hwStackPortStatus10 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.1.0')#Stack(GE1/0/51)端口状态
        hwStackPortStatus20 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.2.0')#Stack(GE2/0/52)端口状态
        hwStackPortStatus21 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.2.1')#Stack(GE2/0/51)端口状态
        hwStackPortStatus31 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.3.1')#Stack(GE3/0/52)端口状态

        if( int(hwEntityTemperature1) < self.mySnmp.hwSwitchTemperatureThreshold and
            int(hwEntityTemperature2) < self.mySnmp.hwSwitchTemperatureThreshold and
            int(hwEntityTemperature3) < self.mySnmp.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPowerThreshold1) > self.mySnmp.hwEntityOpticalTxPowerThreshold and
            int(hwEntityOpticalTxPowerThreshold2) > self.mySnmp.hwEntityOpticalTxPowerThreshold and
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
        hwEntityTemperature1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.0.0')#MPU 1温度
        hwEntityFanState1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.0.0')#MPU 1风扇状态
        hwEntityOpticalTxPowerThreshold1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67308622')#GE0/0/49 SPF模块功率
        hwEntityOpticalTxPowerThreshold2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67308686')#GE0/0/50 SPF模块功率
        hwTrunkOperstatus160 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.160')#Eth-Trunk(GE1/0/49)端口状态
        hwTrunkOperstatus161 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.161')#Eth-Trunk(GE2/0/49)端口状态

        if( int(hwEntityTemperature1) < self.mySnmp.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPowerThreshold1) > self.mySnmp.hwEntityOpticalTxPowerThreshold and
            int(hwEntityOpticalTxPowerThreshold2) > self.mySnmp.hwEntityOpticalTxPowerThreshold and
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
        hwEntityTemperature1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67371017')#MPU 1温度
        hwEntityTemperature2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67633161')#MPU 2温度
        hwEntityOpticalTxPowerThreshold1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67570766')#GE1/0/49 SPF模块功率
        hwEntityOpticalTxPowerThreshold2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67832910')#GE2/0/49 SPF模块功率
        hwEntityFanState1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.0')#MPU 1风扇状态
        hwEntityFanState2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.0')#MPU 2风扇状态
        hwTrunkOperstatus55 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.55')#Eth-Trunk(GE1/0/49)端口状态
        hwTrunkOperstatus107 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.107')#Eth-Trunk(GE2/0/49)端口状态
        hwStackPortStatus10 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.1.0')#Stack(GE1/0/51)端口状态
        hwStackPortStatus11 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.1.1')#Stack(GE2/0/52)端口状态
        hwStackPortStatus20 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.2.0')#Stack(GE1/0/52)端口状态
        hwStackPortStatus21 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.2.1')#Stack(GE2/0/51)端口状态

        if( int(hwEntityTemperature1) < self.mySnmp.hwSwitchTemperatureThreshold and
            int(hwEntityTemperature2) < self.mySnmp.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPowerThreshold1) > self.mySnmp.hwEntityOpticalTxPowerThreshold and
            int(hwEntityOpticalTxPowerThreshold2) > self.mySnmp.hwEntityOpticalTxPowerThreshold and
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
        hwEntityTemperature1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67371017')#MPU 1温度
        hwEntityTemperature2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67633161')#MPU 2温度
        hwEntityOpticalTxPowerThreshold1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67570766')#GE1/0/49 SPF模块功率
        hwEntityOpticalTxPowerThreshold2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67832910')#GE2/0/49 SPF模块功率
        hwEntityFanState1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.0')#MPU 1风扇状态
        hwEntityFanState2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.0')#MPU 2风扇状态
        hwTrunkOperstatus55 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.55')#Eth-Trunk(GE1/0/49)端口状态
        hwTrunkOperstatus107 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.107')#Eth-Trunk(GE2/0/49)端口状态
        hwStackPortStatus10 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.1.0')#Stack(GE1/0/51)端口状态
        hwStackPortStatus11 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.1.1')#Stack(GE2/0/52)端口状态
        hwStackPortStatus20 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.2.0')#Stack(GE1/0/52)端口状态
        hwStackPortStatus21 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.2.1')#Stack(GE2/0/51)端口状态

        if( int(hwEntityTemperature1) < self.mySnmp.hwSwitchTemperatureThreshold and
            int(hwEntityTemperature2) < self.mySnmp.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPowerThreshold1) > self.mySnmp.hwEntityOpticalTxPowerThreshold and
            int(hwEntityOpticalTxPowerThreshold2) > self.mySnmp.hwEntityOpticalTxPowerThreshold and
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
        hwEntityTemperature1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67371017')#MPU 1温度
        hwEntityTemperature2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67633161')#MPU 2温度
        hwEntityOpticalTxPowerThreshold1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67570766')#GE1/0/49 SPF模块功率
        hwEntityOpticalTxPowerThreshold2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67832910')#GE2/0/49 SPF模块功率
        hwEntityFanState1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.0')#MPU 1风扇状态
        hwEntityFanState2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.0')#MPU 2风扇状态
        hwTrunkOperstatus55 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.55')#Eth-Trunk(GE1/0/49)端口状态
        hwTrunkOperstatus107 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.107')#Eth-Trunk(GE2/0/49)端口状态
        hwStackPortStatus10 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.1.0')#Stack(GE1/0/51)端口状态
        hwStackPortStatus11 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.1.1')#Stack(GE2/0/52)端口状态
        hwStackPortStatus20 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.2.0')#Stack(GE1/0/52)端口状态
        hwStackPortStatus21 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.2.1')#Stack(GE2/0/51)端口状态

        if( int(hwEntityTemperature1) < self.mySnmp.hwSwitchTemperatureThreshold and
            int(hwEntityTemperature2) < self.mySnmp.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPowerThreshold1) > self.mySnmp.hwEntityOpticalTxPowerThreshold and
            int(hwEntityOpticalTxPowerThreshold2) > self.mySnmp.hwEntityOpticalTxPowerThreshold and
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
        hwEntityTemperature1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.68157449') #MPU 1温度
        hwEntityTemperature2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.69206025') #MPU 2温度
        hwEntityFanState10 =self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.0')#MPU 10风扇状态
        hwEntityFanState11 =self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.1')#MPU 11风扇状态
        hwEntityFanState12 =self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.2')#MPU 12风扇状态
        hwEntityFanState13 =self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.3')#MPU 13风扇状态
        hwEntityFanState14 =self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.4')#MPU 14风扇状态
        hwEntityFanState20 =self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.0')#MPU 20风扇状态
        hwEntityFanState21 =self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.1')#MPU 21风扇状态
        hwEntityFanState22 =self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.2')#MPU 22风扇状态
        hwEntityFanState23 =self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.3')#MPU 23风扇状态
        hwEntityFanState24 =self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.4')#MPU 24风扇状态
        hwStackPortStatus10 =self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.1.0')#Stack(XGE1/0/3)端口状态
        hwStackPortStatus11 =self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.1.1')#Stack(XGE2/0/4)端口状态
        hwStackPortStatus20 =self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.2.0')#Stack(XGE1/0/4)端口状态
        hwStackPortStatus21 =self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.2.1')#Stack(XGE2/0/3)端口状态


        if( int(hwEntityTemperature1) < self.mySnmp.hwSwitchTemperatureThreshold and
            int(hwEntityTemperature2) < self.mySnmp.hwSwitchTemperatureThreshold and
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
        hwEntityTemperature11 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.68943881')#MPU 11温度
        hwEntityTemperature12 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.69206025')#MPU 12温度
        hwEntityTemperature21 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.69206025')#MPU 21温度
        hwEntityTemperature22 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.136314889')#MPU 22温度
        hwEntityFanState300 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.30.1')#MPU 00风扇状态
        hwEntityFanState301 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.30.2')#MPU 01风扇状态
        hwEntityFanState311 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.31.1')#MPU 11风扇状态
        hwEntityFanState312 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.31.2')#MPU 12风扇状态
        hwEntityFanState321 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.32.1')#MPU 21风扇状态
        hwEntityFanState322 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.32.2')#MPU 22风扇状态
        hwEntityFanState331 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.33.1')#MPU 31风扇状态
        hwEntityFanState332 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.33.2')#MPU 32风扇状态
        hwTrunkOperstatus240 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.5.240')#Eth-Trunk(GE 1/6/0/6)端口状态
        hwTrunkOperstatus423 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.5.423')#Eth-Trunk(GE 2/6/0/6)端口状态
        hwTrunkOperstatus10 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.6.10')#Eth-Trunk(GE 1/6/0/7)端口状态
        hwTrunkOperstatus298 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.6.298')#Eth-Trunk(GE 2/6/0/7)端口状态
        ifOperStatus241 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.2.1.2.2.1.8.241')#Eth-Trunk(XGE 1/6/0/7) For刀片交换机 Left198 TE1/0/1 非Eth-Trunk
        ifOperStatus424 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.2.1.2.2.1.8.424')#Eth-Trunk(XGE 2/6/0/7) For刀片交换机 Right199 TE1/0/1 非Eth-Trunk
        ifOperStatus242 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.2.1.2.2.1.8.242')#Eth-Trunk(XGE 1/6/0/8)端口状态 ForCSS
        ifOperStatus243 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.2.1.2.2.1.8.243')#Eth-Trunk(XGE 2/6/0/8)端口状态 ForCSS
        ifOperStatus244 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.2.1.2.2.1.8.244')#Eth-Trunk(XGE 1/6/0/9)端口状态 ForCSS
        ifOperStatus245 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.2.1.2.2.1.8.245')#Eth-Trunk(XGE 2/6/0/9)端口状态 ForCSS
        ifOperStatus425 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.2.1.2.2.1.8.425')#Eth-Trunk(XGE 1/6/0/10)端口状态 ForCSS
        ifOperStatus426 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.2.1.2.2.1.8.426')#Eth-Trunk(XGE 2/6/0/11)端口状态 ForCSS
        ifOperStatus427 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.2.1.2.2.1.8.427')#Eth-Trunk(XGE 1/6/0/12)端口状态 ForCSS
        ifOperStatus428 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.2.1.2.2.1.8.428')#Eth-Trunk(XGE 2/6/0/13)端口状态 ForCSS

        if( int(hwEntityTemperature11) < self.mySnmp.hwSwitchTemperatureThreshold and
            int(hwEntityTemperature12) < self.mySnmp.hwSwitchTemperatureThreshold and
            int(hwEntityTemperature21) < self.mySnmp.hwSwitchTemperatureThreshold and
            int(hwEntityTemperature22) < self.mySnmp.hwSwitchTemperatureThreshold and
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

class BlDell():
    '''
    北仑地区Dell服务器
    '''
    def __init__(self):
        self.mySnmp = SnmpUtils()

    def getDellCMC(self):
        '''
        #Dell e1000刀框
        #管理地址：10.15.0.200
        :return:
        '''
        #获取常用配置信息
        address = '10.15.0.200'
        drsCMCAmbientTemperatur = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.674.10892.2.3.1.10.0') #环境温度
        drsGlobalSystemStaus = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.674.10892.2.2.1.0') #全局状态,3表示OK

        if( int(drsCMCAmbientTemperatur) < self.mySnmp.drsCMCAmbientTemperatureThreshold and
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

    def getDelliDRAC6(self):
        '''
        检查所有Dell iDrac6 服务器，如R710，M710HD
        :return:
        '''
        #遍历配置表中iDRAC6的服务器列表
        errorStatus = ''
        for hostname,ip in self.mySnmp.iDRAC6ServerDict.items():
            if (hostname != '__name__'):
                globalSystemStatus = self.mySnmp.getSnmpValue(ip, '.1.3.6.1.4.1.674.10892.2.2.1.0') #全局状态,3表示OK
                if(int(globalSystemStatus) == 3):
                    globalStatus = 'ok'
                else:
                    globalStatus = 'fault'
                    errorStatus += hostname.upper()+'：'+globalStatus+'\n'
                    #self.myWxMessage.wxMessage('\n'+hostname.upper()+'：'+globalStatus)
        return globalStatus,errorStatus

    def getDelliDRAC8(self):
        '''
        :param address: Dell R730/R630HD
        :return: OID信息
        '''
        errorStatus = ''
        for hostname,ip in self.mySnmp.iDRAC8ServerDict.items():
            if (hostname != '__name__'):
                globalSystemStatus = self.mySnmp.getSnmpValue(ip, '.1.3.6.1.4.1.674.10892.5.2.1.0') #全局状态,3表示OK
                if(int(globalSystemStatus) == 3):
                    globalStatus = 'ok'
                else:
                    globalStatus = 'fault'
                    errorStatus += hostname.upper()+'：'+globalStatus+'\n'
                    #self.myWxMessage.wxMessage('\n'+hostname.upper()+'：'+globalStatus)
        return globalStatus,errorStatus

class BlOthers():
    '''
    北仑地区其他设备，如深信服SG，360天堤
    '''
    def __init__(self):
        self.mySnmp = SnmpUtils()

    def getSangforSG(self):
        '''
        #深信服SG SANGFOR-GENERAL-MIB.mib
        #管理地址：10.15.1.253
        :return:
        '''
         #获取常用配置信息
        address = '10.15.1.253'
        sfSysCpuCostRate = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.35047.1.3.0') #当前CPU使用率
        numOfCurOnlin = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.35047.2.1.1.1.0') #在线用户数
        numOfSession = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.35047.2.1.1.6.0') #当前会话数
        ifTxKBs = int(self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.35047.2.1.2.1.7.1'))/1024 #Eth0端口发送速率
        ifRxKBs = int(self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.35047.2.1.2.1.8.1'))/1024 #Eth0端口接收速率

        if( int(sfSysCpuCostRate) < self.mySnmp.sfSysCpuCostRateThreshold and
            int(numOfCurOnlin) < self.mySnmp.numOfCurOnlinThreshold and int(numOfSession) < self.mySnmp.numOfSessionThreshold ):
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
        systemTemperature = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.32328.6.1.8.0')#设备温度
        cpuPercentUsage = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.32328.6.1.10.1.2.0')#CPU使用率
        memoryPercentUsage = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.32328.6.1.10.3.2.0')#内存使用率
        CFDiskPrcentUsage = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.32328.6.1.10.2.2.0')#系统盘使用率
        fanSpeedSpeed1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.32328.6.1.10.5.1.1.3.1')#系统风扇转速
        fanSpeedSpeed2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.32328.6.1.10.5.1.1.3.2') #CPU风扇转速
        sessionCurrentNumber = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.32328.6.2.1.2.0')#当前会话数
        #ifInBps5 = int(self.getSnmpValue(address, '.1.3.6.1.4.1.32328.6.2.3.1.1.3.5'))/1024*8 #进系统速率(惠州到宁波）bps/s
        #ifOutBps5 = int(self.getSnmpValue(address, '.1.3.6.1.4.1.32328.6.2.3.1.1.4.5'))/1024*8 #出系统速率（宁波到惠州）bps/s

        ifInBps5 = round(float(self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.32328.6.2.3.1.1.3.5'))/1024*8,1) #进系统速率(惠州到宁波）bps/s
        ifOutBps5 = round(float(self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.32328.6.2.3.1.1.4.5'))/1024*8,1) #出系统速率（宁波到惠州）bps/s
        ifInBps2 = round(float(self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.32328.6.2.3.1.1.3.2'))/1024*8,1) #进系统速率(奉化到北仑）bps/s
        ifOutBps2 = round(float(self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.32328.6.2.3.1.1.4.2'))/1024*8,1) #出系统速率（北仑到奉化）bps/s

        if( int(systemTemperature) < self.mySnmp.systemTemperatureThreshold and
            int(fanSpeedSpeed1) > self.mySnmp.fanSpeedSpeedSysThreshold and int(fanSpeedSpeed2) > self.mySnmp.fanSpeedSpeedCpuThreshold and
            int(sessionCurrentNumber) < self.mySnmp.sessionCurrentNumberThreshold ):
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

class FhHw():
    '''
    奉化地区华为设备
    '''
    def __init__(self):
        self.mySnmp = SnmpUtils()

    def getHW_FH_AGG(self):
        '''
        奉化汇聚层交换机
        S5700HI 双机堆叠
        :return:返回包含主机名、全局状态及关键项状态的数据字典
        '''
        address = '10.15.255.254'
        hwEntityTemperature1 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.68157449') #MPU 1温度
        hwEntityTemperature2 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.69206025') #MPU 2温度
        hwEntityFanState10 =self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.0')#MPU 10风扇状态
        hwEntityFanState11 =self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.1')#MPU 11风扇状态
        hwEntityFanState12 =self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.2')#MPU 12风扇状态
        hwEntityFanState13 =self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.3')#MPU 13风扇状态
        hwEntityFanState14 =self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.1.4')#MPU 14风扇状态
        hwEntityFanState20 =self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.0')#MPU 20风扇状态
        hwEntityFanState21 =self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.1')#MPU 21风扇状态
        hwEntityFanState22 =self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.2')#MPU 22风扇状态
        hwEntityFanState23 =self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.3')#MPU 23风扇状态
        hwEntityFanState24 =self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.2.4')#MPU 24风扇状态
        hwStackPortStatus10 =self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.1.0')#Stack(XGE1/0/3)端口状态
        hwStackPortStatus11 =self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.1.1')#Stack(XGE2/0/4)端口状态
        hwStackPortStatus20 =self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.2.0')#Stack(XGE1/0/4)端口状态
        hwStackPortStatus21 =self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.183.1.21.1.5.2.1')#Stack(XGE2/0/3)端口状态


        if( int(hwEntityTemperature1) < self.mySnmp.hwSwitchTemperatureThreshold and
            int(hwEntityTemperature2) < self.mySnmp.hwSwitchTemperatureThreshold and
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
        hwEntityTemperature = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.9') #CPU温度
        #Eth-Trunk端口状态 GE0/0/1
        hwTrunkOperstatus3 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.3')
        #Eth-Trunk端口状态 GE0/0/2
        hwTrunkOperstatus4 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.4')
        hwWlanCurJointApNum = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.6.139.12.1.2.1.0') #在线AP数量
        hwWlanCurAuthSuccessStaNum = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.6.139.12.1.2.3.0') #在线终端数
        hwWlanRfComplianceRate = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.6.139.12.1.4.6.0') #射频总体达标率
        hwWlanApComplianceRate = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.6.139.12.1.5.5.0') #AP总体达标率
        hwWlanStaComplianceRate = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.6.139.12.1.3.5.0') #终端总体达标率
        hwStaGlobalWirelessPacketDropRate = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.6.139.12.1.3.17.0') #终端平均丢包率

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

        if( int(hwEntityTemperature) < self.mySnmp.hwSwitchTemperatureThreshold and
            int(hwTrunkOperstatus3) == 1 and
            int(hwTrunkOperstatus4) == 1 and
            #int(hwStaGlobalWirelessPacketDropRate) < int(self.hwStaGlobalWirelessPacketDropRateThreshold) and #终端丢包率
            int(hwWlanStaComplianceRate) > int(self.mySnmp.hwWlanStaComplianceRateThreshold) and #终端达成率
            int(hwWlanApComplianceRate) > int(self.mySnmp.hwWlanApComplianceRateThreshold) and #AP达成率
            int(hwWlanRfComplianceRate) > int(self.mySnmp.hwWlanRfComplianceRateThreshold) and #射频达成率
            int(hwWlanCurJointApNum) == int(self.mySnmp.hwWlanCurJointApNumThreshold) #在线AP数

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
        hwEntityTemperature = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.9') #CPU温度
        #Eth-Trunk端口状态 GE0/0/1
        hwTrunkOperstatus3 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.3')
        #Eth-Trunk端口状态 GE0/0/2
        hwTrunkOperstatus4 = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.4')
        hwWlanCurJointApNum = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.6.139.12.1.2.1.0') #在线AP数量
        hwWlanCurAuthSuccessStaNum = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.6.139.12.1.2.3.0') #在线终端数
        hwWlanRfComplianceRate = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.6.139.12.1.4.6.0') #射频总体达标率
        hwWlanApComplianceRate = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.6.139.12.1.5.5.0') #AP总体达标率
        hwWlanStaComplianceRate = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.6.139.12.1.3.5.0') #终端总体达标率
        hwStaGlobalWirelessPacketDropRate = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.6.139.12.1.3.17.0') #终端平均丢包率

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

        if( int(hwEntityTemperature) < self.mySnmp.hwSwitchTemperatureThreshold and
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
        hwEntityTemperature = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.9')#MPU 温度
        hwEntityFanState1 = self.mySnmp.getSnmpValue(address,'1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.0.1')#hwEntityFanState1
        hwEntityFanState2 = self.mySnmp.getSnmpValue(address,'1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.0.2')#hwEntityFanState2
        hwEntityFanState3 = self.mySnmp.getSnmpValue(address,'1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7.0.3')#hwEntityFanState3
        ifOperStatus4 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.2.1.2.2.1.8.4')#端口(GE0/0/1)状态 to FH LJ-1
        ifOperStatus5 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.2.1.2.2.1.8.5')#端口(GE0/0/2)状态 to NB BL

        if( int(hwEntityTemperature) < self.mySnmp.hwRouterTemperatureThreshold and
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
        hwEntityTemperature = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67108873')#MPU 温度
        hwTrunkOperstatus5 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.5')#Eth-Trunk端口状态 GE0/0/1
        hwTrunkOperstatus6 =self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.6')#Eth-Trunk端口状态 GE0/0/2

        if( int(hwEntityTemperature) < self.mySnmp.hwSwitchTemperatureThreshold and
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
        hwEntityTemperature = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67108873')#MPU 温度
        hwEntityOpticalTxPower1 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67306062')#GE0/0/9 单模SPF模块功率
        hwEntityOpticalTxPower2 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67306126')#EGE0/0/10 单模SPF模块功率
        hwTrunkOperstatus15 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.15')#Eth-Trunk端口状态 GE0/0/9
        hwTrunkOperstatus16 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.16')#Eth-Trunk端口状态 GE0/0/10

        if( int(hwEntityTemperature) < self.mySnmp.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPower1) >self.mySnmp.hwEntitySOpticalTxPowerThreshold and
            int(hwEntityOpticalTxPower2) > self.mySnmp.hwEntitySOpticalTxPowerThreshold and
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
        hwEntityTemperature = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67108873')#MPU 温度
        hwEntityOpticalTxPower1 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67306062')#GE0/0/9 单模SPF模块功率
        hwEntityOpticalTxPower2 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67306126')#EGE0/0/10 单模SPF模块功率
        hwTrunkOperstatus15 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.15')#Eth-Trunk端口状态 GE0/0/9
        hwTrunkOperstatus16 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.16')#Eth-Trunk端口状态 GE0/0/10

        if( int(hwEntityTemperature) < self.mySnmp.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPower1) >self.mySnmp.hwEntitySOpticalTxPowerThreshold and
            int(hwEntityOpticalTxPower2) > self.mySnmp.hwEntitySOpticalTxPowerThreshold and
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
        hwEntityTemperature = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67108873')#MPU 温度
        hwEntityOpticalTxPower1 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67306062')#GE0/0/9 单模SPF模块功率
        hwEntityOpticalTxPower2 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67306126')#EGE0/0/10 单模SPF模块功率
        hwTrunkOperstatus15 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.15')#Eth-Trunk端口状态 GE0/0/9
        hwTrunkOperstatus16 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.16')#Eth-Trunk端口状态 GE0/0/10

        if( int(hwEntityTemperature) < self.mySnmp.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPower1) >self.mySnmp.hwEntitySOpticalTxPowerThreshold and
            int(hwEntityOpticalTxPower2) > self.mySnmp.hwEntitySOpticalTxPowerThreshold and
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
        hwEntityTemperature = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67108873')#MPU 温度
        hwEntityOpticalTxPower1 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67306062')#GE0/0/9 单模SPF模块功率
        hwEntityOpticalTxPower2 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67306126')#EGE0/0/10 单模SPF模块功率
        hwTrunkOperstatus15 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.15')#Eth-Trunk端口状态 GE0/0/9
        hwTrunkOperstatus16 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.16')#Eth-Trunk端口状态 GE0/0/10

        if( int(hwEntityTemperature) < self.mySnmp.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPower1) >self.mySnmp.hwEntitySOpticalTxPowerThreshold and
            int(hwEntityOpticalTxPower2) > self.mySnmp.hwEntitySOpticalTxPowerThreshold and
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
        hwEntityTemperature = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67108873')#MPU 温度
        hwEntityOpticalTxPower1 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67306062')#GE0/0/9 单模SPF模块功率
        hwEntityOpticalTxPower2 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67306126')#EGE0/0/10 单模SPF模块功率
        hwTrunkOperstatus13 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.13')#Eth-Trunk端口状态 GE0/0/9
        hwTrunkOperstatus14 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.14')#Eth-Trunk端口状态 GE0/0/10

        if( int(hwEntityTemperature) < self.mySnmp.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPower1) >self.mySnmp.hwEntitySOpticalTxPowerThreshold and
            int(hwEntityOpticalTxPower2) > self.mySnmp.hwEntitySOpticalTxPowerThreshold and
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
        hwEntityTemperature = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67108873')#MPU 温度
        hwEntityOpticalTxPower1 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67306062')#GE0/0/9 单模SPF模块功率
        hwEntityOpticalTxPower2 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67306126')#EGE0/0/10 单模SPF模块功率
        hwTrunkOperstatus15 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.15')#Eth-Trunk端口状态 GE0/0/9
        hwTrunkOperstatus16 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.16')#Eth-Trunk端口状态 GE0/0/10

        if( int(hwEntityTemperature) < self.mySnmp.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPower1) >self.mySnmp.hwEntitySOpticalTxPowerThreshold and
            int(hwEntityOpticalTxPower2) > self.mySnmp.hwEntitySOpticalTxPowerThreshold and
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
        hwEntityTemperature = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67108873')#MPU 温度
        hwEntityOpticalTxPower1 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67306062')#GE0/0/9 单模SPF模块功率
        hwEntityOpticalTxPower2 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67306126')#EGE0/0/10 单模SPF模块功率
        hwTrunkOperstatus15 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.15')#Eth-Trunk端口状态 GE0/0/9
        hwTrunkOperstatus16 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.16')#Eth-Trunk端口状态 GE0/0/10

        if( int(hwEntityTemperature) < self.mySnmp.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPower1) >self.mySnmp.hwEntitySOpticalTxPowerThreshold and
            int(hwEntityOpticalTxPower2) > self.mySnmp.hwEntitySOpticalTxPowerThreshold and
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
        hwEntityTemperature = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67108873')#MPU 温度
        hwEntityOpticalTxPower1 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67306062')#GE0/0/9 单模SPF模块功率
        hwTrunkOperstatus13 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.13')#Eth-Trunk端口状态 GE0/0/9

        if( int(hwEntityTemperature) < self.mySnmp.hwSwitchTemperatureThreshold and
            int(hwEntityOpticalTxPower1) >self.mySnmp.hwEntitySOpticalTxPowerThreshold and
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
        hwEntityTemperature = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67108873')#MPU 温度
        hwEntityOpticalTxPower1 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67305550')#GE0/0/1 单模SPF模块功率
        hwTrunkOperstatus1 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.31')#Eth-Trunk端口状态 GE0/0/1

        if( int(hwEntityTemperature) < self.mySnmp.hwSwitchTemperatureThreshold and
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
        hwEntityTemperature = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67108873')#MPU 温度
        hwEntityOpticalTxPower1 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67305550')#GE0/0/1 单模SPF模块功率
        hwTrunkOperstatus1 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.31')#Eth-Trunk端口状态 GE0/0/1

        if( int(hwEntityTemperature) < self.mySnmp.hwSwitchTemperatureThreshold and
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
        hwEntityTemperature = self.mySnmp.getSnmpValue(address, '.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11.67108873')#MPU 温度
        hwEntityOpticalTxPower1 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9.67305550')#GE0/0/1 单模SPF模块功率
        hwTrunkOperstatus1 = self.mySnmp.getSnmpValue(address,'.1.3.6.1.4.1.2011.5.25.41.1.4.1.1.6.0.31')#Eth-Trunk端口状态 GE0/0/1

        if( int(hwEntityTemperature) < self.mySnmp.hwSwitchTemperatureThreshold and
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

def main():
    # myBlHw = BlHw()
    # print myBlHw.getHW_BL_AGG()
    #
    # myBlDell = BlDell()
    # print myBlDell.getDelliDRAC6()[0]
    # print myBlDell.getDelliDRAC8()[1]
    #
    # myBlOther = BlOthers()
    # print myBlOther.get360TD()
    #
    # myFhHw = FhHw()
    # print myFhHw.getHW_FH_1_S1()
    pass


if __name__ == '__main__':
    main()


