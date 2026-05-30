import base64,os,random,sys,threading,time,chardet,json,tkinter.messagebox,tkinter as tk,logging
from logging.handlers import TimedRotatingFileHandler
from tkinter import simpledialog as sip

# 获取脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))

# 配置logging
log_dir = os.path.join(script_dir, 'log')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 获取当天的日期作为日志文件名
today = time.strftime('%Y-%m-%d')
log_file = os.path.join(log_dir, f'{today}.log')

# 创建日志文件处理器
handler = logging.FileHandler(log_file, encoding='utf-8')

# 设置日志格式
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# 获取logger实例
logger = logging.getLogger('11班抽取')
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# 添加控制台输出
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# 记录启动日志
logger.info('程序启动')

def detect_encoding(file_path):
    """自动检测文件编码"""
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding'] if result['encoding'] else 'gbk'
            return encoding
    except:
        return 'gbk'  # 默认使用 gbk

def check_and_create_file(file_path, default_content=None):
    """检查文件是否存在，如果不存在则创建"""
    if not os.path.exists(file_path):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                if default_content:
                    f.writelines(default_content)
            msgbox_create(0, '提示', f'已创建文件: {file_path}')
            return True
        except Exception as e:
            msgbox_create(2, '错误', f'创建文件 {file_path} 失败: {e}')
            return False
    return True

def b64_encode(data):
    global EXIT_WITH_AN_ERROR, The_ERROR_when_EXIT
    try:
        # 尝试多种编码
        for encoding in ['utf-8', 'gbk', 'gb2312', 'gb18030']:
            try:
                data_en = str(data).encode(encoding)
                b64_en = base64.b64encode(data_en)
                return b64_en.decode('ascii')  # base64 总是 ASCII
            except UnicodeEncodeError:
                continue
        # 如果所有编码都失败，使用 utf-8 并忽略错误
        data_en = str(data).encode('utf-8', errors='ignore')
        b64_en = base64.b64encode(data_en)
        return b64_en.decode('ascii')
    except Exception as error:
        msgbox_create(2, '致命错误', f'试图加密{data}时发生未知错误：\n{error}')
        EXIT_WITH_AN_ERROR = True
        The_ERROR_when_EXIT = 1
        EXIT()

def b64_decode(data_encoded):
    global EXIT_WITH_AN_ERROR, The_ERROR_when_EXIT
    try:
        # 先解码 base64
        b64_de = base64.b64decode(data_encoded.encode('ascii'))
        
        # 尝试多种编码解码
        for encoding in ['utf-8', 'gbk', 'gb2312', 'gb18030']:
            try:
                return b64_de.decode(encoding)
            except UnicodeDecodeError:
                continue
        
        # 如果所有编码都失败，使用 utf-8 并忽略错误
        return b64_de.decode('utf-8', errors='ignore')
    except Exception as error:
        msgbox_create(2, '致命错误', f'试图解密{data_encoded}时发生未知错误：\n{error}')
        EXIT_WITH_AN_ERROR = True
        The_ERROR_when_EXIT = 1
        EXIT()


class one_find:  # 名字模式
    closed_fun = None

    def show(self):  # 显示UI
        self.win.mainloop()

    def destroy(self):
        try:
            # 更严格地检查closed_fun是否存在且可调用
            if hasattr(self, 'closed_fun'):
                if self.closed_fun is not None:
                    if callable(self.closed_fun):
                        self.closed_fun()
        except Exception as error:
            print(f"Unknown ERROR: {error}")
        self.win.destroy()

    def unload(self):
        self.win.withdraw()

    def load(self):
        self.win.deiconify()

    def __init__(self):
        self.win = tk.Tk()

        def no_closing():
            global EXIT_WITH_AN_ERROR, The_ERROR_when_EXIT
            if msgbox_choice(1, '请确认', '是否关闭窗口'):
                EXIT_WITH_AN_ERROR = False
                The_ERROR_when_EXIT = 0
                EXIT()
            else:
                pass

        self.win.protocol("WM_DELETE_WINDOW", no_closing)

        self.win.geometry("720x580")
        self.win.title("11班抽取")

        self.label2 = tk.Label(self.win)
        self.label2.place(relx=0.15, rely=0.02, height=31, relwidth=0.7)
        self.label2.configure(text='欢迎使用！当前模式为 名字 退出请点击 设置', font=('宋体', 16))

        self.label = tk.Label(self.win)
        self.label.place(relx=0.85, rely=0.02, height=62, relwidth=0.15)
        self.label.configure(text='已抽次数\n（本次启动）', font=('宋体', 16))

        self.times_this_time = tk.StringVar()
        self.times_this_time_show = tk.Label(self.win)
        self.times_this_time_show.place(relx=0.87, rely=0.12, relheight=0.05, relwidth=0.11)
        self.times_this_time_show.configure(bg='white', font=('宋体', 16), textvariable=self.times_this_time)

        self.label1 = tk.Label(self.win)
        self.label1.place(relx=0.85, rely=0.16, height=62, relwidth=0.15)
        self.label1.configure(text='已抽次数\n（总次数）', font=('宋体', 16))

        self.times_all_time = tk.StringVar()
        self.times_all_time_show = tk.Label(self.win)
        self.times_all_time_show.place(relx=0.87, rely=0.26, relheight=0.05, relwidth=0.11)
        self.times_all_time_show.configure(bg='white', font=('宋体', 16), textvariable=self.times_all_time)

        self.label3 = tk.Label(self.win)
        self.label3.place(relx=0.85, rely=0.30, height=62, relwidth=0.15)
        self.label3.configure(text='防重复\n列表人数', font=('宋体', 16))

        self.name_random_false_reset = tk.StringVar()
        self.name_random_false_reset_show = tk.Label(self.win)
        self.name_random_false_reset_show.place(relx=0.87, rely=0.40, relheight=0.05, relwidth=0.11)
        self.name_random_false_reset_show.configure(bg='white', font=('宋体', 16),
                                                    textvariable=self.name_random_false_reset)

        self.label4 = tk.Label(self.win)
        self.label4.place(relx=0.85, rely=0.45, height=31, relwidth=0.15)
        self.label4.configure(text='当前时间', font=('宋体', 16))

        self.times = tk.StringVar()
        self.times_show = tk.Label(self.win)
        self.times_show.place(relx=0.87, rely=0.50, relheight=0.05, relwidth=0.11)
        self.times_show.configure(bg='white', font=('宋体', 14), textvariable=self.times)

        self.times1 = tk.StringVar()
        self.times1_show = tk.Label(self.win)
        self.times1_show.place(relx=0.87, rely=0.55, relheight=0.05, relwidth=0.11)
        self.times1_show.configure(bg='white', font=('宋体', 14), textvariable=self.times1)

        self.label5 = tk.Label(self.win)
        self.label5.place(relx=0.00, rely=0.02, height=62, relwidth=0.15)
        self.label5.configure(text='概率公示\n单位概率', font=('宋体', 16))

        self.percent_for_1 = tk.StringVar()
        self.percent_for_1_show = tk.Label(self.win)
        self.percent_for_1_show.place(relx=0.02, rely=0.12, relheight=0.05, relwidth=0.11)
        self.percent_for_1_show.configure(bg='white', font=('宋体', 14), textvariable=self.percent_for_1)

        self.label6 = tk.Label(self.win)
        self.label6.place(relx=0.00, rely=0.16, height=62, relwidth=0.15)
        self.label6.configure(text='概率公示\n平均概率', font=('宋体', 16))

        self.percent_for_normal = tk.StringVar()
        self.percent_for_normal_show = tk.Label(self.win)
        self.percent_for_normal_show.place(relx=0.02, rely=0.26, relheight=0.05, relwidth=0.11)
        self.percent_for_normal_show.configure(bg='white', font=('宋体', 14), textvariable=self.percent_for_normal)

        self.label7 = tk.Label(self.win)
        self.label7.place(relx=0.00, rely=0.30, height=62, relwidth=0.15)
        self.label7.configure(text='当前被抽\n被抽概率', font=('宋体', 16))

        self.percent_for_now = tk.StringVar()
        self.percent_for_now_show = tk.Label(self.win)
        self.percent_for_now_show.place(relx=0.02, rely=0.40, relheight=0.05, relwidth=0.11)
        self.percent_for_now_show.configure(bg='white', font=('宋体', 14), textvariable=self.percent_for_now)

        self.btn_one_find = tk.Button(self.win)
        self.btn_one_find.place(relx=0.15, rely=0.72, relheight=0.1, relwidth=0.32)
        self.btn_one_find.configure(text='抽取', font=('宋体', 32))

        self.btn_setting = tk.Button(self.win)
        self.btn_setting.place(relx=0.72, rely=0.72, relheight=0.1, relwidth=0.13)
        self.btn_setting.configure(text='设置', font=('宋体', 32))

        self.btn_switch_mode = tk.Button(self.win)
        self.btn_switch_mode.place(relx=0.495, rely=0.72, relheight=0.1, relwidth=0.20)
        self.btn_switch_mode.configure(text='数字模式', font=('宋体', 27))

        self.name_history = tk.StringVar()
        self.name_history_show = tk.Label(self.win)
        self.name_history_show.place(relx=0.15, rely=0.84, relheight=0.1, relwidth=0.7)
        self.name_history_show.configure(bg='white', font=('宋体', 32), textvariable=self.name_history)

        self.name = tk.StringVar()
        self.name_show = tk.Label(self.win)
        self.name_show.place(relx=0.15, rely=0.07, relheight=0.63, relwidth=0.7)
        self.name_show.configure(bg='white', font=('宋体', 120), textvariable=self.name)




# 添加切换回名字模式的函数
def switch_to_name_mode():
    global is_number_mode
    is_number_mode = False
    # 更新名字模式界面的标题
    one_find.label2.configure(text='欢迎使用！当前模式为 名字 退出请点击 设置', font=('宋体', 16))
    # 更新按钮文本
    one_find.btn_switch_mode.configure(text='数字模式', font=('宋体', 27))
    one_find.btn_switch_mode.configure(command=random_clicked_to_number_find)


class setting:
    closed_fun = None

    def show(self):
        self.win.mainloop()

    def destroy(self):
        try:
            # 检查closed_fun是否存在且可调用
            if hasattr(self, 'closed_fun') and self.closed_fun is not None and callable(self.closed_fun):
                self.closed_fun()
        except Exception as error:
            print(f"Unknown ERROR: {error}")
        self.win.destroy()

    def unload(self):
        self.win.withdraw()

    def load(self):
        self.win.deiconify()

    def __init__(self):
        self.win = tk.Tk()

        def no_closing():
            global EXIT_WITH_AN_ERROR, The_ERROR_when_EXIT
            if msgbox_choice(1, '请确认', '是否关闭窗口'):
                EXIT_WITH_AN_ERROR = False
                The_ERROR_when_EXIT = 0
                EXIT()
            else:
                pass

        self.win.protocol("WM_DELETE_WINDOW", no_closing)

        self.win.geometry("720x580")
        self.win.title("设置")

        self.label2 = tk.Label(self.win)
        self.label2.place(relx=0.15, rely=0.02, height=31, relwidth=0.7)
        self.label2.configure(text='欢迎使用！当前模式为 设置 退出请点击 退出', font=('宋体', 16))

        self.btn_show_percent_of_next = tk.Button(self.win)
        self.btn_show_percent_of_next.place(relx=0.15, rely=0.28, relheight=0.1, relwidth=0.32)
        self.btn_show_percent_of_next.configure(text='下次抽取概率', font=('宋体', 24))

        self.btn_show_percent_label = tk.Button(self.win)
        self.btn_show_percent_label.place(relx=0.53, rely=0.28, relheight=0.1, relwidth=0.32)
        self.btn_show_percent_label.configure(text='显示概率', font=('宋体', 32))

        self.btn_show_percent_of_name = tk.Button(self.win)
        self.btn_show_percent_of_name.place(relx=0.15, rely=0.39, relheight=0.1, relwidth=0.32)
        self.btn_show_percent_of_name.configure(text='查看概率', font=('宋体', 32))

        self.btn_change_mode_debug = tk.Button(self.win)
        self.btn_change_mode_debug.place(relx=0.53, rely=0.39, relheight=0.1, relwidth=0.32)
        self.btn_change_mode_debug.configure(text='开发者模式', font=('宋体', 32))

        self.btn_show_setting_in_one_find = tk.Button(self.win)
        self.btn_show_setting_in_one_find.place(relx=0.15, rely=0.5, relheight=0.1, relwidth=0.32)
        self.btn_show_setting_in_one_find.configure(text='显示参数', font=('宋体', 32))

        self.btn_reset_statistics = tk.Button(self.win)
        self.btn_reset_statistics.place(relx=0.53, rely=0.5, relheight=0.1, relwidth=0.32)
        self.btn_reset_statistics.configure(text='重置统计', font=('宋体', 32))

        self.btn_statistics = tk.Button(self.win)
        self.btn_statistics.place(relx=0.53, rely=0.61, relheight=0.1, relwidth=0.32)
        self.btn_statistics.configure(text='统计信息', font=('宋体', 32))

        self.btn_Reload = tk.Button(self.win)
        self.btn_Reload.place(relx=0.15, rely=0.61, relheight=0.1, relwidth=0.32)
        self.btn_Reload.configure(text='更新配置', font=('宋体', 32))

        self.btn_EXIT = tk.Button(self.win)
        self.btn_EXIT.place(relx=0.15, rely=0.72, relheight=0.1, relwidth=0.32)
        self.btn_EXIT.configure(text='退出', font=('宋体', 32))

        self.btn_to_one_find = tk.Button(self.win)
        self.btn_to_one_find.place(relx=0.70, rely=0.72, relheight=0.1, relwidth=0.15)
        self.btn_to_one_find.configure(text='名字模式', font=('宋体', 20))

        self.btn_to_number_mode = tk.Button(self.win)
        self.btn_to_number_mode.place(relx=0.53, rely=0.72, relheight=0.1, relwidth=0.15)
        self.btn_to_number_mode.configure(text='数字模式', font=('宋体', 20))
        self.btn_to_number_mode.configure(command=lambda: random_clicked_to_number_find())
        self.btn_to_number_mode.configure(state='normal')


class unload_setting_only_admin:
    closed_fun = None

    def show(self):
        self.win.mainloop()

    def destroy(self):
        try:
            # 检查closed_fun是否存在且可调用
            if hasattr(self, 'closed_fun') and self.closed_fun is not None and callable(self.closed_fun):
                self.closed_fun()
        except Exception as error:
            print(f"Unknown ERROR{error}")
        self.win.destroy()

    def unload(self):
        self.win.withdraw()

    def load(self):
        self.win.deiconify()

    def __init__(self):
        self.win = tk.Tk()

        def no_closing():
            global EXIT_WITH_AN_ERROR, The_ERROR_when_EXIT
            if msgbox_choice(1, '请确认', '是否关闭窗口'):
                EXIT_WITH_AN_ERROR = False
                The_ERROR_when_EXIT = 0
                EXIT()
            else:
                pass

        self.win.protocol("WM_DELETE_WINDOW", no_closing)

        self.win.geometry("720x580")
        self.win.title("Admin")
        self.win.configure(bg='black')

        self.label2 = tk.Label(self.win)
        self.label2.place(relx=0.15, rely=0.02, height=31, relwidth=0.7)
        self.label2.configure(text='Welcome! The current mode is *&#$*%^ Exit: @$#^%$&%', font=('宋体', 16),
                              bg='black',
                              fg='red')

        self.label = tk.Label(self.win)
        self.label.place(relx=0.15, rely=0.02, height=31, relwidth=0.7)
        self.label.configure(text='恭喜发现无效页面！', font=('宋体', 16), bg='black',
                             fg='red')

        self.btn_EXIT = tk.Button(self.win)
        self.btn_EXIT.place(relx=0.15, rely=0.72, relheight=0.1, relwidth=0.35)
        self.btn_EXIT.configure(text='back', font=('宋体', 32), bg='black', fg='red')

        self.btn_password_import = tk.Button(self.win)
        self.btn_password_import.place(relx=0.72, rely=0.72, relheight=0.1, relwidth=0.13)
        self.btn_password_import.configure(text='password', font=('宋体', 32), bg='black', fg='red')

        self.btn_666 = tk.Button(self.win)
        self.btn_666.place(relx=0.55, rely=0.72, relheight=0.1, relwidth=0.13)
        self.btn_666.configure(text='666', font=('宋体', 32), bg='black', fg='red')


def get_time_show():
    try:
        # 只更新一次时间
        one_find.times.set(time.strftime('%m月%d日', time.localtime(time.time())))
        one_find.times1.set(time.strftime('%H:%M:%S', time.localtime(time.time())))
        # 使用after方法安排下次更新，100毫秒后执行
        one_find.win.after(100, get_time_show)
    except Exception as e:
        # 防止窗口关闭后出现错误
        pass


def cycle_to_test(a, times):
    print(a)
    for i in range(int(times)):
        random_clicked_one()
    msgbox_create(0, 'info', 'over')


def get_time():
    return time.strftime('%m月%d日%H:%M:%S', time.localtime(time.time()))


def get_random():
    rnm = random.randint(1, random_max)
    return int(rnm)


def get_name():
    global random_max, random_randint_max
    name = ""
    random_max = sum(name_proportion)
    rnm = get_random()
    for i in range(len(name_proportion)):
        interval_max = sum(name_proportion[0:i + 1])
        if i == 0:
            interval_min = 0
        else:
            interval_min = sum(name_proportion[0:i])
        if interval_min < rnm <= interval_max:
            name = name_list_random[i]
    return name


def load_setting():
    global key, name_random_false_reset, name_random_false_ban_list, name_list_random, name_proportion, name_list, \
        double_list, EXIT_WITH_AN_ERROR, The_ERROR_when_EXIT, percent_find_1, name_list_number, students_data
    
    # 从victim.json读取名单数据
    victim_json_path = os.path.join(script_dir, 'victim.json')
    try:
        with open(victim_json_path, 'r', encoding='utf-8') as f:
            students_data = json.load(f)
    except FileNotFoundError:
        msgbox_create(2, '错误', f'victim.json文件不存在！路径：{victim_json_path}')
        EXIT_WITH_AN_ERROR = True
        The_ERROR_when_EXIT = 1
        EXIT()
    except json.JSONDecodeError as e:
        msgbox_create(2, '错误', f'victim.json文件格式错误：{e}')
        EXIT_WITH_AN_ERROR = True
        The_ERROR_when_EXIT = 1
        EXIT()
    except Exception as e:
        msgbox_create(2, '错误', f'读取victim.json文件时发生未知错误：{e}')
        EXIT_WITH_AN_ERROR = True
        The_ERROR_when_EXIT = 1
        EXIT()
    
    # 检查外部名单是否为空
    if not students_data or len(students_data) == 0:
        msgbox_create(2, '错误', 'victim.json文件为空！请填写学生名单')
        EXIT_WITH_AN_ERROR = True
        The_ERROR_when_EXIT = 1
        EXIT()
    
    # 从setting.dat读取其他配置
    setting_info = get_setting()[0]
    
    # 检查配置文件是否为空或格式错误
    if not setting_info or len(setting_info) < 10:  # 至少需要10行基本配置
        msgbox_create(1, '配置错误', '配置文件格式错误或内容不完整，将使用默认配置')
        # 使用默认配置
        setting_info = default_setting.copy()

    try:
        key = setting_info[1]
    except IndexError as error:
        msgbox_create(1, '错误', f'加载配置第1行时发生错误：{error}\n使用默认配置')
        key = "b'1qazxsw23Aw4Ffr4'"

    try:
        name_random_false_reset = int(setting_info[3])
    except (IndexError, ValueError) as error:
        msgbox_create(1, '错误', f'加载配置第3行时发生错误：{error}\n使用默认配置：60')
        name_random_false_reset = 60
    
    if name_random_false_reset > 100 or name_random_false_reset <= 0:
        msgbox_create(1, '错误',
                      f'加载配置第3行时发现问题：超出允许的范围(0,100]，为{name_random_false_reset}，将使用默认配置：60')
        name_random_false_reset = 60

    name_random_false_ban_list = []
    for i in range(5, 15):
        try:
            if setting_info[i] and setting_info[i] != "None":
                name_random_false_ban_list.append(setting_info[i])
        except IndexError:
            break  # 如果索引超出范围，停止添加

    # 从students_data中提取名字和概率
    name_list_random = []
    name_proportion = []
    
    for student in students_data:
        try:
            name_list_random.append(student['name'])
            name_proportion.append(int(student['prob']))
        except KeyError as e:
            msgbox_create(1, '警告', f'victim.txt文件中缺少字段：{e}')
        except ValueError as e:
            msgbox_create(1, '警告', f'victim.txt文件中概率值格式错误：{e}')
            name_proportion.append(100)  # 默认概率

    # 检查是否成功加载学生数据
    if not name_list_random:
        msgbox_create(2, '错误', '未从victim.txt文件中加载到有效学生数据')
        EXIT_WITH_AN_ERROR = True
        The_ERROR_when_EXIT = 1
        EXIT()

    # 检查概率总和是否过大
    if 2147483647 <= sum(name_proportion) < 9223372036854775807:
        msgbox_create(1, 'Warning', 'Warning: The sum of the parameters exceeds the 32-bit limit, an unknown error may occur!')
    if sum(name_proportion) >= 9223372036854775807:
        msgbox_create(2, 'Error', 'Warning: Since the sum of the parameters exceeds the 64-bit limit, an unknown error is highly likely, so terminate the program!')
        EXIT_WITH_AN_ERROR = True
        The_ERROR_when_EXIT = 1
        EXIT()
    
    name_list = ['Fail to get name']
    name_list_number = [0]
    for i in range(len(name_list_random)):
        for j in name_list:
            if name_list_random[i] == j:
                name_list_number.append(name_proportion[i])
    
    double_list = []
    one_find.name_random_false_reset.set(str(name_random_false_reset / 100 * len(name_list_random)))
    one_find.percent_for_1.set(f"{1 / sum(name_proportion) * 1000:.4f}‰")
    one_find.percent_for_normal.set(f"{1 / len(name_proportion) * 100:.4f}%")


def get_random_false():  # 伪随机
    global name_list, double_list, times_all_time, times_this_time, name_list_number, is_number_mode, students_data
    
    if is_number_mode:
        # 数字模式：随机生成1-54之间的数字
        number = random.randint(1, 54)
        # 根据编号找到对应的学生名字
        student_name = f"编号 {number}"
        if 'students_data' in globals():
            for student in students_data:
                if student.get('id') == number:
                    student_name = f"编号 {number} ({student.get('name')})"
                    break
        # 记录数字模式下的抽取结果
        history_add_file(student_name)
        # 更新抽取次数
        times_all_time += 1
        times_this_time += 1
        # 更新界面显示
        one_find.times_this_time.set(str(times_this_time))
        one_find.times_all_time.set(str(times_all_time))
        return str(number)
    
    # 名字模式的处理
    Do_random_False_True = True
    name = get_name()
    for ban_name in name_random_false_ban_list:
        if name == ban_name:
            Do_random_False_True = False
        else:
            pass
    if Do_random_False_True:
        double = False
        for i in name_list:
            if name == i:
                double = True
                double_list.append(i)

        if double:
            for i in double_list:
                while name == i:
                    name = get_name()
                    for j in name_list:
                        if name == j:
                            double_list.append(j)
            double_list = []

        name_list.append(str(name))

    print(sum(name_proportion))
    for i in range(len(name_list_random)):
        if name_list_random[i] == name:
            one_find.percent_for_now.set(
                f"{name_proportion[i] / (sum(name_proportion) - sum(name_list_number)) * 100:.4f}%")
            if Do_random_False_True:
                name_list_number.append(name_proportion[i])
    if len(name_list) - 1 >= name_random_false_reset / 100 * len(name_list_random):
        del name_list[1]
        del name_list_number[1]
        double_list = []
    print("冷却名单", name_list)
    print(name_list_number)

    history_add_file(str(name))
    times_all_time += 1
    times_this_time += 1

    one_find.times_this_time.set(str(times_this_time))
    one_find.times_all_time.set(str(times_all_time))

    return name


def operate_list_to_install_admin_setting():
    global operate_list
    if len(operate_list) > len(operate_list_TRUE):
        operate_list = []
    operate_list_IS_TRUE = True
    for i in range(len(operate_list)):
        if operate_list[i] == operate_list_TRUE[i]:
            pass
        else:
            operate_list_IS_TRUE = False
    if not operate_list_IS_TRUE:
        operate_list = []
    if len(operate_list) == len(operate_list_TRUE) and operate_list_IS_TRUE:
        one_find.unload()
        number_find.unload()
        setting.unload()
        unload_setting_only_admin.load()
        unload_setting_only_admin.btn_EXIT.configure(command=back)
        unload_setting_only_admin.btn_password_import.configure(command=admin_password)
        unload_setting_only_admin.btn_666.configure(command=test_lots_times_find)


def test_lots_times_find():
    times = sip.askinteger(title='times', prompt='循环次数')
    tt = threading.Thread(target=cycle_to_test, args=("1", times))  # 添加线程
    tt.setDaemon(True)
    tt.start()
    msgbox_create(0, 'info', '已新建线程')


def setting_add_file_b64(file_setting_b64, ADD_TRUE):
    # 使用脚本所在目录的文件
    file_setting_path = os.path.join(script_dir, file_setting_b64)
    
    setting_log_0 = get_setting_b64(file_setting_path)
    setting_log = []
    for i in setting_log_0:
        if ADD_TRUE:
            setting_log.append(b64_encode(i) + '\n')
        else:
            setting_log.append(b64_decode(i) + '\n')
    try:
        # 保存时使用 UTF-8 编码以确保兼容性
        with open(file_setting_path, 'w', encoding='utf-8') as file_write_setting:
            file_write_setting.writelines(setting_log)
    except FileNotFoundError:
        msgbox_error("文件不存在")
    except PermissionError:
        msgbox_error("无权访问文件")
    except Exception as error:
        msgbox_error(f'未知错误:{error}')


def get_setting_b64(file_setting_b64):
    # 使用脚本所在目录的文件
    file_setting_path = os.path.join(script_dir, file_setting_b64)
    
    try:
        encoding = detect_encoding(file_setting_path)
        with open(file_setting_path, 'r', encoding=encoding) as file_get_setting:
            setting_info = file_get_setting.read().splitlines()
    except FileNotFoundError:
        msgbox_error("文件不存在")
    except PermissionError:
        msgbox_error("无权访问文件")
    except Exception as error:
        msgbox_error(f'未知错误:{error}')
    return setting_info


def msgbox_error(msg):
    tkinter.messagebox.showerror('未知错误', msg)


def admin_password():
    # 使用脚本所在目录的setting.dat文件
    setting_dat_path = os.path.join(script_dir, 'setting.dat')
    
    if debug_mode:
        msgbox_create(0, 'info', 'PASS!')
        setting_add_file_b64('setting.dat', False)
        os.startfile(setting_dat_path)
        msgbox_create(1, 'info', '编辑完成后关闭此对话框以自动加密')
        setting_add_file_b64('setting.dat', True)
    else:
        password = sip.askstring(title='password', prompt='please import password')
        if password == main_password:
            msgbox_create(0, 'info', 'PASS!')
            setting_add_file_b64('setting.dat', False)
            os.startfile(setting_dat_path)
            msgbox_create(1, 'info', '编辑完成后关闭此对话框以自动加密')
            setting_add_file_b64('setting.dat', True)
        else:
            msgbox_create(1, 'warning', 'Password ERROR!')


def back():
    global UI_ID
    one_find.unload()
    setting.unload()
    unload_setting_only_admin.unload()
    if UI_ID == 0:
        one_find.load()
    elif UI_ID == 2:
        setting.load()


def random_clicked_one():
    global name1, operate_list, times_this_time, is_number_mode
    operate_list.append('random_clicked_one')
    operate_list_to_install_admin_setting()
    
    # 确保无论如何都会恢复按钮状态
    try:
        # 禁用按钮
        one_find.btn_one_find.configure(state='disabled')
        one_find.btn_one_find.update_idletasks()  # 立即更新界面
        
        name0 = name1
        try:
            # 统一调用get_random_false函数，它会根据模式返回不同的结果
            name1 = get_random_false()
        except Exception as error:
            msgbox_create(2, 'error', f'未知错误：{error}')
        
        if name0 == name1:
            one_find.name_show.configure(font=('宋体', 64))
            one_find.name.set('又是 ' + str(name1))
        else:
            one_find.name_show.configure(font=('宋体', 120))
            one_find.name.set(name1)
        one_find.name_history.set('上一次抽到的是 ' + str(name0))
        
        # 更新抽取次数
        # 注意：times_this_time和times_all_time已经在get_random_false函数中更新了
    finally:
        # 无论是否发生异常，都会恢复按钮状态为normal
        one_find.btn_one_find.configure(state='normal')
        one_find.btn_one_find.update_idletasks()  # 立即更新界面


def Reload_setting():
    global name_random_false_reset, random_max, random_randint_max, operate_list
    operate_list.append('Get_ALL_setting')
    operate_list_to_install_admin_setting()
    load_setting()
    msgbox_create(0, '提示', '刷新成功！')


def EXIT():
    # 使用脚本所在目录的setting.dat文件
    setting_dat_path = os.path.join(script_dir, 'setting.dat')
    
    if EXIT_WITH_AN_ERROR:
        if The_ERROR_when_EXIT == -1:
            pass
        elif The_ERROR_when_EXIT == 0:
            pass
        elif The_ERROR_when_EXIT == 1:
            msgbox_create(1, '警告', '疑似配置文件错误')

            ANS = msgbox_choice(1, '提示', '是否使用默认参数重新配置文件')
            print(ANS)
            if ANS:
                pass
            elif not ANS:
                sys.exit()
            os.remove(setting_dat_path)
            file_create = open(setting_dat_path, 'w', encoding='ANSI')
            file_create.close()
            with open(setting_dat_path, 'w', encoding='ANSI') as file_write_inside:
                file_write_inside.writelines(double_find_name_list)
            msgbox_create(0, '提示', '已重新配置文件')
        elif The_ERROR_when_EXIT == 2:
            pass
        else:
            print("UNKNOWN ERROR when Exit")

    try:
        # 检查对象的destroy方法是否存在且可调用
        # 对于one_find，需要检查它是否已经被初始化
        if 'one_find' in globals() and hasattr(one_find, 'destroy') and callable(one_find.destroy):
            try:
                one_find.destroy()
            except TypeError:
                # 如果是因为缺少self参数，说明one_find可能还没有被正确初始化
                pass
        if 'setting' in globals() and hasattr(setting, 'destroy') and callable(setting.destroy):
            try:
                setting.destroy()
            except TypeError:
                # 如果是因为缺少self参数，说明setting可能还没有被正确初始化
                pass
        if 'unload_setting_only_admin' in globals() and hasattr(unload_setting_only_admin, 'destroy') and callable(unload_setting_only_admin.destroy):
            try:
                unload_setting_only_admin.destroy()
            except TypeError:
                # 如果是因为缺少self参数，说明unload_setting_only_admin可能还没有被正确初始化
                pass
    except Exception as error:
        print(f"Unknown ERROR: {error}")
    finally:
        sys.exit(0)





def double_random_show_clear():
    pass


# 页面切换
# 添加全局变量用于模式切换
global is_number_mode
is_number_mode = False

def random_clicked_to_number_find():  # ID=1
    global UI_ID, operate_list, is_number_mode
    operate_list.append('random_clicked_to_number_find')
    operate_list_to_install_admin_setting()
    
    # 切换到数字模式
    is_number_mode = True
    
    # 更新数字模式界面的标题
    one_find.label2.configure(text='欢迎使用！当前模式为 数字 退出请点击 设置', font=('宋体', 16))
    
    # 更新按钮文本和命令为名字模式
    one_find.btn_switch_mode.configure(text='名字模式', font=('宋体', 27))
    one_find.btn_switch_mode.configure(command=random_clicked_to_one_find)
    
    # 确保显示的是数字模式界面
    if UI_ID != 1:
        if UI_ID == 1:
            number_find.unload()
        elif UI_ID == 2:
            setting.unload()
        UI_ID = 0
        one_find.load()
        one_find.show()


def main_clicked_to_setting():  # ID=2
    global UI_ID, operate_list
    operate_list.append('main_clicked_to_setting')
    operate_list_to_install_admin_setting()
    if UI_ID == 0:
        one_find.unload()
    UI_ID = 2
    setting.btn_to_number_mode.configure(state='normal')  # 设置为可用状态
    setting.btn_to_number_mode.configure(command=lambda: random_clicked_to_number_find())
    setting.btn_to_one_find.configure(command=random_clicked_to_one_find)
    setting.btn_EXIT.configure(command=EXIT)
    setting.btn_Reload.configure(command=Reload_setting)
    setting.btn_statistics.configure(command=statistics)
    setting.btn_reset_statistics.configure(command=reset_statistics)
    setting.btn_show_setting_in_one_find.configure(command=show_or_not_setting_in_one_find)
    setting.btn_change_mode_debug.configure(command=change_mode_debug)
    setting.btn_show_percent_of_name.configure(command=show_percent_of_names)
    setting.btn_show_percent_label.configure(command=show_percent_in_one_find)
    setting.btn_show_percent_of_next.configure(command=show_percent_next)
    setting.load()


def random_clicked_to_one_find():  # ID=0
    global UI_ID, operate_list, is_number_mode
    operate_list.append('random_clicked_to_one_find')
    operate_list_to_install_admin_setting()
    
    # 切换回名字模式
    is_number_mode = False
    
    # 更新界面标题
    one_find.label2.configure(text='欢迎使用！当前模式为 名字 退出请点击 设置', font=('宋体', 16))
    
    # 更新按钮文本和命令
    one_find.btn_switch_mode.configure(text='数字模式', font=('宋体', 27))
    one_find.btn_switch_mode.configure(command=random_clicked_to_number_find)
    
    # 卸载其他界面
    if UI_ID == 1:
        number_find.unload()
    elif UI_ID == 2:
        setting.unload()
    
    UI_ID = 0
    one_find.btn_one_find.configure(command=random_clicked_one)
    one_find.btn_setting.configure(command=main_clicked_to_setting)
    
    one_find.load()


"""
# setting每行定义 #
1.批注
2.加密秘钥 
3.批注
4.伪随机覆盖人数
5.批注
6~16.禁用伪随机名单
17.批注
18~93.1~38每人的概率，默认值100，值域=[0,∞]的整数，2行为一组，每组第一行名字第二行数据
"""


def get_setting():
    # 初始化变量以避免UnboundLocalError
    setting_info = []
    log_of_setting = []
    
    # 使用脚本所在目录的setting.dat文件
    setting_dat_path = os.path.join(script_dir, 'setting.dat')
    
    try:
        # 使用detect_encoding函数检测文件编码
        encoding = detect_encoding(setting_dat_path)
        with open(setting_dat_path, 'r', encoding=encoding) as file_log:
            log_of_setting = file_log.readlines()
        with open(setting_dat_path, 'r', encoding=encoding) as file_get_setting:
            setting_info = file_get_setting.read().splitlines()
    except FileNotFoundError:
        print("文件不存在")
        msgbox_create(2, '错误', '配置文件不存在！')
        # 使用系统默认编码创建文件
        with open(setting_dat_path, 'w', encoding='utf-8') as file_get_setting:
            # 写入默认配置
            for item in default_setting_en:
                file_get_setting.write(item)
        msgbox_create(0, '提示', '已创建文件并写入默认配置')
        # 重新读取刚创建的文件
        return get_setting()
    except PermissionError:
        print("无权访问文件")
        msgbox_create(2, '错误', '无权访问配置文件！')
        # 返回默认配置
        return default_setting, []
    except Exception as error:
        print(f'未知错误:{error}')
        msgbox_create(2, '错误', f'未知错误:{error}')
        # 返回默认配置作为备选
        return default_setting, []
    
    # 确保setting_info不为空
    if not setting_info:
        return default_setting, []
    
    # 解码配置信息
    setting_info_de = []
    try:
        for i in setting_info:
            if i.strip():
                setting_info_de.append(b64_decode(i))
    except Exception as e:
        print(f'解码错误:{e}')
        # 如果解码失败，返回默认配置
        return default_setting, []
    
    return setting_info_de, log_of_setting


def get_history():
    # 使用脚本所在目录的history.txt文件
    history_txt_path = os.path.join(script_dir, 'history.txt')
    
    try:
        encoding = detect_encoding(history_txt_path)
        with open(history_txt_path, 'r', encoding=encoding) as file_log:
            log_of_history = file_log.readlines()
        with open(history_txt_path, 'r', encoding=encoding) as file_get_history:
            history_info = file_get_history.read().splitlines()
    except FileNotFoundError:
        print("文件不存在")
        file_get_history = open(history_txt_path, 'w', encoding='utf-8')
        file_get_history.close()
        return [], []
    except PermissionError:
        print("无权访问文件")
        msgbox_create(2, '错误', '无权访问历史记录文件！')
        return [], []
    except Exception as error:
        print(f'未知错误:{error}')
        msgbox_create(2, '错误', f'未知错误:{error}')
        return [], []
    return history_info, log_of_history


def msgbox_create(type_msgbox, title, msg):
    root = tkinter.Tk()
    root.withdraw()
    if type_msgbox == 0:
        try:
            tkinter.messagebox.showinfo(title, msg)
        except Exception as error:
            print(f'Unknown ERROR{error}')
    elif type_msgbox == 1:
        try:
            tkinter.messagebox.showwarning(title, msg)
        except Exception as error:
            print(f'Unknown ERROR{error}')
    elif type_msgbox == 2:
        try:
            tkinter.messagebox.showerror(title, msg)
        except Exception as error:
            print(f'Unknown ERROR{error}')
    else:
        print(f'ERROR(Variable \'type_msgbox\' contains an unknown parameter {type_msgbox})')


def msgbox_choice(type_msgbox, title, msg):
    root = tkinter.Tk()
    root.withdraw()
    if type_msgbox == 0:  # return:yes/no 是/否
        try:
            return tkinter.messagebox.askquestion(title, msg)
        except Exception as error:
            print(f'Unknown ERROR{error}')
    elif type_msgbox == 1:  # return:True/False 是/否
        try:
            return tkinter.messagebox.askyesno(title, msg)
        except Exception as error:
            print(f'Unknown ERROR{error}')
    elif type_msgbox == 2:  # return:True/False 确定/取消
        try:
            return tkinter.messagebox.askokcancel(title, msg)
        except Exception as error:
            print(f'Unknown ERROR{error}')
    elif type_msgbox == 3:  # return:True/False 重试/取消
        try:
            return tkinter.messagebox.askretrycancel(title, msg)
        except Exception as error:
            print(f'Unknown ERROR{error}')
    elif type_msgbox == 4:  # return:True/False/None 是/否/取消
        try:
            return tkinter.messagebox.askyesnocancel(title, msg)
        except Exception as error:
            print(f'Unknown ERROR{error}')
    else:
        print(f'ERROR(Variable \'type_msgbox\' contains an unknown parameter {type_msgbox})')


def history_add_file(history_new_setting):
    # 使用脚本所在目录的history.txt文件
    history_txt_path = os.path.join(script_dir, 'history.txt')
    
    try:
        # 使用logging记录抽取历史
        logger.info(f'抽取结果: {history_new_setting}')
        
        # 仍然保留写入history.txt文件的功能，确保统计功能正常
        try:
            # 读取现有内容
            encoding = detect_encoding(history_txt_path)
            try:
                with open(history_txt_path, 'r', encoding=encoding) as f:
                    history_log = f.readlines()
            except:
                history_log = []
            
            # 添加新内容
            history_log.append(time.strftime('%m月%d日%H:%M:%S', time.localtime(time.time())) + '\n')
            history_log.append(str(history_new_setting) + '\n')
            
            # 使用 UTF-8 保存以确保兼容性
            with open(history_txt_path, 'w', encoding='utf-8') as file_write_history:
                file_write_history.writelines(history_log)
        except FileNotFoundError:
            logger.error("history.txt文件不存在，创建新文件")
            file_add_history = open(history_txt_path, 'w', encoding='utf-8')
            file_add_history.close()
        except PermissionError:
            logger.error("无权访问文件")
            msgbox_create(2, '错误', '无权访问历史记录文件！')
        except Exception as error:
            logger.error(f'写入history.txt文件失败: {error}')
    except Exception as error:
        logger.error(f'记录抽取历史失败: {error}')
        print(f'未知错误:{error}')
        msgbox_create(2, '错误', f'未知错误:{error}')


def setting_add_file(subject_new_setting):  # 添加配置设置
    # 使用脚本所在目录的setting.dat文件
    setting_dat_path = os.path.join(script_dir, 'setting.dat')
    
    subject_new_setting_en = b64_encode(subject_new_setting)
    try:
        setting_log = get_setting()[1]
        setting_log.append(str(subject_new_setting_en) + '\n')
        with open(setting_dat_path, 'w', encoding='ANSI') as file_write_setting:
            file_write_setting.writelines(setting_log)
    except FileNotFoundError:
        print("文件不存在")
        msgbox_create(2, '错误', '配置文件不存在！')
        file_create_setting = open(setting_dat_path, 'w', encoding='ANSI')
        msgbox_create(0, '提示', '已创建文件')
        file_create_setting.close()
    except PermissionError:
        print("无权访问文件")
        msgbox_create(2, '错误', '无权访问配置文件！')
    except Exception as error:
        print(f'未知错误:{error}')
        msgbox_create(2, '错误', f'试图写入配置文件时发生未知错误:{error}')


def statistics():
    # 检查name_list_random是否已定义
    global name_list_random
    if 'name_list_random' not in globals() or not name_list_random:
        msgbox_create(1, '警告', '学生名单未加载，请先加载配置')
        return
    
    True_to_PASS = True
    history_first = []
    try:
        history_first = get_history()[0]
    except Exception as error:
        msgbox_create(1, '警告', f'暂无日志文件\n{error}')
        True_to_PASS = False
    if not history_first and True_to_PASS:
        True_to_PASS = False
        msgbox_create(1, '警告', f'暂无日志')
    if True_to_PASS:
        history = []
        for i in range(int(len(history_first) / 2)):
            record = history_first[2 * i + 1]
            # 处理数字模式下的记录，提取括号中的姓名
            if '(' in record and ')' in record:
                # 提取括号中的内容
                start = record.find('(') + 1
                end = record.find(')')
                if start < end:
                    record = record[start:end]
            history.append(record)
        # 对名字列表进行去重处理，只统计唯一名字
        unique_names = list(set(name_list_random))
        name_list_random_statistics = []
        for i in unique_names:
            name_statistics = 0
            for j in history:
                if i == j:
                    name_statistics += 1
            name_list_random_statistics.append(name_statistics)
        # 更新为去重后的列表
        name_list_random = unique_names

        zip_max = zip(name_list_random, name_list_random_statistics)
        zip_max_used = sorted(zip_max, key=lambda x: x[1])
        result = zip(*zip_max_used)
        name_list_random_used, name_list_random_statistics_used = [list(x) for x in result]
        msg = ""
        if len(name_list_random) % 3 == 0:
            for i in range(int(len(name_list_random) / 3)):
                msg = msg + str(name_list_random_used[3 * i]) + ': ' + str(
                    name_list_random_statistics_used[3 * i]) + '次    ' + str(name_list_random_used[3 * i + 1]) + ': ' + str(
                    name_list_random_statistics_used[3 * i + 1]) + '次    ' + str(name_list_random_used[3 * i + 2]) + ': ' + str(
                    name_list_random_statistics_used[3 * i + 2]) + '次\n'
        elif len(name_list_random) % 3 == 1:
            for i in range(int((len(name_list_random) - 1) / 3)):
                msg = msg + str(name_list_random_used[3 * i]) + ': ' + str(
                    name_list_random_statistics_used[3 * i]) + '次    ' + str(name_list_random_used[3 * i + 1]) + ': ' + str(
                    name_list_random_statistics_used[3 * i + 1]) + '次    ' + str(name_list_random_used[3 * i + 2]) + ': ' + str(
                    name_list_random_statistics_used[3 * i + 2]) + '次\n'
            msg = msg + str(name_list_random_used[len(name_list_random) - 1]) + ': ' + str(
                name_list_random_statistics_used[len(name_list_random) - 1]) + '次'
        elif len(name_list_random) % 3 == 2:
            for i in range(int((len(name_list_random) - 2) / 3)):
                msg = msg + str(name_list_random_used[3 * i]) + ': ' + str(
                    name_list_random_statistics_used[3 * i]) + '次    ' + str(name_list_random_used[3 * i + 1]) + ': ' + str(
                    name_list_random_statistics_used[3 * i + 1]) + '次    ' + str(name_list_random_used[3 * i + 2]) + ': ' + str(
                    name_list_random_statistics_used[3 * i + 2]) + '次\n'
            msg = msg + str(name_list_random_used[len(name_list_random) - 2]) + ': ' + str(
                name_list_random_statistics_used[len(name_list_random) - 2]) + '次    ' + str(
                name_list_random_used[len(name_list_random) - 1]) + ': ' + str(
                name_list_random_statistics_used[len(name_list_random) - 1]) + '次'

        msgbox_create(0, '统计信息', msg)


def percent_show(is_really):
    if is_really:
        name_list_percent_really = []
        name_list_percent_really_inside = []
        for i in range(len(name_proportion)):
            name_list_percent_really.append(f"{name_proportion[i] / sum(name_proportion) * 100:.5f}%")
            name_list_percent_really_inside.append(f"{name_proportion[i] / sum(name_proportion) * 100}")
            print(f"{name_list_random[i]} {name_proportion[i] / sum(name_proportion) * 100}%")

        zip_max = zip(name_list_random, name_list_percent_really_inside, name_list_percent_really)
        zip_max_used = sorted(zip_max, key=lambda x: x[1])
        result = zip(*zip_max_used)
        name_list_random_used, useless, name_list_percent_really_used = [list(x) for x in result]
        msg = ""
        if len(name_list_random) % 3 == 0:
            for i in range(int(len(name_list_random) / 3)):
                msg = msg + str(name_list_random_used[3 * i]) + str(
                    name_list_percent_really_used[3 * i]) + '    ' + str(name_list_random_used[3 * i + 1]) + str(
                    name_list_percent_really_used[3 * i + 1]) + '    ' + str(name_list_random_used[3 * i + 2]) + str(
                    name_list_percent_really_used[3 * i + 2]) + '\n'
        elif len(name_list_random) % 3 == 1:
            for i in range(int((len(name_list_random) - 1) / 3)):
                msg = msg + str(name_list_random_used[3 * i]) + str(
                    name_list_percent_really_used[3 * i]) + '    ' + str(name_list_random_used[3 * i + 1]) + str(
                    name_list_percent_really_used[3 * i + 1]) + '    ' + str(name_list_random_used[3 * i + 2]) + str(
                    name_list_percent_really_used[3 * i + 2]) + '\n'
            msg = msg + str(name_list_random_used[len(name_list_random) - 1]) + str(
                name_list_percent_really_used[len(name_list_random) - 1])
        elif len(name_list_random) % 3 == 2:
            for i in range(int((len(name_list_random) - 2) / 3)):
                msg = msg + str(name_list_random_used[3 * i]) + str(
                    name_list_percent_really_used[3 * i]) + '    ' + str(name_list_random_used[3 * i + 1]) + str(
                    name_list_percent_really_used[3 * i + 1]) + '    ' + str(name_list_random_used[3 * i + 2]) + str(
                    name_list_percent_really_used[3 * i + 2]) + '\n'
            msg = msg + str(name_list_random_used[len(name_list_random) - 2]) + str(
                name_list_percent_really_used[len(name_list_random) - 2]) + '    ' + str(
                name_list_random_used[len(name_list_random) - 1]) + str(
                name_list_percent_really_used[len(name_list_random) - 1])

        msgbox_create(0, '概率公示(real)', msg)
    else:
        name_list_percent_really = []
        name_list_percent_really_inside = []
        sum_name_percent = sum(name_proportion)
        real_list = []
        for i in range(len(name_proportion)):
            real = False
            for j in name_list_random[i]:
                if j == "#":
                    real = True
            if real:
                real_list.append(int(i))
        for i in real_list:
            sum_name_percent -= name_proportion[i]
        normal_percent = sum_name_percent / (len(name_proportion) - len(real_list)) / sum(name_proportion) * 100
        print(f"其他 {normal_percent}%")
        for i in range(len(name_proportion)):
            real = False
            for j in real_list:
                if i == j:
                    real = True
            if real:
                name_list_percent_really.append(f"{name_proportion[i] / sum(name_proportion) * 100:.5f}%")
                name_list_percent_really_inside.append(f"{name_proportion[i] / sum(name_proportion) * 100}")
                print(f"{name_list_random[i]} {name_proportion[i] / sum(name_proportion) * 100}%")
            else:
                name_list_percent_really.append(f"{normal_percent:.5f}%")
                name_list_percent_really_inside.append(f"{normal_percent}")
        zip_max = zip(name_list_random, name_list_percent_really_inside, name_list_percent_really)
        zip_max_used = sorted(zip_max, key=lambda x: x[1])
        result = zip(*zip_max_used)
        name_list_random_used, useless, name_list_percent_really_used = [list(x) for x in result]
        msg = ""
        if len(name_list_random) % 3 == 0:
            for i in range(int(len(name_list_random) / 3)):
                msg = msg + str(name_list_random_used[3 * i]) + str(
                    name_list_percent_really_used[3 * i]) + '    ' + str(name_list_random_used[3 * i + 1]) + str(
                    name_list_percent_really_used[3 * i + 1]) + '    ' + str(name_list_random_used[3 * i + 2]) + str(
                    name_list_percent_really_used[3 * i + 2]) + '\n'
        elif len(name_list_random) % 3 == 1:
            for i in range(int((len(name_list_random) - 1) / 3)):
                msg = msg + str(name_list_random_used[3 * i]) + str(
                    name_list_percent_really_used[3 * i]) + '    ' + str(name_list_random_used[3 * i + 1]) + str(
                    name_list_percent_really_used[3 * i + 1]) + '    ' + str(name_list_random_used[3 * i + 2]) + str(
                    name_list_percent_really_used[3 * i + 2]) + '\n'
            msg = msg + str(name_list_random_used[len(name_list_random) - 1]) + str(
                name_list_percent_really_used[len(name_list_random) - 1])
        elif len(name_list_random) % 3 == 2:
            for i in range(int((len(name_list_random) - 2) / 3)):
                msg = msg + str(name_list_random_used[3 * i]) + str(
                    name_list_percent_really_used[3 * i]) + '    ' + str(name_list_random_used[3 * i + 1]) + str(
                    name_list_percent_really_used[3 * i + 1]) + '    ' + str(name_list_random_used[3 * i + 2]) + str(
                    name_list_percent_really_used[3 * i + 2]) + '\n'
            msg = msg + str(name_list_random_used[len(name_list_random) - 2]) + str(
                name_list_percent_really_used[len(name_list_random) - 2]) + '    ' + str(
                name_list_random_used[len(name_list_random) - 1]) + str(
                name_list_percent_really_used[len(name_list_random) - 1])

        msgbox_create(0, '概率公示', msg)


def show_percent_next():
    if debug_mode:
        name_list_percent_really = []
        name_list_percent_really_inside = []
        for i in range(len(name_proportion)):
            cooling = False
            for j in name_list:
                if name_list_random[i] == j:
                    cooling = True
            if cooling:
                name_list_percent_really.append(f"{0:.5f}%")
                name_list_percent_really_inside.append(f"{0}")
                print(f"{name_list_random[i]} {0}%")
            else:
                name_list_percent_really.append(
                    f"{name_proportion[i] / (sum(name_proportion) - sum(name_list_number)) * 100:.5f}%")
                name_list_percent_really_inside.append(
                    f"{name_proportion[i] / (sum(name_proportion) - sum(name_list_number)) * 100}")
            print(f"{name_list_random[i]} {name_proportion[i] / (sum(name_proportion) - sum(name_list_number)) * 100}%")

        zip_max = zip(name_list_random, name_list_percent_really_inside, name_list_percent_really)
        zip_max_used = sorted(zip_max, key=lambda x: x[1])
        result = zip(*zip_max_used)
        name_list_random_used, useless, name_list_percent_really_used = [list(x) for x in result]
        msg = ""
        if len(name_list_random) % 3 == 0:
            for i in range(int(len(name_list_random) / 3)):
                msg = msg + str(name_list_random_used[3 * i]) + str(
                    name_list_percent_really_used[3 * i]) + '    ' + str(name_list_random_used[3 * i + 1]) + str(
                    name_list_percent_really_used[3 * i + 1]) + '    ' + str(name_list_random_used[3 * i + 2]) + str(
                    name_list_percent_really_used[3 * i + 2]) + '\n'
        elif len(name_list_random) % 3 == 1:
            for i in range(int((len(name_list_random) - 1) / 3)):
                msg = msg + str(name_list_random_used[3 * i]) + str(
                    name_list_percent_really_used[3 * i]) + '    ' + str(name_list_random_used[3 * i + 1]) + str(
                    name_list_percent_really_used[3 * i + 1]) + '    ' + str(name_list_random_used[3 * i + 2]) + str(
                    name_list_percent_really_used[3 * i + 2]) + '\n'
            msg = msg + str(name_list_random_used[len(name_list_random) - 1]) + str(
                name_list_percent_really_used[len(name_list_random) - 1])
        elif len(name_list_random) % 3 == 2:
            for i in range(int((len(name_list_random) - 2) / 3)):
                msg = msg + str(name_list_random_used[3 * i]) + str(
                    name_list_percent_really_used[3 * i]) + '    ' + str(name_list_random_used[3 * i + 1]) + str(
                    name_list_percent_really_used[3 * i + 1]) + '    ' + str(name_list_random_used[3 * i + 2]) + str(
                    name_list_percent_really_used[3 * i + 2]) + '\n'
            msg = msg + str(name_list_random_used[len(name_list_random) - 2]) + str(
                name_list_percent_really_used[len(name_list_random) - 2]) + '    ' + str(
                name_list_random_used[len(name_list_random) - 1]) + str(
                name_list_percent_really_used[len(name_list_random) - 1])

        msgbox_create(0, '概率公示(real)', msg)
    else:
        msgbox_create(1, 'warning', '请先启用开发者模式！')


def reset_statistics():
    global times_all_time, times_this_time, name_list, operate_list, name_list_number
    # 使用脚本所在目录的history.txt文件
    history_txt_path = os.path.join(script_dir, 'history.txt')
    
    operate_list.append('reset_history')
    operate_list_to_install_admin_setting()
    reset_TRUE = msgbox_choice(1, '请确认', "是否重置历史记录？")
    print(reset_TRUE)
    if reset_TRUE:
        try:
            os.remove(history_txt_path)
            logger.info('重置历史记录成功')
        except Exception as error:
            logger.error(f'重置历史记录失败: {error}')
            msgbox_create(1, '错误', f'未知错误{error}')
        file_create = open(history_txt_path, 'w', encoding='ANSI')
        file_create.close()
        times_all_time = 0
        one_find.times_all_time.set(str(times_all_time))
    times_this_time = 0
    one_find.times_this_time.set(str(times_this_time))
    name_list = ["Fail to get name"]
    name_list_number = [0]
    for i in range(len(name_list_random)):
        for j in name_list:
            if name_list_random[i] == j:
                name_list_number.append(name_proportion[i])
    one_find.name.set('N/A')
    one_find.name_history.set('还没有上一次')
    # 检查number_find是否已定义
    if 'number_find' in globals():
        try:
            number_find.name.set('N/A')
        except:
            pass


def show_or_not_setting_in_one_find():
    global operate_list
    operate_list.append('hide_info')
    operate_list_to_install_admin_setting()
    global IS_showing
    one_find.label.pack()
    one_find.label1.pack()
    one_find.label4.pack()
    one_find.times_all_time_show.pack()
    one_find.times_this_time_show.pack()
    one_find.times_show.pack()
    one_find.times1_show.pack()
    if IS_showing:
        one_find.label.place(relx=1.85, rely=0.02, height=62, relwidth=0.15)
        one_find.times_this_time_show.place(relx=1.87, rely=0.12, relheight=0.05, relwidth=0.11)
        one_find.label1.place(relx=1.85, rely=1.16, height=62, relwidth=0.15)
        one_find.times_all_time_show.place(relx=1.87, rely=0.26, relheight=0.05, relwidth=0.11)
        one_find.label4.place(relx=1.85, rely=0.30, height=62, relwidth=0.15)
        one_find.times_show.place(relx=1.87, rely=0.40, relheight=0.05, relwidth=0.11)
        one_find.times1_show.place(relx=1.87, rely=0.45, relheight=0.05, relwidth=0.11)
        setting.btn_show_setting_in_one_find.configure(text='显示参数')
        IS_showing = False
    else:
        one_find.label.place(relx=0.85, rely=0.02, height=62, relwidth=0.15)
        one_find.times_this_time_show.place(relx=0.87, rely=0.12, relheight=0.05, relwidth=0.11)
        one_find.label1.place(relx=0.85, rely=0.16, height=62, relwidth=0.15)
        one_find.times_all_time_show.place(relx=0.87, rely=0.26, relheight=0.05, relwidth=0.11)
        one_find.label4.place(relx=0.85, rely=0.30, height=62, relwidth=0.15)
        one_find.times_show.place(relx=0.87, rely=0.40, relheight=0.05, relwidth=0.11)
        one_find.times1_show.place(relx=0.87, rely=0.45, relheight=0.05, relwidth=0.11)
        setting.btn_show_setting_in_one_find.configure(text='隐藏参数')
        IS_showing = True


def show_percent_in_one_find():
    global IS_showing_percent
    if debug_mode:
        one_find.label7.pack()
        one_find.percent_for_now_show.pack()
        if IS_showing_percent:
            one_find.label7.place(relx=10.00, rely=0.30, height=62, relwidth=0.15)
            one_find.percent_for_now_show.place(relx=10.02, rely=0.40, relheight=0.05, relwidth=0.11)
            setting.btn_show_percent_label.configure(text='显示概率')
            IS_showing_percent = False
        else:
            one_find.label7.place(relx=0.00, rely=0.30, height=62, relwidth=0.15)
            one_find.percent_for_now_show.place(relx=0.02, rely=0.40, relheight=0.05, relwidth=0.11)
            setting.btn_show_percent_label.configure(text='隐藏概率')
            IS_showing_percent = True
    else:
        msgbox_create(1, 'warning', '请先启用开发者模式！')


def show_percent_of_names():
    percent_show(debug_mode)


def change_mode_debug():
    global debug_mode
    if debug_mode:  # 开发者->用户
        debug_mode = False
        setting.btn_change_mode_debug.configure(text='开发者模式')
    else:  # 用户->开发者
        password = sip.askstring(title='password', prompt='please import password')
        if password == debug_password:
            msgbox_create(0, 'info', '密码正确,已切换至开发者模式！')
            debug_mode = True
            setting.btn_change_mode_debug.configure(text='用户模式')

        else:
            msgbox_create(1, 'warning', '密码错误！')


# 加载参数
main_password = 'A1B2C3D4'
debug_password = '2411'
debug_mode = False
EXIT_WITH_AN_ERROR = False
The_ERROR_when_EXIT = 0  # -1已处理0正常1配置文件错误2未知错误
key = b'2m9KG6R54Vbg'
name_random_false_ban_list = []
default_setting = ["# 加密秘钥（未启用）", "b'1qazxsw23Aw4Ffr4'", "# 伪随机上限人数百分比", "60", "# 禁用伪随机的名单",
                   "None", "None", "None", "None", "None", "None", "None", "None", "None", "None", "# 几率，默认100",
                   "潘玥", "100", "荆睿", "100", "周叙宏", "100", "徐晨熙", "100", "顾歆漪", "100", "尹子益",
                   "100", "彭世豪", "100", "刘梓舒", "100", "吴胤瑶", "100", "吴悠然", "100", "顾纾嫣", "100", "王艺雅",
                   "100", "陈乐瑶", "100", "段麟涵", "100", "端彦哲", "100", "冯钰泽", "100", "范子轩", "100", "陈梓桐",
                   "100", "葛昊哲", "100", "胡俊熙", "100", "韩良源", "100", "姜硕", "100", "匡蕊", "100", "柳浩宇",
                   "100", "罗涵月", "100", "廖金海", "100", "李思颖", "100", "鲁雨辰", "100", "刘卓菲", "100", "彭一丁",
                   "100", "邱子炫", "100", "时婧涵", "100", "孙于轩", "100", "王东甫", "100", "王航", "100", "王淑婷",
                   "100", "王天磊", "100", "王奕辰", "100", "汪雨希", "100", "王子宸", "100", "徐浩喆",
                   "100", "许昕冉", "100", "肖媛曦", "100", "杨纯", "100", "杨梓涵", "100", "周浩轩", "100", "朱金迪",
                   "100", "张可悦", "100", "郑鹏宇", "100", "张逸凡", "100", "左原菡", "100", "张媛萌", "100", "张尊涵",
                   "100"]
operate_list_TRUE = ['main_clicked_to_setting', 'reset_history', 'random_clicked_to_one_find', 'random_clicked_one',
                     'main_clicked_to_setting', 'hide_info', 'hide_info']
name_list_random = []
name_proportion = []
operate_list = []
double_find_times = 10
double_find_name_list = []
UI_ID = 0
# random_max will be set dynamically based on sum of probabilities
random_randint_max = 10000
name_random_false_reset = 60  # x%
name_list = ["Fail to get name"]
name_list_number = [0]
double_list = []
name1 = "N/A"
times_this_time = 0
times_all_time = 0
percent_find_1 = ''

# 文件检查 - 使用新的文件检查函数
default_setting_en = []
for iii in default_setting:
    default_setting_en.append(b64_encode(iii) + '\n')

# 检查并创建 setting.dat 文件
setting_dat_path = os.path.join(script_dir, 'setting.dat')
if not check_and_create_file(setting_dat_path, default_setting_en):
    EXIT_WITH_AN_ERROR = True
    The_ERROR_when_EXIT = 1
    EXIT()

# 检查victim.json文件是否存在
victim_json_path = os.path.join(script_dir, 'victim.json')
if not os.path.exists(victim_json_path):
    msgbox_create(2, '错误', f'victim.json文件不存在！路径：{victim_json_path}')
    EXIT_WITH_AN_ERROR = True
    The_ERROR_when_EXIT = 1
    EXIT()

# 检查并创建 history.txt 文件
history_txt_path = os.path.join(script_dir, 'history.txt')
if not check_and_create_file(history_txt_path):
    msgbox_create(1, '警告', '历史文件创建失败，统计功能可能受限')

# 读取历史记录次数
try:
    encoding = detect_encoding(history_txt_path)
    with open(history_txt_path, 'r', encoding=encoding) as file:
        times_all_time = len(file.read().splitlines()) // 2
except:
    times_all_time = 0

# 加载UI
show_or_not_setting_in_one_find_first_chick = False
IS_showing = False
IS_showing_percent = True
one_find = one_find()

setting = setting()
setting.unload()

unload_setting_only_admin = unload_setting_only_admin()
unload_setting_only_admin.unload()

one_find.name.set('N/A')
one_find.name_history.set('还没有上一次')
one_find.percent_for_now.set('N/A')
one_find.times_this_time.set(str(times_this_time))
one_find.times_all_time.set(str(times_all_time))
# 初始化模式标志
is_number_mode = False
    
one_find.btn_one_find.configure(command=random_clicked_one)
one_find.btn_setting.configure(command=main_clicked_to_setting)
one_find.btn_switch_mode.configure(command=random_clicked_to_number_find)

one_find.label.pack()
one_find.label1.pack()
one_find.label3.pack()
one_find.label4.pack()
one_find.times_all_time_show.pack()
one_find.times_this_time_show.pack()
one_find.times_show.pack()
one_find.times1_show.pack()
one_find.name_random_false_reset_show.pack()
one_find.label7.pack()
one_find.percent_for_now_show.pack()

one_find.label.pack_forget()
one_find.label1.pack_forget()
one_find.label3.pack_forget()
one_find.label4.pack_forget()
one_find.times_all_time_show.pack_forget()
one_find.times_this_time_show.pack_forget()
one_find.times_show.pack_forget()
one_find.name_random_false_reset_show.pack_forget()
one_find.times1_show.pack_forget()
one_find.label7.pack_forget()
one_find.percent_for_now_show.pack_forget()

show_or_not_setting_in_one_find()
one_find.unload()
# 加载配置文件
load_setting()

# 不再使用单独线程，直接调用get_time_show函数，它会通过after方法自动循环更新
one_find.times.set('unknown')
one_find.times1.set('unknown')

# 在UI加载完成后启动时间更新
get_time_show()

# 显示
one_find.load()
one_find.show()