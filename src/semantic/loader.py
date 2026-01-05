import pandas as pd
from pathlib import Path
from src.config import SEMANTIC_DIR, SEMANTIC_PARQUET


def load_semantic_dataframe(repo_path: Path) -> pd.DataFrame:
    parquet_path = repo_path / SEMANTIC_DIR / SEMANTIC_PARQUET

    if not parquet_path.exists():
        raise FileNotFoundError(f"Missing semantic parquet in {repo_path.name}")

    return pd.read_parquet(parquet_path)
