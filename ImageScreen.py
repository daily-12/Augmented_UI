## 영역 지정 이미지 vs 예측 이미지 구분 방법? 
import sys, math
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QPoint, QRectF, QRect, pyqtSlot, pyqtSignal, QObject, QThread, QTimer, QMetaObject
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtGui import QCursor, QPainter, QPen, QColor, QPixmap, QImage, QBrush, QPalette, QMovie
from PIL import ImageGrab
import cv2 
import numpy as np 
from predict_lesion import UNet, VGGBlock, predict
from PIL.ImageQt import ImageQt
from PIL import Image 

class Worker(QtCore.QRunnable):
    def __init__(self, img , start_position, dialog  ):
        super(Worker, self).__init__()
        self.image = img 
        self.start_position =  start_position
        self.w = dialog 
        
    def run(self):
        predict()
        QMetaObject.invokeMethod(self.w , "FinishedPredict", QtCore.Qt.QueuedConnection)


class ImageScreen(QMainWindow):

    #position = pyqtSignal(object, tuple)
    image_width = None 
    image_height = None
    lesion_predict_state = False 

    def __init__(self,  img = None, start_position = (300, 300, 350, 350), parent = None): #, xy, size=1.0, on_top=False):
        super(ImageScreen, self).__init__(parent)
        
        print('ImageScreen start')
        #self.spinner = view_loading(self, True, True, QtCore.Qt.ApplicationModal)#QtWaitingSpinner(self, True, True, QtCore.Qt.ApplicationModal)
 
        self.image = img

        #self.xy = xy
        #self.from_xy = xy
        self.from_xy_diff = [0, 0]
        #self.to_xy = xy
        self.to_xy_diff = [0, 0]
        self.speed = 60
        self.direction = [0, 0] # x: 0(left), 1(right), y: 0(up), 1(down)
        
        self.start_position = start_position

        self.label = QLabel('', self)
        self.label.setMinimumSize(QtCore.QSize(50, 50))
        self.loading = QMovie('spinner')
        self.label.setMovie(self.loading)

        # From the second initialization, both arguments will be valid
        if img is not None : # and snip_number is not None:
            self.qimage = self.convert_numpy_img_to_qpixmap(img)
        else:
            self.qimage = QPixmap("")

        self.setGeometry(*start_position)
        print('init position;', *start_position)
        self.resize(self.qimage.width(), self.qimage.height())

    #def resizeEvent(self, event): #resizeEvent(self, event):
        #self.spinner.resize(event.size())#(self.qimage.width(), self.qimage.height())#event.size())
        #event.accept()

    def paintEvent(self, event):
        print('painter start;;;')
        painter = QPainter(self)
        
        rect = QRect(0, 0, self.qimage.width(), self.qimage.height()) # 화면보다 더 크기가 큰가 ..?
        painter.drawPixmap(rect, self.qimage)
        #self.update()
        
        
        # 버튼을 누를때 실행 됐으면 좋겠는데,
        #if self.lesion_predict_state == True : 
        print('lesion predict state;;', self.lesion_predict_state)

        # show loading 
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(event.rect(), QBrush(QColor(255, 255, 255, 70)))
        self.loading.start()
        self.loading.setScaledSize(QtCore.QSize(50, 50))
        self.label.move(self.width()/2 -25 , self.height()/2 - 25)


    def keyPressEvent(self, event):
        # esc 버튼 눌렀을 때
        if event.key() == Qt.Key_Escape:
            self.close()
        print('key press event')
        event.accept()
    
    # 드래그 할 때
    def mouseMoveEvent(self, a0: QtGui.QMouseEvent):
        self.xy = [(a0.globalX() - self.localPos.x()), (a0.globalY() - self.localPos.y())]
        self.move(*self.xy)


    # 마우스 눌렀을 때
    def mousePressEvent(self, a0: QtGui.QMouseEvent):
        self.localPos = a0.localPos()
    
    # 마우스 놓았을 때
    def mouseReleaseEvent(self, a0: QtGui.QMouseEvent):
        pass   

    def show_predict(self, image, position):
        
        if image is None:
            msg = QMessageBox()
            msg.warning(self, '경고', '선택된 이미지가 없습니다.')
            
        else : 
            # 선택한 영역 이미지 저장
            cv2.imwrite('input.png', image)

            print('show predict, lesion predict state;;', self.lesion_predict_state)
            print('position;;', *position)
            print('predict pos;;', self.pos())
            # 병변 예측하기
            print('start position ---', self.width(), self.height())
            
            #self.spinner.start()
            #self.spinner.setGeometry(position[0] + int(self.qimage.width()/2), position[1] + int(self.qimage.height()/2), self.qimage.width(), self.qimage.height() ) 
            
            # thread 설정
            worker = Worker(self.image, position, self) #self.start_position, self)
            QtCore.QThreadPool.globalInstance().start(worker)

        #self.close() # not working ... 
        print('close 실행..')

    @QtCore.pyqtSlot()
    def FinishedPredict(self):
        print('finish predict;;')
        #self.spinner.stop()
        self.close() # not working... 
        # 예측이 완료되었습니다 표시 추가..?
        msg = QMessageBox()
        msg.information(self, '완료', '예측이 완료되었습니다.')

    @QtCore.pyqtSlot(bool)
    def get_click_lesion_predict(self, value):
        print('slot lesion_predict;;', value)
        self.lesion_predict_state = value
        
      
    @staticmethod
    def convert_numpy_img_to_qpixmap(np_img):
        height, width, channel = np_img.shape
        bytesPerLine = 3 * width
        return QPixmap(QImage(np_img.data, width, height, bytesPerLine, QImage.Format_RGB888).rgbSwapped())
