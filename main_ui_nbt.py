import sys
from PyQt5.QtWidgets import QApplication
from NBT_UI import NBT_UI


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NBT_UI()
    window.show()
    sys.exit(app.exec_())