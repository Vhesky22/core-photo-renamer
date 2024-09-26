# main.py
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from main_window import ResponsiveMainWindow

# Set High DPI scaling attribute before creating QApplication
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Create and show the main window
    main_window = ResponsiveMainWindow()
    main_window.show()

    sys.exit(app.exec_())
