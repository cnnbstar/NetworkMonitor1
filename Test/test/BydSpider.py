#!/usr/bin/env python27
# -*- coding: utf-8 -*-

try:
    import requests
    import csv
    import random
    import time
    import socket
    #import http.client #python3由httplib改名为http.client
    import httplib
    # import urllib.request
    from bs4 import BeautifulSoup
    import simplejson
except ImportError:
    print 'ImportError'

__all__ = [
    "BydWeather","BydUps"
]

class BydWeather:
    '''
    从中国气象网抓取北仑近一周的天气，并打印今明两天或者最近7天的天气
    '''
    def __init__(self):
        '''
        初始化设置北仑URL地址
        '''
        self.bl_url ='http://www.weather.com.cn/weather/101210410.shtml'

    def __getContent(self,url ):
        '''
        模拟浏览器访问，获取HTML源代码
        :param url:中国天气网之北仑URL
        :return:HTML源代码
        '''
        header={
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.235'
        }
        timeout = random.choice(range(80, 180)) #加入随机数，防止被网站识别
        while True:
            try:
                rep = requests.get(url,headers = header,timeout = timeout)
                rep.encoding = 'utf-8'
                # req = urllib.request.Request(url, data, header)
                # response = urllib.request.urlopen(req, timeout=timeout)
                # html1 = response.read().decode('UTF-8', errors='ignore')
                # response.close()
                break
            # except urllib.request.HTTPError as e:
            #         print( '1:', e)
            #         time.sleep(random.choice(range(5, 10)))
            #
            # except urllib.request.URLError as e:
            #     print( '2:', e)
            #     time.sleep(random.choice(range(5, 10)))
            except socket.timeout as e:
                print( '3:', e)
                time.sleep(random.choice(range(8,15)))

            except socket.error as e:
                print( '4:', e)
                time.sleep(random.choice(range(20, 60)))

            #except http.client.BadStatusLine as e:
            except httplib.BadStatusLine as e:
                print( '5:', e)
                time.sleep(random.choice(range(30, 80)))

            except httplib.IncompleteRead as e:
                print( '6:', e)
                time.sleep(random.choice(range(5, 15)))

        return rep.text
        # return html_text

    def __getData(self,html_text):
        '''
        通过正则匹配，获取指定标签中的内容
        :param html_text: HTML源代码
        :return:气象具体内容
        '''
        final = []
        bs = BeautifulSoup(html_text, "html.parser")  # 创建BeautifulSoup对象
        body = bs.body # 获取body部分
        data = body.find('div', {'id': '7d'})  # 找到id为7d的div
        ul = data.find('ul')  # 获取ul部分
        li = ul.find_all('li')  # 获取所有的li

        for day in li: # 对每个li标签中的内容进行遍历
            temp = []
            date = day.find('h1').string  # 找到日期
            temp.append(date.encode('utf-8'))  # 添加到temp中
            inf = day.find_all('p')  # 找到li中的所有p标签
            temp.append(inf[0].string.encode('utf-8'),)  # 第一个p标签中的内容（天气状况）加到temp中
            if inf[1].find('span') is None:
                temperature_highest = None # 天气预报可能没有当天的最高气温（到了傍晚，就是这样），需要加个判断语句,来输出最低气温
            else:
                temperature_highest = inf[1].find('span').string  # 找到最高温
                temperature_highest = temperature_highest.replace(u'℃', '')  # 到了晚上网站会变，最高温度后面也有个℃
            temperature_lowest = inf[1].find('i').string  # 找到最低温
            temperature_lowest = temperature_lowest.replace(u'℃', '')  # 最低温度后面有个℃，去掉这个符号
            temp.append(temperature_highest.encode('utf-8'))   # 将最高温添加到temp中
            temp.append(temperature_lowest.encode('utf-8'))   #将最低温添加到temp中
            final.append(temp)   #将temp加到final中
        return final

    def __getWeather(self):
        '''
        天气列表
        :return:包含未来7天天气内容的列表
        '''
        html = self.__getContent(self.bl_url)
        weathersLists = self.__getData(html)
        return weathersLists

    def __print7Days(self):
        '''
        打印未来7天的天气
        '''
        weathers = self.__getWeather()
        for weather in weathers:
            print weather[0]+':'+weather[1]+'，温度:'+weather[3]+'-'+weather[2]

    def get2Days(self):
        '''
        打印未来2天的天气
        '''
        weathers = self.__getWeather()
        todayResult = weathers[0][0]+':'+weathers[0][1]+',温度:'+weathers[0][3]+'-'+weathers[0][2]
        tomorrowResutl = weathers[1][0]+':'+weathers[1][1]+',温度:'+weathers[1][3]+'-'+weathers[1][2]
        return todayResult+'\n'+tomorrowResutl

class BydUps:
    def __init__(self):
        UA = "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.13 Safari/537.36"
        self.bydUpsPrefixUrl = 'http://res.byd.cn/LocalWebSysC550/'
        self.header = { "User-Agent" : UA, "Referer": "http://res.byd.cn/LocalWebSysC550/login.action"}

    def __getUpsId(self,upsName):
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

    def __getAssMsgUrl(self,upsName):
        '''
        获取辅助信息的URL
        :param upsName: ups1或者ups2
        :return:ups1或者ups2对应的辅助信息的URL地址
        '''
        return self.bydUpsPrefixUrl+'getAssMsg.action?rtuId='+self.__getUpsId(upsName)+'&intType=1'

    def __getBatMsgUrl(self,upsName):
        '''
        获取电池信息的URL
        :param upsNmae: ups1或者ups2
        :return:ups1或者ups2对应的电池信息的URL地址
        '''
        return self.bydUpsPrefixUrl+'showBat.action?numIndex=1&rtuId='+self.__getUpsId(upsName)

    def __getPcsMsgUrl(self,upsName):
        '''
        获取PCS信息的URL
        :param upsName: ups1或者ups2
        :return:ups1或者ups2对应的PCS信息的URL地址
        '''
        return self.bydUpsPrefixUrl+'getPcsMsg.action?rtuId='+self.__getUpsId(upsName)

    def __getLoadMsgUrl(self,upsName):
        '''
        获取负载信息的URL
        :param upsName: ups1或者ups2
        :return:ups1或者ups2对应的负载信息的URL地址
        '''
        return self.bydUpsPrefixUrl+'getLoadMsg.action?rtuId='+self.__getUpsId(upsName)

    def __getSession(self):
        '''
        获取res.byd.cn的登陆SESSION
        '''
        url_Login = "http://res.byd.cn/LocalWebSysC550/login.action" #登陆地址
        adminSession = requests.Session()
        postData = {'username':'admin', 'password':'123'} #账号密码
        adminSession.post(url_Login,data = postData,headers = self.header)

        return adminSession

    def __getJSContent(self,url):
        '''
        获取URL对应的JS动态内容（非HTML）
        '''
        content = self.__getSession().get(url,headers=self.header).content

        return content

    def __getHtmlContent(self,url):
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

    def __upsAssMsg(self,upsName):
        '''
        辅助信息
        '''
        assMsg = self.__getJSContent(self.__getAssMsgUrl(upsName))
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

    def __upsBatMsg(self,upsName):
        '''
        电池组信息
        '''
        batMsg = self.__getJSContent(self.__getBatMsgUrl(upsName)) #
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
            float(bmsTotalVoltage) < 755 and
            float(bmsCellMaxVoltage) < 3.5 and
            float(bmsCellMixVoltage) > 3
           ):
            checkAssStatus = True
        else:
            checkFaltResult = \
            '电池组信息'.decode('utf-8')+'\n' \
            '工作状态(运行):'.decode('utf-8')+bmsStatus+'\n' \
            '平均温度(<35):'.decode('utf-8')+bmsTemp+'\n' \
            '总电压 (<755):'.decode('utf-8')+bmsTotalVoltage+'\n' \
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

    def __upsPcsMsg(self,upsName):
        '''
        PCS信息
        '''
        pcsMsg = self.__getJSContent(self.__getPcsMsgUrl(upsName))
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

    def __upsLoadMsg(self,upsName):
        '''
        负载信息
        '''
        loadMsg = self.__getJSContent(self.__getLoadMsgUrl(upsName))
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

    def getUpsStatus(self,upsName):
        '''
        检查UPS工作状态
        '''
        assStatus = self.__upsAssMsg(upsName)[1] #辅助状态
        assFaultResult = self.__upsAssMsg(upsName)[2] #辅助故障结果

        batStatus = self.__upsBatMsg(upsName)[1] #
        batFaultResult = self.__upsBatMsg(upsName)[2]

        pcsStatus = self.__upsPcsMsg(upsName)[1]
        pcsFaultResult = self.__upsPcsMsg(upsName)[2]

        loadStatus = self.__upsLoadMsg(upsName)[1]
        loadFaultResult = self.__upsLoadMsg(upsName)[2]

        if(assStatus and batStatus and pcsStatus and loadStatus):
            return 'ok','ok'
        else:
            result = ''
            if(not assStatus):result += assFaultResult+'\n\n'
            if(not batStatus):result += batFaultResult+'\n\n'
            if(not pcsStatus):result += pcsFaultResult+'\n\n'
            if(not loadStatus):result += loadFaultResult+'\n\n'

            return 'fault',result

    def getUpsInfo(self,upsName):
        '''
        UPS负载、PCS、电池组、辅助信息
        '''
        return '***'+upsName.upper()+'***'+'\n'+\
               self.__upsAssMsg(upsName)[0]+'\n\n'+\
               self.__upsBatMsg(upsName)[0]+'\n\n'+\
               self.__upsPcsMsg(upsName)[0]+'\n\n'+\
               self.__upsLoadMsg(upsName)[0]

    def getUpsBoxTemp(self,upsName):
        '''
        UPS控制柜环境温度
        :return:UPS柜子温度
        '''
        # {"datas":["35","40","32","40","37"],"intType":1,"rtuId":356}
        # ups1Str[10:-26]  "35","40","32","39","37"
        # str.split(',')[0][1:-1] :35
        return self.__getJSContent(self.__getAssMsgUrl(upsName))[10:-26].split(',')[0][1:-1]

    def getUpsBoxHumidity(self,upsName):
        '''
        UPS控制柜环境湿度
        :return:UPS柜子湿度
        '''
        return self.__getJSContent(self.__getAssMsgUrl(upsName))[10:-26].split(',')[3][1:-1]\

class HPServer():
    pass

def main():
    try:
        pass
        # blWeather = BydWeather()
        # print blWeather.get2Days()

        # myBydUps = BydUps()
        # # # print myBydUps.getUpsBoxTemp('ups1') #UPS柜子温度
        # # # print myBydUps.getUpsBoxHumidity('ups1') #UPS柜子湿度
        # # #print myBydUps.getUpsInfo('ups1')
        # # #print myBydUps.getUpsInfo('ups2')
        # print myBydUps.getUpsInfo('ups1')
        # print myBydUps.getUpsInfo('ups2')

    except Exception as e:
        print 'ExeMainError'  #主程序执行异常

if __name__ == '__main__':
    main()

