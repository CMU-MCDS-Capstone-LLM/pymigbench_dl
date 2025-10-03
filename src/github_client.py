"""
GitHub API client for downloading commits and getting parent information.
"""

import zipfile
import requests
import logging
from pathlib import Path
from typing import Optional, Tuple


class GitHubClient:
    """Client for interacting with GitHub API."""
    
    def __init__(self, github_token: str):
        self.github_token = github_token
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        })
        self.logger = logging.getLogger(__name__)

    def get_commit_parents(self, repo: str, commit_sha: str) -> Tuple[int, Optional[str]]:
        """
        Get the number of parents and the first parent SHA for a commit.
        
        Args:
            repo: Repository in format "owner/name"
            commit_sha: Commit SHA to query
            
        Returns:
            Tuple of (parent_count, first_parent_sha)
        """
        url = f"https://api.github.com/repos/{repo}/commits/{commit_sha}"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            commit_data = response.json()
            parents = commit_data.get("parents", [])
            
            parent_count = len(parents)
            first_parent_sha = parents[0]["sha"] if parents else None
            
            return parent_count, first_parent_sha
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching commit {commit_sha} from {repo}: {e}")
            return 0, None

    def download_commit_zip(self, repo: str, commit_sha: str, output_path: Path) -> bool:
        """
        Download a specific commit as a zip file from GitHub.
        
        Args:
            repo: Repository in format "owner/name"
            commit_sha: Commit SHA to download
            output_path: Path where to save the zip file
            
        Returns:
            True if download successful, False otherwise
        """
        url = f"https://api.github.com/repos/{repo}/zipball/{commit_sha}"
        
        try:
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error downloading {commit_sha} from {repo}: {e}")
            return False

    def extract_zip(self, zip_path: Path, extract_to: Path) -> bool:
        """
        Extract a zip file and clean up the zip.
        
        Args:
            zip_path: Path to the zip file
            extract_to: Directory to extract to
            
        Returns:
            True if extraction successful, False otherwise
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
            
            # Remove the zip file after extraction
            zip_path.unlink()
            return True
            
        except (zipfile.BadZipFile, OSError) as e:
            self.logger.error(f"Error extracting {zip_path}: {e}")
            return False