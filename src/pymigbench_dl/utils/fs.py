import tarfile
from pathlib import Path

def extract_tar_top(tar_path: Path, extract_to: Path) -> Path:
    with tarfile.open(tar_path, "r:gz") as tf:
        tf.extractall(extract_to)
    subdirs = [d for d in extract_to.iterdir() if d.is_dir()]
    if len(subdirs) != 1:
        raise RuntimeError(f"Expected exactly 1 subdir in {tar_path}, found {len(subdirs)}")
    return subdirs[0]
