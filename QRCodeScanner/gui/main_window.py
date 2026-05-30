from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QApplication, QHBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

class MainWindow(QMainWindow):
    scan_requested = pyqtSignal()
    language_switched = pyqtSignal()
    
    def __init__(self, language_manager):
        super().__init__()
        self.language_manager = language_manager
        self.setWindowTitle(self.language_manager.get_text("main_window_title"))
        self.setFixedSize(500, 300)
        self.center()
        self.init_ui()
        self.connect_signals()
    
    def center(self):
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        
        # 语言切换按钮
        self.language_btn = QPushButton(self.language_manager.get_text("language_switch"))
        self.language_btn.setFont(QFont("Arial", 10))
        self.language_btn.setFixedSize(80, 30)
        self.language_btn.setStyleSheet("QPushButton {background-color: #2196F3; color: white; border-radius: 5px; border: none;} QPushButton:hover {background-color: #1976D2;}")
        
        # 标题和语言切换按钮的水平布局
        title_layout = QHBoxLayout()
        title_layout.setAlignment(Qt.AlignCenter)
        title_layout.addStretch()
        
        title_label = QLabel(self.language_manager.get_text("main_window_title"))
        title_label.setFont(QFont("Arial", 20, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.language_btn)
        
        layout.addLayout(title_layout)
        
        desc_label = QLabel(self.language_manager.get_text("main_window_desc"))
        desc_label.setFont(QFont("Arial", 12))
        desc_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc_label)
        
        self.start_button = QPushButton(self.language_manager.get_text("start_scan_btn"))
        self.start_button.setFont(QFont("Arial", 14))
        self.start_button.setFixedSize(200, 50)
        self.start_button.setStyleSheet("QPushButton {background-color: #4CAF50; color: white; border-radius: 10px; border: none;} QPushButton:hover {background-color: #45a049;} QPushButton:pressed {background-color: #3e8e41;}")
        layout.addWidget(self.start_button, 0, Qt.AlignCenter)
        
        self.copyright_button = QPushButton(self.language_manager.get_text("copyright"))
        self.copyright_button.setFont(QFont("Arial", 10))
        self.copyright_button.setFlat(True)
        self.copyright_button.setStyleSheet("QPushButton {color: #666; background-color: transparent; border: none;} QPushButton:hover {color: #333; text-decoration: underline;}")
        self.copyright_button.setFixedSize(400, 30)
        layout.addWidget(self.copyright_button, 0, Qt.AlignCenter)
    


    def connect_signals(self):
        self.start_button.clicked.connect(self.start_scanning)
        self.language_btn.clicked.connect(self.switch_language)
    
    def start_scanning(self):
        self.scan_requested.emit()
    
    def switch_language(self):
        """
        切换语言
        """
        self.language_switched.emit()
    
    def update_language(self):
        """
        更新语言显示
        """
        self.setWindowTitle(self.language_manager.get_text("main_window_title"))
        
        # 更新标题标签
        title_layout = self.centralWidget().layout().itemAt(0)
        title_label = title_layout.itemAt(1).widget()
        title_label.setText(self.language_manager.get_text("main_window_title"))
        
        # 更新语言按钮文本
        self.language_btn.setText(self.language_manager.get_text("language_switch"))
        
        # 更新描述标签
        desc_label = self.centralWidget().layout().itemAt(1).widget()
        desc_label.setText(self.language_manager.get_text("main_window_desc"))
        
        # 更新开始按钮文本
        self.start_button.setText(self.language_manager.get_text("start_scan_btn"))
        
        # 更新版权按钮文本
        copyright_button = self.centralWidget().layout().itemAt(3).widget()
        copyright_button.setText(self.language_manager.get_text("copyright"))
