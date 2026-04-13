
import os
from dotenv import load_dotenv
from src.core.github_bridge import RepoManager

# Load .env
env_path = os.path.join(os.getcwd(), '.env')
load_dotenv(env_path)

repo = RepoManager()
print(f"Target Repo: {repo.repo_slug}")
print(f"Token present: {bool(repo.token)}")

info = repo.get_repo_info()
print("\n--- Repo Info ---")
print(info)

status = repo.get_git_status()
print("\n--- Local Git Status ---")
print(status)
