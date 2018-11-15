#!/usr/bin/env python27
# -*- coding: utf-8 -*-

'''
http://blog.chinaunix.net/uid-27659438-id-3351967.html
使用socket远程发送命令并获得执行结果
此处为server端
绑定1000端口，持续进行监听，'0.0.0.0'表示监听本地
'''

import socket
import os
import sys

def work():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('0.0.0.0',1000))
        sock.listen(5)
        while True:
                try:
                        conn, addr = sock.accept()
                        ret = conn.recv(2048)
                        result = os.popen(ret).read()
                        conn.send(result)
                except KeyboardInterrupt:
                        print 'Now we will exit'
                        sys.exit(0)
        sock.close()

if __name__ == '__main__':
        work()