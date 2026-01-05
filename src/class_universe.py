import json
from pathlib import Path
from typing import List, Set
from src.config import STATIC_DIR, TYPE_DATA_FILE, EXCLUDE_TEST_CLASSES


def _is_test_class(class_name: str) -> bool:
    return (
        ".test." in class_name.lower()
        or class_name.endswith("Test")
    )


def load_class_universe(repo_path: Path) -> List[str]:
    type_data_path = repo_path / STATIC_DIR / TYPE_DATA_FILE

    if not type_data_path.exists():
        raise FileNotFoundError(f"Missing typeData.json in {repo_path.name}")

    type_data = json.load(open(type_data_path))

    classes: Set[str] = set()

    for t in type_data:
        if t.get("isAnonymous") or t.get("isImplicit"):
            continue

        class_name = t.get("fullName")
        if not class_name:
            continue

        if EXCLUDE_TEST_CLASSES and _is_test_class(class_name):
            continue

        classes.add(class_name)

    return sorted(classes)
