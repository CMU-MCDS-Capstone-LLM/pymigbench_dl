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

from .utils.git import create_git_repo_from_commit
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
        try:
            repo_folder_name = commit_info.folder_name
            repo_dir = self.output_dir / repo_folder_name
            
            # Skip if already downloaded (folder exists means successful download)
            if repo_dir.exists():
                self.logger.info(f"Skipping {commit_info.repo}:{commit_info.commit_sha} (already exists at {repo_dir})")
                return True
            
            # Get parent information
            parent_count, parent_sha = self.github_client.get_commit_parents(commit_info.repo, commit_info.commit_sha)
            
            if parent_count != 1:
                self.logger.error(f"Found a repo with parent count not equal 1. Can't handle such case. Skipping {commit_info.repo}:{commit_info.commit_sha} ({parent_count} parents)")
                return False
            
            if not parent_sha:
                self.logger.error(f"No parent SHA found for {commit_info.repo}:{commit_info.commit_sha}")
                return False

            parent_commit_info = CommitInfo(commit_info.repo, parent_sha)
            create_git_repo_from_commit(self.output_dir, repo_folder_name, parent_commit_info, self.github_client)
            return True
        except Exception as e:
            self.logger.error(f"Failed to process repo {commit_info.repo} commit {commit_info.commit_sha}")
            self.logger.error(f"Got error: {e}")
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
