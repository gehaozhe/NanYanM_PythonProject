import os

import io
import zipfile
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import webbrowser
from PIL import Image, ImageTk
from ttkbootstrap import Style, Frame, Label, Button, Entry, Separator, Labelframe

# 将tkinter的scrolledtext别名为ScrolledText以保持代码一致性
ScrolledText = scrolledtext.ScrolledText

# 尝试导入拖放库
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    HAS_DND = True
except ImportError:
    HAS_DND = False
    print("警告: 未安装tkinterdnd2库，拖放功能不可用")


class 图片隐藏工具:
    def __init__(self, 主窗口):
        self.主窗口 = 主窗口
        self.样式 = Style(theme="minty")
        self.主窗口.title("图片藏文件工具")
        self.主窗口.geometry("650x650")
        self.居中窗口()

        # 存储预览图片引用
        self.预览图片 = None
        self.预览照片 = None

        # 初始化界面
        self.初始化界面()

        # 设置拖放支持
        if HAS_DND:
            self.设置拖放功能()
        else:
            self.记录日志("⚠️ 拖放功能不可用，请安装tkinterdnd2库", 错误=True)

    def 居中窗口(self):
        """居中窗口"""
        self.主窗口.update_idletasks()
        宽度 = self.主窗口.winfo_width()
        高度 = self.主窗口.winfo_height()
        x = (self.主窗口.winfo_screenwidth() // 2) - (宽度 // 2)
        y = (self.主窗口.winfo_screenheight() // 2) - (高度 // 2)
        self.主窗口.geometry(f"+{x}+{y}")

    def 初始化界面(self):
        """初始化用户界面"""
        # 主框架
        self.主框架 = Frame(self.主窗口)
        self.主框架.pack(fill="both", expand=True, padx=15, pady=15)

        # 标题
        Label(self.主框架,
              text="🔒 图片藏文件工具",
              font=("Microsoft YaHei", 18, "bold"),
              style="primary.TLabel").pack(pady=(0, 15))

        # 分隔线
        Separator(self.主框架, orient="horizontal", style="primary.Horizontal.TSeparator").pack(fill="x", pady=5)

        # 主功能区域
        内容框架 = Labelframe(self.主框架, text=" 文件隐藏操作 ", style="info.TLabelframe")
        内容框架.pack(fill="both", expand=True, pady=10)

        # 图片选择和预览区域
        图片框架 = Frame(内容框架)
        图片框架.pack(fill="x", pady=(0, 10))

        # 图片选择部分
        Label(图片框架, text="选择图片:", font=("Microsoft YaHei", 10), style="dark.TLabel").grid(row=0, column=0,
                                                                                                   sticky="w",
                                                                                                   pady=(0, 5))

        图片选择框架 = Frame(图片框架)
        图片选择框架.grid(row=1, column=0, sticky="ew")

        self.图片路径输入框 = Entry(图片选择框架, font=("Microsoft YaHei", 10))
        self.图片路径输入框.pack(side="left", fill="x", expand=True, padx=(0, 10))

        Button(
            图片选择框架,
            text="浏览图片",
            command=lambda: self.浏览文件(输入框="图片路径", 文件类型=[("图片文件", "*.jpg;*.png;*.bmp")]),
            width=10,
            style="primary.Outline.TButton"
        ).pack(side="left")

        # 图片预览部分
        预览框架 = Labelframe(图片框架, text="预览", width=150, height=120, style="light.TLabelframe")
        预览框架.grid(row=0, column=1, rowspan=2, padx=10, sticky="ns")
        预览框架.pack_propagate(False)

        self.预览标签 = Label(预览框架, text="等待图片...",
                                   anchor="center",
                                   font=("Microsoft YaHei", 9),
                                   style="secondary.TLabel")
        self.预览标签.pack(fill="both", expand=True)

        # 选择文件或文件夹
        文件选择框架 = Frame(内容框架)
        文件选择框架.pack(fill="x", pady=(10, 0))

        Label(文件选择框架, text="选择文件或文件夹:", font=("Microsoft YaHei", 10), style="dark.TLabel").pack(
            anchor="w", pady=(0, 5))

        按钮框架 = Frame(文件选择框架)
        按钮框架.pack(fill="x", pady=(0, 10))

        self.文件路径输入框 = Entry(按钮框架, font=("Microsoft YaHei", 10))
        self.文件路径输入框.pack(side="left", fill="x", expand=True, padx=(0, 10))

        Button(
            按钮框架,
            text="选择文件",
            command=lambda: self.浏览文件(输入框="文件路径", 文件类型=[("所有文件", "*.*")]),
            width=10,
            style="primary.Outline.TButton"
        ).pack(side="left", padx=(0, 10))

        Button(
            按钮框架,
            text="选择文件夹",
            command=lambda: self.浏览文件夹(输入框="文件路径"),
            width=10,
            style="primary.Outline.TButton"
        ).pack(side="left")

        # 输出路径
        输出框架 = Frame(内容框架)
        输出框架.pack(fill="x", pady=(10, 0))

        Label(输出框架, text="输出图片路径:", font=("Microsoft YaHei", 10), style="dark.TLabel").pack(anchor="w",
                                                                                                          pady=(0, 5))

        输出按钮框架 = Frame(输出框架)
        输出按钮框架.pack(fill="x")

        self.输出路径输入框 = Entry(输出按钮框架, font=("Microsoft YaHei", 10))
        self.输出路径输入框.pack(side="left", fill="x", expand=True, padx=(0, 10))

        Button(
            输出按钮框架,
            text="另存为",
            command=lambda: self.浏览另存为(输入框="输出路径", 文件类型=[("PNG图片", "*.png")],
                                               默认名称="hidden.png"),
            width=10,
            style="primary.Outline.TButton"
        ).pack(side="left")

        # 操作按钮区域
        操作按钮框架 = Frame(内容框架)
        操作按钮框架.pack(fill="x", pady=15)

        # 按钮组框架
        按钮组框架 = Frame(操作按钮框架)
        按钮组框架.pack(expand=True)

        # 隐藏文件按钮
        Button(
            按钮组框架,
            text="🔒 隐藏文件",
            command=self.隐藏文件,
            style="success.TButton",
            width=15
        ).pack(side="left", padx=(0, 15))

        # 关于按钮
        Button(
            按钮组框架,
            text="ℹ️ 关于",
            command=self.显示关于窗口,
            style="info.Outline.TButton",
            width=15
        ).pack(side="left")

        # 日志输出区域
        日志框架 = Labelframe(self.主框架, text=" 操作日志 ", style="secondary.TLabelframe")
        日志框架.pack(fill="both", expand=True, pady=(10, 0))

        self.日志 = ScrolledText(日志框架, height=8, state="disabled", font=("Consolas", 9))
        self.日志.pack(fill="both", expand=True, padx=5, pady=5)

        # 拖放提示
        Label(self.主框架,
              text="📌 提示: 可以直接拖放图片或文件到窗口任意位置",
              font=("Microsoft YaHei", 9),
              style="inverse.TLabel").pack(pady=(10, 0))

    def 设置拖放功能(self):
        """设置拖放功能"""
        if not HAS_DND:
            return

        # 为整个主窗口框架设置拖放
        self.主框架.drop_target_register(DND_FILES)
        self.主框架.dnd_bind('<<Drop>>', self.处理拖放)

    def 处理拖放(self, 事件):
        """处理拖放事件"""
        if not HAS_DND:
            return

        数据 = 事件.data

        # 处理Windows路径格式
        if 数据.startswith('{') and 数据.endswith('}'):
            数据 = 数据[1:-1]

        # 处理多个文件的情况（只取第一个）
        文件列表 = 数据.split()
        if not 文件列表:
            return

        路径 = 文件列表[0]

        # 处理Windows路径中的花括号
        if '{' in 路径 and '}' in 路径:
            路径 = 路径.replace('{', '').replace('}', '')

        # 处理Windows路径中的反斜杠
        路径 = 路径.replace('\\', '/')

        # 自动识别文件类型并填充到对应输入框
        if 路径.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
            # 如果是图片文件，填充到图片路径并更新预览
            self.图片路径输入框.delete(0, tk.END)
            self.图片路径输入框.insert(0, 路径)
            self.更新预览(路径)
            self.记录日志(f"📷 已识别图片文件: {路径}")
        else:
            # 其他文件或文件夹，填充到文件路径
            self.文件路径输入框.delete(0, tk.END)
            self.文件路径输入框.insert(0, 路径)
            if os.path.isdir(路径):
                self.记录日志(f"📁 已识别文件夹: {路径}")
            else:
                self.记录日志(f"📄 已识别文件: {路径}")

    def 更新预览(self, 图片路径):
        """更新图片预览"""
        try:
            # 清除旧图片引用
            if self.预览照片:
                self.预览标签.config(image="")
                self.预览照片 = None

            # 打开并调整图片大小
            图片 = Image.open(图片路径)
            图片.thumbnail((140, 100))  # 增大预览图尺寸

            # 创建PhotoImage并显示
            self.预览照片 = ImageTk.PhotoImage(图片)
            self.预览标签.config(image=self.预览照片, text="")

            # 保持图片引用防止被垃圾回收
            self.预览图片 = 图片

        except Exception as 错误:
            self.预览标签.config(image="", text="预览加载失败")
            self.记录日志(f"❌ 预览加载失败: {str(错误)}", 错误=True)

    def 显示关于窗口(self):
        """显示关于窗口"""
        关于窗口 = tk.Toplevel(self.主窗口)
        关于窗口.title("关于")
        关于窗口.geometry("450x450")
        关于窗口.resizable(False, False)

        # 使关于窗口居中
        关于窗口.update_idletasks()
        宽度 = 关于窗口.winfo_width()
        高度 = 关于窗口.winfo_height()
        x = (关于窗口.winfo_screenwidth() // 2) - (宽度 // 2)
        y = (关于窗口.winfo_screenheight() // 2) - (高度 // 2)
        关于窗口.geometry(f"+{x}+{y}")

        # 主框架
        主框架 = Frame(关于窗口)
        主框架.pack(fill="both", expand=True, padx=20, pady=20)

        # 标题
        Label(主框架,
              text="图片藏文件工具",
              font=("Microsoft YaHei", 18, "bold"),
              style="primary.TLabel").pack(fill="x", pady=(0, 15))

        # 版本信息
        Label(主框架,
              text="版本: 1.0.0",
              font=("Microsoft YaHei", 11),
              style="dark.TLabel").pack(anchor="w", pady=(0, 10))

        # 开发日志区域
        日志框架 = Labelframe(主框架, text="开发日志", style="info.TLabelframe")
        日志框架.pack(fill="both", expand=True, pady=(0, 15))

        日志文本 = ScrolledText(日志框架, height=12, state="disabled", font=("Consolas", 10))
        日志文本.pack(fill="both", expand=True, padx=5, pady=5)

        # 添加开发日志内容
        更新日志 = """v1.0.0 (2025-07-24)
  感觉不错！停更！！！
  实现基本文件隐藏功能
  添加图片预览功能！！！
  支持拖放操作

v0.9.0 (2025-07-24)
- 完成核心功能开发
- 实现ZIP压缩功能
- 添加UI界面（bug多多）

v0.8.0 (2023-07-22)
  初步完成核心算法（啥也不是）
  测试文件隐藏功能"""

        日志文本.config(state="normal")
        日志文本.insert(tk.END, 更新日志)
        日志文本.config(state="disabled")

        # 按钮区域
        按钮框架 = Frame(主框架)
        按钮框架.pack(fill="x", pady=(10, 0))

        # 访问作者按钮
        Button(
            按钮框架,
            text="访问作者哔哩哔哩",
            command=lambda: webbrowser.open("https://space.bilibili.com/3494375101302875"),
            style="info.TButton",
            width=20
        ).pack(side="left", expand=True)

        Button(
            按钮框架,
            text="关闭",
            command=关于窗口.destroy,
            style="light.TButton",
            width=10
        ).pack(side="right", padx=(10, 0))

    def 浏览文件(self, 输入框, 文件类型=None):
        """浏览文件"""
        路径 = filedialog.askopenfilename(filetypes=文件类型 if 文件类型 else [("所有文件", "*.*")])
        if 路径:
            getattr(self, 输入框 + "输入框").delete(0, tk.END)
            getattr(self, 输入框 + "输入框").insert(0, 路径)

            # 如果是图片路径，更新预览
            if 输入框 == "图片路径":
                self.更新预览(路径)

    def 浏览文件夹(self, 输入框):
        """浏览文件夹"""
        路径 = filedialog.askdirectory()
        if 路径:
            getattr(self, 输入框 + "输入框").delete(0, tk.END)
            getattr(self, 输入框 + "输入框").insert(0, 路径)

    def 浏览另存为(self, 输入框, 文件类型=None, 默认名称=""):
        """浏览另存为"""
        路径 = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=文件类型 if 文件类型 else [("所有文件", "*.*")],
            initialfile=默认名称
        )
        if 路径:
            getattr(self, 输入框 + "输入框").delete(0, tk.END)
            getattr(self, 输入框 + "输入框").insert(0, 路径)

    def 记录日志(self, 消息, 错误=False):
        """记录日志"""
        self.日志.config(state="normal")
        标签 = "ERROR" if 错误 else "INFO"
        self.日志.insert(tk.END, 消息 + "\n", 标签)
        self.日志.tag_config("ERROR", foreground="red")
        self.日志.tag_config("INFO", foreground="green")
        self.日志.config(state="disabled")
        self.日志.see(tk.END)

    def 隐藏文件(self):
        """隐藏文件到图片"""
        图片路径 = self.图片路径输入框.get()
        文件路径 = self.文件路径输入框.get()
        输出路径 = self.输出路径输入框.get()

        if not all([图片路径, 文件路径, 输出路径]):
            self.记录日志("❌ 请填写所有必填项！", 错误=True)
            messagebox.showerror("错误", "请填写所有必填项！")
            return

        try:
            # 检查图片文件是否存在
            if not os.path.exists(图片路径):
                self.记录日志(f"❌ 图片文件不存在: {图片路径}", 错误=True)
                messagebox.showerror("错误", f"图片文件不存在: {图片路径}")
                return

            # 检查源文件/文件夹是否存在
            if not os.path.exists(文件路径):
                self.记录日志(f"❌ 源文件或文件夹不存在: {文件路径}", 错误=True)
                messagebox.showerror("错误", f"源文件或文件夹不存在: {文件路径}")
                return

            # 压缩处理
            zip缓冲区 = io.BytesIO()
            with zipfile.ZipFile(zip缓冲区, 'w', zipfile.ZIP_DEFLATED) as zip文件:
                if os.path.isdir(文件路径):
                    for 根目录, _, 文件列表 in os.walk(文件路径):
                        for 文件 in 文件列表:
                            完整路径 = os.path.join(根目录, 文件)
                            相对路径 = os.path.relpath(完整路径, start=文件路径)
                            zip文件.write(完整路径, 相对路径)
                    self.记录日志(f"📁 正在压缩文件夹: {文件路径}")
                else:
                    zip文件.write(文件路径, os.path.basename(文件路径))
                    self.记录日志(f"📄 正在压缩文件: {文件路径}")

            # 合并图片和ZIP
            with open(图片路径, 'rb') as 文件:
                合并数据 = 文件.read() + zip缓冲区.getvalue()

            with open(输出路径, 'wb') as 文件:
                文件.write(合并数据)

            成功消息 = f"✅ 文件已成功隐藏到: {输出路径}"
            self.记录日志(成功消息)
            messagebox.showinfo("成功", 成功消息)
        except Exception as 错误:
            错误消息 = f"❌ 隐藏失败: {str(错误)}"
            self.记录日志(错误消息, 错误=True)
            messagebox.showerror("错误", 错误消息)


if __name__ == "__main__":
    # 使用 tkinterdnd2 的 Tk 类
    if HAS_DND:
        主窗口 = TkinterDnD.Tk()
    else:
        主窗口 = tk.Tk()

    应用 = 图片隐藏工具(主窗口)
    主窗口.mainloop()