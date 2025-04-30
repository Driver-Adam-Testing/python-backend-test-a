import os
import shutil
import subprocess
import time

import jwt
import requests

APP_ID = 1212408
INSTALLATION_ID = 65566326
PRIVATE_KEY_PATH = (
    "/Users/ghostmac/Downloads/eric-miller-gh-app.2025-04-29.private-key.pem"
)
REPO_NAME = "eric-driverai/someapp"
BRANCH = "main"
COMMIT_MESSAGE = "Bot: update docs via GitHub App"
NEW_FILES = {"build/docs/example.txt": "Hello from the GitHub API\n"}
REPO_DIR = "/Users/ghostmac/WebstormProjects/DriverAI/someapp"
COMMIT_MESSAGE = "Bot: update docs"
SOURCE_DIR = "/Users/ghostmac/Downloads/driver_docs"
TARGET_DIR = "driver_docs"
# --------------------------


def get_installation_token(app_id, installation_id, private_key_path):
    with open(private_key_path, "rb") as f:
        private_key = f.read()

    payload = {
        "iat": int(time.time()) - 60,
        "exp": int(time.time()) + (10 * 60),
        "iss": app_id,
    }
    jwt_token = jwt.encode(payload, private_key, algorithm="RS256")

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json",
    }
    resp = requests.post(
        f"https://api.github.com/app/installations/{installation_id}/access_tokens",
        headers=headers,
    )
    resp.raise_for_status()
    return resp.json()["token"]


def run(cmd, cwd=None, check=True):
    print(f"> {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd)
    return result


def sync_directory(src, dest):
    if os.path.exists(dest):
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    print(f"✅ Synced `{src}` to `{dest}`")


def main():
    token = get_installation_token(APP_ID, INSTALLATION_ID, PRIVATE_KEY_PATH)
    remote_url = f"https://x-access-token:{token}@github.com/{REPO_NAME}.git"

    # Setup repo if not cloned
    if not os.path.exists(REPO_DIR):
        run(f"git clone {remote_url} {REPO_DIR}")

    # Checkout branch and make changes
    run(f"git checkout -B {BRANCH}", cwd=REPO_DIR)
    # Copy from dri/ into build/docs/
    src_path = os.path.abspath(SOURCE_DIR)
    dst_path = os.path.join(REPO_DIR, TARGET_DIR)
    sync_directory(src_path, dst_path)

    # Commit and push
    run('git config user.name "docs-bot"', cwd=REPO_DIR)
    run('git config user.email "bot@example.com"', cwd=REPO_DIR)
    run("git add driver_docs", cwd=REPO_DIR)

    # Only commit if changes
    diff = run("git diff --cached --quiet", cwd=REPO_DIR, check=False)
    if diff.returncode == 0:
        print("✅ No changes to commit.")
        return

    run(f'git commit -m "{COMMIT_MESSAGE}"', cwd=REPO_DIR)
    run(f"git push {remote_url} {BRANCH}", cwd=REPO_DIR)
    print(f"✅ Pushed changes to `{BRANCH}`")


if __name__ == "__main__":
    main()
