# -*- coding:gbk -*-
__author__ = 'li.shida'
'''
采用pysnmp rfc3413 模块
输入对应的OID 即可输入对应的值
问题：貌似不支持MIB对象
'''
from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.hlapi import ObjectIdentity,ObjectType

def getTrunk(ip,port,agent,communication):
    gen = cmdgen.CommandGenerator()
    # gen.getCmd()
    # gen.bulkCmd()
    errorIndication1, errorStatus1, errorIndex1, varBinds1 = gen.nextCmd(
        cmdgen.CommunityData(agent,communication,1),
        cmdgen.UdpTransportTarget((ip,port)),
        '.1.3.6.1.4.1.35047.1.3.0'
    )

    for varBind in varBinds1:
        print varBind[0]
        # smiName = [x.prettyPrint() for x in varBind][0]
        # smiValue = [x.prettyPrint() for x in varBind][1]
        # print smiName
        # print smiValue

def main():
    print "\nresult:"
    getTrunk('10.15.1.253',161,'myagent','public@byd')
    # print "\nOFF1F-1 result:"
    # getTrunk('10.15.2.11',161,'myagent','public@byd')
    # print "\nOFF4F result:"
    # getTrunk('10.15.2.41',161,'myagent','public@byd')
    # print "\nFH_1#S1 result:"
    # getTrunk('10.15.255.11',161,'myagent','public@byd')
    # print "\nOFFTD result:"
    # getTrunk('10.15.2.49',161,'myagent','public@byd')
    # print "\nAGG result:"
    # getTrunk('10.15.2.254',161,'myagent','public@byd')

if __name__ == '__main__':
    main()
