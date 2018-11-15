# -*- coding:gbk -*-
__author__ = 'li.shida'

from pysnmp.hlapi import *


def getSnmp(ip,oid):
    try:
        iterrator = getCmd(
            SnmpEngine(),
            CommunityData('public@byd'),
            UdpTransportTarget((ip, 161)),
            ContextData(),
            ObjectType(ObjectIdentity(oid))
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
                        mibValue = [x.prettyPrint() for x in varBind][1] #只返回第一行（当字符串有多行时，仅返回第一行）
                        return mibValue[:].split('\r')[0]

    except Exception as e:
        print e
        print 'Error'

def main():
    #print getSnmp('10.15.1.251','.1.3.6.1.4.1.32328.6.1.8.0')
    print getSnmp('10.15.8.96','.1.3.6.1.2.1.1.1')

if __name__ == '__main__':
    main()



