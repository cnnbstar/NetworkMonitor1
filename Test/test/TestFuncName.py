#!/usr/bin/env python27
# -*- coding: utf-8 -*-

# def func_year(s):
#  print 'func_year:', s
#
# def func_month(s):
#  print 'func_month:', s
#
# strs = ['year', 'month']
# for s in strs:
#  globals().get('func_%s' % s)(s)

'''
测试获取函数名字
'''

import sys

class foo(object):
    def load(self,procName):
        f = getattr(self, procName)
        return f()

    def json(self):
        print 'ok'
        return [1,2,3]
        print sys._getframe().f_code.co_name

class A:
    def test(self):
        self.myfunc = foo()
        print self.myfunc.load('json')[0]
        #print self.myfunc.load('json')[0]

def main():
    myA = A()
    myA.test()

if __name__ == '__main__':
    main()

