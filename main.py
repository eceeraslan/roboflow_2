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
        self.setDragMode(QGraphicsView.DragMode.NoDrag)

    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())

        if isinstance(item, QGraphicsRectItem):
            super().mousePressEvent(event)
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = self.mapToScene(event.pos())

    def mouseMoveEvent(self,event):
        if not self.start_pos:
            super().mouseMoveEvent(event)
            return
        
        end_pos=self.mapToScene(event.pos())
        rect=QRectF(self.start_pos,end_pos).normalized()

        if self.current_rect:
            self.scene().removeItem(self.current_rect)

        self.current_rect=self.scene().addRect(rect,QPen(Qt.GlobalColor.red,2,Qt.PenStyle.DashLine))
        self.current_rect.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable,True)
        self.current_rect.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable,True)
            
    def mouseReleaseEvent(self, event):
        if not self.start_pos:
            super().mouseReleaseEvent(event)
            return
        
        if event.button() == Qt.MouseButton.LeftButton and self.current_rect:

            self.current_rect.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
            self.current_rect.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)

            label, ok = QInputDialog.getText(self, "Label", "Enter Label:")

            if ok and label:
                text_item = QGraphicsTextItem(label, self.current_rect)
                text_item.setDefaultTextColor(Qt.GlobalColor.darkCyan)
                rect = self.current_rect.rect()
                text_item.setPos(rect.x(), rect.y() - 20)
                self.current_rect.label_item = text_item

            self.rectangles.append({
                "rect": self.current_rect.rect(),
                "label": label if ok and label else ""
            })

            self.current_rect = None
            self.start_pos = None

   
    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())

        if isinstance(item, QGraphicsRectItem):

            menu = QMenu(self)
            delete_action = menu.addAction("Delete")

            action = menu.exec(event.globalPos())

            if action == delete_action:
                if hasattr(item, "label_item"):
                    self.scene().removeItem(item.label_item)
                self.rectangles = [r for r in self.rectangles if r["rect"] != item.rect()]
                self.scene().removeItem(item)


#UPLOAD SCREEN
class UploadScreen(QWidget):
    def __init__(self):
        super().__init__()

        self.files=[]
        self.boxes={}
        self.current_image=None
        
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


        self.list_widget=QListWidget()
        self.list_widget.setIconSize(QSize(80,80))
        self.list_widget.setFixedWidth(130)
        self.list_widget.itemClicked.connect(self.show_image)

        #image view area
        self.scene = QGraphicsScene()
        self.view = GraphicsView(self.scene)
        self.view.setAlignment(Qt.AlignmentFlag.AlignCenter)

        #LAYOUT
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.label)
        right_layout.addWidget(self.view, stretch=4)
        right_layout.addWidget(self.scroll, stretch=1)
        right_layout.addWidget(self.button)
        
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.list_widget)
        main_layout.addLayout(right_layout)
        self.setLayout(main_layout)


    def file_open(self):
        files,_=QFileDialog.getOpenFileNames(
            self,
            "Select images",
            "",
            "Images (*.png *.jpg *.jpeg)"
        )
        
        if files : 
            self.list_widget.clear()
            self.files=files

            for f in self.files:
                pixmap = QPixmap(f)
                thumbnail = pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio)
                icon = QIcon(thumbnail)
                item =QListWidgetItem(icon, "")
                item.setData(Qt.ItemDataRole.UserRole,f)
                self.list_widget.addItem(item)

            self.list_widget.setCurrentRow(0)
            self.show_image(self.list_widget.item(0))

    def show_image(self, item):
        image_path = item.data(Qt.ItemDataRole.UserRole)
        pix_map = QPixmap(image_path)

        if self.current_image:
            self.boxes[self.current_image] = self.view.rectangles.copy()

        self.scene.clear()
        self.current_image = image_path
        self.view.rectangles = []

        new_scene = self.scene.addPixmap(pix_map)
        self.view.fitInView(new_scene, Qt.AspectRatioMode.KeepAspectRatio)

        if image_path in self.boxes:
            for box_data in self.boxes[image_path]:
                rect = box_data["rect"]
                label = box_data["label"]
                new_box = self.scene.addRect(rect, QPen(Qt.GlobalColor.red, 2, Qt.PenStyle.DashLine))
                new_box.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
                new_box.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
                if label:
                    text_item = QGraphicsTextItem(label, new_box)
                    text_item.setDefaultTextColor(Qt.GlobalColor.darkCyan)
                    text_item.setPos(rect.x(), rect.y() - 20)
                    new_box.label_item = text_item
                self.view.rectangles.append({"rect": rect, "label": label})
        
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


