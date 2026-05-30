import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import importlib, subprocess, time, threading, json, os
from datetime import datetime
import traceback
import functools
import sys

# 全局错误处理装饰器
def handle_errors(func):
    """装饰器：捕获异常并输出到日志，防止程序崩溃"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # 获取异常信息
            error_type = type(e).__name__
            error_msg = str(e)
            error_traceback = traceback.format_exc()
            
            # 尝试获取GUI实例来输出日志
            try:
                # 检查args中是否有self参数，且self有add_log方法
                if args and hasattr(args[0], 'add_log'):
                    gui_instance = args[0]
                    gui_instance.add_log(f"🚨 程序异常 - {error_type}: {error_msg}", "CRITICAL")
                    gui_instance.add_log(f"📍 异常位置: {func.__name__} - {func.__module__}", "ERROR")
                    gui_instance.add_log(f"📋 异常堆栈:\n{error_traceback}", "ERROR")
                    gui_instance.update_status_info(f"错误: {error_type}")
                else:
                    # 如果无法获取GUI实例，输出到控制台
                    print(f"[CRITICAL] 程序异常 - {error_type}: {error_msg}")
                    print(f"[ERROR] 异常位置: {func.__name__} - {func.__module__}")
                    print(f"[ERROR] 异常堆栈:\n{error_traceback}")
            except:
                # 如果连日志输出都失败了，至少输出到控制台
                print(f"[CRITICAL] 程序异常 - {error_type}: {error_msg}")
                print(f"[ERROR] 异常位置: {func.__name__} - {func.__module__}")
                print(f"[ERROR] 异常堆栈:\n{error_traceback}")
            
            # 返回None或默认值，避免程序崩溃
            return None
    return wrapper

# 全局异常处理函数
def global_exception_handler(exc_type, exc_value, exc_traceback):
    """全局异常处理器"""
    if issubclass(exc_type, KeyboardInterrupt):
        # 允许Ctrl+C正常退出
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    try:
        # 尝试输出到日志
        if 'log_callback' in globals() and log_callback:
            log_callback(f"🚨 未捕获异常: {exc_type.__name__}: {exc_value}", "CRITICAL")
            log_callback(f"📋 异常详情:\n{error_msg}", "ERROR")
        else:
            print(f"[CRITICAL] 未捕获异常: {exc_type.__name__}: {exc_value}")
            print(f"[ERROR] 异常详情:\n{error_msg}")
    except:
        print(f"[CRITICAL] 未捕获异常: {exc_type.__name__}: {exc_value}")
        print(f"[ERROR] 异常详情:\n{error_msg}")

# 设置全局异常处理器
sys.excepthook = global_exception_handler

try:
    from pynput import mouse
    GLOBAL_MOUSE_SUPPORT = True
except ImportError:
    GLOBAL_MOUSE_SUPPORT = False

# 先尝试安装依赖，再导入模块
SparkWeb = None
@handle_errors
def install_dependencies():
    """使用importlib安装依赖库并尝试导入SparkWeb"""
    global SparkWeb, _dependencies_checked
    
    # 如果已经检查过依赖且成功，直接返回
    if _dependencies_checked and SparkWeb is not None:
        return True
    
    try:
        # 使用importlib动态导入库
        sparkdesk_module = importlib.import_module('sparkdesk_web.core')
        SparkWeb = sparkdesk_module.SparkWeb
        add_global_log("sparkdesk_web.core组件已经安装。", "SUCCESS")
        _dependencies_checked = True
        return True
    except ImportError:
        add_global_log("sparkdesk_web.core组件未安装,正在尝试安装...", "WARNING")
        try:
            # 安装依赖包
            packages = ['requests', 'pyhandytools', 'sparkdesk-api', 'pynput']
            add_global_log(f"正在安装依赖: {', '.join(packages)}", "INFO")
            subprocess.check_call(['pip3', 'install', '-i', 'https://mirrors.aliyun.com/pypi/simple'] + packages)
            
            # 安装后尝试再次动态导入
            try:
                sparkdesk_module = importlib.import_module('sparkdesk_web.core')
                SparkWeb = sparkdesk_module.SparkWeb
                add_global_log("sparkdesk_web.core组件安装成功。", "SUCCESS")
                _dependencies_checked = True
                return True
            except ImportError:
                # 直接安装sparkdesk_web模块
                add_global_log("尝试直接安装sparkdesk_web模块...", "INFO")
                subprocess.check_call(['pip3', 'install', '-i', 'https://mirrors.aliyun.com/pypi/simple', 'sparkdesk_web'])
                
                # 再次尝试动态导入
                sparkdesk_module = importlib.import_module('sparkdesk_web.core')
                SparkWeb = sparkdesk_module.SparkWeb
                add_global_log("sparkdesk_web模块安装成功。", "SUCCESS")
                _dependencies_checked = True
                return True
        except subprocess.CalledProcessError as e:
            add_global_log(f"依赖安装失败: {e}", "ERROR")
            add_global_log("请手动安装以下依赖: pip3 -i https://mirrors.aliyun.com/pypi/simple sparkdesk_web requests pyhandytools", "ERROR")
            return False

# 凭证存储文件
CREDENTIALS_FILE = 'sparkdesk_credentials.json'
# 更新间隔（秒），建议设置为小于凭证过期时间，这里设置为2小时
UPDATE_INTERVAL = 2 * 60 * 60

# 全局变量
sparkWeb = None
chat = None
log_callback = None
debug_mode = False  # Debug模式标志
_dependencies_checked = False  # 依赖检查标志，避免重复检查

@handle_errors
def set_log_callback(callback):
    """设置日志回调函数"""
    global log_callback
    log_callback = callback

@handle_errors
def set_debug_mode(enabled):
    """设置debug模式"""
    global debug_mode
    debug_mode = enabled
    add_global_log(f"Debug模式: {'开启' if enabled else '关闭'}", "INFO")

@handle_errors
def debug_log(message, level="DEBUG"):
    """debug日志函数，只有在debug模式下才输出"""
    global debug_mode
    if debug_mode:
        add_global_log(f"[DEBUG] {message}", level)

@handle_errors
def add_global_log(message, level="INFO"):
    """添加全局日志"""
    global log_callback
    print(f"[{level}] {message}")  # 同时输出到控制台
    if log_callback:
        log_callback(message, level)

credentials = {
    'cookie': "JSESSIONID=F603D5F34258CF971EE8913F90675829; d_d_app_ver=1.4.0; d_d_ci=23914129-a0c1-60a5-901d-743faeb67bd4; ssoSessionId=f26fda01-36a9-47b6-b62c-2d2e7c29497c; account_id=21246793392; ui=21246793392; daas_st={%22sdk_ver%22:%221.3.9%22%2C%22status%22:%220%22}; appid=fc6576da65; gt_local_id=gqZJVb5BwcOMrTIrBcvNr66tIfvEkKpOGJSQbFBWAivd2a1UuNMIwA==",
    'fd': "187907",
    'GtToken': "RzAwAGPl9Lq6UL8EurNvu79/fLwfi135ybHTQcoeeq2kPcBBzmE7v3mnkf4x6RpkJ+06oojZutWWmP4lgIz299br8TFh2Qxnq/b1IJz0qJZSCsXoAtRI8R2egBB1jk8fdatmpc6jePvG7+opW8OtrSbmhCSGhakZc0vJlAU5SHPA26FTgcspZotQvnHl0c5ea9prex+kLADHjwtAq+FcZRMnePrcLDM4WDDckfON7xFE3G/e8UKMWelUC5m+WMTS7V5LiDwOh3tBTKXxrh60d9qP7FJQKgcBW6fb5Hn/NORzgTud2dV9oq1h5oaM1++CuRMOj+QaF0jMuHGcqZO81Mdj06q88Q7HB2xdMrByOE4Aku3rg6cTsttfjTqW902w9bFioaFghr2zFS2Ki9UtScywgWaBmDb2TdeTsN9OKE3+y6ljTsgthK58KOJ1Zv/imOsszsWJCv+Q1wbHdvJYY2K5FHMzuxqkeNvl3CSfXncf3EIIoMzbl3o9OFCJXMIjDvvFfQmbQmQzPMoeWZ8K3JPhRMkWFAu1w+X6MQcvxYxJDt+ctTruhjK6W2+yGLnFfxqaRhR6N0unaoDsZDV2QAMoCld3Iy9BSqZrNQPLPJvFtSG9+OKpkqQP3Bho8NGTrkqof2sgPUUu3l0hC/f1LzWE3F1ui0QUCw4/TFGeBYWrI9oQC++iViaBCmq+O3TePgXe9pFItJ5P33U7upgBXDlW1kBBSSeY6GF7+QvlOcAAd67hc4wMnE1alfyhEm7W54uy3g5qEfmp/4eLeE9PqB0s0zT4RJmKnzWjyxiwuFmfiX9JWetnkCWgWcC5Mu98b/3BBVFM7JhmIe+/HkYGOyCJZFOStWx3JITCAeoCUJBaWov0wsg7M5sKsJw/WkV1giHVFIE1jngKoOOqstfhbF88Kg93K0F6dDPoJU7k+FBtd3B72Sexi6kXcp7UG32dPzE6wmLcSQgQ27/0xPGbsjzTTYU7BsV1wWvP48pJvBF2LtQ/COBRNvLS/GQC741Ooa+qAcy6tswFcURxjHoGjkyZXzFVhEeH6TwIyCzI2Uqwvmnvu+najcyoSh2KSqmCWvj8zCkWW+/wqS+5ZtXhKMsZuCp",
    'update_time': time.time()
}

@handle_errors
def load_credentials():
    """从文件加载凭证"""
    global credentials
    try:
        if os.path.exists(CREDENTIALS_FILE):
            with open(CREDENTIALS_FILE, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                # 确保所有必需的字段都存在
                if all(key in loaded for key in ['cookie', 'fd', 'GtToken']):
                    credentials = loaded
                    add_global_log("从文件加载凭证成功", "SUCCESS")
                    return True
        return False
    except Exception as e:
        add_global_log(f"加载凭证文件失败: {e}", "ERROR")
        return False

@handle_errors
def save_credentials():
    """保存凭证到文件"""
    try:
        with open(CREDENTIALS_FILE, 'w', encoding='utf-8') as f:
            json.dump(credentials, f, ensure_ascii=False, indent=2)
        add_global_log(f"凭证已保存到 {CREDENTIALS_FILE}", "SUCCESS")
    except Exception as e:
        add_global_log(f"保存凭证失败: {e}", "ERROR")

@handle_errors
def update_credentials():
    """更新凭证的函数"""
    global credentials, sparkWeb, chat
    
    # 这里应该实现获取新凭证的逻辑
    # 由于获取新凭证通常需要手动从浏览器中提取，这里提供一个交互式输入方式
    print("\n=== 开始更新科大讯飞星火模型凭证 ===")
    print("请从浏览器中复制新的凭证信息")
    add_global_log("开始更新科大讯飞星火模型凭证", "INFO")
    
    try:
        # 获取用户输入的新凭证
        new_cookie = input("请输入新的cookie (直接回车使用当前值): ")
        new_fd = input("请输入新的fd (直接回车使用当前值): ")
        new_gt_token = input("请输入新的GtToken (直接回车使用当前值): ")
        
        # 更新凭证（如果用户提供了新值）
        if new_cookie:
            credentials['cookie'] = new_cookie
        if new_fd:
            credentials['fd'] = new_fd
        if new_gt_token:
            credentials['GtToken'] = new_gt_token
        
        credentials['update_time'] = time.time()
        
        # 保存到文件
        save_credentials()
        
        # 更新SparkWeb实例
        add_global_log("正在更新SparkWeb实例...", "INFO")
        sparkWeb = SparkWeb(
            cookie=credentials['cookie'],
            fd=credentials['fd'],
            GtToken=credentials['GtToken']
        )
        chat = sparkWeb.create_continuous_chat()
        
        add_global_log("凭证更新成功！", "SUCCESS")
        return True
    except Exception as e:
        add_global_log(f"更新凭证失败: {e}", "ERROR")
        return False

@handle_errors
def initialize_sparkweb():
    """初始化SparkWeb实例"""
    global sparkWeb, chat
    
    # 尝试加载保存的凭证
    load_credentials()
    
    # 初始化SparkWeb实例
    try:
        sparkWeb = SparkWeb(
            cookie=credentials['cookie'],
            fd=credentials['fd'],
            GtToken=credentials['GtToken']
        )
        chat = sparkWeb.create_continuous_chat()
        add_global_log("SparkWeb实例初始化成功", "SUCCESS")
        return True
    except Exception as e:
        add_global_log(f"初始化SparkWeb失败: {e}", "ERROR")
        # 尝试更新凭证
        return update_credentials()

class SparkDeskGUI:
    @handle_errors
    def __init__(self, root):
        self.root = root
        self.root.title("科大讯飞星火模型 GUI")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # 设置样式
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # 初始化变量
        self.is_processing = False
        self.debug_mode = False  # GUI实例的debug模式变量
        self.global_mouse_listener = None  # 全局鼠标监听器
        self.global_mouse_enabled = False  # 全局鼠标监听状态
        
        # 创建主框架（这会创建log_display）
        self.create_main_frame()
        
        # 居中显示窗口
        self.center_window()
        
        # 设置全局日志回调（在创建主框架后设置）
        set_log_callback(self.add_log)
        
        # 添加初始化日志（在创建主框架后添加）
        self.add_log("星火大模型GUI启动成功", "SUCCESS")
        self.add_log(f"窗口大小: {self.root.geometry()}", "INFO")
        self.add_log("窗口已居中显示", "INFO")
        
        # 初始化SparkWeb
        self.initialize_sparkweb_gui()
        
        # 绑定窗口级别的鼠标事件
        self.root.bind('<Button-1>', self.on_window_click)
        self.root.bind('<Motion>', self.on_mouse_motion)
        
        # 检查全局鼠标支持并初始化
        if GLOBAL_MOUSE_SUPPORT:
            self.add_log("检测到全局鼠标监听支持", "SUCCESS")
            # 只有在debug模式下才显示鼠标坐标按钮
            if self.debug_mode:
                self.coords_button.pack(side=tk.LEFT, padx=5)
        else:
            self.add_log("未安装pynput库，无法支持全局鼠标监听", "WARNING")
            self.add_log("请运行: pip3 -i https://pypi.tuna.tsinghua.edu.cn/simple pynput", "INFO")
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 启动定时更新线程
        self.start_update_thread()
    
    @handle_errors
    def center_window(self):
        """将窗口居中显示在屏幕上"""
        # 更新窗口以获取正确的尺寸
        self.root.update_idletasks()
        
        # 获取窗口的宽度和高度
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        
        # 获取屏幕的宽度和高度
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 计算窗口在屏幕中央的位置
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # 设置窗口位置
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
    @handle_errors
    def create_main_frame(self):
        """创建主界面框架"""
        # 创建工具栏
        self.create_toolbar()
        
        # 创建主内容区域
        self.create_content_area()
        
        # 创建状态栏
        self.create_status_bar()
        
    @handle_errors
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)
        
        # 文件操作按钮组
        ttk.Button(toolbar, text="加载对话", command=self.load_conversation).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="保存对话", command=self.save_conversation).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="清除对话", command=self.clear_conversation).pack(side=tk.LEFT, padx=2)        
        ttk.Button(toolbar, text="凭证设置", command=self.show_settings_dialog).pack(side=tk.LEFT, padx=2)
        
        # 分隔符
        ttk.Separator(toolbar, orient='vertical').pack(side=tk.LEFT, padx=10, fill=tk.Y)
        
        # Debug模式复选框
        self.debug_var = tk.BooleanVar(value=self.debug_mode)
        ttk.Checkbutton(
            toolbar,
            text="Debug模式",
            variable=self.debug_var,
            command=self.toggle_debug_mode
        ).pack(side=tk.LEFT, padx=5)
        
        # 显示鼠标坐标按钮（初始隐藏）
        self.show_coords_var = tk.BooleanVar(value=False)
        self.coords_button = ttk.Checkbutton(
            toolbar,
            text="显示鼠标坐标",
            variable=self.show_coords_var,
            command=self.toggle_mouse_coords,
            width=12
        )
        # 初始时隐藏此按钮，只有在debug模式下才显示
        if not self.debug_mode:
            self.coords_button.pack_forget()
        
        # 右侧分隔符
        ttk.Separator(toolbar, orient='vertical').pack(side=tk.RIGHT, padx=10, fill=tk.Y)
        
        # 退出按钮（放在右上角）
        exit_button = ttk.Button(
            toolbar,
            text="退出",
            command=self.root.quit,
            width=6
        )
        exit_button.pack(side=tk.RIGHT, padx=2)
        
        # 关于按钮（放在右上角）
        about_button = ttk.Button(
            toolbar,
            text="关于",
            command=self.show_about,
            width=6
        )
        about_button.pack(side=tk.RIGHT, padx=2)
        
        # 状态标签
        self.status_label = ttk.Label(toolbar, text="状态: 未连接", foreground="red")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
    @handle_errors
    def create_content_area(self):
        """创建主内容区域"""
        # 创建主要的水平分割窗口（左侧：对话和输入，右侧：日志）
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左侧区域（包含对话记录和输入区域）
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=3)  # 恢复原始权重
        
        # 创建垂直分割窗口用于分割聊天区域和输入区域
        left_paned = ttk.PanedWindow(left_frame, orient=tk.VERTICAL)
        left_paned.pack(fill=tk.BOTH, expand=True)
        
        # 聊天显示区域
        chat_frame = ttk.LabelFrame(left_paned, text="对话记录", padding=5)
        left_paned.add(chat_frame, weight=3)
        
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame, 
            wrap=tk.WORD, 
            font=('Microsoft YaHei UI', 11),
            state=tk.DISABLED,
            bg='#f8f9fa'
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
        # 绑定聊天区域的鼠标事件
        self.chat_display.bind('<Button-1>', self.on_chat_click)
        self.chat_display.bind('<Motion>', self.on_mouse_motion)
        
        # 输入区域
        input_frame = ttk.LabelFrame(left_paned, text="请输入你的问题", padding=5)
        left_paned.add(input_frame, weight=1)
        
        # 输入文本框
        self.input_text = scrolledtext.ScrolledText(
            input_frame,
            wrap=tk.WORD,
            font=('Microsoft YaHei UI', 11),
            height=4
        )
        self.input_text.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # 绑定回车键发送消息 - 修改为Enter键发送
        self.input_text.bind('<Return>', self.send_message)
        # 绑定Ctrl+Enter换行
        self.input_text.bind('<Control-Return>', self.insert_newline)
        # 绑定快捷键
        self.root.bind('<Control-l>', lambda e: self.get_log_area_info() if self.debug_mode else None)  # Ctrl+L获取日志区信息（仅debug模式）
        self.root.bind('<Control-d>', lambda e: (self.debug_var.set(not self.debug_var.get()), self.toggle_debug_mode()))  # Ctrl+D切换debug模式
        
        # 绑定输入区域的鼠标事件
        self.input_text.bind('<Button-1>', self.on_input_click)
        self.input_text.bind('<Motion>', self.on_mouse_motion)
        
        # 按钮框架
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill=tk.X)
        
        # 发送按钮 - 更新快捷键提示
        self.send_button = ttk.Button(
            button_frame, 
            text="发送 (Enter)", 
            command=self.send_message
        )
        self.send_button.pack(side=tk.RIGHT, padx=5)
        
        # 清除输入按钮
        ttk.Button(
            button_frame, 
            text="清除输入", 
            command=self.clear_input
        ).pack(side=tk.RIGHT, padx=5)
        
        # 右侧日志区域
        log_frame = ttk.LabelFrame(main_paned, text="日志", padding=5)
        main_paned.add(log_frame, weight=1)
        
        # 日志显示区域
        self.log_display = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            font=('Consolas', 10),
            state=tk.DISABLED,
            bg='#2b2b2b',              # 深色背景
            fg='#d4d4d4',              # 浅色文字
            insertbackground='#ffffff', # 光标颜色
            selectbackground='#555555', # 选中背景
            selectforeground='#ffffff', # 选中文字
            relief=tk.FLAT,            # 平坦边框
            borderwidth=0,             # 无边框
            height=20,
            padx=5,                    # 内边距
            pady=3                     # 内边距
        )
        self.log_display.pack(fill=tk.BOTH, expand=True)
        
        # 配置日志区域的默认标签样式
        self.log_display.tag_config("timestamp", 
            foreground="#888888",               # 灰色时间戳
            font=('Consolas', 9, 'normal'))     # 小号等宽字体
        
        self.log_display.tag_config("level", 
            font=('Arial', 9, 'bold'),          # 粗体级别标签
            spacing1=2)                          # 上间距
        
        # 绑定日志区域的鼠标事件
        self.log_display.bind('<Motion>', self.on_mouse_motion)
        
        # 日志控制按钮
        log_button_frame = ttk.Frame(log_frame)
        log_button_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(
            log_button_frame,
            text="清除日志",
            command=self.clear_log,
            width=8
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            log_button_frame,
            text="保存日志",
            command=self.save_log,
            width=8
        ).pack(side=tk.LEFT, padx=2)
        
        # 自动滚动选项
        self.auto_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            log_button_frame,
            text="自动滚动",
            variable=self.auto_scroll_var
        ).pack(side=tk.RIGHT, padx=5)
        
        # 设置初始分隔位置，让日志窗口初始宽度较小
        self.root.update_idletasks()  # 确保所有组件都已渲染
        total_width = main_paned.winfo_width()
        if total_width > 0:
            # 设置日志窗口宽度为315像素
            sash_position = total_width - 350
            main_paned.sashpos(0, sash_position)  # 使用正确的sashpos方法
        
    @handle_errors
    def create_status_bar(self):
        """创建状态栏"""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 状态信息
        self.status_info = ttk.Label(status_frame, text="就绪", relief=tk.SUNKEN)
        self.status_info.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2, pady=2)
        
        # 程序标识
        app_label = ttk.Label(status_frame, text="By:NanYanM", relief=tk.SUNKEN, foreground="#0066cc")
        app_label.pack(side=tk.RIGHT, padx=2, pady=2)
        
        # 时间显示
        self.time_label = ttk.Label(status_frame, text="", relief=tk.SUNKEN)
        self.time_label.pack(side=tk.RIGHT, padx=2, pady=2)
        
        # 更新时间显示
        self.update_time_display()
        
        # 绑定全局快捷键
        self.root.bind('<Control-l>', lambda e: self.get_log_area_info() if self.debug_mode else None)  # Ctrl+L获取日志区信息（仅debug模式）
        self.root.bind('<Control-d>', lambda e: (self.debug_var.set(not self.debug_var.get()), self.toggle_debug_mode()))  # Ctrl+D切换debug模式
        
        if self.debug_mode:
            self.add_log("全局快捷键已绑定: Ctrl+L(获取日志区信息) Ctrl+D(切换Debug模式)", "DEBUG")
        
    @handle_errors
    def initialize_sparkweb_gui(self):
        """GUI版本的SparkWeb初始化"""
        if self.debug_mode:
            self.add_log("DEBUG: 开始SparkWeb GUI初始化流程", "INFO")
            
        def init_thread():
            try:
                if self.debug_mode:
                    self.add_log("DEBUG: 开始检查和安装依赖", "INFO")
                    start_time = time.time()
                    
                # 安装依赖
                if not install_dependencies():
                    if self.debug_mode:
                        self.add_log("DEBUG: 依赖安装失败", "ERROR")
                    self.root.after(0, lambda: self.show_error("依赖安装失败"))
                    return
                
                if self.debug_mode:
                    end_time = time.time()
                    self.add_log(f"DEBUG: 依赖安装完成 - 耗时: {end_time - start_time:.2f}秒", "SUCCESS")
                    self.add_log("DEBUG: 开始初始化SparkWeb", "INFO")
                    start_time = time.time()
                
                # 初始化SparkWeb
                if not initialize_sparkweb():
                    if self.debug_mode:
                        self.add_log("DEBUG: SparkWeb初始化失败", "ERROR")
                    self.root.after(0, lambda: self.show_error("SparkWeb初始化失败"))
                    return
                
                if self.debug_mode:
                    end_time = time.time()
                    self.add_log(f"DEBUG: SparkWeb初始化成功 - 耗时: {end_time - start_time:.2f}秒", "SUCCESS")
                    self.add_log("DEBUG: 全局变量状态检查", "INFO")
                    self.add_log(f"DEBUG: sparkWeb类型: {type(sparkWeb)}", "INFO")
                    self.add_log(f"DEBUG: chat类型: {type(chat)}", "INFO")
                
                # 更新状态
                self.root.after(0, self.update_status_connected)
                
            except Exception as e:
                if self.debug_mode:
                    self.add_log(f"DEBUG: 初始化异常 - {type(e).__name__}: {str(e)}", "ERROR")
                    import traceback
                    self.add_log(f"DEBUG: 异常堆栈: {traceback.format_exc()}", "ERROR")
                self.root.after(0, lambda: self.show_error(f"初始化失败: {str(e)}"))
        
        # 在后台线程中初始化
        if self.debug_mode:
            self.add_log("DEBUG: 启动后台初始化线程", "INFO")
        threading.Thread(target=init_thread, daemon=True).start()
        self.update_status_info("正在初始化...")
        
    @handle_errors
    def update_status_connected(self):
        """更新连接状态"""
        self.status_label.config(text="状态: 已连接", foreground="green")
        self.update_status_info("就绪")
        self.add_message("系统", "科大讯飞星火模型已成功连接！")
        
    @handle_errors
    def update_status_info(self, message):
        """更新状态信息"""
        self.status_info.config(text=message)
        
    @handle_errors
    def update_time_display(self):
        """更新时间显示"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_time_display)
        
    @handle_errors
    def insert_newline(self, event=None):
        """插入换行符 - Ctrl+Enter功能"""
        self.input_text.insert(tk.INSERT, "\n")
        return "break"  # 阻止默认行为
        
    @handle_errors
    def send_message(self, event=None):
        """发送消息"""
        if self.is_processing:
            if self.debug_mode:
                self.add_log("⏳ DEBUG: 消息发送被阻止，正在处理中", "WARNING")
            messagebox.showwarning("提示", "正在处理中，请稍候...")
            return
            
        user_input = self.input_text.get(1.0, tk.END).strip()
        if not user_input:
            if self.debug_mode:
                self.add_log("DEBUG: 用户输入为空，消息发送被阻止", "WARNING")
            return
        
        # Debug模式下记录详细信息
        if self.debug_mode:
            self.add_log(f"📤 DEBUG: 准备发送消息 - 长度: {len(user_input)} 字符", "INFO")
            self.add_log(f"DEBUG: 消息内容预览: {user_input[:100]}{'...' if len(user_input) > 100 else ''}", "INFO")
            self.add_log(f"DEBUG: 当前处理状态: is_processing={self.is_processing}", "INFO")
            
        # 清空输入框
        self.clear_input()
        
        # 显示用户消息
        self.add_message("用户", user_input)
        
        # 开始处理
        self.is_processing = True
        self.send_button.config(state=tk.DISABLED)
        self.update_status_info("正在思考...")
        
        if self.debug_mode:
            self.add_log("🌐 DEBUG: 开始后台线程处理请求", "NETWORK")
        
        # 在后台线程中处理请求
        @handle_errors
        def process_request():
            try:
                if self.debug_mode:
                    self.add_log("DEBUG: 检查聊天对象状态", "INFO")
                    
                if chat is None:
                    if self.debug_mode:
                        self.add_log("DEBUG: 聊天对象为空，初始化失败", "ERROR")
                    self.root.after(0, lambda: self.show_error("聊天对象未初始化"))
                    return
                
                if self.debug_mode:
                    self.add_log("DEBUG: 开始调用chat.chat()方法", "INFO")
                    start_time = time.time()
                    
                response = chat.chat(user_input)
                
                if self.debug_mode:
                    end_time = time.time()
                    duration = end_time - start_time
                    self.add_log(f"DEBUG: 聊天请求完成 - 耗时: {duration:.2f}秒", "SUCCESS")
                    self.add_log(f"DEBUG: 响应长度: {len(response) if response else 0} 字符", "INFO")
                    if response:
                        self.add_log(f"DEBUG: 响应内容预览: {response[:100]}{'...' if len(response) > 100 else ''}", "INFO")
                
                self.root.after(0, lambda: self.add_message("星火", response))
                
            except Exception as e:
                error_msg = f"请求失败: {str(e)}"
                if self.debug_mode:
                    self.add_log(f"🚨 DEBUG: 请求异常 - {type(e).__name__}: {str(e)}", "CRITICAL")
                    import traceback
                    self.add_log(f"DEBUG: 异常堆栈: {traceback.format_exc()}", "ERROR")
                    
                self.root.after(0, lambda: self.add_message("系统", error_msg))
                self.root.after(0, lambda: self.show_error(error_msg))
                
            finally:
                # 恢复状态
                if self.debug_mode:
                    self.add_log("DEBUG: 重置处理状态", "INFO")
                self.root.after(0, self.reset_processing_state)
        
        threading.Thread(target=process_request, daemon=True).start()
        
    @handle_errors
    def reset_processing_state(self):
        """重置处理状态"""
        self.is_processing = False
        self.send_button.config(state=tk.NORMAL)
        self.update_status_info("就绪")
        
    @handle_errors
    def add_message(self, sender, message):
        """添加消息到聊天显示区域"""
        self.chat_display.config(state=tk.NORMAL)
        
        # 添加时间戳
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 根据发送者设置不同的颜色
        if sender == "用户":
            tag = "user"
            self.chat_display.tag_config("user", foreground="#0066cc", font=('Microsoft YaHei UI', 11, 'bold'))
        elif sender == "星火":
            tag = "assistant"
            self.chat_display.tag_config("assistant", foreground="#009900", font=('Microsoft YaHei UI', 11))
        else:
            tag = "system"
            self.chat_display.tag_config("system", foreground="#666666", font=('Microsoft YaHei UI', 10, 'italic'))
        
        # 插入消息
        self.chat_display.insert(tk.END, f"[{timestamp}] {sender}: ", tag)
        self.chat_display.insert(tk.END, f"{message}\n\n", tag)
        
        # 滚动到底部
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
    @handle_errors
    def clear_input(self):
        """清空输入框"""
        self.input_text.delete(1.0, tk.END)
        self.input_text.focus_set()
        
    @handle_errors
    def clear_conversation(self):
        """清除对话记录"""
        result = messagebox.askyesno("确认", "确定要清除所有对话记录吗？")
        if result:
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.delete(1.0, tk.END)
            self.chat_display.config(state=tk.DISABLED)
            self.add_message("系统", "对话记录已清除")
            
    @handle_errors
    def save_conversation(self):
        """保存对话记录"""
        try:
            # 创建临时父窗口用于文件对话框居中
            temp_root = tk.Toplevel(self.root)
            temp_root.withdraw()  # 隐藏窗口
            
            # 计算主窗口中心位置
            main_x = self.root.winfo_x()
            main_y = self.root.winfo_y()
            main_width = self.root.winfo_width()
            main_height = self.root.winfo_height()
            
            # 设置临时窗口位置在主窗口中心
            temp_root.geometry(f"1x1+{main_x + main_width//2}+{main_y + main_height//2}")
            
            filename = filedialog.asksaveasfilename(
                parent=temp_root,
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
                initialfile=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            
            # 销毁临时窗口
            temp_root.destroy()
            
            if filename:
                content = self.chat_display.get(1.0, tk.END)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("成功", f"对话记录已保存到:\n{filename}")
                return True
                
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")
            return False
        return False
            
    @handle_errors
    def load_conversation(self):
        """加载对话记录"""
        try:
            # 创建临时父窗口用于文件对话框居中
            temp_root = tk.Toplevel(self.root)
            temp_root.withdraw()  # 隐藏窗口
            
            # 计算主窗口中心位置
            main_x = self.root.winfo_x()
            main_y = self.root.winfo_y()
            main_width = self.root.winfo_width()
            main_height = self.root.winfo_height()
            
            # 设置临时窗口位置在主窗口中心
            temp_root.geometry(f"1x1+{main_x + main_width//2}+{main_y + main_height//2}")
            
            filename = filedialog.askopenfilename(
                parent=temp_root,
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
            )
            
            # 销毁临时窗口
            temp_root.destroy()
            
            if filename:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                self.chat_display.config(state=tk.NORMAL)
                self.chat_display.delete(1.0, tk.END)
                self.chat_display.insert(1.0, content)
                self.chat_display.config(state=tk.DISABLED)
                messagebox.showinfo("成功", "对话记录已加载")
                
        except Exception as e:
            messagebox.showerror("错误", f"加载失败: {str(e)}")
            self.add_log(f"加载对话记录失败: {str(e)}", "ERROR")
            
    @handle_errors
    def show_settings_dialog(self):
        """显示凭证设置对话框"""
        # 计算居中位置
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 500) // 2
        y = (screen_height - 450) // 2
        
        # 创建对话框时立即设置位置
        dialog = tk.Toplevel(self.root)
        dialog.title("凭证设置")
        dialog.geometry(f"500x450+{x}+{y}")
        dialog.resizable(False, False)
        
        # 使对话框模态
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 确保窗口不会闪现
        dialog.withdraw()  # 先隐藏
        dialog.update_idletasks()
        dialog.deiconify()  # 再显示
        
        # 创建设置界面
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Cookie设置
        ttk.Label(main_frame, text="Cookie:", font=('Microsoft YaHei UI', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=5)
        cookie_text = scrolledtext.ScrolledText(main_frame, height=6, width=55)
        cookie_text.grid(row=1, column=0, columnspan=2, pady=5, padx=5, sticky=tk.EW)
        cookie_text.insert(1.0, credentials.get('cookie', ''))
        
        # FD设置
        ttk.Label(main_frame, text="FD:", font=('Microsoft YaHei UI', 10, 'bold')).grid(row=2, column=0, sticky=tk.W, pady=5)
        fd_entry = ttk.Entry(main_frame, width=55)
        fd_entry.grid(row=3, column=0, columnspan=2, pady=5, padx=5, sticky=tk.EW)
        fd_entry.insert(0, credentials.get('fd', ''))
        
        # GtToken设置
        ttk.Label(main_frame, text="GtToken:", font=('Microsoft YaHei UI', 10, 'bold')).grid(row=4, column=0, sticky=tk.W, pady=5)
        token_text = scrolledtext.ScrolledText(main_frame, height=6, width=55)
        token_text.grid(row=5, column=0, columnspan=2, pady=5, padx=5, sticky=tk.EW)
        token_text.insert(1.0, credentials.get('GtToken', ''))
        
        # 更新时间显示
        update_time = credentials.get('update_time', 0)
        if update_time:
            time_str = datetime.fromtimestamp(update_time).strftime('%Y-%m-%d %H:%M:%S')
            ttk.Label(main_frame, text=f"上次更新时间: {time_str}").grid(row=6, column=0, columnspan=2, pady=10)
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=2, pady=10)
        
        def save_settings():
            """保存凭证设置"""
            try:
                if self.debug_mode:
                    self.add_log("DEBUG: 开始保存凭证设置", "INFO")
                    
                new_cookie = cookie_text.get(1.0, tk.END).strip()
                new_fd = fd_entry.get().strip()
                new_token = token_text.get(1.0, tk.END).strip()
                
                if self.debug_mode:
                    self.add_log(f"DEBUG: 凭证信息检查 - Cookie长度: {len(new_cookie)}, FD长度: {len(new_fd)}, Token长度: {len(new_token)}", "INFO")
                
                if new_cookie:
                    credentials['cookie'] = new_cookie
                    if self.debug_mode:
                        self.add_log("DEBUG: Cookie已更新", "SUCCESS")
                if new_fd:
                    credentials['fd'] = new_fd
                    if self.debug_mode:
                        self.add_log("DEBUG: FD已更新", "SUCCESS")
                if new_token:
                    credentials['GtToken'] = new_token
                    if self.debug_mode:
                        self.add_log("DEBUG: GtToken已更新", "SUCCESS")
                    
                credentials['update_time'] = time.time()
                save_credentials()
                
                if self.debug_mode:
                    self.add_log("DEBUG: 凭证已保存到文件", "SUCCESS")
                    self.add_log("DEBUG: 开始重新初始化SparkWeb", "INFO")
                
                # 重新初始化SparkWeb
                def reinit():
                    try:
                        if self.debug_mode:
                            self.add_log("DEBUG: 创建新的SparkWeb实例", "INFO")
                            start_time = time.time()
                            
                        global sparkWeb, chat
                        sparkWeb = SparkWeb(
                            cookie=credentials['cookie'],
                            fd=credentials['fd'],
                            GtToken=credentials['GtToken']
                        )
                        
                        if self.debug_mode:
                            end_time = time.time()
                            self.add_log(f"DEBUG: SparkWeb实例创建完成 - 耗时: {end_time - start_time:.2f}秒", "SUCCESS")
                            self.add_log("DEBUG: 创建连续聊天对象", "INFO")
                            start_time = time.time()
                        
                        chat = sparkWeb.create_continuous_chat()
                        
                        if self.debug_mode:
                            end_time = time.time()
                            self.add_log(f"DEBUG: 连续聊天对象创建完成 - 耗时: {end_time - start_time:.2f}秒", "SUCCESS")
                        
                        self.root.after(0, self.update_status_connected)
                        self.root.after(0, lambda: messagebox.showinfo("成功", "凭证已更新并重新连接"))
                        
                    except Exception as e:
                        if self.debug_mode:
                            self.add_log(f"DEBUG: 重新初始化失败 - {type(e).__name__}: {str(e)}", "ERROR")
                            import traceback
                            self.add_log(f"DEBUG: 异常堆栈: {traceback.format_exc()}", "ERROR")
                        self.root.after(0, lambda: messagebox.showerror("错误", f"重新连接失败: {str(e)}"))
                
                threading.Thread(target=reinit, daemon=True).start()
                dialog.destroy()
                
            except Exception as e:
                if self.debug_mode:
                    self.add_log(f"DEBUG: 保存设置异常 - {type(e).__name__}: {str(e)}", "ERROR")
                messagebox.showerror("错误", f"保存设凭证设置失败: {str(e)}")
        
        ttk.Button(button_frame, text="保存", command=save_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
    @handle_errors
    def toggle_debug_mode(self):
        """切换Debug模式"""
        # 从复选框获取状态
        self.debug_mode = self.debug_var.get()
        global debug_mode
        debug_mode = self.debug_mode
        
        if self.debug_mode:
            self.add_log("Debug模式已开启", "SUCCESS")
            self.add_log("将显示详细的调试信息", "DEBUG")
            
            # 获取并显示日志区宽度信息
            self.get_log_area_info()
            
            # 显示"显示鼠标坐标"按钮，插入到Debug模式复选框后面
            self.coords_button.pack(side=tk.LEFT, padx=5)
        else:
            self.add_log("Debug模式已关闭", "WARNING")
            self.add_log("已停止显示调试信息", "DEBUG")
            # 隐藏"显示鼠标坐标"按钮并重置状态
            self.coords_button.pack_forget()
            self.show_coords_var.set(False)
            self.add_log("鼠标坐标显示已自动关闭", "SYSTEM")
            # 停止全局鼠标监听
            self.disable_global_mouse()
    
    @handle_errors
    def get_log_area_info(self):
        """获取日志区域的详细信息"""
        try:
            # 确保窗口已经渲染
            self.root.update_idletasks()
            
            # 获取日志显示区域的基本信息
            log_width = self.log_display.winfo_width()
            log_height = self.log_display.winfo_height()
            log_req_width = self.log_display.winfo_reqwidth()
            log_req_height = self.log_display.winfo_reqheight()
            
            # 获取日志框架的信息
            log_frame_width = self.log_display.master.winfo_width()
            log_frame_height = self.log_display.master.winfo_height()
            
            # 获取主分割面板的信息
            main_paned_width = self.log_display.master.master.winfo_width()
            main_paned_height = self.log_display.master.master.winfo_height()
            
            # 获取窗口总信息
            window_width = self.root.winfo_width()
            window_height = self.root.winfo_height()
            
            # 计算日志区占比
            width_percentage = (log_width / window_width * 100) if window_width > 0 else 0
            height_percentage = (log_height / window_height * 100) if window_height > 0 else 0
            
            self.add_log("📏 日志区域尺寸信息:", "DEBUG")
            self.add_log(f"   ├─ 日志显示区实际宽度: {log_width}px (请求宽度: {log_req_width}px)", "DEBUG")
            self.add_log(f"   ├─ 日志显示区实际高度: {log_height}px (请求高度: {log_req_height}px)", "DEBUG")
            self.add_log(f"   ├─ 日志框架宽度: {log_frame_width}px, 高度: {log_frame_height}px", "DEBUG")
            self.add_log(f"   ├─ 主分割面板宽度: {main_paned_width}px, 高度: {main_paned_height}px", "DEBUG")
            self.add_log(f"   ├─ 窗口总宽度: {window_width}px, 总高度: {window_height}px", "DEBUG")
            self.add_log(f"   └─ 日志区占比: 宽度 {width_percentage:.1f}%, 高度 {height_percentage:.1f}%", "DEBUG")
            
            # 获取字体信息
            font_info = self.log_display.cget("font")
            self.add_log(f"日志区字体设置: {font_info}", "DEBUG")
            
            # 获取滚动条信息
            try:
                scrollbar_width = 0
                for child in self.log_display.master.winfo_children():
                    if isinstance(child, ttk.Scrollbar):
                        scrollbar_width = child.winfo_width()
                        break
                self.add_log(f"滚动条宽度: {scrollbar_width}px", "DEBUG")
            except:
                self.add_log("滚动条信息获取失败", "DEBUG")
            
            # 获取内边距信息
            padx = self.log_display.cget("padx")
            pady = self.log_display.cget("pady")
            self.add_log(f"日志区内边距: 水平 {padx}px, 垂直 {pady}px", "DEBUG")
            
        except Exception as e:
            self.add_log(f"获取日志区域信息失败: {str(e)}", "ERROR")
    
    @handle_errors
    def on_window_click(self, event):
        """处理窗口点击事件"""
        if self.debug_mode:
            current_time = datetime.now()
            date_str = current_time.strftime("%Y-%m-%d")
            time_str = current_time.strftime("%H:%M:%S.%f")[:-3]
            
            self.add_log(f"用户点击程序窗口-位置: ({event.x}, {event.y})\n屏幕坐标: ({event.x_root}, {event.y_root})\n时间: {time_str}", "USER")
    
    @handle_errors
    def on_chat_click(self, event):
        """处理聊天区域点击事件"""
        if self.debug_mode:
            current_time = datetime.now()
            date_str = current_time.strftime("%Y-%m-%d")
            time_str = current_time.strftime("%H:%M:%S.%f")[:-3]
            
            # 获取点击位置的文本信息
            try:
                index = self.chat_display.index(f"@{event.x},{event.y}")
                line_content = self.chat_display.get(f"{index} linestart", f"{index} lineend")
                self.add_log(f"💬 [{date_str}] 用户点击聊天区-位置: ({event.x}, {event.y})\n屏幕坐标: ({event.x_root}, {event.y_root})\n时间: {time_str}\n文本位置: {index}\n内容: {line_content[:50]}...", "USER")
            except:
                self.add_log(f"💬 [{date_str}] 用户点击聊天区-位置: ({event.x}, {event.y})\n屏幕坐标: ({event.x_root}, {event.y_root})\n时间: {time_str}", "USER")
    
    @handle_errors
    def on_input_click(self, event):
        """处理输入区域点击事件"""
        if self.debug_mode:
            current_time = datetime.now()
            date_str = current_time.strftime("%Y-%m-%d")
            time_str = current_time.strftime("%H:%M:%S.%f")[:-3]
            
            # 获取输入框内容信息
            try:
                input_content = self.input_text.get(1.0, tk.END).strip()
                cursor_pos = self.input_text.index(tk.INSERT)
                self.add_log(f"[{date_str}] 用户点击输入区-位置: ({event.x}, {event.y})\n屏幕坐标: ({event.x_root}, {event.y_root})\n时间: {time_str}\n光标位置: {cursor_pos}\n输入长度: {len(input_content)} 字符", "USER")
            except:
                self.add_log(f"[{date_str}] 用户点击输入区-位置: ({event.x}, {event.y})\n屏幕坐标: ({event.x_root}, {event.y_root})\n时间: {time_str}", "USER")
    
    @handle_errors
    def on_mouse_motion(self, event):
        """处理鼠标移动事件"""
        if self.debug_mode and self.show_coords_var.get():
            current_time = datetime.now()
            time_str = current_time.strftime("%H:%M:%S.%f")[:-3]
            
            # 限制鼠标移动日志的频率，避免过多日志
            if not hasattr(self, '_last_motion_log_time'):
                self._last_motion_log_time = 0
            
            if current_time.timestamp() - self._last_motion_log_time > 0.5:  # 每0.5秒最多记录一次
                self._last_motion_log_time = current_time.timestamp()
                
                # 识别鼠标所在的区域
                widget = event.widget
                widget_name = "未知"
                
                if widget == self.chat_display:
                    widget_name = "聊天区"
                elif widget == self.input_text:
                    widget_name = "输入区"
                elif widget == self.log_display:
                    widget_name = "日志区"
                    # 在debug模式下，当鼠标在日志区时显示额外的宽度信息
                    if self.debug_mode:
                        try:
                            log_width = self.log_display.winfo_width()
                            log_height = self.log_display.winfo_height()
                            cursor_x = event.x
                            cursor_y = event.y
                            
                            # 计算鼠标在日志区内的相对位置百分比
                            width_percent = (cursor_x / log_width * 100) if log_width > 0 else 0
                            height_percent = (cursor_y / log_height * 100) if log_height > 0 else 0
                            
                            self.add_log(f"鼠标移动 - 位置: ({event.x}, {event.y}) 屏幕坐标: ({event.x_root}, {event.y_root}) 区域: {widget_name} 日志区尺寸: {log_width}×{log_height}px 鼠标相对位置: ({width_percent:.1f}%, {height_percent:.1f}%) 时间: {time_str}", "DEBUG")
                        except Exception as e:
                            self.add_log(f"鼠标移动 - 位置: ({event.x}, {event.y}) 屏幕坐标: ({event.x_root}, {event.y_root}) 区域: {widget_name} 时间: {time_str}", "DEBUG")
                        return
                elif widget == self.root:
                    widget_name = "主窗口"
                
                self.add_log(f"鼠标移动 - 位置: ({event.x}, {event.y}) 屏幕坐标: ({event.x_root}, {event.y_root}) 区域: {widget_name} 时间: {time_str}", "DEBUG")
    
    @handle_errors
    def toggle_mouse_coords(self):
        """切换鼠标坐标显示功能"""
        show_coords = self.show_coords_var.get()
        
        if show_coords:
            # 只有在debug模式下才启用全局鼠标监听
            if self.debug_mode:
                self.enable_global_mouse()
            else:
                self.add_log("鼠标坐标显示仅在debug模式下可用", "INFO")
                self.show_coords_var.set(False)
        else:
            self.disable_global_mouse()
    
    @handle_errors
    def enable_global_mouse(self):
        """启用全局鼠标监听"""
        if not GLOBAL_MOUSE_SUPPORT:
            messagebox.showwarning("功能不可用", "未安装pynput库，无法使用全局鼠标监听功能。\n请运行: pip3 install pynput")
            self.show_coords_var.set(False)
            return
        
        if self.global_mouse_listener is not None:
            self.add_log("全局鼠标监听已在运行", "WARNING")
            return
        
        # 只有在debug模式下才启用全局鼠标监听
        if not self.debug_mode:
            self.add_log("全局鼠标监听仅在debug模式下可用", "INFO")
            self.show_coords_var.set(False)
            return
        
        try:
            self.add_log("启动全局鼠标监听...", "USER")
            
            def on_move(x, y):
                """全局鼠标移动回调"""
                if self.global_mouse_enabled and self.debug_mode:
                    current_time = datetime.now()
                    time_str = current_time.strftime("%H:%M:%S.%f")[:-3]
                    
                    # 限制日志频率
                    if not hasattr(self, '_last_global_motion_time'):
                        self._last_global_motion_time = 0
                    
                    if current_time.timestamp() - self._last_global_motion_time > 1.0:  # 每秒最多记录一次
                        self._last_global_motion_time = current_time.timestamp()
                        
                        # 获取当前活动窗口信息
                        try:
                            focused_widget = self.root.focus_get()
                            window_title = self.root.title()
                            
                            # 判断鼠标是否在程序窗口内
                            root_x = self.root.winfo_x()
                            root_y = self.root.winfo_y()
                            root_width = self.root.winfo_width()
                            root_height = self.root.winfo_height()
                            
                            if root_x <= x <= root_x + root_width and root_y <= y <= root_y + root_height:
                                location = "程序窗口内"
                                # 获取焦点控件信息
                                focused_info = f"焦点控件: {focused_widget.__class__.__name__}" if focused_widget else "无焦点控件"
                            else:
                                location = "其他窗口"
                                focused_info = "程序外"
                            
                            self.add_log(f"全局鼠标移动 - 屏幕坐标: ({x}, {y}) 位置: {location} 窗口标题: {window_title} {focused_info} 时间: {time_str}", "USER")
                        except Exception as e:
                            self.add_log(f"全局鼠标移动 - 屏幕坐标: ({x}, {y}) 时间: {time_str}", "USER")
            
            def on_click(x, y, button, pressed):
                """全局鼠标点击回调"""
                if self.global_mouse_enabled and self.debug_mode and pressed:
                    current_time = datetime.now()
                    time_str = current_time.strftime("%H:%M:%S.%f")[:-3]
                    
                    # 获取按钮名称
                    button_name = str(button).split('.')[-1] if button else "unknown"
                    
                    # 判断鼠标是否在程序窗口内
                    try:
                        root_x = self.root.winfo_x()
                        root_y = self.root.winfo_y()
                        root_width = self.root.winfo_width()
                        root_height = self.root.winfo_height()
                        
                        if root_x <= x <= root_x + root_width and root_y <= y <= root_y + root_height:
                            location = "程序窗口内"
                        else:
                            location = "其他窗口"
                        
                        self.add_log(f"全局鼠标点击 - 按钮: {button_name} 坐标: ({x}, {y}) 位置: {location} 时间: {time_str}", "USER")
                    except Exception:
                        self.add_log(f"全局鼠标点击 - 按钮: {button_name} 坐标: ({x}, {y}) 时间: {time_str}", "USER")
            
            # 创建鼠标监听器
            self.global_mouse_listener = mouse.Listener(
                on_move=on_move,
                on_click=on_click
            )
            
            self.global_mouse_listener.start()
            self.global_mouse_enabled = True
            self.add_log("✅ 全局鼠标监听已启动", "SUCCESS")
            
        except Exception as e:
            self.add_log(f"❌ 启动全局鼠标监听失败: {str(e)}", "ERROR")
            messagebox.showerror("错误", f"启动全局鼠标监听失败:\n{str(e)}")
            self.show_coords_var.set(False)
    
    @handle_errors
    def disable_global_mouse(self):
        """禁用全局鼠标监听"""
        if self.global_mouse_listener is not None:
            try:
                self.add_log("🛑 停止全局鼠标监听...", "USER")
                self.global_mouse_enabled = False
                self.global_mouse_listener.stop()
                self.global_mouse_listener = None
                self.add_log("✅ 全局鼠标监听已停止", "SUCCESS")
            except Exception as e:
                self.add_log(f"❌ 停止全局鼠标监听失败: {str(e)}", "ERROR")
        else:
            self.add_log("全局鼠标监听未运行", "INFO")
    
    @handle_errors
    def cleanup_global_mouse(self):
        """清理全局鼠标监听资源"""
        if self.global_mouse_listener is not None:
            try:
                self.global_mouse_enabled = False
                self.global_mouse_listener.stop()
                self.global_mouse_listener = None
            except:
                pass
    
    @handle_errors
    def add_log(self, message, level="INFO"):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 根据日志级别设置丰富的颜色和样式
        if level == "ERROR":
            tag = "error"
            self.log_display.tag_config("error", 
                foreground="#ff4757",           # 鲜红色
                font=('Arial', 10, 'bold'),     # 粗体
                selectbackground="#ff6b6b",     # 选中背景
                selectforeground="white")       # 选中文字
        elif level == "WARNING":
            tag = "warning"
            self.log_display.tag_config("warning", 
                foreground="#ff9800",           # 橙色
                font=('Arial', 10, 'italic'),   # 斜体
                selectbackground="#ffa726")     # 选中背景
        elif level == "SUCCESS":
            tag = "success"
            self.log_display.tag_config("success", 
                foreground="#4caf50",           # 绿色
                font=('Arial', 10, 'bold'),     # 粗体
                selectbackground="#66bb6a")     # 选中背景
        elif level == "DEBUG":
            tag = "debug"
            self.log_display.tag_config("debug", 
                foreground="#9c27b0",           # 紫色
                font=('Consolas', 10, 'normal'), # 等宽字体
                selectbackground="#ba68c8")     # 选中背景
        elif level == "CRITICAL":
            tag = "critical"
            self.log_display.tag_config("critical", 
                foreground="#d32f2f",           # 深红色
                font=('Arial', 11, 'bold'),     # 更大粗体
                selectbackground="#f44336")     # 选中背景
        elif level == "INFO":
            tag = "info"
            self.log_display.tag_config("info", 
                foreground="#2196f3",           # 蓝色
                font=('Arial', 10, 'normal'),   # 普通字体
                selectbackground="#42a5f5")     # 选中背景
        elif level == "SYSTEM":
            tag = "system"
            self.log_display.tag_config("system", 
                foreground="#607d8b",           # 蓝灰色
                font=('Arial', 10, 'bold'),     # 粗体
                selectbackground="#78909c")     # 选中背景
        elif level == "USER":
            tag = "user"
            self.log_display.tag_config("user", 
                foreground="#795548",           # 棕色
                font=('Arial', 10, 'italic'),   # 斜体
                selectbackground="#8d6e63")     # 选中背景
        elif level == "NETWORK":
            tag = "network"
            self.log_display.tag_config("network", 
                foreground="#00bcd4",           # 青色
                font=('Courier', 10, 'normal'), # 等宽字体
                selectbackground="#26c6da")     # 选中背景
        else:
            tag = "default"
            self.log_display.tag_config("default", 
                foreground="#d4d4d4",           # 浅灰色
                font=('Arial', 10, 'normal'),   # 普通字体
                selectbackground="#555555")     # 选中背景
        
        # 添加时间戳标签样式
        self.log_display.tag_config("timestamp", 
            foreground="#888888",               # 灰色
            font=('Consolas', 9, 'normal'))     # 小号等宽字体
        
        # 添加级别标签样式
        self.log_display.tag_config("level", 
            font=('Arial', 9, 'bold'))          # 粗体
        
        # 添加日志消息
        self.log_display.config(state=tk.NORMAL)
        
        # 插入带样式的日志内容
        self.log_display.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.log_display.insert(tk.END, f"[{level}] ", "level")
        self.log_display.insert(tk.END, f"{message}\n", tag)
        
        # 自动滚动到底部
        if self.auto_scroll_var.get():
            self.log_display.see(tk.END)
        
        self.log_display.config(state=tk.DISABLED)
        
        # 限制日志行数，避免内存占用过多
        try:
            line_count = int(self.log_display.index('end-1c').split('.')[0])
            if line_count > 1000:  # 最多保留1000行日志
                self.log_display.config(state=tk.NORMAL)
                self.log_display.delete(1.0, f"{line_count-800}.0")
                self.log_display.config(state=tk.DISABLED)
        except:
            pass
    
    @handle_errors
    def clear_log(self):
        """清除日志"""
        self.log_display.config(state=tk.NORMAL)
        self.log_display.delete(1.0, tk.END)
        self.log_display.config(state=tk.DISABLED)
        self.add_log("🗑️ 日志已清除", "SYSTEM")
    
    @handle_errors
    def save_log(self):
        """保存日志到文件"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".log",
                filetypes=[("日志文件", "*.log"), ("文本文件", "*.txt"), ("所有文件", "*.*")],
                initialfile=f"spark_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            )
            
            if filename:
                content = self.log_display.get(1.0, tk.END)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.add_log(f"💾 日志已保存到: {filename}", "SUCCESS")
                messagebox.showinfo("成功", f"日志已保存到:\n{filename}")
                
        except Exception as e:
            self.add_log(f"❌ 保存日志失败: {str(e)}", "CRITICAL")
            messagebox.showerror("错误", f"保存失败: {str(e)}")

    @handle_errors
    def show_about(self):
        """显示关于对话框"""
        about_text = """科大讯飞星火模型 GUI v3.0

这是一个基于科大讯飞星火大模型的图形用户界面程序。

功能特点：
• 友好的图形界面
• 实时对话功能
• 对话记录保存/加载
• 凭证管理
• 自动重连机制
• 实时日志显示

快捷键：
• Enter: 发送消息
• Ctrl+Enter: 换行

作者：NanYanM
版本：3.0"""
        
        # 计算居中位置
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 300) // 2
        
        # 创建自定义关于对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("关于")
        dialog.geometry(f"400x300+{x}+{y}")
        dialog.resizable(False, False)
        
        # 确保窗口不会闪现
        dialog.withdraw()  # 先隐藏
        dialog.update_idletasks()
        dialog.deiconify()  # 再显示
        
        # 创建内容框架
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 添加文本
        text_widget = tk.Text(frame, wrap=tk.WORD, height=12, width=40)
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert("1.0", about_text)
        text_widget.config(state=tk.DISABLED)
        
        # 添加关闭按钮
        close_button = ttk.Button(frame, text="关闭", command=dialog.destroy)
        close_button.pack(pady=(10, 0))
        
    @handle_errors
    def get_log_area_info(self):
        """获取日志区信息（Debug功能）"""
        if not self.debug_mode:
            return
        
        try:
            # 获取日志区的基本信息
            line_count = int(self.log_display.index('end-1c').split('.')[0])
            char_count = len(self.log_display.get(1.0, tk.END))
            
            # 获取当前滚动位置
            first_visible = self.log_display.index('@0,0')
            last_visible = self.log_display.index('@0,%d' % self.log_display.winfo_height())
            
            # 获取选中的文本（如果有）
            try:
                selected_text = self.log_display.get(tk.SEL_FIRST, tk.SEL_LAST)
                selected_length = len(selected_text)
                selected_preview = selected_text[:50] + ('...' if len(selected_text) > 50 else '')
            except:
                selected_length = 0
                selected_preview = "无"
            
            # 获取日志区尺寸
            width = self.log_display.winfo_width()
            height = self.log_display.winfo_height()
            
            # 获取字体信息
            font_info = self.log_display.cget('font')
            
            # 获取自动滚动状态
            auto_scroll_status = "开启" if self.auto_scroll_var.get() else "关闭"
            
            # 输出详细信息
            self.add_log("📊 ===== 日志区详细信息 =====", "SYSTEM")
            self.add_log(f"📏 尺寸: {width}x{height} 像素", "INFO")
            self.add_log(f"📝 总行数: {line_count} 行", "INFO")
            self.add_log(f"🔤 总字符数: {char_count} 字符", "INFO")
            self.add_log(f"📖 可见范围: 第{first_visible.split('.')[0]}行 - 第{last_visible.split('.')[0]}行", "INFO")
            self.add_log(f"🎯 选中文本: {selected_length} 字符 - 预览: {selected_preview}", "INFO")
            self.add_log(f"🔤 字体: {font_info}", "INFO")
            self.add_log(f"🔄 自动滚动: {auto_scroll_status}", "INFO")
            self.add_log(f"🎨 颜色主题: 深色模式", "INFO")
            self.add_log("📊 ===== 信息结束 =====", "SYSTEM")
            
        except Exception as e:
            self.add_log(f"❌ 获取日志区信息失败: {str(e)}", "ERROR")
    
    @handle_errors
    def show_error(self, message):
        """显示错误信息"""
        messagebox.showerror("错误", message)
        self.update_status_info(f"错误: {message}")
    
    @handle_errors
    def on_closing(self):
        """窗口关闭处理"""
        try:
            self.add_log("🔄 正在关闭程序...", "SYSTEM")
            
            # 清理全局鼠标监听
            self.cleanup_global_mouse()
            
            # 停止定时更新线程
            if hasattr(self, 'update_thread') and self.update_thread:
                self.add_log("🛑 停止定时更新线程...", "SYSTEM")
                # 这里可以添加线程停止逻辑
            
            self.add_log("✅ 程序已安全关闭", "SUCCESS")
            
            # 销毁窗口
            self.root.destroy()
            
        except Exception as e:
            self.add_log(f"❌ 关闭程序时出错: {str(e)}", "ERROR")
            self.root.destroy()
    
    @handle_errors
    def start_update_thread(self):
        """启动定时更新线程"""
        def scheduled_update():
            while True:
                time.sleep(UPDATE_INTERVAL)
                try:
                    # 这里可以添加自动更新凭证的逻辑
                    pass
                except Exception as e:
                    print(f"定时更新出错: {e}")
        
        update_thread = threading.Thread(target=scheduled_update, daemon=True)
        update_thread.start()

    @handle_errors
    def run(self):
        """运行程序"""
        self.root.mainloop()

@handle_errors
def main():
    """主函数"""
    # 设置全局异常处理器
    sys.excepthook = global_exception_handler
    
    # 安装依赖
    if not install_dependencies():
        print("依赖安装失败，程序可能无法正常运行")
    
    root = tk.Tk()
    app = SparkDeskGUI(root)
    
    # 显示debug模式状态
    if debug_mode:
        print("Debug模式已启用 - 将在日志中显示详细的调试信息")
        app.add_log("🚀 程序启动 - Debug模式已启用", "SUCCESS")
        app.add_log("🔍 新功能：用户交互行为记录已激活", "DEBUG")
        app.add_log("📍 将记录：点击日期、输入区/回答区行为、鼠标详细坐标", "DEBUG")
        app.add_log("🎨 日志系统已升级\n支持丰富的颜色显示", "SYSTEM")
        
        # 延迟获取日志区信息，确保窗口完全渲染
        root.after(1000, app.get_log_area_info)
    else:
        app.add_log("🚀 程序启动 - Debug模式已禁用", "INFO")
        app.add_log("🎨 日志系统已升级\n支持丰富的颜色显示", "SYSTEM")
    
    root.mainloop()

if __name__ == "__main__":
    main()
    