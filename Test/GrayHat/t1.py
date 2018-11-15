#!/usr/bin/env python27
# -*- coding: utf-8 -*-

from ctypes import *

msvcrt = cdll.msvcrt
message_string = 'Hello World!'
msvcrt.printf('Testing:%s',message_string)
