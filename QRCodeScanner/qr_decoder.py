import cv2
import numpy as np

class QRDecoder:
    def __init__(self):
        self.detector = cv2.QRCodeDetector()
    
    def detect_qr_codes(self, img):
        qr_codes = []
        retval, decoded_info, points, _ = self.detector.detectAndDecodeMulti(img)
        
        if retval:
            for i in range(len(decoded_info)):
                if decoded_info[i]:
                    qr_codes.append({
                        "content": decoded_info[i],
                        "points": points[i]
                    })
        
        return qr_codes
    
    def get_qr_center(self, points):
        center_x = int(np.mean(points[:, 0]))
        center_y = int(np.mean(points[:, 1]))
        return (center_x, center_y)
