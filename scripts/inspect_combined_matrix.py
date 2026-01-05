import argparse
from pathlib import Path
import numpy as np
import pandas as pd


def summarize_matrix(df: pd.DataFrame, top_k_pairs: int = 15, top_k_per_class: int = 5) -> None:
    # Basic checks
    n = df.shape[0]
    print("=" * 80)
    print("COMBINED SCORE MATRIX INSPECTOR")
    print("=" * 80)
    print(f"Shape              : {df.shape}")
    print(f"Row labels present : {df.index.is_unique and df.index.dtype == object}")
    print(f"Col labels present : {df.columns.is_unique and df.columns.dtype == object}")
    print(f"Symmetric?         : {np.allclose(df.to_numpy(), df.to_numpy().T, atol=1e-9)}")
    print(f"Diagonal all 1?    : {np.allclose(np.diag(df.to_numpy()), 1.0, atol=1e-12)}")

    # Numeric stats
    M = df.to_numpy(dtype=float)
    diag = np.diag(M)
    off = M[~np.eye(n, dtype=bool)]

    print("-" * 80)
    print("NUMERIC SUMMARY")
    print("-" * 80)
    print(f"Min / Max (all)    : {M.min():.6f} / {M.max():.6f}")
    print(f"Mean / Std (all)   : {M.mean():.6f} / {M.std():.6f}")
    print(f"Min / Max (offdiag): {off.min():.6f} / {off.max():.6f}")
    print(f"Mean (offdiag)     : {off.mean():.6f}")
    print(f"Mean (diag)        : {diag.mean():.6f}")

    # Top-k strongest pairs (excluding diagonal)
    print("-" * 80)
    print(f"TOP {top_k_pairs} STRONGEST CLASS PAIRS (excluding diagonal)")
    print("-" * 80)

    # Get upper triangle indices
    triu_i, triu_j = np.triu_indices(n, k=1)
    vals = M[triu_i, triu_j]

    if len(vals) == 0:
        print("(matrix too small)")
    else:
        k = min(top_k_pairs, len(vals))
        top_idx = np.argpartition(-vals, kth=k-1)[:k]
        top_sorted = top_idx[np.argsort(-vals[top_idx])]

        rows = df.index.to_list()
        cols = df.columns.to_list()

        for rank, idx in enumerate(top_sorted, start=1):
            i = triu_i[idx]
            j = triu_j[idx]
            print(f"{rank:>2}. {rows[i]}  <->  {cols[j]}   score={M[i, j]:.6f}")

    # Per-class top neighbors
    print("-" * 80)
    print(f"TOP {top_k_per_class} NEIGHBORS PER CLASS (first 10 classes)")
    print("-" * 80)

    rows = df.index.to_list()
    for i in range(min(10, n)):
        sims = M[i].copy()
        sims[i] = -1  # exclude self
        k = min(top_k_per_class, n - 1)
        nn_idx = np.argpartition(-sims, kth=k-1)[:k]
        nn_sorted = nn_idx[np.argsort(-sims[nn_idx])]

        items = [f"{rows[j]}({M[i,j]:.4f})" for j in nn_sorted]
        print(f"- {rows[i]}:")
        print(f"  {', '.join(items)}")


def main():
    parser = argparse.ArgumentParser(description="Inspect combined_score_matrix.parquet and log stats to terminal.")
    parser.add_argument(
        "--repo",
        required=True,
        help="Repo name under outputs/ (e.g., jpetstore-6)"
    )
    parser.add_argument(
        "--outputs-root",
        default="outputs",
        help="Outputs root folder (default: outputs)"
    )
    parser.add_argument(
        "--top-pairs",
        type=int,
        default=15,
        help="Top strongest pairs to show (default: 15)"
    )
    parser.add_argument(
        "--top-neighbors",
        type=int,
        default=5,
        help="Top neighbors per class to show (default: 5)"
    )
    args = parser.parse_args()

    path = Path(args.outputs_root) / args.repo / "combined_score_matrix.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Not found: {path}")

    df = pd.read_parquet(path)

    # Ensure index/cols are strings
    df.index = df.index.map(str)
    df.columns = df.columns.map(str)

    summarize_matrix(df, top_k_pairs=args.top_pairs, top_k_per_class=args.top_neighbors)


if __name__ == "__main__":
    main()
