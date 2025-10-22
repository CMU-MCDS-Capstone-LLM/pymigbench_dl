from pathlib import Path
import os

def to_path(p: str, check_exists=False) -> Path:
    """
    Safely convert a possibly-relative, user/env-containing path string to an absolute Path.

    E.g. 
    (assume pwd = /home/user/projects, home dir is /home/user)
    ~/projects => /home/user/projects
    ./src/utils/ => /home/user/projects/src/utils
    $HOME/projects => /home/user/projects

    Args:
        p: Path as a string.
        check_exists: If true, check if path exists, and raise FileNotFoundError if not
    """
    expanded = os.path.expanduser(os.path.expandvars(p))
    return Path(expanded).resolve(check_exists)
