"""
PyMigBench dataset loader using the official PyMigBench Python package.
"""

import logging
from pathlib import Path
from typing import List
from pymigbench.migration import Migration
import yaml

from pymigbench.database import Database
from pymigbench.parsers import parse_migration


from .utils.paths import to_path
from .providers.github.models import CommitInfo


class PyMigBenchLoader:
    """Loader for PyMigBench dataset using the official Python package."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def load_all_commits_from_database(self, yaml_root_path: str) -> List[CommitInfo]:
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

    def load_single_commit_from_yaml(self, yaml_file_path: str) -> CommitInfo:
        """
        Load a single migration commit from a yaml file, following PyMigBench's yaml format

        PyMigBench didn't provide this functionality, so we have to implement it with non-documented fucntions from PyMigBench package.
        """

        path = to_path(yaml_file_path)
        migration = self.parse_mig_from_file(path)
        commit_info = CommitInfo(
            repo=migration.repo,
            commit_sha=migration.commit
        )
        return commit_info

    # parse_mig_from_file function is copied from PyMigBench's source code
    def parse_mig_from_file(self, path: Path) -> Migration:
        raw = yaml.unsafe_load(path.read_text("utf8"))
        migration = parse_migration(raw)
        return migration

