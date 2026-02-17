import os
import requests
import base64
import json
import sys

# Load .env manually if it exists, otherwise rely on system env
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(os.path.dirname(script_dir), "backend")
env_path = os.path.join(backend_dir, ".env")

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
sys.path.append(backend_dir)
try:
    from lib.github_app import get_installation_token
except ImportError:
    print("Error: Could not import 'lib.github_app'. Check path.")
    sys.exit(1)

# TARGET REPOSITORY
OWNER = "beam-me"
REPO = "user-code"
TARGET_PATH = "libs/physics/pav_physics.py" # Remote path

def push_file(auth):
    # Determine source file path
    # We want to push the file we created in development/beam-user-code/libs/physics/pav_physics.py
    source_path = os.path.join(os.path.dirname(os.path.dirname(script_dir)), "beam-user-code", "libs", "physics", "pav_physics.py")
    
    if not os.path.exists(source_path):
        print(f"❌ Error: Source file not found at {source_path}")
        return

    print(f"📖 Reading source: {source_path}")
    try:
        with open(source_path, "rb") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    content_b64 = base64.b64encode(content).decode("utf-8")
    
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{TARGET_PATH}"
    headers = {
        "Authorization": f"token {auth['token']}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Check if file exists to get SHA (for update)
    sha = None
    print(f"🔍 Checking if file exists at {url}...")
    try:
        get_resp = requests.get(url, headers=headers)
        if get_resp.status_code == 200:
            sha = get_resp.json().get("sha")
            print(f"   File exists (sha: {sha[:7]}), updating...")
        elif get_resp.status_code == 404:
            print("   File not found, creating new...")
        else:
            print(f"   Unexpected status: {get_resp.status_code}")
    except Exception as e:
        print(f"Error checking file status: {e}")
            
    data = {
        "message": f"feat: Add shared physics library (pav_physics.py)",
        "content": content_b64,
        "branch": "main"
    }
    if sha:
        data["sha"] = sha
        
    # PUT request
    print(f"📤 Pushing content...")
    try:
        resp = requests.put(url, headers=headers, data=json.dumps(data))
        
        if resp.status_code in [200, 201]:
            print(f"✅ SUCCESS! Pushed to https://github.com/{OWNER}/{REPO}/blob/main/{TARGET_PATH}")
        else:
            print(f"❌ FAILED to push: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"Push Error: {e}")

def main():
    print(f"🚀 Starting Push to {OWNER}/{REPO}...")
    
    # 1. Auth (Get GitHub App Installation Token for the user-code repo)
    try:
        auth = get_installation_token(OWNER, REPO)
    except Exception as e:
        print(f"Auth Exception: {e}")
        return

    if isinstance(auth, dict) and "error" in auth:
        print(f"🔥 Auth Failed: {auth['error']}")
        return

    print("🔐 Auth successful.")

    # 2. Push File
    push_file(auth)

if __name__ == "__main__":
    main()
