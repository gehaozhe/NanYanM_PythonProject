import sys
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer

# 导入自定义模块
from screen_capture import ScreenCapture
from qr_decoder import QRDecoder
from language import LanguageManager
from gui.main_window import MainWindow
from gui.capture_window import CaptureWindow
from gui.result_window import ResultWindow

class QRCodeScannerApp:
    """
    二维码识别应用类，协调各个模块的工作
    """
    
    def __init__(self):
        # 创建QApplication实例
        self.app = QApplication(sys.argv)
        
        # 初始化语言管理器
        self.language_manager = LanguageManager()
        
        # 初始化各个模块
        self.screen_capture = ScreenCapture()
        self.qr_decoder = QRDecoder()
        
        # 创建主窗口
        self.main_window = MainWindow(self.language_manager)
        # 连接主窗口的开始扫描信号
        self.main_window.scan_requested.connect(self.start_scanning)
        # 连接主窗口的语言切换信号
        self.main_window.language_switched.connect(self.handle_language_switch)
        
        # 存储当前的截屏窗口和结果窗口
        self.capture_window = None
        self.result_window = None
    
    def start_scanning(self):
        """
        开始扫描二维码
        """
        # 关闭先前的结果窗口（如果存在）
        if self.result_window:
            self.result_window.close()
            self.result_window = None
        
        # 使用QTimer延迟执行实际的扫描操作，给UI足够的时间处理关闭事件
        QTimer.singleShot(300, self._do_scanning)
    
    def _do_scanning(self):
        """
        实际执行扫描操作
        """
        try:
            # 1. 捕获屏幕
            pixmap, img = self.screen_capture.capture_screen()
            
            # 2. 存储捕获的图像，用于后续处理
            self.captured_pixmap = pixmap
            self.captured_img = img
            
            # 3. 识别二维码
            qr_codes = self.qr_decoder.detect_qr_codes(img)
            
            # 4. 显示截屏窗口，高亮显示二维码
            self.capture_window = CaptureWindow(pixmap, qr_codes, self.language_manager)
            # 连接截屏窗口的信号
            self.capture_window.qr_selected.connect(self.handle_qr_selected)
            self.capture_window.canceled.connect(self.handle_canceled)
            
        except Exception as e:
            QMessageBox.critical(self.main_window, self.language_manager.get_text("error_title"), 
                              self.language_manager.get_text("scan_error").format(str(e)))
    
    def handle_language_switch(self):
        """
        处理语言切换事件
        """
        # 切换语言
        self.language_manager.switch_language()
        
        # 更新主窗口语言
        self.main_window.update_language()
        
        # 如果结果窗口存在，更新其语言
        if self.result_window:
            self.result_window.update_language()
    
    def handle_qr_selected(self, qr_code):
        """
        处理用户选择的二维码
        
        Args:
            qr_code: dict，选中的二维码信息
        """
        # 获取二维码内容
        qr_content = qr_code["content"]
        
        # 显示结果窗口
        self.result_window = ResultWindow(qr_content, self.language_manager)
        # 连接结果窗口的信号
        self.result_window.rescan_requested.connect(self.start_scanning)
        self.result_window.show()
    
    def handle_canceled(self):
        """
        处理用户取消选择的情况
        """
        pass  # 可以添加一些日志或提示
    
    def run(self):
        """
        运行应用程序
        
        Returns:
            int: 应用程序退出码
        """
        # 显示主窗口
        self.main_window.show()
        
        # 运行应用程序
        return self.app.exec_()

def main():
    """
    主函数，程序入口
    """
    app = QRCodeScannerApp()
    sys.exit(app.run())

if __name__ == "__main__":
    main()
