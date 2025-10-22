"""
Data models for PyMigBench downloader.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CommitInfo:
    """Information about a commit to be downloaded."""
    repo: str
    commit_sha: str
    parent_sha: Optional[str] = None
    parents_count: int = 0

    @property
    def repo_safe(self) -> str:
        """Repository name safe for use in filesystem paths."""
        return self.repo.replace("/", "_")

    @property
    def folder_name(self) -> str:
        """Folder name for this commit download."""
        return f"{self.repo_safe}__{self.commit_sha}"