#!/usr/bin/env python27
# -*- coding: utf-8 -*-

#!/usr/bin/env python27
# -*- coding: utf-8 -*-

try:
    import requests
    from bs4 import BeautifulSoup
    import simplejson
except ImportError:
    print 'ImportError'

__all__ = [
    "WxBydUps"
]


class WxBydUps:
    def __init__(self):
        UA = "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.13 Safari/537.36"
        self.bydUpsPrefixUrl = 'http://res.byd.cn/LocalWebSysC550/'
        self.header = { "User-Agent" : UA, "Referer": "http://res.byd.cn/LocalWebSysC550/login.action"}

    def getUpsId(self,upsName):
        '''
        ups1对应的ID：356
        ups2对应地ID：361
        :param upsName:ups1或者ups2
        :return:UPS对应的ID
        '''
        if(upsName == 'ups1'):
            return '356'
        if(upsName == 'ups2'):
            return '361'

    def getAssMsgUrl(self,upsName):
        '''
        获取辅助信息的URL
        :param upsName: ups1或者ups2
        :return:ups1或者ups2对应的辅助信息的URL地址
        '''
        return self.bydUpsPrefixUrl+'getAssMsg.action?rtuId='+self.getUpsId(upsName)+'&intType=1'

    def getBatMsgUrl(self,upsName):
        '''
        获取电池信息的URL
        :param upsNmae: ups1或者ups2
        :return:ups1或者ups2对应的电池信息的URL地址
        '''
        return self.bydUpsPrefixUrl+'showBat.action?numIndex=1&rtuId='+self.getUpsId(upsName)

    def getPcsMsgUrl(self,upsName):
        '''
        获取PCS信息的URL
        :param upsName: ups1或者ups2
        :return:ups1或者ups2对应的PCS信息的URL地址
        '''
        return self.bydUpsPrefixUrl+'getPcsMsg.action?rtuId='+self.getUpsId(upsName)

    def getLoadMsgUrl(self,upsName):
        '''
        获取负载信息的URL
        :param upsName: ups1或者ups2
        :return:ups1或者ups2对应的负载信息的URL地址
        '''
        return self.bydUpsPrefixUrl+'getLoadMsg.action?rtuId='+self.getUpsId(upsName)

    def getSession(self):
        '''
        获取res.byd.cn的登陆SESSION
        '''
        url_Login = "http://res.byd.cn/LocalWebSysC550/login.action" #登陆地址
        admin_session = requests.Session()
        postData = {'username':'admin', 'password':'123'} #账号密码
        admin_session.post(url_Login,data = postData,headers = self.header)

        return admin_session

    def getJSContent(self,url):
        '''
        获取URL对应的JS动态内容（非HTML）
        '''
        content = self.getSession().get(url,headers=self.header).content

        return content

    def getHtmlContent(self,url):
        '''
        获取URL对应的HTML静态内容
        '''
        pass
        '''
        url_ups1 = 'http://res.byd.cn/LocalWebSysC550/showAssMsg.action?upsName=%E5%AE%81%E6%B3%A2ups1&rtuId=356&intType=1'
        page_NB_UPS1_AssMsg = self.getSession().get(url_ups1,headers=self.header)
        #print(page_NB_UPS1_AssMsg.content.decode('utf-8'))
        #print(page_NB_UPS2_AssMsg.content.decode('utf-8'))

        content_NB_UPS1_AssMsg = page_NB_UPS1_AssMsg.content
        contentTD =  BeautifulSoup(content_NB_UPS1_AssMsg, "html.parser").findAll('td',attrs={'class':'tdCss'})
        for i in range(10):
            print contentTD[i]
        # 输出结果：
        # <td class="tdCss" width="20%">控制柜内环境温度(℃)：</td>
        # <td align="left" class="tdCss" width="15%"><span style="color:blue;"></span></td>
        # <td class="tdCss" width="20%">旁路控制箱温度1(℃)：</td>
        # <td align="left" class="tdCss" width="15%"><span style="color:blue;"></span></td>
        # <td class="tdCss" width="20%">变压器温度(℃)：</td>
        # <td align="left" class="tdCss" width="10%"><span style="color:blue;"></span></td>
        # <td class="tdCss" width="20%">控制柜内环境湿度(%)：</td>
        # <td align="left" class="tdCss" width="15%"><span style="color:blue;"></span></td>
        # <td class="tdCss" width="20%">旁路控制箱温度2(℃)：</td>
        # <td align="left" class="tdCss" width="15%"><span style="color:blue;"></span></td>
        '''

    def getUpsBoxTemp(self,upsName):
        '''
        UPS控制柜环境温度
        :return:UPS柜子温度
        '''
        # {"datas":["35","40","32","40","37"],"intType":1,"rtuId":356}
        # ups1Str[10:-26]  "35","40","32","39","37"
        # str.split(',')[0][1:-1] :35
        return self.getJSContent(self.getAssMsgUrl(upsName))[10:-26].split(',')[0][1:-1]

    def getUpsBoxHumidity(self,upsName):
        '''
        UPS控制柜环境湿度
        :return:UPS柜子湿度
        '''
        return self.getJSContent(self.getAssMsgUrl(upsName))[10:-26].split(',')[3][1:-1]

    def upsAssMsg(self,upsName):
        '''
        辅助信息
        '''
        assMsg = self.getJSContent(self.getAssMsgUrl(upsName))
        assAllList = simplejson.loads(assMsg)['datas'] #['35', '40', '32', '39', '37']
        assHJTemp = assAllList[0] #柜内环境温度
        assBYQTemp = assAllList[2] #变压器温度
        assHJHumidity = assAllList[3] #柜内环境湿度

        #辅助状态检查
        checkAssStatus = False
        checkFaltResult = ''
        if( int(assHJTemp) < 40 and
            int(assHJHumidity) < 70 and
            int(assBYQTemp) < 40
          ):
            checkAssStatus = True
        else:
             checkFaltResult = \
            '辅助信息'.decode('utf-8')+'\n' \
            '柜内环境温度(<40):'.decode('utf-8')+assHJTemp+'\n' \
            '柜内环境湿度(<70):'.decode('utf-8')+assHJHumidity+'\n' \
            '变压器温度  (<40):'.decode('utf-8')+assBYQTemp

        return  '辅助信息'.decode('utf-8')+'\n' \
                '柜内环境温度:'.decode('utf-8')+assHJTemp+'\n' \
                '柜内环境湿度:'.decode('utf-8')+assHJHumidity+'\n' \
                '变压器温度  :'.decode('utf-8')+assBYQTemp,checkAssStatus,checkFaltResult

    def upsBatMsg(self,upsName):
        '''
        电池组信息
        '''
        batMsg = self.getJSContent(self.getBatMsgUrl(upsName)) #
        bmsAllList = simplejson.loads(batMsg)['bmsAllList'] #电池组状态列表（将batMsg字符串类型转换为字典，并取bmsAllList的value值）
        bmsStatus = bmsAllList[1] #电池组状态
        bmsSOC = bmsAllList[9] #组SOC%
        bmsTemp = bmsAllList[2] #电池组平均温度
        bmsTotalVoltage = bmsAllList[7] #总电压
        bmsTotalCurrent = bmsAllList[8] #组电流
        bmsCellMaxVoltage = bmsAllList[11] #单节电压最大值
        bmsCellMixVoltage = bmsAllList[14] #单节电压最小值

        #电池组状态检查
        checkAssStatus = False
        checkFaltResult = ''
        if( cmp(bmsStatus,'运行'.decode('utf-8')) == 0 and
            float(bmsSOC) > 60 and
            int(bmsTemp) < 35 and
            float(bmsTotalVoltage) < 750 and
            float(bmsCellMaxVoltage) < 3.5 and
            float(bmsCellMixVoltage) > 3
           ):
            checkAssStatus = True
        else:
            checkFaltResult = \
            '电池组信息'.decode('utf-8')+'\n' \
            '工作状态(运行):'.decode('utf-8')+bmsStatus+'\n' \
            '平均温度(<35):'.decode('utf-8')+bmsTemp+'\n' \
            '总电压 (<750):'.decode('utf-8')+bmsTotalVoltage+'\n' \
            'SoC(%) (>60):'.decode('utf-8')+bmsSOC+'\n' \
            '单节最大电压(<3.5):'.decode('utf-8')+bmsCellMaxVoltage+'\n' \
            '单节最小电压(>3)  :'.decode('utf-8')+bmsCellMixVoltage

        return  '电池组信息'.decode('utf-8')+'\n' \
                '工作状态:'.decode('utf-8')+bmsStatus+'\n' \
                '平均温度:'.decode('utf-8')+bmsTemp+'\n' \
                '总电压  :'.decode('utf-8')+bmsTotalVoltage+'\n' \
                '总电流  :'.decode('utf-8')+bmsTotalCurrent+'\n' \
                'SoC(%)  :'.decode('utf-8')+bmsSOC+'\n' \
                '单节最大电压:'.decode('utf-8')+bmsCellMaxVoltage+'\n' \
                '单节最小电压:'.decode('utf-8')+bmsCellMixVoltage,checkAssStatus,checkFaltResult

    def upsPcsMsg(self,upsName):
        '''
        PCS信息
        '''
        pcsMsg = self.getJSContent(self.getPcsMsgUrl(upsName))
        pcsAllList = simplejson.loads(pcsMsg)['datas'] #PCS状态列表（将pcsMsg字符串类型转换为字典，并取datas的value值）
        #整流器信息
        zlqList = pcsAllList[:25]
        zlqStatus = zlqList[0]   #工作状态
        zlqWorkMode = zlqList[1] #工作模式

        #逆变器信息
        nbqList = pcsAllList[25:]
        nbqStatus = nbqList[0]   #工作状态
        nbqWorkMode = nbqList[1] #工作模式

        #PCS状态检查
        checkAssStatus = False
        checkFaltResult = ''
        if( cmp(zlqStatus,'运行'.decode('utf-8')) == 0 and
            cmp(zlqWorkMode,'恒流模式'.decode('utf-8')) == 0 and
            cmp(nbqStatus,'运行'.decode('utf-8')) == 0 and
            cmp(nbqWorkMode,'UPS模式'.decode('utf-8')) == 0

           ):
            checkAssStatus = True
        else:
            checkFaltResult = \
            'PCS信息'.decode('utf-8')+'\n' \
            '整流器状态(运行):'.decode('utf-8')+zlqStatus+'\n' \
            '整流器模式(恒流模式):'.decode('utf-8')+zlqWorkMode+'\n' \
            '逆变器状态(运行):'.decode('utf-8')+nbqStatus+'\n' \
            '逆变器模式(UPS模式):'.decode('utf-8')+nbqWorkMode

        return 'PCS信息'.decode('utf-8')+'\n' \
               '整流器状态:'.decode('utf-8')+zlqStatus+'\n' \
               '整流器模式:'.decode('utf-8')+zlqWorkMode+'\n' \
               '逆变器状态:'.decode('utf-8')+nbqStatus+'\n' \
               '逆变器模式:'.decode('utf-8')+nbqWorkMode,checkAssStatus,checkFaltResult

    def upsLoadMsg(self,upsName):
        '''
        负载信息
        '''
        loadMsg = self.getJSContent(self.getLoadMsgUrl(upsName))
        loadAllList = simplejson.loads(loadMsg)['datas']
        loadStatus = loadAllList[0]     #工作状态
        loadWorkMode = loadAllList[2]   #工作模式
        loadFactor = loadAllList[3]     #负载率
        loadOnlineTime = loadAllList[4] #备点时间

        #电池组状态检查
        checkAssStatus = False
        checkFaltResult = ''
        if( cmp(loadStatus,'运行'.decode('utf-8')) == 0 and
            cmp(loadWorkMode,'在线模式'.decode('utf-8')) == 0 and
            float(loadFactor) < 15
           ):
            checkAssStatus = True
        else:
            checkFaltResult = \
            '负载信息'.decode('utf-8')+'\n' \
            '工作状态(运行):'.decode('utf-8')+loadStatus+'\n'  \
            '工作模式(在线模式):'.decode('utf-8')+loadWorkMode+'\n' \
            '负载率  (<15):'.decode('utf-8')+loadFactor

        return '负载信息'.decode('utf-8')+'\n' \
               '工作状态:'.decode('utf-8')+loadStatus+'\n'  \
               '工作模式:'.decode('utf-8')+loadWorkMode+'\n' \
               '负载率  :'.decode('utf-8')+loadFactor+'\n' \
               '备电时间:'.decode('utf-8')+loadOnlineTime,checkAssStatus,checkFaltResult

    def checkUpsStatus(self,upsName):
        '''
        检查UPS工作状态
        '''
        assStatus = self.upsAssMsg(upsName)[1] #辅助状态
        assFaultResult = self.upsAssMsg(upsName)[2] #辅助故障结果

        batStatus = self.upsBatMsg(upsName)[1] #
        batFaultResult = self.upsBatMsg(upsName)[2]

        pcsStatus = self.upsPcsMsg(upsName)[1]
        pcsFaultResult = self.upsPcsMsg(upsName)[2]

        loadStatus = self.upsLoadMsg(upsName)[1]
        loadFaultResult = self.upsLoadMsg(upsName)[2]

        if(assStatus and batStatus and pcsStatus and loadStatus):
            return True
        else:
            result = ''
            if(not assStatus):result += assFaultResult+'\n\n'
            if(not batStatus):result += batFaultResult+'\n\n'
            if(not pcsStatus):result += pcsFaultResult+'\n\n'
            if(not loadStatus):result += loadFaultResult+'\n\n'

            return result

    def getUpsInfo(self,upsName):
        '''
        UPS负载、PCS、电池组、辅助信息
        '''
        return '***'+upsName.upper()+'***'+'\n'+\
               self.upsAssMsg(upsName)[0]+'\n\n'+\
               self.upsBatMsg(upsName)[0]+'\n\n'+\
               self.upsPcsMsg(upsName)[0]+'\n\n'+\
               self.upsLoadMsg(upsName)[0]

def main():
    try:
        myBydUps = WxBydUps()
        # print myBydUps.getUpsBoxTemp('ups1') #UPS柜子温度
        # print myBydUps.getUpsBoxHumidity('ups1') #UPS柜子湿度
        #print myBydUps.getUpsInfo('ups1')
        #print myBydUps.getUpsInfo('ups2')
        print myBydUps.checkUpsStatus('ups1')
        print myBydUps.checkUpsStatus('ups2')

    except Exception as e:
            print 'ExeMainError'  #主程序执行异常

if __name__ == '__main__':
    main()










