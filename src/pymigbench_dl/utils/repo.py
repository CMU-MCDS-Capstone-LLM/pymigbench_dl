import logging
import os
import shutil
import tempfile
from pathlib import Path

from ..const.git import (
    DEFAULT_PRE_MIG_BRANCH_NAME,
    PYMIGBENCH_DL_PRE_MIG_COMMIT_MSG,
    PYMIGBENCH_DL_GT_MIG_COMMIT_MSG,
)
from ..providers.github.client import GitHubClient
from ..providers.github.models import CommitInfo
from .fs import extract_tar_top
from .git import add_and_commit, get_cur_branch_name, run_git

logger = logging.getLogger(__name__)

def _clear_worktree_but_git(repo_dir: Path) -> None:
    for p in repo_dir.iterdir():
        if p.name == ".git":
            continue
        if p.is_dir() and not p.is_symlink():
            shutil.rmtree(p)
        else:
            p.unlink(missing_ok=True)

def _move_children(src_dir: Path, dst_dir: Path) -> None:
    for child in src_dir.iterdir():
        shutil.move(str(child), str(dst_dir / child.name))

def _materialize_commit_tree(dst_dir: Path, commit: CommitInfo, github: GitHubClient) -> None:
    """
    Download tarball for `commit` and mirror its tree into `dst_dir`.
    Assumes `dst_dir` exists; clears everything except .git first.
    """
    with tempfile.TemporaryDirectory(dir=dst_dir.parent, prefix=f".fetch__{commit.repo_safe}__") as t:
        tdir = Path(t)
        tar_path = tdir / f"{commit.repo_safe}__{commit.commit_sha}.tar.gz"  # matches r:gz
        logger.info("Downloading %s@%s", commit.repo, commit.commit_sha)
        github.download_commit_tar(commit.repo, commit.commit_sha, tar_path)
        extracted_top = extract_tar_top(tar_path, extract_to=tdir)

        dst_dir.mkdir(parents=True, exist_ok=True)
        _clear_worktree_but_git(dst_dir)
        _move_children(extracted_top, dst_dir)

def _initialize_git_repo(repo_dir: Path, branch_name: str) -> None:
    logger.debug("Initializing git repo at %s with branch %s", repo_dir, branch_name)
    run_git(repo_dir, "init", "-b", branch_name)
    add_and_commit(repo_dir, PYMIGBENCH_DL_PRE_MIG_COMMIT_MSG)

def _create_gt_branch_from_commit(repo_dir: Path, branch_name: str,
                                              commit: CommitInfo, github: GitHubClient) -> None:
    """
    Create a new branch at current HEAD, replace tree with `commit` snapshot, commit,
    then switch back to the previous branch
    """
    cur = get_cur_branch_name(repo_dir)
    if cur == "HEAD":
        raise RuntimeError("Current branch is named 'HEAD', meaning it's detached. This shouldn't happen.")
    if cur == branch_name:
        raise RuntimeError(f"Current branch is named '{branch_name}', which is the same as the new branch name. Name conflict!")

    # fail if branch somehow exists
    run_git(repo_dir, "checkout", "-b", branch_name)

    _materialize_commit_tree(repo_dir, commit, github)
    add_and_commit(repo_dir, PYMIGBENCH_DL_GT_MIG_COMMIT_MSG)

    run_git(repo_dir, "checkout", cur)

def create_pymigbench_type_repo(
    mig_commit_info: CommitInfo,
    output_dir: Path,
    gt_patch_branch_name: str,
    github_client: GitHubClient,
    pre_mig_branch_name: str = DEFAULT_PRE_MIG_BRANCH_NAME,
) -> None:
    """
    Transactionally build the repo:
      - Base = parent of migration commit (initial commit on pre_mig_branch_name)
      - New branch = gt_patch_branch_name with migration snapshot commit on top
    Publish to output_dir only if everything succeeds.
    Policy: if final_dir already exists, we assume it's correct and SKIP.
    """
    final_dir = output_dir / mig_commit_info.folder_name
    if final_dir.exists():
        logger.info("Skipping %s (exists at %s)", mig_commit_info.commit_sha, final_dir)
        return

    parents, parent_sha = github_client.get_commit_parents(mig_commit_info.repo, mig_commit_info.commit_sha)
    if parents != 1 or not parent_sha:
        raise RuntimeError(
            f"Unsupported parents={parents} for {mig_commit_info.repo}@{mig_commit_info.commit_sha}"
        )
    parent_info = CommitInfo(mig_commit_info.repo, parent_sha)

    # Single staging dir on the SAME filesystem as output_dir for atomic publish
    with tempfile.TemporaryDirectory(dir=output_dir, prefix=f".staging__{mig_commit_info.folder_name}__") as tmp:
        staging_root = Path(tmp)
        staging_repo = staging_root / "work"
        staging_repo.mkdir(parents=True, exist_ok=True)

        # 1) parent snapshot -> initial commit
        _materialize_commit_tree(staging_repo, parent_info, github_client)
        _initialize_git_repo(staging_repo, pre_mig_branch_name)

        # 2) GT branch -> migration snapshot commit
        _create_gt_branch_from_commit(staging_repo, gt_patch_branch_name, mig_commit_info, github_client)

        # 3) publish atomically; final_dir must not exist by policy
        os.replace(staging_repo, final_dir)
        # TemporaryDirectory cleans up the now-empty staging_root
