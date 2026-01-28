import os
import subprocess
from .github_app import get_installation_token

def check_git_connection():
    repo_owner = "beam-me"
    repo_name = "user-code"
    
    # 1. Authenticate as App
    auth_result = get_installation_token(repo_owner, repo_name)
    
    if "error" in auth_result:
        return {"status": "error", "message": "App Authentication Failed", "details": auth_result}
    
    token = auth_result["token"]
    
    # 2. Verify Git Access via HTTPS
    # Construct URL with token
    # https://x-access-token:<token>@github.com/owner/repo.git
    repo_url = f"https://x-access-token:{token}@github.com/{repo_owner}/{repo_name}.git"
    
    try:
        # We use git ls-remote to verify read access without cloning
        # Using subprocess since 'git' binary might be missing, 
        # BUT WAIT, we established 'git' is missing.
        # We should use Dulwich for HTTPS now?
        # Or simple requests? 
        # Actually 'git ls-remote' won't work if git is missing.
        
        # Let's use Dulwich for the actual git check over HTTPS
        from dulwich import client
        
        dulwich_client = client.HttpGitClient(f"https://github.com/{repo_owner}/{repo_name}.git")
        # Dulwich requires a credential manager or headers
        # We can pass headers manually? Not easily in HttpGitClient.
        # Actually, we can just put the token in the URL for Dulwich too.
        
        # Dulwich client with auth in URL
        dulwich_client = client.HttpGitClient(repo_url)
        refs = dulwich_client.get_refs(repo_url)
        
        # Format refs for display
        ref_list = []
        for key, sha in list(refs.items())[:3]:
            ref_list.append(f"{key.decode('utf-8')}: {sha.decode('utf-8')}")

        return {
            "status": "connected",
            "message": "Successfully authenticated via GitHub App (HTTPS)",
            "app_auth": "success",
            "git_access": "success",
            "refs_head": ref_list
        }

    except Exception as e:
        return {
            "status": "error", 
            "message": "Git Access Failed", 
            "error": str(e),
            "app_auth": "success" # Auth worked, but git op failed
        }
