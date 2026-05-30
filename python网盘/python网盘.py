import psutil, socket, subprocess, platform
import sys
import io


def check_interface_ipv6_support():
    net_if_addrs = psutil.net_if_addrs()
    for interface, addrs in net_if_addrs.items():
        for addr in addrs:
            if addr.family.name.startswith('AF_INET6'):
                return True
    return False


def check_ipv6_connectivity():
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
        subprocess.run(['netsh', 'interface', 'ipv6', 'set', 'interface', 'all', 'advertise=enabled'], check=True)
        subprocess.run(['netsh', 'interface', 'ipv6', 'set', 'interface', 'all', 'forwarding=enabled'], check=True)
        print("已尝试在 Windows 系统上启用 IPv6，请稍等片刻...")
        return True
    except subprocess.CalledProcessError as e:
        print(f"在 Windows 系统上启用 IPv6 时出现错误: {e}")
        return False


def enable_ipv6_linux():
    try:
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
print('环境检查完毕，网盘脚本开始运行')
import os, sys, threading, uuid, tkinter as tk, json, subprocess
from tkinter import messagebox

def check_and_install_libraries():
    required_libraries = ['flask', 'werkzeug']
    missing_libraries = []
    
    for lib in required_libraries:
        try:
            __import__(lib)
        except ImportError:
            missing_libraries.append(lib)
    
    if missing_libraries:
        print(f"缺少以下库：{', '.join(missing_libraries)}")
        print("正在使用清华大学PyPI镜像安装...")
        
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "--index-url", "https://pypi.tuna.tsinghua.edu.cn/simple",
                *missing_libraries
            ])
            print("库安装成功！")
        except subprocess.CalledProcessError:
            print("库安装失败，请手动安装所需库：")
            print(f"pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple {' '.join(missing_libraries)}")
            sys.exit(1)

# 检测并安装必要的库
check_and_install_libraries()

from flask import Flask, request, send_from_directory, redirect, url_for, render_template_string, abort, session
from werkzeug.security import generate_password_hash, check_password_hash

# 获取程序运行的目录
APP_ROOT = os.path.dirname(os.path.abspath(__file__))

def is_text_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read(1000)
            for char in content:
                if ord(char) < 32 and char not in '\n\r\t\f\v':
                    return False
            return True
    except UnicodeDecodeError:
        return False
    except Exception:
        return False

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = os.path.join(APP_ROOT, 'user_uploads')

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

USERS_FILE = os.path.join(APP_ROOT, 'users.json')

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

users = load_users()

def save_users():
    if not os.path.exists(os.path.dirname(USERS_FILE)) and os.path.dirname(USERS_FILE) != '':
        os.makedirs(os.path.dirname(USERS_FILE))
    
    try:
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
    except IOError as e:
        print(f"保存用户数据失败: {e}")

PREVIEW_EXTENSIONS = {'txt', 'pdf', 'jpg', 'jpeg', 'png', 'gif', 'mp4', 'webm', 'ogg', 'mp3', 'wav'}
file_shares = {}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, minimum-scale=0.6">
    <title>NYM网盘</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root {
            --primary-color: #4a90e2;
            --primary-hover: #357abd;
            --secondary-color: #6c757d;
            --success-color: #28a745;
            --danger-color: #dc3545;
            --warning-color: #ffc107;
            --info-color: #17a2b8;
            --light-color: #f8f9fa;
            --dark-color: #343a40;
            --background-color: #f5f7fa;
            --card-background: #ffffff;
            --border-color: #e9ecef;
            --text-color: #212529;
            --text-muted: #6c757d;
            --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.08);
            --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.12);
            --border-radius: 8px;
            --transition: all 0.2s ease;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: var(--background-color);
            color: var(--text-color);
            padding: 20px;
            line-height: 1.6;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        h1 {
            font-size: 2rem;
            margin-bottom: 20px;
            color: var(--dark-color);
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        h1 i {
            color: var(--primary-color);
        }

        .user-info {
            display: flex;
            justify-content: flex-end;
            align-items: center;
            gap: 15px;
            margin-bottom: 20px;
            padding: 15px 20px;
            background: var(--card-background);
            border-radius: var(--border-radius);
            box-shadow: var(--shadow-md);
            transition: var(--transition);
        }

        .user-info:hover {
            box-shadow: var(--shadow-lg);
        }

        .user-info span {
            font-weight: 600;
            color: var(--dark-color);
        }

        .card {
            background: var(--card-background);
            padding: 25px;
            margin-bottom: 25px;
            border-radius: var(--border-radius);
            box-shadow: var(--shadow-md);
            transition: var(--transition);
        }

        .card:hover {
            box-shadow: var(--shadow-lg);
        }

        h2 {
            font-size: 1.4rem;
            margin-bottom: 20px;
            color: var(--dark-color);
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        h2 i {
            color: var(--primary-color);
            font-size: 1.2rem;
        }

        input[type="file"],
        input[type="text"],
        input[type="password"] {
            padding: 10px 15px;
            border: 2px solid var(--border-color);
            border-radius: var(--border-radius);
            margin-right: 10px;
            margin-bottom: 15px;
            font-size: 14px;
            transition: var(--transition);
            background: var(--card-background);
            color: var(--text-color);
            min-width: 250px;
        }

        input[type="file"]:focus,
        input[type="text"]:focus,
        input[type="password"]:focus {
            outline: none;
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
        }

        button,
        .btn {
            padding: 10px 20px;
            background: var(--primary-color);
            color: white;
            border: none;
            border-radius: var(--border-radius);
            cursor: pointer;
            text-decoration: none;
            font-size: 14px;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: var(--transition);
            box-shadow: var(--shadow-sm);
        }

        button:hover,
        .btn:hover {
            background: var(--primary-hover);
            transform: translateY(-1px);
            box-shadow: var(--shadow-md);
        }

        button:active,
        .btn:active {
            transform: translateY(0);
        }

        .btn-danger {
            background: var(--danger-color);
        }

        .btn-danger:hover {
            background: #c82333;
        }

        .btn-warning {
            background: var(--warning-color);
            color: var(--dark-color);
        }

        .btn-warning:hover {
            background: #e0a800;
        }

        .btn-info {
            background: var(--info-color);
        }

        .btn-info:hover {
            background: #138496;
        }

        .btn-outline {
            background: transparent;
            color: var(--primary-color);
            border: 2px solid var(--primary-color);
        }

        .btn-outline:hover {
            background: var(--primary-color);
            color: white;
        }

        .btn-sm {
            padding: 6px 12px;
            font-size: 12px;
            gap: 5px;
        }

        .input-group {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
            align-items: flex-start;
            flex-wrap: wrap;
        }

        .input-group input {
            flex: 1;
            min-width: 250px;
            margin-right: 0;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background: var(--card-background);
            border-radius: var(--border-radius);
            overflow: hidden;
            box-shadow: var(--shadow-sm);
        }

        th,
        td {
            padding: 15px 20px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }

        th {
            background: linear-gradient(135deg, var(--primary-color), var(--primary-hover));
            color: white;
            font-weight: 600;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        tr {
            transition: var(--transition);
        }

        tr:last-child td {
            border-bottom: none;
        }

        tr:hover {
            background: var(--light-color);
            transform: translateX(5px);
        }

        td a {
            color: var(--primary-color);
            text-decoration: none;
            font-weight: 500;
            transition: var(--transition);
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }

        td a:hover {
            color: var(--primary-hover);
            text-decoration: underline;
        }

        .file-actions {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }

        .text-center {
            text-align: center;
        }

        .mt-3 {
            margin-top: 20px;
        }

        .mb-3 {
            margin-bottom: 20px;
        }

        .mb-4 {
            margin-bottom: 25px;
        }

        .py-4 {
            padding: 30px 0;
        }

        .fs-5 {
            font-size: 1.25rem;
        }

        .text-primary {
            color: var(--primary-color);
            font-weight: 600;
        }

        .text-muted {
            color: var(--text-muted);
        }

        .file-name {
            font-weight: 500;
            color: var(--dark-color);
        }

        .file-size {
            font-size: 0.9rem;
            color: var(--text-muted);
            margin-left: 10px;
        }

        /* 响应式设计 */
        @media (max-width: 768px) {
            body {
                padding: 10px;
            }

            .container {
                padding: 0;
            }

            h1 {
                font-size: 1.5rem;
            }

            h2 {
                font-size: 1.2rem;
            }

            .card {
                padding: 15px;
            }

            .input-group {
                flex-direction: column;
            }

            .input-group input {
                min-width: 100%;
                margin-right: 0;
                margin-bottom: 10px;
            }

            table {
                font-size: 0.9rem;
            }

            th,
            td {
                padding: 10px;
            }

            .file-actions {
                flex-direction: column;
            }

            .file-actions .btn {
                width: 100%;
                justify-content: center;
            }

            .user-info {
                flex-direction: column;
                align-items: stretch;
                text-align: center;
            }

            .user-info .btn {
                width: 100%;
                justify-content: center;
            }
        }

        /* 动画效果 */
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .card {
            animation: fadeIn 0.3s ease-out;
        }

        /* 表单样式 */
        .form-label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: var(--dark-color);
        }

        /* 选择文件按钮样式 */
        input[type="file"] {
            background: var(--light-color);
            cursor: pointer;
        }

        input[type="file"]:hover {
            background: #e9ecef;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1><i class="fas fa-cloud"></i> NYM网盘</h1>

        <!-- 用户登录状态 -->
        <div class="user-info">
            {% if 'username' in session %}
                <span><i class="fas fa-user"></i> 欢迎，{{ session['username'] }}！</span>
                <a href="{{ url_for('logout') }}" class="btn btn-sm btn-danger"><i class="fas fa-sign-out-alt"></i> 退出登录</a>
            {% else %}
                <a href="{{ url_for('login') }}" class="btn btn-sm btn-outline"><i class="fas fa-sign-in-alt"></i> 登录</a>
                <a href="{{ url_for('register') }}" class="btn btn-sm"><i class="fas fa-user-plus"></i> 注册</a>
            {% endif %}
        </div>

        <!-- 上传文件部分 -->
        {% if 'username' in session %}
            <div class="card">
                <h2><i class="fas fa-upload"></i> 上传文件</h2>
                <form action="/upload" method="post" enctype="multipart/form-data">
                    <input type="file" name="file" multiple>
                    <button type="submit" class="btn"><i class="fas fa-paper-plane"></i> 开始上传</button>
                </form>
            </div>

            <!-- 文件搜索 -->
            <div class="card">
                <h2><i class="fas fa-search"></i> 文件搜索</h2>
                <form action="/search" method="get">
                    <div class="input-group">
                        <input type="text" name="query" placeholder="搜索文件...">
                        <button type="submit" class="btn"><i class="fas fa-search"></i> 搜索</button>
                    </div>
                </form>
            </div>

            <!-- 文件列表 -->
            <div class="card">
                <h2><i class="fas fa-folder-open"></i> 文件列表</h2>
                <form action="/batch_delete" method="post">
                    {% if files|length > 0 %}
                        <table>
                            <thead>
                                <tr>
                                    <th>选择</th>
                                    <th>文件名</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for file in files %}
                                    <tr>
                                        <td><input type="checkbox" name="file" value="{{ file }}"></td>
                                        <td>
                                            <a href="{{ url_for('download_file', filename=file) }}" class="file-name">
                                                {% if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')) %}
                                                    <i class="fas fa-image"></i>
                                                {% elif file.lower().endswith(('.mp4', '.webm', '.ogg', '.avi', '.mov')) %}
                                                    <i class="fas fa-film"></i>
                                                {% elif file.lower().endswith(('.mp3', '.wav', '.ogg', '.flac')) %}
                                                    <i class="fas fa-music"></i>
                                                {% elif file.lower().endswith(('.pdf')) %}
                                                    <i class="fas fa-file-pdf"></i>
                                                {% elif file.lower().endswith(('.txt')) %}
                                                    <i class="fas fa-file-alt"></i>
                                                {% elif file.lower().endswith(('.doc', '.docx')) %}
                                                    <i class="fas fa-file-word"></i>
                                                {% elif file.lower().endswith(('.xls', '.xlsx')) %}
                                                    <i class="fas fa-file-excel"></i>
                                                {% elif file.lower().endswith(('.ppt', '.pptx')) %}
                                                    <i class="fas fa-file-powerpoint"></i>
                                                {% elif file.lower().endswith(('.zip', '.rar', '.7z', '.tar', '.gz')) %}
                                                    <i class="fas fa-file-archive"></i>
                                                {% elif file.lower().endswith(('.py', '.js', '.html', '.css', '.php', '.java', '.c', '.cpp', '.h', '.hpp')) %}
                                                    <i class="fas fa-file-code"></i>
                                                {% else %}
                                                    <i class="fas fa-file"></i>
                                                {% endif %} {{ file }}
                                            </a>
                                        </td>
                                        <td class="file-actions">
                                            <a href="{{ url_for('preview_file', filename=file) }}" class="btn btn-sm btn-info" title="预览">
                                                <i class="fas fa-eye"></i>
                                            </a>
                                            <a href="{{ url_for('share_file', filename=file) }}" class="btn btn-sm btn-warning" title="分享">
                                                <i class="fas fa-share-alt"></i>
                                            </a>
                                            <a href="{{ url_for('delete_file', filename=file) }}" class="btn btn-sm btn-danger" onclick="return confirm('确定删除此文件吗？')" title="删除">
                                                <i class="fas fa-trash"></i>
                                            </a>
                                        </td>
                                    </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                        <button type="submit" class="btn btn-danger mt-3"><i class="fas fa-trash-alt"></i> 删除选中文件</button>
                    {% else %}
                        <div class="text-center py-4">
                            <i class="fas fa-inbox" style="font-size: 3rem; color: var(--text-muted); margin-bottom: 15px;"></i>
                            <p class="fs-5 text-muted">暂无文件</p>
                            <p class="text-muted">上传您的第一个文件开始使用</p>
                        </div>
                    {% endif %}
                </form>
            </div>
        {% else %}
            <div class="card text-center">
                <i class="fas fa-lock" style="font-size: 4rem; color: var(--primary-color); margin-bottom: 20px;"></i>
                <p class="fs-5 py-4">请<a href="{{ url_for('login') }}" class="text-primary">登录</a>或<a href="{{ url_for('register') }}" class="text-primary">注册</a>以使用网盘功能。</p>
            </div>
        {% endif %}
    </div>
</body>
</html>
"""


@app.errorhandler(404)
def page_not_found(error):
    return render_template_string('''
        <style>
            body {
                font-family: system-ui, -apple-system, sans-serif;
                background: #f0f0f0;
                color: #333;
                padding: 20px;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .error-container {
                text-align: center;
                max-width: 500px;
                background: #fff;
                padding: 30px;
                border-radius: 4px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            h1 {
                font-size: 4rem;
                margin-bottom: 20px;
                color: #e74c3c;
            }
            p {
                font-size: 1.2rem;
                margin-bottom: 30px;
            }
            .btn {
                padding: 10px 24px;
                background: #4a90e2;
                color: white;
                border: none;
                border-radius: 3px;
                cursor: pointer;
                text-decoration: none;
                font-size: 1.1rem;
            }
            .btn:hover {
                background: #357abd;
            }
        </style>
        <div class="error-container">
            <h1>404</h1>
            <p>页面未找到</p>
            <p>您访问的页面不存在，请检查 URL 是否正确。</p>
            <div>
                <a href="{{ url_for('index') }}" class="btn">返回首页</a>
            </div>
        </div>
    '''), 404


@app.errorhandler(500)
def internal_server_error(error):
    return render_template_string('''
        <style>
            body {
                font-family: system-ui, -apple-system, sans-serif;
                background: #f0f0f0;
                color: #333;
                padding: 20px;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .error-container {
                text-align: center;
                max-width: 500px;
                background: #fff;
                padding: 30px;
                border-radius: 4px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            h1 {
                font-size: 4rem;
                margin-bottom: 20px;
                color: #e74c3c;
            }
            p {
                font-size: 1.2rem;
                margin-bottom: 30px;
            }
            .btn {
                padding: 10px 24px;
                background: #4a90e2;
                color: white;
                border: none;
                border-radius: 3px;
                cursor: pointer;
                text-decoration: none;
                font-size: 1.1rem;
            }
            .btn:hover {
                background: #357abd;
            }
        </style>
        <div class="error-container">
            <h1>500</h1>
            <p>服务器内部错误</p>
            <p>服务器遇到错误，请稍后重试。</p>
            <div>
                <a href="{{ url_for('index') }}" class="btn">返回首页</a>
            </div>
        </div>
    '''), 500


@app.route('/')
def index():
    if 'username' not in session:
        return render_template_string(HTML_TEMPLATE, files=[])
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], session['username'])
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)
    files = os.listdir(user_folder)
    return render_template_string(HTML_TEMPLATE, files=files)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            return render_template_string('''
                <style>
                    body {
                        font-family: system-ui, -apple-system, sans-serif;
                        background: #f0f0f0;
                        color: #333;
                        padding: 20px;
                        min-height: 100vh;
                    }
                    .container {
                        max-width: 400px;
                        margin: 0 auto;
                    }
                    h1 {
                        font-size: 1.8rem;
                        margin-bottom: 15px;
                        text-align: center;
                    }
                    .card {
                        background: #fff;
                        padding: 30px;
                        border-radius: 4px;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                    }
                    .text-danger {
                        color: #e74c3c;
                        text-align: center;
                        margin-bottom: 15px;
                    }
                    .btn {
                        padding: 8px 12px;
                        background: #4a90e2;
                        color: white;
                        border: none;
                        border-radius: 3px;
                        cursor: pointer;
                        text-decoration: none;
                        font-size: 0.9rem;
                    }
                    .btn:hover {
                        background: #357abd;
                    }
                    .text-center {
                        text-align: center;
                    }
                </style>
                <div class="container">
                    <h1>注册</h1>
                    <div class="card">
                        <p class="text-danger">用户名和密码不能为空！</p>
                        <div class="text-center">
                            <a href="{{ url_for('register') }}" class="btn">返回注册</a>
                        </div>
                    </div>
                </div>
            ''')
        if username in users:
            return render_template_string('''
                <style>
                    body {
                        font-family: system-ui, -apple-system, sans-serif;
                        background: #f0f0f0;
                        color: #333;
                        padding: 20px;
                        min-height: 100vh;
                    }
                    .container {
                        max-width: 400px;
                        margin: 0 auto;
                    }
                    h1 {
                        font-size: 1.8rem;
                        margin-bottom: 15px;
                        text-align: center;
                    }
                    .card {
                        background: #fff;
                        padding: 30px;
                        border-radius: 4px;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                    }
                    .text-danger {
                        color: #e74c3c;
                        text-align: center;
                        margin-bottom: 15px;
                    }
                    .btn {
                        padding: 8px 12px;
                        background: #4a90e2;
                        color: white;
                        border: none;
                        border-radius: 3px;
                        cursor: pointer;
                        text-decoration: none;
                        font-size: 0.9rem;
                    }
                    .btn:hover {
                        background: #357abd;
                    }
                    .text-center {
                        text-align: center;
                    }
                </style>
                <div class="container">
                    <h1>注册</h1>
                    <div class="card">
                        <p class="text-danger">用户名已存在！</p>
                        <div class="text-center">
                            <a href="{{ url_for('register') }}" class="btn">返回注册</a>
                        </div>
                    </div>
                </div>
            ''')
        users[username] = generate_password_hash(password)
        save_users()  # 保存用户数据到文件
        return redirect(url_for('login'))
    return render_template_string('''
        <style>
            body {
                font-family: system-ui, -apple-system, sans-serif;
                background: #f0f0f0;
                color: #333;
                padding: 20px;
                min-height: 100vh;
            }
            .container {
                max-width: 400px;
                margin: 0 auto;
            }
            h1 {
                font-size: 1.8rem;
                margin-bottom: 15px;
                text-align: center;
            }
            .card {
                background: #fff;
                padding: 30px;
                border-radius: 4px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            .mb-4 {
                margin-bottom: 15px;
            }
            .form-label {
                display: block;
                margin-bottom: 5px;
                font-weight: 600;
            }
            input[type="text"],
            input[type="password"] {
                width: 100%;
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 3px;
            }
            .btn {
                padding: 8px 12px;
                background: #4a90e2;
                color: white;
                border: none;
                border-radius: 3px;
                cursor: pointer;
                text-decoration: none;
                font-size: 0.9rem;
                width: 100%;
            }
            .btn:hover {
                background: #357abd;
            }
            .btn-outline {
                background: transparent;
                color: #4a90e2;
                border: 1px solid #4a90e2;
            }
            .btn-outline:hover {
                background: #4a90e2;
                color: white;
            }
            .text-center {
                text-align: center;
                margin-top: 15px;
            }
        </style>
        <div class="container">
            <h1>注册</h1>
            <div class="card">
                <form action="/register" method="post">
                    <div class="mb-4">
                        <label for="username" class="form-label">用户名</label>
                        <input type="text" name="username" required>
                    </div>
                    <div class="mb-4">
                        <label for="password" class="form-label">密码</label>
                        <input type="password" name="password" required>
                    </div>
                    <button type="submit" class="btn">注册</button>
                </form>
                <div class="text-center">
                    <a href="{{ url_for('login') }}" class="btn btn-outline">已有账号？登录</a>
                </div>
            </div>
        </div>
    ''')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            return render_template_string('''
                <style>
                    body {
                        font-family: system-ui, -apple-system, sans-serif;
                        background: #f0f0f0;
                        color: #333;
                        padding: 20px;
                        min-height: 100vh;
                    }
                    .container {
                        max-width: 400px;
                        margin: 0 auto;
                    }
                    h1 {
                        font-size: 1.8rem;
                        margin-bottom: 15px;
                        text-align: center;
                    }
                    .card {
                        background: #fff;
                        padding: 30px;
                        border-radius: 4px;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                    }
                    .text-danger {
                        color: #e74c3c;
                        text-align: center;
                        margin-bottom: 15px;
                    }
                    .btn {
                        padding: 8px 12px;
                        background: #4a90e2;
                        color: white;
                        border: none;
                        border-radius: 3px;
                        cursor: pointer;
                        text-decoration: none;
                        font-size: 0.9rem;
                    }
                    .btn:hover {
                        background: #357abd;
                    }
                    .text-center {
                        text-align: center;
                    }
                </style>
                <div class="container">
                    <h1>登录</h1>
                    <div class="card">
                        <p class="text-danger">用户名和密码不能为空！</p>
                        <div class="text-center">
                            <a href="{{ url_for('login') }}" class="btn">返回登录</a>
                        </div>
                    </div>
                </div>
            ''')
        if username not in users or not check_password_hash(users[username], password):
            return render_template_string('''
                <style>
                    body {
                        font-family: system-ui, -apple-system, sans-serif;
                        background: #f0f0f0;
                        color: #333;
                        padding: 20px;
                        min-height: 100vh;
                    }
                    .container {
                        max-width: 400px;
                        margin: 0 auto;
                    }
                    h1 {
                        font-size: 1.8rem;
                        margin-bottom: 15px;
                        text-align: center;
                    }
                    .card {
                        background: #fff;
                        padding: 30px;
                        border-radius: 4px;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                    }
                    .text-danger {
                        color: #e74c3c;
                        text-align: center;
                        margin-bottom: 15px;
                    }
                    .btn {
                        padding: 8px 12px;
                        background: #4a90e2;
                        color: white;
                        border: none;
                        border-radius: 3px;
                        cursor: pointer;
                        text-decoration: none;
                        font-size: 0.9rem;
                    }
                    .btn:hover {
                        background: #357abd;
                    }
                    .text-center {
                        text-align: center;
                    }
                </style>
                <div class="container">
                    <h1>登录</h1>
                    <div class="card">
                        <p class="text-danger">用户名或密码错误！</p>
                        <div class="text-center">
                            <a href="{{ url_for('login') }}" class="btn">返回登录</a>
                        </div>
                    </div>
                </div>
            ''')
        session['username'] = username
        return redirect(url_for('index'))
    return render_template_string('''
        <style>
            body {
                font-family: system-ui, -apple-system, sans-serif;
                background: #f0f0f0;
                color: #333;
                padding: 20px;
                min-height: 100vh;
            }
            .container {
                max-width: 400px;
                margin: 0 auto;
            }
            h1 {
                font-size: 1.8rem;
                margin-bottom: 15px;
                text-align: center;
            }
            .card {
                background: #fff;
                padding: 30px;
                border-radius: 4px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            .mb-4 {
                margin-bottom: 15px;
            }
            .form-label {
                display: block;
                margin-bottom: 5px;
                font-weight: 600;
            }
            input[type="text"],
            input[type="password"] {
                width: 100%;
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 3px;
            }
            .btn {
                padding: 8px 12px;
                background: #4a90e2;
                color: white;
                border: none;
                border-radius: 3px;
                cursor: pointer;
                text-decoration: none;
                font-size: 0.9rem;
                width: 100%;
            }
            .btn:hover {
                background: #357abd;
            }
            .btn-outline {
                background: transparent;
                color: #4a90e2;
                border: 1px solid #4a90e2;
            }
            .btn-outline:hover {
                background: #4a90e2;
                color: white;
            }
            .text-center {
                text-align: center;
                margin-top: 15px;
            }
        </style>
        <div class="container">
            <h1>登录</h1>
            <div class="card">
                <form action="/login" method="post">
                    <div class="mb-4">
                        <label for="username" class="form-label">用户名</label>
                        <input type="text" name="username" required>
                    </div>
                    <div class="mb-4">
                        <label for="password" class="form-label">密码</label>
                        <input type="password" name="password" required>
                    </div>
                    <button type="submit" class="btn">登录</button>
                </form>
                <div class="text-center">
                    <a href="{{ url_for('register') }}" class="btn btn-outline">没有账号？注册</a>
                </div>
            </div>
        </div>
    ''')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'username' not in session:
        return redirect(url_for('login'))
    if 'file' not in request.files:
        return redirect(request.url)
    files = request.files.getlist('file')
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], session['username'])
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)
    for file in files:
        if file.filename == '':
            continue
        if file:
            file_path = os.path.join(user_folder, file.filename)
            file.save(file_path)
    return redirect(url_for('index'))


@app.route('/download/<filename>')
def download_file(filename):
    if 'username' not in session:
        return redirect(url_for('login'))
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], session['username'])
    try:
        return send_from_directory(user_folder, filename, as_attachment=True)
    except FileNotFoundError:
        abort(404)


@app.route('/delete/<filename>')
def delete_file(filename):
    if 'username' not in session:
        return redirect(url_for('login'))
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], session['username'])
    file_path = os.path.join(user_folder, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    return redirect(url_for('index'))


@app.route('/batch_delete', methods=['POST'])
def batch_delete():
    if 'username' not in session:
        return redirect(url_for('login'))
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], session['username'])
    files_to_delete = request.form.getlist('file')
    for filename in files_to_delete:
        file_path = os.path.join(user_folder, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
    return redirect(url_for('index'))


@app.route('/share/<filename>')
def share_file(filename):
    if 'username' not in session:
        return redirect(url_for('login'))
    share_code = str(uuid.uuid4())
    file_shares[share_code] = (session['username'], filename)
    share_url = f"{request.host_url}download_shared/{share_code}"
    return render_template_string('''
        <style>
            body {
                font-family: system-ui, -apple-system, sans-serif;
                background: #f0f0f0;
                color: #333;
                padding: 20px;
                min-height: 100vh;
            }
            .container {
                max-width: 650px;
                margin: 0 auto;
            }
            h1 {
                font-size: 1.8rem;
                margin-bottom: 15px;
                text-align: center;
            }
            .card {
                background: #fff;
                padding: 35px;
                border-radius: 4px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            .share-url {
                background: #f8f8f8;
                padding: 20px;
                border-radius: 3px;
                word-break: break-all;
                margin: 25px 0;
                font-family: monospace;
                font-size: 0.95rem;
                color: #444;
                border-left: 4px solid #4a90e2;
            }
            .share-url a {
                color: #4a90e2;
                text-decoration: none;
            }
            .share-url a:hover {
                text-decoration: underline;
            }
            .btn {
                padding: 8px 12px;
                background: #4a90e2;
                color: white;
                border: none;
                border-radius: 3px;
                cursor: pointer;
                text-decoration: none;
                font-size: 0.9rem;
            }
            .btn:hover {
                background: #357abd;
            }
            .text-center {
                text-align: center;
            }
            .mt-4 {
                margin-top: 15px;
            }
        </style>
        <div class="container">
            <h1>文件分享</h1>
            <div class="card text-center">
                <p>分享链接已生成：</p>
                <div class="share-url">
                    <a href="{{ share_url }}">{{ share_url }}</a>
                </div>
                <div class="mt-4">
                    <a href="{{ url_for('index') }}" class="btn">返回首页</a>
                </div>
            </div>
        </div>
    ''', share_url=share_url)


@app.route('/download_shared/<share_code>')
def download_shared(share_code):
    if share_code in file_shares:
        username, filename = file_shares[share_code]
        user_folder = os.path.join(app.config['UPLOAD_FOLDER'], username)
        return send_from_directory(user_folder, filename, as_attachment=True)
    else:
        abort(404)


@app.route('/search')
def search_file():
    if 'username' not in session:
        return redirect(url_for('login'))
    query = request.args.get('query', '').lower()
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], session['username'])
    files = os.listdir(user_folder)
    matched_files = [f for f in files if query in f.lower()]
    return render_template_string(HTML_TEMPLATE, files=matched_files)


@app.route('/preview/<filename>')
def preview_file(filename):
    if 'username' not in session:
        return redirect(url_for('login'))
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], session['username'])
    file_path = os.path.join(user_folder, filename)
    if not os.path.exists(file_path):
        abort(404)

    # 获取文件扩展名
    file_extension = filename.split('.')[-1].lower()

    # 通用预览样式
    preview_style = '''
        <style>
            body {
                font-family: system-ui, -apple-system, sans-serif;
                background: #f0f0f0;
                color: #333;
                padding: 20px;
                min-height: 100vh;
            }
            .container {
                max-width: 900px;
                margin: 0 auto;
            }
            h1 {
                font-size: 1.8rem;
                margin-bottom: 15px;
                text-align: center;
            }
            .card {
                background: #fff;
                padding: 15px;
                margin-bottom: 15px;
                border-radius: 4px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            .preview-container {
                margin-top: 20px;
                text-align: center;
                padding: 15px;
                background: #f8f8f8;
                border-radius: 3px;
                border: 1px solid #eee;
            }
            .preview-container img {
                max-width: 100%;
                height: auto;
                border-radius: 3px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                margin: 10px 0;
            }
            .preview-container video,
            .preview-container audio {
                width: 100%;
                max-width: 700px;
                margin: 15px auto;
                border-radius: 3px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                background: #eee;
                padding: 10px;
            }
            .preview-container embed {
                width: 100%;
                height: 650px;
                border-radius: 3px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                border: none;
            }
            .preview-container pre {
                background: #f8f8f8;
                padding: 25px;
                border-radius: 3px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                overflow-x: auto;
                text-align: left;
                font-family: monospace;
                font-size: 14px;
                line-height: 1.6;
                color: #333;
                border-left: 4px solid #4a90e2;
                white-space: pre-wrap;
                word-wrap: break-word;
            }
            .btn {
                padding: 8px 12px;
                background: #4a90e2;
                color: white;
                border: none;
                border-radius: 3px;
                cursor: pointer;
                text-decoration: none;
                font-size: 0.9rem;
            }
            .btn:hover {
                background: #357abd;
            }
            .text-center {
                text-align: center;
            }
            .mt-4 {
                margin-top: 15px;
            }
            .text-danger {
                color: #e74c3c;
                font-weight: 600;
            }
        </style>
    '''

    # 图片文件
    if file_extension in {'jpg', 'jpeg', 'png', 'gif'}:
        return render_template_string(preview_style + '''
            <div class="container">
                <h1>预览文件：{{ filename }}</h1>
                <div class="card">
                    <div class="preview-container">
                        <img src="{{ url_for('download_file', filename=filename) }}" alt="{{ filename }}">
                    </div>
                    <div class="text-center mt-4">
                        <a href="{{ url_for('index') }}" class="btn">返回首页</a>
                    </div>
                </div>
            </div>
        ''', filename=filename)

    # 文本文件和代码文件
    elif file_extension == 'txt' or file_extension in {
        'py', 'pyw',  # Python
        'js', 'jsx', 'mjs',  # JavaScript
        'ts', 'tsx',  # TypeScript
        'html', 'htm',  # HTML
        'css', 'scss', 'sass', 'less',  # CSS
        'java',  # Java
        'c', 'cpp', 'cxx', 'cc', 'h', 'hpp', 'hxx',  # C/C++
        'cs',  # C#
        'php', 'php5',  # PHP
        'rb', 'rbw',  # Ruby
        'go',  # Go
        'rs',  # Rust
        'swift',  # Swift
        'kt', 'kts',  # Kotlin
        'sql',  # SQL
        'sh', 'bash', 'zsh',  # Shell
        'pl', 'pm',  # Perl
        'lua',  # Lua
        'r',  # R
        'matlab', 'm',  # MATLAB
        'asm', 's',  # Assembly
        'json', 'xml', 'yaml', 'yml', 'toml',  # 配置文件
        'md', 'markdown',  # Markdown
        'vue', 'svelte',  # 前端框架
        'dart',  # Dart/Flutter
        'groovy',  # Groovy
        'scala'  # Scala
    }:
        # 尝试多种编码格式打开文件
        encodings = ['utf-8', 'gbk', 'gb2312', 'ansi', 'latin-1', 'utf-16']
        content = None
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue
        
        if content is not None:
            return render_template_string('''
                <div class="container">
                    <h1>预览文件：{{ filename }}</h1>
                    <div class="card">
                        <div class="preview-container">
                            <pre>{{ content }}</pre>
                        </div>
                        <div class="text-center mt-4">
                            <a href="{{ url_for('index') }}" class="btn">返回首页</a>
                        </div>
                    </div>
                </div>
            ''', filename=filename, content=content)
        else:
            # 如果所有编码都无法打开，显示错误信息
            return render_template_string('''
                <div class="container">
                    <h1>预览失败：{{ filename }}</h1>
                    <div class="card text-center">
                        <p class="text-danger">该文件可能不是文本格式或无法识别的编码，无法预览。</p>
                        <div class="mt-4">
                            <a href="{{ url_for('index') }}" class="btn">返回首页</a>
                        </div>
                    </div>
                </div>
            ''', filename=filename)

    # PDF 文件
    elif file_extension == 'pdf':
        return render_template_string(preview_style + '''
            <div class="container">
                <h1>预览文件：{{ filename }}</h1>
                <div class="card">
                    <div class="preview-container">
                        <embed src="{{ url_for('download_file', filename=filename) }}" type="application/pdf">
                    </div>
                    <div class="text-center mt-4">
                        <a href="{{ url_for('index') }}" class="btn">返回首页</a>
                    </div>
                </div>
            </div>
        ''', filename=filename)

    # 视频文件
    elif file_extension in {'mp4', 'webm', 'ogg'}:
        return render_template_string(preview_style + '''
            <div class="container">
                <h1>预览文件：{{ filename }}</h1>
                <div class="card">
                    <div class="preview-container">
                        <video controls>
                            <source src="{{ url_for('download_file', filename=filename) }}" type="video/{{ file_extension }}">
                            您的浏览器不支持视频播放。
                        </video>
                    </div>
                    <div class="text-center mt-4">
                        <a href="{{ url_for('index') }}" class="btn">返回首页</a>
                    </div>
                </div>
            </div>
        ''', filename=filename, file_extension=file_extension)

    # 音频文件
    elif file_extension in {'mp3', 'wav', 'ogg'}:
        return render_template_string(preview_style + '''
            <div class="container">
                <h1>预览文件：{{ filename }}</h1>
                <div class="card">
                    <div class="preview-container">
                        <audio controls>
                            <source src="{{ url_for('download_file', filename=filename) }}" type="audio/{{ file_extension }}">
                            您的浏览器不支持音频播放。
                        </audio>
                    </div>
                    <div class="text-center mt-4">
                        <a href="{{ url_for('index') }}" class="btn">返回首页</a>
                    </div>
                </div>
            </div>
        ''', filename=filename, file_extension=file_extension)

    # 其他文件类型：自动检测是否为文本文件（音视频除外）
    else:
        # 音视频文件除外，其他文件自动检测是否为文本
        if file_extension not in {'mp4', 'webm', 'ogg', 'mp3', 'wav', 'flac', 'm4a'}:
            if is_text_file(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    return render_template_string(preview_style + '''
                        <div class="container">
                            <h1>预览文件：{{ filename }}</h1>
                            <div class="card">
                                <div class="preview-container">
                                    <pre>{{ content }}</pre>
                                </div>
                                <div class="text-center mt-4">
                                    <a href="{{ url_for('index') }}" class="btn">返回首页</a>
                                </div>
                            </div>
                        </div>
                    ''', filename=filename, content=content)
                except Exception:
                    pass
        
        return render_template_string(preview_style + '''
            <div class="container">
                <h1>不支持预览的文件类型：{{ filename }}</h1>
                <div class="card text-center">
                    <p>该文件类型不支持在线预览。</p>
                    <div class="mt-4">
                        <a href="{{ url_for('index') }}" class="btn">返回首页</a>
                    </div>
                </div>
            </div>
        ''', filename=filename)


# 运行 Flask 服务器
def run_flask():
    # 导入需要的模块
    from werkzeug.serving import run_simple
    # 使用run_simple代替app.run，这样可以更灵活地控制服务器
    run_simple('0.0.0.0', 5001, app, threaded=True, use_reloader=False)


# Flask 服务器线程
flask_thread = None

# 服务器状态全局变量 (0: 未运行, 1: 已运行)
server_status = 0


def start_flask(log_text=None):
    global flask_thread
    global server_status
    if flask_thread is None or not flask_thread.is_alive():
        flask_thread = threading.Thread(target=run_flask)
        flask_thread.daemon = True
        flask_thread.start()
        server_status = 1  # 更新服务器状态为已运行
        write_log(log_text, "Flask 服务器已启动！访问 http://localhost:5001/")
    else:
        write_log(log_text, "Flask 服务器已经在运行中。")


def stop_flask(log_text=None):
    global server_status
    global flask_thread
    if flask_thread and flask_thread.is_alive():
        server_status = 0  # 更新服务器状态为未运行
        # 重置线程变量，下次启动时会创建新线程
        flask_thread = None
        write_log(log_text, "Flask 服务器已停止！")
    else:
        write_log(log_text, "Flask 服务器未运行。")


# 更新服务器状态指示器
def update_status_indicator(canvas):
    global server_status
    canvas.delete("status_indicator")
    if server_status == 1:
        # 绿色圆形表示运行中，去除黑边
        canvas.create_oval(5, 5, 25, 25, fill="#28a745", outline="", tags="status_indicator")
        # 添加白色中心点
        canvas.create_oval(10, 10, 20, 20, fill="white", outline="", tags="status_indicator")
    else:
        # 红色圆形表示未运行，去除黑边
        canvas.create_oval(5, 5, 25, 25, fill="#dc3545", outline="", tags="status_indicator")
        # 添加白色中心点
        canvas.create_oval(10, 10, 20, 20, fill="white", outline="", tags="status_indicator")
    canvas.after(1000, update_status_indicator, canvas)  # 每秒更新一次



def write_log(log_text, message):
    """写入日志信息到文本框"""
    if log_text:
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 根据消息内容设置颜色
        tag = "info"  # 默认信息标签
        if "error" in message.lower() or "exception" in message.lower() or "traceback" in message.lower():
            tag = "error"
        elif "warning" in message.lower() or "warn" in message.lower():
            tag = "warning"
        elif "success" in message.lower() or "已启动" in message or "已停止" in message:
            tag = "success"
        
        log_entry = f"[{timestamp}] {message}\n"
        
        log_text.config(state=tk.NORMAL)
        log_text.insert(tk.END, log_entry, tag)
        # 滚动到底部
        log_text.see(tk.END)
        log_text.config(state=tk.DISABLED)

def toggle_server(canvas, btn, log_text=None):
    global server_status
    if server_status == 0:
        start_flask(log_text)
        btn.config(
            text="停止服务器",
            bg="#dc3545",
            activebackground="#c82333"
        )
    else:
        stop_flask(log_text)
        btn.config(
            text="启动服务器",
            bg="#4a90e2",
            activebackground="#357abd"
        )
    update_status_indicator(canvas)



def center_window(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")



def create_gui():
    root = tk.Tk()
    root.title("NYM网盘服务器")
    center_window(root, 450, 600)
    
    # 设置窗口背景
    root.configure(bg="#f0f2f5")
    
    # 设置字体
    title_font = ("Microsoft YaHei", 14, "bold")
    label_font = ("Microsoft YaHei", 10)
    button_font = ("Microsoft YaHei", 11, "bold")
    info_font = ("Consolas", 10)

    # 创建标题区域
    title_frame = tk.Frame(root, bg="#f0f2f5")
    title_frame.pack(pady=20)
    
    title_label = tk.Label(title_frame, text="NYM网盘服务器", font=title_font, bg="#f0f2f5", fg="#4a90e2")
    title_label.pack()

    # 创建服务器状态指示
    status_frame = tk.Frame(root, bg="#f0f2f5")
    status_frame.pack(pady=15)

    status_label = tk.Label(status_frame, text="服务器状态:", font=label_font, bg="#f0f2f5", fg="#333")
    status_label.pack(side=tk.LEFT, padx=10)

    status_canvas = tk.Canvas(status_frame, width=30, height=30, bg="#f0f2f5", highlightthickness=0)
    status_canvas.pack(side=tk.LEFT)
    update_status_indicator(status_canvas)

    # 创建启动/停止按钮
    btn_frame = tk.Frame(root, bg="#f0f2f5")
    btn_frame.pack(pady=20)

    toggle_btn = tk.Button(
        btn_frame, 
        text="启动服务器", 
        command=lambda: toggle_server(status_canvas, toggle_btn), 
        width=22, 
        height=2, 
        font=button_font,
        bg="#4a90e2",
        fg="white",
        activebackground="#357abd",
        activeforeground="white",
        relief=tk.FLAT,
        borderwidth=0,
        cursor="hand2"
    )
    toggle_btn.pack()

    # 服务器信息显示
    info_frame = tk.Frame(root, bg="#f0f2f5")
    info_frame.pack(pady=15)

    info_label = tk.Label(info_frame, text="访问地址:", font=label_font, bg="#f0f2f5", fg="#333")
    info_label.pack(pady=(0, 10))

    # 创建信息卡片
    info_card = tk.Frame(info_frame, bg="white", relief=tk.RAISED, borderwidth=1)
    info_card.pack(padx=20)
    
    info_text = tk.Text(
        info_card, 
        width=45, 
        height=4, 
        wrap=tk.WORD, 
        font=info_font,
        bg="white",
        fg="#333",
        relief=tk.FLAT,
        borderwidth=0
    )
    info_text.pack(padx=15, pady=15)
    info_text.insert(tk.END, "http://localhost:5001/\nhttp://127.0.0.1:5001/\nhttp://[::1]:5001/\nhttp://192.168.0.107:5001/")
    info_text.config(state=tk.DISABLED)

    # 创建日志区域
    log_frame = tk.Frame(root, bg="#f0f2f5")
    log_frame.pack(pady=15, padx=20, fill=tk.X)
    
    log_label = tk.Label(log_frame, text="服务器日志:", font=label_font, bg="#f0f2f5", fg="#333")
    log_label.pack(pady=(0, 5), anchor=tk.W)
    
    # 创建日志文本框
    log_text = tk.Text(
        log_frame, 
        width=45, 
        height=7, 
        wrap=tk.WORD, 
        font=("Microsoft YaHei", 9),
        bg="white",
        fg="#333",
        relief=tk.FLAT,
        borderwidth=1,
        state=tk.DISABLED
    )
    log_text.pack(fill=tk.BOTH, expand=True)
    
    # 添加颜色标签
    log_text.tag_config("info", foreground="#333333")        # 普通信息 - 黑色
    log_text.tag_config("error", foreground="#dc3545")        # 错误信息 - 红色
    log_text.tag_config("warning", foreground="#ffc107")      # 警告信息 - 黄色
    log_text.tag_config("success", foreground="#28a745")     # 成功信息 - 绿色
    
    # 初始化并启动控制台重定向
    redirector = ConsoleRedirector(log_text)
    redirector.start()
    
    # 保存重定向器引用
    root.redirector = redirector
    
    # 创建底部信息
    footer_frame = tk.Frame(root, bg="#f0f2f5")
    footer_frame.pack(pady=10)
    
    footer_label = tk.Label(footer_frame, text="© 2026 NYM网盘", font=("Microsoft YaHei", 9), bg="#f0f2f5", fg="#999")
    footer_label.pack()
    
    # 更新按钮命令，传递log_text
    toggle_btn.config(command=lambda: toggle_server(status_canvas, toggle_btn, log_text))

    # 运行主循环
    root.mainloop()


class ConsoleRedirector:
    """将控制台输出重定向到GUI日志文本框"""
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.old_stdout = None
        self.old_stderr = None
        self.buffer = ""  # 缓冲区，用于收集不完整的消息
    
    def write(self, message):
        """写入消息到日志文本框"""
        if self.text_widget:
            # 将消息添加到缓冲区
            self.buffer += message
            
            # 当遇到换行符时，处理完整的消息
            if "\n" in self.buffer:
                lines = self.buffer.split("\n")
                for i, line in enumerate(lines):
                    # 处理除最后一行外的所有行（最后一行可能不完整）
                    if i < len(lines) - 1:
                        self._process_line(line)
                # 保留最后一行（可能不完整）在缓冲区中
                self.buffer = lines[-1]
    
    def _process_line(self, line):
        """处理单行完整的消息"""
        if line.strip():
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 根据消息内容设置颜色
            tag = "info"  # 默认信息标签
            if "error" in line.lower() or "exception" in line.lower() or "traceback" in line.lower():
                tag = "error"
            elif "warning" in line.lower() or "warn" in line.lower():
                tag = "warning"
            elif "success" in line.lower() or "已启动" in line or "已停止" in line:
                tag = "success"
            
            log_entry = f"[{timestamp}] {line}\n"
            
            self.text_widget.config(state="normal")
            self.text_widget.insert("end", log_entry, tag)
            self.text_widget.see("end")
            self.text_widget.config(state="disabled")
    
    def flush(self):
        """刷新输出"""
        # 处理缓冲区中剩余的内容
        if self.buffer.strip():
            self._process_line(self.buffer)
            self.buffer = ""
    
    def start(self):
        """开始重定向"""
        global sys
        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self
    
    def stop(self):
        """停止重定向"""
        global sys
        if self.old_stdout:
            sys.stdout = self.old_stdout
        if self.old_stderr:
            sys.stderr = self.old_stderr

# 运行GUI
if __name__ == "__main__":
    create_gui()