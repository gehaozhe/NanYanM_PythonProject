import tkinter
from tkinter import messagebox,simpledialog
def show():
    messagebox.showinfo(': )','你的桌面被我发射了二向箔变成了屏保(一脸坏笑)')
    密码文件 = 'password.txt'
    if not os.path.exists(密码文件):
        with open(密码文件, 'w', encoding='utf-8') as f:
            f.write('123456')
        messagebox.showinfo("提示", f"密码文件 '{密码文件}' 不存在，已创建默认密码文件")
    try:
        with open(密码文件, 'r', encoding='utf-8') as f:
            正确的密码 = f.read().strip()
    except:
        messagebox.showerror("错误", "读取密码文件失败，使用默认密码")
        正确的密码 = '123456'
    输入的密码 = simpledialog.askstring("密码验证", "请输入解除密码:", show='*')
    
    # 验证密码
    if 输入的密码 == 正确的密码:
        messagebox.showinfo("成功", "密码正确，正在回滚二向箔...")
        tk.destroy()
    else:
        messagebox.showerror("错误", "密码错误，请重试！")
tk = tkinter.Tk()
tk.attributes('-fullscreen', True)
tk.attributes('-alpha', 0.01)
button = tkinter.Button(tk,command=show,width=tk.winfo_screenwidth(),height=tk.winfo_screenheight())
button.pack()
tk.mainloop()