from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import os


class TrainScreen(QWidget):
    def __init__(self,upload_screen,switch_to_upload):
        super().__init__()
        self.upload_screen = upload_screen
        self.switch_to_upload =switch_to_upload

        self.data_path=None

        self.back_to_upload_button = QPushButton("<-")
        self.back_to_upload_button.clicked.connect(self.switch_to_upload)
        self.back_to_upload_button.setFixedWidth(40)

        self.left_layout = QVBoxLayout()

        self.left_layout.addWidget(self.back_to_upload_button)
        
        self.model_label = QLabel("Model:")
        self.combo_box = QComboBox()
        self.combo_box.addItems(["yolov8n", "yolov8s", "yolov8m"])
        self.combo_box.setPlaceholderText("Choose your model")
        self.combo_box.setCurrentIndex(-1)
        self.left_layout.addWidget(self.model_label)
        self.left_layout.addWidget(self.combo_box)

        self.epoch_label=QLabel("Epochs:")
        self.epoch_spin = QSpinBox()
        self.epoch_spin.setRange(1,1000)
        self.epoch_spin.setValue(50)
        self.left_layout.addWidget(self.epoch_label)
        self.left_layout.addWidget(self.epoch_spin)

        self.batch_label =QLabel("Batch size:")
        self.batch_spin = QSpinBox()
        self.batch_spin.setRange(1,128)
        self.batch_spin.setValue(8)
        self.left_layout.addWidget(self.batch_label)
        self.left_layout.addWidget(self.batch_spin)

        self.imagesize_label =QLabel("Image size:")
        self.imagesize_spin = QSpinBox()
        self.imagesize_spin.setRange(32,1280)
        self.imagesize_spin.setValue(640)
        self.left_layout.addWidget(self.imagesize_label)
        self.left_layout.addWidget(self.imagesize_spin)

        self.start_button=QPushButton("Start training")
        self.start_button.clicked.connect(self.start_training)
        self.left_layout.addWidget(self.start_button)


        self.left_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.right_layout=QVBoxLayout()

        self.data_button =QPushButton("Select your data")
        self.data_menu = QMenu()
        

        self.action_annotated = self.data_menu.addAction("Use your annotated images")
        self.action_folder = self.data_menu.addAction("Select from folder")

        self.action_annotated.triggered.connect(self.use_annotated_data)
        self.action_folder.triggered.connect(self.select_folder)
        self.data_button.setMenu(self.data_menu)

        self.right_layout.addWidget(self.data_button)
        self.log_area=QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setPlaceholderText("Training logs will appear here...")
        self.right_layout.addWidget(self.log_area)


        self.main_train_layout =QHBoxLayout()
        self.main_train_layout.addLayout(self.left_layout)
        self.main_train_layout.addLayout(self.right_layout)

        self.setLayout(self.main_train_layout)

    def use_annotated_data(self):
        self.data_path = None  
        self.log_area.append("Using annotated images...")

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self , "Select data folder")

        if folder :
            self.data_path = folder
            self.log_area.append(f"Selected folder: {folder}")

    def start_training(self):
        if self.combo_box.currentIndex() == -1:
            QMessageBox.warning(self,"Warning", "Please select a model ! ")
            return
    
        if self.data_path is None:
            if not hasattr(self, 'temp_data_path'):
                QMessageBox.warning(self, "Warning", "No annotated images found!")
                return
            data = self.temp_data_path
        else:
            data = self.data_path
            
        model = self.combo_box.currentText()
        epochs = self.epoch_spin.value()
        batch = self.batch_spin.value()
        imgsz= self.imagesize_spin.value()
        yaml_path=os.path.join(data , "data.yaml")

        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self.handle_output)
        self.process.readyReadStandardError.connect(self.handle_output)
        self.process.finished.connect(lambda: self.log_area.append("✅ Training complete!"))
        self.process.start("yolo",
                           ["train",
                            f"model={model}.pt",
                            f"data={yaml_path}",
                            f"epochs={epochs}",
                            f"batch={batch}",
                            f"imgsz={imgsz}"
                        ])
        self.log_area.append("Starting training...")
        if not self.process.waitForStarted(3000):
            self.log_area.append("Error: Could not start yolo.")
    
    def handle_output(self):
        output = self.process.readAllStandardOutput().data().decode()
        error = self.process.readAllStandardError().data().decode()

        if output : 
            self.log_area.append(output)
        if error : 
            self.log_area.append(error)

  