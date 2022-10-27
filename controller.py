import sys, math, os 
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QMouseEvent, QPixmap, QIcon

import screen
import controller_select # 캡쳐할 영역을 지정하기 위해 존재함
import cv2
import numpy as np 
from pathlib import Path
from PIL import Image 

from predict_lesion import UNet, VGGBlock #, UNet_, DoubleConv, Up, Down, OutConv


#from PIL import Image
#from PIL.ImageQt import ImageQt


FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]  # YOLOv5 root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH

def find_contour(image):
    img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    contours, hierarchy = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    for cnt in contours:
        #print(image.shape, ';;', len(contours))
        cv2.drawContours(image, [cnt], 0, (0, 0, 255, 255), 2)

    return len(contours)

class control_screen(QWidget):

    chkbox_pressed = pyqtSignal(list)#, np.ndarray, np.ndarray, np.ndarray, np.ndarray)
    setwindgeometry = pyqtSignal(tuple)
    imgsize = pyqtSignal(tuple)
    opacity_value = pyqtSignal(int)

    clicklesionpredict = pyqtSignal()
    manual_btn_clicked = pyqtSignal(bool) 
    auto_btn_clicked = pyqtSignal(bool) 

    def __init__(self, img = None, start_position = (300, 300, 150, 150)):
        super(control_screen, self).__init__()
        
        flags = Qt.WindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowFlags(flags)
        
        self.image = img 
        self.start_position = start_position 
        ##### 선언부 #####
        #self.screen_win = ImageScreen_()
        self.controller_select = controller_select.SnippingWidget()
        self.predictimage = screen.PredictImage(img = None, start_position= self.start_position)
        
        monitor_x = QApplication.desktop().screenGeometry().x()
        monitor_y = QApplication.desktop().screenGeometry().x()
        monitor_width = QApplication.desktop().screenGeometry().width()
        monitor_height = QApplication.desktop().screenGeometry().height()

        
        self.setGeometry( int((monitor_width - monitor_x)/2), int((monitor_height - monitor_y)/2) -250, 125, 100)
        #self.setWindowOpacity(0.7)
    

        if self.image is not None : 
            # image.shape = height, width, channel
            self.imgsize.connect(self.predictimage.get_imgsize)
            self.imgsize.emit(self.image.shape)

        ##################
        self.chk_all = QCheckBox('ALL')#('All', self)
        self.chk_EX  = QCheckBox('EX') #('Hard Exudate', self)
        self.chk_SE  = QCheckBox('SE') #('Soft Exudate', self)
        self.chk_HE  = QCheckBox('HE') #('Hemorrhage', self)
        self.chk_MA  = QCheckBox('MA') #('Microaneurysm', self)
        self.chk_lst = [self.chk_all, self.chk_EX, self.chk_SE, self.chk_HE, self.chk_MA]
        self.setWindowTitle('')
        self.setupUI()


    def setupUI(self):
        main = QVBoxLayout()
        self.setLayout(main)

        button_layout = QVBoxLayout()
        main.addLayout(button_layout)

        new_image = QPushButton('\t수동 찾기', self) # 수동 찾기
        icon_new_img = QPixmap('icon_photo_capture.png')
        new_image.setIcon(QIcon(icon_new_img))

        '''
        self.setStyleSheet("""
        QWidget {
            background-color: rgba(69, 67, 77, 180);
            }
        """)
        

        new_image.setStyleSheet("""
            QPushButton{
        	color: white ;    
        	background-color: rgb(60, 67, 93);
        	
            }
            """
        )
        '''
        #font: bold;
        #border-radius: 5px;
        self.auto_lesion_predict = QPushButton('\t자동 찾기', self)
        icon_lesion_predict = QPixmap('icon_auto.png')
        self.auto_lesion_predict.setIcon(QIcon(icon_lesion_predict))

        '''
        self.auto_lesion_predict.setStyleSheet("""
            QPushButton{
        	color: white ;
        	background-color: rgb(60, 67, 93);
        	
            }
            """
        )
        '''

        # 각 항목 위치 시키기 
        button_layout.addWidget(self.auto_lesion_predict)
        button_layout.addWidget(new_image)
        

        # 연결하기
        new_image.clicked.connect(self.new_image_window)
        self.auto_lesion_predict.clicked.connect(self.call_predict)


        ################# 병변 선택 #####################
        # checkbox 항목
        lesion_group_layout = QVBoxLayout()
        lesion_group = QGroupBox('병변 선택')
        chk_layout = QVBoxLayout()
        main.addLayout(lesion_group_layout)
        # self.chekbox로 __init__에 선언 되어 있음 ..
        '''
        lesion_group.setStyleSheet("""
            QGroupBox{
        	color: white ;
            }
            """
        )
        '''
        # lesion 선택할 수 있는 groupbox추가
        lesion_group_layout.addWidget(lesion_group)
        lesion_group.setLayout(chk_layout)
        
        # 병변선택 checkbox layout
        for chkbox in self.chk_lst:
            chk_layout.addWidget(chkbox)

            '''
            chkbox.setStyleSheet("""
            QCheckbox{
        	color: white ;
            }
            """
            )
            '''
            
        # checkbox의 all을 눌렀을 때 checkbox가 모두 선택되고 해제되게 하기 위함
        self.chk_all.stateChanged.connect(self.chk_all_clicked)
        # checkbox 연결
        self.chkbox_pressed.connect(self.predictimage.get_chk_press)
        #screen.worker_detect()
        

        ################# 위치 조정 ######################
        # 예측한 병변의 위치 조정
        
        geometry_group_layout = QVBoxLayout()
        geometry_layout = QHBoxLayout()
        main.addLayout(geometry_group_layout)
        
        # 예측된 병변의 이미지 위치조정 group
        #lesion_geometry_group = QGroupBox('위치', self)
        #btn_lesion_back = QPushButton('원위치', self)

        # 위치조정 group
        #main.addWidget(lesion_geometry_group)

        #lesion_geometry_group.setLayout(geometry_layout)
        #geometry_layout.addWidget(btn_lesion_back)



        ################# 투명도 조절 #####################
        # 투명도 조절 layout
        win_opacity_layout = QHBoxLayout()
        main.addLayout(win_opacity_layout)
        # 투명도 조절 groupbox
        #win_opacity_group = QGroupBox('투명도')
        label_opacity = QLabel('투명도')
        slider_opacity = QSlider(Qt.Horizontal, self)
        label_opacity_value = QLabel('0')

        '''
        label_opacity.setStyleSheet("""
            QLabel{
        	color: white ;
            }
            """
        )
        '''

        '''
        label_opacity_value.setStyleSheet("""
            QLabel{
        	color: white ;
            }
            """
        )
        '''

        # 빈칸 layout
        box = QHBoxLayout()

        def change_opacity_value(value):
            label_opacity_value.setText(str(value))

            # signal 보내기
            self.opacity_value.connect(self.predictimage.get_opacity)
            self.opacity_value.emit(value)
 
        # 투명도 조절 groupbox
        #main.addWidget(win_opacity_group)
        main.addLayout(win_opacity_layout)
        win_opacity_layout.addWidget(label_opacity)
        win_opacity_layout.addWidget(slider_opacity)
        win_opacity_layout.addWidget(label_opacity_value)
        #win_opacity_group.setLayout(win_opacity_layout)

        #######################################

        

        #lesion_group.setLayout(chk_layout)
        
        #######################################

        ###### 연결부분
        

        #btn_lesion_back.clicked.connect(self.click_btn)

        for checkbox in self.chk_lst:
            checkbox.stateChanged.connect(self.checkbox_change)

        # 투명도 값 
        slider_opacity.valueChanged.connect(change_opacity_value)

    # https://learndataanalysis.org/qcheckbox-select-all-select-none-pyqt5-tutorial/
    # checkbox all버튼을 눌렀을 때는 나머지 checkbox가 클릭됨
    def chk_all_clicked(self, state):
        for checkbox in self.chk_lst:
            checkbox.setCheckState(state)

    def checkbox_change(self):
        # 버튼 상태 저장을 위한 list
        # state: all, ex, se, he, ma
        # image read >
        state = []

        #if self.image is not None :
        for chkbox in self.chk_lst :
            
            state.append(chkbox.checkState())

        else :    
            pass 
            # 이미지가 선택되지 않았습니다.
            
        # 체크박스 눌 렀을 때 작동 
        self.chkbox_pressed.emit(state) #, img_ex, img_se, img_he, img_ma)
        #self.predictimage.show()
        if self.image is not None : 
            img_ex = cv2.imread('EX.png', cv2.IMREAD_COLOR)
            img_se = cv2.imread('SE.png', cv2.IMREAD_COLOR)
            img_he = cv2.imread('HE.png', cv2.IMREAD_COLOR)
            img_ma = cv2.imread('MA.png', cv2.IMREAD_COLOR)

            contour_ex = find_contour(img_ex)
            contour_se = find_contour(img_se)
            contour_he = find_contour(img_he)
            contour_ma = find_contour(img_ma)

            if state[1] == 2:
                self.chk_EX.setText('EX' + '\t\t' + str(contour_ex))
            else : 
                self.chk_EX.setText('EX')

            if state[2] == 2:
                self.chk_SE.setText('SE' + '\t\t' + str(contour_se))
            else : 
                self.chk_SE.setText('SE')

            if state[3] == 2:
                self.chk_HE.setText('HE' + '\t\t' + str(contour_he))
            else : 
                self.chk_HE.setText('HE')

            if state[4] == 2:
                self.chk_MA.setText('MA' + '\t\t' + str(contour_ma))
            else : 
                self.chk_MA.setText('MA')

        #return state

    def new_image_window(self):
        self.hide()
        # start 함수가 캡쳐할 떄 열리는 창?
        self.controller_select.start()
    
    # auto detect and segmentation 
    def call_predict(self):
        self.hide()
        #msg = QMessageBox()
        #msg.warning(self, '찾는 중', '안저 찾는 중.')
        self.controller_select.detectimage()
        #msg.close()
        #self.show()

    def click_btn(self):                                                                                                                               
        # 처음 설정한 위치로 돌아가는 기능
        self.setwindgeometry.connect(self.predictimage.get_geometry)
        self.setwindgeometry.emit(self.start_position)

    def keyPressEvent(self, event):
        # esc 버튼 눌렀을 때
        if event.key() == Qt.Key_Escape:
            self.close()
            self.predictimage.close()
        '''
        if event.key() == Qt.Key_0:
            print('0') 
            self.hide()
        if event.key() == Qt.Key_1:
            print('1')
            self.show()                                                    
        '''
        event.accept()

    # 드래그 할 때
    def mouseMoveEvent(self, a0: QMouseEvent):
        self.xy = [(a0.globalX() - self.localPos.x()), (a0.globalY() - self.localPos.y())]
        self.move( *self.xy )

    # 마우스 눌렀을 때
    def mousePressEvent(self, a0: QMouseEvent):
        self.localPos = a0.localPos()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    control = control_screen()
    control.show()
    sys.exit(app.exec_())

