from collections import defaultdict
from typing import Dict, List
import pandas as pd


def _resolve_class_column(df: pd.DataFrame) -> str:
    """
    Try to infer the class-name column from common variants.
    """
    candidates = [
        "class_name",
        "class",
        "fullName",
        "classname",
        "type",
        "owner"
    ]

    for c in candidates:
        if c in df.columns:
            return c

    raise ValueError(
        f"Cannot find class column in semantic parquet. "
        f"Available columns: {list(df.columns)}"
    )


def build_class_documents(
    semantic_df: pd.DataFrame,
    class_names: List[str]
) -> Dict[str, List[str]]:

    class_col = _resolve_class_column(semantic_df)

    valid_classes = set(class_names)
    documents = defaultdict(list)

    for row in semantic_df.itertuples(index=False):
        class_name = getattr(row, class_col)

        if class_name in valid_classes:
            documents[class_name].extend(
                [row.word] * int(row.count)
            )

    # Ensure every class exists (even if empty)
    for c in class_names:
        documents.setdefault(c, [])

    return documents
