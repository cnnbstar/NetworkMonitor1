# -*- coding:gbk -*-
'''
2种coding申明方式
#coding=gbk/utf-8
# -*- coding:gbk -*-

IDE Encoding
Project Encoding

参考：windows下pycharm编码设置：https://segmentfault.com/q/1010000003951153/a-1020000003952775

'''

__author__ = 'li.shida'


print "running test..."
print u"测试"

w = raw_input(u"输入：".encode("mbcs"))
print u"%s" % (w)

a = u"中文"
print u"Show As: %s" % (a)

