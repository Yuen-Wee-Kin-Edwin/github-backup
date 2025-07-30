import os
import subprocess
import json
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk

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


# GUI class
class BackupApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub Backup Tool")

        # Backup folder input
        tk.Label(root, text="Backup folder:").grid(row=0, column=0, sticky="w", padx=5, pady=5)

        self.path_var = tk.StringVar(value="GitHub_Backups")
        self.path_entry = tk.Entry(root, textvariable=self.path_var, width=50)
        self.path_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Button(root, text="Browse", command=self.browse_folder).grid(row=0, column=2, padx=5, pady=5)

        # Output log area
        self.output_box = scrolledtext.ScrolledText(root, width=80, height=25)
        self.output_box.grid(row=1, column=0, columnspan=3, padx=10, pady=10)

        self.progress_bar = ttk.Progressbar(root, orient="horizontal", length=600, mode="determinate")
        self.progress_bar.grid(row=2, column=0, columnspan=3, pady=5)

        # Start button
        tk.Button(root, text="Start Backup", command=self.start_backup).grid(row=3, column=1, pady=5)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.path_var.set(folder)

    def log(self, message):
        self.output_box.insert(tk.END, message)
        self.output_box.see(tk.END)

    def update_progress(self, value):
        self.progress_bar["value"] = value
        self.root.update_idletasks()

    def run_backup(self):
        self.progress_bar["value"] = 0
        path = self.path_var.get().strip()
        if not path:
            self.log("Please specify a valid path.\n")
            return

        github = GithubBackup(path, self.log, self.update_progress)
        repos = github.fetch_repos()
        if repos:
            github.clone_or_update_repos(repos)
        else:
            self.log("No repositories found.\n")
        self.progress_bar["value"] = 100

    def start_backup(self):
        threading.Thread(target=self.run_backup, daemon=True).start()


# Application entry point
if __name__ == "__main__":
    root = tk.Tk()
    app = BackupApp(root)
    root.mainloop()
