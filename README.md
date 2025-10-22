# PyMigBench Downloader

`pymigbench-dl` is a small helper that fetches repository snapshots referenced by the [PyMigBench] benchmark.
Instead of cloning full histories, it downloads **only the parent of each target commit** (when the target has exactly one parent), then initializes a minimal git repo for that snapshot.

## TODO

* [ ] Rewrite README.md

* [ ] Create a commit that reflect the post-mig status of the repo

* [ ] Modify the date of commit, b/c we will use date to heuristically discover python interpreter version

## Overview

For each migration entry in PyMigBench:

1. Look up the target commit’s parents via the GitHub API.
2. **If and only if** the commit has exactly **one** parent, download a zipball of that parent commit.
3. Extract to `owner_repo__target_commit_sha/`, then initialize a one-commit git repo inside it.
4. Skip anything already present on disk.

This minimizes bandwidth and storage while giving you a consistent, file-system-level snapshot that corresponds to the *pre-migration* parent.

---

## Installation

Requires **Python 3.11+**.

```bash
# inside your (conda) env
pip install -e .
```

This provides:

* A library: `pymigbench_dl`
* A CLI: `pymigbench-dl`

### Dependencies

* `pymigbench` (to read the YAML database and parse single migration YAMLs)
* `requests`, `PyYAML`

---

## Authentication

Set your GitHub token (recommended to avoid low rate limits):

```bash
export GITHUB_TOKEN=ghp_your_token_here
```

You can also pass `--github-token` on the CLI.

---

## CLI Usage

The CLI exposes two subcommands: `dl-all` and `dl-single`. Use `-v` (or `-vv`) for more logs.

### Download all (YAML root directory)

```bash
pymigbench-dl -v dl-all \
  --yaml-root /path/to/repo-yamls \
  --output-dir /path/to/output \
  --github-token "$GITHUB_TOKEN" \
  --max-workers 8 \
  --max-count 100 \
  --rate-limit 0.5
```

**Flags (current behavior):**

* `--yaml-root` *(required)*: Directory containing PyMigBench YAML files.
* `--output-dir` *(optional)*: Where snapshots go. Defaults to `repos/` if omitted.
* `--github-token` *(optional)*: Falls back to `$GITHUB_TOKEN`.
* `--max-workers` *(optional, default 5)*: Thread pool size.
* `--max-count` *(optional)*: Process only the first N entries (useful for smoke tests).
* `--rate-limit` *(optional, default 1.0)*: Sleep (seconds) between downloads.

### Download a single commit (single YAML file)

```bash
pymigbench-dl -v dl-single \
  --yaml-file /path/to/migration.yaml \
  --output-dir /path/to/output \
  --github-token "$GITHUB_TOKEN"
```

* `--yaml-file` *(required)*: One migration YAML in PyMigBench format.
* Other flags behave like above.

### Help

```bash
pymigbench-dl --help
pymigbench-dl dl-all --help
pymigbench-dl dl-single --help
```

---

## Programmatic Usage

Use the downloader as a library:

```python
from pymigbench_dl import PyMigBenchDownloader

dl = PyMigBenchDownloader(
    github_token="YOUR_TOKEN",
    output_dir="repos",    # default if omitted
    max_workers=5,         # default
    rate_limit_delay=1.0   # default
)

# Download everything listed in the YAML database directory
dl.download_all("/path/to/repo-yamls", max_count=50)

# Or download one migration from a YAML file
dl.download_single("/path/to/migration.yaml")
```

---

## Output Layout

Snapshots are placed under the output directory using this naming scheme:

```
<output-dir>/
└── <owner>_<repo>__<target_commit_sha>/
    ├── ... extracted files from the downloaded parent commit ...
    └── .git/  (initialized with a single commit)
```

Notes:

* A directory is created **per target commit**, but its contents come from the **parent** of that target (only when there’s exactly one parent).
* If a directory already exists, the downloader **skips** it.

---

## Logging

* Default level: `WARNING`
* Use `-v` for `INFO`, `-vv` for `DEBUG`
* Logs include module names and timestamps.

Example:

```bash
pymigbench-dl -vv dl-all --yaml-root ./repo-yamls
```

---

## Project Structure (current)

```
src/pymigbench_dl/
├── __init__.py
├── cli/
│   └── main.py           # argparse-based CLI (dl-all, dl-single)
├── downloader.py         # main coordinator
├── loader.py             # loads migrations from YAMLs via pymigbench
├── providers/
│   └── github/
│       ├── __init__.py
│       ├── client.py     # GitHub API calls, zip download + extract
│       └── models.py     # CommitInfo
└── utils/
    ├── __init__.py
    └── paths.py          # to_path helper
```
