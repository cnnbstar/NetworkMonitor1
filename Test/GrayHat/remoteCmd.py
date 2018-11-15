#!/usr/bin/env python27
# -*- coding: utf-8 -*-

"""
@version=v1.0
@author:shihuiyong
@file: RemoteUtil.py
@time: 2016/9/22 10:19
@description='远程执行批处理命令'
"""
import wmi
import time

bat_name = "D:\\date.bat"
logfile = 'logs_%s.txt' % time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime())


class RemoteUtil:
    def __init__(self):
        pass

    @staticmethod
    def call_remote_bat(ipaddress, username, password, date):
        try:
            conn = wmi.WMI(computer=ipaddress, user=username, password=password)
            cmd_call_bat = "cmd /c call %s %s" % (bat_name, date)
            conn.Win32_Process.Create(CommandLine=cmd_call_bat)
            print "执行成功!"
            return True
        except Exception, e:
            log = open(logfile, 'a')
            log.write('%s, call bat Failed!\r\n' % ipaddress)
            log.close()
        return False


if __name__ == "__main__":
    RemoteUtil.call_remote_bat("10.33.27.120", "administrator", "Hik12345", "2016/09/22")
