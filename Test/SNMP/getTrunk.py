# -*- coding:gbk -*-
__author__ = 'li.shida'
from pysnmp.entity.rfc3413.oneliner import cmdgen

'''
交换机里有一个arp表，利用arp表可以找到与其相连的交换机的mac地址，然后再从mac端口对应表里找出端口
'''

def getTrunk(ip,port,agent,communication):
    macAddr = []
    macList = []
    portList = []
    macStrList = []
    linkPort = []
    oid1 = (1,3,6,1,2,1,4,22,1,2)#ARP表oid
    oid2 = (1,3,6,1,2,1,17,4,3,1,2)#mac端口对应表lid


    gen = cmdgen.CommandGenerator()

    #开始测试
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

    #测试结束


    errorIndication, errorStatus, errorIndex, varBinds = gen.nextCmd(
        cmdgen.CommunityData(agent,communication,1),
        cmdgen.UdpTransportTarget((ip,port)),
        oid1,
        )
    #获取ARP表里的mac地址
    for varBind in varBinds:
        for name,val in varBind:
            macAddr.append(val.prettyPrint(0))

    gen.ignoreNonIncreasingOid = True#让oid可以非递增
    errorIndication, errorStatus, errorIndex, varBinds = gen.nextCmd(
        cmdgen.CommunityData(agent,communication,1),
        cmdgen.UdpTransportTarget((ip,port)),
        oid2,
        )
    #获取mac端口对应关系
    for varBind in varBinds:
        for name,val in varBind:
            macList.append(name[-6:])
            portList.append(val.prettyPrint())
    #将十进制mac地址转化为16进制的字符串
    for item in macList:
        temp = ''
        for part in item:
            temp += str(hex(int(part)))[2:]
        temp = '0x' + temp
        macStrList.append(temp)
    for item in macAddr:#获取端口号
        if item in macStrList:
            index = macStrList.index(item)
            linkPort.append(portList[index])
    #去除列表中的重复元素
    linkPort = {}.fromkeys(linkPort).keys()#linkPort = list(set(linkPort))
    return linkPort


def main():
    print getTrunk('10.15.2.254',161,'myagent','public@byd')

if __name__ == '__main__':
    main()