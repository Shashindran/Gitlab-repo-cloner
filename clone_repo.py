import os
import requests
import subprocess

GITLAB_URL = "<GITLAB_URL"
GROUP_NAME = "<GITLAB_GROUPNAME_OR_ID>"
ACCESS_TOKEN = "<GITLAB_ACCESS_TOKEN>"
USE_SSH = False
CLONE_DIR = "<CLONE_DIR>"

headers = {
    "PRIVATE-TOKEN": ACCESS_TOKEN
}

def get_all_projects(group_name):
    projects = []
    page = 1

    while True:
        url = f"{GITLAB_URL}/api/v4/groups/{group_name}/projects"
        params = {
            "per_page": 100,
            "page": page,
            "include_subgroups": False
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch projects: {response.text}")

        data = response.json()
        if not data:
            break

        projects.extend(data)
        page += 1

    return projects

def clone_repo(clone_url, project_name):
    repo_path = os.path.join(CLONE_DIR, project_name)
    if os.path.exists(repo_path):
        print(f"[SKIP] {project_name} already cloned.")

    print(f"[CLONE] {project_name} ...")
    subprocess.run(["git", "clone", clone_url, repo_path], check=True)

def main():
    os.makedirs(CLONE_DIR, exist_ok=True)
    projects = get_all_projects(GROUP_NAME)

    for project in projects:
        clone_url = project["ssh_url_to_repo"] if USE_SSH else project["http_url_to_repo"]
        project_name = project["path"]

        try:
            clone_repo(clone_url, project_name)
        except subprocess.CalledProcessError:
            print(f"[ERROR] Failed to clone {project_name}")

if __name__ == "__main__":
    main()
