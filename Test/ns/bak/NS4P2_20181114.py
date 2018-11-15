#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
NS For Linux Depend on Python2
CentOS 5,6,7 Default has Python2
'''

try:
    from urllib2 import Request,urlopen
    import json
    import sys
except ImportError:
    print 'ImportError'

__all__ = [
    "NS4P2"
]

class NS4P2():
    '''
    初始化说明
    '''
    def __init__(self):
        '''
        NS4P2的初始化函数
        :return:
        '''
        self.param_SECRET = '@superman@ironman'  #发送通知的校验码
        self.param_SENDER = 'NS'                 #通知发送者，默认为NS
        self.param_SUBJECT = 'Notice From Linux' #通知主题
        self.param_PCCMD = 'false'               #是否为PC命令

        self.param_NsHearders = {'Content-Type':'application/json'}      #NS头类型
        self.param_NsUrl = 'http://ns.nbbyd.com/NotificationSystem/send' #NS URL

        self.myDatas ={}

    def __post2NsServer(self,dataDict):
        '''
        内部方法
        通过POST方式将请求数据发送到NS服务器
        :param dataDict
        :return resultDict列表，依次是NS,SMS,PC,WX,MAIL
        '''
        dataJson = json.dumps(dataDict)
        try:
            request = Request(url=self.param_NsUrl,headers=self.param_NsHearders,data=dataJson)
            response = urlopen(request)
            resultDict = json.loads(response.read())
        except Exception as e:
            print 'HttpError'

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

        return {
            'ns':nsResult.decode('utf8').encode('gb2312'),
            'sms':smsResult.decode('utf8').encode('gb2312'),
            'pc':pcResult.decode('utf8').encode('gb2312'),
            'mail':mailResult.decode('utf8').encode('gb2312'),
            'wx':wxResult.decode('utf8').encode('gb2312')
        }

    def __setDatas(self,users,groups,types,content,important):
        '''
        内部方法，设置数据
        :param users 用户列表，如li.shida|he.wenzhen
        :param groups 组列表，如itGroups|ccdGroups
        :param types 通知类型,如PC|WX|SMS|Email
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
            self.myDatas = {
                'sender':self.param_SENDER,
                'togroup':groups,
                'subject':self.param_SUBJECT,
                'content':content,
                'secret':self.param_SECRET,
                'noticetype':types,
                'important':important,
                'pccmd':self.param_PCCMD
            }
        elif groups is  None:
            self.myDatas = {
                'sender':self.param_SENDER,
                'touser':users,
                'subject':self.param_SUBJECT,
                'content':content,
                'secret':self.param_SECRET,
                'noticetype':types,
                'important':important,
                'pccmd':self.param_PCCMD
            }
        else:
            self.myDatas = {
                'sender':self.param_SENDER,
                'touser':users,
                'togroup':groups,
                'subject':self.param_SUBJECT,
                'content':content,
                'secret':self.param_SECRET,
                'noticetype':types,
                'important':important,
                'pccmd':self.param_PCCMD
            }

        return self.myDatas

    def sendNotices(self,myDict):
        '''
        公开方法，用于发送通知
        :param myDict 发送消息的内容
        '''
        #允许接收用户为空
        if myDict['toUsers'] is None:
            users = None
        if myDict['toUsers'] is None:
            users = None
        self.__setDatas(users = myDict['toUsers'],
                        groups = myDict['toGroups'],
                        types = myDict['noticeType'],
                        content=myDict['noticeContent'],
                        important=myDict['typeImportant']
                        )
        #发送通知
        if (myDict['toUsers'] is None and myDict['toGroups'] is None):
            print "Need users Or groups"
            print "-h for Help"
        else:
            self.__post2NsServer(self.myDatas)

    def inputFormat(self,inputList):
        '''
        格式化Shell输入的参数 并转换成字典格式作为返回
        通知内容None，发送类型PC，消息不重要
        :param inputList Shell输入的参数
        :return resultDict
        '''
        resultDict = {'toUsers':None,
                      'toGroups':None,
                      'noticeContent':'None',    #默认通知内容：None
                      'noticeType':'PC',         #默认接收类型：PC
                      'typeImportant':'false'    #默认消息为不重要
                      }

        for l in inputList:
            if l == '-u':
                resultDict['toUsers']=inputList[inputList.index('-u')+1]
            elif l == '-g':
                resultDict['toGroups']=inputList[inputList.index('-g')+1]
            elif l == '-t':
                resultDict['noticeType']=inputList[inputList.index('-t')+1]
            elif l == '-c':
                resultDict['noticeContent']=inputList[inputList.index('-c')+1]
            elif l == '-i':
                resultDict['typeImportant']='true'
            elif l == '-h':
                print "NS4P2.py      Usage:"
                print '-u:users      ;eg:-u "zhang.san|li.si" '
                print '-g:groups     ;eg:-g "group1|group2" '
                print '-t:type       ;eg:-t "Email|SMS|WX|PC" '
                print '-i:important  ;eg:-i '
                print '-c:content    ;eg:-c "Hello,World" '
                sys.exit()
        return resultDict

def main():
    '''
    主程序说明
    :return:
    '''
    try:
        myNS4P2 = NS4P2()
        myParaDict = myNS4P2.inputFormat(sys.argv)
        myNS4P2.sendNotices(myParaDict)
    except Exception as e:
        print 'ExeMainError'  #主程序执行异常


if __name__ =='__main__':
    main()

