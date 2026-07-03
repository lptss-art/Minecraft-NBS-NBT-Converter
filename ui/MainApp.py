from PyQt5.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget
from ui.NBS_UI import NBS_UI
from ui.NBT_UI import NBT_UI

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NoteBlock Studio to NBT Generator")
        self.resize(800, 600)

        # Main widget and layout
        main_widget = QWidget()
        layout = QVBoxLayout()
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

        # Tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # NBS Tab (Instrument & Tempo)
        self.nbs_tab = NBS_UI()
        self.tabs.addTab(self.nbs_tab, "1. Pre-process NBS (Instruments & Tempo)")

        # NBT Tab (Layout & Generation)
        self.nbt_tab = NBT_UI()
        self.tabs.addTab(self.nbt_tab, "2. Generate NBT Structure")
