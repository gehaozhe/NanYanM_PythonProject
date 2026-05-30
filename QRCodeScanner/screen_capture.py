from PyQt5.QtWidgets import QApplication
import numpy as np
import cv2

class ScreenCapture:
    def __init__(self):
        self.app = QApplication.instance()
    
    def capture_screen(self):
        screen = self.app.primaryScreen()
        pixmap = screen.grabWindow(0)
        
        qimg = pixmap.toImage()
        width, height = qimg.width(), qimg.height()
        
        ptr = qimg.constBits()
        ptr.setsize(height * width * 4)
        img = np.array(ptr).reshape(height, width, 4)
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
        
        return pixmap, img
