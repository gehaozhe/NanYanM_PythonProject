from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QPolygon
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QRect
import numpy as np

class CaptureWindow(QWidget):
    """
    截屏窗口类，用于显示捕获的屏幕内容和识别到的二维码
    """
    
    # 信号：用户选择了二维码
    qr_selected = pyqtSignal(dict)  # 返回选中的二维码信息
    
    # 信号：用户取消选择
    canceled = pyqtSignal()
    
    def __init__(self, pixmap, qr_codes, language_manager):
        super().__init__()
        
        # 设置窗口为全屏、无边框、半透明
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.showFullScreen()
        
        # 存储捕获的图像、二维码信息和语言管理器
        self.pixmap = pixmap
        self.qr_codes = qr_codes
        self.language_manager = language_manager
        
        # 存储每个二维码的中心点和边界信息
        self.qr_centers = []  # 存储(center_x, center_y, qr_code_info)
        self.qr_bounds = []  # 存储每个二维码的边界范围 (min_x, max_x, min_y, max_y)
        
        # 存储当前鼠标悬停的二维码索引，-1表示没有悬停
        self.hovered_qr_index = -1
        
        # 初始化二维码中心点和边界
        self.init_qr_info()
    
    def init_qr_info(self):
        """
        初始化二维码的中心点和边界信息
        """
        for qr_code in self.qr_codes:
            points = qr_code["points"]
            
            # 计算中心点
            center_x = int(np.mean(points[:, 0]))
            center_y = int(np.mean(points[:, 1]))
            
            # 计算边界范围
            min_x = int(np.min(points[:, 0]))
            max_x = int(np.max(points[:, 0]))
            min_y = int(np.min(points[:, 1]))
            max_y = int(np.max(points[:, 1]))
            
            # 存储信息
            self.qr_centers.append((center_x, center_y, qr_code))
            self.qr_bounds.append((min_x, max_x, min_y, max_y))
    
    def paintEvent(self, event):
        """
        绘制事件，用于绘制屏幕内容和二维码标记
        """
        painter = QPainter(self)
        
        # 绘制捕获的屏幕内容
        painter.drawPixmap(0, 0, self.pixmap)
        
        # 设置半透明遮罩，让屏幕变暗
        painter.setOpacity(0.5)
        painter.fillRect(self.rect(), QColor(0, 0, 0))
        painter.setOpacity(1.0)
        
        # 绘制所有二维码的高亮效果
        for i, qr_code in enumerate(self.qr_codes):
            points = qr_code["points"]
            min_x, max_x, min_y, max_y = self.qr_bounds[i]
            
            # 高亮显示二维码区域
            margin = 20
            highlight_rect = QRect(
                min_x - margin, 
                min_y - margin, 
                (max_x - min_x) + 2 * margin, 
                (max_y - min_y) + 2 * margin
            )
            
            # 使用原始屏幕内容填充高亮区域，覆盖遮罩
            painter.drawPixmap(highlight_rect, self.pixmap, highlight_rect)
            
            # 如果是悬停的二维码，绘制绿框
            if i == self.hovered_qr_index:
                pen = QPen(QColor(0, 255, 0), 3, Qt.SolidLine)
                painter.setPen(pen)
                # 将numpy数组转换为QPolygon
                qpoints = []
                for point in points:
                    qpoints.append(QPoint(int(point[0]), int(point[1])))
                polygon = QPolygon(qpoints)
                painter.drawPolygon(polygon)
        
        # 绘制提示信息
        self.draw_hint(painter)
    
    def draw_hint(self, painter):
        """
        绘制提示信息
        """
        # 提示文字
        if self.qr_codes:
            hint_text = self.language_manager.get_text("hover_hint")
        else:
            hint_text = self.language_manager.get_text("no_qr_hint")
        
        # 设置字体
        font = QFont("Arial", 12)
        painter.setFont(font)
        
        # 设置文字颜色
        painter.setPen(QColor(255, 255, 255))
        
        # 绘制文字背景
        text_rect = painter.fontMetrics().boundingRect(hint_text)
        text_rect.setWidth(text_rect.width() + 20)
        text_rect.setHeight(text_rect.height() + 10)
        text_rect.moveCenter(self.rect().center())
        text_rect.moveTop(50)
        
        painter.setBrush(QColor(0, 0, 0, 150))
        painter.drawRect(text_rect)
        
        # 绘制文字
        painter.drawText(text_rect, Qt.AlignCenter, hint_text)
    
    def mousePressEvent(self, event):
        """
        鼠标点击事件，处理用户选择二维码
        """
        # 获取点击位置
        click_x = event.x()
        click_y = event.y()
        
        # 如果没有识别到二维码，直接取消
        if not self.qr_codes:
            self.canceled.emit()
            self.close()
            return
        
        # 判断点击位置是否在某个二维码的边界内
        for i, (min_x, max_x, min_y, max_y) in enumerate(self.qr_bounds):
            # 扩大边界范围，让鼠标更容易点击
            margin = 20
            if (min_x - margin <= click_x <= max_x + margin and 
                min_y - margin <= click_y <= max_y + margin):
                # 发送选中信号
                self.qr_selected.emit(self.qr_codes[i])
                # 关闭窗口
                self.close()
                return
        
        # 如果点击位置不在任何二维码上，取消选择
        self.canceled.emit()
        self.close()
    
    def mouseMoveEvent(self, event):
        """
        鼠标移动事件，检测鼠标是否悬停在二维码上方
        """
        # 获取鼠标位置
        mouse_x = event.x()
        mouse_y = event.y()
        
        # 如果没有识别到二维码，直接返回
        if not self.qr_codes:
            return
        
        # 检测鼠标是否在某个二维码的边界内
        new_hovered_index = -1
        for i, (min_x, max_x, min_y, max_y) in enumerate(self.qr_bounds):
            # 扩大边界范围，让鼠标更容易悬停
            margin = 20
            if (min_x - margin <= mouse_x <= max_x + margin and 
                min_y - margin <= mouse_y <= max_y + margin):
                new_hovered_index = i
                break
        
        # 如果悬停状态发生变化，更新并触发重绘
        if new_hovered_index != self.hovered_qr_index:
            self.hovered_qr_index = new_hovered_index
            self.update()
    
    def keyPressEvent(self, event):
        """
        键盘事件，按Esc键取消选择
        """
        if event.key() == Qt.Key_Escape:
            self.canceled.emit()
            self.close()