# PyMigBench Downloader (`pymigbench-dl`)

A focused helper that reconstructs **minimal, reproducible repos** for the [PyMigBench] dataset:

- **Base:** the *parent* of each migration commit (only if it has exactly **one** parent).
- **GT branch:** a new branch (default `gt-patch`) whose tip mirrors the *migration* commit’s tree.

No full clone, no history fetches—just two precise snapshots turned into a tiny Git repo.

---

## Installation

Requires **Python 3.11+** and a working `git` in `PATH`.

We recommend installation from GitHub repo directly, using

```bash
pip install git+https://github.com/CMU-MCDS-Capstone-LLM/pymigbench_dl.git
```

This installs:

- Library: `pymigbench_dl`
- CLI: `pymigbench-dl`

### Dependencies

- `pymigbench` (read YAML DB / parse single YAML)
- `requests`, `PyYAML`

---

## Authentication

Provide a GitHub token (mandatory in this tool to avoid rate-limit pain):

```bash
export GITHUB_TOKEN=ghp_your_token_here
```

You can also pass `--github-token` on the CLI.

---

## CLI Usage

Two subcommands: `dl-all` and `dl-single`. Use `-v` / `-vv` for more logs.

### Download **all** migrations (from a YAML directory)

```bash
pymigbench-dl -v dl-all \
  --yaml-root /path/to/repo-yamls \
  --output-dir /path/to/output \
  --gt-patch-branch-name gt-patch \
  --github-token "$GITHUB_TOKEN" \
  --max-workers 8 \
  --rate-limit 0.5
```

**Flags:**

- `--yaml-root` *(required)*: directory with PyMigBench YAMLs.
- `--output-dir` *(required)*: output root (repos are created under here).
- `--gt-patch-branch-name` *(default: `gt-patch`)*: name of the ground-truth branch.
- `--github-token` *(optional if `$GITHUB_TOKEN` is set)*.
- `--max-workers` *(default 5)*: thread pool size.
- `--rate-limit` *(default 1.0s)*: per-task delay (coarse throttling).

### Download a **single** migration (one YAML file)

```bash
pymigbench-dl -v dl-single \
  --yaml-file /path/to/migration.yaml \
  --output-dir /path/to/output \
  --gt-patch-branch-name gt-patch \
  --github-token "$GITHUB_TOKEN"
```

### Help

```bash
pymigbench-dl --help
pymigbench-dl dl-all --help
pymigbench-dl dl-single --help
```

---

## What gets created (layout & contents)

For a migration `{repo="owner/name", commit_sha="Y"}` we create:

```
<output-dir>/
└── owner_name__Y/           # directory name uses the MIGRATION sha
    ├── .git/                # initialized repository
    ├── ...                  # files from the PARENT of Y (base snapshot)
    └── (no working junk)
```

**Inside the repo:**

- **Base branch (current branch after build):** 1 commit representing the **parent of Y**
  Commit message:
  `Repo initialized using parent commit of the migration commit (git history of original repo is removed)`

- **GT branch (`gt-patch` by default):** 1 commit whose tree equals **Y**
  Commit message:
  `Repo updated with ground truth migration commit`

We **switch back** to the base branch before publishing, so the repo is left checked out at the parent snapshot.

**Idempotency / skipping:** if `owner_name__Y/` already exists, we assume it’s complete and **skip**.

---

## How it works (pipeline)

For each migration:

1. Parse migration(s) via `pymigbench`.
2. Query GitHub for commit `Y`’s parents; **require exactly one** parent `X`.
3. In a **TemporaryDirectory under `output_dir`**:

   - Download **tarball** for `X`, extract, mirror into staging repo, `git init` + initial commit.
   - Create branch `gt-patch` (create-only), download **tarball** for `Y`, extract/mirror, **`git add -A`** + commit.
   - Switch back to the base branch.
4. **Atomic publish:** `os.replace(staging_repo, final_dir)`.
5. If *anything* fails, staging is removed; `final_dir` is untouched.

---

## Programmatic Usage

```python
from pymigbench_dl import PyMigBenchDownloader

dl = PyMigBenchDownloader(
    github_token="YOUR_TOKEN",
    output_dir="repos",     # required by CLI, default here is "repos"
    max_workers=5,
    rate_limit_delay=1.0
)

# Download a directory of YAMLs
dl.download_all("/path/to/repo-yamls", gt_patch_branch_name="gt-patch")

# Or a single YAML
dl.download_single("/path/to/migration.yaml", gt_patch_branch_name="gt-patch")
```

---

## Project Structure

```
src/pymigbench_dl/
├── __init__.py                     # exposes PyMigBenchDownloader
├── cli/
│   └── main.py                     # argparse CLI (dl-all, dl-single)
├── downloader.py                   # coordinator (thread pool, orchestration)
├── loader.py                       # reads YAMLs via pymigbench
├── providers/
│   └── github/
│       ├── __init__.py
│       ├── client.py               # GitHub API (parents, tarball download)
│       └── models.py               # CommitInfo (repo, commit_sha)
├── utils/
│   ├── __init__.py
│   ├── fs.py                       # extract_tar_top (handles GitHub top-dir)
│   ├── git.py                      # thin git wrappers (run_git, add_and_commit, etc.)
│   ├── paths.py                    # to_path
│   └── repo.py                     # transactional build: parent base + GT branch + atomic publish
└── const/
    ├── __init__.py
    └── git.py                      # defaults: branch name, commit messages, git identity
```

---
