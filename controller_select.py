import os, sys
from pathlib import Path
import tkinter as tk 
import numpy as np 
import cv2
from PIL import ImageGrab, Image
from PyQt5.QtCore import Qt, QPoint, QRectF
from PyQt5.QtWidgets import QWidget, QApplication, QDialog
from PyQt5.QtGui import QCursor, QPainter, QPen, QColor

#from screen  import ImageScreen
from predict_lesion import predict
from screen import ImageScreen_
from controller import control_screen
from detect import main, parse_opt

class SnippingWidget(QWidget):
    num_snip = 0
    is_snipping = False     
    background = True

    def __init__(self, parent=None):
        super(SnippingWidget, self).__init__()
        self.parent = parent
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

        root = tk.Tk()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        self.setGeometry(0, 0, screen_width, screen_height)
        self.begin = QPoint()
        self.end = QPoint()

    def start(self):
        self.close()
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        SnippingWidget.background = False
        SnippingWidget.is_snipping = True
        self.setWindowOpacity(0.5)
        QApplication.setOverrideCursor(QCursor(Qt.CrossCursor))
        self.setWindowFlags(Qt.FramelessWindowHint)

        # 반투명창 보이기 (기존 화면에 반투명창 하나 띄운것임)
        self.show()

    def paintEvent(self, event):
        if SnippingWidget.is_snipping:
            #print('snipping if')
            brush_color = (128, 128, 255, 100)
            lw = 3
            opacity = 0.3
        else:
            # reset points, so the rectangle won't show up again.
            self.begin = QPoint()
            self.end = QPoint()
            brush_color = (0, 0, 0, 0)
            lw = 0
            opacity = 0

        
        self.setWindowOpacity(opacity)
        qp = QPainter(self)
        qp.setPen(QPen(QColor('red'), lw))
        qp.setBrush(QColor('Alpha')) #qp.setBrush(QtGui.QColor(*brush_color))
        rect = QRectF(self.begin, self.end)
        qp.drawRect(rect)
        

    def keyPressEvent(self, event):
        # esc 버튼 눌렀을 때
        if event.key() == Qt.Key_Escape:
            self.close()
            self.control_screen = control_screen()
            self.control_screen.show()
        event.accept()
        

    def mousePressEvent(self, event):
        self.begin = event.pos()
        self.end = self.begin
        self.update()

    def mouseMoveEvent(self, event):
        self.end = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):
        SnippingWidget.num_snip += 1
        SnippingWidget.is_snipping = False
        QApplication.restoreOverrideCursor()
        x1 = min(self.begin.x(), self.end.x())
        y1 = min(self.begin.y(), self.end.y())
        x2 = max(self.begin.x(), self.end.x())
        y2 = max(self.begin.y(), self.end.y())

        if self.begin.x() == self.end.x() and self.begin.y() ==  self.end.y() :
            self.control_screen = control_screen()
            self.control_screen.show()
        elif self.end.x() - self.begin.x() < 15 and self.end.y() - self.begin.y() < 15: 
            self.control_screen = control_screen()
            self.control_screen.show()
        else :     
            self.repaint()
            QApplication.processEvents()
            img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            QApplication.processEvents()
            img = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2RGB)

            # add to the snips list the object that opens a window of the image
            self.imagescreen = ImageScreen_(img, (x1, y1, x2, y2)) #, SnippingWidget.num_snip, (x1, y1, x2, y2)).show()
            self.imagescreen.show()
            self.control_screen = control_screen(img = img, start_position = (x1, y1, x2, y2))
            self.control_screen.show()
            print('snippet control widget;;', self.control_screen)

        #event.accept()
        self.close()

    def detectimage(self): 
        # 화면 캡쳐 후 저장 --> 저장 경로 잘 지정해줬는지 ? 
        screen_save_path = 'capture.png' #os.path.join(ROOT, 'capture.png') # capture.png로 저장
        screenshot = ImageGrab.grab()
        screenshot.save(screen_save_path, format='PNG')
        opt = parse_opt() # 저장된 이미지 해당 경로에 있는 파일명으로 불러오기,, capture.png 불러오기
        bbox = main(opt) # 좌표 예측

        image = Image.open('capture.png')
        # 좌표 이용하여 캡쳐 이미지 자르기
        crop_img = image.crop(bbox)
        save_path = 'input.png' #os.path.join(ROOT, 'input.png')
        #crop_img.save(save_path, format = 'PNG')

        img = cv2.cvtColor(np.array(crop_img), cv2.COLOR_BGR2RGB)
        # 실행중 표시를 위해 ImageScreen_ 호출 
        # 자른 이미지 및 좌표 ImageScreen_에 전달
        self.imagescreen = ImageScreen_(img = img, start_position= bbox)
        self.imagescreen.show() # working...
        QApplication.processEvents()
        self.control_ = control_screen(img = img, start_position = bbox )
        self.control_.show() # not working...
        print('show controller;;', self.control_)

    

        
FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]  # YOLOv5 root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH

'''
class DetectImage(QDialog):
    def __init__(self):
        super(DetectImage, self).__init__()

        # 화면 캡쳐 후 저장 --> 저장 경로 잘 지정해줬는지 ? 
        screen_save_path = 'capture.png' #os.path.join(ROOT, 'capture.png') # capture.png로 저장
        screenshot = ImageGrab.grab()
        screenshot.save(screen_save_path, format='PNG')
        opt = parse_opt() # 저장된 이미지 해당 경로에 있는 파일명으로 불러오기,, capture.png 불러오기
        bbox = main(opt) # 좌표 예측

        image = Image.open('capture.png')
        # 좌표 이용하여 캡쳐 이미지 자르기
        crop_img = image.crop(bbox)
        save_path = 'input.png' #os.path.join(ROOT, 'input.png')
        #crop_img.save(save_path, format = 'PNG')

        img = cv2.cvtColor(np.array(crop_img), cv2.COLOR_BGR2RGB)
        # 실행중 표시를 위해 ImageScreen_ 호출 
        # 자른 이미지 및 좌표 ImageScreen_에 전달
        self.imagescreen = ImageScreen_(img = img, start_position= bbox)
        self.imagescreen.show() # working...
        QApplication.processEvents()
        self.control_ = control_screen(img = img, start_position = bbox )
        self.control_.show() # not working...
        print('show controller;;', self.control_)

        # 병변 위치 찾는것도 표시 ? --> 메시지 표시 ..
'''        
