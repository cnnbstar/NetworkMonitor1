#!/usr/bin/env python27
# -*- coding: utf-8 -*-

def hello():
    return 'hello'

if __name__ == '__main__':
    print('###' * 10)
    print('###' * 10)
    print('###' * 10)
    print('###' * 10)
    name = raw_input("Please input your name: ")
    print(hello() + name)
    print('###' * 10)