import sys
from PyQt5.QtWidgets import QApplication
from NBS_UI import NBS_UI


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NBS_UI()
    window.show()
    sys.exit(app.exec_())