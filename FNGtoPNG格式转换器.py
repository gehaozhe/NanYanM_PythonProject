import wx
import os
import sys
import time

from PIL import Image

# 直接在程序中实现image_to_fng和fng_to_image函数
def image_to_fng(image_path, fng_path=None):
    """
    将任意图片格式转换为FNG格式
    
    Args:
        image_path: 图片文件路径（支持所有PIL支持的格式）
        fng_path: 输出FNG文件路径，如果为None则使用原文件名.fng
    """
    # 打开图片（PIL自动处理不同格式）
    img = Image.open(image_path)
    # 转换为RGB模式
    img = img.convert('RGB')
    width, height = img.size
    
    # 如果没有指定输出路径，使用原文件名.fng
    if fng_path is None:
        fng_path = image_path.rsplit('.', 1)[0] + '.fng'
    
    # 生成FNG内容
    fng_content = []
    fng_content.append(f"{width}*{height}")
    
    # 遍历每个像素
    for y in range(height):
        row_colors = []
        for x in range(width):
            r, g, b = img.getpixel((x, y))
            hex_color = f"#{r:02x}{g:02x}{b:02x}"
            row_colors.append(hex_color)
        fng_content.append(" ".join(row_colors))
    
    # 写入FNG文件
    with open(fng_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(fng_content))

def fng_to_image(fng_path, image_path=None):
    """
    将FNG格式转换为任意图片格式
    
    Args:
        fng_path: FNG文件路径
        image_path: 输出图片文件路径，如果为None则使用原文件名.png
    """
    # 读取FNG文件
    with open(fng_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 解析尺寸
    size_line = lines[0].strip()
    width, height = map(int, size_line.split('*'))
    
    # 如果没有指定输出路径，使用原文件名.png
    if image_path is None:
        image_path = fng_path.rsplit('.', 1)[0] + '.png'
    
    # 创建新图片
    img = Image.new('RGB', (width, height))
    
    # 填充像素
    for y in range(height):
        if y + 1 >= len(lines):
            break
        colors = lines[y + 1].strip().split()
        for x in range(min(width, len(colors))):
            hex_color = colors[x]
            # 移除#号并转换为RGB
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            img.putpixel((x, y), (r, g, b))
    
    # 保存图片（根据文件扩展名自动选择格式）
    img.save(image_path)

class FNGConverterFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="FNG格式转换器", size=(600, 400))
        self.init_ui()
        self.Center()
    
    def init_ui(self):
        # 创建面板
        panel = wx.Panel(self)
        
        # 创建垂直布局管理器
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # 文件选择部分
        file_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # 输入文件标签
        self.input_label = wx.StaticText(panel, label="输入文件:")
        file_sizer.Add(self.input_label, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=10)
        
        # 输入文件路径文本框
        self.input_path = wx.TextCtrl(panel, size=(200, -1), style=wx.TE_CENTER)
        file_sizer.Add(self.input_path, flag=wx.RIGHT, border=10)
        
        # 文件格式显示框
        self.format_display = wx.StaticText(panel, label="")
        self.format_display.SetBackgroundColour(wx.LIGHT_GREY)
        self.format_display.SetMinSize((25, -1))  # 再缩小一半宽度
        self.format_display.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        file_sizer.Add(self.format_display, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=4)
        
        # 浏览按钮
        browse_btn = wx.Button(panel, label="浏览")
        browse_btn.Bind(wx.EVT_BUTTON, self.on_browse)
        file_sizer.Add(browse_btn)
        
        vbox.Add(file_sizer, flag=wx.ALL | wx.EXPAND, border=20)
        
        # 输出文件部分
        output_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # 输出文件标签
        self.output_label = wx.StaticText(panel, label="输出文件:")
        output_sizer.Add(self.output_label, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=10)
        
        # 输出文件路径文本框
        self.output_path = wx.TextCtrl(panel, size=(200, -1), style=wx.TE_CENTER)
        self.output_path.Bind(wx.EVT_TEXT, self.on_output_path_change)
        output_sizer.Add(self.output_path, flag=wx.RIGHT, border=10)
        
        # 输出文件格式显示框
        self.output_format = wx.StaticText(panel, label="")
        self.output_format.SetBackgroundColour(wx.LIGHT_GREY)
        self.output_format.SetMinSize((25, -1))  # 再缩小一半宽度
        self.output_format.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        output_sizer.Add(self.output_format, flag=wx.ALIGN_CENTER_VERTICAL)
        
        vbox.Add(output_sizer, flag=wx.LEFT | wx.RIGHT | wx.EXPAND, border=20)
        
        # 转换按钮
        convert_btn = wx.Button(panel, label="转换")
        convert_btn.Bind(wx.EVT_BUTTON, self.on_convert)
        vbox.Add(convert_btn, flag=wx.ALL | wx.CENTER, border=20)
        
        # 进度条
        self.progress_bar = wx.Gauge(panel, range=100, size=(250, 20))
        self.progress_bar.Hide()  # 初始隐藏
        vbox.Add(self.progress_bar, flag=wx.LEFT | wx.RIGHT | wx.CENTER, border=20)
        
        # 状态文本框
        self.status_text = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        vbox.Add(self.status_text, proportion=1, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, border=20)
        
        panel.SetSizer(vbox)
    
    def on_browse(self, event):
        # 打开文件选择对话框，支持所有常见图片格式
        wildcard = "支持的文件 (*.png;*.fng;*.jpg;*.jpeg;*.bmp;*.gif;*.tiff;*.tif;*.webp;*.ico;*.ppm;*.pgm;*.pbm)|*.png;*.fng;*.jpg;*.jpeg;*.bmp;*.gif;*.tiff;*.tif;*.webp;*.ico;*.ppm;*.pgm;*.pbm"
        with wx.FileDialog(self, "选择文件", wildcard=wildcard,
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return     # 用户取消了操作
            
            # 获取选择的文件路径
            input_path = fileDialog.GetPath()
            self.input_path.SetValue(input_path)
            
            # 确定输入文件格式
            input_ext = os.path.splitext(input_path)[1].lower()
            
            # 检查是否为图片格式（PIL支持的常见格式）
            image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif', '.webp', '.ico', '.ppm', '.pgm', '.pbm']
            
            if input_ext in image_extensions:
                input_format = input_ext[1:].upper()
                output_ext = ".fng"
            elif input_ext == '.fng':
                input_format = "FNG"
                output_ext = ".png"  # 默认输出为PNG
            else:
                input_format = "未知"
                output_ext = ".output"
            
            # 更新格式显示框
            self.format_display.SetLabel(f".{input_format.lower()}")
            
            # 自动生成输出文件路径
            output_path = os.path.splitext(input_path)[0] + output_ext
            self.output_path.SetValue(output_path)
    
    def on_output_path_change(self, event):
        # 当用户修改输出路径时，自动更新输出格式显示
        output_path = self.output_path.GetValue().strip()
        if output_path:
            output_ext = os.path.splitext(output_path)[1].lower()
            
            # 检查是否为图片格式
            image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif', '.webp', '.ico', '.ppm', '.pgm', '.pbm']
            
            if output_ext in image_extensions:
                output_format = output_ext[1:].upper()
            elif output_ext == '.fng':
                output_format = "FNG"
            else:
                output_format = "未知"
            
            self.output_format.SetLabel(f".{output_format.lower()}")
        else:
            self.output_format.SetLabel("")
    
    def on_convert(self, event):
        # 获取输入和输出路径
        input_path = self.input_path.GetValue().strip()
        output_path = self.output_path.GetValue().strip()
        
        # 验证输入
        if not input_path:
            self.show_error("请选择输入文件")
            return
        
        if not os.path.exists(input_path):
            self.show_error(f"输入文件不存在: {input_path}")
            return
        
        if not output_path:
            self.show_error("请指定输出文件路径")
            return
        
        try:
            # 执行转换
            input_ext = os.path.splitext(input_path)[1].lower()
            
            # 检查是否为图片格式
            image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif', '.webp', '.ico', '.ppm', '.pgm', '.pbm']
            
            if input_ext in image_extensions:
                # 图片转FNG
                input_format = input_ext[1:].upper()
                self.append_status(f"正在将{input_format}转换为FNG...")
                wx.Yield()  # 更新界面
                
                # 显示并更新进度条
                self.progress_bar.Show()
                self.progress_bar.SetValue(0)
                wx.Yield()  # 更新界面
                
                # 添加进度动画
                for i in range(101):
                    self.progress_bar.SetValue(i)
                    time.sleep(0.005)  # 每次暂停0.005秒，总时长约0.5秒
                    if i % 10 == 0:  # 每10%更新一次界面，避免过于频繁
                        wx.Yield()  # 更新界面
                
                image_to_fng(input_path, output_path)
                self.append_status(f"转换成功: {input_path} -> {output_path}")
                self.append_status("=" * 30)
                
                # 隐藏进度条
                self.progress_bar.Hide()
                wx.Yield()  # 更新界面
                
            elif input_ext == '.fng':
                # FNG转图片
                output_ext = os.path.splitext(output_path)[1].lower()
                if output_ext in image_extensions:
                    output_format = output_ext[1:].upper()
                    self.append_status(f"正在将FNG转换为{output_format}...")
                    wx.Yield()  # 更新界面
                    
                    # 显示并更新进度条
                    self.progress_bar.Show()
                    self.progress_bar.SetValue(0)
                    wx.Yield()  # 更新界面
                    
                    # 添加进度动画
                    for i in range(101):
                        self.progress_bar.SetValue(i)
                        time.sleep(0.005)  # 每次暂停0.005秒，总时长约0.5秒
                        if i % 10 == 0:  # 每10%更新一次界面，避免过于频繁
                            wx.Yield()  # 更新界面
                    
                    fng_to_image(input_path, output_path)
                    self.append_status(f"转换成功: {input_path} -> {output_path}")
                    self.append_status("=" * 30)
                    
                    # 隐藏进度条
                    self.progress_bar.Hide()
                    wx.Yield()  # 更新界面
                else:
                    self.show_error("不支持的输出图片格式，请使用常见图片格式如PNG、JPG等")
            else:
                self.show_error("不支持的文件格式，请使用图片文件或FNG文件")
        except Exception as e:
            self.show_error(f"转换失败: {str(e)}")
            self.append_status("=" * 30)
            # 确保错误时也隐藏进度条
            self.progress_bar.Hide()
            wx.Yield()  # 更新界面
    
    def show_error(self, message):
        # 显示错误信息
        self.append_status(f"错误: {message}", is_error=True)
        wx.MessageBox(message, "错误", wx.OK | wx.ICON_ERROR)
    
    def append_status(self, message, is_error=False):
        # 追加状态信息
        self.status_text.AppendText(message + "\n")
        # 如果是错误信息，滚动到底部
        if is_error:
            self.status_text.SetInsertionPointEnd()

class FNGConverterApp(wx.App):
    def OnInit(self):
        frame = FNGConverterFrame()
        frame.Show(True)
        return True

if __name__ == "__main__":
    app = FNGConverterApp()
    app.MainLoop()