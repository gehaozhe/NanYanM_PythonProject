import tkinter as tk

from tkinter import messagebox
import sys
import ctypes
import os
import threading
import time
import win32gui
import win32con
from datetime import datetime
import cv2
import pygame.camera
from PIL import Image, ImageDraw, ImageFont
import traceback
from itertools import cycle


class UltimateLockScreen:
    def __init__(self):
        self.setup_logging()
        self.initialize_security()
        self.setup_camera()
        self.create_main_window()
        self.start_protection_threads()
        self.setup_blink_effect()

    def setup_logging(self):
        self.log_dir = "lock_screen_logs"
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file = os.path.join(self.log_dir, f"security_log_{datetime.now().strftime('%Y%m%d')}.txt")
        self.log("=== 锁屏程序启动 ===")

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            print(f"日志写入失败: {str(e)}")
        print(log_entry.strip())

    def initialize_security(self):
        self.correct_password = 'xiexia0418'
        self.max_attempts = 20
        self.attempts_left = self.max_attempts
        self.protection_active = True

        os.system('taskkill /f /im explorer.exe')
        self.log("已结束文件资源管理器进程", "INFO")

        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        self.kernel32.SetProcessShutdownParameters(0x3FF, 0)

    def setup_camera(self):
        self.camera_available = False
        self.camera_type = None
        self.camera = None
        self.photo_dir = "security_photos"
        os.makedirs(self.photo_dir, exist_ok=True)

        try:
            self.log("正在初始化OpenCV摄像头...")
            self.camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if self.camera.isOpened():
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                self.camera.set(cv2.CAP_PROP_AUTOFOCUS, 1)
                self.camera_available = True
                self.camera_type = 'opencv'
                self.log("OpenCV摄像头初始化成功")
            else:
                self.camera.release()
                self.log("OpenCV摄像头未就绪", "WARNING")
        except Exception as e:
            self.log(f"OpenCV初始化失败: {str(e)}", "WARNING")
            if hasattr(self, 'camera'):
                self.camera.release()

        if not self.camera_available:
            try:
                self.log("正在初始化Pygame摄像头...")
                pygame.camera.init()
                cam_list = pygame.camera.list_cameras()
                if cam_list:
                    self.camera = pygame.camera.Camera(cam_list[0], (640, 480))
                    self.camera.start()
                    time.sleep(2)
                    self.camera_available = True
                    self.camera_type = 'pygame'
                    self.log("Pygame摄像头初始化成功")
                else:
                    self.log("未检测到可用摄像头", "WARNING")
            except Exception as e:
                self.log(f"Pygame初始化失败: {str(e)}", "WARNING")

    def capture_photo(self):
        if not self.camera_available:
            return False, None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.photo_dir, f"intruder_{timestamp}.jpg")

        try:
            if self.camera_type == 'opencv':
                time.sleep(1)
                ret, frame = self.camera.read()
                if ret:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img_pil = Image.fromarray(frame)
                    self.add_watermark(img_pil)
                    img_pil.save(filename, quality=95)
                    return True, filename

            elif self.camera_type == 'pygame':
                time.sleep(1)
                img = self.camera.get_image()
                if img:
                    pygame.image.save(img, filename)
                    img_pil = Image.open(filename)
                    self.add_watermark(img_pil)
                    img_pil.save(filename, quality=95)
                    return True, filename

        except Exception as e:
            self.log(f"拍照失败: {str(e)}", "ERROR")
            traceback.print_exc()

        return False, None

    def add_watermark(self, img_pil):
        try:
            draw = ImageDraw.Draw(img_pil)
            try:
                font = ImageFont.truetype("simhei.ttf", 36)
            except:
                font = ImageFont.load_default()

            text = f"未经授权访问 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            draw.text((50, 50), text, font=font, fill=(255, 0, 0))
        except Exception as e:
            self.log(f"水印添加失败: {str(e)}", "WARNING")

    def create_main_window(self):
        try:
            self.root = tk.Tk()
            self.root.withdraw()

            self.root.attributes('-fullscreen', True)
            self.root.configure(bg='black')
            self.root.wm_attributes('-topmost', True)
            self.root.overrideredirect(True)

            for key in ['<Alt-F4>', '<Escape>', '<Control-Alt-Delete>',
                        '<Alt-Tab>', '<Control-Escape>', '<Super_L>', '<Super_R>']:
                self.root.bind(key, lambda e: "break")

            self.create_ui()
            self.root.deiconify()
            self.log("主窗口创建完成")
        except Exception as e:
            self.log(f"窗口创建失败: {str(e)}", "ERROR")
            self.emergency_recovery()

    def create_ui(self):
        main_container = tk.Frame(self.root, bg='black')
        main_container.pack(fill='both', expand=True, padx=50, pady=50)

        self.create_tech_panel(main_container)
        self.create_password_panel(main_container)
        self.create_legal_panel(main_container)

        self.root.bind('<Return>', lambda e: self.check_password())

    def create_tech_panel(self, parent):
        frame = tk.Frame(parent, bg='#111111', width=300)
        frame.pack(side='left', fill='y', padx=(0, 20))

        tk.Label(
            frame, text="🔒技术锁机",
            font=('Microsoft YaHei', 14, 'bold'),
            fg='white', bg='#111111', pady=20
        ).pack()

        tech_items = [
            "1. 全屏置顶窗口锁定",
            "2. 系统快捷键全局禁用",
            "3. Win键实时拦截",
            "4. 文件资源管理器已结束",
            "5. 20次错误触发关机",
            f"6. 摄像头自动取证 {'(可用)' if self.camera_available else '(不可用)'}",
            "7. 键盘输入监控",
            "8. 详细操作日志记录"
        ]

        for item in tech_items:
            tk.Label(
                frame, text=item,
                font=('Microsoft YaHei', 11),
                fg='#00CCFF', bg='#111111',
                anchor='w', padx=20
            ).pack(fill='x', pady=2)

    def create_password_panel(self, parent):
        frame = tk.Frame(parent, bg='black')
        frame.pack(side='left', expand=True)

        self.title_label = tk.Label(
            frame, text="这是我的电脑，别想乱动！",
            font=('Microsoft YaHei', 28, 'bold'), bg='black'
        )
        self.title_label.pack(pady=(0, 30))

        self.status_label = tk.Label(
            frame, text=f"剩余尝试次数: {self.attempts_left}/{self.max_attempts}",
            font=('Arial', 14), fg='white', bg='black'
        )
        self.status_label.pack()

        self.password_entry = tk.Entry(
            frame, show="*", font=('Arial', 18),
            width=20, bd=2, relief='flat'
        )
        self.password_entry.pack(pady=20, ipady=5)
        self.password_entry.focus_set()

        tk.Button(
            frame, text="解  锁", font=('Arial', 14),
            command=self.check_password,
            width=10, bg='#0078d7', fg='white', bd=0
        ).pack(pady=(10, 0), ipady=5)

    def create_legal_panel(self, parent):
        frame = tk.Frame(parent, bg='#220000', width=350)
        frame.pack(side='right', fill='y', padx=(20, 0))

        tk.Label(
            frame, text="⚠️ 法律警示",
            font=('Microsoft YaHei', 16, 'bold'),
            fg='white', bg='#220000', pady=20
        ).pack()

        legal_texts = [
            "《中华人民共和国刑法》",
            "第二百八十五条：",
            "非法侵入计算机系统",
            "最高可处七年有期徒刑",
            "",
            "第二百八十六条：",
            "破坏计算机系统功能",
            "造成严重后果的",
            "处五年以上有期徒刑",
            "",
            "未经授权访问他人电脑",
            "可能构成违法行为",
            "请立即停止操作！"
        ]

        for text in legal_texts:
            color = '#FF9999' if "刑法" in text else '#FF6666'
            tk.Label(
                frame, text=text,
                font=('Microsoft YaHei', 11),
                fg=color, bg='#220000',
                anchor='w', padx=20
            ).pack(fill='x', pady=2)

    def setup_blink_effect(self):
        self.blink_colors = cycle(['red', '#FF9900', '#FF33CC', '#00FF66', '#0099FF'])
        self.blink_speed = 800
        self.blink_label()

    def blink_label(self):
        try:
            if hasattr(self, 'title_label'):
                color = next(self.blink_colors)
                self.title_label.config(fg=color)
                self.root.after(self.blink_speed, self.blink_label)
        except Exception as e:
            self.log(f"闪烁效果错误: {str(e)}", "ERROR")
            self.root.after(1000, self.blink_label)

    def start_protection_threads(self):
        def protected_thread(target_func):
            def wrapper():
                while self.protection_active:
                    try:
                        target_func()
                    except Exception as e:
                        self.log(f"防护线程错误: {str(e)}", "ERROR")
                        time.sleep(1)

            return wrapper

        threading.Thread(
            target=protected_thread(self.win_key_protection),
            daemon=True
        ).start()

        self.log("防护线程已启动")

    def win_key_protection(self):
        if self.user32.GetAsyncKeyState(0x5B) & 0x8000:
            self.log("检测到Win键按下，已拦截", "INFO")
            self.clear_keyboard()
        time.sleep(0.1)

    def clear_keyboard(self):
        try:
            for _ in range(3):
                self.user32.keybd_event(0x5B, 0, 0x0002, 0)
            self.log("键盘缓冲区已清除", "INFO")
        except Exception as e:
            self.log(f"清除键盘失败: {str(e)}", "ERROR")

    def check_password(self, event=None):
        try:
            entered_password = self.password_entry.get()
            self.log(f"密码尝试输入: {'*' * len(entered_password)}", "INFO")

            if entered_password == self.correct_password:
                self.clean_exit()
            else:
                self.handle_wrong_password()

        except Exception as e:
            self.log(f"密码检查错误: {str(e)}", "ERROR")
            self.root.after(1000, lambda: self.check_password())

    def handle_wrong_password(self):
        self.attempts_left -= 1
        self.password_entry.delete(0, tk.END)
        self.status_label.config(text=f"剩余尝试次数: {self.attempts_left}/{self.max_attempts}")
        self.log(f"密码错误！剩余尝试次数: {self.attempts_left}/{self.max_attempts}", "WARNING")

        self.root.update()

        if self.camera_available:
            self.log("正在执行拍照取证...", "INFO")
            self.status_label.config(text="正在拍照取证...")
            self.root.update()

            success, filename = self.capture_photo()
            if success:
                self.log(f"已保存入侵者照片: {filename}", "INFO")
                self.status_label.config(text=f"取证完成！剩余尝试: {self.attempts_left}/{self.max_attempts}")
            else:
                self.log("拍照取证失败", "WARNING")
                self.status_label.config(text=f"拍照失败！剩余尝试: {self.attempts_left}/{self.max_attempts}")

        if self.attempts_left <= 0:
            self.trigger_shutdown()
        else:
            self.password_entry.config(bg='#fff0f0')
            self.root.after(500, lambda: self.password_entry.config(bg='white'))

    def trigger_shutdown(self):
        try:
            self.log("正在触发系统关机...", "CRITICAL")

            # 显示关机警告
            self.root.withdraw()
            messagebox.showerror(
                "安全警告",
                "检测到多次非法访问尝试\n系统将在5秒后自动关机",
                master=self.root
            )

            # 倒计时显示
            countdown_window = tk.Toplevel()
            countdown_window.attributes('-fullscreen', True)
            countdown_window.configure(bg='black')
            countdown_window.wm_attributes('-topmost', True)
            countdown_window.overrideredirect(True)

            countdown_label = tk.Label(
                countdown_window,
                text="系统将在5秒后关机",
                font=('Microsoft YaHei', 36, 'bold'),
                fg='red', bg='black'
            )
            countdown_label.pack(expand=True)

            # 倒计时动画
            for i in range(5, 0, -1):
                countdown_label.config(text=f"系统将在{i}秒后关机")
                countdown_window.update()
                time.sleep(1)

            # 执行关机命令
            os.system("shutdown /s /f /t 0")

        except Exception as e:
            self.log(f"触发关机失败: {str(e)}", "ERROR")

            # 备用关机方案
            try:
                os.system("shutdown /s /f /t 3")
            except:
                pass

    def clean_exit(self):
        try:
            self.log("开始安全退出流程...", "INFO")
            self.protection_active = False

            if hasattr(self, 'camera'):
                if self.camera_type == 'opencv':
                    self.camera.release()
                elif self.camera_type == 'pygame':
                    self.camera.stop()
                self.log("摄像头资源已释放", "INFO")

            os.system('start explorer.exe')
            self.log("已重新启动文件资源管理器", "INFO")

            if hasattr(self, 'root'):
                try:
                    self.root.destroy()
                    self.log("主窗口已销毁", "INFO")
                except Exception as e:
                    self.log(f"销毁窗口失败: {str(e)}", "WARNING")

            self.log("资源已释放，程序退出", "INFO")

        except Exception as e:
            self.log(f"退出时发生严重错误: {str(e)}", "CRITICAL")
            os._exit(0)

    def emergency_recovery(self):
        try:
            self.log("正在尝试紧急恢复...", "WARNING")
            os.system('start explorer.exe')
            os._exit(1)
        except:
            os._exit(1)


if __name__ == "__main__":
    def run_with_recovery():
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if ctypes.windll.shell32.IsUserAnAdmin() == 0:
                    ctypes.windll.shell32.ShellExecuteW(
                        None, "runas", sys.executable, " ".join(sys.argv), None, 1
                    )
                    sys.exit()

                lock_screen = UltimateLockScreen()
                lock_screen.root.mainloop()
                break

            except Exception as e:
                error_msg = f"启动失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}"
                print(error_msg)
                with open("startup_error.log", "a") as f:
                    f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {error_msg}\n")

                if attempt == max_retries - 1:
                    messagebox.showerror("致命错误", "程序无法启动，将恢复系统")
                    os.system('start explorer.exe')
                    sys.exit(1)
                time.sleep(2)


    run_with_recovery()