"""
PyMigBench Downloader CLI

Downloads one repo or the entire PyMigBench dataset efficiently by downloading only the parent commits
of target commits that have exactly one parent.
"""

import os
import argparse
import logging

from ..downloader import PyMigBenchDownloader
from ..const.git import DEFAULT_GT_PATCH_BRANCH_NAME

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="pymigbench-dl", description="PyMigBench downloader helper")
    sub = p.add_subparsers(dest="cmd", required=True)

    # download-all
    a = sub.add_parser("dl-all", help="Download all commits from a YAML root")
    a.add_argument("--yaml-root", required=True)
    a.add_argument("--output-dir", required=True)
    a.add_argument("--gt-patch-branch-name", default=DEFAULT_GT_PATCH_BRANCH_NAME)
    a.add_argument("--github-token")
    a.add_argument("--max-workers", type=int, default=5)
    a.add_argument("--rate-limit", type=float, default=1.0)

    # download-single
    s = sub.add_parser("dl-single", help="Download a single commit from a YAML file")
    s.add_argument("--yaml-file", required=True)
    s.add_argument("--output-dir", required=True)
    s.add_argument("--gt-patch-branch-name", default=DEFAULT_GT_PATCH_BRANCH_NAME)
    s.add_argument("--github-token")

    p.add_argument("-v", "--verbose", action="count", default=0)
    return p

def main():
    args = build_parser().parse_args()
    lvl = logging.WARNING if args.verbose == 0 else (logging.INFO if args.verbose == 1 else logging.DEBUG)
    logging.basicConfig(level=lvl, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    github_token = (getattr(args, "github_token", None) or os.getenv("GITHUB_TOKEN"))
    if not github_token:
        raise SystemExit("Error: GitHub token required. Set GITHUB_TOKEN or pass --github-token")

    dl = PyMigBenchDownloader(
        github_token=github_token,
        output_dir=getattr(args, "output_dir", "repos"),
        max_workers=getattr(args, "max_workers", 5),
        rate_limit_delay=getattr(args, "rate_limit", 1.0),
    )

    if args.cmd == "dl-all":
        dl.download_all(args.yaml_root, args.gt_patch_branch_name)
    elif args.cmd == "dl-single":
        dl.download_single(args.yaml_file, args.gt_patch_branch_name)

if __name__ == "__main__":
    main()
