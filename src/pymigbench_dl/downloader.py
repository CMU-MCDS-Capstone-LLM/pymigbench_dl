"""
Main downloader coordinator for PyMigBench dataset.
"""

import os
import time
import shutil
import logging
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess

from .utils.paths import to_path

from .providers.github.models import CommitInfo
from .providers.github.client import GitHubClient
from .loader import PyMigBenchLoader


class PyMigBenchDownloader:
    """Main coordinator for downloading PyMigBench dataset."""
    
    def __init__(self, github_token: str, output_dir: str = "repos", max_workers: int = 5, rate_limit_delay: float = 1.0):
        self.output_dir = to_path(output_dir, check_exists=False)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.max_workers = max_workers
        self.rate_limit_delay = rate_limit_delay
        
        # Initialize components
        self.github_client = GitHubClient(github_token)
        self.pymigbench_loader = PyMigBenchLoader()
        
        # Setup logging to both file and console
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initialized downloader with output folder %s (workers=%d, rate=%.2fs)",
                       self.output_dir, self.max_workers, self.rate_limit_delay)

    def process_single_commit(self, commit_info: CommitInfo) -> bool:
        """
        Process a single commit: check parents, download if valid.
        
        Args:
            commit_info: Information about the commit to process
            
        Returns:
            True if processed successfully, False otherwise
        """
        commit_dir = self.output_dir / commit_info.folder_name
        
        # Skip if already downloaded (folder exists means successful download)
        if commit_dir.exists():
            self.logger.info(f"Skipping {commit_info.repo}:{commit_info.commit_sha} (already exists at {commit_dir})")
            return True
        
        # Get parent information
        parent_count, parent_sha = self.github_client.get_commit_parents(commit_info.repo, commit_info.commit_sha)
        
        if parent_count != 1:
            self.logger.info(f"Skipping {commit_info.repo}:{commit_info.commit_sha} ({parent_count} parents)")
            return False
        
        if not parent_sha:
            self.logger.error(f"No parent SHA found for {commit_info.repo}:{commit_info.commit_sha}")
            return False
        
        # Use a temporary directory for download
        temp_dir = self.output_dir / f".temp__{commit_info.folder_name}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        zip_path = temp_dir / f"{parent_sha}.zip"
        
        try:
            # Download parent commit
            self.logger.info(f"Downloading {commit_info.repo}:{parent_sha} (parent of {commit_info.commit_sha})")
            
            if not self.github_client.download_commit_zip(commit_info.repo, parent_sha, zip_path):
                return False
            
            # Extract the zip directly to temp directory
            if not self.github_client.extract_zip(zip_path, temp_dir):
                return False

            assert os.path.exists(commit_dir)

            # Initialize git repo and make dummy commit
            if not self._initialize_git_repo(commit_dir):
                # Remove the downloaded commit snapshot
                shutil.rmtree(commit_dir)
                return False
            
            # Rate limiting to respect GitHub API
            time.sleep(self.rate_limit_delay)
            
            self.logger.info(f"Successfully processed {commit_info.repo}:{commit_info.commit_sha} -> {commit_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing {commit_info.repo}:{commit_info.commit_sha}: {e}")
            # Clean up temp directory on failure
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            return False

    def _initialize_git_repo(self, repo_dir: Path) -> bool:
        """
        Initialize a git repository and create a dummy commit.
        
        Args:
            repo_dir: Directory to initialize as git repo
        """
        try:
            
            # Change to the repository directory and run git commands
            git_commands = [
                ["git", "init"],
                ["git", "add", "."],
                ["git", "-c", "user.name=PyMigBench Downloader", "-c", "user.email=downloader@pymigbench.local", 
                 "commit", "-m", "init commit (git history of original repo is removed)"]
            ]
            
            for cmd in git_commands:
                subprocess.run(cmd, cwd=repo_dir, check=True, capture_output=True)
            
            self.logger.debug(f"Initialized git repo in {repo_dir}")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"Failed to initialize git repo in {repo_dir}: {e}")
            return False

    def download_single(self, yaml_file_path: str) -> None:
        """
        Download a single commit from PyMigBench dataset, following the provided yaml file

        Args:
            yaml_file_path: path to the yaml file that defines a migration commit in PyMigBench format
        """
        commit_info = self.pymigbench_loader.load_single_commit_from_yaml(yaml_file_path)
        self.process_single_commit(commit_info)
        
    def download_all(self, yaml_root_path: str, max_count: Optional[int] = None) -> None:
        """
        Download all valid commits from PyMigBench dataset.
        
        Args:
            yaml_root_path: Path to the directory containing PyMigBench YAML files
            max_count: Optional limit on number of commits to process (for testing)
        """
        commits = self.pymigbench_loader.load_all_commits_from_database(yaml_root_path)
        
        if max_count:
            commits = commits[:max_count]
            self.logger.info(f"Limited to {max_count} commits for testing")
        
        self.logger.info(f"Starting download of {len(commits)} commits using {self.max_workers} workers")
        
        successful = 0
        failed = 0
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all jobs
            future_to_commit = {
                executor.submit(self.process_single_commit, commit): commit 
                for commit in commits
            }
            
            # Process completed jobs
            for future in as_completed(future_to_commit):
                commit = future_to_commit[future]
                try:
                    success = future.result()
                    if success:
                        successful += 1
                    else:
                        failed += 1
                except Exception as e:
                    self.logger.error(f"Exception processing {commit.repo}:{commit.commit_sha}: {e}")
                    failed += 1
                
                # Progress update
                total_processed = successful + failed
                if total_processed % 10 == 0:
                    self.logger.info(f"Progress: {total_processed}/{len(commits)} processed "
                                   f"({successful} successful, {failed} failed)")
        
        self.logger.info(f"Download complete: {successful} successful, {failed} failed")
