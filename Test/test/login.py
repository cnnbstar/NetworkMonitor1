# -*- coding:gbk -*-
__author__ = 'li.shida'

user_file = file('logindb.txt')
user_list = user_file.readlines()
user_file.close()

user_dict = {}

for user in user_list:
    user_str = user.split(';')
    user_dict[user_str[0]] = {'pwd':user_str[1],'times':int(user_str[2].strip())}

while True:
    username = raw_input("intput your name:")
    if username not in user_dict.keys():
        print "username not exist,input again"
    else:
        if user_dict[username]['times'] > 2:
            print 'account had locked'
            break
        else:
            pwd = raw_input('input your pwd:')
            if pwd == user_dict[username]['pwd']:
                user_dict[username]['times'] = 0
                print 'login success'
                break
            else:
                user_dict[username]['times'] += 1

            tmp_list = []
            for key,value in user_dict.items():
                tmp = "%s;%s;%d" %(key,value['pwd'],value['times'])
                tmp_list.append(tmp)
                tmp_str = "\n".join(tmp_list)
                w_obj = file('logindb.txt',mode='w')
                w_obj.write(tmp_str)
                w_obj.flush()
                w_obj.close()