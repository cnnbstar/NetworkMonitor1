# -*- coding:gbk -*-
__author__ = 'li.shida'

from pysnmp.hlapi import *

errorIndication, errorStatus, errorIndex, varBinds = next(
    sendNotification(
        SnmpEngine(),
        CommunityData('public@byd', mpModel=0),
        UdpTransportTarget(('10.15.2.42', 162)),
        ContextData(),
        'trap',
        NotificationType(
            ObjectIdentity('1.3.6.1.4.1.2011.6.3.4.1.2.0')
        )
        # ).addVarBinds(
        #     ('1.3.6.1.6.3.1.1.4.3.0', '1.3.6.1.4.1.20408.4.1.1.2'),
        #     ('1.3.6.1.2.1.1.1.0', OctetString('my system'))
        # )
    )
)

print varBinds

