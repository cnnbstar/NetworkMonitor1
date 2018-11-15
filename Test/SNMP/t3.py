# -*- coding:gbk -*-
__author__ = 'li.shida'

from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.hlapi import *

# x= ObjectIdentity('SNMPv2-MIB','system')
# print tuple(x)

g = getCmd(
    SnmpEngine(),
    CommunityData('public@byd'),
    UdpTransportTarget('10.15.2.42',161),
    ContextData,
    ObjectType(ObjectIdentity('1.3.6.1.4.1.2011.6.3.4.1.2.0'))
)

errorIndication,errorStatus,errorIndex,varBinds = next(g)
print varBinds

print next(g)
