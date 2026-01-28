import os
import time
import base64
import jwt
import requests
from typing import Optional

def get_jwt(app_id: str, private_key_pem: str) -> str:
    """Generate a JWT for GitHub App authentication."""
    now = int(time.time())
    payload = {
        "iat": now - 60,
        "exp": now + (10 * 60),
        "iss": app_id
    }
    return jwt.encode(payload, private_key_pem, algorithm="RS256")

def get_installation_token(owner: str, repo: str) -> dict:
    """
    Exchanges the Private Key for an Installation Access Token 
    scoped to the specific repository.
    """
    app_id = os.environ.get("GITHUB_APP_ID")
    key_b64 = os.environ.get("GITHUB_PRIVATE_KEY_B64")
    
    if not app_id:
        return {"error": "Missing GITHUB_APP_ID environment variable"}
    if not key_b64:
        return {"error": "Missing GITHUB_PRIVATE_KEY_B64 environment variable"}

    try:
        # Decode key
        private_key = base64.b64decode(key_b64).decode('utf-8')
        
        # 1. Generate JWT
        encoded_jwt = get_jwt(app_id, private_key)
        headers = {
            "Authorization": f"Bearer {encoded_jwt}",
            "Accept": "application/vnd.github.v3+json"
        }

        # 2. Get Installation ID for the repo
        # This automatically handles finding the correct installation
        url = f"https://api.github.com/repos/{owner}/{repo}/installation"
        resp = requests.get(url, headers=headers)
        
        if resp.status_code != 200:
            return {
                "error": f"Could not find installation for {owner}/{repo}", 
                "details": resp.json()
            }
        
        installation_id = resp.json()["id"]

        # 3. Get Access Token
        token_url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
        token_resp = requests.post(token_url, headers=headers)
        
        if token_resp.status_code != 201:
            return {
                "error": "Failed to generate access token", 
                "details": token_resp.json()
            }
            
        token_data = token_resp.json()
        return {
            "token": token_data["token"],
            "expires_at": token_data["expires_at"],
            "installation_id": installation_id
        }

    except Exception as e:
        return {"error": str(e)}
