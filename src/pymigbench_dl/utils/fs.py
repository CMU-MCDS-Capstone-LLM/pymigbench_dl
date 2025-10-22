from pathlib import Path
import zipfile

def extract_zip_flat(zip_path: Path, extract_to: Path):
    """
    Extract a zip file without creating a new folder
    
    Args:
        zip_path: Path to the zip file
        extract_to: Directory to extract to
    """
    try:
        # Extract zip to target directory
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)

        # Find the single subdirectory GitHub created
        subdirs = [d for d in extract_to.iterdir() if d.is_dir()]
        if len(subdirs) != 1:
            raise Exception(f"Expected exactly 1 subdirectory in {zip_path}, found {len(subdirs)}")
        
        return subdirs[0]
    finally:
        try:
            zip_path.unlink(missing_ok=True)
        except Exception:
            pass
