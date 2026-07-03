import sys
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QFileDialog, QLabel, QComboBox, QCheckBox,
                             QProgressBar, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from core.MusicData import MusicData, prep_data
from core.customNBT import CustomNBT
from core.StructureGenerator import StructureGenerator

class GeneratorThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, nbs_path, layout_type, export_mode):
        super().__init__()
        self.nbs_path = nbs_path
        self.layout_type = layout_type
        self.export_mode = export_mode

    def run(self):
        try:
            self.progress.emit(10)

            # Load Data
            music = MusicData()
            music.read_file(self.nbs_path)
            self.progress.emit(30)

            if music.data is None or music.data.empty:
                self.error.emit("NBS file contains no note data.")
                return

            # Prepare data
            # Use 20 ticks per second as target speed for NBT
            df_prep = prep_data(music.data, ticks_per_second=20, tick_offset=5)
            self.progress.emit(50)

            # Generate Structure
            nbt_template = CustomNBT()
            generator = StructureGenerator(df_prep, nbt_template, layout_type=self.layout_type)
            generator.generate_blocks()
            self.progress.emit(80)

            # Export
            out_name = os.path.splitext(os.path.basename(self.nbs_path))[0]
            if self.export_mode == "Single Monolithic File":
                out_path = f"output/{out_name}_complete.nbt"
                generator.export_monolithic(out_path)
            else:
                out_dir = f"output/{out_name}_parts"
                os.makedirs(out_dir, exist_ok=True)
                generator.export_multipart(out_dir)
                out_path = out_dir

            self.progress.emit(100)
            self.finished.emit(out_path)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error.emit(str(e))

class NBT_UI(QWidget):
    def __init__(self):
        super().__init__()
        self.nbs_file_path = None
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # File Selection
        file_layout = QHBoxLayout()
        self.lbl_file = QLabel("No NBS file selected.")
        btn_select = QPushButton("Select NBS File")
        btn_select.clicked.connect(self.select_file)
        file_layout.addWidget(self.lbl_file)
        file_layout.addWidget(btn_select)
        layout.addLayout(file_layout)

        # Layout Selection
        layout_select_box = QHBoxLayout()
        layout_select_box.addWidget(QLabel("Select Structure Layout:"))
        self.cb_layout = QComboBox()
        self.cb_layout.addItems(["Layout2 (Compact Serpentine)", "Layout1 (Minecart)"])
        layout_select_box.addWidget(self.cb_layout)
        layout.addLayout(layout_select_box)

        # Generation Mode
        mode_box = QHBoxLayout()
        mode_box.addWidget(QLabel("Generation Mode:"))
        self.cb_mode = QComboBox()
        self.cb_mode.addItems(["Single Monolithic File", "Dynamic Multi-Part (Structure Blocks)"])
        mode_box.addWidget(self.cb_mode)
        layout.addLayout(mode_box)

        # Generate Button & Progress
        self.btn_generate = QPushButton("Generate NBT")
        self.btn_generate.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        self.btn_generate.clicked.connect(self.start_generation)
        layout.addWidget(self.btn_generate)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        layout.addStretch()

    def select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open NBS File", "", "NBS Files (*.nbs)")
        if path:
            self.nbs_file_path = path
            self.lbl_file.setText(os.path.basename(path))

    def start_generation(self):
        if not self.nbs_file_path:
            QMessageBox.warning(self, "Error", "Please select an NBS file first.")
            return

        self.btn_generate.setEnabled(False)
        self.progress_bar.setValue(0)

        layout_choice = self.cb_layout.currentText()
        mode_choice = self.cb_mode.currentText()

        self.thread = GeneratorThread(self.nbs_file_path, layout_choice, mode_choice)
        self.thread.progress.connect(self.update_progress)
        self.thread.finished.connect(self.generation_finished)
        self.thread.error.connect(self.generation_error)
        self.thread.start()

    def update_progress(self, val):
        self.progress_bar.setValue(val)

    def generation_finished(self, path):
        self.btn_generate.setEnabled(True)
        QMessageBox.information(self, "Success", f"Generation completed successfully!\nSaved to: {path}")

    def generation_error(self, err):
        self.btn_generate.setEnabled(True)
        self.progress_bar.setValue(0)
        QMessageBox.critical(self, "Error", f"An error occurred during generation:\n{err}")
