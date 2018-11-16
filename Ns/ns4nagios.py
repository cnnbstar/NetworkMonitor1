#!/usr/bin/env python27
# -*- coding: utf-8 -*-

try:
    from urllib2 import Request,urlopen
    import json
    import sys
    import smtplib
    from email.mime.text import MIMEText
except ImportError:
    print 'ImportError'

__all__ = [
    "NS4P","NS4Nagios"
]

class NS4P:
    '''
    初始化说明
    相比于独立NS4P.py做了如下改动：P254,256去掉repr()，启用\n转义符
    '''
    def __init__(self):
        '''
        NS4P2的初始化函数
        :return:
        '''
        self.postParamData ={}        #待发送的参数
        self.myPostResult = {}  #Post结果集

        #NS内容
        self.param_SECRET = '@superman@ironman'  #发送通知的校验码
        self.param_SENDER = 'NS'                 #通知发送者，默认为NS
        self.param_SUBJECT = 'Notice From Linux' #通知主题
        self.param_PCCMD = 'false'               #是否为PC命令

        #NS URL
        self.param_NsHearders = {'Content-Type':'application/json'}      #NS头类型
        self.param_NsUrl = 'http://ns.nbbyd.com/NotificationSystem/send' #NS URL

        #NS发送异常时，将异常系统发送到内部邮箱，用来告警系统管理员
        #邮件转SMS触发条件：Subject是SMS内容，Content是SMS的手机号
        self.mailSender = 'ns@mon.nbbyd.com'
        self.mailReceiver = 'sms@mon.nbbyd.com'
        #self.mailReceiverUsersList = ['18967892202']
        self.mailReceiverLists = ['18967892202','18967892188','17757400383']
        self.mailHost = '10.15.6.6'
        self.mailHostPort = '25'

    def __post2NsServer(self,postParamDataDict):
        '''
        内部方法
        通过POST方式将请求数据发送到NS服务器
        :param dataDict
        :return resultDict列表，依次是NS,SMS,PC,WX,MAIL
        '''
        dataJson = json.dumps(postParamDataDict)
        try:
            request = Request(url=self.param_NsUrl,headers=self.param_NsHearders,data=dataJson)
            response = urlopen(request)
            resultDict = json.loads(response.read())

            #NS
            nsResult = resultDict['ns_errmsg']

            #PC
            if resultDict['pc'] is not None:
                pcResult = resultDict['pc']['errmsg']
            else:
                pcResult = 'None'

            #SMS
            if resultDict['sms'] is not None:
                smsResult = resultDict['sms']['errmsg']
            else:
                smsResult = 'None'

            #WX
            if resultDict['wx'] is not None:
                wxResult = resultDict['wx']['errmsg']
            else:
                wxResult = 'None'

            #MAIL
            if resultDict['email'] is not None:
                mailResult = resultDict['email']['errmsg']
            else:
                mailResult = 'None'

            self.myPostResult = {
                'post.status':'ok',
                'ns.status':nsResult.decode('utf8').encode('gb2312'),
                'sms.status':smsResult.decode('utf8').encode('gb2312'),
                'pc.status':pcResult.decode('utf8').encode('gb2312'),
                'mail.status':mailResult.decode('utf8').encode('gb2312'),
                'wx.status':wxResult.decode('utf8').encode('gb2312')
            }

        except Exception,e:
            self.myPostResult = {'post.status':'failed'}
            #print 'HttpError'

    def __setDatas(self,users,groups,types,subject,content,important):
        '''
        内部方法，设置数据
        :param users 用户列表，如li.shida|he.wenzhen
        :param groups 组列表，如itGroups|ccdGroups
        :param types 通知类型,如PC|WX|SMS|Email
        :param subject 通知主题
        :param content 通知内容
        :param important 是否为重要通知
        :return myDatas 参数集的字典
        '''
        #判断是否为重要通知
        if important == 'true':
            important = 'true'
        else:
            important = 'false'

        if users is  None:
            self.postParamData = {
                'sender':self.param_SENDER,
                'togroup':groups,
                'subject':subject.strip('\''),
                'content':content.strip('\''),
                'secret':self.param_SECRET,
                'noticetype':types,
                'important':important,
                'pccmd':self.param_PCCMD
            }
        elif groups is  None:
            self.postParamData = {
                'sender':self.param_SENDER,
                'touser':users,
                'subject':subject.strip('\''),
                'content':content.strip('\''),
                'secret':self.param_SECRET,
                'noticetype':types,
                'important':important,
                'pccmd':self.param_PCCMD
            }
        else:
            self.postParamData = {
                'sender':self.param_SENDER,
                'touser':users,
                'togroup':groups,
                'subject':subject.strip('\''),
                'content':content.strip('\''),
                'secret':self.param_SECRET,
                'noticetype':types,
                'important':important,
                'pccmd':self.param_PCCMD
            }

        return self.postParamData

    def __sendSmsMail(self,subject):
        '''
        当NS发送故障时发送故障告警邮件到sms@mon.nbbyd.com
        邮件转SMS触发条件：Subject是SMS内容，Content是SMS的手机号
        :param subject 邮件头
        '''
        #循环发送
        #邮件转SMS触发条件：Subject是SMS内容，Content是SMS的手机号
        for mailReceiverUser in self.mailReceiverUsersList:
            mailMsg = MIMEText(mailReceiverUser)    #邮件正文为手机号，用于转发成短消息
            mailMsg['Subject'] = repr(subject).strip('\'')     #转移成原始字符串
            try:
                s = smtplib.SMTP(self.mailHost,self.mailHostPort)
                s.sendmail(self.mailSender, self.mailReceiver, mailMsg.as_string())
                print "Mail Send Success"
            except s.SMTPException,e:
                print "Mail Send Failed"
            finally:
                s.quit()

    def __checkPostResult(self,inputParamDict):
        '''
        :param inputParamDict 待发送的参数
        '''
        #发送到NS状态检查
        postStatus = self.myPostResult['post.status']
        if postStatus != 'ok':
            print "Post NS Failed!"
            self.__sendSmsMail("Post to NS Failed!")
        else:
            print "Post NS OK"

            #根据Response回值判断状态
            nsStatus = self.myPostResult['ns.status']
            pcStatus= (self.myPostResult['pc.status'] == 'ok' or self.myPostResult['pc.status'] == 'None')
            wxStatus = (self.myPostResult['wx.status'] == 'ok' or self.myPostResult['wx.status'] == 'None')
            mailStatus = (self.myPostResult['mail.status'] == 'ok' or self.myPostResult['mail.status'] == 'None')
            smsStatus = (self.myPostResult['sms.status'] == 'ok' or self.myPostResult['sms.status'] == 'None')

            if (nsStatus and pcStatus and wxStatus and mailStatus and smsStatus):
                print "NS Resp OK"
            else:
                print "NS Resp Failed!"
                subject = inputParamDict['noticeSubject']
                content = inputParamDict['noticeContent']
                mysubject = "NS Resp Status Failed!" + ' '+ subject + ' '+content
                self.__sendSmsMail(mysubject)

    def sendNotices(self,postParamDataDict):
        '''
        公开方法，用于发送通知
        :param myDict 发送消息的内容
        '''
        #允许接收用户为空
        if postParamDataDict['toUsers'] is None:
            users = None
        if postParamDataDict['toUsers'] is None:
            users = None
        self.__setDatas(users = postParamDataDict['toUsers'],
                        groups = postParamDataDict['toGroups'],
                        types = postParamDataDict['noticeType'],
                        subject = postParamDataDict['noticeSubject'],
                        content=postParamDataDict['noticeContent'],
                        important=postParamDataDict['typeImportant']
                        )
        #发送通知
        if (postParamDataDict['toUsers'] is None and postParamDataDict['toGroups'] is None):
            print "Input Users or Groups"
            print "-h for Help"
        else:
            #发送到NS
            self.__post2NsServer(self.postParamData)
            #结果判断
            self.__checkPostResult(postParamDataDict)

    def inputFormat(self,inputList):
        '''
        格式化Shell输入的参数 并转换成字典格式作为返回
        通知内容None，发送类型PC，消息不重要
        :param inputList Shell输入的参数
        :return resultDict
        '''
        resultDict = {'toUsers':None,
                      'toGroups':None,
                      'noticeSubject':'Linux', #默认通知主题：Nbbyd Linux
                      'noticeContent':'None',    #默认通知内容：Nbbyd NS
                      'noticeType':'PC',             #默认接收类型：PC
                      'typeImportant':'false'        #默认消息为不重要
                      }

        for l in inputList:
            if l == '-u':
                resultDict['toUsers']=inputList[inputList.index('-u')+1]
            elif l == '-g':
                resultDict['toGroups']=inputList[inputList.index('-g')+1]
            elif l == '-t':
                resultDict['noticeType']=inputList[inputList.index('-t')+1]
            elif l == '-s':
                #resultDict['noticeSubject']=repr(inputList[inputList.index('-s')+1])
                resultDict['noticeSubject']=inputList[inputList.index('-s')+1]
            elif l == '-c':
                #resultDict['noticeContent']=repr(inputList[inputList.index('-c')+1])
                resultDict['noticeContent']=inputList[inputList.index('-c')+1]
            elif l == '-i':
                resultDict['typeImportant']='true'
            elif l == '-h':
                #programName = inputList[0]  #打印程序名
                print "ns4p           Usage:"
                print "-u:users      ;eg:-u 'zhang.san|li.si' "
                print "-g:groups     ;eg:-g 'group1|group2' "
                print "-s:subject    ;eg:-s 'MES' "
                print "-c:content    ;eg:-c 'Hello,World' "
                print "-t:type       ;eg:-t 'Email|SMS|WX|PC' "
                print "-i:important  ;eg:-i "
                sys.exit()
        return resultDict

class NS4Nagios:

    def __init__(self):
        '''
        初始化
        '''
        try:
            self.myns = NS4P()
            #nagios报警接收者为手机，此处需要转为邮箱
            self.phone2MailDict = {
                '18967892202':'li.shida',
                '18967892188':'he.wenzhen',
                '17757400383':'wang.wenbo1',
                '18967892337':'li.baode',
                '18967892338':'shen.lijuan',
                '18967892156':'ding.jian3',
                '18967892260':'yu.yan5',
                '17757400332':'liu.taotao',
                '18967892356':'shen.kehua',
                '17757400356':'chen.yafei1',
                '17757400393':'che.guiping',
                '18967892269':'li.yulei',
                '18967892045':'wei.hongyan',
                '18967892021':'sun.hao1'
            }
        except Exception:
            print "InitError"

    def __getNagiosContent(self,content):
        '''
        获取Nagios的消息格式
        :param content:Nagios格式的通知内容
        :return:包含Nagios内容和联系人的字典
        '''
        notify_content = ''
        content_data=content.split('-@@-')
        notify_type=content_data[0]
        if notify_type == 'host':
            type1=content_data[1]
            host_name=content_data[2]
            host_state=content_data[3]
            host_address=content_data[4]
            host_info=content_data[5]
            notify_contact=content_data[6]
            notify_content="\n***** Nagios *****\n" \
                             "Type: "+ type1 + \
                             "\nHost: " + host_name + \
                             "\nStat: " + host_state + \
                             "\nAddr: " + host_address + \
                             "\nInfo: " + host_info + "\n"
        elif notify_type == 'service':
            type1=content_data[1]
            service_desc=content_data[2]
            host_name=content_data[3]
            host_address=content_data[4]
            service_state=content_data[5]
            service_info=content_data[6]
            notify_contact=content_data[7]
            notify_content="\n***** Nagios *****\n" \
                            "Type: "+ type1 + \
                           "\nServ: " + service_desc + \
                            "\nHost: " + host_name + \
                            "\nAddr: " + host_address + \
                             "\nStat: " + service_state + \
                             "\nInfo: " + service_info + "\n"

        try:
            #消息字典
            notify = {
                "user":notify_contact,
                "content":notify_content
            }
            return notify

        except Exception:
            print 'NagiosFormatError'

    def sendNagiosMessage(self,content):
        '''
        发送Nagios格式的消息
        :param content: 消息内容
        '''
        try:
            notify = self.__getNagiosContent(content)
            user = notify['user']       #nagios消息接收者
            content = notify['content'] #nagios告警内容

            inputList = [
                '-u',self.phone2MailDict[user],
                '-t','PC|WX',
                '-s','nagios',
                '-c',content,
                '-i'
            ]
            myParaDict = self.myns.inputFormat(inputList)
            self.myns.sendNotices(myParaDict)

        except Exception:
            print 'SendNagiosMessageError'

def main():
    '''
    主函数
    将接收的参数除去'或者''，然后调用sendNagiosMessage
    注意：不接受双引号格式的参数，存在字符串转移的情况
    格式1：python2 WxNagios.py 'host-@@-$NOTIFICATIONTYPE$-@@-$HOSTNAME$-@@-$HOSTSTATE$-@@-$HOSTADDRESS$-@@-$HOSTOUTPUT$-@@-18967892202'
    格式2：python2 WxNagios.py 'service-@@-$NOTIFICATIONTYPE$-@@-$SERVICEDESC$-@@-$HOSTALIAS$-@@-$HOSTADDRESS$-@@-$SERVICESTATE$-@@-$SERVICEOUTPUT$-@@-18967892202'
    '''
    try:
        myNagios = NS4Nagios()
        #myNagios.sendNagiosMessage(hostContent)
        #myNagios.sendNagiosMessage(serviceContent)
        content = sys.argv[1].strip('\'') or sys.argv[1].strip('\'')
        myNagios.sendNagiosMessage(content)
    except Exception,e:
        print 'ExeMainError'

if __name__ == "__main__":
    main()
