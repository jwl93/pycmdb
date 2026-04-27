"""pycmdb - Git-based CMDB"""
import os
from pathlib import Path


def get_cmdb_root() -> Path:
    """Get CMDB root directory from CMDB_ROOT env var, default current directory."""
    return Path(os.environ.get("CMDB_ROOT", "."))
