from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit, QHBoxLayout, QApplication, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

class ResultWindow(QMainWindow):
    rescan_requested = pyqtSignal()
    
    def __init__(self, qr_content, language_manager):
        super().__init__()
        self.language_manager = language_manager
        self.qr_content = qr_content
        self.setFixedSize(550, 400)
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
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.title_label = QLabel()
        self.title_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)
        
        self.content_label = QLabel()
        self.content_label.setFont(QFont("Arial", 12))
        layout.addWidget(self.content_label)
        
        self.content_text_edit = QTextEdit()
        self.content_text_edit.setPlainText(self.qr_content)
        self.content_text_edit.setFont(QFont("Arial", 12))
        self.content_text_edit.setReadOnly(True)
        self.content_text_edit.setLineWrapMode(QTextEdit.WidgetWidth)
        layout.addWidget(self.content_text_edit)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.copy_button = QPushButton()
        self.copy_button.setFont(QFont("Arial", 12))
        self.copy_button.setFixedSize(120, 40)
        self.copy_button.setStyleSheet("QPushButton {background-color: #2196F3; color: white; border-radius: 5px; border: none;} QPushButton:hover {background-color: #1976D2;} QPushButton:pressed {background-color: #1565C0;}")
        button_layout.addWidget(self.copy_button)
        
        self.rescan_button = QPushButton()
        self.rescan_button.setFont(QFont("Arial", 12))
        self.rescan_button.setFixedSize(120, 40)
        self.rescan_button.setStyleSheet("QPushButton {background-color: #4CAF50; color: white; border-radius: 5px; border: none;} QPushButton:hover {background-color: #45a049;} QPushButton:pressed {background-color: #3e8e41;}")
        button_layout.addWidget(self.rescan_button)
        
        self.close_button = QPushButton()
        self.close_button.setFont(QFont("Arial", 12))
        self.close_button.setFixedSize(120, 40)
        self.close_button.setStyleSheet("QPushButton {background-color: #f44336; color: white; border-radius: 5px; border: none;} QPushButton:hover {background-color: #da190b;} QPushButton:pressed {background-color: #b71c1c;}")
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        # 更新语言
        self.update_language()
    
    def connect_signals(self):
        self.copy_button.clicked.connect(self.copy_content)
        self.rescan_button.clicked.connect(self.request_rescan)
        self.close_button.clicked.connect(self.close)
    
    def update_language(self):
        """
        更新界面语言
        """
        self.setWindowTitle(self.language_manager.get_text("result_window_title"))
        self.title_label.setText(self.language_manager.get_text("result_window_title"))
        self.content_label.setText(self.language_manager.get_text("result_content_label"))
        self.copy_button.setText(self.language_manager.get_text("copy_btn"))
        self.rescan_button.setText(self.language_manager.get_text("rescan_btn"))
        self.close_button.setText(self.language_manager.get_text("close_btn"))
    
    def copy_content(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.qr_content)
        QMessageBox.information(self, 
                               self.language_manager.get_text("copy_title"), 
                               self.language_manager.get_text("copy_success"))
    
    def request_rescan(self):
        self.rescan_requested.emit()
        self.close()