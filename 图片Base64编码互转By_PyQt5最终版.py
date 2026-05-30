import base64
import os
import sys
import time
import tempfile
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, 
    QWidget, QLabel, QTextEdit, QFileDialog, QMessageBox, QProgressBar, QStatusBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QFontDatabase

# 图片/Base64编码互转工具 - PyQt5图形界面版本
# 功能：
# 1. 图片转换为Base64编码
# 2. Base64编码转换为图片
# 3. 支持大文件处理（通过分块处理和进度显示）
# 4. 提供结果预览、复制到剪贴板等功能

class FileBasedConvertWorker(QObject):
    """文件转换工作线程类
    负责在后台线程中执行图片和Base64编码之间的转换，避免阻塞主UI线程
    """
    # 进度更新信号
    progress_updated = pyqtSignal(int)
    # 转换完成信号 (是否成功, 消息, 结果文件路径)
    conversion_completed = pyqtSignal(bool, str, str)
    
    def __init__(self, conversion_type, source_path=None, target_path=None):
        """初始化工作线程
        参数:
            conversion_type: 转换类型 'image_to_base64' 或 'base64_to_image'
            source_path: 源文件路径
            target_path: 目标文件路径
        """
        super().__init__()
        self.conversion_type = conversion_type
        self.source_path = source_path
        self.target_path = target_path
        self._stop_flag = False  # 停止标志位
    
    def stop(self):
        """停止正在进行的转换任务"""
        self._stop_flag = True
    
    def process(self):
        """根据转换类型执行相应的转换操作"""
        try:
            if self.conversion_type == 'image_to_base64':
                self._image_to_base64_file_based()
            elif self.conversion_type == 'base64_to_image':
                self._base64_to_image_file_based()
        except Exception as e:
            self.conversion_completed.emit(False, f"处理错误: {str(e)}", "")
    
    def _image_to_base64_file_based(self):
        """将图片文件转换为Base64编码文件"""
        # 创建临时文件用于存储Base64结果
        temp_fd, temp_file_path = tempfile.mkstemp(suffix='.txt', text=True)
        os.close(temp_fd)
        
        try:
            file_size = os.path.getsize(self.source_path)
            processed_size = 0
            chunk_size = 64 * 1024  # 减小块大小到64KB，适合处理大文件
            
            # 分块读取图片文件并转换为Base64编码
            with open(self.source_path, 'rb') as f_in, open(temp_file_path, 'w', encoding='utf-8') as f_out:
                while True:
                    if self._stop_flag:
                        self.conversion_completed.emit(False, "转换已取消", "")
                        return
                    
                    chunk = f_in.read(chunk_size)
                    if not chunk:
                        break
                    
                    # 将每个块编码并直接写入文件
                    base64_chunk = base64.b64encode(chunk).decode('utf-8')
                    f_out.write(base64_chunk)
                    
                    # 刷新缓冲区以确保数据被写入
                    f_out.flush()
                    os.fsync(f_out.fileno())
                    
                    # 更新进度
                    processed_size += len(chunk)
                    progress = min(99, int((processed_size / file_size) * 100))
                    self.progress_updated.emit(progress)
                    
                    # 短暂暂停，确保UI响应
                    time.sleep(0.01)
            
            self.progress_updated.emit(100)
            # 传递结果文件路径，而不是内容
            self.conversion_completed.emit(True, "图片转换完成", temp_file_path)
        except Exception as e:
            # 发生错误时删除临时文件
            if os.path.exists(temp_file_path):
                try: 
                    os.remove(temp_file_path)
                except: 
                    pass
            self.conversion_completed.emit(False, f"转换错误: {str(e)}", "")
    
    def _base64_to_image_file_based(self):
        """将Base64编码文件转换为图片文件"""
        try:
            # 确保目标文件存在
            with open(self.target_path, 'wb') as f:
                pass
            
            file_size = os.path.getsize(self.source_path)
            processed_size = 0
            chunk_size = 128 * 1024  # Base64块大小为128KB
            
            # 分块读取Base64编码并转换为图片数据
            with open(self.source_path, 'r', encoding='utf-8') as f_in, open(self.target_path, 'wb') as f_out:
                while True:
                    if self._stop_flag:
                        self.conversion_completed.emit(False, "转换已取消", "")
                        return
                    
                    # 读取Base64数据块
                    chunk = f_in.read(chunk_size)
                    if not chunk:
                        break
                    
                    # 清理Base64数据（去除换行符、空格等）
                    chunk = chunk.replace('\n', '').replace('\r', '').replace(' ', '')
                    
                    # 确保Base64数据长度是4的倍数（Base64编码要求）
                    padding_needed = 4 - (len(chunk) % 4)
                    if padding_needed < 4:
                        chunk += '=' * padding_needed
                    
                    try:
                        # 解码并写入文件
                        binary_data = base64.b64decode(chunk)
                        f_out.write(binary_data)
                        
                        # 刷新缓冲区
                        f_out.flush()
                        os.fsync(f_out.fileno())
                    except Exception as e:
                        self.conversion_completed.emit(False, f"Base64解码错误: {str(e)}", "")
                        return
                    
                    # 更新进度
                    processed_size += len(chunk)
                    progress = min(99, int((processed_size / file_size) * 100))
                    self.progress_updated.emit(progress)
                    
                    # 短暂暂停
                    time.sleep(0.01)
            
            self.progress_updated.emit(100)
            self.conversion_completed.emit(True, "图片已保存完成", self.target_path)
        except Exception as e:
            self.conversion_completed.emit(False, f"转换错误: {str(e)}", "")

class ImageToBase64App(QMainWindow):
    """主应用程序窗口类
    负责创建GUI界面和处理用户交互"""
    def __init__(self):
        super().__init__()
        self.worker_thread = None  # 工作线程引用
        self.worker = None  # 工作对象引用
        self.temp_files = []  # 跟踪所有临时文件，用于程序关闭时清理
        self.current_result_file = None  # 当前结果文件路径
        self.is_full_result_shown = False  # 跟踪是否显示完整结果
        self.brief_content = ""  # 存储简洁内容
        self.init_ui()  # 初始化用户界面
    
    def init_ui(self):
        """初始化用户界面，创建所有控件和布局"""
        # 窗口设置
        self.setWindowTitle("图片/ Base64编码互转工具v1.0.0")
        self.resize(700, 500)
        
        # 获取系统可用的中文字体
        font_families = QFontDatabase().families()
        chinese_font = "Heiti TC"  # macOS默认中文字体
        for font in ["SimHei", "WenQuanYi Micro Hei", "Heiti TC", "Microsoft YaHei"]:
            if font in font_families:
                chinese_font = font
                break
        
        # 中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 标题标签
        title_label = QLabel('<font color="red">///WARING///</font>\n只能转换小图片,如图标等\n大图片有Bug!!!')
        title_label.setFont(QFont(chinese_font, 16, QFont.Bold))
        title_label.setTextFormat(Qt.RichText)  # 确保支持HTML格式
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("background-color: #3498db; color: white; padding: 10px;")
        main_layout.addWidget(title_label)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 主要功能按钮
        self.btn1 = QPushButton("图片转Base64")
        self.btn1.setFont(QFont(chinese_font, 11))
        self.btn1.setStyleSheet("background-color: #2ecc71; color: white;")
        self.btn1.clicked.connect(self.start_image_to_base64)
        
        self.btn2 = QPushButton("Base64转图片")
        self.btn2.setFont(QFont(chinese_font, 11))
        self.btn2.setStyleSheet("background-color: #e67e22; color: white;")
        self.btn2.clicked.connect(self.start_base64_to_image)
        
        self.btn3 = QPushButton("复制结果到剪贴板")
        self.btn3.setFont(QFont(chinese_font, 10))
        self.btn3.setStyleSheet("background-color: #9b59b6; color: white;")
        self.btn3.clicked.connect(self.copy_to_clipboard)
        
        self.btn4 = QPushButton("显示完整结果")
        self.btn4.setFont(QFont(chinese_font, 10))
        self.btn4.setStyleSheet("background-color: #f39c12; color: white;")
        self.btn4.clicked.connect(self.show_full_result)
        self.btn5 = QPushButton("退出")
        self.btn5.setFont(QFont(chinese_font, 10))
        self.btn5.setStyleSheet("background-color: #e74c3c; color: white;")
        self.btn5.clicked.connect(self.close)
        
        # 添加按钮到布局
        button_layout.addWidget(self.btn1)
        button_layout.addWidget(self.btn2)
        button_layout.addWidget(self.btn3)
        button_layout.addWidget(self.btn4)
        button_layout.addWidget(self.btn5)
        main_layout.addLayout(button_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)
        
        # 结果显示区域标签
        result_label = QLabel("结果预览:")
        result_label.setFont(QFont(chinese_font, 11))
        main_layout.addWidget(result_label)
        
        # 结果文本编辑框
        self.result_text = QTextEdit()
        self.result_text.setFont(QFont(chinese_font, 10))
        self.result_text.setReadOnly(False)  # 改为可编辑，允许用户输入Base64编码
        self.result_text.setUndoRedoEnabled(True)  # 启用撤销/重做
        
        # 添加不可选中的灰色提示文字
        self.result_text.setPlaceholderText("转换完成的Base64编码在这里\n在这里输入Base64编码")
        
        main_layout.addWidget(self.result_text, 1)  # 占据剩余空间
        
        # 状态栏
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("就绪")
    
    def start_image_to_base64(self):
        """启动图片转Base64编码功能"""
        # 停止任何正在运行的任务
        self._stop_current_task()
            
        # 打开文件选择对话框，让用户选择图片文件
        image_path, _ = QFileDialog.getOpenFileName(
            self, "选择图片文件", "", "图片文件 (*.jpg *.jpeg *.png *.bmp *.gif);;所有文件 (*.*)"
        )
        
        if not image_path:
            self.statusBar().showMessage("未选择图片文件")
            return
            
        # 文件大小检查
        file_size_mb = os.path.getsize(image_path) / (1024 * 1024)
        
        # 对于大文件，显示提示信息
        if file_size_mb > 5 and not QMessageBox.question(
            self, "提示", f"文件大小为{file_size_mb:.2f}MB，转换可能需要一定时间，是否继续？", 
            QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            return
            
        # 创建新的工作线程和工作对象
        self.worker_thread = QThread()
        self.worker = FileBasedConvertWorker('image_to_base64', source_path=image_path)
        
        # 将工作对象移动到线程
        self.worker.moveToThread(self.worker_thread)
        
        # 连接信号和槽
        self.worker_thread.started.connect(self.worker.process)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.conversion_completed.connect(self.on_image_to_base64_completed)
        self.worker_thread.finished.connect(self._on_thread_finished)  # 线程结束时的处理
        
        # 清空结果文本框
        self.result_text.clear()
        self.current_result_file = None
        
        # 启动线程
        self.worker_thread.start()
        
        self.statusBar().showMessage(f"正在处理: {os.path.basename(image_path)}")
    
    def start_base64_to_image(self):
        """启动Base64编码转图片功能"""
        # 停止任何正在运行的任务
        self._stop_current_task()
            
        # 创建临时文件用于存储用户输入的Base64编码
        temp_fd, temp_file_path = tempfile.mkstemp(suffix='.txt', text=True)
        os.close(temp_fd)
        self.temp_files.append(temp_file_path)
        
        # 从文本框获取用户输入的Base64编码
        base64_content = self.result_text.toPlainText().strip()
        
        if not base64_content:
            # 如果文本框为空，检查是否有当前结果文件
            if not self.current_result_file or not os.path.exists(self.current_result_file):
                QMessageBox.warning(self, "警告", "请先在文本框中输入Base64编码\n再执行操作")
                return
            # 使用现有结果文件
            source_path = self.current_result_file
        else:
            # 将用户输入的内容保存到临时文件
            with open(temp_file_path, 'w', encoding='utf-8') as f:
                f.write(base64_content)
            source_path = temp_file_path
            
        # 打开文件保存对话框，让用户选择保存路径
        save_path, _ = QFileDialog.getSaveFileName(
            self, "保存图片文件", "", "PNG图片 (*.png);;JPG图片 (*.jpg);;所有文件 (*.*)"
        )
        
        if not save_path:
            self.statusBar().showMessage("未保存图片文件")
            return
            
        # 创建新的工作线程和工作对象
        self.worker_thread = QThread()
        self.worker = FileBasedConvertWorker('base64_to_image', 
                                           source_path=source_path, 
                                           target_path=save_path)
        
        # 将工作对象移动到线程
        self.worker.moveToThread(self.worker_thread)
        
        # 连接信号和槽
        self.worker_thread.started.connect(self.worker.process)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.conversion_completed.connect(self.on_base64_to_image_completed)
        self.worker_thread.finished.connect(self._on_thread_finished)  # 线程结束时的处理
        
        # 启动线程
        self.worker_thread.start()
        
        self.statusBar().showMessage(f"正在保存: {os.path.basename(save_path)}")
    
    def _on_thread_finished(self):
        """线程结束时的处理"""
        # 确保线程完全停止后再清理资源
        self.worker = None
        if self.worker_thread and self.worker_thread.isFinished():
            self.worker_thread = None
    
    def on_image_to_base64_completed(self, success, message, result_file_path):
        """图片转Base64编码完成后的回调处理"""
        if success:
            # 保存结果文件路径
            self.current_result_file = result_file_path
            self.temp_files.append(result_file_path)
            
            # 显示文件大小信息
            file_size = os.path.getsize(result_file_path)
            brief_text = f"转换完成！Base64数据已保存到临时文件中。\n"
            brief_text += f"文件大小: {file_size/1024:.2f} KB\n"
            brief_text += f"点击'显示完整结果'按钮查看内容或点击'复制到剪贴板'复制内容。"
            
            self.result_text.setPlainText(brief_text)
            self.brief_content = brief_text  # 保存简洁内容
            
            # 重置按钮状态
            self.btn4.setText("显示完整结果")
            self.is_full_result_shown = False
            
            QMessageBox.information(self, "成功", message)
            self.statusBar().showMessage("转换成功")
        else:
            self.result_text.setPlainText(f"转换失败: {message}")
            QMessageBox.critical(self, "错误", message)
            self.statusBar().showMessage(f"转换失败")
        
        # 清理资源
        self._cleanup_task()
    
    def on_base64_to_image_completed(self, success, message, result_file_path):
        """Base64编码转图片完成后的回调处理"""
        if success:
            QMessageBox.information(self, "成功", f"图片已保存到: {result_file_path}")
            self.statusBar().showMessage("保存成功")
        else:
            QMessageBox.critical(self, "错误", message)
            self.statusBar().showMessage(f"保存失败")
        
        # 清理资源
        self._cleanup_task()
    
    def show_full_result(self):
        """显示或隐藏完整的Base64编码结果"""
        # 检查是否已经显示了完整结果
        if self.is_full_result_shown:
            # 如果已经显示完整结果，则隐藏它并恢复简洁内容
            self.result_text.setPlainText(self.brief_content)
            self.btn4.setText("显示完整结果")  # 恢复按钮文本
            self.is_full_result_shown = False
            self.statusBar().showMessage("已显示简洁结果")
            return
        
        # 显示完整的Base64结果
        if not self.current_result_file or not os.path.exists(self.current_result_file):
            QMessageBox.warning(self, "警告", "没有可显示的结果")
            return
        
        # 保存当前的简洁内容，以便稍后恢复
        self.brief_content = self.result_text.toPlainText()
        
        try:
            file_size = os.path.getsize(self.current_result_file)
            
            # 对于大文件，只显示部分内容
            if file_size > 1024 * 1024:  # 1MB
                try:
                    with open(self.current_result_file, 'r', encoding='utf-8') as f:
                        # 读取文件的前1000个字符
                        start_content = f.read(1000)
                        
                        try:
                            # 尝试使用seek从末尾读取
                            f.seek(-1000, 2)  # 移动到文件末尾前1000个字符
                            end_content = f.read()
                        except IOError:
                            # 如果seek操作失败，使用替代方法
                            # 重新打开文件并读取
                            f.seek(0)
                            if file_size > 2000:
                                # 读取前1000和后1000字符
                                start_content = f.read(1000)
                                # 计算要跳过的字节数
                                skip_bytes = max(0, file_size - 2000)  # 留一些余量
                                f.seek(skip_bytes)
                                end_content = f.read()
                            else:
                                # 文件太小，直接显示全部内容
                                f.seek(0)
                                content = f.read()
                                self.result_text.setPlainText(content)
                                self.btn4.setText("隐藏完整结果")  # 更改按钮文本
                                self.is_full_result_shown = True
                                return
                except Exception as e:
                    # 最保险的方式：只显示文件开头部分
                    with open(self.current_result_file, 'r', encoding='utf-8') as f:
                        content = f.read(2000)
                        self.result_text.setPlainText("文件过大 (" + str(file_size/1024/1024)[:5] + " MB)，显示开头部分：\n" + content)
                    self.btn4.setText("隐藏完整结果")  # 更改按钮文本
                    self.is_full_result_shown = True
                    return
                
                # 使用简单的字符串连接方式
                result_text = "文件过大 (" + str(file_size/1024/1024)[:5] + " MB)，仅显示部分内容：\n"
                result_text += "--- 开始部分 ---"
                result_text += start_content
                result_text += "\n\n...\n\n"
                result_text += "--- 结束部分 ---"
                result_text += end_content
                self.result_text.setPlainText(result_text)
            else:
                # 对于小文件，显示全部内容
                try:
                    with open(self.current_result_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self.result_text.setPlainText(content)
                except Exception as e:
                    # 即使是小文件也可能出现读取问题
                    with open(self.current_result_file, 'r', encoding='utf-8') as f:
                        content = f.read(5000)  # 读取前5000个字符
                    self.result_text.setPlainText("部分内容：\n" + content + "\n\n...\n\n读取完整内容失败: " + str(e))
            
            # 更改按钮文本并更新状态标志
            self.btn4.setText("隐藏完整结果")
            self.is_full_result_shown = True
            self.statusBar().showMessage("已显示完整结果")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取结果文件失败: {str(e)}")
    
    def copy_to_clipboard(self):
        """将Base64编码结果复制到剪贴板"""
        if not self.current_result_file or not os.path.exists(self.current_result_file):
            QMessageBox.warning(self, "警告", "没有可复制的内容")
            return
        
        try:
            file_size = os.path.getsize(self.current_result_file)
            
            # 检查文件大小，避免复制过大的内容
            if file_size > 10 * 1024 * 1024:  # 10MB
                QMessageBox.warning(self, "警告", f"文件过大 ({file_size/1024/1024:.2f} MB)，不适合复制到剪贴板")
                return
            
            # 读取文件内容并复制到剪贴板
            with open(self.current_result_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            QApplication.clipboard().setText(content)
            QMessageBox.information(self, "成功", "内容已复制到剪贴板")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"复制失败: {str(e)}")
    
    def update_progress(self, value):
        """更新进度条显示"""
        self.progress_bar.setValue(value)
    
    def _stop_current_task(self):
        """停止当前正在执行的转换任务"""
        # 停止当前工作线程
        if self.worker and self.worker_thread and self.worker_thread.isRunning():
            self.worker.stop()
            self.worker_thread.quit()
            if not self.worker_thread.wait(3000):  # 等待最多3秒
                print("线程无法正常停止，可能会导致资源泄漏")
    
    def _cleanup_task(self):
        """清理任务资源"""
        # 重置进度条
        QApplication.processEvents()
        time.sleep(0.3)
        self.progress_bar.setValue(0)
        
        # 清理工作线程资源
        if self.worker_thread and self.worker_thread.isFinished():
            # 线程已完成，安全地清理
            self.worker = None
            self.worker_thread = None
    
    def closeEvent(self, event):
        """窗口关闭事件处理，确保资源被正确清理"""
        # 在关闭窗口时安全地清理资源
        self._stop_current_task()
        
        # 等待线程完全停止
        if self.worker_thread and not self.worker_thread.isFinished():
            self.worker_thread.wait(3000)  # 等待最多3秒
        
        # 删除所有临时文件
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                print(f"删除临时文件失败: {temp_file}, 错误: {str(e)}")
        
        event.accept()

# 主程序入口
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ImageToBase64App()
    window.show()
    sys.exit(app.exec_())