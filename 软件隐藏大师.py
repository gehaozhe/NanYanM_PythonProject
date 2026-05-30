import sys

import psutil
import win32gui
import win32con
import win32process
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget,
                             QPushButton, QListWidget, QLabel, QLineEdit,
                             QHBoxLayout, QListWidgetItem, QRadioButton,
                             QButtonGroup, QTextEdit, QMessageBox, QDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
import keyboard
import threading
import os
import webbrowser


class WindowHider(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("应用隐藏大师（摸鱼专用）")
        self.setGeometry(100, 100, 800, 600)

        # 初始化变量
        self.hidden_windows = {}  # 格式: {hwnd: (title, pid)}
        self.all_windows = []
        self.user_type = "worker"  # 默认是上班族模式
        self.version = "1.1.0"

        self.init_ui()
        self.setup_hotkeys()
        self.refresh_processes()
        self.update_ui_text()

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()

        # 标题栏
        title_layout = QHBoxLayout()
        self.title_label = QLabel("应用隐藏大师（摸鱼专用）")
        self.title_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.title_label.setToolTip("老板键在手，摸鱼不用愁！")

        settings_btn = QPushButton("摸鱼设置")
        settings_btn.clicked.connect(self.show_settings)

        about_btn = QPushButton("关于")
        about_btn.clicked.connect(self.show_about)

        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        title_layout.addWidget(settings_btn)
        title_layout.addWidget(about_btn)
        main_layout.addLayout(title_layout)

        # 搜索栏
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入你想藏起来的东西...比如'老板'或'钉钉'")
        self.search_input.textChanged.connect(self.filter_processes)

        search_layout.addWidget(self.search_input)
        main_layout.addLayout(search_layout)

        # 窗口列表 (带复选框)
        self.process_list = QListWidget()
        self.process_list.setSelectionMode(QListWidget.NoSelection)
        self.process_list.setStyleSheet("""
            QListWidget::item { 
                padding: 5px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:hover {
                background: #f5f5f5;
            }
        """)
        self.process_list_label = QLabel("当前正在暴露你摸鱼的窗口（勾选你想藏起来的）：")
        main_layout.addWidget(self.process_list_label)
        main_layout.addWidget(self.process_list)

        # 操作按钮
        button_layout = QHBoxLayout()

        self.toggle_button = QPushButton("一键隐藏/恢复")
        self.toggle_button.clicked.connect(self.toggle_hide_windows)
        self.toggle_button.setToolTip("老板来了点这里！")

        self.emergency_btn = QPushButton("!! 毁灭证据 !!")
        self.emergency_btn.setStyleSheet("background-color: #ff4444; color: white; font-weight: bold;")
        self.emergency_btn.clicked.connect(self.emergency_exit)
        self.emergency_btn.setToolTip("老板已经站在你身后了？点这个！")

        refresh_button = QPushButton("刷新列表")
        refresh_button.clicked.connect(self.refresh_processes)
        refresh_button.setToolTip("看看有没有新窗口暴露你在摸鱼")

        button_layout.addWidget(self.toggle_button)
        button_layout.addWidget(self.emergency_btn)
        button_layout.addWidget(refresh_button)

        main_layout.addLayout(button_layout)

        # 状态栏
        self.status_label = QLabel("摸鱼状态 | 正常模式 | 快捷键: Ctrl+Alt+H(老板键) Ctrl+Alt+Shift+E(紧急销毁)")
        main_layout.addWidget(self.status_label)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def update_ui_text(self):
        """根据用户类型更新界面文字"""
        if self.user_type == "student":
            self.setWindowTitle("应用隐藏大师（学习摸鱼专用）")
            self.title_label.setText("应用隐藏大师（学习摸鱼专用）")
            self.process_list_label.setText("当前正在暴露你摸鱼的窗口（勾选你想藏起来的）：")
            self.toggle_button.setToolTip("老师来了点这里！")
            self.emergency_btn.setToolTip("老师已经站在你身后了？点这个！")
        else:
            self.setWindowTitle("应用隐藏大师（上班摸鱼专用）")
            self.title_label.setText("应用隐藏大师（上班摸鱼专用）")
            self.process_list_label.setText("当前正在暴露你摸鱼的窗口（勾选你想藏起来的）：")
            self.toggle_button.setToolTip("老板来了点这里！")
            self.emergency_btn.setToolTip("老板已经站在你身后了？点这个！")

    def setup_hotkeys(self):
        """设置全局快捷键"""

        def start_hotkey_listener():
            keyboard.add_hotkey('ctrl+alt+h', self.toggle_hide_windows)
            keyboard.add_hotkey('ctrl+alt+x', self.toggle_app_visibility)
            keyboard.add_hotkey('ctrl+alt+shift+e', self.emergency_exit)
            keyboard.wait()  # 保持监听

        # 在新线程中运行键盘监听
        hotkey_thread = threading.Thread(target=start_hotkey_listener, daemon=True)
        hotkey_thread.start()

    def emergency_exit(self):
        """紧急模式：强制结束所有被隐藏窗口的进程并退出"""
        # 直接执行不询问
        killed_count = 0
        for hwnd, (title, pid) in list(self.hidden_windows.items()):
            try:
                process = psutil.Process(pid)
                process.terminate()
                killed_count += 1
            except:
                continue

        # 立即退出
        os._exit(0)

    def show_settings(self):
        """显示设置对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("摸鱼设置")
        dialog.setFixedSize(400, 250)

        layout = QVBoxLayout()

        # 用户类型选择
        user_type_group = QHBoxLayout()
        user_type_group.addWidget(QLabel("用户类型:"))

        # 使用单选按钮组
        self.user_type_group = QButtonGroup(self)

        self.worker_radio = QRadioButton("上班族模式")
        self.student_radio = QRadioButton("学生模式")

        self.user_type_group.addButton(self.worker_radio)
        self.user_type_group.addButton(self.student_radio)

        if self.user_type == "worker":
            self.worker_radio.setChecked(True)
        else:
            self.student_radio.setChecked(True)

        self.worker_radio.toggled.connect(lambda: self.set_user_type("worker"))
        self.student_radio.toggled.connect(lambda: self.set_user_type("student"))

        user_type_group.addWidget(self.worker_radio)
        user_type_group.addWidget(self.student_radio)
        user_type_group.addStretch()
        layout.addLayout(user_type_group)

        # 快捷键设置
        layout.addWidget(QLabel("摸鱼快捷键设置:"))
        layout.addWidget(QLabel("Ctrl+Alt+H: 一键隐藏/恢复窗口（老板键）"))
        layout.addWidget(QLabel("Ctrl+Alt+X: 显示/隐藏摸鱼面板"))
        layout.addWidget(QLabel("Ctrl+Alt+Shift+E: 紧急销毁证据"))

        warning_label = QLabel("警告: 紧急销毁会强制结束所有被隐藏窗口的进程！")
        warning_label.setStyleSheet("color: red; font-weight: bold;")
        warning_label.setToolTip("这相当于把电脑砸了毁灭证据")
        layout.addWidget(warning_label)

        ok_btn = QPushButton("懂了，继续摸鱼")
        ok_btn.clicked.connect(dialog.accept)
        layout.addWidget(ok_btn)

        dialog.setLayout(layout)
        dialog.exec_()

    def set_user_type(self, user_type):
        """设置用户类型并更新界面"""
        self.user_type = user_type
        self.update_ui_text()

    def show_about(self):
        """显示关于对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"关于 应用隐藏大师 v{self.version}")
        dialog.setFixedSize(500, 400)

        layout = QVBoxLayout()

        # 标题
        title_label = QLabel(f"应用隐藏大师 v{self.version}")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title_label)

        # 开发日志
        log_label = QLabel("开发日志:")
        layout.addWidget(log_label)

        log_text = QTextEdit()
        log_text.setReadOnly(True)
        log_text.setPlainText(
            "v1.1.0 (2025-07-25)\n"
            "- 新增学生/上班族模式切换\n"
            "- 增加关于对话框\n"
            "- 优化界面文字\n\n"
            "v1.0.0 (2025-07-20)\n"
            "- 初始版本发布\n"
            "- 实现基本窗口隐藏功能\n"
            "- 添加老板键和紧急销毁功能"
        )
        layout.addWidget(log_text)

        # 作者信息
        author_layout = QHBoxLayout()
        author_label = QLabel("作者: 磊起字节（摸鱼大师）")
        author_layout.addWidget(author_label)

        bilibili_btn = QPushButton("访问作者哔哩哔哩")
        bilibili_btn.clicked.connect(
            lambda: webbrowser.open("网页链接​"))
        author_layout.addWidget(bilibili_btn)

        layout.addLayout(author_layout)

        # 确定按钮
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(dialog.accept)
        layout.addWidget(ok_btn)

        dialog.setLayout(layout)
        dialog.exec_()

    def toggle_app_visibility(self):
        """切换程序显示/隐藏"""
        if self.isVisible():
            self.hide()
        else:
            self.show_normal()

    def show_normal(self):
        """正常显示窗口"""
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        self.activateWindow()

    def refresh_processes(self):
        """刷新窗口列表"""
        self.all_windows = self.get_all_windows()
        self.process_list.clear()

        for hwnd, title, exe, pid in self.all_windows:
            if title.strip():
                item = QListWidgetItem(f"{title} [{exe}] (PID: {pid})")
                item.setData(Qt.UserRole, (hwnd, title, exe, pid))
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Unchecked)
                self.process_list.addItem(item)

        self.filter_processes()
        self.update_status()

    def filter_processes(self):
        """过滤窗口列表"""
        search_text = self.search_input.text().lower()

        for i in range(self.process_list.count()):
            item = self.process_list.item(i)
            hwnd, title, exe, pid = item.data(Qt.UserRole)
            text_match = search_text in title.lower() or search_text in exe.lower() or search_text in str(pid)
            item.setHidden(not text_match)

    def get_all_windows(self):
        """获取所有可见窗口及其进程ID"""
        windows = []

        def enum_windows_callback(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                try:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    process = psutil.Process(pid)
                    exe = process.name()
                    windows.append((hwnd, title, exe, pid))
                except:
                    pass
            return True

        win32gui.EnumWindows(enum_windows_callback, None)
        return windows

    def toggle_hide_windows(self):
        """切换选中窗口的隐藏/显示状态"""
        selected_windows = []
        for i in range(self.process_list.count()):
            item = self.process_list.item(i)
            if not item.isHidden() and item.checkState() == Qt.Checked:
                hwnd, title, exe, pid = item.data(Qt.UserRole)
                selected_windows.append((hwnd, title, pid))

        if not selected_windows:
            return

        # 判断当前应该隐藏还是恢复
        all_hidden = all(hwnd in self.hidden_windows for hwnd, _, _ in selected_windows)

        if all_hidden:
            # 恢复窗口
            for hwnd, title, pid in selected_windows:
                if hwnd in self.hidden_windows:
                    try:
                        win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                        win32gui.BringWindowToTop(hwnd)
                        del self.hidden_windows[hwnd]
                    except:
                        continue
            if self.user_type == "student":
                self.status_label.setText(f"已恢复 {len(selected_windows)} 个窗口 | 可以继续学习了")
            else:
                self.status_label.setText(f"已恢复 {len(selected_windows)} 个窗口 | 可以继续摸鱼了")
        else:
            # 隐藏窗口
            count = 0
            for hwnd, title, pid in selected_windows:
                if hwnd not in self.hidden_windows and self.hide_window(hwnd, title, pid):
                    count += 1
            if self.user_type == "student":
                self.status_label.setText(f"已隐藏 {count} 个窗口 | 老师看不见模式")
            else:
                self.status_label.setText(f"已隐藏 {count} 个窗口 | 老板看不见模式")

        self.update_status()

    def hide_window(self, hwnd, title, pid):
        """隐藏指定窗口并记录进程ID"""
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
            win32gui.ShowWindow(hwnd, win32con.SW_FORCEMINIMIZE)
            win32gui.SetWindowPos(hwnd, 0, 0, 0, 0, 0,
                                  win32con.SWP_HIDEWINDOW |
                                  win32con.SWP_NOACTIVATE |
                                  win32con.SWP_NOMOVE |
                                  win32con.SWP_NOSIZE |
                                  win32con.SWP_NOZORDER)

            self.hidden_windows[hwnd] = (title, pid)
            return True
        except:
            return False

    def update_status(self):
        """更新状态栏信息"""
        selected_count = sum(1 for i in range(self.process_list.count())
                             if not self.process_list.item(i).isHidden()
                             and self.process_list.item(i).checkState() == Qt.Checked)

        if self.user_type == "student":
            mode = "老师看不见模式" if self.hidden_windows else "安心学习模式"
        else:
            mode = "老板看不见模式" if self.hidden_windows else "安心摸鱼模式"

        self.status_label.setText(
            f"暴露风险窗口: {self.process_list.count()} | "
            f"已隐藏: {len(self.hidden_windows)} | "
            f"选中: {selected_count} | "
            f"状态: {mode} | "
            f"紧急销毁: Ctrl+Alt+Shift+E"
        )

    def closeEvent(self, event):
        """处理关闭事件"""
        reply = QMessageBox.question(
            self, '确认退出摸鱼',
            "确定要退出摸鱼模式吗？\n所有被隐藏窗口将保持隐藏状态",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

if __name__ == "__main__":
    # 检查依赖
    try:
        import win32process
        import keyboard
    except ImportError:
        QMessageBox.critical(None, "摸鱼失败",
                             "缺少必要的摸鱼工具！\n请运行: pip install pywin32 keyboard psutil PyQt5")
        sys.exit(1)

    app = QApplication(sys.argv)
    window = WindowHider()
    window.show()
    sys.exit(app.exec_())