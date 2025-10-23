from pymigbench_dl import PyMigBenchDownloader
import os
import logging

lvl = logging.DEBUG
logging.basicConfig(level=lvl, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

github_token = os.getenv("GITHUB_TOKEN")
output_dir = "tests/dl-all/output"
yaml_root_path = "tests/dl-all/data/repo-yamls/"

downloader = PyMigBenchDownloader(github_token=github_token, output_dir=output_dir)

downloader.download_all(yaml_root_path)
