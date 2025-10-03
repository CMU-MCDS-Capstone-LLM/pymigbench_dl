"""
Main downloader coordinator for PyMigBench dataset.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from .models import CommitInfo
from .github_client import GitHubClient
from .pymigbench_loader import PyMigBenchLoader


class PyMigBenchDownloader:
    """Main coordinator for downloading PyMigBench dataset."""
    
    def __init__(self, github_token: str, output_dir: str = "repos", max_workers: int = 5):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.max_workers = max_workers
        
        # Initialize components
        self.github_client = GitHubClient(github_token)
        self.pymigbench_loader = PyMigBenchLoader()
        
        # Setup logging to both file and console
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        log_file = self.output_dir / "download.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"PyMigBench Downloader initialized. Log file: {log_file}")

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
            
            self.logger.info(f"Successfully processed {commit_info.repo}:{commit_info.commit_sha} -> {commit_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing {commit_info.repo}:{commit_info.commit_sha}: {e}")
            # Clean up temp directory on failure
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            return False


    def download_all(self, yaml_root_path: str, max_count: Optional[int] = None) -> None:
        """
        Download all valid commits from PyMigBench dataset.
        
        Args:
            yaml_root_path: Path to the directory containing PyMigBench YAML files
            max_count: Optional limit on number of commits to process (for testing)
        """
        commits = self.pymigbench_loader.load_commits_from_database(yaml_root_path)
        
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
