import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import psutil
import time
import os
import threading
from datetime import datetime

class ProcessFileMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("进程文件操作监控器")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # 监控状态
        self.is_monitoring = False
        self.monitor_thread = None
        self.recorded_files = set()
        self.current_process = None
        
        self.setup_ui()
        self.refresh_process_list()
        
    def setup_ui(self):
        """设置用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="进程文件操作监控器", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 进程选择区域
        process_frame = ttk.LabelFrame(main_frame, text="进程选择", padding="10")
        process_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        process_frame.columnconfigure(1, weight=1)
        
        ttk.Label(process_frame, text="选择进程:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        # 进程选择组合框
        self.process_var = tk.StringVar()
        self.process_combo = ttk.Combobox(process_frame, textvariable=self.process_var, 
                                         state="readonly", width=40)
        self.process_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # 刷新按钮
        self.refresh_btn = ttk.Button(process_frame, text="刷新列表", 
                                     command=self.refresh_process_list)
        self.refresh_btn.grid(row=0, column=2, padx=(0, 10))
        
        # 手动输入进程名
        ttk.Label(process_frame, text="或输入进程名:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        
        self.manual_process_var = tk.StringVar()
        self.manual_entry = ttk.Entry(process_frame, textvariable=self.manual_process_var, width=40)
        self.manual_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=(10, 0))
        self.manual_entry.bind('<Return>', self.start_monitoring_from_entry)
        
        # 控制按钮区域
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=2, column=0, columnspan=3, pady=(0, 10))
        
        self.start_btn = ttk.Button(control_frame, text="开始监控", 
                                   command=self.start_monitoring, state="normal")
        self.start_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_btn = ttk.Button(control_frame, text="停止监控", 
                                  command=self.stop_monitoring, state="disabled")
        self.stop_btn.grid(row=0, column=1, padx=(0, 10))
        
        self.clear_btn = ttk.Button(control_frame, text="清空日志", 
                                   command=self.clear_log)
        self.clear_btn.grid(row=0, column=2, padx=(0, 10))
        
        # 监控设置区域
        settings_frame = ttk.LabelFrame(main_frame, text="监控设置", padding="10")
        settings_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(settings_frame, text="监控间隔(秒):").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        self.interval_var = tk.StringVar(value="2")
        interval_spin = ttk.Spinbox(settings_frame, from_=1, to=10, textvariable=self.interval_var, 
                                   width=5)
        interval_spin.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        # 状态显示
        self.status_var = tk.StringVar(value="就绪 - 请选择要监控的进程")
        status_label = ttk.Label(settings_frame, textvariable=self.status_var, 
                                foreground="blue")
        status_label.grid(row=0, column=2, sticky=tk.W)
        
        # 日志显示区域
        log_frame = ttk.LabelFrame(main_frame, text="监控日志", padding="10")
        log_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # 日志文本框
        self.log_text = scrolledtext.ScrolledText(log_frame, width=80, height=20, 
                                                 font=("Consolas", 10))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 统计信息
        stats_frame = ttk.Frame(main_frame)
        stats_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E))
        
        self.stats_var = tk.StringVar(value="发现文件: 0")
        stats_label = ttk.Label(stats_frame, textvariable=self.stats_var)
        stats_label.grid(row=0, column=0, sticky=tk.W)
        
    def refresh_process_list(self):
        """刷新进程列表"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    process_name = proc.info['name']
                    if process_name and process_name not in processes:
                        processes.append(process_name)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            processes.sort()
            self.process_combo['values'] = processes
            self.log_message("系统", f"已加载 {len(processes)} 个进程")
            
        except Exception as e:
            messagebox.showerror("错误", f"刷新进程列表时出错: {str(e)}")
    
    def get_selected_process(self):
        """获取选择的进程"""
        # 优先使用手动输入的进程名
        manual_name = self.manual_process_var.get().strip()
        if manual_name:
            return manual_name
        
        # 使用下拉框选择的进程名
        combo_name = self.process_var.get().strip()
        if combo_name:
            return combo_name
        
        return None
    
    def start_monitoring(self):
        """开始监控"""
        process_name = self.get_selected_process()
        if not process_name:
            messagebox.showwarning("警告", "请选择或输入要监控的进程名")
            return
        
        try:
            interval = float(self.interval_var.get())
            if interval < 0.1 or interval > 10:
                messagebox.showwarning("警告", "监控间隔应在 0.1 到 10 秒之间")
                return
        except ValueError:
            messagebox.showwarning("警告", "请输入有效的监控间隔")
            return
        
        self.current_process = process_name
        self.is_monitoring = True
        self.recorded_files.clear()
        
        # 更新UI状态
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.refresh_btn.config(state="disabled")
        self.process_combo.config(state="disabled")
        self.manual_entry.config(state="disabled")
        
        self.status_var.set(f"监控中: {process_name} - 间隔: {interval}秒")
        self.log_message("系统", f"开始监控进程: {process_name}")
        
        # 启动监控线程
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop, 
            args=(process_name, interval),
            daemon=True
        )
        self.monitor_thread.start()
    
    def start_monitoring_from_entry(self, event=None):
        """从输入框开始监控"""
        self.start_monitoring()
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1)
        
        # 更新UI状态
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.refresh_btn.config(state="normal")
        self.process_combo.config(state="readonly")
        self.manual_entry.config(state="normal")
        
        self.status_var.set("监控已停止")
        self.log_message("系统", f"停止监控进程: {self.current_process}")
        self.update_stats()
        
        # 生成报告
        self.generate_report()
    
    def _monitor_loop(self, process_name, interval):
        """监控循环"""
        while self.is_monitoring:
            try:
                self._check_process_files(process_name)
                time.sleep(interval)
            except Exception as e:
                self.log_message("错误", f"监控过程中出错: {str(e)}")
                time.sleep(interval)
    
    def _check_process_files(self, process_name):
        """检查进程文件"""
        found_any = False
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if not self.is_monitoring:
                    break
                    
                if process_name.lower() in proc.info['name'].lower():
                    pid = proc.info['pid']
                    process = psutil.Process(pid)
                    
                    try:
                        open_files = process.open_files()
                        for file_info in open_files:
                            if not self.is_monitoring:
                                break
                                
                            file_path = file_info.path
                            
                            if file_path not in self.recorded_files:
                                self.recorded_files.add(file_path)
                                self._log_file_access(pid, file_path)
                                found_any = True
                                
                    except (psutil.AccessDenied, psutil.NoSuchProcess):
                        continue
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if found_any:
            self.update_stats()
    
    def _log_file_access(self, pid, file_path):
        """记录文件访问"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        try:
            if os.path.exists(file_path):
                if os.path.isfile(file_path):
                    file_type = "文件"
                    file_size = os.path.getsize(file_path)
                    message = f"[{timestamp}] PID:{pid:>6} | {file_type} | {file_path} ({file_size} bytes)"
                elif os.path.isdir(file_path):
                    file_type = "目录"
                    message = f"[{timestamp}] PID:{pid:>6} | {file_type} | {file_path}"
                else:
                    file_type = "其他"
                    message = f"[{timestamp}] PID:{pid:>6} | {file_type} | {file_path}"
            else:
                message = f"[{timestamp}] PID:{pid:>6} | 已删除 | {file_path}"
        except Exception as e:
            message = f"[{timestamp}] PID:{pid:>6} | 错误 | {file_path} ({str(e)})"
        
        self.log_message("监控", message)
    
    def log_message(self, source, message):
        """添加日志消息"""
        def update_log():
            timestamp = datetime.now().strftime("%H:%M:%S")
            if source == "监控":
                self.log_text.insert(tk.END, f"{message}\n")
            else:
                self.log_text.insert(tk.END, f"[{timestamp}] [{source}] {message}\n")
            
            self.log_text.see(tk.END)
            self.log_text.update()
        
        # 在UI线程中更新日志
        self.root.after(0, update_log)
    
    def update_stats(self):
        """更新统计信息"""
        def update():
            self.stats_var.set(f"发现文件: {len(self.recorded_files)}")
        
        self.root.after(0, update)
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
        self.recorded_files.clear()
        self.update_stats()
        self.log_message("系统", "日志已清空")
    
    def generate_report(self):
        """生成监控报告"""
        if not self.recorded_files:
            self.log_message("报告", "未发现任何文件操作")
            return
        
        self.log_message("报告", "=" * 50)
        self.log_message("报告", "监控报告摘要")
        self.log_message("报告", "=" * 50)
        self.log_message("报告", f"监控进程: {self.current_process}")
        self.log_message("报告", f"发现文件数量: {len(self.recorded_files)}")
        self.log_message("报告", "=" * 50)
        
        # 分类统计
        files = []
        dirs = []
        others = []
        
        for file_path in self.recorded_files:
            try:
                if os.path.exists(file_path):
                    if os.path.isfile(file_path):
                        files.append(file_path)
                    elif os.path.isdir(file_path):
                        dirs.append(file_path)
                    else:
                        others.append(file_path)
                else:
                    others.append(file_path)
            except:
                others.append(file_path)
        
        if files:
            self.log_message("报告", f"\n访问的文件 ({len(files)}个):")
            for file in sorted(files):
                self.log_message("报告", f"  📄 {file}")
        
        if dirs:
            self.log_message("报告", f"\n访问的目录 ({len(dirs)}个):")
            for dir_path in sorted(dirs):
                self.log_message("报告", f"  📁 {dir_path}")
        
        if others:
            self.log_message("报告", f"\n其他资源 ({len(others)}个):")
            for other in sorted(others):
                self.log_message("报告", f"  ❓ {other}")

def main():
    try:
        root = tk.Tk()
        app = ProcessFileMonitorGUI(root)
        root.mainloop()
    except Exception as e:
        print(f"程序启动失败: {e}")
        input("按回车键退出...")

if __name__ == "__main__":
    main()