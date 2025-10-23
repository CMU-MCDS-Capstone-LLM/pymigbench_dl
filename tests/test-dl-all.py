from pymigbench_dl import PyMigBenchDownloader
import os
import logging
from pathlib import Path

lvl = logging.DEBUG

# Configure logging to write to both console and file
log_file = Path("tests/dl-all/output/download.log")
log_file.parent.mkdir(parents=True, exist_ok=True)  # Ensure directory exists

handlers = [
    logging.StreamHandler(),  # Console
    logging.FileHandler(log_file)  # File
]

logging.basicConfig(
    level=lvl,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=handlers
)

github_token = os.getenv("GITHUB_TOKEN")
output_dir = "tests/dl-all/output"
yaml_root_path = "tests/dl-all/data/repo-yamls/"

downloader = PyMigBenchDownloader(github_token=github_token, output_dir=output_dir)

downloader.download_all(yaml_root_path)
