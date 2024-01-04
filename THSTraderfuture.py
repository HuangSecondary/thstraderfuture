import time
from datetime import datetime
import os
import uiautomator2 as u2
import easyocr
import multiprocessing
from PIL import Image
import re
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.mime.multipart import MIMEMultipart
import logging

# import cv2 
# pip install -i https://pypi.tuna.tsinghua.edu.cn/simple uiautomator2


PAGE_INDICATOR = {
    "AppRank": "com.hexin.android.futures:id/ivScoreRefuse",
    "首页广告": "com.hexin.android.futures:id/adImageView",
    "返回":"com.hexin.android.futures:id/title_bar_left_container",
}

MAX_COUNT = 1000   # 最大可显示持仓数目，调试用

class THSTraderfuture:
    def __init__(self, serial="emulator-5554") -> None:    
        self.d =  u2.connect_usb(serial)
        self.reader = easyocr.Reader(['ch_sim','en'])
        # 行情是否OCR正确
        self.indhq=0
        self.ma155=0
        self.ma1510=0
        self.ma1520=0
        self.ma1560=0
        self.fiveseq={"-2": 0,"-1": 0,"0": 0}
        self.ykseq={"-2": 0,"-1": 1,"0": 0}
        self.cp=0
        self.checkseq="unknow"
        # 是否持仓
        self.balance=0
        # 是否交易时间
        self.istrade=0
        self.mode=1
        self.bid=""

    def update_queue(self, new_value):
        self.fiveseq["-2"] = self.fiveseq["-1"]
        self.fiveseq["-1"] = self.fiveseq["0"]
        self.fiveseq["0"] = new_value
        
    def update_queueyk(self, new_value):
        self.ykseq["-2"] = self.ykseq["-1"]
        self.ykseq["-1"] = self.ykseq["0"]
        self.ykseq["0"] = new_value
        
    def check_sequence(self):
        differences = [self.fiveseq[str(i)] - self.fiveseq[str(i-1)] for i in range(0, -2, -1)]
        if all(d > 0.00025*self.fiveseq["0"] for d in differences):
            self.checkseq="Inc"
        elif all(d < -0.00025*self.fiveseq["0"] for d in differences):
            self.checkseq="Dec"
        else:
            self.checkseq="unknow"
    
    def get_balance(self):
        """ 获取资产 """
        # 点击交易
        self.d.xpath('//*[@content-desc="交易"]/android.widget.LinearLayout[1]/android.widget.ImageView[1]').click()
        time.sleep(2)
        if self.mode==1:
            #点击实盘
            self.d.xpath('//*[@resource-id="com.hexin.android.futures:id/shipan_btn"]').click()
        elif self.mode==0:
            #点击模拟盘
            self.d.xpath('//*[@resource-id="com.hexin.android.futures:id/moni_btn"]').click()
        # 获取
        zongzijin=float(self.d(resourceId="com.hexin.android.futures:id/rightNumberTv").get_text().replace(",", ""))
        keyong=float(self.d(resourceId="com.hexin.android.futures:id/availablePriceNumberTv").get_text().replace(",", ""))
        yingkui=float(self.d(resourceId="com.hexin.android.futures:id/everyProfitLossNumberTv").get_text().replace(",", ""))
        if zongzijin == keyong:
            self.balance=0
        elif zongzijin>keyong:
            self.balance=1
        return {
            "总资产": zongzijin,
            "可用资金": keyong,
            "逐笔盈亏": yingkui,
        }
    
    def EmailMeg(self,meg):
        # 邮件服务器地址和端口号
        smtp_server = 'smtp.163.com'
        smtp_port = 465
        # 发件人邮箱地址和密码
        sender_email = 'XX@163.com'  # 这里替换为您自己的发件人邮箱地址
        sender_password = 'XX'  # 这里是你的授权码？ 非邮箱登录密码
        # 收件人邮箱地址
        recipient_email = 'XX@163.com'
        
        # 创建一封邮件，文本内容为 "Hello, World!"
        message = MIMEMultipart()
        content=meg
        message['From'] = Header('发件人昵称 <{}>'.format(sender_email), 'utf-8')  # 设置发件人昵称
        message['To'] = Header('收件人昵称 <{}>'.format(recipient_email), 'utf-8')  # 设置收件人昵称
        message['Subject'] = Header(meg, 'utf-8')  # 设置邮件主题
        message.attach(MIMEText(content, 'html', 'utf-8'))
        # 构造附件2，传送当前目录下的文件
        attpath='my_log.log'
        att2 = MIMEText(open(attpath, 'rb').read(), 'base64', 'utf-8')
        att2["Content-Type"] = 'application/octet-stream'
        att2["Content-Disposition"] = 'attachment; filename="my_log.log"'
        message.attach(att2)
        try:
            # 连接邮件服务器并登录
            smtp_connection = smtplib.SMTP_SSL(smtp_server, smtp_port)
            smtp_connection.login(sender_email, sender_password)
            # 发送邮件
            smtp_connection.sendmail(sender_email, recipient_email, message.as_string())
            # 关闭连接
            smtp_connection.quit()
            print("邮件发送成功！")
        except Exception as e:
            print("邮件发送失败：", e)

  
    def maiduo(self, stock_no, amount, price):
        return self.__imeaction(stock_no, amount, price, "maiduo")
        
    def maikong(self, stock_no, amount, price):
        return self.__imeaction(stock_no, amount, price, "maikong")
    
    def pingcang(self, stock_no, amount, price):
        return self.__imeaction(stock_no, amount, price, "pingcang")

    def __imeaction(self, stock_no, amount, price, open_tag):
        """ 买入或者卖出通用 """
        stock_no = str(stock_no)
        price = str(price)
        success = False
        msg = ""
        stock_name = ""
        while True:
            # self.back_to_moni_page()
            # 点击下单
            self.d(resourceId="com.hexin.android.futures:id/tradeOrderRl").click()
            time.sleep(1)
            # 点击搜索
            self.d(resourceId="com.hexin.android.futures:id/search_btn").click()
            time.sleep(1)
            # 输入搜索框
            self.d(resourceId="com.hexin.android.futures:id/stock_search_editview").click()
            time.sleep(1)
            # 输入期货代码，点击第一个选项
            self.__input_stock_no(stock_no)
            # 暂且买一手，后续优化
            # self.__input_stock_price(price)
            # self.__input_stock_buy_count(amount)
            time.sleep(1)
            if open_tag=="maiduo":
                # # 加1手
                if self.mode==1:
                    self.d(resourceId="com.hexin.android.futures:id/iv_quantity_add").click()
                    time.sleep(1)
                elif self.mode==0 and amount=='zhongcang':
                    # 1/2仓位
                    self.d(resourceId="com.hexin.android.futures:id/stock_quantity").click()  
                    time.sleep(1)
                    self.d(resourceId="com.hexin.android.futures:id/cangweiTextView3").click()
                    time.sleep(1)
                elif self.mode==0 and amount=='qingcang':
                    # 轻仓1手
                    self.d(resourceId="com.hexin.android.futures:id/stock_quantity").click()  
                    time.sleep(1)
                    self.d(resourceId="com.hexin.android.futures:id/iv_quantity_add").click()
                    time.sleep(1)
                #点击买多
                self.d(resourceId="com.hexin.android.futures:id/rl_maiduo").click()
                time.sleep(1)
                # 点击确认
                self.d(resourceId="com.hexin.android.futures:id/positiveButton").click()   
                time.sleep(30)
                # 点击返回持仓页面
                self.__util_close_otherpingcang()
                time.sleep(1)
                break
                # # 点击持仓
                # self.d(resourceId="com.hexin.android.futures:id/chicang_tv").click()   
                # time.sleep(1)   
            if open_tag=="maikong":
                # # 卖空
                if self.mode==1:
                    self.d(resourceId="com.hexin.android.futures:id/iv_quantity_add").click()
                    time.sleep(1)
                elif self.mode==0 and amount=='zhongcang':
                    # 1/2仓位
                    self.d(resourceId="com.hexin.android.futures:id/stock_quantity").click()  
                    time.sleep(1)
                    self.d(resourceId="com.hexin.android.futures:id/cangweiTextView3").click()
                    time.sleep(1)
                elif self.mode==0 and amount=='qingcang':
                    # 轻仓1手
                    self.d(resourceId="com.hexin.android.futures:id/iv_quantity_add").click()
                    time.sleep(1)
                # 点击卖空
                self.d(resourceId="com.hexin.android.futures:id/rl_maikong").click()
                time.sleep(1)
                # 点击确认
                self.d(resourceId="com.hexin.android.futures:id/positiveButton").click()
                time.sleep(30)
                # 点击返回持仓页面
                self.__util_close_otherpingcang()
                time.sleep(1)
                break
            if open_tag=="pingcang":
                # # 1手 
                if self.mode==1:
                    self.d(resourceId="com.hexin.android.futures:id/iv_quantity_add").click()
                    time.sleep(1)
                    # 点击平仓
                    self.d(resourceId="com.hexin.android.futures:id/rl_pingcang").click()
                    time.sleep(1)
                    self.d(resourceId="com.hexin.android.futures:id/positiveButton").click()
                    time.sleep(30)
                elif self.mode==0:
                    # 全部仓位
                    os.system("adb shell input tap 300 800")
                    time.sleep(1)
                    # 点击平仓
                    self.d(resourceId="com.hexin.android.futures:id/rl_pingcang").click()
                    time.sleep(1)
                    # 点击确认
                    self.d(resourceId="com.hexin.android.futures:id/positiveButton").click()
                    time.sleep(30)
                # 点击返回持仓页面
                self.__util_close_otherpingcang()
                time.sleep(1)
                break                
    def hangqing(self, stock_no):
            """ 买入或者卖出通用 """
            stock_no = str(stock_no)
            msg = ""
            stock_name = ""
            # self.back_to_moni_page()
            # 点击行情
            self.d.xpath('//*[@content-desc="行情"]/android.widget.LinearLayout[1]/android.widget.ImageView[1]').click()
            time.sleep(1)
            # 点击搜索
            self.d.xpath('//*[@resource-id="com.hexin.android.futures:id/btnSearch"]').click()
            time.sleep(1)
            # 输入搜索框
            self.d.xpath('//*[@resource-id="com.hexin.android.futures:id/stock_search_editview"]').click()
            time.sleep(1)
            # 输入期货代码，点击第一个选项
            self.__input_stock_no(stock_no)
            time.sleep(10)
            # 点击5分钟线,15分钟线最后一个数字是5
            self.d.xpath('//*[@resource-id="com.hexin.android.futures:id/period_tablayout"]/android.widget.HorizontalScrollView[1]/android.widget.LinearLayout[1]/android.widget.FrameLayout[4]').click()
            time.sleep(10)
            #获取行情参数
            self.indhq=1
            indwronghq=0
            while self.indhq==1:
                indwronghq=indwronghq+1
                if indwronghq>=10:
                    break
                try:
                    self.indhq=0
                    os.system("adb shell screencap -p /sdcard/screen.png")
                    time.sleep(1)
                    os.system("adb pull /sdcard/screen.png") 
                    time.sleep(1)
                    self.__ocr_get_full_text()                    
                except:
                    self.indhq=1
            #点击返回并取消
            self.__util_close_other()
            self.__util_close_quxiao()
            # 点击交易
            self.d.xpath('//*[@content-desc="交易"]/android.widget.LinearLayout[1]/android.widget.ImageView[1]').click()
       

    def back_to_moni_page(self):
        self.d.app_stop("com.hexin.android.futures")
        self.d.app_start("com.hexin.android.futures")
        time.sleep(20)
        if self.__util_check_app_page(PAGE_INDICATOR["首页广告"]) or self.__util_check_app_page(PAGE_INDICATOR["AppRank"]):
            self.d(resourceId="com.hexin.android.futures:id/adImageView").click()
            self.__util_close_other()            
            time.sleep(5)
        # 点击交易
        self.d.xpath('//*[@content-desc="交易"]/android.widget.LinearLayout[1]/android.widget.ImageView[1]').click()
        time.sleep(2)
        if self.mode==1:
            # 点击实盘
            try:
                self.d.xpath('//*[@resource-id="com.hexin.android.futures:id/shipan_btn"]').click()
                time.sleep(3)
            except:
                print('already shipan')
            # 点击 进入账号
            os.system("adb shell input tap 300 150") 
            time.sleep(1)
            #点击交易密码
            self.d.xpath('//*[@resource-id="com.hexin.android.futures:id/weituo_edit_trade_password"]').click()
            time.sleep(1)
            mima=str('XX')#更换为自己的密码
            self.__util_input_text(mima)
            time.sleep(1)
            # #点击同意协议
            # self.d.xpath('//*[@resource-id="com.hexin.android.futures:id/protocol_ll"]/android.widget.CheckBox[1]').click()
            #点击登录
            self.d.xpath('//*[@resource-id="com.hexin.android.futures:id/weituo_btn_login"]').click()
            time.sleep(1)
            #确认交割单
            try:
                self.d.xpath('//*[@resource-id="com.hexin.android.futures:id/check_bill_ok"]').click()
            except:pass
            time.sleep(1)   
        elif self.mode==0:
            # 点击模拟
            self.d.xpath('//*[@resource-id="com.hexin.android.futures:id/moni_btn"]').click()
            time.sleep(5)
            # # 点击模拟交易进入
            # self.d.xpath('//*[@resource-id="com.hexin.android.futures:id/moni_future_login_view"]').click()
            # 点击模拟比赛
            os.system("adb shell input tap 300 300")
            time.sleep(10)

        
 
    def __input_stock_no(self, stock_no):
        """ 输入股票ID """
        # self.__util_close_other()
        self.d(resourceId="com.hexin.android.futures:id/stock_search_editview").click()
        time.sleep(1)
        self.__util_input_text(stock_no)
        time.sleep(1)    
        self.d.xpath('//*[@resource-id="com.hexin.android.futures:id/stock_search_result_listview"]/android.widget.RelativeLayout[1]').click()
        time.sleep(1) 

    def __input_stock_price(self, price):
        """ 输入股票价格 """
        self.__util_close_other()
        self.d(resourceId="com.hexin.plat.android:id/stockprice").click()
        time.sleep(2)
        self.__util_input_text(price)


    def __util_close_other(self):
        time.sleep(1)
        try:
            self.d.xpath('//*[@resource-id="com.hexin.android.futures:id/left_btn"]').click()
            
        except: pass
    
    def __util_close_otherpingcang(self):
        time.sleep(1)
        try:
            self.d.xpath('//*[@resource-id="com.hexin.android.futures:id/title_bar_left"]').click()
        except: pass

        
    def __util_close_quxiao(self):
        time.sleep(1)
        try:
            self.d.xpath('//*[@resource-id="com.hexin.android.futures:id/stock_search_cancel_textview"]').click()
        except: pass
        
    def __util_input_text(self, text):
        """ 输入工具，uiautomator2的clear_text和send_keys速度好像有点儿慢，所以用了这种方法 """
        self.d.shell("input keyevent 123")
        for _ in range(20):
            self.d.shell("input keyevent 67")
        self.d.shell(f"input text {text}")

    def __util_check_app_page(self, indicator):
        """ 工具，检查页面是否包含某特征 """
        hierachy = self.d.dump_hierarchy()
        if indicator in hierachy:
            return True
        return False
    def buguoye(self):
        indpingcang=0
        now = datetime.now().time()
        target_time1 = datetime.strptime("14:50", "%H:%M").time()
        target_time2 = datetime.strptime("21:00", "%H:%M").time()
        target_time3 = datetime.strptime("22:50", "%H:%M").time()
        target_time34 = datetime.strptime("23:05", "%H:%M").time()
        target_time4 = datetime.strptime("02:20", "%H:%M").time()
        target_time41 = datetime.strptime("02:40", "%H:%M").time()
        if now >= target_time1 and now <= target_time2:
            indpingcang=1
        if now >= target_time3 and now <= target_time34:
            indpingcang=1
        if now >= target_time4 and now <= target_time41:
            indpingcang=1
        return indpingcang 
    def tradejudge(self,bid,amount):
        mincp5=self.cp - self.ma155
        min510=self.ma155 - self.ma1510
        min1020=self.ma1510 - self.ma1520
        add='cp is '+str(self.cp)+',MA5 is '+str(self.ma155)+',MA10 is '+str(self.ma1510)+',MA20 is '+str(self.ma1520)
        indbgy=self.buguoye()
        self.check_sequence()
        # tragger is 1 not
        #if indbgy==0 and mincp5>=0.1 and min510>=0.2 and min1020>=0.2:
        if indbgy==0 and self.checkseq=="Inc":
            self.maiduo(bid, amount, 1)
        elif indbgy==0 and self.checkseq=="Dec":
            self.maikong(bid, amount, 1)
        return 
        

    def __ocr_get_full_text(self):
        # os.system("adb shell rm /sdcard/screen.png")
        # time.sleep(1)
        # os.system("adb kill-server")
        # os.system("adb start-server")
        # reader = easyocr.Reader(['ch_sim'])
        result = self.reader.readtext("screen.png")
        time.sleep(2)
        text = ""
        for line in result:
            text += line[1]
        # # current price
        # try:
        #     x=result[3]
        #     self.cp=round(float(x[1]),2)
        # except:
        #     print("cp wrong")
        #     self.indhq=1
        # MA5
        match = re.search(r'5分MA5:(\d+\.\d+)', text)
        if match:
            result = match.group(1)
            self.ma155=float(result)
            self.update_queue(self.ma155)
        else:
            print("ma5 No match found.")
            self.indhq=1
        # # MA10
        # match = re.search(r'10:(\d+\.\d+)', text)
        # if match:
        #     result = match.group(1)
        #     self.ma1510=float(result)
        # else:
        #     print("ma10 No match found.")
        #     self.indhq=1
        # MA20
        # match = re.search(r'20:(\d+\.\d+)', text)
        # match2 = re.search(r'20;(\d+\.\d+)', text) 
        # if match:
        #     result = match.group(1)
        #     self.ma1520=float(result)   
        # elif match2:
        #     result = match2.group(1)
        #     self.ma1520=float(result)
        # else:
        #     print("ma20  No match found.")
        #     self.indhq=1
        # MA60
        # match = re.search(r'60:(\d+\.\d+)', text)
        # match2 = re.search(r'60;(\d+\.\d+)', text) 
        # if match:
        #     result = match.group(1)
        #     self.ma1560=float(result)   
        # elif match2:
        #     result = match2.group(1)
        #     self.ma1560=float(result)
        # else:
        #     print("ma60  No match found.")
        #     self.indhq=1