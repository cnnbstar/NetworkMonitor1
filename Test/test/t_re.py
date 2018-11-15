# -*- coding:gbk -*-
__author__ = 'li.shida'


import re
s = ' 100 NORTH BROAD ROAD'
print re.sub('ROAD$','RD.',s)
print '----------------------'

s1 = ' 100 BROAD'
print re.sub('ROAD$','RD.',s1)
print re.sub(r'\bROAD$','RD.',s1)

s2 = ' 100 BROAD ROAD APT. 3'
print re.sub(r'\bROAD\b','RD.',s2)

print '\b'

print '-----------------------'
pattern = '^M?M?M$'
print re.search(pattern,'M')

#L602605A006 00-25-64-98-B6-78
#C0-3F-D5-ED-80-86
params = {"server":"mpilgrim","database":"master","uid":"sa","pwd":"secret"}
print "%(pwd)s" %params