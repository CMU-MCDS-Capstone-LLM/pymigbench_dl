# PyMigBench Downloader

This script efficiently downloads the PyMigBench dataset by downloading only the parent commits of target commits that have exactly one parent.

## Overview

For each migration in the PyMigBench dataset, instead of downloading the full repository history, we:
1. Check if the target commit has exactly 1 parent (skip merge commits and initial commits)
2. Download only the parent commit as a zip file from GitHub
3. Extract and organize the downloaded commits

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set your GitHub token:
```bash
export GITHUB_TOKEN="your_github_personal_access_token"
```

3. Download the PyMigBench YAML files to `./repo-yamls/` directory

## Usage

Basic usage (assumes YAML files are in `./repo-yamls/`):
```bash
python3 main.py
```

With options:
```bash
python3 main.py \
    --yaml-root "./repo-yamls" \
    --output-dir repos \
    --max-workers 5 \
    --max-count 100
```

### Arguments
- `--yaml-root`: Path to PyMigBench YAML files directory (default: "./repo-yamls")
- `--output-dir`: Directory to save downloaded repos (default: "repos")
- `--github-token`: GitHub API token (or set GITHUB_TOKEN env var)
- `--max-workers`: Number of concurrent downloads (default: 5)
- `--max-count`: Limit number of commits for testing (optional)
- `--rate-limit`: Delay between downloads in seconds (default: 1.0)

## Output Structure

Downloaded commits are organized as:
```
repos/
├── owner_repo__target_commit_sha/
│   ├── source_file1.py
│   ├── source_file2.py
│   └── ... (all source code files from parent commit)
```

Each folder contains the complete source code snapshot from the parent commit of the target migration commit.

## Project Structure

```
pymigbench_downloader/
├── main.py                 # CLI entry point
├── src/
│   ├── __init__.py        # Package initialization
│   ├── models.py          # Data models (CommitInfo)
│   ├── github_client.py   # GitHub API operations
│   ├── pymigbench_loader.py # YAML parsing and data loading
│   └── downloader.py      # Main download coordinator
├── requirements.txt       # Python dependencies
├── envrc                 # Environment configuration
└── download_example.sh   # Example usage script
```

## Features

- **Modular design**: Clean separation of concerns across multiple modules
- **Efficient**: Downloads only necessary commits (parent commits with exactly 1 parent)
- **Concurrent**: Multi-threaded downloads with configurable worker count
- **Resumable**: Skips already downloaded commits
- **Error handling**: Robust error handling with detailed logging
- **Progress tracking**: Real-time progress updates
