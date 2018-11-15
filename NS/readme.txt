

ns4p.py 说明文档
一、简介
ns4p.py，NS通知系统 For Python2的脚本化实现，便于系统管理员调用

二、使用
2.1 python2安装（升级）
    mkdir /usr/local/python2.7    #安装路径

    方法1：
    解压python2.7.tar（编译完成的包）到/usr/local/python2.7

    方法2：
    2.gunzip Python-2.7.11.tgz
    3.tar -xvf Python-2.7.11.tar
    4.cd Python-2.7.11
    5../configure --prefix=/usr/local/python2.7
    6.make && make install
    7./usr/local/python2.7/bin/python -V   #查看版本是否为2.7.11

2.2 脚本位置
    1.mkdir /usr/local/ns
    2.脚本存放路径：/usr/local/ns/ns4p.py

2.3 使用说明
    /usr/local/python2.7/bin/python /usr/local/ns/ns4p.py -h  #查看使用说明
    ns4p           Usage:
    -u:users      ;eg:-u 'zhang.san|li.si'   通知接收者，邮箱账号，使用|分隔符
    -g:groups     ;eg:-g 'group1|group2'     通知接收组，NS管理员定义，使用|分隔符
    -s:subject    ;eg:-s 'MES'               标题，系统主机名或者应用名称等标识符  （默认Linux）
    -c:content    ;eg:-c 'Hello,World'       内容，通知的具体内容                （默认None）
    -t:type       ;eg:-t 'Email|SMS|WX|PC'   类型，邮件、短消息，企业微信，PC     （默认PC）
    -i:important  ;eg:-i                     重要性，特指PC端通知

    示例：
        /usr/local/python2.7/bin/python /usr/local/ns/ns4p.py -u 'li.shida' -s 'NBUTest' -c 'Test' -t 'WX|PC'
    注：
    1.所有输入参数均使用单引号''（当使用双引号时，遇到Shell保留字符时会报错）
    2.-u 或 -g 二者必须有一个输入参数，否则输出：
      Need users Or groups
      -h for Help
    3.当NS异常时，短消息通知NS管理员

三、输出说明
1.Post NS OK
Post到NS正常

2.Post NS Failed!
Post到NS失败

3.NS Resp OK
通知类型(Email|SMS|WX|PC)响应正常，反馈值为ok

4.NS Resp Failed
通知类型(Email|SMS|WX|PC)响应异常，反馈值为非ok

5.Mail Send Success
当“Post NS Failed!” 或者“NS Resp Failed”时，发送邮件通知NS管理员
通知邮件发送成功

6.Mail Send Failed
当“Post NS Failed!” 或者“NS Resp Failed”时，发送邮件通知NS管理员
通知邮件发送失败
