import requests
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import threading

# Open-Meteo API URL
BASE_URL = "https://api.open-meteo.com/v1/forecast"

# 中国主要城市坐标映射（包含所有省会城市和主要城市）
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
    "烟台": (37.5396, 121.4049),
    "石家庄": (38.0428, 114.5149),
    "唐山": (39.6334, 118.1781),
    "邯郸": (36.6075, 114.4773),
    "保定": (38.8781, 115.4845),
    "张家口": (40.8106, 114.8759),
    "承德": (40.9798, 117.9335),
    "沧州": (38.3046, 116.8393),
    "廊坊": (39.5171, 116.7009),
    "衡水": (37.7272, 115.7282),
    "邢台": (37.0708, 114.5149),
    "秦皇岛": (39.9212, 119.5953),
    "张家口": (40.8106, 114.8759),
    "承德": (40.9798, 117.9335),
    "沧州": (38.3046, 116.8393),
    "廊坊": (39.5171, 116.7009),
    "衡水": (37.7272, 115.7282),
    "邢台": (37.0708, 114.5149),
    "秦皇岛": (39.9212, 119.5953)
}

class WeatherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("天气预报")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        # 设置样式
        self.style = ttk.Style()
        self.style.configure("TLabel", font=("Arial", 12))
        self.style.configure("TButton", font=("Arial", 10))
        self.style.configure("TCombobox", font=("Arial", 10))
        
        # 创建主框架
        self.main_frame = ttk.Frame(root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 城市选择
        self.city_label = ttk.Label(self.main_frame, text="选择城市:")
        self.city_label.pack(pady=5)
        
        self.city_var = tk.StringVar()
        # 按字母排序城市列表
        sorted_cities = sorted(CITIES.keys())
        self.city_combo = ttk.Combobox(self.main_frame, textvariable=self.city_var, values=sorted_cities, state="readonly")
        self.city_combo.current(0)  # 默认选择北京
        self.city_combo.pack(pady=5, fill=tk.X)
        
        # 查询按钮和加载状态
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(pady=10, fill=tk.X)
        
        self.query_btn = ttk.Button(self.button_frame, text="查询天气", command=self.start_get_weather)
        self.query_btn.pack(side=tk.LEFT, expand=True)
        
        # 加载指示器
        self.loading_label = ttk.Label(self.button_frame, text="", font=("Arial", 10))
        self.loading_label.pack(side=tk.RIGHT, padx=10)
        
        # 结果显示区域
        self.result_frame = ttk.LabelFrame(self.main_frame, text="天气信息", padding="10")
        self.result_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 当前天气
        self.current_frame = ttk.Frame(self.result_frame)
        self.current_frame.pack(fill=tk.X, pady=5)
        
        self.temp_label = ttk.Label(self.current_frame, text="当前温度: --°C", font=("Arial", 14, "bold"))
        self.temp_label.pack(side=tk.LEFT, padx=10)
        
        self.condition_label = ttk.Label(self.current_frame, text="天气状况: --")
        self.condition_label.pack(side=tk.RIGHT, padx=10)
        
        # 天气详情
        self.detail_frame = ttk.Frame(self.result_frame)
        self.detail_frame.pack(fill=tk.X, pady=5)
        
        self.humidity_label = ttk.Label(self.detail_frame, text="湿度: --%")
        self.humidity_label.pack(side=tk.LEFT, padx=10)
        
        self.wind_label = ttk.Label(self.detail_frame, text="风速: -- km/h")
        self.wind_label.pack(side=tk.RIGHT, padx=10)
        
        # 未来天气预报
        self.forecast_label = ttk.Label(self.result_frame, text="未来天气预报:", font=("Arial", 12, "bold"))
        self.forecast_label.pack(anchor=tk.W, pady=5)
        
        self.forecast_tree = ttk.Treeview(self.result_frame, columns=("date", "temp_min", "temp_max", "condition"), show="headings", height=5)
        self.forecast_tree.heading("date", text="日期")
        self.forecast_tree.heading("temp_min", text="最低温度(°C)")
        self.forecast_tree.heading("temp_max", text="最高温度(°C)")
        self.forecast_tree.heading("condition", text="天气状况")
        
        # 设置列宽
        self.forecast_tree.column("date", width=100)
        self.forecast_tree.column("temp_min", width=100, anchor=tk.CENTER)
        self.forecast_tree.column("temp_max", width=100, anchor=tk.CENTER)
        self.forecast_tree.column("condition", width=150, anchor=tk.CENTER)
        
        self.forecast_tree.pack(fill=tk.BOTH, expand=True, pady=5)
    
    def start_get_weather(self):
        """启动线程获取天气信息，避免UI阻塞"""
        # 禁用查询按钮，显示加载状态
        self.query_btn.config(state=tk.DISABLED)
        self.loading_label.config(text="加载中...")
        
        # 清空之前的显示内容
        self.temp_label.config(text="当前温度: --°C")
        self.condition_label.config(text="天气状况: --")
        self.humidity_label.config(text="湿度: --%")
        self.wind_label.config(text="风速: -- km/h")
        
        # 清空树形视图
        for item in self.forecast_tree.get_children():
            self.forecast_tree.delete(item)
        
        # 创建线程执行网络请求
        thread = threading.Thread(target=self.get_weather)
        thread.daemon = True  # 设置为守护线程
        thread.start()
    
    def get_weather(self):
        city = self.city_var.get()
        if not city:
            self.root.after(0, lambda: messagebox.showerror("错误", "请选择城市"))
            self.root.after(0, self.reset_ui)
            return
        
        latitude, longitude = CITIES[city]
        
        try:
            # 调用Open-Meteo API，设置超时
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
                "daily": "temperature_2m_max,temperature_2m_min,weather_code",
                "timezone": "Asia/Shanghai",
                "forecast_days": 5
            }
            
            # 设置超时时间为10秒
            response = requests.get(BASE_URL, params=params, timeout=10)
            response.raise_for_status()  # 检查请求是否成功
            
            data = response.json()
            
            # 在主线程中更新UI
            self.root.after(0, lambda: self.display_weather(data, city))
            
        except requests.exceptions.RequestException as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"网络请求失败: {str(e)}"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"获取天气信息失败: {str(e)}"))
        finally:
            # 恢复UI状态
            self.root.after(0, self.reset_ui)
    
    def reset_ui(self):
        """恢复UI状态"""
        self.query_btn.config(state=tk.NORMAL)
        self.loading_label.config(text="")
    
    def display_weather(self, data, city):
        # 更新标题
        self.root.title(f"天气预报 - {city}")
        
        # 显示当前天气
        current = data["current"]
        self.temp_label.config(text=f"当前温度: {current['temperature_2m']}°C")
        self.humidity_label.config(text=f"湿度: {current['relative_humidity_2m']}%")
        self.wind_label.config(text=f"风速: {current['wind_speed_10m']} km/h")
        self.condition_label.config(text=f"天气状况: {self.get_weather_condition(current['weather_code'])}")
        
        # 清空之前的预报数据
        for item in self.forecast_tree.get_children():
            self.forecast_tree.delete(item)
        
        # 显示未来天气预报
        daily = data["daily"]
        for i in range(len(daily["time"])):
            date = daily["time"][i]
            temp_min = daily["temperature_2m_min"][i]
            temp_max = daily["temperature_2m_max"][i]
            weather_code = daily["weather_code"][i]
            condition = self.get_weather_condition(weather_code)
            
            # 格式化日期
            formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%m-%d")
            
            self.forecast_tree.insert("", tk.END, values=(formatted_date, temp_min, temp_max, condition))
    
    def get_weather_condition(self, weather_code):
        """根据天气代码返回天气状况描述"""
        # 简化的天气代码映射
        weather_codes = {
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
        return weather_codes.get(weather_code, "未知")

if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherApp(root)
    root.mainloop()