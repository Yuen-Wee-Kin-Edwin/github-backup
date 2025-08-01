# worker.py
from PySide6.QtCore import QObject, Signal
from src.backup import GithubBackup


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
