import importlib

import subprocess
# 定义需要检查的库列表
libraries = [
    'io',
    'time',
    'pyautogui',
    'subprocess',
    'platform',
    'cv2',
    'logging',
    'flask',
    'PIL',
    'tkinter',
    'threading',
    'queue',
    'psutil',
    'os'
]

# 遍历库列表进行检查和安装
for library in libraries:
    try:
        # 尝试导入库
        if library == 'cv2':
            importlib.import_module('cv2')
        elif library == 'PIL':
            importlib.import_module('PIL')
        else:
            importlib.import_module(library)
        print(f"{library} 已经安装。")
    except ImportError:
        print(f"{library} 未安装，正在尝试安装...")
        try:
            # 使用 subprocess 调用 pip 进行安装
            if library == 'cv2':
                subprocess.check_call(['pip', 'install', '-i','https://mirrors.aliyun.com/pypi/simple/','opencv-python'])

            elif library == 'PIL':
                subprocess.check_call(['pip', 'install', '-i','https://mirrors.aliyun.com/pypi/simple/','Pillow'])

            else:
                subprocess.check_call(['pip', 'install', '-i','https://mirrors.aliyun.com/pypi/simple/',library])
            print(f"{library} 安装成功。")
        except subprocess.CalledProcessError:
            print(f"{library} 安装失败，请手动安装。")

import psutil
import socket
import subprocess
import os
import platform


def check_interface_ipv6_support():
    """
    检查网络接口是否支持 IPv6
    """
    net_if_addrs = psutil.net_if_addrs()
    for interface, addrs in net_if_addrs.items():
        for addr in addrs:
            if addr.family.name.startswith('AF_INET6'):
                return True
    return False


def check_ipv6_connectivity():
    """
    尝试建立 IPv6 连接来检测 IPv6 可用性
    """
    try:
        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(('2001:4860:4860::8888', 53))
        sock.close()
        return True
    except (socket.gaierror, socket.error):
        return False


def enable_ipv6_windows():
    try:
        # 启用 IPv6
        subprocess.run(['netsh', 'interface', 'ipv6', 'set', 'interface', 'all', 'advertise=enabled'], check=True)
        subprocess.run(['netsh', 'interface', 'ipv6', 'set', 'interface', 'all', 'forwarding=enabled'], check=True)
        print("已尝试在 Windows 系统上启用 IPv6，请稍等片刻...")
        return True
    except subprocess.CalledProcessError as e:
        print(f"在 Windows 系统上启用 IPv6 时出现错误: {e}")
        return False


def enable_ipv6_linux():
    try:
        # 备份原始配置文件
        subprocess.run(['cp', '/etc/sysctl.conf', '/etc/sysctl.conf.bak'], check=True)
        with open('/etc/sysctl.conf', 'a') as f:
            f.write('\nnet.ipv6.conf.all.disable_ipv6 = 0\n')
            f.write('net.ipv6.conf.default.disable_ipv6 = 0\n')
        subprocess.run(['sysctl', '-p'], check=True)
        print("已尝试在 Linux 系统上启用 IPv6，请稍等片刻...")
        return True
    except subprocess.CalledProcessError as e:
        print(f"在 Linux 系统上启用 IPv6 时出现错误: {e}")
        return False


# 首次检测
interface_support = check_interface_ipv6_support()
connectivity = check_ipv6_connectivity()

if interface_support and connectivity:
    print("电脑支持并可以正常使用 IPv6。")
elif interface_support and not connectivity:
    print("电脑网络接口支持 IPv6，但可能由于网络环境或防火墙等原因无法正常使用 IPv6。")
elif not interface_support and connectivity:
    print("出现异常情况，检测到可建立 IPv6 连接，但未发现支持 IPv6 的网络接口。")
else:
    print("电脑可能未开启 IPv6 或不支持 IPv6，尝试开启 IPv6...")
    system = platform.system()
    enabled = False
    if system == 'Windows':
        enabled = enable_ipv6_windows()
    elif system == 'Linux':
        enabled = enable_ipv6_linux()
    else:
        print(f"不支持的操作系统: {system}，无法自动开启 IPv6。")

    if enabled:
        # 等待一段时间让配置生效
        import time
        time.sleep(10)
        # 再次检测
        new_interface_support = check_interface_ipv6_support()
        new_connectivity = check_ipv6_connectivity()
        if new_interface_support and new_connectivity:
            print("成功开启并可以正常使用 IPv6。")
        else:
            print("尝试开启 IPv6 后仍无法正常使用，请手动检查网络设置。")
print('环境检查完毕，远程控制脚本开始运行')
import io
import time
import pyautogui
import subprocess
import platform
import cv2
import logging
from flask import Flask, Response, request, jsonify, render_template_string, send_from_directory
from PIL import ImageGrab
import tkinter as tk
from threading import Thread
from queue import Queue
import psutil
import os

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
# 存储摄像头状态的队列
摄像头状态队列 = Queue()

# 创建上传文件的目录
上传文件夹 = '上传文件夹'
os.makedirs(上传文件夹, exist_ok=True)
app.config['上传文件夹'] = 上传文件夹

# 初始帧率设置
屏幕帧率 = 30
摄像头帧率 = 30
# 手机模式标志
是否为手机模式 = False
# 隐藏客户端图形界面标志
是否隐藏客户端界面 = False
# 全局 tkinter 窗口对象
根窗口 = None

class 摄像头处理器:
    def __init__(self):
        self.摄像头 = None
        状态 = self._初始化摄像头()
        # 将摄像头状态放入队列
        摄像头状态队列.put(状态)
        logger.info(状态)

    def _初始化摄像头(self):
        try:
            # 尝试打开摄像头
            self.摄像头 = cv2.VideoCapture(0)
            self.摄像头.set(cv2.CAP_PROP_FPS, 摄像头帧率)
            return "摄像头已打开" if self.摄像头.isOpened() else "摄像头未打开"
        except Exception as e:
            return f"摄像头初始化出错: {e}"

    def 生成摄像头帧(self):
        if not self.摄像头:
            return
        try:
            while True:
                成功, 帧 = self.摄像头.read()
                if 成功:
                    结果, 缓冲区 = cv2.imencode('.jpg', 帧)
                    if 结果:
                        # 修改这里，将 '帧' 替换为 'frame'
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + 缓冲区.tobytes() + b'\r\n')
                    else:
                        logger.warning("无法编码摄像头帧")
                else:
                    logger.warning("无法读取摄像头帧")
                    break
        except Exception as e:
            logger.error(f"生成摄像头视频流出错: {e}")
        finally:
            self._释放摄像头()

    def _释放摄像头(self):
        if self.摄像头:
            # 释放摄像头资源
            self.摄像头.release()
            logger.info("摄像头已释放")

摄像头处理器 = 摄像头处理器()

def 生成屏幕帧():
    try:
        while True:
            图像 = ImageGrab.grab()
            图像字节数组 = io.BytesIO()
            图像.save(图像字节数组, format='PNG')

            yield (b'--frame\r\n'
                   b'Content-Type: image/png\r\n\r\n' + 图像字节数组.getvalue() + b'\r\n')
            time.sleep(1 / 屏幕帧率)
    except Exception as e:
        logger.error(f"生成屏幕截图流出错: {e}")

@app.route('/视频流')
def 视频流():
    return Response(生成屏幕帧(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/摄像头流')
def 摄像头流():
    return Response(摄像头处理器.生成摄像头帧(), mimetype='multipart/x-mixed-replace; boundary=frame')



def 验证请求(data, 必需参数):
    缺失参数 = [参数 for 参数 in 必需参数 if 参数 not in data]
    if 缺失参数:
        错误信息 = f"请求缺少必要参数: {', '.join(缺失参数)}"
        logger.error(错误信息)
        return jsonify({"错误": 错误信息}), 400
    return None

@app.route('/鼠标点击', methods=['POST'])
def 鼠标点击():
    数据 = request.get_json()
    必需参数 = ['x', 'y', '缩放比例_x', '缩放比例_y', '点击类型']
    验证结果 = 验证请求(数据, 必需参数)
    if 验证结果:
        return 验证结果

    实际_x = int(数据['x'] * 数据['缩放比例_x'])
    实际_y = int(数据['y'] * 数据['缩放比例_y'])
    点击类型 = 数据['点击类型']
    点击函数映射 = {
        '左键': pyautogui.click,
        '右键': pyautogui.rightClick,
        '双击': pyautogui.doubleClick,
        '拖动': pyautogui.dragTo
    }
    点击函数 = 点击函数映射.get(点击类型)
    if 点击类型 == '拖动':
        起始_x = int(数据.get('起始_x', 0) * 数据['缩放比例_x'])
        起始_y = int(数据.get('起始_y', 0) * 数据['缩放比例_y'])
        pyautogui.moveTo(起始_x, 起始_y)
        pyautogui.mouseDown()
        点击函数(实际_x, 实际_y)
        pyautogui.mouseUp()
    elif 点击函数:
        点击函数(实际_x, 实际_y)
    else:
        错误信息 = f"无效的点击类型: {点击类型}"
        logger.error(错误信息)
        return jsonify({"错误": 错误信息}), 400
    logger.info(f"鼠标 {点击类型} 点击事件: 坐标 ({实际_x}, {实际_y})")
    return 'OK'

@app.route('/键盘按键', methods=['POST'])
def 键盘按键():
    数据 = request.get_json()
    必需参数 = ['按键']
    验证结果 = 验证请求(数据, 必需参数)
    if 验证结果:
        return 验证结果
    # 模拟按下键盘按键
    pyautogui.press(数据['按键'])
    logger.info(f"键盘输入事件: 按键 {数据['按键']}")
    return 'OK'

@app.route('/执行命令', methods=['POST'])
def 执行命令():
    数据 = request.get_json()
    必需参数 = ['命令']
    验证结果 = 验证请求(数据, 必需参数)
    if 验证结果:
        return 验证结果
    try:
        # 执行命令
        结果 = subprocess.run(数据['命令'], shell=True, capture_output=True, text=True, check=True)
        输出 = 结果.stdout if 结果.stdout else 结果.stderr
        logger.info(f"执行命令: {数据['命令']}, 输出: {输出}")
        return jsonify({'输出': 输出})
    except subprocess.CalledProcessError as e:
        错误信息 = f"执行命令出错: {e.stderr}"
        logger.error(错误信息)
        return jsonify({"错误": 错误信息}), 500

@app.route('/获取电脑信息')
def 获取电脑信息():
    # 获取电脑的各种信息
    return jsonify({
        '操作系统': platform.system(),
        '版本号': platform.release(),
        '详细版本': platform.version(),
        '机器类型': platform.machine(),
        '处理器': platform.processor(),
        'CPU使用率': psutil.cpu_percent(interval=1),
        '内存使用率': psutil.virtual_memory().percent
    })

@app.route('/关机', methods=['POST'])
def 关机():
    命令 = "shutdown /s /t 0" if platform.system() == "Windows" else "sudo shutdown -h now"
    try:
        # 发送关机命令
        subprocess.run(命令, shell=True, check=True)
        logger.info("关机命令已发送")
        return jsonify({"消息": "关机命令已发送"})
    except subprocess.CalledProcessError as e:
        错误信息 = f"关机命令执行出错: {e.stderr}"
        logger.error(错误信息)
        return jsonify({"错误": 错误信息}), 500

@app.route('/重启', methods=['POST'])
def 重启():
    命令 = "shutdown /r /t 0" if platform.system() == "Windows" else "sudo shutdown -r now"
    try:
        # 发送重启命令
        subprocess.run(命令, shell=True, check=True)
        logger.info("重启命令已发送")
        return jsonify({"消息": "重启命令已发送"})
    except subprocess.CalledProcessError as e:
        错误信息 = f"重启命令执行出错: {e.stderr}"
        logger.error(错误信息)
        return jsonify({"错误": 错误信息}), 500

@app.route('/音量控制', methods=['POST'])
def 音量控制():
    数据 = request.get_json()
    必需参数 = ['操作']
    验证结果 = 验证请求(数据, 必需参数)
    if 验证结果:
        return 验证结果
    操作 = 数据['操作']
    if 操作 == '增大':
        # 模拟按下音量增大键
        pyautogui.press('volumeup')
    elif 操作 == '减小':
        # 模拟按下音量减小键
        pyautogui.press('volumedown')
    elif 操作 == '静音':
        # 模拟按下静音键
        pyautogui.press('volumemute')
    else:
        错误信息 = f"无效的音量控制动作: {操作}"
        logger.error(错误信息)
        return jsonify({"错误": 错误信息}), 400
    logger.info(f"音量控制动作: {操作}")
    return 'OK'

@app.route('/上传文件', methods=['POST'])
def 上传文件():
    if '文件' not in request.files:
        错误信息 = "文件上传请求缺少文件"
        logger.error(错误信息)
        return jsonify({"错误": 错误信息}), 400
    文件 = request.files['文件']
    if 文件.filename == '':
        错误信息 = "未选择文件"
        logger.error(错误信息)
        return jsonify({"错误": 错误信息}), 400
    if 文件:
        文件名 = os.path.join(app.config['上传文件夹'], 文件.filename)
        文件.save(文件名)
        logger.info(f"文件 {文件.filename} 上传成功")
        return jsonify({"消息": "文件上传成功"})

@app.route('/设置帧率', methods=['POST'])
def 设置帧率():
    global 屏幕帧率, 摄像头帧率
    数据 = request.get_json()
    if '屏幕帧率' in 数据:
        try:
            新屏幕帧率 = int(数据['屏幕帧率'])
            if 新屏幕帧率 > 0:
                屏幕帧率 = 新屏幕帧率
            else:
                return jsonify({"错误": "屏幕帧率必须为正整数"}), 400
        except ValueError:
            return jsonify({"错误": "屏幕帧率必须为正整数"}), 400
    if '摄像头帧率' in 数据:
        try:
            新摄像头帧率 = int(数据['摄像头帧率'])
            if 新摄像头帧率 > 0:
                摄像头帧率 = 新摄像头帧率
                if 摄像头处理器.摄像头:
                    摄像头处理器.摄像头.set(cv2.CAP_PROP_FPS, 新摄像头帧率)
            else:
                return jsonify({"错误": "摄像头帧率必须为正整数"}), 400
        except ValueError:
            return jsonify({"错误": "摄像头帧率必须为正整数"}), 400
    return jsonify({"消息": "帧率设置成功"})

@app.route('/设置手机模式', methods=['POST'])
def 设置手机模式():
    global 是否为手机模式, 屏幕帧率, 摄像头帧率
    数据 = request.get_json()
    if '是否为手机模式' in 数据:
        是否为手机模式 = 数据['是否为手机模式']
        if 是否为手机模式:
            # 手机模式下降低帧率
            屏幕帧率 = 5
            摄像头帧率 = 15
            if 摄像头处理器.摄像头:
                摄像头处理器.摄像头.set(cv2.CAP_PROP_FPS, 摄像头帧率)
        else:
            # 恢复默认帧率
            屏幕帧率 = 10
            摄像头帧率 = 30
            if 摄像头处理器.摄像头:
                摄像头处理器.摄像头.set(cv2.CAP_PROP_FPS, 摄像头帧率)
        return jsonify({"消息": f"手机模式已设置为 {是否为手机模式}"})
    return jsonify({"错误": "缺少必要参数: 是否为手机模式"}), 400

@app.route('/设置隐藏客户端界面', methods=['POST'])
def 设置隐藏客户端界面():
    global 是否隐藏客户端界面, 根窗口
    数据 = request.get_json()
    if '是否隐藏客户端界面' in 数据:
        是否隐藏客户端界面 = 数据['是否隐藏客户端界面']
        if 是否隐藏客户端界面:
            if 根窗口:
                # 隐藏窗口
                根窗口.withdraw()
        else:
            if 根窗口:
                # 显示窗口
                根窗口.deiconify()
        return jsonify({"消息": f"客户端图形界面已设置为 {'隐藏' if 是否隐藏客户端界面 else '显示'}"})
    return jsonify({"错误": "缺少必要参数: 是否隐藏客户端界面"}), 400

def 生成HTML模板(标题, 内容, 返回按钮=True):
    手机模式CSS = """
        @media (max-width: 768px) {
            .btn {
                font-size: 1.2rem;
                padding: 10px 20px;
            }
            .form-control {
                font-size: 1.2rem;
                padding: 10px;
            }
            .btn-group-vertical a {
                display: block;
                width: 100%;
                margin-bottom: 10px;
            }
        }
    """ if 是否为手机模式 else ""
    返回链接 = '<a href="/" class="btn btn-secondary back-button">返回菜单</a>' if 返回按钮 else ''
    return f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{标题}</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f4f4f9;
            }}
            .btn {{
                transition: all 0.3s ease;
            }}
            .btn:hover {{
                transform: scale(1.05);
            }}
            .back-button {{
                position: absolute;
                top: 10px;
                left: 10px;
            }}
            .settings-button {{
                position: fixed;
                bottom: 20px;
                right: 20px;
            }}
            {手机模式CSS}
        </style>
    </head>
    <body>
        {返回链接}
        <div class="container my-5">
            {内容}
        </div>
        <button type="button" class="btn btn-primary settings-button" data-bs-toggle="modal" data-bs-target="#settingsModal">设置</button>
        <div class="modal fade" id="settingsModal" tabindex="-1" aria-labelledby="settingsModalLabel" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="settingsModalLabel">设置</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="mb-3">
                            <label for="screenFrameRate" class="form-label">屏幕截图帧率 (帧/秒)</label>
                            <input type="number" class="form-control" id="screenFrameRate" value="{屏幕帧率}">
                        </div>
                        <div class="mb-3">
                            <label for="cameraFrameRate" class="form-label">摄像头帧率 (帧/秒)</label>
                            <input type="number" class="form-control" id="cameraFrameRate" value="{摄像头帧率}">
                        </div>
                        <div class="mb-3 form-check">
                            <input type="checkbox" class="form-check-input" id="mobileModeCheckbox" {'checked' if 是否为手机模式 else ''}>
                            <label class="form-check-label" for="mobileModeCheckbox">手机模式</label>
                        </div>
                        <div class="mb-3 form-check">
                            <input type="checkbox" class="form-check-input" id="clientHiddenCheckbox" {'checked' if 是否隐藏客户端界面 else ''}>
                            <label class="form-check-label" for="clientHiddenCheckbox">隐藏客户端图形界面</label>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                        <button type="button" class="btn btn-primary" onclick="saveSettings()">保存设置</button>
                    </div>
                </div>
            </div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            function saveSettings() {{
                const screenFrameRate = document.getElementById('screenFrameRate').value;
                const cameraFrameRate = document.getElementById('cameraFrameRate').value;
                const mobileMode = document.getElementById('mobileModeCheckbox').checked;
                const clientHidden = document.getElementById('clientHiddenCheckbox').checked;
                fetch('/设置帧率', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{屏幕帧率: screenFrameRate, 摄像头帧率: cameraFrameRate}})
                }})
               .then(response => response.json())
               .then(data => {{
                    alert(data.消息);
                }})
               .catch(error => {{
                    alert('错误: ' + error.message);
                }});
                fetch('/设置手机模式', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{是否为手机模式: mobileMode}})
                }})
               .then(response => response.json())
               .then(data => {{
                    alert(data.消息);
                }})
               .catch(error => {{
                    alert('错误: ' + error.message);
                }});
                fetch('/设置隐藏客户端界面', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{是否隐藏客户端界面: clientHidden}})
                }})
               .then(response => response.json())
               .then(data => {{
                    alert(data.消息);
                    $('#settingsModal').modal('hide');
                }})
               .catch(error => {{
                    alert('错误: ' + error.message);
                }});
            }}
        </script>
    </body>
    </html>
    """

@app.route('/')
def 主页():
    宽度, 高度 = pyautogui.size()
    return render_template_string(生成HTML模板("桌面投影菜单", f"""
        <div class="text-center">
            <h1 class="display-4">远程控制</h1>
            <div class="btn-group-vertical mt-4">
                <a href="/远程控制" class="btn btn-primary">远程控制</a>
                <a href="/命令行" class="btn btn-primary">命令行</a>
                <a href="/电脑信息" class="btn btn-primary">电脑参数</a>
                <a href="/摄像头查看" class="btn btn-primary">摄像头查看</a>
                <a href="/文件上传" class="btn btn-primary">文件上传</a>
                <button onclick="shutdownComputer()" class="btn btn-danger">远程关机</button>
                <button onclick="restartComputer()" class="btn btn-warning">远程重启</button>
                <div class="mt-3">
                    <button onclick="volumeUp()" class="btn btn-info">音量增大</button>
                    <button onclick="volumeDown()" class="btn btn-info">音量减小</button>
                    <button onclick="volumeMute()" class="btn btn-info">静音</button>
                </div>
            </div>
        </div>
        <script>
            function shutdownComputer() {{
                if (confirm('确定要关机吗？')) {{
                    fetch('/关机', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify({{}})
                    }})
                   .then(response => response.json())
                   .then(data => {{
                        alert(data.消息);
                    }})
                   .catch(error => {{
                        alert('错误: ' + error.message);
                    }});
                }}
            }}
            function restartComputer() {{
                if (confirm('确定要重启吗？')) {{
                    fetch('/重启', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify({{}})
                    }})
                   .then(response => response.json())
                   .then(data => {{
                        alert(data.消息);
                    }})
                   .catch(error => {{
                        alert('错误: ' + error.message);
                    }});
                }}
            }}
            function volumeUp() {{
                fetch('/音量控制', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{操作: '增大'}})
                }});
            }}
            function volumeDown() {{
                fetch('/音量控制', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{操作: '减小'}})
                }});
            }}
            function volumeMute() {{
                fetch('/音量控制', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{操作: '静音'}})
                }});
            }}
        </script>
    """, 返回按钮=False))

@app.route('/远程控制')
def 远程控制():
    宽度, 高度 = pyautogui.size()
    触摸事件脚本 = """
        let isDragging = false;
        let startX = 0;
        let startY = 0;

        video.addEventListener('touchstart', function(event) {
            event.preventDefault();
            if (event.touches.length === 1) {
                // 单点触摸模拟左键点击
                const touch = event.touches[0];
                const x = touch.offsetX || touch.layerX;
                const y = touch.offsetY || touch.layerY;
                const scaleX = screenWidth / video.offsetWidth;
                const scaleY = screenHeight / video.offsetHeight;
                fetch('/鼠标点击', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({x: x, y: y, 缩放比例_x: scaleX, 缩放比例_y: scaleY, 点击类型: '左键'})
                });
            } else if (event.touches.length === 2) {
                // 双指触摸开始拖动
                isDragging = true;
                startX = event.touches[0].pageX;
                startY = event.touches[0].pageY;
            }
        });

        video.addEventListener('touchmove', function(event) {
            if (isDragging && event.touches.length === 2) {
                const touch = event.touches[0];
                const x = touch.offsetX || touch.layerX;
                const y = touch.offsetY || touch.layerY;
                const scaleX = screenWidth / video.offsetWidth;
                const scaleY = screenHeight / video.offsetHeight;
                fetch('/鼠标点击', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({x: x, y: y, 缩放比例_x: scaleX, 缩放比例_y: scaleY, 点击类型: '拖动', 起始_x: startX, 起始_y: startY})
                });
            }
        });

        video.addEventListener('touchend', function(event) {
            isDragging = false;
        });
    """ if 是否为手机模式 else ""
    return render_template_string(生成HTML模板("远程控制", f"""
        <div class="text-center">
            <h2>远程控制</h2>
            <div id="video-container" class="mt-4">
                <img id="video" src="/视频流" class="img-fluid">
            </div>
        </div>
        <script>
            const video = document.getElementById('video');
            const screenWidth = {宽度};
            const screenHeight = {高度};
            let clickTimer = null;
            let isDragging = false;
            let dragStartX = 0;
            let dragStartY = 0;

            video.addEventListener('mousedown', function(event) {{
                isDragging = true;
                dragStartX = event.offsetX;
                dragStartY = event.offsetY;
            }});

            video.addEventListener('mousemove', function(event) {{
                if (isDragging) {{
                    const x = event.offsetX;
                    const y = event.offsetY;
                    const scaleX = screenWidth / video.offsetWidth;
                    const scaleY = screenHeight / video.offsetHeight;
                    fetch('/鼠标点击', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify({{x: x, y: y, 缩放比例_x: scaleX, 缩放比例_y: scaleY, 点击类型: '拖动', 起始_x: dragStartX, 起始_y: dragStartY}})
                    }});
                }}
            }});

            video.addEventListener('mouseup', function(event) {{
                isDragging = false;
            }});

            video.addEventListener('click', function(event) {{
                if (clickTimer) {{
                    clearTimeout(clickTimer);
                    clickTimer = null;
                    sendClickRequest(event, '双击');
                }} else {{
                    clickTimer = setTimeout(() => {{
                        clickTimer = null;
                        sendClickRequest(event, '左键');
                    }}, 300);
                }}
            }});

            video.addEventListener('contextmenu', function(event) {{
                event.preventDefault();
                sendClickRequest(event, '右键');
            }});

            function sendClickRequest(event, clickType) {{
                const x = event.offsetX;
                const y = event.offsetY;
                const scaleX = screenWidth / video.offsetWidth;
                const scaleY = screenHeight / video.offsetHeight;
                fetch('/鼠标点击', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{x: x, y: y, 缩放比例_x: scaleX, 缩放比例_y: scaleY, 点击类型: clickType}})
                }});
            }}

            document.addEventListener('keydown', function(event) {{
                const key = event.key;
                fetch('/键盘按键', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{按键: key}})
                }});
            }});

            {触摸事件脚本}
        </script>
    """))

@app.route('/命令行')
def 命令行():
    return render_template_string(生成HTML模板("命令行", f"""
        <div class="text-center">
            <h2>命令行</h2>
            <div id="terminal-container" class="mt-4">
                <div id="terminal-output" class="bg-dark text-white p-3" style="height: 300px; overflow-y: auto;"></div>
                <input type="text" id="terminal-input" class="form-control mt-3" placeholder="输入命令" {'inputmode="text"' if 是否为手机模式 else ''}>
            </div>
        </div>
        <script>
            const terminalInput = document.getElementById('terminal-input');
            const terminalOutput = document.getElementById('terminal-output');
            terminalInput.addEventListener('keydown', function(event) {{
                if (event.key === 'Enter') {{
                    const command = terminalInput.value;
                    terminalInput.value = '';
                    fetch('/执行命令', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify({{命令: command}})
                    }})
                   .then(response => response.json())
                   .then(data => {{
                        const outputElement = document.createElement('pre');
                        outputElement.textContent = '$ ' + command + '\\n' + data.输出;
                        terminalOutput.appendChild(outputElement);
                        terminalOutput.scrollTop = terminalOutput.scrollHeight;
                    }})
                   .catch(error => {{
                        const errorElement = document.createElement('pre');
                        errorElement.textContent = '错误: ' + error.message;
                        terminalOutput.appendChild(errorElement);
                        terminalOutput.scrollTop = terminalOutput.scrollHeight;
                    }});
                }}
            }});
        </script>
    """))

@app.route('/电脑信息')
def 电脑信息():
    return render_template_string(生成HTML模板("电脑参数", f"""
        <div class="text-center">
            <h2>电脑参数</h2>
            <pre id="info-output" class="bg-dark text-white p-3 mt-4"></pre>
        </div>
        <script>
            fetch('/获取电脑信息')
           .then(response => response.json())
           .then(data => {{
                const infoOutput = document.getElementById('info-output');
                let infoText = '';
                for (const key in data) {{
                    infoText += key + ': ' + data[key] + '\\n';
                }}
                infoOutput.textContent = infoText;
            }})
           .catch(error => {{
                const infoOutput = document.getElementById('info-output');
                infoOutput.textContent = '错误: ' + error.message;
            }});
        </script>
    """))

@app.route('/摄像头查看')
def 摄像头查看():
    状态 = 摄像头状态队列.get() if not 摄像头状态队列.empty() else "未知状态"
    return render_template_string(生成HTML模板("摄像头查看", f"""
        <div class="text-center">
            <h2>摄像头查看</h2>
            <p class="mt-4">摄像头状态: {状态}</p>
            <img src="/摄像头流" class="img-fluid mt-3">
        </div>
    """))

@app.route('/文件上传')
def 文件上传():
    return render_template_string(生成HTML模板("文件上传", f"""
        <div class="text-center">
            <h2>文件上传</h2>
            <form id="upload-form" enctype="multipart/form-data">
                <input type="file" id="file-input" name="文件" class="form-control mt-4">
                <button type="button" onclick="uploadFile()" class="btn btn-primary mt-3">上传文件</button>
            </form>
            <div id="upload-status" class="mt-3"></div>
        </div>
        <script>
            function uploadFile() {{
                const fileInput = document.getElementById('file-input');
                const file = fileInput.files[0];
                if (!file) {{
                    alert('请选择文件');
                    return;
                }}
                const formData = new FormData();
                formData.append('文件', file);
                fetch('/上传文件', {{
                    method: 'POST',
                    body: formData
                }})
               .then(response => response.json())
               .then(data => {{
                    const statusDiv = document.getElementById('upload-status');
                    statusDiv.textContent = data.消息;
                }})
               .catch(error => {{
                    const statusDiv = document.getElementById('upload-status');
                    statusDiv.textContent = '错误: ' + error.message;
                }});
            }}
        </script>
    """))

def 启动Flask服务器():
    app.run(debug=False, host='::', port=5000)

def 启动图形界面():
    global 根窗口
    根窗口 = tk.Tk()
    根窗口.title("远程桌面")
    tk.Label(根窗口, text="服务已启动，访问 http://localhost:5000 或 http://[::1]:5000 查看。").pack(pady=20)
    根窗口.mainloop()

if __name__ == '__main__':
    # 启动 Flask 服务器线程
    flask线程 = Thread(target=启动Flask服务器, daemon=True)
    flask线程.start()
    # 启动 GUI 线程
    启动图形界面()