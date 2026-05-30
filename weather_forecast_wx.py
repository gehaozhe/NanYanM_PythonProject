import requests
import wx
import wx.adv
import wx.grid as gridlib
import threading
import matplotlib
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from datetime import datetime, timedelta

# 设置matplotlib使用TkAgg后端
matplotlib.use('WXAgg')

# Open-Meteo API URL
BASE_URL = "https://api.open-meteo.com/v1/forecast"
HISTORY_URL = "https://archive-api.open-meteo.com/v1/archive"

# 中国主要城市坐标映射
CITIES = {
    # 直辖市
    "北京": (39.9042, 116.4074),
    "上海": (31.2304, 121.4737),
    "天津": (39.3434, 117.3616),
    "重庆": (29.5630, 106.5516),
    
    # 省会城市
    "石家庄": (38.0428, 114.5149),
    "太原": (37.8716, 112.5489),
    "呼和浩特": (40.8174, 111.6578),
    "沈阳": (41.8057, 123.4315),
    "长春": (43.8170, 125.3245),
    "哈尔滨": (45.8038, 126.5349),
    "南京": (32.0603, 118.7969),
    "杭州": (30.2741, 120.1551),
    "合肥": (31.8206, 117.2272),
    "福州": (26.0745, 119.2965),
    "南昌": (28.6824, 115.8581),
    "济南": (36.6512, 117.1201),
    "郑州": (34.8021, 113.4668),
    "武汉": (30.5928, 114.3055),
    "长沙": (28.2278, 112.9388),
    "广州": (23.1291, 113.2644),
    "南宁": (22.8170, 108.3668),
    "海口": (20.0440, 110.3595),
    "成都": (30.5728, 104.0668),
    "贵阳": (26.5783, 106.7078),
    "昆明": (25.0389, 102.7183),
    "拉萨": (29.6469, 91.1175),
    "西安": (34.2658, 108.9541),
    "兰州": (36.0611, 103.8343),
    "西宁": (36.6172, 101.7782),
    "银川": (38.4680, 106.2319),
    "乌鲁木齐": (43.8256, 87.6168),
    "台北": (25.0330, 121.5654),
    
    # 计划单列市和经济特区
    "深圳": (22.5431, 114.0579),
    "厦门": (24.4798, 118.0894),
    "宁波": (29.8683, 121.5440),
    "青岛": (36.0671, 120.3826),
    "大连": (38.9140, 121.6147),
    "苏州": (31.2989, 120.5853),
    "温州": (28.0191, 120.7025),
    "东莞": (23.0478, 113.7333),
    "佛山": (23.0247, 113.2892),
    "泉州": (24.9088, 118.6080),
    "烟台": (37.5396, 121.4049)
}

# 天气代码映射
WEATHER_CODES = {
    0: "晴天",
    1: "多云",
    2: "多云",
    3: "阴天",
    45: "雾",
    48: "雾凇",
    51: "小雨",
    53: "小雨",
    55: "小雨",
    56: "冻雨",
    57: "冻雨",
    61: "中雨",
    63: "中雨",
    65: "中雨",
    66: "冻雨",
    67: "冻雨",
    71: "小雪",
    73: "小雪",
    75: "小雪",
    77: "雪粒",
    80: "阵雨",
    81: "阵雨",
    82: "阵雨",
    85: "阵雪",
    86: "阵雪",
    95: "雷暴",
    96: "雷暴伴冰雹",
    99: "雷暴伴冰雹"
}

class WeatherApp(wx.Frame):
    def __init__(self):
        super().__init__(None, title="天气预报", size=(800, 700))
        
        # 存储天气数据
        self.forecast_data = None
        self.history_data = None
        
        # 创建主面板
        self.panel = wx.Panel(self)
        
        # 创建垂直布局
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 创建顶部控制区域
        self.create_control_panel()
        
        # 创建天气信息显示区域
        self.create_weather_display()
        
        # 创建历史天气查询面板
        self.create_history_panel()
        
        # 创建图表区域
        self.create_chart_panel()
        
        # 设置主布局
        self.panel.SetSizer(self.main_sizer)
        
        # 居中显示
        self.Center()
        
        # 绑定窗口大小变化事件
        self.Bind(wx.EVT_SIZE, self.on_window_resize)
    
    def create_control_panel(self):
        """创建顶部控制区域"""
        control_panel = wx.Panel(self.panel)
        control_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # 城市选择
        city_label = wx.StaticText(control_panel, label="选择城市:")
        control_sizer.Add(city_label, 0, wx.ALL | wx.CENTER, 5)
        
        # 城市下拉框
        self.city_choice = wx.Choice(control_panel, choices=sorted(CITIES.keys()))
        self.city_choice.Select(0)  # 默认选择第一个城市
        control_sizer.Add(self.city_choice, 1, wx.ALL | wx.EXPAND, 5)
        
        # 查询按钮
        self.query_btn = wx.Button(control_panel, label="查询天气")
        self.query_btn.Bind(wx.EVT_BUTTON, self.on_query_weather)
        control_sizer.Add(self.query_btn, 0, wx.ALL, 5)
        
        # 加载状态
        self.loading_gauge = wx.Gauge(control_panel, range=100, size=(100, 20), style=wx.GA_HORIZONTAL | wx.GA_SMOOTH)
        self.loading_gauge.Hide()
        control_sizer.Add(self.loading_gauge, 1, wx.ALL | wx.EXPAND, 5)
        
        control_panel.SetSizer(control_sizer)
        self.main_sizer.Add(control_panel, 0, wx.ALL | wx.EXPAND, 10)
    
    def create_weather_display(self):
        """创建天气信息显示区域"""
        display_panel = wx.Panel(self.panel)
        display_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 当前天气信息
        current_panel = wx.Panel(display_panel, style=wx.BORDER_SIMPLE)
        current_sizer = wx.GridSizer(2, 2, 10, 10)
        
        # 当前温度
        self.temp_text = wx.StaticText(current_panel, label="当前温度: --°C", style=wx.ALIGN_CENTER)
        self.temp_text.SetFont(wx.Font(24, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        current_sizer.Add(self.temp_text, 0, wx.ALL | wx.EXPAND, 10)
        
        # 天气状况
        self.condition_text = wx.StaticText(current_panel, label="天气状况: --")
        self.condition_text.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        current_sizer.Add(self.condition_text, 0, wx.ALL | wx.CENTER, 10)
        
        # 湿度
        self.humidity_text = wx.StaticText(current_panel, label="湿度: --%")
        self.humidity_text.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        current_sizer.Add(self.humidity_text, 0, wx.ALL | wx.CENTER, 10)
        
        # 风速
        self.wind_text = wx.StaticText(current_panel, label="风速: -- km/h")
        self.wind_text.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        current_sizer.Add(self.wind_text, 0, wx.ALL | wx.CENTER, 10)
        
        current_panel.SetSizer(current_sizer)
        display_sizer.Add(current_panel, 0, wx.ALL | wx.EXPAND, 10)
        
        # 天气预报表格
        forecast_label = wx.StaticText(display_panel, label="未来天气预报 (7天):")
        forecast_label.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        display_sizer.Add(forecast_label, 0, wx.ALL, 10)
        
        self.forecast_grid = gridlib.Grid(display_panel)
        self.forecast_grid.CreateGrid(0, 5)
        
        # 设置列标题
        headers = ["日期", "最高温度 (°C)", "最低温度 (°C)", "天气状况", "湿度 (%)"]
        for col, header in enumerate(headers):
            self.forecast_grid.SetColLabelValue(col, header)
        
        # 设置网格列宽
        self.forecast_grid.SetColSize(0, 100)  # 日期列固定宽度
        self.forecast_grid.SetColSize(1, 100)  # 最高温度列固定宽度
        self.forecast_grid.SetColSize(2, 100)  # 最低温度列固定宽度
        self.forecast_grid.SetColSize(3, 150)  # 天气状况列较宽
        self.forecast_grid.SetColSize(4, 100)  # 湿度列固定宽度
        
        display_sizer.Add(self.forecast_grid, 1, wx.ALL | wx.EXPAND, 10)
        
        display_panel.SetSizer(display_sizer)
        self.main_sizer.Add(display_panel, 1, wx.ALL | wx.EXPAND, 10)
    
    def create_history_panel(self):
        """创建历史天气查询面板"""
        history_panel = wx.Panel(self.panel)
        history_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 历史天气标题
        history_label = wx.StaticText(history_panel, label="历史天气查询:")
        history_label.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        history_sizer.Add(history_label, 0, wx.ALL, 10)
        
        # 日期选择和查询
        date_panel = wx.Panel(history_panel)
        date_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # 开始日期
        start_label = wx.StaticText(date_panel, label="开始日期:")
        date_sizer.Add(start_label, 0, wx.ALL | wx.CENTER, 5)
        
        self.start_date = wx.adv.DatePickerCtrl(date_panel, style=wx.adv.DP_DROPDOWN | wx.adv.DP_SHOWCENTURY)
        # 默认选择7天前的日期
        default_date = wx.DateTime.Now() - wx.TimeSpan(7, 0, 0, 0)
        self.start_date.SetValue(default_date)
        date_sizer.Add(self.start_date, 0, wx.ALL, 5)
        
        # 结束日期
        end_label = wx.StaticText(date_panel, label="结束日期:")
        date_sizer.Add(end_label, 0, wx.ALL | wx.CENTER, 5)
        
        self.end_date = wx.adv.DatePickerCtrl(date_panel, style=wx.adv.DP_DROPDOWN | wx.adv.DP_SHOWCENTURY)
        self.end_date.SetValue(wx.DateTime.Now())
        date_sizer.Add(self.end_date, 0, wx.ALL, 5)
        
        # 查询按钮
        self.history_btn = wx.Button(date_panel, label="查询历史天气")
        self.history_btn.Bind(wx.EVT_BUTTON, self.on_query_history)
        date_sizer.Add(self.history_btn, 0, wx.ALL, 5)
        
        date_panel.SetSizer(date_sizer)
        history_sizer.Add(date_panel, 0, wx.ALL | wx.EXPAND, 10)
        
        # 历史天气表格
        self.history_grid = gridlib.Grid(history_panel)
        self.history_grid.CreateGrid(0, 5)
        
        # 设置列标题
        history_headers = ["日期", "最高温度 (°C)", "最低温度 (°C)", "平均温度 (°C)", "天气状况"]
        for col, header in enumerate(history_headers):
            self.history_grid.SetColLabelValue(col, header)
        
        # 设置网格列宽
        self.history_grid.SetColSize(0, 100)  # 日期列固定宽度
        self.history_grid.SetColSize(1, 100)  # 最高温度列固定宽度
        self.history_grid.SetColSize(2, 100)  # 最低温度列固定宽度
        self.history_grid.SetColSize(3, 100)  # 平均温度列固定宽度
        self.history_grid.SetColSize(4, 150)  # 天气状况列较宽
        
        history_sizer.Add(self.history_grid, 1, wx.ALL | wx.EXPAND, 10)
        
        history_panel.SetSizer(history_sizer)
        self.main_sizer.Add(history_panel, 1, wx.ALL | wx.EXPAND, 10)
    
    def create_chart_panel(self):
        """创建图表显示区域"""
        chart_panel = wx.Panel(self.panel)
        chart_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 图表标题
        chart_label = wx.StaticText(chart_panel, label="温度趋势图:")
        chart_label.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        chart_sizer.Add(chart_label, 0, wx.ALL, 10)
        
        # 创建matplotlib图表
        self.figure = Figure(figsize=(8, 3), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(chart_panel, -1, self.figure)
        
        # 连接图表重绘事件
        chart_panel.Bind(wx.EVT_SIZE, self.on_chart_resize)
        
        chart_sizer.Add(self.canvas, 1, wx.ALL | wx.EXPAND, 10)
        
        chart_panel.SetSizer(chart_sizer)
        self.main_sizer.Add(chart_panel, 1, wx.ALL | wx.EXPAND, 10)
    
    def on_query_weather(self, event):
        """查询天气事件处理"""
        self.query_btn.Disable()
        self.loading_gauge.Show()
        self.loading_gauge.Pulse()
        self.Refresh()
        
        # 启动线程查询天气
        threading.Thread(target=self.query_weather_thread).start()
    
    def query_weather_thread(self):
        """后台线程查询天气"""
        try:
            city = self.city_choice.GetStringSelection()
            if not city:
                wx.CallAfter(self.show_error, "请选择城市")
                return
            
            latitude, longitude = CITIES[city]
            
            # 调用Open-Meteo API
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
                "daily": "temperature_2m_max,temperature_2m_min,weather_code,relative_humidity_2m_max",
                "timezone": "Asia/Shanghai",
                "forecast_days": 7  # 增加到7天预报
            }
            
            response = requests.get(BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            self.forecast_data = response.json()
            
            # 在主线程更新UI
            wx.CallAfter(self.update_weather_display)
            
        except requests.exceptions.RequestException as e:
            wx.CallAfter(self.show_error, f"网络请求失败: {str(e)}")
        except Exception as e:
            wx.CallAfter(self.show_error, f"获取天气信息失败: {str(e)}")
        finally:
            # 恢复UI状态
            wx.CallAfter(self.query_btn.Enable)
            wx.CallAfter(self.loading_gauge.Hide)
    
    def update_weather_display(self):
        """更新天气信息显示"""
        if not self.forecast_data:
            return
        
        # 更新当前天气
        current = self.forecast_data["current"]
        self.temp_text.SetLabel(f"当前温度: {current['temperature_2m']}°C")
        self.condition_text.SetLabel(f"天气状况: {WEATHER_CODES.get(current['weather_code'], '未知')}")
        self.humidity_text.SetLabel(f"湿度: {current['relative_humidity_2m']}%")
        self.wind_text.SetLabel(f"风速: {current['wind_speed_10m']} km/h")
        
        # 更新天气预报表格
        self.forecast_grid.ClearGrid()
        self.forecast_grid.DeleteRows(0, self.forecast_grid.GetNumberRows())
        
        daily = self.forecast_data["daily"]
        for i in range(len(daily["time"])):
            self.forecast_grid.AppendRows()
            
            date = daily["time"][i]
            max_temp = daily["temperature_2m_max"][i]
            min_temp = daily["temperature_2m_min"][i]
            weather_code = daily["weather_code"][i]
            humidity = daily.get("relative_humidity_2m_max", ["--"] * len(daily["time"]))[i]
            
            # 格式化日期
            formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%m-%d")
            
            # 设置表格数据
            self.forecast_grid.SetCellValue(i, 0, formatted_date)
            self.forecast_grid.SetCellValue(i, 1, f"{max_temp}")
            self.forecast_grid.SetCellValue(i, 2, f"{min_temp}")
            self.forecast_grid.SetCellValue(i, 3, WEATHER_CODES.get(weather_code, "未知"))
            self.forecast_grid.SetCellValue(i, 4, f"{humidity}")
            
            # 设置单元格对齐方式
            for col in range(5):
                self.forecast_grid.SetCellAlignment(i, col, wx.ALIGN_CENTER, wx.ALIGN_CENTER)
        
        # 更新图表
        self.update_temperature_chart()
    
    def update_temperature_chart(self):
        """更新温度趋势图表"""
        if not self.forecast_data:
            return
        
        self.ax.clear()
        
        daily = self.forecast_data["daily"]
        dates = [datetime.strptime(date, "%Y-%m-%d").strftime("%m-%d") for date in daily["time"]]
        max_temps = daily["temperature_2m_max"]
        min_temps = daily["temperature_2m_min"]
        
        # 绘制折线图
        self.ax.plot(dates, max_temps, marker='o', label='最高温度', color='red')
        self.ax.plot(dates, min_temps, marker='o', label='最低温度', color='blue')
        
        # 设置图表属性
        self.ax.set_title('未来7天温度趋势')
        self.ax.set_xlabel('日期')
        self.ax.set_ylabel('温度 (°C)')
        self.ax.legend()
        self.ax.grid(True, linestyle='--', alpha=0.7)
        
        # 调整布局
        self.figure.tight_layout()
        
        # 更新图表
        self.canvas.draw()
        
    def on_window_resize(self, event):
        """窗口大小变化事件处理"""
        # 跳过最小化事件
        if event.GetSize().GetWidth() == 0 or event.GetSize().GetHeight() == 0:
            return
            
        # 让wxWidgets处理默认的大小变化
        event.Skip()
        
        # 延迟调整网格列宽，确保窗口已经完成调整
        wx.CallLater(100, self.adjust_grid_columns)
        
    def on_chart_resize(self, event):
        """图表面板大小变化事件处理"""
        # 跳过最小化事件
        if event.GetSize().GetWidth() == 0 or event.GetSize().GetHeight() == 0:
            return
            
        # 让wxWidgets处理默认的大小变化
        event.Skip()
        
        # 重绘图表以适应新大小
        self.canvas.Refresh()
        
    def adjust_grid_columns(self):
        """调整网格控件的列宽以适应窗口大小"""
        if not hasattr(self, 'forecast_grid') or not hasattr(self, 'history_grid'):
            return
            
        # 获取窗口宽度
        window_width = self.GetSize().GetWidth()
        
        # 计算每列的理想宽度（减去边距和间隙）
        if window_width > 600:
            # 只有在窗口足够宽时才调整列宽
            available_width = window_width - 200  # 减去边距和间隙
            column_width = available_width // 5  # 平均分配给5列
            
            # 为预报网格设置新的列宽
            for col in range(5):
                self.forecast_grid.SetColSize(col, column_width)
            
            # 为历史网格设置新的列宽
            for col in range(5):
                self.history_grid.SetColSize(col, column_width)
            
            # 重绘网格
            self.forecast_grid.Refresh()
            self.history_grid.Refresh()
    
    def on_query_history(self, event):
        """查询历史天气事件处理"""
        self.history_btn.Disable()
        self.loading_gauge.Show()
        self.loading_gauge.Pulse()
        self.Refresh()
        
        # 启动线程查询历史天气
        threading.Thread(target=self.query_history_thread).start()
    
    def query_history_thread(self):
        """后台线程查询历史天气"""
        try:
            city = self.city_choice.GetStringSelection()
            if not city:
                wx.CallAfter(self.show_error, "请选择城市")
                return
            
            latitude, longitude = CITIES[city]
            
            # 获取日期范围
            start_date = self.start_date.GetValue()
            end_date = self.end_date.GetValue()
            
            # 格式化为API需要的格式
            start_str = f"{start_date.GetYear():04d}-{start_date.GetMonth() + 1:02d}-{start_date.GetDay():02d}"
            end_str = f"{end_date.GetYear():04d}-{end_date.GetMonth() + 1:02d}-{end_date.GetDay():02d}"
            
            # 检查日期范围
            max_days = 90  # 限制最大查询范围
            start_dt = datetime.strptime(start_str, "%Y-%m-%d")
            end_dt = datetime.strptime(end_str, "%Y-%m-%d")
            
            if (end_dt - start_dt).days > max_days:
                wx.CallAfter(self.show_error, f"查询范围不能超过{max_days}天")
                return
            
            # 调用Open-Meteo历史API
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "daily": "temperature_2m_max,temperature_2m_min,temperature_2m_mean,weather_code",
                "timezone": "Asia/Shanghai",
                "start_date": start_str,
                "end_date": end_str
            }
            
            response = requests.get(HISTORY_URL, params=params, timeout=15)
            response.raise_for_status()
            
            self.history_data = response.json()
            
            # 在主线程更新UI
            wx.CallAfter(self.update_history_display)
            
        except requests.exceptions.RequestException as e:
            wx.CallAfter(self.show_error, f"网络请求失败: {str(e)}")
        except Exception as e:
            wx.CallAfter(self.show_error, f"获取历史天气失败: {str(e)}")
        finally:
            # 恢复UI状态
            wx.CallAfter(self.history_btn.Enable)
            wx.CallAfter(self.loading_gauge.Hide)
    
    def update_history_display(self):
        """更新历史天气显示"""
        if not self.history_data:
            return
        
        # 更新历史天气表格
        self.history_grid.ClearGrid()
        self.history_grid.DeleteRows(0, self.history_grid.GetNumberRows())
        
        daily = self.history_data["daily"]
        if not daily or not daily["time"]:
            wx.MessageBox("未找到历史天气数据", "提示", wx.OK | wx.ICON_INFORMATION)
            return
        
        for i in range(len(daily["time"])):
            self.history_grid.AppendRows()
            
            date = daily["time"][i]
            max_temp = daily["temperature_2m_max"][i]
            min_temp = daily["temperature_2m_min"][i]
            mean_temp = daily["temperature_2m_mean"][i]
            weather_code = daily["weather_code"][i]
            
            # 格式化日期
            formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
            
            # 设置表格数据
            self.history_grid.SetCellValue(i, 0, formatted_date)
            self.history_grid.SetCellValue(i, 1, f"{max_temp}")
            self.history_grid.SetCellValue(i, 2, f"{min_temp}")
            self.history_grid.SetCellValue(i, 3, f"{mean_temp}")
            self.history_grid.SetCellValue(i, 4, WEATHER_CODES.get(weather_code, "未知"))
            
            # 设置单元格对齐方式
            for col in range(5):
                self.history_grid.SetCellAlignment(i, col, wx.ALIGN_CENTER, wx.ALIGN_CENTER)
    
    def show_error(self, message):
        """显示错误信息"""
        wx.MessageBox(message, "错误", wx.OK | wx.ICON_ERROR)
    
    def show_error(self, message):
        """显示错误信息"""
        wx.MessageBox(message, "错误", wx.OK | wx.ICON_ERROR)

if __name__ == "__main__":
    app = wx.App()
    frame = WeatherApp()
    frame.Show()
    app.MainLoop()