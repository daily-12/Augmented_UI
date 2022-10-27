## 영역 지정 이미지 vs 예측 이미지 구분 방법? 
import sys, math, os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QRect, pyqtSlot, QMetaObject, QTimer, QThread, QObject, QPoint, pyqtSignal
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtGui import  QPainter, QColor, QPixmap, QImage, QBrush, QMovie, QPen
import cv2
from pathlib import Path
import numpy as np
from predict_lesion import UNet, VGGBlock, predict
from PIL.ImageQt import ImageQt
from PIL import Image, ImageGrab
from detect import main, parse_opt

class Worker(QtCore.QRunnable):
    def __init__(self, img , start_position, dialog  ):
        super(Worker, self).__init__()
        self.image = img 
        self.start_position =  start_position
        self.w = dialog 
        
    def run(self):
        #print('worker start')
        predict()
        QMetaObject.invokeMethod(self.w , "FinishedPredict", QtCore.Qt.QueuedConnection)


class WorkerDetect(QThread):#QtCore.QRunnable):
    threadEvent = pyqtSignal(tuple)

    def __init__(self,dialog ): # img , start_position, dialog  ):
        super(WorkerDetect, self).__init__()
        #self.image = img 
        #self.start_position =  start_position
        self.w = dialog 

    def run(self):
        while True:
            try : 
                bbox = self.detect()

                self.threadEvent.emit(bbox)
            except :
                print('영상을 찾지 못했습니다.')

    def detect(self):
        screen_save_path = 'capture.png' #os.path.join(ROOT, 'capture.png') # capture.png로 저장
        screenshot = ImageGrab.grab()
        screenshot.save(screen_save_path, format='PNG')
        opt = parse_opt() # 저장된 이미지 해당 경로에 있는 파일명으로 불러오기,, capture.png 불러오기
        bbox = main(opt) # x1, y1, w, h
    
        return bbox 

class ImageScreen_(QDialog):

    #position = pyqtSignal(object, tuple)
    image_width = None 
    image_height = None
    manual_btn_clicked = None 
    auto_btn_clicked = None 
    lesion_predict_state = None

    def __init__(self,  img = None, start_position = (300, 300, 350, 350), parent = None): #, xy, size=1.0, on_top=False):
        super(ImageScreen_, self).__init__(parent)
    
        flags = Qt.WindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowFlags(flags)

        #self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.image = img  
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
        self.resize(self.qimage.width(), self.qimage.height())

        if self.image is not None:
            self.show_predict(self.image, self.start_position)
            #self.show_predict(img, start_position)
            


    def paintEvent(self, event):
        painter = QPainter(self)
        
        #rect = QRect(0, 0, self.qimage.width(), self.qimage.height()) # 화면보다 더 크기가 큰가 ..?
        #painter.drawPixmap(rect, self.qimage)
        #self.update()
        
        
        # 버튼을 누를때 실행 됐으면 좋겠는데,
        #if self.lesion_predict_state == True : 
        #print('lesion predict state;;', self.lesion_predict_state)

        # show loading 
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor('red'), 4))
        #painter.setBrush(QColor(255, 255, 255, 70))
        #print('rect;;;', event.rect().x(), event.rect().y(),event.rect().width(), event.rect().height() )
        rect = QRect(QPoint(event.rect().x(), event.rect().y()) , QPoint(event.rect().x() + event.rect().width(), event.rect().y() + event.rect().height()) )
        painter.drawRect(rect)
        painter.fillRect(event.rect(), QBrush(QColor(255, 255, 255, 70)))

        self.loading.start()
        self.loading.setScaledSize(QtCore.QSize(50, 50))
        self.label.move(self.width()/2 -25 , self.height()/2 - 25)

    def show_predict(self, image, position):
        print('show predict;;', self.manual_btn_clicked, self.auto_btn_clicked)

        if image is None:
            msg = QMessageBox()
            msg.warning(self, '경고', '선택된 이미지가 없습니다.')
            
        else : 
            # 선택한 영역 이미지 저장
            cv2.imwrite('input.png', image)

            # 병변 예측하기
            #self.spinner.start()
            #self.spinner.setGeometry(position[0] + int(self.qimage.width()/2), position[1] + int(self.qimage.height()/2), self.qimage.width(), self.qimage.height() ) 
            
            # thread 설정
            worker = Worker(self.image, position, self) #self.start_position, self)
            QtCore.QThreadPool.globalInstance().start(worker)

    @QtCore.pyqtSlot()
    def FinishedPredict(self):
        #self.spinner.stop()
        self.close() 
        # 예측이 완료되었습니다 표시 추가..?
        msg = QMessageBox()
        msg.information(self, '완료', '예측이 완료되었습니다.')

    @QtCore.pyqtSlot(bool)
    def get_click_lesion_predict(self, value):
        self.lesion_predict_state = value
        #self.show_predict(self.image, self.start_position)
        
              
    @staticmethod
    def convert_numpy_img_to_qpixmap(np_img):
        height, width, channel = np_img.shape
        bytesPerLine = 3 * width
        return QPixmap(QImage(np_img.data, width, height, bytesPerLine, QImage.Format_RGB888).rgbSwapped())


    '''
    def keyPressEvent(self, event):
        # esc 버튼 눌렀을 때
        if event.key() == Qt.Key_Escape:
            self.close()
        print('key press event')
        event.accept()
    '''
    
    '''
    # 드래그 할 때
    def mouseMoveEvent(self, a0: QtGui.QMouseEvent):
        self.xy = [(a0.globalX() - self.localPos.x()), (a0.globalY() - self.localPos.y())]
        self.move(*self.xy)

    # 마우스 눌렀을 때
    def mousePressEvent(self, a0: QtGui.QMouseEvent):
        self.localPos = a0.localPos()
    
    # 마우스 놓았을 때
    #def mouseReleaseEvent(self, a0: QtGui.QMouseEvent):
    #    pass   
    '''

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]  # YOLOv5 root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
#ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative


"""
class worker_test(QObject):
    def __init__(self, parent = None ):
        super(self.__class__, self).__init__(parent)
        print('worker_test')

    @pyqtSlot()
    def segmentation(self):
        print('segmentation start')
        predict()


class AutoImageScreen(QObject):
    def __init__(self):
        
        self.worker = worker_test()
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.start()
        self.find_n_predict()
        
    def find_n_predict(self):
        # 안저 이미지 찾고 병변 segmentation
        # 화면 캡쳐 후 저장


        opt = parse_opt()
        bbox = main(opt)
        print('bbox ;;', bbox)
        image = Image.open('capture.png')
        print('img size', image.size)
        crop_img = image.crop(bbox)
        print('crop size;', crop_img.size)
        crop_img.show()


        save_path = os.path.join(ROOT, 'input.png')
        print('save_path;;', save_path)
        crop_img.save(save_path, format = 'PNG')
        
        self.worker.segmentation()
        #predict()

        #worker = Worker(image, position, self) #self.start_position, self)
        #QtCore.QThreadPool.globalInstance().start(worker)
"""

def find_contour(image):
    img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    contours, hierarchy = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    for cnt in contours:
        #print(image.shape, ';;', len(contours))
        cv2.drawContours(image, [cnt], 0, (0, 0, 255, 255), 2)

    return len(contours)



###############################
# 예측한 이미지 보여주기
class PredictImage(QDialog):
    chkbox_state = None 
    EX = None 
    SE = None 
    HE = None 
    MA = None 
    start_position = None
    imgsize = None
    result_img = None
    num_contour = pyqtSignal(list, int, int, int, int)

    def __init__(self, img = None, start_position = (0, 0, 0, 0), parent = None): 
        
        super(PredictImage, self).__init__(parent)
        self.image = img 
        self.start_position = start_position

        # 0 ~ 1.0 값 가질 수 있음
        self.setWindowOpacity(0.7)

        # 상단 바 없애기
        flags = Qt.WindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowFlags(flags)

        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.adjust_geometry()

        self.timer = QTimer(self) # get_chk_press에서 실행

        #self.worker_thread = QThread()
        self.worker = WorkerDetect(self)
        self.worker.threadEvent.connect(self.get_bbox)
        #self.worker.moveToThread(self.worker_thread)
        #self.worker_thread.start()


    def adjust_geometry(self):
        self.setGeometry(self.start_position[0], self.start_position[1], self.start_position[2] - self.start_position[0],self.start_position[3] - self.start_position[1])

    def keyPressEvent(self, event):
        # esc 버튼 눌렀을 때
        if event.key() == Qt.Key_Escape:
            self.close()
        event.accept()

    def adjust_lesion_position(self): # 없어도 될듯?
        #print('adjust lesion')
        #screen_save_path = 'capture.png' #os.path.join(ROOT, 'capture.png') # capture.png로 저장
        #screenshot = ImageGrab.grab()
        #screenshot.save(screen_save_path, format='PNG')
        #opt = parse_opt() # 저장된 이미지 해당 경로에 있는 파일명으로 불러오기,, capture.png 불러오기
        #bbox = main(opt) # x1, y1, w, h
        #print('bbox;;', bbox)
        #bbox = self.worker.detect()
        #self.worker.run()
        #image = Image.open('capture.png')
        # thread 설정

        #QtCore.QThreadPool.globalInstance().start(self.worker)
        self.worker.start()
        #bbox = self.worker.detect()

        # 좌표 이용하여 위치 변경
        #self.setGeometry(bbox[0], bbox[1], bbox[2] - bbox[0], bbox[3] - bbox[1])


    # 윈도우에 그리기
    def paintEvent(self, event):
        painter = QPainter(self)
        self.update()
        if not self.chkbox_state  : 
            pass   
        else :
            result_pixmap = ImageQt(self.result_img)
            result_pixmap = QPixmap.fromImage(result_pixmap)
            #print('predictimage painter:', result_pixmap.width(), result_pixmap.height())
            #print('position;;', *self.start_position)
            #print('adjust geometry', self.start_position[0], self.start_position[1], self.start_position[2] - self.start_position[0],self.start_position[3] - self.start_position[1])
            #self.setGeometry(self.pos().x(), self.pos().y(), result_pixmap.width(), result_pixmap.height())
            #self.resize(result_pixmap.width(), result_pixmap.height())
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            #print('event size;;', event.rect().width(), event.rect().height(), result_pixmap.width(), result_pixmap.height())
            rect = QRect(0, 0, event.rect().width(), event.rect().height())#result_pixmap.width(), result_pixmap.height())
            painter.drawPixmap(rect, result_pixmap)
        
    @pyqtSlot(list)#(list, np.ndarray, np.ndarray, np.ndarray, np.ndarray)
    def get_chk_press(self, state ): #, img0, img1, img2, img3):
        
        self.chkbox_state = state
        if not self.chkbox_state :
            print('체크박스 상태 비어있음...')
            
            pass 
        else : 
            #self.timer.start(1000) # ()msec 마다 반복
            #self.timer.timeout.connect(self.adjust_lesion_position)

            if self.chkbox_state[1] == 0 and self.chkbox_state[2] == 0 and self.chkbox_state[3] == 0 and self.chkbox_state[4] == 0 :
                self.close()
                self.timer.stop()
            else:
                self.show()
            try : 
                img_ex = cv2.imread('EX.png', cv2.IMREAD_UNCHANGED)
                img_se = cv2.imread('SE.png', cv2.IMREAD_UNCHANGED)
                img_he = cv2.imread('HE.png', cv2.IMREAD_UNCHANGED)
                img_ma = cv2.imread('MA.png', cv2.IMREAD_UNCHANGED)

                ex_b, ex_g, ex_r = cv2.split(img_ex)
                se_b, se_g, se_r = cv2.split(img_se)
                he_b, he_g, he_r = cv2.split(img_he)
                ma_b, ma_g, ma_r = cv2.split(img_ma)
                img_ex[img_ex > 0] = 255
                img_se[img_se > 0] = 255
                img_he[img_he > 0] = 255
                img_ma[img_ma > 0] = 255
                canvas = np.zeros(shape = img_ex.shape, dtype=np.uint8)

                if state[1] == 2 : 
                    img_ex = cv2.merge([ canvas[:,:,0], canvas[:,:,1], ex_r ])
                elif state[1] == 0 : 
                    img_ex = np.zeros(shape = img_ex.shape, dtype=np.uint8)

                if state[2] == 2 : 
                    img_se = cv2.merge([ canvas[:,:,0], se_g, se_r ])
                elif state[2] == 0 : 
                    img_se = np.zeros(shape = img_se.shape, dtype=np.uint8)

                if state[3] == 2 : 
                    img_he = cv2.merge([ he_b, he_g, canvas[:,:,2] ])
                elif state[3] == 0 : 
                    img_he = np.zeros(shape = img_he.shape, dtype=np.uint8)

                if state[4] == 2 : 
                    img_ma = cv2.merge([ canvas[:,:,0], ma_g, canvas[:,:,2] ])
                elif state[4] == 0 : 
                    img_ma = np.zeros(shape = img_ma.shape, dtype=np.uint8)

                self.result_img = img_ex + img_se + img_he + img_ma
                self.result_img = cv2.resize(self.result_img, dsize = (self.imgsize[1], self.imgsize[0]) )
                self.result_img = Image.fromarray(self.result_img)
                self.result_img = self.result_img.convert("RGBA")

                # 이미지의 배경부분 투명하게 변경 하기 위함
                data_ex = self.result_img.getdata()
                new_da_ex = []
                for item in data_ex:
                    if item[0] == 0 and item[1] == 0 and item[2] == 0:
                        new_da_ex.append((255, 255, 255, 0)) #(255,255,255,0)
                    else : 
                        new_da_ex.append(item)
                
                self.result_img.putdata(new_da_ex)
                #self.result_img.save('lesion.png')
            except:
                self.close()

    @pyqtSlot(tuple)
    def get_geometry(self, position):
        self.start_position = position
        #self.setGeometry(*self.start_position)
        self.setGeometry(self.start_position[0], self.start_position[1], self.start_position[2] - self.start_position[0],self.start_position[3] - self.start_position[1])

    @pyqtSlot(tuple)
    def get_imgsize(self, shape): 
        # image.shape = height, width, channel
        self.imgsize = shape
        #self.resize(shape[1], shape[0])

    @pyqtSlot(int)
    def get_opacity(self, value):
        self.setWindowOpacity((100-value)/100)

    @pyqtSlot(tuple)
    def get_bbox(self, bbox):
        self.setGeometry(bbox[0], bbox[1], bbox[2] - bbox[0], bbox[3] - bbox[1])

    '''
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
        #if self.to_xy_diff == [0, 0] and self.from_xy_diff == [0, 0]:
        #    pass
        #else:
        #    self.walk_diff(self.from_xy_diff, self.to_xy_diff, self.speed, restart=True)
    
    '''

