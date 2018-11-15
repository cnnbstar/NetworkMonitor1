#!/usr/bin/env python27
# -*- coding: utf-8 -*-

from BydMonitor import WxMessage,BydMonitor

myMsg = WxMessage()
myMonitor = BydMonitor()
xx = myMonitor.getStatusByName('ups1')
myMsg.wxMessage(xx)
