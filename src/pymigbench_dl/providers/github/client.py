"""
GitHub API client for downloading commits and getting parent information.
"""

import zipfile
import requests
import logging
from pathlib import Path
from typing import Optional, Tuple
import subprocess


class GitHubClient:
    """Client for interacting with GitHub API."""
    
    def __init__(self, github_token: str):
        self.github_token = github_token
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "pymigbench-dl"
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
        self.logger.debug(f"Getting parent commit of repo {repo} commit {commit_sha}")
        url = f"https://api.github.com/repos/{repo}/commits/{commit_sha}"
        response = self.session.get(url)
        response.raise_for_status()
        
        commit_data = response.json()
        parents = commit_data.get("parents", [])
        
        parent_count = len(parents)
        first_parent_sha = parents[0]["sha"] if parents else None
        
        return parent_count, first_parent_sha

    def download_commit_zip(self, repo: str, commit_sha: str, output_path: Path) -> None:
        """
        Download a specific commit as a zip file from GitHub.
        
        Args:
            repo: Repository in format "owner/name"
            commit_sha: Commit SHA to download
            output_path: Path where to save the zip file
        """
        url = f"https://api.github.com/repos/{repo}/zipball/{commit_sha}"
        
        response = self.session.get(url, stream=True)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

