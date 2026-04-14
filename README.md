# Gitlab-repo-cloner

A Python script that clones or updates all repositories within one or more GitLab groups. For each configured group it will:
- **Clone** the repository if it does not yet exist locally.
- **Pull** the latest changes (tries `main`, then `master`) if it already exists.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.9+ | `python3 --version` |
| `git` | `git --version` |
| `requests` library | `pip install requests` |
| GitLab Personal Access Token (PAT) | Scopes: `read_api`, `read_repository` |

---

## 1. Generate a GitLab Personal Access Token

1. Log in to your GitLab instance.
2. Go to **User Settings → Access Tokens** (or `-/profile/personal_access_tokens`).
3. Create a token with the following scopes:
   - `read_api` — needed to list group projects via the API.
   - `read_repository` — needed to clone/pull repositories.
4. Copy the generated token (it is shown only once).

---

## 2. Configure git credentials (HTTPS authentication)

The script uses the token only for the GitLab API. Git clone/pull authentication is handled by git's own credential system — **the token is never embedded in a URL**.

Choose one of the options below.

### Option A — `~/.netrc` (recommended)

Add the following line to `~/.netrc` (create the file if it does not exist):

```
machine <your-gitlab-hostname> login oauth2 password <YOUR_ACCESS_TOKEN>
```

Example:
```
machine mygithub.com login oauth2 password glpat-xxxxxxxxxxxxxxxxxxxx
```

Then restrict the file permissions:
```bash
chmod 600 ~/.netrc
```

Git reads `~/.netrc` automatically for HTTPS authentication — no further configuration required.

### Option B — git credential store

```bash
git config --global credential.helper store
```

Then perform a one-time manual clone or fetch and enter your credentials when prompted:
- **Username:** `oauth2`
- **Password:** `<YOUR_ACCESS_TOKEN>`

Git stores them in `~/.git-credentials` and reuses them for all subsequent operations.

### Option C — SSH (skip credential setup entirely)

Generate an SSH key pair and add the public key to **GitLab → User Settings → SSH Keys**, then set `USE_SSH = True` in `clone_repo.py`. No token-in-URL or credential helper needed.

---

## 3. Configure the script

Open `clone_repo.py` and update the following constants near the top of the file:

```python
# Base URL of your GitLab instance — no trailing slash
GITLAB_URL = "mygithub.com"

# Your GitLab Personal Access Token (used for the API only)
ACCESS_TOKEN = "<YOUR_ACCESS_TOKEN>"

# True = clone via SSH, False = clone via HTTPS
USE_SSH = False

# Map each GitLab group ID to the local directory it should be cloned into. The target folder can be anything.
GROUP_CLONE_MAP = {
    "1234": "/target/folder/1",
    "4567": "/target/folder/2",
}
```

To find a **group ID**: open the group in GitLab → the ID is shown below the group name on the group overview page.

---

## 4. Run the script

```bash
python3 clone_repo.py
```

Expected output:
```
[GROUP] Cloning projects for group 567 into /target/folder/1/
[CLONE] my-service into /home/youruser/development/allianz/cloud-first/ ...
[PULL]  other-service already exists. Pulling latest main/master...
[ERROR] Failed to clone broken-repo
```

---

## Security notes

- **Do not commit `clone_repo.py` with a real token in `ACCESS_TOKEN`.**  
  Add it to `.gitignore`, use an environment variable, or replace the value before each run.
- **`~/.netrc` and `~/.git-credentials` contain sensitive data** — ensure they are readable only by your user (`chmod 600`).
- The token is transmitted over HTTPS to the GitLab API and to git remotes but is never written into repository files or URLs by this script.
