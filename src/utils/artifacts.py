import json
from pathlib import Path
from typing import Any, Dict, List

import numpy as np


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def save_json(path: Path, obj: Any) -> None:
    ensure_dir(path.parent)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)


def save_numpy(path: Path, arr: np.ndarray) -> None:
    ensure_dir(path.parent)
    np.save(path, arr)


def save_text(path: Path, lines: List[str]) -> None:
    ensure_dir(path.parent)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
