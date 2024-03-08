# gitloader.py
import os
from git import Repo
from github import Github
from langchain_community.document_loaders import GitLoader
from datetime import datetime, timezone
import subprocess

# GitHub credentials
github_token = ""
github_username = ""

# Initialize GitHub instance
github_client = Github(github_token)

# Retrieve a list of repositories for the authenticated user
repositories = github_client.get_user(github_username).get_repos()

# Function to check if the repository needs to be updated
def needs_update(local_repo_path, last_update_time):
    if not os.path.exists(local_repo_path):
        return True
    local_last_update_time = datetime.fromtimestamp(os.path.getmtime(local_repo_path)).replace(tzinfo=timezone.utc)
    last_update_time = last_update_time.replace(tzinfo=timezone.utc)
    return local_last_update_time < last_update_time


def update_backend_document(document_path, updated_data):
    with open(document_path, 'w') as f:
        f.write(updated_data)
        print("Document updated:", document_path)
        
all_data = []
for repo in repositories:
    repo_clone_path = f"./git_data/{repo.name}"
    last_update_time = repo.updated_at
    if not os.path.exists(repo_clone_path):
        Repo.clone_from(repo.clone_url, repo_clone_path)

    # Create GitLoader instance
    loader = GitLoader(repo_path=repo_clone_path)

    # Get the repository object
    local_repo = Repo(repo_clone_path)

    # Get the latest commit
    latest_commit = repo.get_commits()[0]

    # Check if the latest commit has been applied
    last_update_commit = local_repo.head.commit
    if latest_commit != last_update_commit:
        # Pull changes from the remote repository
        origin = local_repo.remotes.origin
        origin.pull()

        # Get the commit changes
        commit_changes = latest_commit.files

        # Update documents in backend
        for commit_change in commit_changes:
            document_path = os.path.join(repo_clone_path, commit_change.filename)
            if commit_change.status == 'update':
             updated_data = loader.load_file(commit_change.filename)
             update_backend_document(document_path, updated_data)

# Now, all_data contains data from all repositories in your GitHub account
print(len(all_data))
print("Process completed.")

def load_git_directory():
    git_directory = "./example_data/{repo.name}"
    return git_directory

git_directory = load_git_directory()
subprocess.run(["python", "gitaccount_rag.py", git_directory])
