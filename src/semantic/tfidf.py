from typing import Dict, List, Tuple, Optional, Any

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfTransformer, TfidfVectorizer

from src.config import TFIDF_TOKEN_PATTERN, TFIDF_MIN_DF


def build_tfidf_from_documents(
    class_docs: Dict[str, List[str]],
    class_names: List[str]
):
    """
    Long-format path: build TF-IDF from reconstructed documents.
    Returns (tfidf_matrix, vectorizer).
    """
    documents = [" ".join(class_docs[c]) for c in class_names]

    vectorizer = TfidfVectorizer(
        lowercase=True,
        token_pattern=TFIDF_TOKEN_PATTERN,
        min_df=TFIDF_MIN_DF
    )
    tfidf_matrix = vectorizer.fit_transform(documents)
    return tfidf_matrix, vectorizer


def build_tfidf_from_counts_wide(
    semantic_df: pd.DataFrame,
    class_names: List[str]
):
    """
    Wide-format path: semantic_df is a term-frequency matrix:
      - columns are class names
      - rows are terms (index may or may not contain term strings)
      - values are counts

    We compute TF-IDF directly from counts (no vocabulary strings needed).
    Returns (tfidf_matrix, transformer).
    """
    # Align to your class universe; missing classes get all-zero columns
    aligned = semantic_df.reindex(columns=class_names, fill_value=0)

    # counts matrix as (n_classes, n_terms)
    X_counts = aligned.to_numpy(dtype=float).T
    X_counts = np.nan_to_num(X_counts, nan=0.0, posinf=0.0, neginf=0.0)

    transformer = TfidfTransformer(
        norm="l2",
        use_idf=True,
        smooth_idf=True,
        sublinear_tf=False
    )

    tfidf_matrix = transformer.fit_transform(csr_matrix(X_counts))
    return tfidf_matrix, transformer
