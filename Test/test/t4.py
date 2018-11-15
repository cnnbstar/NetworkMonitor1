#!/usr/bin/env python27
# -*- coding: utf-8 -*-

import sys
import os
import io


users=os.popen("net user").read()
f=io.open("t4.txt",'w',encoding='utf-8')
f.write(users.decode('gbk'))
f.close()


# fos = open("t4.text","w",encoding="utf-8")
# fos.write("我今年十八岁".decode('utf-8'))
# fos.close()