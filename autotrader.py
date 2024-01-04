#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 11 23:25:19 2023

@author: xylhfree
"""

#! /usr/bin/env python
# coding=utf-8




import os as os
from THSTraderfuture import *
import time
from datetime import datetime
import logging



os.system("adb kill-server")
# os.system("adb start-server")
d = os.system("adb devices")
# d = os.system("python -m uiautomator2 init")

yuanyou = 'sc2401'
luowengang = 'rb2401'
jiachun='ma2401'
chunjian='sa2401'

# 交谊品种

traderfuture = THSTraderfuture(r"emulator-5554")
# 1 is real, 0 is moni
traderfuture.mode=0
traderfuture.bid = chunjian

# 创建一个logger
logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)      
# 创建一个handler，用于写入日志文件
fh = logging.FileHandler('my_log.log')
fh.setLevel(logging.DEBUG)      
# 定义handler的输出格式
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)      
# 给logger添加handler
logger.addHandler(fh)




# 初始界面 
traderfuture.back_to_moni_page()      
balance=traderfuture.get_balance()       
# 获取行情
traderfuture.hangqing(traderfuture.bid)
traderfuture.tradejudge(traderfuture.bid,tempamount)
traderfuture.EmailMeg('平仓成功，盈亏比例为'+str(bili)+str('%'))

