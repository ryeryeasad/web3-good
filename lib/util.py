#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# @Time     : 2022/8/21 12:57 
# @Author   : 0xJohsnon
# @File     : util.py
# @Usage    :

def convert_second(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%02d:%02d:%02d" % (h, m, s)
