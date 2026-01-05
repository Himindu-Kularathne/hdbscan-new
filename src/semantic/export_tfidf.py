from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix


@dataclass
class ClassTfidfRow:
    class_name: str
    top_terms: List[Tuple[str, float]]  # (term, score)


def _get_row_sparse(X, i: int) -> csr_matrix:
    # X is sparse
    return X[i]  # 1 x vocab


def _topk_from_sparse_row(row: csr_matrix, feature_names: List[str], k: int) -> List[Tuple[str, float]]:
    if row.nnz == 0:
        return []
    # row is 1 x V
    idx = row.indices
    data = row.data
    if len(data) <= k:
        order = np.argsort(-data)
    else:
        # partial top-k
        top_idx = np.argpartition(-data, kth=k-1)[:k]
        order = top_idx[np.argsort(-data[top_idx])]

    return [(feature_names[idx[j]], float(data[j])) for j in order]


def export_top_tfidf_per_class(
    tfidf_matrix,
    class_names: List[str],
    semantic_model: Any,
    *,
    format_kind: str,                # "LONG" or "WIDE"
    semantic_df: Optional[pd.DataFrame] = None,   # required for WIDE if you want term names
    top_k: int = 25
) -> List[ClassTfidfRow]:
    """
    Returns a list of per-class top-k TF-IDF terms.

    LONG:
      - semantic_model is a TfidfVectorizer
      - feature names come from vectorizer.get_feature_names_out()

    WIDE:
      - semantic_model is a TfidfTransformer
      - feature names must come from semantic_df.index (terms)
        If semantic_df.index isn't string terms, we fall back to feature_i names.
    """
    X = tfidf_matrix  # sparse (n_classes x vocab)

    if format_kind.upper() == "LONG":
        feature_names = list(semantic_model.get_feature_names_out())

    elif format_kind.upper() == "WIDE":
        if semantic_df is None:
            raise ValueError("semantic_df is required for WIDE to recover term names")

        # In WIDE: we built counts matrix as aligned.to_numpy().T
        # aligned shape: (n_terms, n_classes)
        # So vocabulary size == number of rows (terms)
        if semantic_df.index is not None and len(semantic_df.index) == X.shape[1]:
            # use index values as term names
            feature_names = [str(t) for t in semantic_df.index]
        else:
            feature_names = [f"feature_{i}" for i in range(X.shape[1])]

    else:
        raise ValueError(f"Unknown format_kind: {format_kind}")

    rows: List[ClassTfidfRow] = []
    for i, cname in enumerate(class_names):
        row = _get_row_sparse(X, i)
        top_terms = _topk_from_sparse_row(row, feature_names, top_k)
        rows.append(ClassTfidfRow(class_name=cname, top_terms=top_terms))

    return rows


def save_top_tfidf_json(out_path: Path, rows: List[ClassTfidfRow]) -> None:
    import json
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        r.class_name: [{"term": t, "score": s} for t, s in r.top_terms]
        for r in rows
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
