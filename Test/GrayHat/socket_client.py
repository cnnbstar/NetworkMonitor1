#!/usr/bin/env python27
# -*- coding: utf-8 -*-

'''
http://blog.chinaunix.net/uid-27659438-id-3351967.html
使用socket远程发送命令并获得执行结果
此处为client端，用于发送命令
'''

import socket
#import WindowsBalloonTip

def socket_send(command):
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('10.15.30.30', 1000))
        sock.send(command)
        result = sock.recv(2048)
        sock.close()
        return result

if __name__ == '__main__':
    # msg = '你好'
    # title = '宁波比亚迪'
    # WindowsBalloonTip(msg.encode('gbk'), title.encode('gbk'))
    print socket_send('netstat -rn').decode('gbk')