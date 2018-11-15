# -*- coding:gbk -*-
__author__ = 'li.shida'

# -*- coding:gbk -*-
__author__ = 'li.shida'

try:

    import os.path
    from pysnmp.hlapi import *
    from  ConfigParser import ConfigParser
except ImportError:
    print 'ImportError'

__all__ = [
    "MySnmp"
]

class BydSnmp():
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
        config = ConfigParser()
        try:
            #获取BydSNMP.py执行时的绝对路径
            self.mainPath = os.path.dirname(os.path.realpath(__file__))
            configFile = os.path.join(self.mainPath,'config_snmp.ini')
            config.readfp(open(configFile, "rb"))
            self.configIniDict = dict(config._sections)
            for k in self.configIniDict:
                self.configIniDict[k] = dict(self.configIniDict[k])

            #获取常用配置信息
            self.snmp_port = int(self.configIniDict['Global']['port'])
            self.snmp_version = int(self.configIniDict['Global']['version'])
            self.snmp_communication = self.configIniDict['Global']['communication']

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
                        mibValue = [x.prettyPrint() for x in varBind][1] #S5700-52P-LI-AC
                        #只返回第一行（当字符串有多行时，仅返回第一行）
                        return mibValue[:].split('\r')[0]
        except Exception as e:
            print 'SmiError'

    def translateNum2Str(self,address,oid):
        '''
        将华为 MIB的OID数字值（如1/2/3)转换成字符串(如'ok','fault')
        :param address :IP Address
        :param oid: OID
        :return: 1=ok 其他=fault
        '''
        if(self.getSnmpValue(address, oid) =='1'):
            return 'ok'
        else:
            return 'fault'

    def getSangforSG(self):
        '''
        :param address: 深信服SG IP地址
        :return: 深信服SG OID信息
        '''
         #获取常用配置信息
        address = self.configIniDict['SANGFOR_SG']['ip'.lower()]
        oid_sfSysCpuCostRate = self.configIniDict['SANGFOR_SG']['sfSysCpuCostRate'.lower()]
        oid_numOfCurOnlin = self.configIniDict['SANGFOR_SG']['numOfCurOnlin'.lower()]
        oid_numOfSession = self.configIniDict['SANGFOR_SG']['numOfSession'.lower()]
        oid_ifTxBytes = self.configIniDict['SANGFOR_SG']['ifTxBytes'.lower()]
        oid_ifRxBytes = self.configIniDict['SANGFOR_SG']['ifRxBytes'.lower()]

        sfSysCpuCostRate = int(self.getSnmpValue(address, oid_sfSysCpuCostRate)) #当前CPU使用率
        numOfCurOnlin = int(self.getSnmpValue(address, oid_numOfCurOnlin)) #在线用户数
        numOfSession = int(self.getSnmpValue(address, oid_numOfSession)) #当前会话数
        ifTxKBs = int(self.getSnmpValue(address, oid_ifTxBytes))/1024 #Eth0端口发送速率
        ifRxKBs = int(self.getSnmpValue(address, oid_ifRxBytes))/1024 #Eth0端口接收速率
        print '\nSANGFOR SG Result:'
        print 'CPU使用率:'+str(sfSysCpuCostRate)+\
              '\n在线用户数:'+str(numOfCurOnlin)+\
              '\n在线会话数:'+str(numOfSession)+\
              '\nEth0发送速率(KB/s):'+str(ifTxKBs)+\
              '\nEth0接收速率(KB/s):'+str(ifRxKBs)

    def get360TD(self):
        '''

        :param address: 360天擎 IP地址
        :return: 360天擎 OID信息
        '''
         #获取常用配置信息
        address = self.configIniDict['360_TD']['ip'.lower()]
        oid_systemTemperature = self.configIniDict['360_TD']['systemTemperature'.lower()]
        oid_cpuPercentUsage = self.configIniDict['360_TD']['cpuPercentUsage'.lower()]
        oid_memoryPercentUsage = self.configIniDict['360_TD']['memoryPercentUsage'.lower()]
        oid_CFDiskPrcentUsage = self.configIniDict['360_TD']['CFDiskPrcentUsage'.lower()]
        oid_fanSpeedSpeed1 = self.configIniDict['360_TD']['fanSpeedSpeed1'.lower()]
        oid_fanSpeedSpeed2 = self.configIniDict['360_TD']['fanSpeedSpeed2'.lower()]
        oid_sessionCurrentNumber = self.configIniDict['360_TD']['sessionCurrentNumber'.lower()]
        oid_ifInBps5 = self.configIniDict['360_TD']['ifInBps.5'.lower()]
        oid_ifOutBps5 = self.configIniDict['360_TD']['ifOutBps.5'.lower()]

        systemTemperature = int(self.getSnmpValue(address, oid_systemTemperature)) #设备温度
        cpuPercentUsage = int(self.getSnmpValue(address, oid_cpuPercentUsage)) #CPU使用率
        memoryPercentUsage = int(self.getSnmpValue(address, oid_memoryPercentUsage)) #内存使用率
        CFDiskPrcentUsage = int(self.getSnmpValue(address, oid_CFDiskPrcentUsage)) #系统盘使用率
        fanSpeedSpeed1 = int(self.getSnmpValue(address, oid_fanSpeedSpeed1)) #系统风扇转速
        fanSpeedSpeed2 = int(self.getSnmpValue(address, oid_fanSpeedSpeed2)) #CPU风扇转速
        sessionCurrentNumber = int(self.getSnmpValue(address, oid_sessionCurrentNumber)) #当前会话数
        ifInBps5 = int(self.getSnmpValue(address, oid_ifInBps5))/1024/8 #进系统速率(惠州到宁波）bps/s
        ifOutBps5 = int(self.getSnmpValue(address, oid_ifOutBps5))/1024/8 #出系统速率（宁波到惠州）bps/s

        print '\n360 TD Result:'
        print '设备温度:'+str(systemTemperature)+\
              '\nCPU使用率:'+str(cpuPercentUsage)+\
              '\n内存使用率:'+str(memoryPercentUsage)+\
              '\n系统盘使用率:'+str(CFDiskPrcentUsage)+\
              '\n系统风扇转速:'+str(fanSpeedSpeed1)+\
              '\nCPU风扇转速:'+str(fanSpeedSpeed2)+\
              '\n当前会话数:'+str(sessionCurrentNumber)+\
              '\n惠州到宁波流量(KB/s):'+str(ifInBps5)+\
              '\n宁波到惠州流量(KB/s):'+str(ifOutBps5)

    def getDellCMC(self):
        '''
        :param address: CMC 地址
        :return: CMC oid信息
        '''
        #获取常用配置信息
        address = self.configIniDict['Dell_CMC']['ip'.lower()]
        oid_drsCMCAmbientTemperature = self.configIniDict['Dell_CMC']['drsCMCAmbientTemperature'.lower()]
        oid_drsGlobalSystemStaus = self.configIniDict['Dell_CMC']['drsGlobalSystemStaus'.lower()]

        drsCMCAmbientTemperatur = int(self.getSnmpValue(address, oid_drsCMCAmbientTemperature)) #环境温度
        num_drsGlobalSystemStaus = int(self.getSnmpValue(address, oid_drsGlobalSystemStaus)) #全局状态,3表示OK
        if(num_drsGlobalSystemStaus == 3):
            drsGlobalSystemStaus = 'ok'
        else:
            drsGlobalSystemStaus = 'fault'

        print '\nDell CMC Result:'
        print '环境温度:'+str(drsCMCAmbientTemperatur)+\
              '\n全局状态:'+str(drsGlobalSystemStaus)

    def getDelliDRAC6(self,address):
        '''
        :param address:
        :return:
        '''
        oid_globalSystemStatus = self.configIniDict['Dell_iDRAC6']['drsGlobalSystemStaus'.lower()]
        num_globalSystemStatus = int(self.getSnmpValue(address, oid_globalSystemStatus)) #全局状态,3表示OK

        if(num_globalSystemStatus == 3):
            globalSystemStatus = 'ok'
        else:
            globalSystemStatus = 'fault'

        #print 'Dell R710/R710HD Result:'
        #print '全局状态:'+str(globalSystemStatus)
        return globalSystemStatus

    def getDelliDRAC8(self,address):
        '''
        :param address: Dell R730/R630HD
        :return: OID信息
        '''
        oid_globalSystemStatus = self.configIniDict['Dell_iDRAC8']['globalSystemStatus'.lower()]
        num_globalSystemStatus = int(self.getSnmpValue(address, oid_globalSystemStatus)) #全局状态,3表示OK
        if(num_globalSystemStatus == 3):
            globalSystemStatus = 'ok'
        else:
            globalSystemStatus = 'fault'

        #print '\nDell R730/R630HD Result:'
        #print '全局状态:'+str(globalSystemStatus)
        return globalSystemStatus

    def getDellAllStatus(self):
        '''
        :return: 所有DELL服务器(基于iDRAC6 & 8版本)，如R710/R730/M630/M730
        '''

        print '\nDell R710/R710HD Result:'
        iDRAC6ServerDict =  self.configIniDict['Dell_iDRAC6_Servers']
        for hostname,ip in iDRAC6ServerDict.items():
            if (hostname != '__name__'):
                print '主机名:'+hostname+'全局状态:'+self.getDelliDRAC6(ip)

        print '\nDell R730/R630HD Result:'
        iDRAC8ServerDict =  self.configIniDict['Dell_iDRAC8_Servers']
        for hostname,ip in iDRAC8ServerDict.items():
            if (hostname != '__name__'):
                print '主机名:'+hostname+'全局状态:'+self.getDelliDRAC8(ip)

    def checkDellAll(self):
        '''
        :return:Dell 服务器状态
        '''

        print '\nCheck Dell Server Status:'
        iDRAC6ServerDict =  self.configIniDict['Dell_iDRAC6_Servers']
        for hostname,ip in iDRAC6ServerDict.items():
            if (hostname != '__name__'):
                if (self.getDelliDRAC6(ip) != 'ok'):
                    print 'ERROR'+':'+hostname
                else:
                    continue

        iDRAC8ServerDict =  self.configIniDict['Dell_iDRAC8_Servers']
        for hostname,ip in iDRAC8ServerDict.items():
            if (hostname != '__name__'):
                #print '主机名:'+hostname
                if(self.getDelliDRAC8(ip) != 'ok'):
                    print 'ERROR'+':'+hostname

    def getHW_BL_LJ_1(self):
        address = self.configIniDict['HW_BL_LJ-1']['ip'.lower()]
        oid_hwEntityTemperature = self.configIniDict['HW_BL_LJ-1']['hwEntityTemperature.67108873'.lower()]
        oid_hwTrunkOperstatus5 = self.configIniDict['HW_BL_LJ-1']['hwTrunkOperstatus.0.5'.lower()]
        oid_hwTrunkOperstatus6 = self.configIniDict['HW_BL_LJ-1']['hwTrunkOperstatus.0.6'.lower()]

        #MPU 温度
        hwEntityTemperature = self.getSnmpValue(address, oid_hwEntityTemperature)

        #Eth-Trunk端口状态 GE0/0/1
        hwTrunkOperstatus5 = self.translateNum2Str(address, oid_hwTrunkOperstatus5)
        #Eth-Trunk端口状态 GE0/0/2
        hwTrunkOperstatus6 = self.translateNum2Str(address, oid_hwTrunkOperstatus6)

        print '\nHW_BL_LJ-1 Result:'
        print 'MPU温度:'+hwEntityTemperature+\
              '\nEth-Trunk成员(GE0/0/1)状态:'+hwTrunkOperstatus5+\
              '\nEth-Trunk成员(GE0/0/2)状态:'+hwTrunkOperstatus6

    def getHW_BL_LJ_2(self):
        address = self.configIniDict['HW_BL_LJ-2']['ip'.lower()]
        oid_hwEntityTemperature = self.configIniDict['HW_BL_LJ-2']['hwEntityTemperature.67108873'.lower()]
        oid_hwTrunkOperstatus5 = self.configIniDict['HW_BL_LJ-2']['hwTrunkOperstatus.0.5'.lower()]
        oid_hwTrunkOperstatus6 = self.configIniDict['HW_BL_LJ-2']['hwTrunkOperstatus.0.6'.lower()]

        #MPU 温度
        hwEntityTemperature = self.getSnmpValue(address, oid_hwEntityTemperature)

        #Eth-Trunk端口状态 GE0/0/1
        hwTrunkOperstatus5 = self.translateNum2Str(address, oid_hwTrunkOperstatus5)
        #Eth-Trunk端口状态 GE0/0/2
        hwTrunkOperstatus6 = self.translateNum2Str(address, oid_hwTrunkOperstatus6)

        print '\nHW_BL_LJ-2 Result:'
        print 'MPU温度:'+hwEntityTemperature+\
              '\nEth-Trunk成员(GE0/0/1)状态:'+hwTrunkOperstatus5+\
              '\nEth-Trunk成员(GE0/0/2)状态:'+hwTrunkOperstatus6

    def getHW_BL_CUB3F(self):
        address = self.configIniDict['HW_BL_CUB3F']['ip'.lower()]
        oid_hwEntityFanState = self.configIniDict['HW_BL_CUB3F']['hwEntityFanState.0.0'.lower()]
        oid_hwEntityTemperature = self.configIniDict['HW_BL_CUB3F']['hwEntityTemperature.67108873'.lower()]
        oid_hwEntityOpticalTxPower = self.configIniDict['HW_BL_CUB3F']['hwEntityOpticalTxPower.67308622'.lower()]
        oid_hwTrunkOperstatus53 = self.configIniDict['HW_BL_CUB3F']['hwTrunkOperstatus.0.53'.lower()]

        #MPU 温度
        hwEntityTemperature = self.getSnmpValue(address, oid_hwEntityTemperature)
        #GE0/0/49 SPF模块功率
        hwEntityOpticalTxPower = self.getSnmpValue(address, oid_hwEntityOpticalTxPower)

        #MPU 风扇状态
        hwEntityFanState = self.translateNum2Str(address, oid_hwEntityFanState)

        #Eth-Trunk(GE0/0/49)端口状态
        hwTrunkOperstatus53 = self.translateNum2Str(address, oid_hwTrunkOperstatus53)

        print '\nHW_BL_CUB3F Result:'
        print 'MPU温度:'+hwEntityTemperature+\
              '\n风扇状态:'+hwEntityFanState+\
              '\nSPF(GE0/0/49)功率(mW):'+hwEntityOpticalTxPower+\
              '\nEth-Trunk成员(GE0/0/49)状态:'+hwTrunkOperstatus53

    def getHW_BL_OFF4FTD(self):
        address = self.configIniDict['HW_BL_OFF4FTD']['ip'.lower()]
        oid_hwEntityFanState = self.configIniDict['HW_BL_OFF4FTD']['hwEntityFanState.1.0'.lower()]
        oid_hwEntityTemperature = self.configIniDict['HW_BL_OFF4FTD']['hwEntityTemperature.67371017'.lower()]
        oid_hwTrunkOperstatus53 = self.configIniDict['HW_BL_OFF4FTD']['hwTrunkOperstatus.0.53'.lower()]

        #MPU 温度
        hwEntityTemperature = self.getSnmpValue(address, oid_hwEntityTemperature)

        #MPU 风扇状态
        hwEntityFanState = self.translateNum2Str(address, oid_hwEntityFanState)

        #Eth-Trunk(GE1/0/47)端口状态
        hwTrunkOperstatus53 = self.translateNum2Str(address, oid_hwTrunkOperstatus53)

        print '\nHW_BL_OFF4FTD Result:'
        print 'MPU温度:'+hwEntityTemperature+\
              '\n风扇状态:'+hwEntityFanState+\
              '\nEth-Trunk成员(GE1/0/47)状态:'+hwTrunkOperstatus53

    def getHW_BL_PUB1F(self):
        address = self.configIniDict['HW_BL_PUB1F']['ip'.lower()]
        oid_hwEntityFanState = self.configIniDict['HW_BL_PUB1F']['hwEntityFanState.0.0'.lower()]
        oid_hwEntityTemperature = self.configIniDict['HW_BL_PUB1F']['hwEntityTemperature.67108873'.lower()]
        oid_hwEntityOpticalTxPower = self.configIniDict['HW_BL_PUB1F']['hwEntityOpticalTxPower.67308622'.lower()]
        oid_hwTrunkOperstatus55 = self.configIniDict['HW_BL_PUB1F']['hwTrunkOperstatus.0.55'.lower()]

        #MPU 温度
        hwEntityTemperature = self.getSnmpValue(address, oid_hwEntityTemperature)
        #GE0/0/49 SPF模块功率
        hwEntityOpticalTxPower = self.getSnmpValue(address, oid_hwEntityOpticalTxPower)

        #MPU 风扇状态
        hwEntityFanState = self.translateNum2Str(address, oid_hwEntityFanState)

        #Eth-Trunk(GE0/0/49)端口状态
        hwTrunkOperstatus55 = self.translateNum2Str(address, oid_hwTrunkOperstatus55)

        print '\nHW_BL_PUB1F Result:'
        print 'MPU温度:'+hwEntityTemperature+\
              '\n风扇状态:'+hwEntityFanState+\
              '\nSPF(GE0/0/49)功率(mW):'+hwEntityOpticalTxPower+\
              '\nEth-Trunk成员(GE0/0/49)状态:'+hwTrunkOperstatus55

    def getHW_BL_DaMen(self):
        address = self.configIniDict['HW_BL_DaMen']['ip'.lower()]
        oid_hwEntityTemperature = self.configIniDict['HW_BL_DaMen']['hwEntityTemperature.67108873'.lower()]
        oid_hwTrunkOperstatus28 = self.configIniDict['HW_BL_DaMen']['hwTrunkOperstatus.0.28'.lower()]

        #MPU 温度
        hwEntityTemperature = self.getSnmpValue(address, oid_hwEntityTemperature)

        #Eth-Trunk(GE0/0/24)端口状态
        hwTrunkOperstatus28 = self.translateNum2Str(address, oid_hwTrunkOperstatus28)

        print '\nHW_BL_DaMen Result:'
        print 'MPU温度:'+hwEntityTemperature+\
              '\nEth-Trunk成员(GE0/0/24)状态:'+hwTrunkOperstatus28

    def getHW_BL_OFF1F_1(self):
        address = self.configIniDict['HW_BL_OFF1F-1']['ip'.lower()]
        oid_hwEntityFanState1 = self.configIniDict['HW_BL_OFF1F-1']['hwEntityFanState.1.0'.lower()]
        oid_hwEntityFanState2 = self.configIniDict['HW_BL_OFF1F-1']['hwEntityFanState.2.0'.lower()]
        oid_hwEntityTemperature1 = self.configIniDict['HW_BL_OFF1F-1']['hwEntityTemperature.67371017'.lower()]
        oid_hwEntityTemperature2 = self.configIniDict['HW_BL_OFF1F-1']['hwEntityTemperature.67633161'.lower()]
        oid_hwEntityOpticalTxPower1 = self.configIniDict['HW_BL_OFF1F-1']['hwEntityOpticalTxPower.67570766'.lower()]
        oid_hwEntityOpticalTxPower2 = self.configIniDict['HW_BL_OFF1F-1']['hwEntityOpticalTxPower.67832910'.lower()]
        oid_hwTrunkOperstatus55 = self.configIniDict['HW_BL_OFF1F-1']['hwTrunkOperstatus.0.55'.lower()]
        oid_hwTrunkOperstatus107 = self.configIniDict['HW_BL_OFF1F-1']['hwTrunkOperstatus.0.107'.lower()]
        oid_hwStackPortStatus1 = self.configIniDict['HW_BL_OFF1F-1']['hwStackPortStatus.1.0'.lower()]
        oid_hwStackPortStatus2 = self.configIniDict['HW_BL_OFF1F-1']['hwStackPortStatus.2.1'.lower()]

        #MPU 1温度
        hwEntityTemperature1 = self.getSnmpValue(address, oid_hwEntityTemperature1)
        hwEntityTemperature2 = self.getSnmpValue(address, oid_hwEntityTemperature2)
        #MPU 2温度
        #GE1/0/49 & 2/0/49 SPF模块功率
        hwEntityOpticalTxPower1 = self.getSnmpValue(address, oid_hwEntityOpticalTxPower1)
        hwEntityOpticalTxPower2 = self.getSnmpValue(address, oid_hwEntityOpticalTxPower2)

        #MPU 1风扇状态
        hwEntityFanState1 = self.translateNum2Str(address, oid_hwEntityFanState1)
        #MPU 2风扇状态
        hwEntityFanState2 = self.translateNum2Str(address, oid_hwEntityFanState2)

        #Eth-Trunk(GE1/0/49)端口状态
        hwTrunkOperstatus55 = self.translateNum2Str(address, oid_hwTrunkOperstatus55)
        #Eth-Trunk(GE2/0/49)端口状态
        hwTrunkOperstatus107 = self.translateNum2Str(address, oid_hwTrunkOperstatus107)

        #Stack(GE1/0/51)端口状态
        hwStackPortStatus1 = self.translateNum2Str(address, oid_hwStackPortStatus1)
        #Stack(GE2/0/52)端口状态
        hwStackPortStatus2 = self.translateNum2Str(address, oid_hwStackPortStatus2)

        print '\nHW_BL_OFF1F-1 Result:'
        print 'MPU1温度:'+hwEntityTemperature1+\
              '\nMPU2温度:'+hwEntityTemperature2+\
              '\n风扇1状态:'+hwEntityFanState1+\
              '\n风扇2状态:'+hwEntityFanState2+\
              '\nSPF(GE1/0/49)功率(mW):'+hwEntityOpticalTxPower1+\
              '\nSPF(GE2/0/49)功率(mW):'+hwEntityOpticalTxPower2+\
              '\nEth-Trunk成员(GE1/0/49)状态:'+hwTrunkOperstatus55+\
              '\nEth-Trunk成员(GE2/0/49)状态:'+hwTrunkOperstatus107+\
              '\nStack成员(GE1/0/51)状态:'+hwStackPortStatus1+\
              '\nStack成员(GE2/0/52)状态:'+hwStackPortStatus2

    def getHW_BL_OFF1F_2(self):
        address = self.configIniDict['HW_BL_OFF1F-2']['ip'.lower()]
        oid_hwEntityFanState1 = self.configIniDict['HW_BL_OFF1F-2']['hwEntityFanState.1.0'.lower()]
        oid_hwEntityFanState2 = self.configIniDict['HW_BL_OFF1F-2']['hwEntityFanState.2.0'.lower()]
        oid_hwEntityTemperature1 = self.configIniDict['HW_BL_OFF1F-2']['hwEntityTemperature.67371017'.lower()]
        oid_hwEntityTemperature2 = self.configIniDict['HW_BL_OFF1F-2']['hwEntityTemperature.67633161'.lower()]
        oid_hwEntityOpticalTxPower1 = self.configIniDict['HW_BL_OFF1F-2']['hwEntityOpticalTxPower.67570766'.lower()]
        oid_hwEntityOpticalTxPower2 = self.configIniDict['HW_BL_OFF1F-2']['hwEntityOpticalTxPower.67832910'.lower()]
        oid_hwTrunkOperstatus55 = self.configIniDict['HW_BL_OFF1F-2']['hwTrunkOperstatus.0.55'.lower()]
        oid_hwTrunkOperstatus107 = self.configIniDict['HW_BL_OFF1F-2']['hwTrunkOperstatus.0.107'.lower()]
        oid_hwStackPortStatus1 = self.configIniDict['HW_BL_OFF1F-2']['hwStackPortStatus.1.0'.lower()]
        oid_hwStackPortStatus2 = self.configIniDict['HW_BL_OFF1F-2']['hwStackPortStatus.2.1'.lower()]

        #MPU 1温度
        hwEntityTemperature1 = self.getSnmpValue(address, oid_hwEntityTemperature1)
        hwEntityTemperature2 = self.getSnmpValue(address, oid_hwEntityTemperature2)
        #MPU 2温度
        #GE1/0/49 & 2/0/49 SPF模块功率
        hwEntityOpticalTxPower1 = self.getSnmpValue(address, oid_hwEntityOpticalTxPower1)
        hwEntityOpticalTxPower2 = self.getSnmpValue(address, oid_hwEntityOpticalTxPower2)

        #MPU 1风扇状态
        hwEntityFanState1 = self.translateNum2Str(address, oid_hwEntityFanState1)
        #MPU 2风扇状态
        hwEntityFanState2 = self.translateNum2Str(address, oid_hwEntityFanState2)

        #Eth-Trunk(GE1/0/49)端口状态
        hwTrunkOperstatus55 = self.translateNum2Str(address, oid_hwTrunkOperstatus55)
        #Eth-Trunk(GE2/0/49)端口状态
        hwTrunkOperstatus107 = self.translateNum2Str(address, oid_hwTrunkOperstatus107)

        #Stack(GE1/0/51)端口状态
        hwStackPortStatus1 = self.translateNum2Str(address, oid_hwStackPortStatus1)
        #Stack(GE2/0/52)端口状态
        hwStackPortStatus2 = self.translateNum2Str(address, oid_hwStackPortStatus2)

        print '\nHW_BL_OFF1F-2 Result:'
        print 'MPU1温度:'+hwEntityTemperature1+\
              '\nMPU2温度:'+hwEntityTemperature2+\
              '\n风扇1状态:'+hwEntityFanState1+\
              '\n风扇2状态:'+hwEntityFanState2+\
              '\nSPF(GE1/0/49)功率(mW):'+hwEntityOpticalTxPower1+\
              '\nSPF(GE2/0/49)功率(mW):'+hwEntityOpticalTxPower2+\
              '\nEth-Trunk成员(GE1/0/49)状态:'+hwTrunkOperstatus55+\
              '\nEth-Trunk成员(GE2/0/49)状态:'+hwTrunkOperstatus107+\
              '\nStack成员(GE1/0/51)状态:'+hwStackPortStatus1+\
              '\nStack成员(GE2/0/52)状态:'+hwStackPortStatus2

    def getHW_BL_OFF1F_3(self):
        address = self.configIniDict['HW_BL_OFF1F-3']['ip'.lower()]
        oid_hwEntityFanState1 = self.configIniDict['HW_BL_OFF1F-3']['hwEntityFanState.1.0'.lower()]
        oid_hwEntityFanState2 = self.configIniDict['HW_BL_OFF1F-3']['hwEntityFanState.2.0'.lower()]
        oid_hwEntityTemperature1 = self.configIniDict['HW_BL_OFF1F-3']['hwEntityTemperature.67371017'.lower()]
        oid_hwEntityTemperature2 = self.configIniDict['HW_BL_OFF1F-3']['hwEntityTemperature.67633161'.lower()]
        oid_hwEntityOpticalTxPower1 = self.configIniDict['HW_BL_OFF1F-3']['hwEntityOpticalTxPower.67570766'.lower()]
        oid_hwEntityOpticalTxPower2 = self.configIniDict['HW_BL_OFF1F-3']['hwEntityOpticalTxPower.67832910'.lower()]
        oid_hwTrunkOperstatus54 = self.configIniDict['HW_BL_OFF1F-3']['hwTrunkOperstatus.0.54'.lower()]
        oid_hwTrunkOperstatus158 = self.configIniDict['HW_BL_OFF1F-3']['hwTrunkOperstatus.0.158'.lower()]
        oid_hwStackPortStatus1 = self.configIniDict['HW_BL_OFF1F-3']['hwStackPortStatus.1.0'.lower()]
        oid_hwStackPortStatus2 = self.configIniDict['HW_BL_OFF1F-3']['hwStackPortStatus.2.1'.lower()]

        #MPU 1温度
        hwEntityTemperature1 = self.getSnmpValue(address, oid_hwEntityTemperature1)
        hwEntityTemperature2 = self.getSnmpValue(address, oid_hwEntityTemperature2)
        #MPU 2温度
        #GE1/0/49 & 2/0/49 SPF模块功率
        hwEntityOpticalTxPower1 = self.getSnmpValue(address, oid_hwEntityOpticalTxPower1)
        hwEntityOpticalTxPower2 = self.getSnmpValue(address, oid_hwEntityOpticalTxPower2)

        #MPU 1风扇状态
        hwEntityFanState1 = self.translateNum2Str(address, oid_hwEntityFanState1)
        #MPU 2风扇状态
        hwEntityFanState2 = self.translateNum2Str(address, oid_hwEntityFanState2)

        #Eth-Trunk(GE1/0/49)端口状态
        hwTrunkOperstatus54 = self.translateNum2Str(address, oid_hwTrunkOperstatus54)
        #Eth-Trunk(GE2/0/49)端口状态
        hwTrunkOperstatus158 = self.translateNum2Str(address, oid_hwTrunkOperstatus158)

        #Stack(GE1/0/51)端口状态
        hwStackPortStatus1 = self.translateNum2Str(address, oid_hwStackPortStatus1)
        #Stack(GE2/0/52)端口状态
        hwStackPortStatus2 = self.translateNum2Str(address, oid_hwStackPortStatus2)

        print '\nHW_BL_OFF1F-3 Result:'
        print 'MPU1温度:'+hwEntityTemperature1+\
              '\nMPU2温度:'+hwEntityTemperature2+\
              '\n风扇1状态:'+hwEntityFanState1+\
              '\n风扇2状态:'+hwEntityFanState2+\
              '\nSPF(GE1/0/49)功率(mW):'+hwEntityOpticalTxPower1+\
              '\nSPF(GE2/0/49)功率(mW):'+hwEntityOpticalTxPower2+\
              '\nEth-Trunk成员(GE1/0/49)状态:'+hwTrunkOperstatus54+\
              '\nEth-Trunk成员(GE2/0/49)状态:'+hwTrunkOperstatus158+\
              '\nStack成员(GE1/0/51)状态:'+hwStackPortStatus1+\
              '\nStack成员(GE2/0/52)状态:'+hwStackPortStatus2

    def getHW_BL_OFF2F_1(self):
        address = self.configIniDict['HW_BL_OFF2F-1']['ip'.lower()]
        oid_hwEntityFanState1 = self.configIniDict['HW_BL_OFF2F-1']['hwEntityFanState.1.0'.lower()]
        oid_hwEntityFanState2 = self.configIniDict['HW_BL_OFF2F-1']['hwEntityFanState.2.0'.lower()]
        oid_hwEntityTemperature1 = self.configIniDict['HW_BL_OFF2F-1']['hwEntityTemperature.67371017'.lower()]
        oid_hwEntityTemperature2 = self.configIniDict['HW_BL_OFF2F-1']['hwEntityTemperature.67633161'.lower()]
        oid_hwEntityOpticalTxPower1 = self.configIniDict['HW_BL_OFF2F-1']['hwEntityOpticalTxPower.67570766'.lower()]
        oid_hwEntityOpticalTxPower2 = self.configIniDict['HW_BL_OFF2F-1']['hwEntityOpticalTxPower.67832910'.lower()]
        oid_hwTrunkOperstatus55 = self.configIniDict['HW_BL_OFF2F-1']['hwTrunkOperstatus.0.55'.lower()]
        oid_hwTrunkOperstatus107 = self.configIniDict['HW_BL_OFF2F-1']['hwTrunkOperstatus.0.107'.lower()]
        oid_hwStackPortStatus1 = self.configIniDict['HW_BL_OFF2F-1']['hwStackPortStatus.1.0'.lower()]
        oid_hwStackPortStatus2 = self.configIniDict['HW_BL_OFF2F-1']['hwStackPortStatus.2.1'.lower()]

        #MPU 1温度
        hwEntityTemperature1 = self.getSnmpValue(address, oid_hwEntityTemperature1)
        hwEntityTemperature2 = self.getSnmpValue(address, oid_hwEntityTemperature2)
        #MPU 2温度
        #GE1/0/49 & 2/0/49 SPF模块功率
        hwEntityOpticalTxPower1 = self.getSnmpValue(address, oid_hwEntityOpticalTxPower1)
        hwEntityOpticalTxPower2 = self.getSnmpValue(address, oid_hwEntityOpticalTxPower2)

        #MPU 1风扇状态
        hwEntityFanState1 = self.translateNum2Str(address, oid_hwEntityFanState1)
        #MPU 2风扇状态
        hwEntityFanState2 = self.translateNum2Str(address, oid_hwEntityFanState2)

        #Eth-Trunk(GE1/0/49)端口状态
        hwTrunkOperstatus55 = self.translateNum2Str(address, oid_hwTrunkOperstatus55)
        #Eth-Trunk(GE2/0/49)端口状态
        hwTrunkOperstatus107 = self.translateNum2Str(address, oid_hwTrunkOperstatus107)

        #Stack(GE1/0/51)端口状态
        hwStackPortStatus1 = self.translateNum2Str(address, oid_hwStackPortStatus1)
        #Stack(GE2/0/52)端口状态
        hwStackPortStatus2 = self.translateNum2Str(address, oid_hwStackPortStatus2)

        print '\nHW_BL_OFF2F-1 Result:'
        print 'MPU1温度:'+hwEntityTemperature1+\
              '\nMPU2温度:'+hwEntityTemperature2+\
              '\n风扇1状态:'+hwEntityFanState1+\
              '\n风扇2状态:'+hwEntityFanState2+\
              '\nSPF(GE1/0/49)功率(mW):'+hwEntityOpticalTxPower1+\
              '\nSPF(GE2/0/49)功率(mW):'+hwEntityOpticalTxPower2+\
              '\nEth-Trunk成员(GE1/0/49)状态:'+hwTrunkOperstatus55+\
              '\nEth-Trunk成员(GE2/0/49)状态:'+hwTrunkOperstatus107+\
              '\nStack成员(GE1/0/51)状态:'+hwStackPortStatus1+\
              '\nStack成员(GE2/0/52)状态:'+hwStackPortStatus2

    def getHW_BL_OFF2F_2(self):
        address = self.configIniDict['HW_BL_OFF2F-2']['ip'.lower()]
        oid_hwEntityFanState1 = self.configIniDict['HW_BL_OFF2F-2']['hwEntityFanState.1.0'.lower()]
        oid_hwEntityFanState2 = self.configIniDict['HW_BL_OFF2F-2']['hwEntityFanState.2.0'.lower()]
        oid_hwEntityTemperature1 = self.configIniDict['HW_BL_OFF2F-2']['hwEntityTemperature.67371017'.lower()]
        oid_hwEntityTemperature2 = self.configIniDict['HW_BL_OFF2F-2']['hwEntityTemperature.67633161'.lower()]
        oid_hwEntityOpticalTxPower1 = self.configIniDict['HW_BL_OFF2F-2']['hwEntityOpticalTxPower.67570766'.lower()]
        oid_hwEntityOpticalTxPower2 = self.configIniDict['HW_BL_OFF2F-2']['hwEntityOpticalTxPower.67832910'.lower()]
        oid_hwTrunkOperstatus55 = self.configIniDict['HW_BL_OFF2F-2']['hwTrunkOperstatus.0.55'.lower()]
        oid_hwTrunkOperstatus107 = self.configIniDict['HW_BL_OFF2F-2']['hwTrunkOperstatus.0.107'.lower()]
        oid_hwStackPortStatus1 = self.configIniDict['HW_BL_OFF2F-2']['hwStackPortStatus.1.0'.lower()]
        oid_hwStackPortStatus2 = self.configIniDict['HW_BL_OFF2F-2']['hwStackPortStatus.2.1'.lower()]

        #MPU 1温度
        hwEntityTemperature1 = self.getSnmpValue(address, oid_hwEntityTemperature1)
        hwEntityTemperature2 = self.getSnmpValue(address, oid_hwEntityTemperature2)
        #MPU 2温度
        #GE1/0/49 & 2/0/49 SPF模块功率
        hwEntityOpticalTxPower1 = self.getSnmpValue(address, oid_hwEntityOpticalTxPower1)
        hwEntityOpticalTxPower2 = self.getSnmpValue(address, oid_hwEntityOpticalTxPower2)

        #MPU 1风扇状态
        hwEntityFanState1 = self.translateNum2Str(address, oid_hwEntityFanState1)
        #MPU 2风扇状态
        hwEntityFanState2 = self.translateNum2Str(address, oid_hwEntityFanState2)

        #Eth-Trunk(GE1/0/49)端口状态
        hwTrunkOperstatus55 = self.translateNum2Str(address, oid_hwTrunkOperstatus55)
        #Eth-Trunk(GE2/0/49)端口状态
        hwTrunkOperstatus107 = self.translateNum2Str(address, oid_hwTrunkOperstatus107)

        #Stack(GE1/0/51)端口状态
        hwStackPortStatus1 = self.translateNum2Str(address, oid_hwStackPortStatus1)
        #Stack(GE2/0/52)端口状态
        hwStackPortStatus2 = self.translateNum2Str(address, oid_hwStackPortStatus2)

        print '\nHW_BL_OFF2F-2 Result:'
        print 'MPU1温度:'+hwEntityTemperature1+\
              '\nMPU2温度:'+hwEntityTemperature2+\
              '\n风扇1状态:'+hwEntityFanState1+\
              '\n风扇2状态:'+hwEntityFanState2+\
              '\nSPF(GE1/0/49)功率(mW):'+hwEntityOpticalTxPower1+\
              '\nSPF(GE2/0/49)功率(mW):'+hwEntityOpticalTxPower2+\
              '\nEth-Trunk成员(GE1/0/49)状态:'+hwTrunkOperstatus55+\
              '\nEth-Trunk成员(GE2/0/49)状态:'+hwTrunkOperstatus107+\
              '\nStack成员(GE1/0/51)状态:'+hwStackPortStatus1+\
              '\nStack成员(GE2/0/52)状态:'+hwStackPortStatus2

    def getHW_BL_OFF2F_3(self):
        address = self.configIniDict['HW_BL_OFF2F-3']['ip'.lower()]
        oid_hwEntityFanState1 = self.configIniDict['HW_BL_OFF2F-3']['hwEntityFanState.1.0'.lower()]
        oid_hwEntityFanState2 = self.configIniDict['HW_BL_OFF2F-3']['hwEntityFanState.2.0'.lower()]
        oid_hwEntityTemperature1 = self.configIniDict['HW_BL_OFF2F-3']['hwEntityTemperature.67371017'.lower()]
        oid_hwEntityTemperature2 = self.configIniDict['HW_BL_OFF2F-3']['hwEntityTemperature.67633161'.lower()]
        oid_hwEntityOpticalTxPower1 = self.configIniDict['HW_BL_OFF2F-3']['hwEntityOpticalTxPower.67570766'.lower()]
        oid_hwEntityOpticalTxPower2 = self.configIniDict['HW_BL_OFF2F-3']['hwEntityOpticalTxPower.67832910'.lower()]
        oid_hwTrunkOperstatus55 = self.configIniDict['HW_BL_OFF2F-3']['hwTrunkOperstatus.0.55'.lower()]
        oid_hwTrunkOperstatus107 = self.configIniDict['HW_BL_OFF2F-3']['hwTrunkOperstatus.0.107'.lower()]
        oid_hwStackPortStatus1 = self.configIniDict['HW_BL_OFF2F-3']['hwStackPortStatus.1.0'.lower()]
        oid_hwStackPortStatus2 = self.configIniDict['HW_BL_OFF2F-3']['hwStackPortStatus.2.1'.lower()]

        #MPU 1温度
        hwEntityTemperature1 = self.getSnmpValue(address, oid_hwEntityTemperature1)
        hwEntityTemperature2 = self.getSnmpValue(address, oid_hwEntityTemperature2)
        #MPU 2温度
        #GE1/0/49 & 2/0/49 SPF模块功率
        hwEntityOpticalTxPower1 = self.getSnmpValue(address, oid_hwEntityOpticalTxPower1)
        hwEntityOpticalTxPower2 = self.getSnmpValue(address, oid_hwEntityOpticalTxPower2)

        #MPU 1风扇状态
        hwEntityFanState1 = self.translateNum2Str(address, oid_hwEntityFanState1)
        #MPU 2风扇状态
        hwEntityFanState2 = self.translateNum2Str(address, oid_hwEntityFanState2)

        #Eth-Trunk(GE1/0/49)端口状态
        hwTrunkOperstatus55 = self.translateNum2Str(address, oid_hwTrunkOperstatus55)
        #Eth-Trunk(GE2/0/49)端口状态
        hwTrunkOperstatus107 = self.translateNum2Str(address, oid_hwTrunkOperstatus107)

        #Stack(GE1/0/51)端口状态
        hwStackPortStatus1 = self.translateNum2Str(address, oid_hwStackPortStatus1)
        #Stack(GE2/0/52)端口状态
        hwStackPortStatus2 = self.translateNum2Str(address, oid_hwStackPortStatus2)

        print '\nHW_BL_OFF2F-3 Result:'
        print 'MPU1温度:'+hwEntityTemperature1+\
              '\nMPU2温度:'+hwEntityTemperature2+\
              '\n风扇1状态:'+hwEntityFanState1+\
              '\n风扇2状态:'+hwEntityFanState2+\
              '\nSPF(GE1/0/49)功率(mW):'+hwEntityOpticalTxPower1+\
              '\nSPF(GE2/0/49)功率(mW):'+hwEntityOpticalTxPower2+\
              '\nEth-Trunk成员(GE1/0/49)状态:'+hwTrunkOperstatus55+\
              '\nEth-Trunk成员(GE2/0/49)状态:'+hwTrunkOperstatus107+\
              '\nStack成员(GE1/0/51)状态:'+hwStackPortStatus1+\
              '\nStack成员(GE2/0/52)状态:'+hwStackPortStatus2

    def getHW_BL_OFF4F(self):
        address = self.configIniDict['HW_BL_OFF4F']['ip'.lower()]
        oid_hwEntityFanState1 = self.configIniDict['HW_BL_OFF4F']['hwEntityFanState.1.0'.lower()]
        oid_hwEntityFanState2 = self.configIniDict['HW_BL_OFF4F']['hwEntityFanState.2.0'.lower()]
        oid_hwEntityFanState3 = self.configIniDict['HW_BL_OFF4F']['hwEntityFanState.3.0'.lower()]
        oid_hwEntityTemperature1 = self.configIniDict['HW_BL_OFF4F']['hwEntityTemperature.67371017'.lower()]
        oid_hwEntityTemperature2 = self.configIniDict['HW_BL_OFF4F']['hwEntityTemperature.67633161'.lower()]
        oid_hwEntityTemperature3 = self.configIniDict['HW_BL_OFF4F']['hwEntityTemperature.67895305'.lower()]
        oid_hwEntityOpticalTxPower1 = self.configIniDict['HW_BL_OFF4F']['hwEntityOpticalTxPower.67570766'.lower()]
        oid_hwEntityOpticalTxPower2 = self.configIniDict['HW_BL_OFF4F']['hwEntityOpticalTxPower.68095054'.lower()]
        oid_hwTrunkOperstatus55 = self.configIniDict['HW_BL_OFF4F']['hwTrunkOperstatus.0.55'.lower()]
        oid_hwTrunkOperstatus159 = self.configIniDict['HW_BL_OFF4F']['hwTrunkOperstatus.0.159'.lower()]
        oid_hwStackPortStatus10 = self.configIniDict['HW_BL_OFF4F']['hwStackPortStatus.1.0'.lower()]
        oid_hwStackPortStatus20 = self.configIniDict['HW_BL_OFF4F']['hwStackPortStatus.2.0'.lower()]
        oid_hwStackPortStatus21 = self.configIniDict['HW_BL_OFF4F']['hwStackPortStatus.2.1'.lower()]
        oid_hwStackPortStatus31 = self.configIniDict['HW_BL_OFF4F']['hwStackPortStatus.3.1'.lower()]

        #MPU 1温度
        hwEntityTemperature1 = self.getSnmpValue(address, oid_hwEntityTemperature1)
        hwEntityTemperature2 = self.getSnmpValue(address, oid_hwEntityTemperature2)
        hwEntityTemperature3 = self.getSnmpValue(address, oid_hwEntityTemperature3)
        #MPU 2温度
        #GE1/0/49 & 2/0/49 SPF模块功率
        hwEntityOpticalTxPower1 = self.getSnmpValue(address, oid_hwEntityOpticalTxPower1)
        hwEntityOpticalTxPower2 = self.getSnmpValue(address, oid_hwEntityOpticalTxPower2)

        #MPU 1风扇状态
        hwEntityFanState1 = self.translateNum2Str(address, oid_hwEntityFanState1)
        #MPU 2风扇状态
        hwEntityFanState2 = self.translateNum2Str(address, oid_hwEntityFanState2)
        #MPU 3风扇状态
        hwEntityFanState3 = self.translateNum2Str(address, oid_hwEntityFanState3)

        #Eth-Trunk(GE1/0/49)端口状态
        hwTrunkOperstatus55 = self.translateNum2Str(address, oid_hwTrunkOperstatus55)
        #Eth-Trunk(GE3/0/49)端口状态
        hwTrunkOperstatus159 = self.translateNum2Str(address, oid_hwTrunkOperstatus159)

        #Stack(GE1/0/51)端口状态
        hwStackPortStatus10 = self.translateNum2Str(address, oid_hwStackPortStatus10)
        #Stack(GE2/0/52)端口状态
        hwStackPortStatus20 = self.translateNum2Str(address, oid_hwStackPortStatus20)
        #Stack(GE2/0/51)端口状态
        hwStackPortStatus21 = self.translateNum2Str(address, oid_hwStackPortStatus21)
        #Stack(GE3/0/52)端口状态
        hwStackPortStatus31 = self.translateNum2Str(address, oid_hwStackPortStatus31)

        print '\nHW_BL_OFF2F-3 Result:'
        print 'MPU1温度:'+hwEntityTemperature1+\
              '\nMPU2温度:'+hwEntityTemperature2+\
              '\nMPU3温度:'+hwEntityTemperature3+\
              '\n风扇1状态:'+hwEntityFanState1+\
              '\n风扇2状态:'+hwEntityFanState2+\
              '\n风扇3状态:'+hwEntityFanState3+\
              '\nSPF(GE1/0/49)功率(mW):'+hwEntityOpticalTxPower1+\
              '\nSPF(GE2/0/49)功率(mW):'+hwEntityOpticalTxPower2+\
              '\nEth-Trunk成员(GE1/0/49)状态:'+hwTrunkOperstatus55+\
              '\nEth-Trunk成员(GE3/0/49)状态:'+hwTrunkOperstatus159+\
              '\nStack成员(GE1/0/51)状态:'+hwStackPortStatus10+\
              '\nStack成员(GE2/0/52)状态:'+hwStackPortStatus20+\
              '\nStack成员(GE2/0/51)状态:'+hwStackPortStatus21+\
              '\nStack成员(GE3/0/52)状态:'+hwStackPortStatus31

    def getHW_BL_PUB1F(self):
        address = self.configIniDict['HW_BL_PUB1F']['ip'.lower()]
        oid_hwEntityFanState1 = self.configIniDict['HW_BL_PUB1F']['hwEntityFanState.0.0'.lower()]
        oid_hwEntityTemperature1 = self.configIniDict['HW_BL_PUB1F']['hwEntityTemperature.67108873'.lower()]
        oid_hwEntityOpticalTxPower1 = self.configIniDict['HW_BL_PUB1F']['hwEntityOpticalTxPower.67308622'.lower()]
        oid_hwEntityOpticalTxPower2 = self.configIniDict['HW_BL_PUB1F']['hwEntityOpticalTxPower.67308686'.lower()]
        oid_hwTrunkOperstatus160 = self.configIniDict['HW_BL_PUB1F']['hwTrunkOperstatus.0.160'.lower()]
        oid_hwTrunkOperstatus161 = self.configIniDict['HW_BL_PUB1F']['hwTrunkOperstatus.0.161'.lower()]

        #MPU 1温度
        hwEntityTemperature1 = self.getSnmpValue(address, oid_hwEntityTemperature1)
        #MPU 2温度
        #GE0/0/49 & 0/0/50 SPF模块功率
        hwEntityOpticalTxPower1 = self.getSnmpValue(address, oid_hwEntityOpticalTxPower1)
        hwEntityOpticalTxPower2 = self.getSnmpValue(address, oid_hwEntityOpticalTxPower2)

        #MPU 1风扇状态
        hwEntityFanState1 = self.translateNum2Str(address, oid_hwEntityFanState1)

        #Eth-Trunk(GE1/0/49)端口状态
        hwTrunkOperstatus160 = self.translateNum2Str(address, oid_hwTrunkOperstatus160)
        #Eth-Trunk(GE2/0/49)端口状态
        hwTrunkOperstatus161 = self.translateNum2Str(address, oid_hwTrunkOperstatus161)

        print '\nHW_BL_PUB1F Result:'
        print 'MPU1温度:'+hwEntityTemperature1+\
              '\n风扇1状态:'+hwEntityFanState1+\
              '\nSPF(GE1/0/49)功率(mW):'+hwEntityOpticalTxPower1+\
              '\nSPF(GE2/0/49)功率(mW):'+hwEntityOpticalTxPower2+\
              '\nEth-Trunk成员(GE0/0/49)状态:'+hwTrunkOperstatus160+\
              '\nEth-Trunk成员(GE0/0/50)状态:'+hwTrunkOperstatus161

    def getHW_BL_PUB3F(self):
        address = self.configIniDict['HW_BL_PUB3F']['ip'.lower()]
        oid_hwEntityFanState1 = self.configIniDict['HW_BL_PUB3F']['hwEntityFanState.1.0'.lower()]
        oid_hwEntityFanState2 = self.configIniDict['HW_BL_PUB3F']['hwEntityFanState.2.0'.lower()]
        oid_hwEntityTemperature1 = self.configIniDict['HW_BL_PUB3F']['hwEntityTemperature.67371017'.lower()]
        oid_hwEntityTemperature2 = self.configIniDict['HW_BL_PUB3F']['hwEntityTemperature.67633161'.lower()]
        oid_hwEntityOpticalTxPower1 = self.configIniDict['HW_BL_PUB3F']['hwEntityOpticalTxPower.67570766'.lower()]
        oid_hwEntityOpticalTxPower2 = self.configIniDict['HW_BL_PUB3F']['hwEntityOpticalTxPower.67832910'.lower()]
        oid_hwTrunkOperstatus55 = self.configIniDict['HW_BL_PUB3F']['hwTrunkOperstatus.0.55'.lower()]
        oid_hwTrunkOperstatus107 = self.configIniDict['HW_BL_PUB3F']['hwTrunkOperstatus.0.107'.lower()]
        oid_hwStackPortStatus10 = self.configIniDict['HW_BL_PUB3F']['hwStackPortStatus.1.0'.lower()]
        oid_hwStackPortStatus11 = self.configIniDict['HW_BL_PUB3F']['hwStackPortStatus.1.1'.lower()]
        oid_hwStackPortStatus20 = self.configIniDict['HW_BL_PUB3F']['hwStackPortStatus.2.0'.lower()]
        oid_hwStackPortStatus21 = self.configIniDict['HW_BL_PUB3F']['hwStackPortStatus.2.1'.lower()]

        #MPU 1温度
        hwEntityTemperature1 = self.getSnmpValue(address, oid_hwEntityTemperature1)
        hwEntityTemperature2 = self.getSnmpValue(address, oid_hwEntityTemperature2)
        #MPU 2温度
        #GE1/0/49 & 2/0/49 SPF模块功率
        hwEntityOpticalTxPower1 = self.getSnmpValue(address, oid_hwEntityOpticalTxPower1)
        hwEntityOpticalTxPower2 = self.getSnmpValue(address, oid_hwEntityOpticalTxPower2)

        #MPU 1风扇状态
        hwEntityFanState1 = self.translateNum2Str(address, oid_hwEntityFanState1)
        #MPU 2风扇状态
        hwEntityFanState2 = self.translateNum2Str(address, oid_hwEntityFanState2)

        #Eth-Trunk(GE1/0/49)端口状态
        hwTrunkOperstatus55 = self.translateNum2Str(address, oid_hwTrunkOperstatus55)
        #Eth-Trunk(GE2/0/49)端口状态
        hwTrunkOperstatus107 = self.translateNum2Str(address, oid_hwTrunkOperstatus107)

        #Stack(GE1/0/51)端口状态
        hwStackPortStatus10 = self.translateNum2Str(address, oid_hwStackPortStatus10)
        #Stack(GE2/0/52)端口状态
        hwStackPortStatus11 = self.translateNum2Str(address, oid_hwStackPortStatus11)
        #Stack(GE1/0/52)端口状态
        hwStackPortStatus20 = self.translateNum2Str(address, oid_hwStackPortStatus20)
        #Stack(GE2/0/51)端口状态
        hwStackPortStatus21 = self.translateNum2Str(address, oid_hwStackPortStatus21)

        print '\nHW_BL_PUB3F Result:'
        print 'MPU1温度:'+hwEntityTemperature1+\
              '\nMPU2温度:'+hwEntityTemperature2+\
              '\n风扇1状态:'+hwEntityFanState1+\
              '\n风扇2状态:'+hwEntityFanState2+\
              '\nSPF(GE1/0/49)功率(mW):'+hwEntityOpticalTxPower1+\
              '\nSPF(GE2/0/49)功率(mW):'+hwEntityOpticalTxPower2+\
              '\nEth-Trunk成员(GE1/0/49)状态:'+hwTrunkOperstatus55+\
              '\nEth-Trunk成员(GE2/0/49)状态:'+hwTrunkOperstatus107+\
              '\nStack成员(GE1/0/51)状态:'+hwStackPortStatus10+\
              '\nStack成员(GE2/0/52)状态:'+hwStackPortStatus11+\
              '\nStack成员(GE1/0/52)状态:'+hwStackPortStatus20+\
              '\nStack成员(GE2/0/51)状态:'+hwStackPortStatus21

    def getHW_BL_SUBFAB_1(self):
        address = self.configIniDict['HW_BL_SUBFAB-1']['ip'.lower()]
        oid_hwEntityFanState1 = self.configIniDict['HW_BL_SUBFAB-1']['hwEntityFanState.1.0'.lower()]
        oid_hwEntityFanState2 = self.configIniDict['HW_BL_SUBFAB-1']['hwEntityFanState.2.0'.lower()]
        oid_hwEntityTemperature1 = self.configIniDict['HW_BL_SUBFAB-1']['hwEntityTemperature.67371017'.lower()]
        oid_hwEntityTemperature2 = self.configIniDict['HW_BL_SUBFAB-1']['hwEntityTemperature.67633161'.lower()]
        oid_hwEntityOpticalTxPower1 = self.configIniDict['HW_BL_SUBFAB-1']['hwEntityOpticalTxPower.67570766'.lower()]
        oid_hwEntityOpticalTxPower2 = self.configIniDict['HW_BL_SUBFAB-1']['hwEntityOpticalTxPower.67832910'.lower()]
        oid_hwTrunkOperstatus55 = self.configIniDict['HW_BL_SUBFAB-1']['hwTrunkOperstatus.0.55'.lower()]
        oid_hwTrunkOperstatus107 = self.configIniDict['HW_BL_SUBFAB-1']['hwTrunkOperstatus.0.107'.lower()]
        oid_hwStackPortStatus10 = self.configIniDict['HW_BL_SUBFAB-1']['hwStackPortStatus.1.0'.lower()]
        oid_hwStackPortStatus11 = self.configIniDict['HW_BL_SUBFAB-1']['hwStackPortStatus.1.1'.lower()]
        oid_hwStackPortStatus20 = self.configIniDict['HW_BL_SUBFAB-1']['hwStackPortStatus.2.0'.lower()]
        oid_hwStackPortStatus21 = self.configIniDict['HW_BL_SUBFAB-1']['hwStackPortStatus.2.1'.lower()]

        #MPU 1温度
        hwEntityTemperature1 = self.getSnmpValue(address, oid_hwEntityTemperature1)
        hwEntityTemperature2 = self.getSnmpValue(address, oid_hwEntityTemperature2)
        #MPU 2温度
        #GE1/0/49 & 2/0/49 SPF模块功率
        hwEntityOpticalTxPower1 = self.getSnmpValue(address, oid_hwEntityOpticalTxPower1)
        hwEntityOpticalTxPower2 = self.getSnmpValue(address, oid_hwEntityOpticalTxPower2)

        #MPU 1风扇状态
        hwEntityFanState1 = self.translateNum2Str(address, oid_hwEntityFanState1)
        #MPU 2风扇状态
        hwEntityFanState2 = self.translateNum2Str(address, oid_hwEntityFanState2)

        #Eth-Trunk(GE1/0/49)端口状态
        hwTrunkOperstatus55 = self.translateNum2Str(address, oid_hwTrunkOperstatus55)
        #Eth-Trunk(GE2/0/49)端口状态
        hwTrunkOperstatus107 = self.translateNum2Str(address, oid_hwTrunkOperstatus107)

        #Stack(GE1/0/51)端口状态
        hwStackPortStatus10 = self.translateNum2Str(address, oid_hwStackPortStatus10)
        #Stack(GE2/0/52)端口状态
        hwStackPortStatus11 = self.translateNum2Str(address, oid_hwStackPortStatus11)
        #Stack(GE1/0/52)端口状态
        hwStackPortStatus20 = self.translateNum2Str(address, oid_hwStackPortStatus20)
        #Stack(GE2/0/51)端口状态
        hwStackPortStatus21 = self.translateNum2Str(address, oid_hwStackPortStatus21)

        print '\nHW_BL_SUBFAB-1 Result:'
        print 'MPU1温度:'+hwEntityTemperature1+\
              '\nMPU2温度:'+hwEntityTemperature2+\
              '\n风扇1状态:'+hwEntityFanState1+\
              '\n风扇2状态:'+hwEntityFanState2+\
              '\nSPF(GE1/0/49)功率(mW):'+hwEntityOpticalTxPower1+\
              '\nSPF(GE2/0/49)功率(mW):'+hwEntityOpticalTxPower2+\
              '\nEth-Trunk成员(GE1/0/49)状态:'+hwTrunkOperstatus55+\
              '\nEth-Trunk成员(GE2/0/49)状态:'+hwTrunkOperstatus107+\
              '\nStack成员(GE1/0/51)状态:'+hwStackPortStatus10+\
              '\nStack成员(GE2/0/52)状态:'+hwStackPortStatus11+\
              '\nStack成员(GE1/0/52)状态:'+hwStackPortStatus20+\
              '\nStack成员(GE2/0/51)状态:'+hwStackPortStatus21

    def getHW_BL_SUBFAB_2(self):
        address = self.configIniDict['HW_BL_SUBFAB-2']['ip'.lower()]
        oid_hwEntityFanState1 = self.configIniDict['HW_BL_SUBFAB-2']['hwEntityFanState.1.0'.lower()]
        oid_hwEntityFanState2 = self.configIniDict['HW_BL_SUBFAB-2']['hwEntityFanState.2.0'.lower()]
        oid_hwEntityTemperature1 = self.configIniDict['HW_BL_SUBFAB-2']['hwEntityTemperature.67371017'.lower()]
        oid_hwEntityTemperature2 = self.configIniDict['HW_BL_SUBFAB-2']['hwEntityTemperature.67633161'.lower()]
        oid_hwEntityOpticalTxPower1 = self.configIniDict['HW_BL_SUBFAB-2']['hwEntityOpticalTxPower.67570766'.lower()]
        oid_hwEntityOpticalTxPower2 = self.configIniDict['HW_BL_SUBFAB-2']['hwEntityOpticalTxPower.67832910'.lower()]
        oid_hwTrunkOperstatus55 = self.configIniDict['HW_BL_SUBFAB-2']['hwTrunkOperstatus.0.55'.lower()]
        oid_hwTrunkOperstatus107 = self.configIniDict['HW_BL_SUBFAB-2']['hwTrunkOperstatus.0.107'.lower()]
        oid_hwStackPortStatus10 = self.configIniDict['HW_BL_SUBFAB-2']['hwStackPortStatus.1.0'.lower()]
        oid_hwStackPortStatus11 = self.configIniDict['HW_BL_SUBFAB-2']['hwStackPortStatus.1.1'.lower()]
        oid_hwStackPortStatus20 = self.configIniDict['HW_BL_SUBFAB-2']['hwStackPortStatus.2.0'.lower()]
        oid_hwStackPortStatus21 = self.configIniDict['HW_BL_SUBFAB-2']['hwStackPortStatus.2.1'.lower()]

        #MPU 1温度
        hwEntityTemperature1 = self.getSnmpValue(address, oid_hwEntityTemperature1)
        hwEntityTemperature2 = self.getSnmpValue(address, oid_hwEntityTemperature2)
        #MPU 2温度
        #GE1/0/49 & 2/0/49 SPF模块功率
        hwEntityOpticalTxPower1 = self.getSnmpValue(address, oid_hwEntityOpticalTxPower1)
        hwEntityOpticalTxPower2 = self.getSnmpValue(address, oid_hwEntityOpticalTxPower2)

        #MPU 1风扇状态
        hwEntityFanState1 = self.translateNum2Str(address, oid_hwEntityFanState1)
        #MPU 2风扇状态
        hwEntityFanState2 = self.translateNum2Str(address, oid_hwEntityFanState2)

        #Eth-Trunk(GE1/0/49)端口状态
        hwTrunkOperstatus55 = self.translateNum2Str(address, oid_hwTrunkOperstatus55)
        #Eth-Trunk(GE2/0/49)端口状态
        hwTrunkOperstatus107 = self.translateNum2Str(address, oid_hwTrunkOperstatus107)

        #Stack(GE1/0/51)端口状态
        hwStackPortStatus10 = self.translateNum2Str(address, oid_hwStackPortStatus10)
        #Stack(GE2/0/52)端口状态
        hwStackPortStatus11 = self.translateNum2Str(address, oid_hwStackPortStatus11)
        #Stack(GE1/0/52)端口状态
        hwStackPortStatus20 = self.translateNum2Str(address, oid_hwStackPortStatus20)
        #Stack(GE2/0/51)端口状态
        hwStackPortStatus21 = self.translateNum2Str(address, oid_hwStackPortStatus21)


        print '\nHW_BL_SUBFAB-2 Result:'
        print 'MPU1温度:'+hwEntityTemperature1+\
              '\nMPU2温度:'+hwEntityTemperature2+\
              '\n风扇1状态:'+hwEntityFanState1+\
              '\n风扇2状态:'+hwEntityFanState2+\
              '\nSPF(GE1/0/49)功率(mW):'+hwEntityOpticalTxPower1+\
              '\nSPF(GE2/0/49)功率(mW):'+hwEntityOpticalTxPower2+\
              '\nEth-Trunk成员(GE1/0/49)状态:'+hwTrunkOperstatus55+\
              '\nEth-Trunk成员(GE2/0/49)状态:'+hwTrunkOperstatus107+\
              '\nStack成员(GE1/0/51)状态:'+hwStackPortStatus10+\
              '\nStack成员(GE2/0/52)状态:'+hwStackPortStatus11+\
              '\nStack成员(GE1/0/52)状态:'+hwStackPortStatus20+\
              '\nStack成员(GE2/0/51)状态:'+hwStackPortStatus21

    def getHW_BL_AGG(self):
        address = self.configIniDict['HW_BL_AGG']['ip'.lower()]
        oid_hwEntityFanState10 = self.configIniDict['HW_BL_AGG']['hwEntityFanState.1.0'.lower()]
        oid_hwEntityFanState11 = self.configIniDict['HW_BL_AGG']['hwEntityFanState.1.1'.lower()]
        oid_hwEntityFanState12 = self.configIniDict['HW_BL_AGG']['hwEntityFanState.1.2'.lower()]
        oid_hwEntityFanState13 = self.configIniDict['HW_BL_AGG']['hwEntityFanState.1.3'.lower()]
        oid_hwEntityFanState14 = self.configIniDict['HW_BL_AGG']['hwEntityFanState.1.4'.lower()]
        oid_hwEntityFanState20 = self.configIniDict['HW_BL_AGG']['hwEntityFanState.2.0'.lower()]
        oid_hwEntityFanState21 = self.configIniDict['HW_BL_AGG']['hwEntityFanState.2.1'.lower()]
        oid_hwEntityFanState22 = self.configIniDict['HW_BL_AGG']['hwEntityFanState.2.2'.lower()]
        oid_hwEntityFanState23 = self.configIniDict['HW_BL_AGG']['hwEntityFanState.2.3'.lower()]
        oid_hwEntityFanState24 = self.configIniDict['HW_BL_AGG']['hwEntityFanState.2.4'.lower()]
        oid_hwEntityTemperature1 = self.configIniDict['HW_BL_AGG']['hwEntityTemperature.68157449'.lower()]
        oid_hwEntityTemperature2 = self.configIniDict['HW_BL_AGG']['hwEntityTemperature.69206025'.lower()]
        oid_hwStackPortStatus10 = self.configIniDict['HW_BL_AGG']['hwStackPortStatus.1.0'.lower()]
        oid_hwStackPortStatus11 = self.configIniDict['HW_BL_AGG']['hwStackPortStatus.1.1'.lower()]
        oid_hwStackPortStatus20 = self.configIniDict['HW_BL_AGG']['hwStackPortStatus.2.0'.lower()]
        oid_hwStackPortStatus21 = self.configIniDict['HW_BL_AGG']['hwStackPortStatus.2.1'.lower()]


        #MPU 1温度
        hwEntityTemperature1 = self.getSnmpValue(address, oid_hwEntityTemperature1)
        #MPU 2温度
        hwEntityTemperature2 = self.getSnmpValue(address, oid_hwEntityTemperature2)

        #MPU 10风扇状态
        hwEntityFanState10 = self.getSnmpValue(address, oid_hwEntityFanState10)
        #MPU 11风扇状态
        hwEntityFanState11 = self.getSnmpValue(address, oid_hwEntityFanState11)
        #MPU 12风扇状态
        hwEntityFanState12 = self.getSnmpValue(address, oid_hwEntityFanState12)
        #MPU 13风扇状态
        hwEntityFanState13 = self.getSnmpValue(address, oid_hwEntityFanState13)
        #MPU 14风扇状态
        hwEntityFanState14 = self.getSnmpValue(address, oid_hwEntityFanState14)

        #MPU 20风扇状态
        hwEntityFanState20 = self.getSnmpValue(address, oid_hwEntityFanState20)
        #MPU 21风扇状态
        hwEntityFanState21 = self.getSnmpValue(address, oid_hwEntityFanState21)
        #MPU 22风扇状态
        hwEntityFanState22 = self.getSnmpValue(address, oid_hwEntityFanState22)
        #MPU 23风扇状态
        hwEntityFanState23 = self.getSnmpValue(address, oid_hwEntityFanState23)
        #MPU 24风扇状态
        hwEntityFanState24 = self.getSnmpValue(address, oid_hwEntityFanState24)

        #Stack(XGE1/0/3)端口状态
        hwStackPortStatus10 = self.getSnmpValue(address, oid_hwStackPortStatus10)
        #Stack(XGE2/0/4)端口状态
        hwStackPortStatus11 = self.getSnmpValue(address, oid_hwStackPortStatus11)
        #Stack(XGE1/0/4)端口状态
        hwStackPortStatus20 = self.getSnmpValue(address, oid_hwStackPortStatus20)
        #Stack(XGE2/0/3)端口状态
        hwStackPortStatus21 = self.getSnmpValue(address, oid_hwStackPortStatus21)


        print '\nHW_BL_AGG Result:'
        print 'MPU1温度:'+hwEntityTemperature1+\
              '\nMPU2温度:'+hwEntityTemperature2+\
              '\n风扇10状态:'+hwEntityFanState10+\
              '\n风扇11状态:'+hwEntityFanState11+\
              '\n风扇12状态:'+hwEntityFanState12+\
              '\n风扇13状态:'+hwEntityFanState13+\
              '\n风扇14状态:'+hwEntityFanState14+\
              '\n风扇20状态:'+hwEntityFanState20+\
              '\n风扇21状态:'+hwEntityFanState21+\
              '\n风扇22状态:'+hwEntityFanState22+\
              '\n风扇23状态:'+hwEntityFanState23+\
              '\n风扇24状态:'+hwEntityFanState24+\
              '\nStack成员(XGE1/0/3)状态:'+hwStackPortStatus10+\
              '\nStack成员(XGE2/0/4)状态:'+hwStackPortStatus11+\
              '\nStack成员(XGE1/0/4)状态:'+hwStackPortStatus20+\
              '\nStack成员(XGE2/0/3)状态:'+hwStackPortStatus21

    def getHW_BL_CORE(self):
        address = self.configIniDict['HW_BL_CORE']['ip'.lower()]
        oid_hwEntityFanState300 = self.configIniDict['HW_BL_CORE']['hwEntityFanState.30.0'.lower()]
        oid_hwEntityFanState301 = self.configIniDict['HW_BL_CORE']['hwEntityFanState.30.1'.lower()]
        oid_hwEntityFanState311 = self.configIniDict['HW_BL_CORE']['hwEntityFanState.31.1'.lower()]
        oid_hwEntityFanState312 = self.configIniDict['HW_BL_CORE']['hwEntityFanState.31.2'.lower()]
        oid_hwEntityFanState321 = self.configIniDict['HW_BL_CORE']['hwEntityFanState.32.1'.lower()]
        oid_hwEntityFanState322 = self.configIniDict['HW_BL_CORE']['hwEntityFanState.32.2'.lower()]
        oid_hwEntityFanState331 = self.configIniDict['HW_BL_CORE']['hwEntityFanState.33.1'.lower()]
        oid_hwEntityFanState332 = self.configIniDict['HW_BL_CORE']['hwEntityFanState.33.2'.lower()]
        oid_hwEntityTemperature11 = self.configIniDict['HW_BL_CORE']['hwEntityTemperature.68943881'.lower()]
        oid_hwEntityTemperature12 = self.configIniDict['HW_BL_CORE']['hwEntityTemperature.69206025'.lower()]
        oid_hwEntityTemperature21 = self.configIniDict['HW_BL_CORE']['hwEntityTemperature.136052745'.lower()]
        oid_hwEntityTemperature22 = self.configIniDict['HW_BL_CORE']['hwEntityTemperature.136314889'.lower()]

        oid_hwTrunkOperstatus240 = self.configIniDict['HW_BL_CORE']['hwTrunkOperstatus.5.240'.lower()]
        oid_hwTrunkOperstatus423 = self.configIniDict['HW_BL_CORE']['hwTrunkOperstatus.5.423'.lower()]
        oid_hwTrunkOperstatus10 = self.configIniDict['HW_BL_CORE']['hwTrunkOperstatus.6.10'.lower()]
        oid_hwTrunkOperstatus298 = self.configIniDict['HW_BL_CORE']['hwTrunkOperstatus.6.298'.lower()]

        oid_ifOperStatus241 = self.configIniDict['HW_BL_CORE']['ifOperStatus.241'.lower()]
        oid_ifOperStatus424 = self.configIniDict['HW_BL_CORE']['ifOperStatus.424'.lower()]

        oid_ifOperStatus242 = self.configIniDict['HW_BL_CORE']['ifOperStatus.242'.lower()]
        oid_ifOperStatus243 = self.configIniDict['HW_BL_CORE']['ifOperStatus.243'.lower()]
        oid_ifOperStatus244 = self.configIniDict['HW_BL_CORE']['ifOperStatus.244'.lower()]
        oid_ifOperStatus245 = self.configIniDict['HW_BL_CORE']['ifOperStatus.245'.lower()]
        oid_ifOperStatus425 = self.configIniDict['HW_BL_CORE']['ifOperStatus.425'.lower()]
        oid_ifOperStatus426 = self.configIniDict['HW_BL_CORE']['ifOperStatus.426'.lower()]
        oid_ifOperStatus427 = self.configIniDict['HW_BL_CORE']['ifOperStatus.427'.lower()]
        oid_ifOperStatus428 = self.configIniDict['HW_BL_CORE']['ifOperStatus.428'.lower()]

        #MPU 11温度
        hwEntityTemperature11 = self.getSnmpValue(address, oid_hwEntityTemperature11)
        #MPU 12温度
        hwEntityTemperature12 = self.getSnmpValue(address, oid_hwEntityTemperature12)
        #MPU 21温度
        hwEntityTemperature21 = self.getSnmpValue(address, oid_hwEntityTemperature21)
        #MPU 22温度
        hwEntityTemperature22 = self.getSnmpValue(address, oid_hwEntityTemperature22)

        #MPU 00风扇状态
        hwEntityFanState300 = self.translateNum2Str(address, oid_hwEntityFanState300)
        #MPU 01风扇状态
        hwEntityFanState301 = self.translateNum2Str(address, oid_hwEntityFanState301)
        #MPU 11风扇状态
        hwEntityFanState311 = self.translateNum2Str(address, oid_hwEntityFanState311)
        #MPU 12风扇状态
        hwEntityFanState312 = self.translateNum2Str(address, oid_hwEntityFanState312)
        #MPU 21风扇状态
        hwEntityFanState321 = self.translateNum2Str(address, oid_hwEntityFanState321)
        #MPU 22风扇状态
        hwEntityFanState322 = self.translateNum2Str(address, oid_hwEntityFanState322)
        #MPU 31风扇状态
        hwEntityFanState331 = self.translateNum2Str(address, oid_hwEntityFanState331)
        #MPU 32风扇状态
        hwEntityFanState332 = self.translateNum2Str(address, oid_hwEntityFanState332)

        #Eth-Trunk(GE 1/6/0/6)端口状态
        hwTrunkOperstatus240 = self.translateNum2Str(address, oid_hwTrunkOperstatus240)
        #Eth-Trunk(GE 2/6/0/6)端口状态
        hwTrunkOperstatus423 = self.translateNum2Str(address, oid_hwTrunkOperstatus423)
        #Eth-Trunk(GE 1/6/0/7)端口状态
        hwTrunkOperstatus10 = self.translateNum2Str(address, oid_hwTrunkOperstatus10)
        #Eth-Trunk(GE 2/6/0/7)端口状态
        hwTrunkOperstatus298 = self.translateNum2Str(address, oid_hwTrunkOperstatus298)

        #Eth-Trunk(XGE 1/6/0/7)端口状态 For刀片交换机
        ifOperStatus241 = self.translateNum2Str(address, oid_ifOperStatus241)
        #Eth-Trunk(XGE 2/6/0/7)端口状态
        ifOperStatus424 = self.translateNum2Str(address, oid_ifOperStatus424)
        #Eth-Trunk(XGE 1/6/0/8)端口状态 For刀框
        ifOperStatus242 = self.translateNum2Str(address, oid_ifOperStatus242)
        #Eth-Trunk(XGE 2/6/0/8)端口状态
        ifOperStatus243 = self.translateNum2Str(address, oid_ifOperStatus243)
        #Eth-Trunk(XGE 1/6/0/9)端口状态
        ifOperStatus244 = self.translateNum2Str(address, oid_ifOperStatus244)
        #Eth-Trunk(XGE 2/6/0/9)端口状态
        ifOperStatus245 = self.translateNum2Str(address, oid_ifOperStatus245)
        #Eth-Trunk(XGE 1/6/0/10)端口状态 For刀框
        ifOperStatus425 = self.translateNum2Str(address, oid_ifOperStatus425)
        #Eth-Trunk(XGE 2/6/0/11)端口状态
        ifOperStatus426 = self.translateNum2Str(address, oid_ifOperStatus426)
        #Eth-Trunk(XGE 1/6/0/12)端口状态
        ifOperStatus427 = self.translateNum2Str(address, oid_ifOperStatus427)
        #Eth-Trunk(XGE 2/6/0/13)端口状态
        ifOperStatus428 = self.translateNum2Str(address, oid_ifOperStatus428)

        print '\nHW_BL_CORE Result:'
        print 'MPU1温度:'+hwEntityTemperature11+\
              '\nMPU2温度:'+hwEntityTemperature12+\
              'MPU1温度:'+hwEntityTemperature21+\
              '\nMPU2温度:'+hwEntityTemperature22+\
              '\n风扇00状态:'+hwEntityFanState300+\
              '\n风扇01状态:'+hwEntityFanState301+\
              '\n风扇11状态:'+hwEntityFanState311+\
              '\n风扇12状态:'+hwEntityFanState312+\
              '\n风扇21状态:'+hwEntityFanState321+\
              '\n风扇22状态:'+hwEntityFanState322+\
              '\n风扇31状态:'+hwEntityFanState331+\
              '\n风扇32状态:'+hwEntityFanState332+\
              '\nEth-Trunk成员(GE1/6/0/6)状态:'+hwTrunkOperstatus240+\
              '\nEth-Trunk成员(GE2/6/0/6)状态:'+hwTrunkOperstatus423+\
              '\nEth-Trunk成员(GE1/6/0/7)状态:'+hwTrunkOperstatus10+\
              '\nEth-Trunk成员(GE2/6/0/7)状态:'+hwTrunkOperstatus298+\
              '\n刀框互连端口(XGE1/6/0/7)状态:'+ifOperStatus241+\
              '\n刀框互连端口(XGE2/6/0/7)状态:'+ifOperStatus424+\
              '\nCSS端口(XGE1/6/0/8)状态:'+ifOperStatus242+\
              '\nCSS端口(XGE2/6/0/8)状态:'+ifOperStatus243+\
              '\nCSS端口(XGE1/6/0/9)状态:'+ifOperStatus244+\
              '\nCSS端口(XGE2/6/0/9)状态:'+ifOperStatus245+\
              '\nCSS端口(XGE1/6/0/10)状态:'+ifOperStatus425+\
              '\nCSS端口(XGE2/6/0/10)状态:'+ifOperStatus426+\
              '\nCSS端口(XGE1/6/0/11)状态:'+ifOperStatus427+\
              '\nCSS端口(XGE2/6/0/11)状态:'+ifOperStatus428

    def getHW_FH_AGG(self):
        address = self.configIniDict['HW_FH_AGG']['ip'.lower()]
        oid_hwEntityFanState10 = self.configIniDict['HW_FH_AGG']['hwEntityFanState.1.0'.lower()]
        oid_hwEntityFanState11 = self.configIniDict['HW_FH_AGG']['hwEntityFanState.1.1'.lower()]
        oid_hwEntityFanState12 = self.configIniDict['HW_FH_AGG']['hwEntityFanState.1.2'.lower()]
        oid_hwEntityFanState13 = self.configIniDict['HW_FH_AGG']['hwEntityFanState.1.3'.lower()]
        oid_hwEntityFanState14 = self.configIniDict['HW_FH_AGG']['hwEntityFanState.1.4'.lower()]
        oid_hwEntityFanState20 = self.configIniDict['HW_FH_AGG']['hwEntityFanState.2.0'.lower()]
        oid_hwEntityFanState21 = self.configIniDict['HW_FH_AGG']['hwEntityFanState.2.1'.lower()]
        oid_hwEntityFanState22 = self.configIniDict['HW_FH_AGG']['hwEntityFanState.2.2'.lower()]
        oid_hwEntityFanState23 = self.configIniDict['HW_FH_AGG']['hwEntityFanState.2.3'.lower()]
        oid_hwEntityFanState24 = self.configIniDict['HW_FH_AGG']['hwEntityFanState.2.4'.lower()]
        oid_hwEntityTemperature1 = self.configIniDict['HW_FH_AGG']['hwEntityTemperature.68157449'.lower()]
        oid_hwEntityTemperature2 = self.configIniDict['HW_FH_AGG']['hwEntityTemperature.69206025'.lower()]
        oid_hwStackPortStatus10 = self.configIniDict['HW_FH_AGG']['hwStackPortStatus.1.0'.lower()]
        oid_hwStackPortStatus11 = self.configIniDict['HW_FH_AGG']['hwStackPortStatus.1.1'.lower()]
        oid_hwStackPortStatus20 = self.configIniDict['HW_FH_AGG']['hwStackPortStatus.2.0'.lower()]
        oid_hwStackPortStatus21 = self.configIniDict['HW_FH_AGG']['hwStackPortStatus.2.1'.lower()]


        #MPU 1温度
        hwEntityTemperature1 = self.getSnmpValue(address, oid_hwEntityTemperature1)
        #MPU 2温度
        hwEntityTemperature2 = self.getSnmpValue(address, oid_hwEntityTemperature2)

        #MPU 10风扇状态
        hwEntityFanState10 =self.translateNum2Str(address,oid_hwEntityFanState10)
        #MPU 11风扇状态
        hwEntityFanState11 =self.translateNum2Str(address,oid_hwEntityFanState11)
        #MPU 12风扇状态
        hwEntityFanState12 =self.translateNum2Str(address,oid_hwEntityFanState12)
        #MPU 13风扇状态
        hwEntityFanState13 =self.translateNum2Str(address,oid_hwEntityFanState13)
        #MPU 14风扇状态
        hwEntityFanState14 =self.translateNum2Str(address,oid_hwEntityFanState14)
        #MPU 20风扇状态
        hwEntityFanState20 =self.translateNum2Str(address,oid_hwEntityFanState20)
        #MPU 21风扇状态
        hwEntityFanState21 =self.translateNum2Str(address,oid_hwEntityFanState21)
        #MPU 22风扇状态
        hwEntityFanState22 =self.translateNum2Str(address,oid_hwEntityFanState22)
        #MPU 23风扇状态
        hwEntityFanState23 =self.translateNum2Str(address,oid_hwEntityFanState23)
        #MPU 24风扇状态
        hwEntityFanState24 =self.translateNum2Str(address,oid_hwEntityFanState24)

        #Stack(XGE1/0/3)端口状态
        hwStackPortStatus10 =self.translateNum2Str(address,oid_hwStackPortStatus10)
        #Stack(XGE2/0/4)端口状态
        hwStackPortStatus11 =self.translateNum2Str(address,oid_hwStackPortStatus11)
        #Stack(XGE1/0/4)端口状态
        hwStackPortStatus20 =self.translateNum2Str(address,oid_hwStackPortStatus20)
        #Stack(XGE2/0/3)端口状态
        hwStackPortStatus21 =self.translateNum2Str(address,oid_hwStackPortStatus21)


        print '\nHW_FH_AGG Result:'
        print 'MPU1温度:'+hwEntityTemperature1+\
              '\nMPU2温度:'+hwEntityTemperature2+\
              '\n风扇10状态:'+hwEntityFanState10+\
              '\n风扇11状态:'+hwEntityFanState11+\
              '\n风扇12状态:'+hwEntityFanState12+\
              '\n风扇13状态:'+hwEntityFanState13+\
              '\n风扇14状态:'+hwEntityFanState14+\
              '\n风扇20状态:'+hwEntityFanState20+\
              '\n风扇21状态:'+hwEntityFanState21+\
              '\n风扇22状态:'+hwEntityFanState22+\
              '\n风扇23状态:'+hwEntityFanState23+\
              '\n风扇24状态:'+hwEntityFanState24+\
              '\nStack成员(XGE1/0/1)状态:'+hwStackPortStatus10+\
              '\nStack成员(XGE2/0/2)状态:'+hwStackPortStatus11+\
              '\nStack成员(XGE1/0/2)状态:'+hwStackPortStatus20+\
              '\nStack成员(XGE2/0/1)状态:'+hwStackPortStatus21

    def getHW_FH_AC1(self):
        address = self.configIniDict['HW_FH_AC-1']['ip'.lower()]
        oid_hwEntityTemperature = self.configIniDict['HW_FH_AC-1']['hwEntityTemperature.9'.lower()]
        oid_hwTrunkOperstatus3 = self.configIniDict['HW_FH_AC-1']['hwTrunkOperstatus.0.3'.lower()]
        oid_hwTrunkOperstatus4 = self.configIniDict['HW_FH_AC-1']['hwTrunkOperstatus.0.4'.lower()]
        oid_hwWlanCurJointApNum = self.configIniDict['HW_FH_AC-1']['hwWlanCurJointApNum'.lower()]
        oid_hwWlanCurAuthSuccessStaNum = self.configIniDict['HW_FH_AC-1']['hwWlanCurAuthSuccessStaNum'.lower()]
        oid_hwWlanRfComplianceRate = self.configIniDict['HW_FH_AC-1']['hwWlanRfComplianceRate'.lower()]
        oid_hwWlanApComplianceRate = self.configIniDict['HW_FH_AC-1']['hwWlanApComplianceRate'.lower()]
        oid_hwWlanStaComplianceRate = self.configIniDict['HW_FH_AC-1']['hwWlanStaComplianceRate'.lower()]
        oid_hwStaGlobalWirelessPacketDropRate = self.configIniDict['HW_FH_AC-1']['hwStaGlobalWirelessPacketDropRate'.lower()]

        hwEntityTemperature = self.getSnmpValue(address, oid_hwEntityTemperature) #CPU温度
        hwWlanCurJointApNum = self.getSnmpValue(address, oid_hwWlanCurJointApNum) #在线AP数量
        hwWlanCurAuthSuccessStaNum = self.getSnmpValue(address, oid_hwWlanCurAuthSuccessStaNum) #在线终端数
        hwWlanRfComplianceRate = self.getSnmpValue(address, oid_hwWlanRfComplianceRate) #射频总体达标率
        hwWlanApComplianceRate = self.getSnmpValue(address, oid_hwWlanApComplianceRate) #AP总体达标率
        hwWlanStaComplianceRate = self.getSnmpValue(address, oid_hwWlanStaComplianceRate) #终端总体达标率
        hwStaGlobalWirelessPacketDropRate = self.getSnmpValue(address, oid_hwStaGlobalWirelessPacketDropRate) #终端平均丢包率

        #Eth-Trunk端口状态 GE0/0/1
        hwTrunkOperstatus3 = self.translateNum2Str(address, oid_hwTrunkOperstatus3)
        #Eth-Trunk端口状态 GE0/0/2
        hwTrunkOperstatus4 = self.translateNum2Str(address, oid_hwTrunkOperstatus4)

        print '\nHW_FH_AC-1 Result:'
        print 'MPU温度:'+hwEntityTemperature+\
              '\nEth-Trunk成员(GE0/0/1)状态:'+hwTrunkOperstatus3+\
              '\nEth-Trunk成员(GE0/0/2)状态:'+hwTrunkOperstatus4+\
              '\n在线AP数量:'+hwWlanCurJointApNum+\
              '\n在线终端数:'+hwWlanCurAuthSuccessStaNum+\
              '\n射频总体达标率:'+hwWlanRfComplianceRate+\
              '\nAP总体达标率:'+hwWlanApComplianceRate+\
              '\n终端总体达标率:'+hwWlanStaComplianceRate+\
              '\n终端平均丢包率:'+hwStaGlobalWirelessPacketDropRate

    def getHW_FH_AC2(self):
        address = self.configIniDict['HW_FH_AC-2']['ip'.lower()]
        oid_hwEntityTemperature = self.configIniDict['HW_FH_AC-2']['hwEntityTemperature.9'.lower()]
        oid_hwTrunkOperstatus3 = self.configIniDict['HW_FH_AC-2']['hwTrunkOperstatus.0.3'.lower()]
        oid_hwTrunkOperstatus4 = self.configIniDict['HW_FH_AC-2']['hwTrunkOperstatus.0.4'.lower()]
        oid_hwWlanCurJointApNum = self.configIniDict['HW_FH_AC-1']['hwWlanCurJointApNum'.lower()]
        oid_hwWlanCurAuthSuccessStaNum = self.configIniDict['HW_FH_AC-1']['hwWlanCurAuthSuccessStaNum'.lower()]
        oid_hwWlanRfComplianceRate = self.configIniDict['HW_FH_AC-1']['hwWlanRfComplianceRate'.lower()]
        oid_hwWlanApComplianceRate = self.configIniDict['HW_FH_AC-1']['hwWlanApComplianceRate'.lower()]
        oid_hwWlanStaComplianceRate = self.configIniDict['HW_FH_AC-1']['hwWlanStaComplianceRate'.lower()]
        oid_hwStaGlobalWirelessPacketDropRate = self.configIniDict['HW_FH_AC-1']['hwStaGlobalWirelessPacketDropRate'.lower()]

        hwEntityTemperature = self.getSnmpValue(address, oid_hwEntityTemperature) #CPU温度
        hwWlanCurJointApNum = self.getSnmpValue(address, oid_hwWlanCurJointApNum) #在线AP数量
        hwWlanCurAuthSuccessStaNum = self.getSnmpValue(address, oid_hwWlanCurAuthSuccessStaNum) #在线终端数
        hwWlanRfComplianceRate = self.getSnmpValue(address, oid_hwWlanRfComplianceRate) #射频总体达标率
        hwWlanApComplianceRate = self.getSnmpValue(address, oid_hwWlanApComplianceRate) #AP总体达标率
        hwWlanStaComplianceRate = self.getSnmpValue(address, oid_hwWlanStaComplianceRate) #终端总体达标率
        hwStaGlobalWirelessPacketDropRate = self.getSnmpValue(address, oid_hwStaGlobalWirelessPacketDropRate) #终端平均丢包率

        #Eth-Trunk端口状态 GE0/0/1
        hwTrunkOperstatus3 = self.translateNum2Str(address, oid_hwTrunkOperstatus3)
        #Eth-Trunk端口状态 GE0/0/2
        hwTrunkOperstatus4 = self.translateNum2Str(address, oid_hwTrunkOperstatus4)

        print '\nHW_FH_AC-2 Result:'
        print 'MPU温度:'+hwEntityTemperature+\
              '\nEth-Trunk成员(GE0/0/1)状态:'+hwTrunkOperstatus3+\
              '\nEth-Trunk成员(GE0/0/2)状态:'+hwTrunkOperstatus4+\
              '\n在线AP数量:'+hwWlanCurJointApNum+\
              '\n在线终端数:'+hwWlanCurAuthSuccessStaNum+\
              '\n射频总体达标率:'+hwWlanRfComplianceRate+\
              '\nAP总体达标率:'+hwWlanApComplianceRate+\
              '\n终端总体达标率:'+hwWlanStaComplianceRate+\
              '\n终端平均丢包率:'+hwStaGlobalWirelessPacketDropRate

    def getHW_FH_Router(self):
        address = self.configIniDict['HW_FH_Router']['ip'.lower()]
        oid_hwEntityTemperature = self.configIniDict['HW_FH_Router']['hwEntityTemperature.9'.lower()]
        oid_hwEntityFanState1 = self.configIniDict['HW_FH_Router']['hwEntityFanState.0.1'.lower()]
        oid_hwEntityFanState2 = self.configIniDict['HW_FH_Router']['hwEntityFanState.0.2'.lower()]
        oid_hwEntityFanState3 = self.configIniDict['HW_FH_Router']['hwEntityFanState.0.3'.lower()]
        oid_ifOperStatus4 = self.configIniDict['HW_FH_Router']['ifOperStatus.4'.lower()]
        oid_ifOperStatus5 = self.configIniDict['HW_FH_Router']['ifOperStatus.5'.lower()]

        #MPU 温度
        hwEntityTemperature = self.getSnmpValue(address, oid_hwEntityTemperature)
        #端口(GE0/0/1)状态 to FH LJ-1
        ifOperStatus4 = self.translateNum2Str(address,oid_ifOperStatus4)
        #端口(GE0/0/2)状态 to NB BL
        ifOperStatus5 = self.translateNum2Str(address,oid_ifOperStatus5)
        #hwEntityFanState1
        hwEntityFanState1 = self.translateNum2Str(address,oid_hwEntityFanState1)
        #hwEntityFanState2
        hwEntityFanState2 = self.translateNum2Str(address,oid_hwEntityFanState2)
        #hwEntityFanState3
        hwEntityFanState3 = self.translateNum2Str(address,oid_hwEntityFanState3)

        print '\nHW_FH_Router Result:'
        print 'MPU温度:'+hwEntityTemperature+\
              '\n风扇1状态:'+hwEntityFanState1+\
              '\nn风扇2状态:'+hwEntityFanState2+\
              '\nn风扇3状态:'+hwEntityFanState3+\
              '\n端口(GE0/0/1)状态:'+ifOperStatus4+\
              '\n端口(GE0/0/2)状态:'+ifOperStatus5

    def getHW_FH_LJ_1(self):
        address = self.configIniDict['HW_FH_LJ-1']['ip'.lower()]
        oid_hwEntityTemperature = self.configIniDict['HW_FH_LJ-1']['hwEntityTemperature.67108873'.lower()]
        oid_hwTrunkOperstatus5 = self.configIniDict['HW_FH_LJ-1']['hwTrunkOperstatus.0.5'.lower()]
        oid_hwTrunkOperstatus6 = self.configIniDict['HW_FH_LJ-1']['hwTrunkOperstatus.0.6'.lower()]

        #MPU 温度
        hwEntityTemperature = self.getSnmpValue(address, oid_hwEntityTemperature)
        #Eth-Trunk端口状态 GE0/0/1
        hwTrunkOperstatus5 = self.translateNum2Str(address,oid_hwTrunkOperstatus5)
        #Eth-Trunk端口状态 GE0/0/2
        hwTrunkOperstatus6 =self.translateNum2Str(address,oid_hwTrunkOperstatus6)


        if( (int(hwEntityTemperature) < 50) and (cmp(hwTrunkOperstatus5,'ok') == 0) and (cmp(hwTrunkOperstatus6,'ok') == 0) ):
            globalStatus = 'ok'
        else:
            globalStatus = 'fault'


        return {
                '1.HostName':'HW_FH_LJ_1',  #手动写的主机名
                '2.GlobalStatus':globalStatus,      #全局状态，需要有个函数来判断的
                '3.CPU Temperature':hwEntityTemperature,
                '4.EthTrunk':hwTrunkOperstatus5+','+hwTrunkOperstatus6
                #'4.EthTrunk':{'GE0/0/1':hwTrunkOperstatus5,'GE0/0/2':hwTrunkOperstatus5}
                }

    def getDeviceOK(self,myDict):
        pass

    def getDeviceStatusBrief(self,myDict):
        '''
        返回设备状态的简单信息
        :param myDict:
        :return:
        '''
        resultStr = ''
        print '\nBrief Device Status:'
        for key in myDict:
            if(key =='1.HostName'):
                resultStr += key+':'+myDict[key]+'\n'
            elif(key =='2.GlobalStatus'):
                resultStr += key+':'+myDict[key]
        return resultStr

    def getDeviceStatusDetail(self,resultDict):
        '''
        返回设备的详细信息
        :param resultDict:
        :return:
        '''
        resultStr = ''
        print '\nDetail Device Status:'
        for key in sorted(resultDict):
            if isinstance(resultDict[key],dict):
                for k in resultDict[key]:
                    resultStr += key+'_'+k+':'+resultDict[key][k]+'\n'
                continue
            resultStr += key+':'+resultDict[key]+'\n'
        return resultStr



def main():
    mySnmp = BydSnmp()
    # mySnmp.getSangforSG() #深信服
    # mySnmp.get360TD() #天堤
    # mySnmp.getDellCMC() #刀框
    # mySnmp.getDelliDRAC8('10.15.0.166')
    # mySnmp.getDelliDRAC8('10.15.0.167')
    # mySnmp.getDelliDRAC8('10.15.0.168')
    # mySnmp.getDelliDRAC6('10.15.0.165')
    #mySnmp.getDellAllStatus()
    #mySnmp.checkDellAll()

    # mySnmp.getHW_BL_LJ_1()
    # mySnmp.getHW_BL_LJ_2()
    # mySnmp.getHW_BL_CUB3F()
    # mySnmp.getHW_BL_PUB1F()
    # mySnmp.getHW_BL_OFF4FTD()
    # mySnmp.getHW_BL_DaMen()

    # mySnmp.getHW_BL_OFF1F_1()
    # mySnmp.getHW_BL_OFF1F_2()
    # mySnmp.getHW_BL_OFF1F_3()
    # mySnmp.getHW_BL_OFF2F_1()
    # mySnmp.getHW_BL_OFF2F_2()
    # mySnmp.getHW_BL_OFF2F_3()
    #mySnmp.getHW_BL_OFF4F()
    #mySnmp.getHW_BL_PUB1F()
    #mySnmp.getHW_BL_PUB3F()
    #mySnmp.getHW_BL_SUBFAB_1()
    #mySnmp.getHW_BL_SUBFAB_2()

    #mySnmp.getHW_BL_AGG()
    #mySnmp.getHW_BL_CORE()
    #mySnmp.getHW_FH_AGG()
    #mySnmp.getHW_FH_AC1()
    #mySnmp.getHW_FH_AC2()

    xxDict = mySnmp.getHW_FH_LJ_1()
    print mySnmp.getDeviceStatusBrief(xxDict)
    print mySnmp.getDeviceStatusDetail(xxDict)
    #mySnmp.getHW_FH_Router()


if __name__ == '__main__':
    main()

