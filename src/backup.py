import json
import os
import subprocess


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
