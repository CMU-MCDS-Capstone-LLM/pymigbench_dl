import logging
import shutil
import tempfile
from pathlib import Path
import subprocess

from pymigbench_dl.providers.github.client import GitHubClient
from pymigbench_dl.providers.github.models import CommitInfo

from .fs import extract_zip_flat

def create_git_repo_from_commit(output_dir: Path, repo_folder_name: str, commit_info: CommitInfo, github_client: GitHubClient) -> None:
    logger = logging.getLogger(__name__)

    repo = commit_info.repo
    commit_sha = commit_info.commit_sha
    tmp_prefix = f".tmp__{commit_info.repo_safe}__{commit_sha}"
    repo_dir = output_dir / repo_folder_name

    logger.debug(f"Create git repo from repo {repo} commit {commit_sha} at path {repo_dir}")

    if repo_dir.exists():
        raise ValueError(f"Can't create repo from commit at path {repo_dir}, folder already exists")

    # tmp folder is removed when we exit with, even due to exception
    with tempfile.TemporaryDirectory(dir=output_dir, prefix=tmp_prefix) as tmp:
        tmpdir = Path(tmp)
        zip_path = tmpdir / f"{commit_info.repo_safe}__{commit_sha}.zip"

        # Download zip from commit
        logger.info(f"Downloading GitHub repo {repo}:{commit_sha}")

        github_client.download_commit_zip(repo, commit_sha, zip_path)

        # Extract the zip in tmp dir
        extracted_top = extract_zip_flat(zip_path, extract_to=tmpdir)

        shutil.move(str(extracted_top), str(repo_dir))

        initialize_git_repo(repo_dir)

def initialize_git_repo(repo_dir: Path):
    """
    Initialize a git repository and create a dummy commit.
    
    Args:
        repo_dir: Directory to initialize as git repo
    """
    logger = logging.getLogger(__name__)

    logger.debug(f"Initializing git repo at folder {repo_dir}")

    # Change to the repository directory and run git commands
    git_commands = [
        ["git", "init"],
        ["git", "add", "."],
        ["git", "-c", "user.name=PyMigBench Downloader", "-c", "user.email=downloader@pymigbench.local", 
            "commit", "-m", "Repo initialized using parent commit of the migration commit (git history of original repo is removed)"]
    ]
    
    for cmd in git_commands:
        subprocess.run(cmd, cwd=repo_dir, check=True, capture_output=True)
