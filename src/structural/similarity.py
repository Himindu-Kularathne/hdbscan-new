import numpy as np
import pandas as pd
from typing import List


def compute_structural_similarity_from_matrix(
    structural_df: pd.DataFrame,
    class_names: List[str],
) -> np.ndarray:
    """
    structural_df: adjacency matrix with columns=class names, rows unlabeled (0..N-1)
    We assume row order == column order, then align to class_names.
    """
    A = structural_df.copy()

    # Label rows to match columns (since index is 0..N-1)
    if isinstance(A.index, pd.RangeIndex) or list(A.index[:3]) == [0, 1, 2]:
        A.index = list(A.columns)

    # Align to class universe (adds missing with 0)
    A = A.reindex(index=class_names, columns=class_names, fill_value=0.0)

    # numeric
    M = A.to_numpy(dtype=float)
    M = np.nan_to_num(M, nan=0.0, posinf=0.0, neginf=0.0)

    # incoming sums
    calls_in = M.sum(axis=0)  # column sums
    N = len(class_names)

    sim = np.zeros((N, N), dtype=float)

    for i in range(N):
        for j in range(N):
            if i == j:
                continue

            in_i = calls_in[i]
            in_j = calls_in[j]

            if in_i > 0 and in_j > 0:
                sim[i, j] = 0.5 * ((M[i, j] / in_j) + (M[j, i] / in_i))
            elif in_i == 0 and in_j > 0:
                sim[i, j] = M[i, j] / in_j
            elif in_j == 0 and in_i > 0:
                sim[i, j] = M[j, i] / in_i
            else:
                sim[i, j] = 0.0

    np.fill_diagonal(sim, 1.0)
    sim = np.clip(sim, 0.0, 1.0)
    return sim
