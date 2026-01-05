from pathlib import Path
import pandas as pd


def load_structural_dataframe(repo_path: Path) -> pd.DataFrame:
    path = repo_path / "structural_data" / "class_interactions.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Missing structural parquet: {path}")
    return pd.read_parquet(path)
