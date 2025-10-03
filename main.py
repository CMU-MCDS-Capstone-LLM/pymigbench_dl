#!/usr/bin/env python3
"""
PyMigBench Downloader CLI

Downloads the entire PyMigBench dataset efficiently by downloading only the parent commits
of target commits that have exactly one parent.
"""

import os
import sys
import argparse
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src import PyMigBenchDownloader


def main():
    parser = argparse.ArgumentParser(description="Download PyMigBench dataset efficiently")
    parser.add_argument("--yaml-root", default="./repo-yamls", help="Path to PyMigBench YAML files directory")
    parser.add_argument("--output-dir", default="repos", help="Output directory for downloaded repos")
    parser.add_argument("--github-token", help="GitHub API token (or set GITHUB_TOKEN env var)")
    parser.add_argument("--max-workers", type=int, default=5, help="Number of concurrent downloads")
    parser.add_argument("--max-count", type=int, help="Limit number of commits (for testing)")
    
    args = parser.parse_args()
    
    # Get GitHub token
    github_token = args.github_token or os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("Error: GitHub token required. Set GITHUB_TOKEN environment variable or use --github-token")
        sys.exit(1)
    
    # Create downloader and start
    downloader = PyMigBenchDownloader(
        github_token=github_token,
        output_dir=args.output_dir,
        max_workers=args.max_workers
    )
    
    try:
        downloader.download_all(args.yaml_root, args.max_count)
    except KeyboardInterrupt:
        print("\nDownload interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()