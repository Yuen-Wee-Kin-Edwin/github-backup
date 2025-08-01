# gui.py
import os.path

from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFileDialog, QPlainTextEdit, QProgressBar
)
from PySide6.QtCore import Qt, QThread
from src.worker import BackupWorker

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DESTINATION_PATH = os.path.join(PROJECT_ROOT, "GitHub_Backups")


# GUI class
class BackupApp(QWidget):
    def __init__(self, /):
        super().__init__()
        self.setWindowTitle("GitHub Backup Tool")
        self.setMinimumWidth(500)
        self.init_ui()

    def init_ui(self):
        # Layouts.
        main_layout = QVBoxLayout()
        path_layout = QHBoxLayout()

        # Backup path label + entry + browse.
        self.path_label = QLabel("Backup folder:")
        self.path_input = QLineEdit()

        # Clean display of just the folder name, with full path as tooltip
        full_path = DESTINATION_PATH
        short_name = os.path.basename(full_path)

        self.path_input.setText(short_name)
        self.path_input.setToolTip(full_path)
        self.path_input.setReadOnly(True)
        self.path_input.setCursorPosition(0)

        # Save original mousePressEvent.
        original_mouse_press = self.path_input.mousePressEvent

        def new_mouse_press(event):
            self.path_input.setText(full_path)
            self.path_input.setCursorPosition(0)
            # Call original handler for normal behaviour.
            original_mouse_press(event)

        self.path_input.mousePressEvent = new_mouse_press

        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_folder)

        path_layout.addWidget(self.path_label)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(self.browse_button)

        # Output log area.
        self.output_box = QPlainTextEdit()
        self.output_box.setReadOnly(True)

        # Progress bar.
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)

        # Start button.
        self.start_button = QPushButton("Start Backup")
        self.start_button.clicked.connect(self.start_backup)

        # Assemble layout.
        main_layout.addLayout(path_layout)
        main_layout.addWidget(self.output_box)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.start_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(main_layout)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Backup Folder")
        if folder:
            self.path_input.setText(folder)

    def log(self, message):
        self.output_box.appendPlainText(message)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def start_backup(self):
        path = self.path_input.text().strip()
        if not path:
            self.log("Please specify a valid path.\n")
            return

        # Disable UI during backup.
        self.toggle_ui(False)

        # Create thread and worker.
        self.thread = QThread()
        self.worker = BackupWorker(path)
        self.worker.moveToThread(self.thread)

        # Connect signals.
        self.thread.started.connect(self.worker.run)
        self.worker.log_signal.connect(self.log)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        # Re-enable UI after backup completes
        self.thread.finished.connect(lambda: self.toggle_ui(True))

        # Start thread.
        self.thread.start()

    def toggle_ui(self, enabled: bool):
        # Enable or disable UI components during backup.
        self.path_input.setEnabled(enabled)
        self.browse_button.setEnabled(enabled)
        self.start_button.setEnabled(enabled)
