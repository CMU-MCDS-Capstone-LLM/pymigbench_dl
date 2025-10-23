"""
Wrapper for git commands
"""

import logging
from pathlib import Path
import subprocess

from ..const.git import PYMIGBENCH_DL_GIT_USERNAME, PYMIGBENCH_DL_GIT_EMAIL

logger = logging.getLogger(__name__)

def run_git(repo_dir: Path, *args: str) -> str:
    cp = subprocess.run(["git", *args], cwd=repo_dir, check=True,
                        capture_output=True, text=True)
    return cp.stdout.strip()

def is_git_repo(repo_dir: Path) -> bool:
    try:
        run_git(repo_dir, "-C", str("."), "rev-parse", "--is-inside-work-tree")
        return True
    except subprocess.CalledProcessError:
        return False

def branch_exists(repo_dir: Path, branch_name: str) -> bool:
    try:
        run_git(repo_dir, "rev-parse", "--verify", "--quiet", f"refs/heads/{branch_name}")
        return True
    except subprocess.CalledProcessError:
        return False

def get_cur_branch_name(repo_dir: Path) -> str:
    """
    Get the name of current branch
    """
    return run_git(repo_dir, "rev-parse", "--abbrev-ref", "HEAD")

def check_branch_name(repo_dir: Path, name: str):
    """
    Validate if a branch name is valid in git. Raise if not.
    """
    run_git(repo_dir, "check-ref-format", f"refs/heads/{name}")
    return name

def safe_create_branch_and_checkout(repo_dir: Path, branch_name: str): 
    """
    Create a branch, check various condition to ensure creation is safe. Raise if unsafe.

    We did the following checks
    - the repo_dir is a git repo
    - 
    """
    if not is_git_repo(repo_dir):
        raise RuntimeError(f"Can't create branch '{branch_name}' at path {repo_dir} because it's not a git repo.")

    if branch_exists(repo_dir, branch_name):
        raise RuntimeError(f"Can't create branch '{branch_name}' at path {repo_dir} because the branch name '{branch_name}' conflicts with an existing branch")

    check_branch_name(repo_dir, branch_name)

    run_git(repo_dir, "checkout", "-b", branch_name) 

def add_and_commit(repo_dir, commit_msg: str):
    run_git(repo_dir, "add", "-A")
    run_git(repo_dir, 
        "-c", f"user.name={PYMIGBENCH_DL_GIT_USERNAME}", 
        "-c", f"user.email={PYMIGBENCH_DL_GIT_EMAIL}", 
        "commit", 
        "-m", commit_msg
    )

