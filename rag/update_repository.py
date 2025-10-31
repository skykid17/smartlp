import requests
import os
import subprocess
from pathlib import Path


def update_elastic_repo():
    """
    Download the list of Elastic packages using GitHub API and maintain local repository.
    """
    # GitHub API URL for packages directory
    api_url = "https://api.github.com/repos/elastic/integrations/contents/packages"
    repo_url = "https://github.com/elastic/integrations.git"
    local_repo_path = "./rag/repos/elastic_repo"
    
    try:
        # Download package list via GitHub API
        print("Downloading Elastic packages list...")
        response = requests.get(api_url)
        response.raise_for_status()
        
        # Handle local repository
        if os.path.exists(local_repo_path):
            print(f"Local repository '{local_repo_path}' exists. Updating...")
            update_local_repository(local_repo_path)
        else:
            print(f"Local repository '{local_repo_path}' doesn't exist. Cloning...")
            clone_repository(repo_url, local_repo_path)
            
    except requests.RequestException as e:
        print(f"Error downloading Elastic packages: {e}")
    except subprocess.CalledProcessError as e:
        print(f"Error with git operation: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def clone_repository(repo_url, local_path):
    """
    Clone the Elastic integrations repository.
    """
    try:
        # Clone only the packages directory to save space and time
        subprocess.run([
            "git", "clone", "--depth", "1", "--filter=blob:none", repo_url, local_path
        ], check=True)
        
        # Set up sparse checkout for packages directory only
        os.chdir(local_path)
        subprocess.run(["git", "sparse-checkout", "set", "packages"], check=True)
        os.chdir("..")  # Go back to original directory
        
        print(f"Repository cloned successfully to '{local_path}'")
    except subprocess.CalledProcessError as e:
        print(f"Error cloning repository: {e}")


def update_local_repository(local_path):
    """
    Update the existing local repository.
    """
    try:
        original_dir = os.getcwd()
        os.chdir(local_path)
        
        # Fetch latest changes
        subprocess.run(["git", "fetch", "origin"], check=True)
        
        # Reset to latest main branch
        subprocess.run(["git", "reset", "--hard", "origin/main"], check=True)
        
        os.chdir(original_dir)
        print(f"Repository '{local_path}' updated successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error updating repository: {e}")
        # Go back to original directory even if error occurs
        try:
            os.chdir(original_dir)
        except:
            pass

if __name__ == "__main__":
    update_elastic_repo()