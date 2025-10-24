"""
Data models for PyMigBench downloader.
"""

from dataclasses import dataclass
from pymigbench.migration import Migration
from typing import Self


@dataclass
class CommitInfo:
    """Information about a commit to be downloaded."""
    repo: str
    commit_sha: str

    @property
    def repo_safe(self) -> str:
        """Repository name safe for use in filesystem paths."""
        return self.repo.replace("/", "_")

    @property
    def folder_name(self) -> str:
        """Folder name for this commit download. Unique across PyMigBench"""
        return f"{self.repo_safe}__{self.commit_sha}"

    @classmethod
    def from_mig(cls, mig: Migration) -> Self:
        return cls(repo=mig.repo, commit_sha=mig.commit)
