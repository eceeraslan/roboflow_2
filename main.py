from PyQt6.QtWidgets import * 
import sys
from PyQt6.QtCore import *
import os
from PyQt6.QtGui import *
import shutil
import json
import random

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
    def __init__(self,scene,upload_screen):
        super().__init__(scene)

        self.upload_screen=upload_screen
        self.start_pos=None
        self.current_rect=None
        self.rectangles=[]
        self.current_tool="bbox"
        self.history=[]
        self.redo_stack = []
        self.polygon_points=[]
        self.current_polygon = None
        self.min_zoom = 1.0
        
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)


    def mousePressEvent(self, event):
        

        if event.button() == Qt.MouseButton.RightButton:
            super().mousePressEvent(event)
            return

        if self.current_tool =="select" :
            super().mousePressEvent(event)
            return

        if self.current_tool =="freehand":
            self.polygon_points=[]
            self.start_pos = None
            self.start_pos = self.mapToScene(event.pos())
            self.polygon_points.append(self.start_pos)  
            return
        
        item = self.itemAt(event.pos())

        if isinstance(item, (QGraphicsRectItem, QGraphicsPolygonItem, QGraphicsTextItem)):
            super().mousePressEvent(event)
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = self.mapToScene(event.pos())


    def mouseMoveEvent(self, event):
        
        if self.current_tool == "select":
            super().mouseMoveEvent(event)
            return
        
        if self.current_tool == "freehand" and self.polygon_points:
            pos = self.mapToScene(event.pos())
            self.polygon_points.append(pos)

            if self.current_polygon:
                self.scene().removeItem(self.current_polygon)

            polygon =   QPolygonF(self.polygon_points)
            self.current_polygon = self.scene().addPolygon(
                polygon ,
                QPen(Qt.GlobalColor.red, 2),
                QBrush(QColor(255, 0, 0, 50))
            )
            return

        if not self.start_pos:
            super().mouseMoveEvent(event)
            return
        
        end_pos = self.mapToScene(event.pos())
        
        scene_rect = self.scene().sceneRect()
        end_pos.setX(max(scene_rect.left(), min(end_pos.x(), scene_rect.right())))
        end_pos.setY(max(scene_rect.top(), min(end_pos.y(), scene_rect.bottom())))
        
        rect = QRectF(self.start_pos, end_pos).normalized()

        if self.current_rect:
            self.scene().removeItem(self.current_rect)

        self.current_rect = self.scene().addRect(rect, QPen(Qt.GlobalColor.red, 2, Qt.PenStyle.DashLine))
        self.current_rect.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.current_rect.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        event.accept()
            
    def mouseReleaseEvent(self, event):

        if self.current_tool == "select":
            super().mouseReleaseEvent(event)
            return
        
        if self.current_tool == "freehand" and self.polygon_points:
            if self.current_polygon:
                self.scene().removeItem(self.current_polygon)
            
            if not self.upload_screen.classes:
                QMessageBox.warning(self, "Uyarı", "First add class please!")
                self.polygon_points = []
                self.current_polygon = None
                return
            
            label, ok = QInputDialog.getItem(self, "Label", "Choose Class:", self.upload_screen.classes, 0, False)
            
            if ok and label:
                polygon = QPolygonF(self.polygon_points)
                item = self.scene().addPolygon(
                    polygon,
                    QPen(Qt.GlobalColor.red, 2),
                    QBrush(QColor(255, 0, 0, 50))
                )
                text_item = QGraphicsTextItem(label, item)
                text_item.setDefaultTextColor(Qt.GlobalColor.darkCyan)
                first_point = self.polygon_points[0]
                text_item.setPos(item.mapFromScene(first_point))
                
                self.rectangles.append({
                    "rect": item.boundingRect(),
                    "label": label,
                    "type": "freehand",
                    "points": [(p.x(), p.y()) for p in self.polygon_points]
                })
                self.upload_screen.label_list.addItem(label)
                self.history.append(self.rectangles.copy())
            
            self.polygon_points = []
            self.current_polygon = None
            self.start_pos = None
            self.current_rect = None
            return                       
        
        if not self.start_pos:
            super().mouseReleaseEvent(event)
            return
        
        if event.button() == Qt.MouseButton.LeftButton and self.current_rect:

            self.current_rect.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
            self.current_rect.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)

            if not self.upload_screen.classes:
                QMessageBox.warning(self, "Uyarı", "First add class please!")
                self.scene().removeItem(self.current_rect)
                self.current_rect = None
                self.start_pos = None
                return

            label, ok = QInputDialog.getItem(self, "Label", "Choose Class:", self.upload_screen.classes, 0, False)

            if ok and label:
                text_item = QGraphicsTextItem(label, self.current_rect)
                text_item.setDefaultTextColor(Qt.GlobalColor.darkCyan)
                rect = self.current_rect.rect()
                text_item.setPos(rect.x(), rect.y() - 20)
                self.current_rect.label_item = text_item

            self.rectangles.append({
                "rect": self.current_rect.rect(),
                "label": label if ok and label else "",
                "type": "bbox"
            })

            self.upload_screen.label_list.addItem(label)

            self.history.append(self.rectangles.copy())

            self.current_rect = None
            self.start_pos = None

   
    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())

        if isinstance(item, QGraphicsTextItem):
            item = item.parentItem()

        if isinstance(item, (QGraphicsRectItem, QGraphicsPolygonItem)):
            menu = QMenu(self)
            delete_action = menu.addAction("Delete")
            action = menu.exec(event.globalPos())

            if action and action == delete_action:
                if hasattr(item, "label_item"):
                    self.scene().removeItem(item.label_item)
                
                item_rect = item.boundingRect() if isinstance(item, QGraphicsPolygonItem) else item.rect()
                self.rectangles = [r for r in self.rectangles 
                                if not (abs(r["rect"].x() - item_rect.x()) < 0.01 and 
                                        abs(r["rect"].y() - item_rect.y()) < 0.01)]
                self.scene().removeItem(item)
                self.upload_screen.label_list.clear()
                for box_data in self.rectangles:
                    self.upload_screen.label_list.addItem(box_data["label"])

    def undo(self):
        if not self.history:
            return
        
        self.history.pop()
        self.redo_stack.append(self.rectangles.copy())
        
        if self.history:
            self.rectangles = self.history[-1].copy()
        else:
            self.rectangles = []
        
        self.scene().clear()
        self.upload_screen.label_list.clear()
        
        pixmap = QPixmap(self.upload_screen.current_image)
        new_scene = self.scene().addPixmap(pixmap)
        self.scene().setSceneRect(new_scene.boundingRect())
        self.fitInView(new_scene, Qt.AspectRatioMode.KeepAspectRatio)
        
        for box_data in self.rectangles:
            rect = box_data["rect"]
            label = box_data["label"]
            self.upload_screen.label_list.addItem(label)
            
            if box_data.get("type") == "freehand":
                points = [QPointF(x, y) for x, y in box_data["points"]]
                new_box = self.scene().addPolygon(
                    QPolygonF(points),
                    QPen(Qt.GlobalColor.red, 2),
                    QBrush(QColor(255, 0, 0, 50))
                )
                if label:
                    text_item = QGraphicsTextItem(label, new_box)
                    text_item.setDefaultTextColor(Qt.GlobalColor.darkCyan)
                    text_item.setPos(new_box.mapFromScene(points[0]))
            else:
                new_box = self.scene().addRect(rect, QPen(Qt.GlobalColor.red, 2, Qt.PenStyle.DashLine))
                new_box.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
                new_box.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
                if label:
                    text_item = QGraphicsTextItem(label, new_box)
                    text_item.setDefaultTextColor(Qt.GlobalColor.darkCyan)
                    text_item.setPos(rect.x(), rect.y() - 20)
                    new_box.label_item = text_item

    def redo(self):
        if not self.redo_stack:
            return
        
        state = self.redo_stack.pop()
        self.rectangles = state.copy()
        self.history.append(state.copy())
        
        self.scene().clear()
        self.upload_screen.label_list.clear()
        
        pixmap = QPixmap(self.upload_screen.current_image)
        new_scene = self.scene().addPixmap(pixmap)
        self.scene().setSceneRect(new_scene.boundingRect())
        self.fitInView(new_scene, Qt.AspectRatioMode.KeepAspectRatio)
        
        for box_data in self.rectangles:
            rect = box_data["rect"]
            label = box_data["label"]
            self.upload_screen.label_list.addItem(label)
            
            if box_data.get("type") == "freehand":
                points = [QPointF(x, y) for x, y in box_data["points"]]
                new_box = self.scene().addPolygon(
                    QPolygonF(points),
                    QPen(Qt.GlobalColor.red, 2),
                    QBrush(QColor(255, 0, 0, 50))
                )
                if label:
                    text_item = QGraphicsTextItem(label, new_box)
                    text_item.setDefaultTextColor(Qt.GlobalColor.darkCyan)
                    text_item.setPos(new_box.mapFromScene(points[0]))
            else:
                new_box = self.scene().addRect(rect, QPen(Qt.GlobalColor.red, 2, Qt.PenStyle.DashLine))
                new_box.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
                new_box.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
                if label:
                    text_item = QGraphicsTextItem(label, new_box)
                    text_item.setDefaultTextColor(Qt.GlobalColor.darkCyan)
                    text_item.setPos(rect.x(), rect.y() - 20)
                    new_box.label_item = text_item

    
    def keyPressEvent(self, event):
        
        if event.key() == Qt.Key.Key_Down:
            if self.transform().m11() > self.min_zoom * 1.01:
                self.verticalScrollBar().setValue(self.verticalScrollBar().value() + 20)
            else:
                count = self.upload_screen.list_widget.count()
                index = self.upload_screen.list_widget.currentRow()
                next_index = index + 1
                if next_index >= count:
                    return
                next_item = self.upload_screen.list_widget.item(next_index)
                self.upload_screen.list_widget.setCurrentRow(next_index)
                self.upload_screen.show_image(next_item)

                    
        elif event.key() == Qt.Key.Key_Up:
            if self.transform().m11() > self.min_zoom * 1.01:
                self.verticalScrollBar().setValue(self.verticalScrollBar().value() - 20)
            else:
                index = self.upload_screen.list_widget.currentRow()
                next_index = index - 1
                next_item = self.upload_screen.list_widget.item(next_index)
                if next_index < 0:
                    return
                self.upload_screen.list_widget.setCurrentRow(next_index)
                self.upload_screen.show_image(next_item)

        elif event.key() == Qt.Key.Key_Right:
            if self.transform().m11() > 1.0:
                self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + 20)

        elif event.key() == Qt.Key.Key_Left:
            if self.transform().m11() > 1.0:
                self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - 20)

        elif event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_Backspace:
            for item in self.scene().selectedItems():
                self.scene().removeItem(item)
                self.rectangles = [r for r in self.rectangles if r["rect"] != item.rect()]
            self.upload_screen.label_list.clear()
            for box_data in self.rectangles:
                self.upload_screen.label_list.addItem(box_data["label"])

        elif event.key() == Qt.Key.Key_Z and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.undo()

        elif event.key() == Qt.Key.Key_Y and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.redo()


    def wheelEvent(self, event):
        
        if event.angleDelta().y() > 0:
            self.scale(1.1, 1.1)
        
        elif event.angleDelta().y() < 0:
            if self.transform().m11() > self.min_zoom:
                self.scale(0.9, 0.9)
        


#UPLOAD SCREEN
class UploadScreen(QWidget):
    def __init__(self):
        super().__init__()

        self.files=[]
        self.boxes={}
        self.boxes_history = {}
        self.current_image=None

        self.classes=[]
        
        #labels
        self.label= QLabel("Upload your images here")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label1 = QLabel(f"Use your own data to start annotating\nUpload and label your images")
        self.label1.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        #buttons
        self.button = QPushButton("Select Images")
        self.button.clicked.connect(self.file_open)
        self.add_button = QPushButton("Add Class")
        self.add_button.clicked.connect(self.add_class)
        
        
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


        #label list area
        self.label_list=QListWidget()
        self.label_list.setFixedWidth(180)
        
        self.class_list = QListWidget()
        self.class_list.setFixedWidth(180)
        
        #image view area
        self.scene = QGraphicsScene()
        self.view = GraphicsView(self.scene,self)
        self.view.setAlignment(Qt.AlignmentFlag.AlignCenter)

        #toolbar
        self.toolbar = QWidget()
        self.toolbar_layout =QVBoxLayout(self.toolbar)
        self.toolbar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.toolbar.setFixedWidth(40)

        self.btn_select = QPushButton("🖱")
        self.btn_bbox =QPushButton("⬜")
        self.btn_freehand = QPushButton("🖌")
        self.btn_clear = QPushButton("⊘")


        self.btn_select.setFixedSize(30,30)
        self.btn_bbox.setFixedSize(30,30)
        self.btn_freehand.setFixedSize(30, 30)
        self.btn_clear.setFixedSize(30,30)

        self.btn_select.clicked.connect(self.set_select)
        self.btn_bbox.clicked.connect(self.set_bbox)
        self.btn_freehand.clicked.connect(self.set_freehand)
        self.btn_clear.clicked.connect(self.clear_annotations)

        self.btn_undo=QPushButton("↩")
        self.btn_redo = QPushButton("↪")
        
        self.btn_undo.setFixedSize(30,30)
        self.btn_redo.setFixedSize(30,30)
        
        self.btn_undo.clicked.connect(self.view.undo)
        self.btn_redo.clicked.connect(self.view.redo)

        self.btn_undo.pressed.connect(lambda: self.btn_undo.setStyleSheet("background-color: rgba(0, 120, 255, 0.3);"))
        self.btn_undo.released.connect(lambda: self.btn_undo.setStyleSheet(""))

        self.btn_redo.pressed.connect(lambda: self.btn_redo.setStyleSheet("background-color: rgba(0, 120, 255, 0.3);"))
        self.btn_redo.released.connect(lambda: self.btn_redo.setStyleSheet(""))

        self.btn_clear.pressed.connect(lambda: self.btn_clear.setStyleSheet("background-color: rgba(0, 120, 255, 0.3);"))
        self.btn_clear.released.connect(lambda: self.btn_clear.setStyleSheet(""))

        self.toolbar_layout.addWidget(self.btn_select)
        self.toolbar_layout.addWidget(self.btn_bbox)
        self.toolbar_layout.addWidget(self.btn_undo)
        self.toolbar_layout.addWidget(self.btn_redo)
        self.toolbar_layout.addWidget(self.btn_freehand)
        self.toolbar_layout.addWidget(self.btn_clear)



        #right panel
        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("Classes:"))
        right_panel.addWidget(self.add_button)
        right_panel.addWidget(self.class_list)
        right_panel.addWidget(QLabel("Annotations:"))
        right_panel.addWidget(self.label_list)
        
        #LAYOUT
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.label)
        right_layout.addWidget(self.view, stretch=4)
        right_layout.addWidget(self.scroll, stretch=1)
        right_layout.addWidget(self.button)
        
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.list_widget)
        main_layout.addLayout(right_layout)
        main_layout.addWidget(self.toolbar)
        main_layout.addLayout(right_panel)

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
            QTimer.singleShot(0, lambda: self.show_image(self.list_widget.item(0)))

        
    def add_class(self):
        label, ok = QInputDialog.getText(self, "Label", "Enter Label:")
        if ok and label:
            self.classes.append(label)
            

            item =QListWidgetItem(self.class_list)
            widget=QWidget()
            layout=QHBoxLayout(widget)

            text_label =QLabel(label)
            delete_btn =QPushButton("x")
            delete_btn.setFixedSize(20,20)
            delete_btn.clicked.connect(lambda: self.remove_class(item,label))

            layout.addWidget(text_label)
            layout.addWidget(delete_btn)

            item.setSizeHint(widget.sizeHint())
            self.class_list.setItemWidget(item,widget)

    def remove_class(self,item,label):
        row = self.class_list.row(item)
        self.class_list.takeItem(row)
        self.classes.remove(label)

    def set_select(self):
        self.view.current_tool = "select"
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.btn_select.setStyleSheet("background-color: rgba(0, 120, 255, 0.3);")
        self.btn_bbox.setStyleSheet("")
        self.btn_freehand.setStyleSheet("")

    def set_bbox(self):
        self.view.current_tool = "bbox"
        self.btn_bbox.setStyleSheet("background-color: rgba(0,120,255,0.3)")
        self.btn_select.setStyleSheet("")
        self.btn_freehand.setStyleSheet("")
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)

    def set_freehand(self):
        self.view.current_tool = "freehand"
        self.btn_freehand.setStyleSheet("background-color: rgba(0, 120, 255, 0.3);")
        self.btn_bbox.setStyleSheet("")
        self.btn_select.setStyleSheet("")
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)

    def clear_annotations(self):
        
        self.view.rectangles = []
        self.view.history = []
        self.scene.clear()
        self.label_list.clear()
        
        pixmap = QPixmap(self.current_image)
        new_scene = self.scene.addPixmap(pixmap)
        self.scene.setSceneRect(new_scene.boundingRect())
        self.view.fitInView(new_scene, Qt.AspectRatioMode.KeepAspectRatio)
        self.view.min_zoom = self.view.transform().m11()


    def show_image(self, item):
        self.label_list.clear()
        image_path = item.data(Qt.ItemDataRole.UserRole)
        pix_map = QPixmap(image_path)

        if self.current_image:
            self.boxes[self.current_image] = self.view.rectangles.copy()
            self.boxes_history[self.current_image] = self.view.history.copy()

        self.scene.clear()
        self.current_image = image_path
        self.view.rectangles = []
        self.view.history = self.boxes_history.get(image_path, [])

        new_scene = self.scene.addPixmap(pix_map)
        self.scene.setSceneRect(new_scene.boundingRect())
        self.view.fitInView(new_scene, Qt.AspectRatioMode.KeepAspectRatio)
        self.view.min_zoom = self.view.transform().m11()
        

        if image_path in self.boxes:
            for box_data in self.boxes[image_path]:
                rect = box_data["rect"]
                label = box_data["label"]
                self.label_list.addItem(label)
                
                if box_data.get("type") == "freehand":
                    points = [QPointF(x, y) for x, y in box_data["points"]]
                    new_box = self.scene.addPolygon(
                        QPolygonF(points),
                        QPen(Qt.GlobalColor.red, 2),
                        QBrush(QColor(255, 0, 0, 50))
                    )
                    if label:
                        text_item = QGraphicsTextItem(label, new_box)
                        text_item.setDefaultTextColor(Qt.GlobalColor.darkCyan)
                        text_item.setPos(new_box.mapFromScene(points[0]))
                else:
                    new_box = self.scene.addRect(rect, QPen(Qt.GlobalColor.red, 2, Qt.PenStyle.DashLine))
                    new_box.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
                    new_box.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
                    if label:
                        text_item = QGraphicsTextItem(label, new_box)
                        text_item.setDefaultTextColor(Qt.GlobalColor.darkCyan)
                        text_item.setPos(rect.x(), rect.y() - 20)
                        new_box.label_item = text_item
                
                self.view.rectangles.append(box_data)
        
        self.view.setFocus()

        
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
        self.file_menu.menuAction().setVisible(True)
        self.export_menu.menuAction().setVisible(True)

    def export_yolo(self):

        files =self.upload.files.copy()
        random.shuffle(files)

        total = len(files)
        train_count=int(total * 0.7)
        val_count = int(total * 0.2)


        train_files = files[:train_count]
        val_files = files[train_count:train_count + val_count]
        test_files = files[train_count + val_count:]


        folder = QFileDialog.getExistingDirectory(self,"Select export folder")
        if not folder:
            return
        
        for split in["train","val","test"]:
            os.makedirs(os.path.join(folder, split, "images"), exist_ok=True)
            os.makedirs(os.path.join(folder, split, "labels"), exist_ok=True)

        if self.upload.current_image:
            self.upload.boxes[self.upload.current_image] = self.upload.view.rectangles.copy()

        all_labels = []
        for box_list in self.upload.boxes.values():
            for box_data in box_list:
                if box_data["label"] and box_data["label"] not in all_labels:
                    all_labels.append(box_data["label"])

        for image_path, box_list in self.upload.boxes.items():
            if not box_list:
                continue

            if image_path in train_files:
                split = "train"
            elif image_path in val_files:
                split = "val"
            else:
                split = "test"

            images_dir = os.path.join(folder, split, "images")
            labels_dir = os.path.join(folder, split, "labels")

            image_name = os.path.basename(image_path)
            shutil.copy(image_path, os.path.join(images_dir, image_name))

            img = QPixmap(image_path)
            img_width = img.width()
            img_height = img.height()

            txt_name = os.path.splitext(image_name)[0] + ".txt"
            txt_path = os.path.join(labels_dir, txt_name)

            with open(txt_path, "w") as f:
                for box_data in box_list:
                    rect = box_data["rect"]
                    label = box_data["label"]

                    if not label:
                        continue

                    x = rect.x()
                    y = rect.y()
                    w = rect.width()
                    h = rect.height()

                    cx = (x + w / 2) / img_width
                    cy = (y + h / 2) / img_height
                    nw = w / img_width
                    nh = h / img_height

                    class_id = all_labels.index(label)
                    f.write(f"{class_id} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}\n")

        classes_path = os.path.join(folder, "classes.txt")
        with open(classes_path, "w") as f:
            for label in all_labels:
                f.write(label + "\n")

        yaml_path = os.path.join(folder, "data.yaml")
        with open(yaml_path, "w") as f:
            f.write(f"nc: {len(all_labels)}\n")
            f.write(f"names: {all_labels}\n")
            f.write(f"train: train/images/\n")
            f.write(f"val: val/images/\n")
            f.write(f"test: test/images/\n")

        try:
            QMessageBox.information(self,"Success", "Export completed successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")

    
    def save_project(self):
        file_path,_=QFileDialog.getSaveFileName(self,"Save Project","","JSON Files (*.json)")
        if not file_path:
            return
        if self.upload.current_image:
            self.upload.boxes[self.upload.current_image]=self.upload.view.rectangles.copy()

        data={  "files": self.upload.files,
                "classes": self.upload.classes,
                "boxes": {}                 }

        for image_path, box_list in self.upload.boxes.items():
            data["boxes"][image_path] = []
            for box_data in box_list:
                rect = box_data["rect"]
                data["boxes"][image_path].append({
                    "x": rect.x(),
                    "y": rect.y(),
                    "w": rect.width(),
                    "h": rect.height(),
                    "label": box_data["label"]
                })
        with open(file_path,"w") as f:
            json.dump(data,f)

        QMessageBox.information(self,"Success","Project saved successfuully!")

    def load_project(self):
        file_path,_=QFileDialog.getOpenFileName(self,"Load Project","","JSON Files (*.json)")
        if not file_path:
            return
        with open(file_path,"r") as f:
            data = json.load(f)
        
        self.upload.boxes = {}

        for image_path, box_list in data["boxes"].items():
            self.upload.boxes[image_path] = []
            for box_data in box_list:
                rect = QRectF(box_data["x"], box_data["y"], box_data["w"], box_data["h"])
                self.upload.boxes[image_path].append({
                    "rect": rect,
                    "label": box_data["label"]
                })

        self.upload.files = data["files"]
        self.upload.classes = data["classes"]
        for c in data["classes"]:
            self.upload.class_list.addItem(c)
        
        self.upload.list_widget.clear()
        
        for f in self.upload.files:
            pixmap = QPixmap(f)
            thumbnail = pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio)
            icon = QIcon(thumbnail)
            item = QListWidgetItem(icon, "")
            item.setData(Qt.ItemDataRole.UserRole, f)
            self.upload.list_widget.addItem(item)
        
        self.upload.list_widget.setCurrentRow(0)
        self.upload.show_image(self.upload.list_widget.item(0))

    def create_menu(self):
        
        self.menu_bar = self.menuBar()
        
        self.file_menu=self.menu_bar.addMenu("File")
        self.file_menu.menuAction().setVisible(False)

        save_action =QAction("Save",self)
        save_action.triggered.connect(self.save_project)
        self.file_menu.addAction(save_action)
        
        load_action =QAction("Load",self)
        load_action.triggered.connect(self.load_project)
        self.file_menu.addAction(load_action)

        self.export_menu=self.menu_bar.addMenu("Export")
        self.export_menu.menuAction().setVisible(False)

        export_action =QAction("Export as YOLO", self)
        export_action.triggered.connect(self.export_yolo)
        self.export_menu.addAction(export_action)



if __name__ =="__main__":
    app = QApplication(sys.argv)
    window=MainWindow()
    window.show()

    sys.exit(app.exec())


