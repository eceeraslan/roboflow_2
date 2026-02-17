from PyQt6.QtWidgets import QApplication ,QMainWindow ,QFileDialog, QVBoxLayout,QWidget,QLabel,QPushButton
import sys
from PyQt6.QtCore import Qt

#WELCOME SCREEN
class WelcomeScreen(QWidget):
    def __init__(self):
        super().__init__()

        #labels
        label = QLabel("Annotate your images quickly and easily")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        #buttons
        button = QPushButton("Get Started")
        
        #layout
        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(button)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)



#MAIN WINDOW
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Roboflow 2")
        self.setGeometry(300,50,600,800)
        self.setFixedSize(1000,750)
        self.create_menu()
        welcome = WelcomeScreen()
        self.setCentralWidget(welcome)
    
    def create_menu(self):
        menu_bar = self.menuBar()
        
        file_menu=menu_bar.addMenu("Annota")



if __name__ =="__main__":
    app = QApplication(sys.argv)
    window=MainWindow()
    window.show()

    sys.exit(app.exec())