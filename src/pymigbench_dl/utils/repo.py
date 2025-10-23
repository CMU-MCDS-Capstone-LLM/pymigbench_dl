"""
High-level operation related to git repo
"""

import logging
import shutil
import tempfile
from pathlib import Path

from ..const.git import PYMIGBENCH_DL_PRE_MIG_COMMIT_MSG, PYMIGBENCH_DL_GT_MIG_COMMIT_MSG

from ..providers.github.client import GitHubClient
from ..providers.github.models import CommitInfo

from .fs import extract_tar_flat
from .git import add_and_commit, get_cur_branch_name, run_git, safe_create_branch_and_checkout

logger = logging.getLogger(__name__)

def create_git_repo_from_commit(output_dir: Path, repo_folder_name: str, commit_info: CommitInfo, github_client: GitHubClient) -> None:
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
        tar_path = tmpdir / f"{commit_info.repo_safe}__{commit_sha}.tar.gz"

        # Download tarball from commit
        logger.info(f"Downloading GitHub repo {repo}:{commit_sha}")

        github_client.download_commit_tar(repo, commit_sha, tar_path)

        # Extract the tarball in tmp dir
        extracted_top = extract_tar_flat(tar_path, extract_to=tmpdir)

        shutil.move(str(extracted_top), str(repo_dir))

        initialize_git_repo(repo_dir)

def initialize_git_repo(repo_dir: Path) -> None:
    """
    Initialize a git repository and create a dummy commit.
    
    Args:
        repo_dir: Directory to initialize as git repo
    """
    logger.debug(f"Initializing git repo at folder {repo_dir}")

    run_git(repo_dir, "init")
    add_and_commit(repo_dir, PYMIGBENCH_DL_PRE_MIG_COMMIT_MSG)
   

def create_branch_using_commit_on_repo(repo_dir: Path, branch_name: str, branch_commit: CommitInfo, github_client: GitHubClient) -> None:
    """
    Create a branch `branch_name` from the HEAD of repo, and apply `branch_commit` on `branch_name`.

    This is implemented by
    1. create new branch from HEAD, and checkout to new branch
    2. replace the repo content with the snapshot of repo at branch_commit
        1. download branch_commit snapshot to tmp folder
        2. delete all files in repo folder except .git/ folder
        3. move all content in tmp folder to repo folder
    3. checkout to original branch

    Note: We don't enforce the HEAD commit and branch commit to be two consecutive commits on the original repo's git history. But it should be the case since we are using parent commit of migration commit as HEAD, and create the branch from migration commit.
    """
    def _clear_worktree_but_git(repo_dir: Path) -> None:
        for p in repo_dir.iterdir():
            if p.name == ".git":
                continue
            if p.is_dir() and not p.is_symlink():
                shutil.rmtree(p)
            else:
                p.unlink(missing_ok=True)

    def _move_children(src_dir: Path, dst_dir: Path) -> None:
        """Move children of src_dir into dst_dir (not the top folder itself)."""
        for child in src_dir.iterdir():
            shutil.move(str(child), str(dst_dir / child.name))
    
    repo_dir = repo_dir.resolve()

    cur_branch_name = get_cur_branch_name(repo_dir)

    safe_create_branch_and_checkout(repo_dir, branch_name)

    commit_sha = branch_commit.commit_sha
    tmp_prefix = f".tmp__{branch_commit.repo_safe}__{commit_sha}"

    with tempfile.TemporaryDirectory(dir=repo_dir.parent, prefix=tmp_prefix) as tmp:
        tmpdir = Path(tmp)
        tar_path = tmpdir / f"{branch_commit.repo_safe}__{branch_commit.commit_sha}.tar.gz"

        logger.debug("Downloading snapshot %s:%s for branch '%s'",
                 branch_commit.repo, branch_commit.commit_sha, branch_name)
        github_client.download_commit_tar(branch_commit.repo, branch_commit.commit_sha, tar_path)

        extracted_top = extract_tar_flat(tar_path, extract_to=tmpdir)

        _clear_worktree_but_git(repo_dir)
        _move_children(extracted_top, repo_dir)

    add_and_commit(repo_dir, PYMIGBENCH_DL_GT_MIG_COMMIT_MSG)

    run_git(repo_dir, "checkout", cur_branch_name)

def create_pymigbench_type_repo(mig_commit_info: CommitInfo, output_dir: Path, gt_patch_branch_name: str, github_client: GitHubClient):
    """
    Create a repo from pymigbench specification
    
    Args:
        commit_info: Information about the commit to process
        TODO: Finish this doc
    """
    repo_folder_name = mig_commit_info.folder_name
    repo_dir = output_dir / repo_folder_name
    
    # Skip if already downloaded (folder exists means successful download)
    if repo_dir.exists():
        logger.info(f"Skipping {mig_commit_info.repo}:{mig_commit_info.commit_sha} (already exists at {repo_dir})")
        return
    
    # Get parent information
    parent_count, parent_commit_sha = github_client.get_commit_parents(mig_commit_info.repo, mig_commit_info.commit_sha)
    
    if parent_count != 1:
        raise RuntimeError(f"Found a repo with parent count not equal 1. Can't handle such case. Skipping {mig_commit_info.repo}:{mig_commit_info.commit_sha} ({parent_count} parents)")
    
    if not parent_commit_sha:
        raise RuntimeError(f"No parent SHA found for {mig_commit_info.repo}:{mig_commit_info.commit_sha}")

    parent_commit_info = CommitInfo(mig_commit_info.repo, parent_commit_sha)
    create_git_repo_from_commit(output_dir, repo_folder_name, parent_commit_info, github_client)
    create_branch_using_commit_on_repo(repo_dir, gt_patch_branch_name, mig_commit_info, github_client)
