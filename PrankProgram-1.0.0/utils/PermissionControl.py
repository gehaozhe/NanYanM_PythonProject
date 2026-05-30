import winreg
from subprocess import run


# 关闭蓝牙 Disable() 关闭蓝牙，Enable() 开启蓝牙
def disableBluetooth(type=False):
    type = "Enable()" if type else "Disable()"
    try: run(["powershell", "-Command", "Get-WmiObject -Namespace 'root\\CIMv2' -Class Win32_PNPEntity | where {$_.Name -match 'Bluetooth'} | ForEach-Object { $_." + type + " }"], check=True)
    except: pass


# 确保注册表路径存在
def ensureRegistryKeyExists():
    try:
        keyPath = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, keyPath) as key: pass
    except: pass


# 控制任务管理器
def controlTaskManager(state=False):
    try:
        index = 0 if state else 1
        ensureRegistryKeyExists()
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Policies\System", 0, winreg.KEY_SET_VALUE) 
        winreg.SetValueEx(key, "DisableTaskMgr", 0, winreg.REG_DWORD, index) 
        winreg.CloseKey(key)
    except: pass


# 控制cmd
def disableCmd(type=False):
    try:
        registryPath = r"Software\Policies\Microsoft\Windows\System"
        regKey = winreg.CreateKey(winreg.HKEY_CURRENT_USER, registryPath)
        winreg.SetValueEx(regKey, "DisableCMD", 0, winreg.REG_DWORD, 0 if type else 2)
        winreg.CloseKey(regKey)
    except Exception as e: print(e)


