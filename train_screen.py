from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import os
import re
import subprocess
import tempfile
import time


class TrainScreen(QWidget):
    def __init__(self,upload_screen,switch_to_upload,export_callback):
        super().__init__()
        self.upload_screen = upload_screen
        self.switch_to_upload =switch_to_upload

        self.data_path=None
        self.export_callback = export_callback

        self.back_to_upload_button = QPushButton("Back")
        self.back_to_upload_button.clicked.connect(self.switch_to_upload)
        self.back_to_upload_button.setFixedWidth(55)

        self.left_layout = QVBoxLayout()
        self.left_layout.setContentsMargins(8, 8, 8, 8)
        self.left_layout.setSpacing(3)

        self.left_layout.addWidget(self.back_to_upload_button)

        left_widget = QWidget()
        left_widget.setObjectName("trainLeftPanel")
        left_widget.setFixedWidth(200)
        left_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        left_widget.setLayout(self.left_layout)

        self.data_button =QPushButton("Select your data")
        self.data_menu = QMenu()
        self.data_button.setMenu(self.data_menu)

        self.left_layout.addWidget(self.data_button)
        
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

        self.width_label=QLabel("Image Width:")
        self.width_spin=QSpinBox()
        self.width_spin.setRange(32,1280)
        self.width_spin.setValue(640)

        self.height_label=QLabel("Image Height:")
        self.height_spin=QSpinBox()
        self.height_spin.setRange(32,1280)
        self.height_spin.setValue(640)

        self.left_layout.addWidget(self.width_label)
        self.left_layout.addWidget(self.width_spin)
        self.left_layout.addWidget(self.height_label)
        self.left_layout.addWidget(self.height_spin)


        self.lr_label = QLabel("Learning Rate : ")
        self.lr_spin = QDoubleSpinBox()
        self.lr_spin.setRange(0.0001, 0.1)
        self.lr_spin.setValue(0.01)
        self.lr_spin.setSingleStep(0.001)
        self.lr_spin.setDecimals(4)
        self.left_layout.addWidget(self.lr_label)
        self.left_layout.addWidget(self.lr_spin)

        self.aug_label=QLabel("Augmentation:")
        self.cb_rotation = QCheckBox("Rotation")
        self.cb_flipud = QCheckBox("Vertical Flip")
        self.cb_fliplr = QCheckBox("Horizontal Flip")
        self.cb_hsv = QCheckBox("Lightning Variation")
        self.cb_scale = QCheckBox("Scaling")
        self.cb_translate = QCheckBox("Translation")

        self.left_layout.addWidget(self.aug_label)
        self.left_layout.addWidget(self.cb_rotation)
        self.left_layout.addWidget(self.cb_flipud)
        self.left_layout.addWidget(self.cb_fliplr)
        self.left_layout.addWidget(self.cb_hsv)
        self.left_layout.addWidget(self.cb_scale)
        self.left_layout.addWidget(self.cb_translate)
        
        self.model_label.setObjectName("trainLabel")
        self.epoch_label.setObjectName("trainLabel")
        self.batch_label.setObjectName("trainLabel")
        self.width_label.setObjectName("trainLabel")
        self.height_label.setObjectName("trainLabel")
        self.lr_label.setObjectName("trainLabel")
        self.aug_label.setObjectName("sectionLabel")



        self.start_button=QPushButton("Start training")
        self.start_button.clicked.connect(self.start_training)
        self.left_layout.addWidget(self.start_button)

        self.open_results_button = QPushButton("📂 Open Results")
        self.open_results_button.clicked.connect(self.open_results)

        self.left_layout.addWidget(self.open_results_button)
        self.open_results_button.setVisible(False)


        self.right_layout=QVBoxLayout()

        self.action_annotated = self.data_menu.addAction("Use your annotated images")
        self.action_folder = self.data_menu.addAction("Select from folder")

        self.action_annotated.triggered.connect(self.use_annotated_data)
        self.action_folder.triggered.connect(self.select_folder)
 
        self.log_area=QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setPlaceholderText("Training logs will appear here...")
        self.right_layout.addWidget(self.log_area)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.right_layout.addWidget(self.progress_bar)

        self.time_label=QLabel("")
        self.right_layout.addWidget(self.time_label)


        self.main_train_layout =QHBoxLayout()
        self.main_train_layout.addWidget(left_widget)
        self.main_train_layout.addLayout(self.right_layout)
        

        self.setLayout(self.main_train_layout)

    def use_annotated_data(self):
        boxes = self.upload_screen.boxes
        has_annotations = any(boxes.values()) if boxes else False
        if not has_annotations:
            QMessageBox.warning(self, "Warning", "No annotated images found!")
            return
        
        temp_dir = tempfile.mkdtemp()
        self.export_callback(temp_dir)
        self.temp_data_path = temp_dir
        self.annotated_selected = True
        self.data_button.setText("✅ Annotated images")
        self.log_area.append("Using annotated images...")

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self , "Select data folder")

        if folder :
            self.data_path = folder
            self.log_area.append(f"Selected folder: {folder}")
            self.data_button.setText(f"✅ {os.path.basename(folder)}")

    def start_training(self):
        
        if self.data_path is None and not hasattr(self, 'temp_data_path') and not getattr(self, 'annotated_selected', False):
            QMessageBox.warning(self, "Warning", "Please select your data first!")
            return
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
            if not os.path.exists(os.path.join(data, "data.yaml")):
                QMessageBox.warning(self, "Warning", "Selected folder does not contain data.yaml!")
                return

        save_folder = QFileDialog.getExistingDirectory(self, "Select folder to save results")
        if not save_folder:
            return
            
        model = self.combo_box.currentText()
        epochs = self.epoch_spin.value()
        batch = self.batch_spin.value()
        width=self.width_spin.value()
        height=self.height_spin.value()
        yaml_path=os.path.join(data , "data.yaml")
        lr=self.lr_spin.value()
        degrees = 45.0 if self.cb_rotation.isChecked() else 0.0
        flipud = 0.5 if self.cb_flipud.isChecked() else 0.0
        fliplr = 0.5 if self.cb_fliplr.isChecked() else 0.0
        hsv = 0.5 if self.cb_hsv.isChecked() else 0.0
        scale = 0.5 if self.cb_scale.isChecked() else 0.0
        translate = 0.1 if self.cb_translate.isChecked() else 0.0

        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self.handle_output)
        self.process.readyReadStandardError.connect(self.handle_output)
        self.process.start("yolo",
                           ["train",
                            f"model={model}.pt",
                            f"data={yaml_path}",
                            f"epochs={epochs}",
                            f"batch={batch}",
                            f"imgsz={width},{height}",
                            f"lr0={lr}",
                            f"degrees={degrees}",
                            f"flipud={flipud}",
                            f"fliplr={fliplr}",
                            f"hsv_h={hsv}",
                            f"hsv_s={hsv}",
                            f"hsv_v={hsv}",
                            f"scale={scale}",
                            f"translate={translate}",
                            f"project={save_folder}",
                            f"name=results",
                        ])
        self.start_button.setEnabled(False)
        self.combo_box.setEnabled(False)
        self.epoch_spin.setEnabled(False)
        self.batch_spin.setEnabled(False)
        self.width_spin.setEnabled(False)
        self.height_spin.setEnabled(False)
        self.lr_spin.setEnabled(False)
        self.cb_rotation.setEnabled(False)
        self.cb_flipud.setEnabled(False)
        self.cb_fliplr.setEnabled(False)
        self.cb_hsv.setEnabled(False)
        self.cb_scale.setEnabled(False)
        self.cb_translate.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.epoch_start_time = time.time()
        self.last_epoch=0
        
        self.log_area.append("Starting training...")
        if not self.process.waitForStarted(3000):
            self.log_area.append("Error: Could not start yolo.")
        self.process.finished.connect(self.on_training_finished)

    
    def handle_output(self):
        output = self.process.readAllStandardOutput().data().decode()
        error = self.process.readAllStandardError().data().decode()
        
        if output:
            clean = re.sub(r'\x1b\[[0-9;]*m', '', output) 
            clean = re.sub(r'\[K', '', clean)              
            clean = clean.strip()
            if clean:
                self.log_area.append(clean)
            match = re.search(r'(\d+)/(\d+)', clean)
            if match:
                current = int(match.group(1))
                total = int(match.group(2))
                self.progress_bar.setMaximum(total)
                self.progress_bar.setValue(current)
                
                if current != self.last_epoch:
                    elapsed = time.time() - self.epoch_start_time
                    remaining_epochs = total - current
                    estimated = elapsed / current * remaining_epochs
                    minutes = int(estimated // 60)
                    seconds = int(estimated % 60)
                    self.time_label.setText(f"⏱ Estimated time remaining: {minutes}m {seconds}s")
                self.last_epoch = current
        if error:
            clean = re.sub(r'\x1b\[[0-9;]*m', '', error)
            clean = re.sub(r'\[K', '', clean)
            clean = clean.strip()
            if clean:
                self.log_area.append(clean)
        
    def on_training_finished(self):
        self.log_area.append("Training completed ! ✅ ")
        self.start_button.setEnabled(True)
        self.combo_box.setEnabled(True)
        self.epoch_spin.setEnabled(True)
        self.batch_spin.setEnabled(True)
        self.width_spin.setEnabled(True)
        self.height_spin.setEnabled(True)
        self.lr_spin.setEnabled(True)
        self.cb_rotation.setEnabled(True)
        self.cb_flipud.setEnabled(True)
        self.cb_fliplr.setEnabled(True)
        self.cb_hsv.setEnabled(True)
        self.cb_scale.setEnabled(True)
        self.cb_translate.setEnabled(True)
        self.open_results_button.setVisible(True)

    def open_results(self):
        path = getattr(self, 'results_path', os.path.join('runs', 'detect'))
        subprocess.Popen(f'explorer "{path}"')
  