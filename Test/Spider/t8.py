#!/usr/bin/env python27
# -*- coding: utf-8 -*-

import ssl
import urllib2

ssl._create_default_https_context = ssl._create_unverified_context
req = urllib2.Request('https://inv-veri.chinatax.gov.cn/')
data = urllib2.urlopen(req).read()
print(data)
