import os
import subprocess
import json
import threading
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFileDialog, QPlainTextEdit, QProgressBar
)
from PySide6.QtCore import Qt, QObject, QThread, Signal

DESTINATION_PATH = "GitHub_Backups"


class GithubBackup:
    def __init__(self, path, log_callback, progress_callback=None):
        self.__path = path
        self.log = log_callback
        self.progress = progress_callback

    def set_path(self, path):
        self.__path = path

    def get_path(self):
        return self.__path

    # Fetch repositories using GitHub CLI
    def fetch_repos(self):
        self.log("Fetching repositories...\n")
        # Show 0% at start of fetch
        if self.progress:
            self.progress(0)

        # Use gh to list repositories, format it to output clone URLs
        result = subprocess.run(
            ["gh", "repo", "list", "--json", "url", "--limit", "1000"],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            self.log(f"Error fetching repositories: {result.stderr}")
            if self.progress:
                self.progress(100)
            return []

        try:
            # Parse the JSON output
            repos = json.loads(result.stdout)
            # Extract the sshUrl from each repository
            urls = [repo["url"] for repo in repos]
            self.log(f"Found {len(urls)} repositories.\n")
            # Show 10% when fetch done
            if self.progress:
                self.progress(10)
            return urls
        except json.JSONDecodeError as e:
            self.log(f"Failed to parse JSON: {e}\n")
            if self.progress:
                self.progress(100)
            return []

    # Clone new repositories or update existing ones
    def clone_or_update_repos(self, repos):
        # Create a directory to store all repositories
        os.makedirs(self.__path, exist_ok=True)
        total = len(repos)
        if total == 0:
            if self.progress:
                self.progress(100)
            return

        # Progress from 10% to 100% during cloning/updating
        for i, repo_url in enumerate(repos, 1):
            # Extract the repository name (from the URL)
            repo_name = repo_url.split("/")[-1].replace(".git", "")
            repo_path = os.path.join(self.__path, repo_name)

            # Clone the repo using subprocess to run the git command
            if os.path.exists(repo_path):
                # Change directory to the repo path and pull the latest changes
                self.log(f"Updating {repo_name}...\n")
                subprocess.run(["git", "-C", repo_path, "pull"])
            else:
                # Clone the repo using subprocess to run the git command
                self.log(f"Cloning {repo_name}...\n")
                subprocess.run(["git", "clone", repo_url, repo_path])

            if self.progress:
                # Map progress i/total from 10%-100%
                percent = 10 + int((i / total) * 90)
                self.progress(percent)

        self.log("Backup completed.\n")
        if self.progress:
            self.progress(100)


class BackupWorker(QObject):
    log_signal = Signal(str)
    progress_signal = Signal(int)
    finished = Signal()

    def __init__(self, path):
        super().__init__()
        self.path = path

    def run(self):
        def log(message):
            self.log_signal.emit(message)

        def progress(value):
            self.progress_signal.emit(value)

        backup = GithubBackup(self.path, log, progress)
        repos = backup.fetch_repos()

        if repos:
            backup.clone_or_update_repos(repos)
        else:
            log("No repositories found.\n")
        self.finished.emit()


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
        self.path_input.setText(DESTINATION_PATH)
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

    def run_backup(self):
        self.update_progress(0)
        path = self.path_input.text().strip()
        if not path:
            self.log("Please specify a valid path.\n")
            return

        github = GithubBackup(path, self.log, self.update_progress)
        repos = github.fetch_repos()
        if repos:
            github.clone_or_update_repos(repos)
        else:
            self.log("No repositories found.\n")
        self.update_progress(100)

    def start_backup(self):
        path = self.path_input.text().strip()
        if not path:
            self.log("Please specify a valid path.\n")
            return

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

        # Start thread.
        self.thread.start()


# Application entry point
if __name__ == "__main__":
    app = QApplication([])
    window = BackupApp()
    window.show()
    app.exec()
