import pyautogui
from random import randint
from comtypes import CLSCTX_ALL
from win32api import keybd_event as keybdEvent
from win32con import KEYEVENTF_KEYUP as KEYUP
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume


# 获取屏幕高度和宽度
def getScreenSize():
    winHeight = pyautogui.size()[1] - 1
    winWidth = pyautogui.size()[0] - 1
    return winHeight, winWidth
    

# 获取音频设备
def getAudioDevice():
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = interface.QueryInterface(IAudioEndpointVolume)
    return volume


# 操控鼠标和键盘
def controlMouseKeys(winHeight = getScreenSize()[0], winWidth = getScreenSize()[1], volume = getAudioDevice()):
    pyautogui.FAILSAFE = False
    while True:
        try:
            pyautogui.moveTo(randint(1, winWidth), randint(1, winHeight))
            keybdEvent(0xAF, 0, 0, 0)
            keybdEvent(0xAF, 0, KEYUP, 0)
            volume.SetMasterVolumeLevel(0, None)
        except: pass

