from collections import defaultdict
from typing import Dict, List
import pandas as pd


def build_class_documents(
    semantic_df: pd.DataFrame,
    class_names: List[str]
) -> Dict[str, List[str]]:
    """
    Build per-class token lists from semantic word counts.

    Supports two schema styles:

    (A) Long format:
        columns: ['class_name' or 'class', 'word', 'count']
        each row = (class, word, count)

    (B) Wide matrix format:
        columns = class names, index = words, values = counts
        each cell = count(word in class)
    """
    valid_classes = set(class_names)
    docs = defaultdict(list)

    cols = set(semantic_df.columns)

    # ---------- Case A: long format ----------
    long_class_cols = [c for c in ["class_name", "class", "fullName", "classname"] if c in cols]
    if long_class_cols and "word" in cols and "count" in cols:
        class_col = long_class_cols[0]

        for row in semantic_df.itertuples(index=False):
            c = getattr(row, class_col)
            if c in valid_classes:
                w = row.word
                n = int(row.count) if row.count is not None else 0
                if n > 0:
                    docs[c].extend([str(w)] * n)

        for c in class_names:
            docs.setdefault(c, [])
        return docs

    # ---------- Case B: wide matrix format ----------
    # Decide if classes are in columns or in index.
    col_matches = len(set(map(str, semantic_df.columns)) & valid_classes)
    idx_matches = len(set(map(str, semantic_df.index)) & valid_classes)

    if col_matches == 0 and idx_matches == 0:
        raise ValueError(
            "Semantic parquet schema not recognized.\n"
            f"Columns sample: {list(semantic_df.columns)[:10]}\n"
            f"Index sample: {list(map(str, semantic_df.index[:10]))}\n"
            "Expected either long format (class_name, word, count) "
            "or wide format (classes in columns or index)."
        )

    # B1: classes are columns, words are index
    if col_matches >= idx_matches:
        # words live in index
        words = [str(w) for w in semantic_df.index]

        for c in (set(semantic_df.columns) & valid_classes):
            series = semantic_df[c]
            # iterate only non-zero / non-null counts
            for w, n in zip(words, series.tolist()):
                if n is None:
                    continue
                try:
                    n_int = int(n)
                except Exception:
                    continue
                if n_int > 0:
                    docs[c].extend([w] * n_int)

    # B2: classes are index, words are columns (transpose case)
    else:
        words = [str(w) for w in semantic_df.columns]
        for c in (set(map(str, semantic_df.index)) & valid_classes):
            row = semantic_df.loc[c]
            for w, n in zip(words, row.tolist()):
                if n is None:
                    continue
                try:
                    n_int = int(n)
                except Exception:
                    continue
                if n_int > 0:
                    docs[c].extend([w] * n_int)

    for c in class_names:
        docs.setdefault(c, [])

    return docs
