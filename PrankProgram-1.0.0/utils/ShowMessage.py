import pyautogui
from time import sleep 
from random import randint
from threading import Thread  
from tkinter import Tk, Label 


# 警告弹窗
def warningMessage(x, y):
    root = Tk()  
    root.title("错误警告")  
    root.geometry(f"400x300+{x}+{y}")  
    root.resizable(False, False)  
    root.attributes("-topmost", True)  
    label = Label(root, text="系统正在遭受网络攻击", padx=20, pady=20, font=("Helvetica", 20), fg="red") 
    label.pack(expand=True)  
    root.protocol("WM_DELETE_WINDOW", lambda: None)  
    root.after(5000, root.destroy)  
    root.mainloop()  


# 读取数据并将其转换为二维数据
def readData(path):
    try:
        data = [] 
        with open(path, 'r') as file: 
            for line in file:
                coords = line.strip().split() 
                if len(coords) == 2: data.append([int(coords[0]), int(coords[1])])
        return data 
    except: pass


# 显示弹窗
def showMessage(path):
    try:
        positionsData = readData(path) 
        screenWidth, screenHeight = pyautogui.size()

        for coords in positionsData:
            sleep(0.05) 
            Thread(target=warningMessage, args=(coords[0], coords[1])).start()  

        while True:  
            sleep(0.05)  
            Thread(target=warningMessage, args=((randint(0, screenWidth), randint(0, screenHeight),))).start()  
    except: pass
