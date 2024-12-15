import os
import subprocess
import json

DESTINATION_PATH = "GitHub_Backups"

# Function to fetch all repository URLs using GitHub CLI
def fetch_repos():
    # Use gh to list repositories, format it to output clone URLs
    result = subprocess.run(
        [
            "gh",
            "repo",
            "list",
            "--json",
            "url",
            "--limit",
            "1000",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"Error fetching repositories: {result.stderr}")
        return []

    try:
        # Parse the JSON output
        repos = json.loads(result.stdout)
        # Extract the sshUrl from each repository
        repo_urls = [repo["url"] for repo in repos]
        return repo_urls
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        return []


# Function to clone the repositories
def clone_or_update_repos(repos):
    # Create a directory to store all repositories
    os.makedirs(DESTINATION_PATH, exist_ok=True)

    for repo_url in repos:
        # Extract the repository name (from the URL)
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        repo_path = os.path.join(DESTINATION_PATH, repo_name)

        # Clone the repo using subprocess to run the git command
        if os.path.exists(repo_path):
            print(f"Repository {repo_name} exists. Performing git pull...")
            # Change directory to the repo path and pull the latest changes
            subprocess.run(["git", "-C", repo_path, "pull"])
        else:
            print(f"Cloning {repo_name}...")
            # Clone the repo using subprocess to run the git command
            subprocess.run(["git", "clone", repo_url, repo_path])


# Main execution
if __name__ == "__main__":
    repos = fetch_repos()

    if repos:
        clone_or_update_repos(repos)
    else:
        print("No repositories to clone.")
