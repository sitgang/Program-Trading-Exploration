# -*- coding: utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
from colle_tool import mailhelper

mail_list=raw_input(u"你想发送的电子邮箱：")
sub=raw_input(u"你想设为的主题：")

while True:
    sender=mailhelper()
    s=raw_input(u"你想说什么？")
    for i in s:
        sender.send_mail([mail_list,sub,i)