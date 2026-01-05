from collections import defaultdict
from typing import Dict, List
import pandas as pd


def build_class_documents(
    semantic_df: pd.DataFrame,
    class_names: List[str]
) -> Dict[str, List[str]]:

    valid_classes = set(class_names)
    documents = defaultdict(list)

    for row in semantic_df.itertuples(index=False):
        if row.class_name in valid_classes:
            documents[row.class_name].extend(
                [row.word] * int(row.count)
            )

    # Ensure every class exists
    for c in class_names:
        documents.setdefault(c, [])

    return documents
