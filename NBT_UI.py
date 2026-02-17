import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QGridLayout, QLabel, QPushButton,
                             QFileDialog, QVBoxLayout,QHBoxLayout, QCheckBox,QLineEdit,QComboBox,QGroupBox,QMessageBox,QTextEdit)
from PyQt5.QtCore import pyqtSignal,Qt
import os
from MusicData import MusicData
import numpy as np
from datetime import datetime


class NBT_UI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.processor = MusicData()
        
        self.setWindowTitle("Noteblock song program")
        
        # Central widget
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        # Vertical layout to hold the entire UI
        v_layout_0 = QVBoxLayout()
        central_widget.setLayout(v_layout_0)

        # Button to load a file
        self.load_file_btn = QPushButton("Load NBS File")
        self.load_file_btn.clicked.connect(self.load_file_button)
        v_layout_0.addWidget(self.load_file_btn)

    def load_file_button(self):
        pass
