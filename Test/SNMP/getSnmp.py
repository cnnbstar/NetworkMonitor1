# -*- coding:gbk -*-
__author__ = 'li.shida'
from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.hlapi import *
from pysnmp.hlapi import getCmd
from pysnmp.hlapi import bulkCmd
from pysnmp.hlapi import ObjectIdentity
from pysnmp.hlapi import ObjectType

def snmpget(ip,port,communication,version,agent,oid):
    # cg = cmdgen.CommandGenerator()
    #
    # errorIndication, errorStatus, errorIndex, varBinds = cg.getCmd(
    # cmdgen.CommunityData(agent, communication, version),
    # cmdgen.UdpTransportTarget((ip, port)),
    # oid
    # )
    # print str(varBinds[0][1]); ##varBinds返回是一个stulp，含有MIB值和获得值

    g = getCmd(
        SnmpEngine(),
        CommunityData(communication),
        UdpTransportTarget('10.15.2.42',161),
        ContextData(),
        ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysDescr', 0))
    )

    print next(g)


def main():
    ip='10.15.2.42'
    port=161
    communication='public@byd'
    version=0
    agent='myAgent'

    oid='.1.3.6.1.2.1.1.1.0'
    snmpget(ip,port,communication,version,agent,oid)

    # print ObjectType(ObjectIdentity('SNMPv2-MIB','sysDescr',0))

if __name__ =='__main__':
    main()

