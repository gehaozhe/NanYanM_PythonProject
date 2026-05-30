class LanguageManager:
    """
    语言管理类，用于存储和切换中英文文本
    """
    
    def __init__(self):
        # 初始化语言为中文
        self.language = "zh"
        
        # 存储中英文文本映射
        self.texts = {
            # 主窗口文本
            "main_window_title": {
                "zh": "二维码识别工具",
                "en": "QR Code Scanner"
            },
            "main_window_desc": {
                "zh": "点击下方按钮开始识别屏幕上的二维码",
                "en": "Click the button below to start scanning"
            },
            "start_scan_btn": {
                "zh": "开始识别",
                "en": "Start Scanning"
            },
            "copyright": {
                "zh": "© 2026 二维码识别工具 By 葛昊哲",
                "en": "© 2026 QR Code Scanner By 葛昊哲"
            },
            "language_switch": {
                "zh": "English",
                "en": "中简"
            },
            
            # 捕获窗口文本
            "capture_hint": {
                "zh": "点击屏幕上的二维码位置开始识别，按Esc取消",
                "en": "Click on the QR code position to start scanning, press Esc to cancel"
            },
            "no_qr_hint": {
                "zh": "未识别到二维码，按Esc取消",
                "en": "No QR code detected, press Esc to cancel"
            },
            "hover_hint": {
                "zh": "鼠标悬停查看二维码，点击选择，按Esc取消",
                "en": "Hover to view QR code, click to select, press Esc to cancel"
            },
            
            # 结果窗口文本
            "result_window_title": {
                "zh": "二维码识别结果",
                "en": "QR Code Recognition Result"
            },
            "result_content_label": {
                "zh": "二维码内容：",
                "en": "QR Code Content:"
            },
            "copy_btn": {
                "zh": "复制结果",
                "en": "Copy"
            },
            "rescan_btn": {
                "zh": "重新识别",
                "en": "Rescan"
            },
            "close_btn": {
                "zh": "关闭",
                "en": "Close"
            },
            "copy_success": {
                "zh": "内容已复制到剪贴板",
                "en": "Content copied to clipboard"
            },
            "copy_title": {
                "zh": "提示",
                "en": "Hint"
            },
            
            # 错误提示
            "no_qr_code": {
                "zh": "未识别到二维码",
                "en": "No QR code detected"
            },
            "error_title": {
                "zh": "错误",
                "en": "Error"
            },
            "scan_error": {
                "zh": "扫描过程中发生错误：{}",
                "en": "Error during scanning: {}"
            }
        }
    
    def switch_language(self):
        """
        切换语言（中英文切换）
        """
        self.language = "en" if self.language == "zh" else "zh"
    
    def get_text(self, key):
        """
        根据当前语言获取文本
        
        Args:
            key: str，文本键名
            
        Returns:
            str，对应语言的文本
        """
        return self.texts.get(key, {}).get(self.language, key)
    
    def get_current_language(self):
        """
        获取当前语言
        
        Returns:
            str，当前语言代码（"zh"或"en"）
        """
        return self.language
