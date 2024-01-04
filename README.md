# THStraderfuture

#### 期货自动化实盘+模拟盘全栈解决方案

#### 知乎和雪球账号：玄野量化；微信：xylhfree

#### 介绍
项目借鉴了thstrader项目，核心原理是程序化模拟点击安卓模拟器中的app交易软件进行自动化交易。项目特点：
1.  项目刚开始在本地开发调试，后移植到了云桌面，实现了7*24小时无人照看托管交易。已经历一个月不间断运行无bug；
2.  实时数据通过点击界面ocr识别获取，纯自己造轮子，无需担心数据源可控问题；
3.  同时具备实盘交易版本和模拟盘交易版本；
4.  交易一次时间包括ocr行情数据识别到下单成功平均70s（取决于运行环境，高配cpu会更快）；
5.  交易信息会自动生成log，并实时发送到自己邮箱中，通过手机安装邮箱客户端，可以实时监控自己的交易情况；
6.  有的交易客户端不容许在云端运行，防止未来app政策变化，该项目逻辑可以支持备用手机usb连接电脑来进行模拟点击的保底。


#### 安装教程

1.  下载并安装python运行环境（如anaconda），选择python3.9运行环境，安装requirements.txt中对应的package版本；
2.  下载并安装雷电模拟器。其中自带ADB并添加adb系统变量（将adb所在目录增加到“我的电脑-属性-高级系统设置-环境变量-系统变量-Path”中）；
3.  运行过程中easyocr会自动下载；国内自动下载不动时需要手动下载并复制到系统目录easyocr/model下面；
4.  刚开始需要初始化“python -m uiautomator2 init”（已放在主文件中，实际运行可以注释掉）；
5.  先在模拟器中自己通过账号密码登录一次，然后再开始跑程序。
6.  购买云桌面（买前和卖家问清楚能运行安装模拟器的版本），然后部署在云上。

#### 使用说明

1.  主程序可以编辑策略，主要操作逻辑在THSTraderfuture中；
2.  找到THSTraderfuture中EmailMeg部分，修改相关发送邮件部分，改为自己的邮箱信息；
3.  THSTraderfuture中back_to_moni_page部分，修改实盘密码。


