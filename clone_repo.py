"""
clone_repo.py

This script clones or updates GitLab repositories for a predefined set of groups.
For each group, it fetches all projects via the GitLab API and either:
  - Clones the repository if it does not exist locally.
  - Pulls the latest changes from the default branch (main or master) if it already exists.

Configuration:
  - GITLAB_URL: Base URL of the GitLab instance (no trailing slash).
  - ACCESS_TOKEN: Personal access token for GitLab API authentication.
  - USE_SSH: Set to True to clone via SSH, False for HTTPS.
  - GROUP_CLONE_MAP: Maps GitLab group IDs to local clone directories.

Usage:
  Set ACCESS_TOKEN to a valid GitLab personal access token, then run:
    python clone_repo.py
"""

import subprocess
from pathlib import Path

import requests


# Base URL of the GitLab instance — no trailing slash to avoid double-slash in API paths
GITLAB_URL = "<GIT_URL>"

# GitLab personal access token for API authentication (used for the GitLab API only).
# Replace <ACCESS_TOKEN> with your actual token before running.
# For git clone/pull authentication, configure git credentials separately — see README.
ACCESS_TOKEN = "<ACCESS_TOKEN>"

# Set to True to clone repositories via SSH, False to use HTTPS
USE_SSH = False

# Map GitLab group IDs to their respective local clone directories
GROUP_CLONE_MAP = {}

# Reusable HTTP session — shares a single TCP connection across all API requests
session = requests.Session()
session.headers.update({"PRIVATE-TOKEN": ACCESS_TOKEN})

# Branch names to attempt when pulling, in order of preference
DEFAULT_BRANCHES = ["main", "master"]


def get_all_projects(group_name: str) -> list[dict]:
    """
    Retrieve all projects belonging to a GitLab group.

    Paginates through the GitLab API to collect all projects in the specified
    group. Subgroups are not included.

    Args:
        group_name (str): The GitLab group ID or URL-encoded path.

    Returns:
        list[dict]: A list of project objects as returned by the GitLab API.

    Raises:
        requests.HTTPError: If the API request returns a non-2xx status code.
    """
    projects = []
    # API URL is constant across pages — build it once outside the loop
    url = f"{GITLAB_URL}/api/v4/groups/{group_name}/projects"
    page = 1

    while True:
        params = {
            "per_page": 100,           # Maximum allowed items per page
            "page": page,
            "include_subgroups": False,  # Only fetch direct group projects
        }

        response = session.get(url, params=params)
        response.raise_for_status()  # Raises HTTPError for 4xx/5xx responses

        data = response.json()
        if not data:
            # Empty page means there are no more results
            break

        projects.extend(data)
        page += 1

    return projects


def clone_repo_with_dir(clone_url: str, project_name: str, clone_dir: str) -> None:
    """
    Clone a repository into a specified directory, or pull the latest changes if it exists.

    If the repository directory already exists locally, this function iterates over
    DEFAULT_BRANCHES ('main', then 'master') and pulls from the first branch that
    succeeds. If neither branch succeeds, an error is logged.

    If the repository does not exist locally, it will be cloned fresh.

    Args:
        clone_url (str): The URL to clone the repository from (SSH or HTTPS).
        project_name (str): The repository path/name used as the local folder name.
        clone_dir (str): The local directory into which the repository will be cloned.
    """
    repo_path = Path(clone_dir) / project_name

    if repo_path.exists():
        # Repository already exists locally — pull latest changes instead of re-cloning
        print(f"[PULL] {project_name} already exists in {clone_dir}. Pulling latest {'/'.join(DEFAULT_BRANCHES)}...")
        for branch in DEFAULT_BRANCHES:
            try:
                subprocess.run(
                    ["git", "-C", str(repo_path), "checkout", branch],
                    check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                subprocess.run(
                    ["git", "-C", str(repo_path), "pull", "origin", branch],
                    check=True,
                )
                return  # Pull succeeded — no need to try further branches
            except subprocess.CalledProcessError:
                continue  # Try the next branch

        print(f"[ERROR] Failed to pull latest for {project_name} (no {'/'.join(DEFAULT_BRANCHES)} branch?)")
        return

    # Repository does not exist locally — perform a fresh clone
    print(f"[CLONE] {project_name} into {clone_dir} ...")
    subprocess.run(["git", "clone", clone_url, str(repo_path)], check=True)


def main() -> None:
    """
    Entry point: iterate over all configured groups and clone/update their repositories.

    For each group defined in GROUP_CLONE_MAP:
      1. Ensures the target clone directory exists.
      2. Fetches all projects in the group via the GitLab API.
      3. Clones each project or pulls the latest changes if already cloned.
    """
    for group_name, clone_dir in GROUP_CLONE_MAP.items():
        print(f"[GROUP] Cloning projects for group {group_name} into {clone_dir}")

        # Create the target directory if it doesn't already exist
        Path(clone_dir).mkdir(parents=True, exist_ok=True)

        projects = get_all_projects(group_name)

        for project in projects:
            # Select SSH or HTTPS clone URL based on configuration
            clone_url = project["ssh_url_to_repo"] if USE_SSH else project["http_url_to_repo"]
            project_name = project["path"]

            try:
                clone_repo_with_dir(clone_url, project_name, clone_dir)
            except subprocess.CalledProcessError:
                print(f"[ERROR] Failed to clone {project_name}")


if __name__ == "__main__":
    main()
