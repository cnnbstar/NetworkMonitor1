# -*- coding:gbk -*-
__author__ = 'li.shida'
from pysnmp.entity.rfc3413.oneliner import cmdgen

'''
����������һ��arp������arp������ҵ����������Ľ�������mac��ַ��Ȼ���ٴ�mac�˿ڶ�Ӧ�����ҳ��˿�
'''

def getTrunk(ip,port,agent,communication):
    macAddr = []
    macList = []
    portList = []
    macStrList = []
    linkPort = []
    oid1 = (1,3,6,1,2,1,4,22,1,2)#ARP��oid
    oid2 = (1,3,6,1,2,1,17,4,3,1,2)#mac�˿ڶ�Ӧ��lid


    gen = cmdgen.CommandGenerator()

    #��ʼ����
    print 'Start'
    errorIndication1, errorStatus1, errorIndex1, varBinds1 = gen.nextCmd(
        cmdgen.CommunityData(agent,communication,1),
        cmdgen.UdpTransportTarget((ip,port)),
        '1.3.6.1.4.1.2011.6.3.4.1.2.0',
    )

    for varBind in varBinds1:
        print varBind[0]
        # smiName = [x.prettyPrint() for x in varBind][0]
        # smiValue = [x.prettyPrint() for x in varBind][1]
        # print smiName
        # print smiValue

    #���Խ���


    errorIndication, errorStatus, errorIndex, varBinds = gen.nextCmd(
        cmdgen.CommunityData(agent,communication,1),
        cmdgen.UdpTransportTarget((ip,port)),
        oid1,
        )
    #��ȡARP�����mac��ַ
    for varBind in varBinds:
        for name,val in varBind:
            macAddr.append(val.prettyPrint(0))

    gen.ignoreNonIncreasingOid = True#��oid���Էǵ���
    errorIndication, errorStatus, errorIndex, varBinds = gen.nextCmd(
        cmdgen.CommunityData(agent,communication,1),
        cmdgen.UdpTransportTarget((ip,port)),
        oid2,
        )
    #��ȡmac�˿ڶ�Ӧ��ϵ
    for varBind in varBinds:
        for name,val in varBind:
            macList.append(name[-6:])
            portList.append(val.prettyPrint())
    #��ʮ����mac��ַת��Ϊ16���Ƶ��ַ���
    for item in macList:
        temp = ''
        for part in item:
            temp += str(hex(int(part)))[2:]
        temp = '0x' + temp
        macStrList.append(temp)
    for item in macAddr:#��ȡ�˿ں�
        if item in macStrList:
            index = macStrList.index(item)
            linkPort.append(portList[index])
    #ȥ���б��е��ظ�Ԫ��
    linkPort = {}.fromkeys(linkPort).keys()#linkPort = list(set(linkPort))
    return linkPort


def main():
    print getTrunk('10.15.2.254',161,'myagent','public@byd')

if __name__ == '__main__':
    main()