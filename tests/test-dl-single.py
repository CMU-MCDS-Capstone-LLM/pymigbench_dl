from pymigbench_dl import PyMigBenchDownloader
import os
import logging

lvl = logging.DEBUG
logging.basicConfig(level=lvl, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

github_token = os.getenv("GITHUB_TOKEN")
output_dir = "tests/dl-single/output"
yaml_file_path = "tests/dl-single/data/repo-yamls/mig.yaml"

downloader = PyMigBenchDownloader(github_token=github_token, output_dir=output_dir)

downloader.download_single(yaml_file_path)
