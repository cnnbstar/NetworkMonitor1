# -*- coding:gbk -*-
__author__ = 'li.shida'
from pysnmp.hlapi import *

def test():
    try:
        iterrator = getCmd(
            SnmpEngine(),
            CommunityData('public@byd'),
            UdpTransportTarget(('10.15.2.42', 161)),
            ContextData(),
            ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysDescr', 0))
        )

        errorIndication,errorStatus,errorIndex,varBinds = next(iterrator)

        if errorIndication:
            print (errorIndication)
        else:
            if errorStatus:
                print('%s at %s' % (errorStatus.prettyPrint(),varBinds[int(errorIndex)-1] if errorIndex else '?'))
            else:
                for varBind in varBinds:
                    smiName = [x.prettyPrint() for x in varBind][0]
                    smiValue = [x.prettyPrint() for x in varBind][1]
                    print smiName
                    print smiValue
                    #print (' = '.join([x.prettyPrint() for x in varBind]))
    except Exception as e:
            print 'SmiError'

def main():
    test()

if __name__ == '__main__':
    main()
