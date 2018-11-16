#!/usr/bin/env python27
# -*- coding: utf-8 -*-

#-*- coding:utf-8 -*-
from flask import Flask,request,make_response,Response
from WXBiz.WXBizMsgCrypt import WXBizMsgCrypt
import xml.etree.cElementTree as ET
import sys
from urllib2 import urlopen
import json
#import WxMessage
#import WxSnmp
from BydMonitor import WxMessage,BydMonitor
app = Flask(__name__)


#http://nbsvpn.byd.com.cn:5000/wxCallbackMsg
@app.route('/wxCallbackMsg',methods=['GET','POST'])
def wxCallbackMsg():
    sToken = 'MCEjp9a9f'
    sEncodingAESKey = 'XOpCngpeuXUaPmyACGVgDtwI68rleIxdisSmUXWQNVc'
    sCorpID = 'ww324ee13912ed789e'

    #https://work.weixin.qq.com/api/doc#12977
    wxcpt=WXBizMsgCrypt(sToken,sEncodingAESKey,sCorpID)
    sVerifyMsgSig=request.args.get('msg_signature')
    sVerifyTimeStamp=request.args.get('timestamp')
    sVerifyNonce=request.args.get('nonce')
    sVerifyEchoStr=request.args.get('echostr')

    sReqMsgSig = sVerifyMsgSig
    sReqTimeStamp = sVerifyTimeStamp
    sReqNonce = sVerifyNonce
    sReqData = request.data

    #yanzheng URL
    if request.method == 'GET':
        ret,sEchoStr=wxcpt.VerifyURL(sVerifyMsgSig, sVerifyTimeStamp,sVerifyNonce,sVerifyEchoStr)
        if (ret != 0 ):
            print "VerifyURLError"
            sys.exit(1)
        return sEchoStr

    #receive client msg
    if request.method == 'POST':
        ret,sMsg=wxcpt.DecryptMsg(sReqData, sReqMsgSig, sReqTimeStamp, sReqNonce)
        if (ret != 0):
            print "VerifyURLError"
            sys.exit(1)

        xml_tree = ET.fromstring(sMsg)
        msgContent = xml_tree.find("Content").text

    #Msg Content Items
    toUserName = xml_tree.find("ToUserName").text
    fromUserName = xml_tree.find("FromUserName").text
    createTime = xml_tree.find("CreateTime").text
    msgType = xml_tree.find("MsgType").text
    msgId = xml_tree.find("MsgId").text
    agentId = xml_tree.find("AgentID").text

    #auto send msg to FromUser
    #myMsg = WxMessage.WxMessage()
    #mySnmp = WxSnmp.WxSnmp()
    #myMsg.wxMessage('hello '+msgContent,fromUserName)
    #myMsg.wxMessage(mySnmp.getStatusByName(msgContent),fromUserName)
    #print mySnmp.getStatusByName(msgContent)

    myMsg = WxMessage()
    myMonitor = BydMonitor()
    myMsg.wxMessage(myMonitor.getStatusByName(msgContent),fromUserName)

    # sRespData ="<xml><ToUserName><![CDATA["+\
    #            toUserName+"]]></ToUserName><FromUserName><![CDATA["+\
    #            fromUserName+"]]></FromUserName><CreateTime>"+\
    #            createTime+"</CreateTime><MsgType><<![CDATA["+\
    #            msgType+"]]></MsgType><Content><![CDATA["+\
    #            msgContent+"]]></Content><MsgId>"+\
    #            msgId+"</MsgId><AgentID>"+\
    #            agentId+"</AgentID></xml>"
    # ret,sEncryptMsg=wxcpt.EncryptMsg(sRespData, sReqNonce, sReqTimeStamp)
    # if( ret!=0 ):
    #     print "EncryptMsgError" + str(ret)
    #     sys.exit(1)
    #     #
    #     # return sEncryptMsg
    # HttpUitls.SetResponse(sEncryptMsg)


    return Response(msgContent)

if __name__ == '__main__':
    app.run(host='10.15.6.7',port=5000,debug=True)
