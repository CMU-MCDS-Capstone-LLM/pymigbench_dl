"""
PyMigBench dataset loader using the official PyMigBench Python package.
"""

import logging
from typing import List, Optional

try:
    from pymigbench.database import Database
except ImportError:
    raise ImportError("PyMigBench package not found. Install with: pip install pymigbench")

from .models import CommitInfo


class PyMigBenchLoader:
    """Loader for PyMigBench dataset using the official Python package."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def load_commits_from_database(self, yaml_root_path: str) -> List[CommitInfo]:
        """
        Load migration data from PyMigBench dataset using the official API.
        
        Args:
            yaml_root_path: Path to the directory containing PyMigBench YAML files
            
        Returns:
            List of CommitInfo objects
        """
        try:
            # Load the PyMigBench database from the specified YAML directory
            from pathlib import Path
            yaml_root = Path(yaml_root_path)
            
            if not yaml_root.exists():
                raise FileNotFoundError(f"PyMigBench YAML directory not found: {yaml_root}")
            
            db = Database.load_from_dir(yaml_root)
            self.logger.info(f"Loaded PyMigBench database from {yaml_root}")
            
            migrations = db.migs()
            self.logger.info(f"Found {len(migrations)} migrations in PyMigBench")
            
            commits = []
            
            # Extract commits from all migrations
            for migration in migrations:
                commit_info = CommitInfo(
                    repo=migration.repo,
                    commit_sha=migration.commit
                )
                commits.append(commit_info)
            
            self.logger.info(f"Found {len(commits)} unique commits")
            return commits
            
        except Exception as e:
            self.logger.error(f"Error loading PyMigBench database: {e}")
            raise

