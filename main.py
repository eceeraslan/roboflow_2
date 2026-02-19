from PyQt6.QtWidgets import * 
import sys
from PyQt6.QtCore import Qt
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

        # MAIN LAYOUT
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label)
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


