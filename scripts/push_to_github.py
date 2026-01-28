import os
import requests
import base64
import json
import sys

# Load .env manually
env_path = os.path.join(os.getcwd(), "backend", ".env")
if os.path.exists(env_path):
    print(f"Loading env from {env_path}")
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip().strip('"').strip("'")

# Add backend to path to import lib
sys.path.append(os.path.join(os.getcwd(), "backend"))
from lib.github_app import get_installation_token

OWNER = "beam-me"
REPO = "core"
ROOT_DIR = "."

IGNORE_DIRS = {
    "node_modules", ".git", ".vercel", "__pycache__", "venv", ".venv", 
    "dist", "coverage", ".idea", ".vscode"
}
IGNORE_FILES = {
    ".DS_Store", ".env", "push_to_github.py", "yarn.lock", "package-lock.json"
}

def push_file(file_path, relative_path, headers):
    try:
        with open(file_path, "rb") as f:
            content = f.read()
            
        content_b64 = base64.b64encode(content).decode("utf-8")
        
        url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{relative_path}"
        
        # Check if file exists to get SHA (for update)
        sha = None
        get_resp = requests.get(url, headers=headers)
        if get_resp.status_code == 200:
            sha = get_resp.json().get("sha")
            
        data = {
            "message": f"update: {relative_path}",
            "content": content_b64,
            "branch": "main"
        }
        if sha:
            data["sha"] = sha
            
        # PUT request
        resp = requests.put(url, headers=headers, data=json.dumps(data))
        
        if resp.status_code in [200, 201]:
            print(f"✅ Pushed: {relative_path}")
        else:
            print(f"❌ Failed to push {relative_path}: {resp.status_code} {resp.text}")
            
    except Exception as e:
        print(f"⚠️ Error pushing {relative_path}: {e}")

def main():
    print(f"🚀 Starting Push to {OWNER}/{REPO}...")
    
    # 1. Auth
    auth = get_installation_token(OWNER, REPO)
    if "error" in auth:
        print(f"🔥 Auth Failed: {auth['error']}")
        return

    headers = {
        "Authorization": f"token {auth['token']}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # 2. Walk and Push
    count = 0
    for root, dirs, files in os.walk(ROOT_DIR):
        # Filter directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            if file in IGNORE_FILES:
                continue
            if file.endswith(".pyc"):
                continue
                
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, ROOT_DIR)
            
            # Skip the script itself if it's in the list
            if "scripts/" in rel_path and "push_to_github" in rel_path:
                continue

            # Push
            push_file(full_path, rel_path, headers)
            count += 1
            
    print(f"✨ Complete! Pushed {count} files.")

if __name__ == "__main__":
    main()
