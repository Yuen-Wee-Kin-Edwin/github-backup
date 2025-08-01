# main.py
from PySide6.QtWidgets import QApplication
from src.gui import BackupApp

# Application entry point
if __name__ == "__main__":
    app = QApplication([])
    window = BackupApp()
    window.show()
    app.exec()
