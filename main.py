from PyQt6.QtWidgets import * 
import sys
from PyQt6.QtCore import *
import os
from PyQt6.QtGui import *


#WELCOME SCREEN
class WelcomeScreen(QWidget):
    def __init__(self,switch_screen):
        super().__init__()

        #labels
        self.label = QLabel("Annotate your images quickly and easily")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        #buttons
        self.button = QPushButton("Get Started")
        self.button.clicked.connect(switch_screen)
        
        #layout
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.button)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(self.layout)

class GraphicsView(QGraphicsView):
    def __init__(self,scene):
        super().__init__(scene)

        self.start_pos=None
        self.current_rect=None
        self.rectangles=[]
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = self.mapToScene(event.pos())

    def mouseMoveEvent(self,event):
        if self.start_pos:
            end_pos=self.mapToScene(event.pos())

            rect=QRectF(self.start_pos,end_pos).normalized()

            if self.current_rect:
                self.scene().removeItem(self.current_rect)

            self.current_rect=self.scene().addRect(rect,QPen(Qt.GlobalColor.red,2))
            

    def mouseReleaseEvent(self,event):
        if event.button() ==Qt.MouseButton.LeftButton and self.current_rect:
            self.rectangles.append(self.current_rect)
            
            label , ok = QInputDialog.getText(self,"Label","Enter Label: ")

            if ok and label : 
                rect_geometry = self.current_rect.rect()
                top_left_scene = self.current_rect.mapToScene(rect_geometry.topLeft())

                text_item = self.scene().addText(label)
                text_item.setDefaultTextColor(Qt.GlobalColor.darkCyan)
                text_item.setPos(top_left_scene)
                self.current_rect.label_item = text_item

            self.current_rect = None
            self.start_pos=None

   
             
    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())

        if isinstance(item, QGraphicsRectItem):

            menu = QMenu(self)
            delete_action = menu.addAction("Delete")

            action = menu.exec(event.globalPos())

            if action == delete_action:
        
                if hasattr(item, "label_item"):
                    self.scene().removeItem(item.label_item)
                self.scene().removeItem(item)


#UPLOAD SCREEN
class UploadScreen(QWidget):
    def __init__(self):
        super().__init__()
        
        #labels
        self.label= QLabel("Upload your images here")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label1 = QLabel(f"Use your own data to start annotating\nUpload and label your images")
        self.label1.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        #buttons
        self.button = QPushButton("Select Images")
        self.button.clicked.connect(self.file_open)
       # SCROLL
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setContentsMargins(10, 10, 10, 10)

        self.scroll_layout.addWidget(self.label1)
        self.scroll.setWidget(self.scroll_widget)
        self.scroll.setFrameShape(QFrame.Shape.Box)

        #image view area
        self.scene = QGraphicsScene()
        self.view = GraphicsView(self.scene)
        self.view.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # MAIN LAYOUT
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.view, stretch=4)
        self.layout.addWidget(self.scroll, stretch=1) 
        self.layout.addWidget(self.button)
        self.setLayout(self.layout)



    def file_open(self):
        files,_=QFileDialog.getOpenFileNames(
            self,
            "Select images",
            "",
            "Images (*.png *.jpg *.jpeg)"
        )
        
        if files : 
            image_path = files[0]
            pixmap = QPixmap(image_path)
            
            if pixmap.isNull():
                print("image could not loaded")
                return
            self.scene.clear()
            item = self.scene.addPixmap(pixmap)
            self.scene.setSceneRect(QRectF(pixmap.rect()))
            self.view.fitInView(item,Qt.AspectRatioMode.KeepAspectRatio)
            
            self.view.setFocus()

     
            
            names = [os.path.basename(f) for f in files]
            self.label1.setText("\n".join(names))
        

        

#MAIN WINDOW
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Roboflow 2")
        self.setGeometry(300,50,600,800)
        self.setFixedSize(1000,750)
        
        self.create_menu()
        
        self.stack=QStackedWidget()
        
        self.welcome = WelcomeScreen(self.show_upload)
        self.upload = UploadScreen()
       
        self.stack.addWidget(self.welcome)
        self.stack.addWidget(self.upload)

        self.setCentralWidget(self.stack)
    
    def show_upload(self):
        self.stack.setCurrentWidget(self.upload)


    def create_menu(self):
        menu_bar = self.menuBar()
        
        file_menu=menu_bar.addMenu("Annota")

        

if __name__ =="__main__":
    app = QApplication(sys.argv)
    window=MainWindow()
    window.show()

    sys.exit(app.exec())


