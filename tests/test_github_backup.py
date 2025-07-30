import sys
import os
import json
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backup import GithubBackup


class TestGithubBackup(unittest.TestCase):
    """
       Test suite for the GithubBackup class.
       Mocks subprocess calls to gh CLI and git commands
       to ensure tests are isolated and do not require
       actual GitHub API interaction or file system changes.
    """

    def setUp(self):
        """
       Set up for each test.
       Initializes a GithubBackup instance with a test-specific path
       and ensures the test backup directory is clean.
       """
        # Define a temporary path for testing backups to avoid interfering with actual backups.
        self.test_backup_path = "Test_GitHub_Backups"
        # Create an instance of GithubBackup using the test path.
        self.github_backup_instance = GithubBackup(self.test_backup_path, self.mock_log)

        # Remove the test backup directory if it exists from a previous run to ensure a clean state.
        if os.path.exists(self.test_backup_path):
            import shutil
            shutil.rmtree(self.test_backup_path)

    def tearDown(self):
        """
        Clean up after each test.
        Removes the test backup directory to ensure test isolation.
       """
        # Remove the test backup directory after each test to clean up.
        if os.path.exists(self.test_backup_path):
            import shutil
            shutil.rmtree(self.test_backup_path)

    def mock_log(self, message):
        pass

    @patch("subprocess.run")
    def test_fetch_repos_success(self, mock_subprocess_run):
        """
        Tests successful fetching of repository URLs.
        Mocks a successful 'gh repo list' command output.
        """
        # Configure the mock subprocess.run to simulate a successful gh repo list command.
        mock_result = MagicMock()
        # Indicate success.
        mock_result.returncode = 0

        # Simulate the JSON output from a successful 'gh repo list --json url'.
        mock_result.stdout = json.dumps([
            {"url": "https://github.com/user/repo1.git"},
            {"url": "https://github.com/user/repo2.git"},
        ])

        # No errors.
        mock_result.stderr = ""

        # Set the return value of the mocked subprocess.run.
        mock_subprocess_run.return_value = mock_result

        # Call the method under test.
        repos = self.github_backup_instance.fetch_repos()

        # Assert that the returned list of repositories matches the expected URLs.
        self.assertEqual(repos, [
            "https://github.com/user/repo1.git",
            "https://github.com/user/repo2.git"
        ])

        # Verify that subprocess.run was called exactly once with the correct arguments.
        mock_subprocess_run.assert_called_once_with(
            ["gh", "repo", "list", "--json", "url", "--limit", "1000"],
            capture_output=True,
            text=True,
        )

    @patch("subprocess.run")
    def test_fetch_repos_cli_errors(self, mock_subprocess_run):
        """
        Tests handling of errors from the GitHub CLI (e.g., gh not found).
        Mocks a failed 'gh repo list' command.
        """
        # Configure the mock subprocess.run to simulate a failed gh repo list command.
        mock_result = MagicMock()
        # Indicate failure.
        mock_result.returncode = 1
        mock_result.stdout = ""
        # Simulate an error message.
        mock_result.stderr = "Error: gh command failed"
        mock_subprocess_run.return_value = mock_result

        # Call the method under test.
        repos = self.github_backup_instance.fetch_repos()
        # Assert that an empty list is returned when the CLI command fails.
        self.assertEqual(repos, [])
        # We're primarily testing the return value (empty list) for this scenario.

    @patch("subprocess.run")
    def test_fetch_repos_json_decode_error(self, mock_subprocess_run):
        """
       Tests handling of invalid JSON output from the GitHub CLI.
       Mocks gh returning malformed JSON.
       """
        # Configure the mock subprocess.run to simulate invalid JSON output.
        mock_result = MagicMock()
        # Command succeeded but output is malformed.
        mock_result.returncode = 0
        # Non-JSON string.
        mock_result.stdout = "This is not valid JSON"
        mock_result.stderr = ""
        mock_subprocess_run.return_value = mock_result

        # Call the method under test.
        repos = self.github_backup_instance.fetch_repos()
        # Assert that an empty list is returned when JSON decoding fails.
        self.assertEqual(repos, [])

    @patch('subprocess.run')
    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_clone_new_repos(self, mock_makedirs, mock_path_exists, mock_subprocess_run):
        """
        Tests the cloning of new repositories that don't exist locally.
        Mocks file system checks and git clone commands.
        """
        # Configure os.path.exists to always return False, simulating non-existent local repos.
        mock_path_exists.return_value = False
        repos_to_clone = [
            "https://github.com/user/new_repo1.git",
            "https://github.com/user/new_repo2.git"
        ]

        # Call the method under test.
        self.github_backup_instance.clone_or_update_repos(repos_to_clone)

        # Verify that the destination directory was created (or checked for existence with exist_ok=True).
        mock_makedirs.assert_called_once_with(self.test_backup_path, exist_ok=True)

        # Assert that 'git clone' was called for each new repository with the correct arguments.
        mock_subprocess_run.assert_any_call(
            ["git", "clone", "https://github.com/user/new_repo1.git", os.path.join(self.test_backup_path, "new_repo1")]
        )
        mock_subprocess_run.assert_any_call(
            ["git", "clone", "https://github.com/user/new_repo2.git", os.path.join(self.test_backup_path, "new_repo2")]
        )
        # Ensure 'git pull' was not called, as these are new clones and not updates.
        # The '...' acts as a wildcard for arguments we do not care about in this specific check.
        self.assertNotIn(["git", "-C", unittest.mock.ANY, "pull"], mock_subprocess_run.call_args_list)

    @patch('subprocess.run')
    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_update_existing_repos(self, mock_makedirs, mock_path_exists, mock_subprocess_run):
        """
        Tests the updating (pulling) of repositories that already exist locally.
        Mocks file system checks and git pull commands.
        """
        # Configure os.path.exists to always return True, simulating existing local repos.
        mock_path_exists.return_value = True
        repos_to_update = [
            "https://github.com/user/existing_repo1.git",
            "https://github.com/user/existing_repo2.git"
        ]

        # Call the method under test.
        self.github_backup_instance.clone_or_update_repos(repos_to_update)

        # Verify that the destination directory was created (or checked for existence)
        mock_makedirs.assert_called_once_with(self.test_backup_path, exist_ok=True)
        # Assert that 'git pull' was called for each existing repository with the correct arguments.
        mock_subprocess_run.assert_any_call(
            ["git", "-C", os.path.join(self.test_backup_path, "existing_repo1"), "pull"]
        )
        mock_subprocess_run.assert_any_call(
            ["git", "-C", os.path.join(self.test_backup_path, "existing_repo2"), "pull"]
        )
        # Ensure 'git clone' was not called, as these are updates and not new clones.
        self.assertNotIn(["git", "clone", unittest.mock.ANY, unittest.mock.ANY], mock_subprocess_run.call_args_list)

    @patch('subprocess.run')
    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_clone_and_update_mixed_repos(self, mock_makedirs, mock_path_exists, mock_subprocess_run):
        """
        Tests the mixed scenario of cloning new and updating existing repositories.
        """

        # Define a side effect for os.path.exists to simulate a mix of existing and new repositories.
        def path_exists_side_effect(path):
            # Returns True if "existing_repo" is in the path, otherwise False.
            if "existing_repo" in path:
                return True  # Simulate existing
            return False  # Simulate new

        mock_path_exists.side_effect = path_exists_side_effect

        repos_mixed = [
            "https://github.com/user/existing_repo.git",
            "https://github.com/user/new_repo.git"
        ]

        # Call the method under test.
        self.github_backup_instance.clone_or_update_repos(repos_mixed)

        mock_makedirs.assert_called_once_with(self.test_backup_path, exist_ok=True)
        # Assert that 'git pull' was called for the existing repository
        mock_subprocess_run.assert_any_call(
            ["git", "-C", os.path.join(self.test_backup_path, "existing_repo"), "pull"]
        )
        # Assert that 'git clone' was called for the new repository
        mock_subprocess_run.assert_any_call(
            ["git", "clone", "https://github.com/user/new_repo.git", os.path.join(self.test_backup_path, "new_repo")]
        )

    def test_set_get_path(self):
        """
        Tests the setter and getter methods for the backup path.
        """
        # Assert that the initial path is correctly retrieved.
        self.assertEqual(self.github_backup_instance.get_path(), self.test_backup_path)
        new_path = "/tmp/new_backups"
        # Set a new path.
        self.github_backup_instance.set_path(new_path)
        # Assert that the new path is correctly retrieved.
        self.assertEqual(self.github_backup_instance.get_path(), new_path)


if __name__ == "__main__":
    unittest.main()
