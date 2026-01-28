import requests
import base64
import json
from lib.github_app import get_installation_token

class GitHubTool:
    """
    Tool for interacting with the User Code Repository.
    """
    def __init__(self):
        self.owner = "beam-me"
        self.repo = "user-code"

    def _get_headers(self):
        auth = get_installation_token(self.owner, self.repo)
        if "error" in auth:
            raise Exception(f"GitHub Auth Failed: {auth['error']}")
        return {
            "Authorization": f"token {auth['token']}",
            "Accept": "application/vnd.github.v3+json"
        }

    def fetch_code(self, file_path: str) -> str:
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/contents/{file_path}"
        headers = self._get_headers()
        
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            content_b64 = resp.json().get("content", "")
            return base64.b64decode(content_b64).decode("utf-8")
        else:
            raise Exception(f"Failed to fetch {file_path}: {resp.status_code}")

    def push_code(self, file_path: str, content: str, message: str) -> str:
        """
        Creates or Updates a file in the repo. Returns the HTML URL.
        """
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/contents/{file_path}"
        headers = self._get_headers()
        
        # Check if file exists to get SHA
        sha = None
        get_resp = requests.get(url, headers=headers)
        if get_resp.status_code == 200:
            sha = get_resp.json().get("sha")

        data = {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
            "branch": "main"
        }
        if sha:
            data["sha"] = sha

        put_resp = requests.put(url, headers=headers, data=json.dumps(data))
        if put_resp.status_code in [200, 201]:
            return put_resp.json().get("content", {}).get("html_url")
        else:
            raise Exception(f"Failed to push {file_path}: {put_resp.text}")
