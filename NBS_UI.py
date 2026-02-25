import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QGridLayout, QLabel, QPushButton,
                             QFileDialog, QVBoxLayout,QHBoxLayout, QCheckBox,QLineEdit,QComboBox,QGroupBox,QMessageBox,QTextEdit)
from PyQt5.QtCore import pyqtSignal,Qt
import os
from MusicData import MusicData
import numpy as np
from datetime import datetime

class DropArea(QWidget):
    fileDropped = pyqtSignal(str)  # Signal to emit the path of the dropped file

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)  # Enable the widget to accept drops
        self.groupBox = QGroupBox("Drop NBS file here")
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.groupBox)
        self.setFixedHeight(200)  # Set a fixed size for the drop area

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()  # Accept the drag event if it contains URLs

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            filepath = urls[0].toLocalFile()  # Assume the first URL is the file path
            self.fileDropped.emit(filepath)  # Emit the file path


class CustomCheckBox(QCheckBox):
    def __init__(self, octave, value, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.octave = octave
        self.value = value
        self.setStyleSheet(self.get_stylesheet())

    def get_stylesheet(self):

        if self.octave < self.value:
            return ("QCheckBox::indicator { width: 15px; height: 15px; }"
                    "QCheckBox::indicator:unchecked { background-color: black; }"
                    "QCheckBox::indicator:checked { background-color: gray; }"
                    )
        elif self.octave == self.value or self.octave == self.value + 1:
            return ("QCheckBox::indicator { width: 15px; height: 15px; }"
                    "QCheckBox::indicator:unchecked { background-color: blue; }"
                    "QCheckBox::indicator:checked { background-color: green; }"
                    )
        else:
            return ("QCheckBox::indicator { width: 15px; height: 15px; }"
                    "QCheckBox::indicator:unchecked { background-color: yellow; }"
                    "QCheckBox::indicator:checked { background-color: orange; }"
                    )


class CheckboxGrid(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):

        self.groupBox = QGroupBox("Instruments by Octave")
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.groupBox)

        # Create a grid layout for checkboxes
        grid_layout = QGridLayout()
        
        self.groupBox.setLayout(grid_layout)


        # Dictionary of instruments with their values
        instruments = {'didgeridoo': -2, 'bass': -2, 'guitar': -1, 'banjo': 0, 'pling': 0, 'iron_xylophone': 0,
                    'bit': 0, 'harp': 0, 'cow_bell': 1, 'flute': 1, 'chime': 2, 'xylophone': 2, 'bell': 2}

        # Create the header row
        grid_layout.addWidget(QLabel('Octaves'), 0, 0, Qt.AlignCenter)
        for col, instrument in enumerate(instruments.keys(), start=1):
            label = QLabel(instrument)
            grid_layout.addWidget(label, 0, col)
            
            
        # Add the rows with checkboxes
        self.checkboxes = []
        for row,octave in enumerate([-3,-2,-1,0,1,2,3,4],start = 1):
            label = QLabel(str(octave))
            grid_layout.addWidget(label, row, 0, Qt.AlignCenter)
            row_checkboxes = []
            for col, (instrument, value) in enumerate(instruments.items(), start=1):
                checkbox = CustomCheckBox(octave, value)
                grid_layout.addWidget(checkbox, row, col, Qt.AlignCenter)
                row_checkboxes.append(checkbox)
            self.checkboxes.append(row_checkboxes)
        
    def get_checkbox_states(self):
        # Initialize an array to hold the state of each checkbox
        states = []
        for row_checkboxes in self.checkboxes:
            row_states = [checkbox.isChecked() for checkbox in row_checkboxes]
            states.append(row_states)
        return np.array(states)


class NBS_UI(QMainWindow):
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

        # Setup drop area
        self.drop_area = DropArea()
        self.drop_area.fileDropped.connect(self.onFileDropped)  # Connect the signal to a slot
        v_layout_0.addWidget(self.drop_area)  # Add the drop area to the layout


        # QGroup for parameters
        param_groupBox = QGroupBox("File parameters")
        v_layout_0.addWidget(param_groupBox)
        param_groupBox_layout = QVBoxLayout()
        param_groupBox.setLayout(param_groupBox_layout)



        # Label to display file name
        
        H_loaded_layout = QHBoxLayout()
        H_loaded_layout.addWidget(QLabel("Input File Name: "))
        self.file_label = QLabel("No file loaded")
        H_loaded_layout.addWidget(self.file_label)
        param_groupBox_layout.addLayout(H_loaded_layout)
        
        # QEdit for save file name
        H_save_layout = QHBoxLayout()
        H_save_layout.addWidget(QLabel("Output File Name: "))
        self.output_file = QLineEdit("")
        H_save_layout.addWidget(self.output_file)
        param_groupBox_layout.addLayout(H_save_layout)
        
        self.output_file.textChanged.connect(self.updateSaveFileName)
        
        
        #For the tempo
        
        self.input_tempo = QLabel("Input Tempo")
        param_groupBox_layout.addWidget(self.input_tempo)
        
        self.fix_tempo = QCheckBox("Adjust Tempo")
        param_groupBox_layout.addWidget(self.fix_tempo)
        
    
        self.choose_tempo = QComboBox()
        H_save_layout = QHBoxLayout()
        H_save_layout.addWidget(QLabel("Chose tempo:"))
        H_save_layout.addWidget(self.choose_tempo)
        param_groupBox_layout.addLayout(H_save_layout)
        
        # Ajouter la grille de checkboxes
        self.checkbox_grid = CheckboxGrid(self)
        v_layout_0.addWidget(self.checkbox_grid)



        # Save button
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_data)
        v_layout_0.addWidget(self.save_btn)

        # Zone de texte pour les logs
        self.text_log = QTextEdit()
        self.text_log.setReadOnly(True)
        self.text_log.setFixedHeight(100) 
        self.text_log.setStyleSheet("font-weight: bold;")
        v_layout_0.addWidget(self.text_log)

    def onFileDropped(self, filepath):
        # Check if the file has the .nbs extension
        if filepath.lower().endswith('.nbs'):
            self.load_file_by_path(filepath)  # Handle the file loading if the extension is correct
        else:
            # Optionally, show a message to the user that the file is not supported
            QMessageBox.warning(self, "Invalid File", "Please drop a '.nbs' file.")

    def load_file_button(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Open File", "", "NBS (*.nbs)", options=options)
        
        self.load_file_by_path(file_name)


    def load_file_by_path(self, path):
        if path:
            name = self.processor.read_file(path)
            name += "_updated"
            self.file_label.setText(name)
            self.output_file.setText(name)
            self.processor.file_name = name
            
            tempo = self.processor.header['tempo']/100
            self.input_tempo.setText(f"Imput tempo : {tempo:.2f}")
            self.update_tempo_box(self.processor.get_tempos())

            self.log_action(path + " has been loaded")




    def save_data(self):
        # Here you can add additional code to save `checkbox_states` to a file or process it further
        self.processor.modify_instrument_data(self.checkbox_grid.get_checkbox_states())

        # tempo change
        
        self.processor.update_tempo(self.choose_tempo.currentIndex())
        
        file_name = self.processor.write_nbs()

        self.log_action(file_name + " has been saved")

        
        
    def updateSaveFileName(self):
        # Récupérer le texte du QLineEdit
        text = self.output_file.text()
        self.processor.file_name = text

        
    def update_tempo_box(self, items, default_index=1): 
        
        self.choose_tempo.clear()  # Clear existing items
        self.choose_tempo.addItems(items)  # Add new items
        if len(items) > default_index:  # Ensure the default index is within the range
            self.choose_tempo.setCurrentIndex(default_index)
        
    def log_action(self, action):
        now = datetime.now().strftime('%d-%m-%Y %H:%M:%S.%f')[:-3]
        log_entry = f"{now} : {action}\n"
        self.text_log.append(log_entry)
