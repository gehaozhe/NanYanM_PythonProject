import tkinter as tk

from tkinter import ttk, filedialog, messagebox
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
import base64
import threading
import time
import webbrowser
import re


def derive_key(password):
    salt = b'salt_'
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key


def encrypt_file(input_file, output_file, password):
    key = derive_key(password)
    f = Fernet(key)
    try:
        with open(input_file, 'rb') as original_file:
            original = original_file.read()
        encrypted = f.encrypt(original)

        file_ext = os.path.splitext(input_file)[1].encode()

        with open(output_file, 'wb') as encrypted_file:
            encrypted_file.write(len(file_ext).to_bytes(1, byteorder='big'))
            encrypted_file.write(file_ext)
            encrypted_file.write(encrypted)
        log_action(f"加密文件: {input_file} 到 {output_file}")
        return True
    except Exception as e:
        messagebox.showerror("错误", f"加密过程中出现错误: {e}")
        log_action(f"加密文件 {input_file} 失败: {e}")
        return False


def decrypt_file(input_file, output_file, password):
    try:
        key = derive_key(password)
        f = Fernet(key)
        with open(input_file, 'rb') as encrypted_file:
            ext_length = int.from_bytes(encrypted_file.read(1), byteorder='big')
            file_ext = encrypted_file.read(ext_length).decode()
            encrypted = encrypted_file.read()

        decrypted = f.decrypt(encrypted)
        output_file_with_ext = output_file + file_ext
        with open(output_file_with_ext, 'wb') as decrypted_file:
            decrypted_file.write(decrypted)
        log_action(f"解密文件: {input_file} 到 {output_file_with_ext}")
        return True
    except Exception as e:
        messagebox.showerror("错误", f"解密过程中出现错误: {e}")
        log_action(f"解密文件 {input_file} 失败: {e}")
        return False


def select_files(entry):
    file_paths = filedialog.askopenfilenames(
        filetypes=[("所有文件", "*.*"), ("文本文件", "*.txt"), ("图片文件", "*.jpg;*.png")])
    if file_paths:
        entry.delete(0, tk.END)
        entry.insert(0, ', '.join(file_paths))
        total_size = 0
        for file_path in file_paths:
            total_size += os.path.getsize(file_path)
        size_label.config(text=f"文件总大小: {total_size / 1024:.2f} KB")


def select_output_dir(entry):
    output_dir = filedialog.askdirectory()
    entry.delete(0, tk.END)
    entry.insert(0, output_dir)


def perform_encryption():
    input_files = input_file_entry.get().split(', ')
    password = password_entry.get()
    output_dir = output_dir_entry.get()
    if not input_files or not password or not output_dir:
        messagebox.showerror("错误", "请填写所有字段！")
        return
    progress_bar['maximum'] = len(input_files)
    progress_bar['value'] = 0
    root.update_idletasks()

    def encryption_thread():
        success_count = 0
        for i, input_file in enumerate(input_files):
            file_name = os.path.basename(input_file)
            output_file = os.path.join(output_dir, os.path.splitext(file_name)[0] + '.jm')
            if encrypt_file(input_file, output_file, password):
                success_count += 1
            progress_bar['value'] = i + 1
            root.update_idletasks()
        messagebox.showinfo("完成", f"加密完成！成功加密 {success_count} 个文件。")

    threading.Thread(target=encryption_thread).start()


def perform_decryption():
    input_files = input_file_entry.get().split(', ')
    password = password_entry.get()
    output_dir = output_dir_entry.get()
    if not input_files or not password or not output_dir:
        messagebox.showerror("错误", "请填写所有字段！")
        return
    progress_bar['maximum'] = len(input_files)
    progress_bar['value'] = 0
    root.update_idletasks()

    def decryption_thread():
        success_count = 0
        for i, input_file in enumerate(input_files):
            file_name = os.path.basename(input_file)
            output_file = os.path.join(output_dir, os.path.splitext(file_name)[0])
            if decrypt_file(input_file, output_file, password):
                success_count += 1
            progress_bar['value'] = i + 1
            root.update_idletasks()
        messagebox.showinfo("完成", f"解密完成！成功解密 {success_count} 个文件。")

    threading.Thread(target=decryption_thread).start()


def check_password_strength(password):
    length = len(password)
    has_upper = re.search(r'[A-Z]', password)
    has_lower = re.search(r'[a-z]', password)
    has_digit = re.search(r'\d', password)
    has_special = re.search(r'[!@#$%^&*(),.?":{}|<>]', password)

    if length < 8:
        strength = "弱"
    elif length < 12:
        if (has_upper and has_lower) or (has_upper and has_digit) or (has_lower and has_digit):
            strength = "中"
        else:
            strength = "弱"
    else:
        if has_upper and has_lower and has_digit and has_special:
            strength = "强"
        elif (has_upper and has_lower and has_digit) or (has_upper and has_lower and has_special) or (
                has_lower and has_digit and has_special):
            strength = "中"
        else:
            strength = "弱"

    password_strength_label.config(text=f"密码强度: {strength}")


def log_action(action):
    with open("encryption_log.txt", "a", encoding="utf-8") as log_file:
        log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {action}\n")


def show_about_info():
    messagebox.showinfo("关于", "制作者: NanYanM ")


# 创建主窗口
root = tk.Tk()
root.title("文件加密解密器    by NanYanM")
root.geometry("600x550")
root.resizable(False, False)
root.configure(bg="#f0f0f0")

# 标题标签
title_label = tk.Label(root, text="文件加密解密器    by NanYanM", font=("Arial", 18, "bold"), bg="#f0f0f0")
title_label.pack(pady=10)

# 分割线
separator = ttk.Separator(root, orient="horizontal")
separator.pack(fill="x", padx=20, pady=10)

# 内容框架
content_frame = tk.Frame(root, bg="#f0f0f0")
content_frame.pack(pady=10)

# 输入文件选择
input_file_label = ttk.Label(content_frame, text="选择文件:", font=("Arial", 12))
input_file_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
input_file_entry = ttk.Entry(content_frame, width=35, font=("Arial", 12))
input_file_entry.grid(row=0, column=1, padx=5, pady=5)
input_file_button = ttk.Button(content_frame, text="浏览", command=lambda: select_files(input_file_entry),
                               style="TButton")
input_file_button.grid(row=0, column=2, padx=5, pady=5)

# 文件大小显示
size_label = ttk.Label(content_frame, text="文件总大小: 0 KB", style="Size.TLabel")
size_label.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

# 密码输入
password_label = ttk.Label(content_frame, text="输入密码:", font=("Arial", 12))
password_label.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
password_entry = ttk.Entry(content_frame, width=35, show='*', font=("Arial", 12))
password_entry.grid(row=2, column=1, padx=5, pady=5)
password_entry.bind("<KeyRelease>", lambda event: check_password_strength(password_entry.get()))

# 密码强度提示
password_strength_label = ttk.Label(content_frame, text="密码强度: 未输入", style="Size.TLabel")
password_strength_label.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)

# 输出目录选择
output_dir_label = ttk.Label(content_frame, text="选择输出目录:", font=("Arial", 12))
output_dir_label.grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
output_dir_entry = ttk.Entry(content_frame, width=35, font=("Arial", 12))
output_dir_entry.grid(row=4, column=1, padx=5, pady=5)
output_dir_button = ttk.Button(content_frame, text="浏览", command=lambda: select_output_dir(output_dir_entry),
                               style="TButton")
output_dir_button.grid(row=4, column=2, padx=5, pady=5)

# 进度条
progress_bar = ttk.Progressbar(root, orient="horizontal", length=500, mode="determinate")
progress_bar.pack(pady=10)

# 按钮框架
button_frame = tk.Frame(root, bg="#f0f0f0")
button_frame.pack(pady=20, padx=20, fill=tk.X)

# 加密按钮
encrypt_button = ttk.Button(button_frame, text="加密", command=perform_encryption, style="Accent.TButton")
encrypt_button.grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)

# 解密按钮
decrypt_button = ttk.Button(button_frame, text="解密", command=perform_decryption, style="Accent.TButton")
decrypt_button.grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)

# 关于按钮
about_button = ttk.Button(button_frame, text="关于", command=show_about_info, style="TButton")
about_button.grid(row=0, column=2, padx=10, pady=10, sticky=tk.E)

# 样式设置
style = ttk.Style()
style.theme_use('default')
style.configure("TButton", font=("Arial", 12))
style.configure("Accent.TButton", font=("Arial", 12), foreground="white", background="#0078d7")
style.map("Accent.TButton",
          foreground=[('pressed', 'white'), ('active', 'white')],
          background=[('pressed', '!disabled', '#005a9e'), ('active', '#​0067b8')])

# 为文件大小和密码强度标签创建样式
style.configure("Size.TLabel", background="#f0f0f0", font=("Arial", 12))

# 运行主循环
root.mainloop()