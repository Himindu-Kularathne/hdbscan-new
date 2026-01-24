from pathlib import Path
from typing import List
from src.config import DATA_ROOT, TARGET_REPO

def discover_repos() -> List[Path]:
    if not DATA_ROOT.exists():
        raise FileNotFoundError(f"Monolithic data folder not found: {DATA_ROOT}")

    if TARGET_REPO:
        repo = DATA_ROOT / TARGET_REPO
        if not repo.exists():
            raise FileNotFoundError(f"Repo not found: {TARGET_REPO}")
        return [repo]

    return sorted(p for p in DATA_ROOT.iterdir() if p.is_dir())
