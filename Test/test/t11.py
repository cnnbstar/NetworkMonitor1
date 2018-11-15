# -*- coding:gbk -*-
__author__ = 'li.shida'

print ("你好 世界")

'''
#test for var
name = "test"
name1 = name
print name,name1
print id(name1)
print id(name)

print name is "test"
print name == "test"

print "-------"
print name is name1
print name == name1

print "-------"
name = "1"
print id(name)
print id(name1)

print name is name1
print name == name1

#test for if-else
print "______________________"
name = raw_input("input your name:")
if name == "johnny":
    print "Sucess"
else:
    print "False"

'''

'''
#测试if-elif-else
from getpass import getpass
name = raw_input("input your name:")
pwd = getpass("input your passwd:")

if name == "johnny" and pwd == "123":
    print "Success"
elif name == "dazi" and pwd == "123":
    print "Admin"
else:
    print "False"
'''

print "helllo"+" world"
print "I am %s,%d" %('dazi',30)


name_list = ['wang1','wang2','wang3']

list1 = list(['hello','world','!'])
tuple1 = tuple(('hello','world','!'))
dict1 = dict({"name":"wang","age":19})
print list1
print tuple1
print dict1

print type(list1)




for xx in name_list:
    print xx
    if xx == 'wang1':
        print "again"
        continue
    if xx == 'wang2':
        print "got it"
        break

print "hello" and "world"
print "hello" or "world"

print list("ddd")
print tuple("aaa")



print "----------"
wj = [11,22,33]
wj.append(44)


myParams = {
    "server":"mpilgri",
    "database":"master",
    "uid":"sa",
    "pwd":"secret"
}

for k in myParams:
    print k+":"+myParams[k]


print "----------"

print ":".join(
    {
        "%s=%s" %(k,v) for k,v in myParams.items()
    }
)


def buildConnectionString(params):
    print "My Function's Parameter is %s" % params

buildConnectionString("dazi")


i = 123
print type(i)


'''
list []
tuple ()
dict {}

'''


if __name__ == '__main__':
    print "OK"


print '-----------------------------------------'

d_dict = {"server":"mpilgrim","database":"master"}
print d_dict

d_dict["user"]={"first_name":"dazi","lastname":"lee","age":30}
print d_dict


print '___________________________________________'
l_list = ['a','b','c']
print l_list

l_list.append("d")
print l_list


li = ['a','b','mpilgrim']
li = li+['example','new']
len(li)


print '_____________________________________________'
t_tuple = ('a','b','c','d')
print t_tuple



a = "fadslkfjadslfa"
b = tuple(a)
print b

print d_dict.keys()
print d_dict.values()
print d_dict.items()

print '-----------------------------------------------'
li = ['a','mpilgrim','foo','b','c','d','d']
print [elem for elem in li if len(elem)>1]


# methodList = [method for method in dir(object) if callable(object,method)]
# print methodList

print (lambda x:x*2)(3)
print (lambda x,y,z:x+y+z)(1,2,3)

g = lambda x:x*x
print g(100)


print '------------------------------------------------'
s = "this   is\na\ttest"
print s
print s.split()
print " ".join(s.split())

print '_____________________________________________'
# from apihelper import info
# l1_list = []
# print info(l1_list)


print "+".join(["a","b"])
print "a b c d".split(" ")