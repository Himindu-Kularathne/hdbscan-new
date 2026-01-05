import argparse
from pathlib import Path
import json
import numpy as np
import pandas as pd

import hdbscan


def cluster_summary(labels, class_names):
    clusters = {}
    for cname, lab in zip(class_names, labels):
        if lab == -1:
            continue
        clusters.setdefault(int(lab), []).append(cname)

    noise = [cname for cname, lab in zip(class_names, labels) if lab == -1]

    # Sort clusters by size desc
    ordered = sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True)
    return ordered, noise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="repo name under outputs/, e.g., jpetstore-6")
    parser.add_argument("--outputs-root", default="outputs")
    parser.add_argument("--min-cluster-size", type=int, default=2)
    parser.add_argument("--min-samples", type=int, default=None)
    args = parser.parse_args()

    out_dir = Path(args.outputs_root) / args.repo

    dist_path = out_dir / "combined_distance_matrix.npy"
    score_path = out_dir / "combined_score_matrix.parquet"

    if not dist_path.exists():
        raise FileNotFoundError(f"Missing: {dist_path}")
    if not score_path.exists():
        raise FileNotFoundError(f"Missing: {score_path}")

    # Load class names from parquet labels (best source)
    df_score = pd.read_parquet(score_path)
    class_names = df_score.index.map(str).tolist()

    dist = np.load(dist_path)

    if dist.shape[0] != dist.shape[1]:
        raise ValueError(f"Distance matrix must be square, got {dist.shape}")
    if dist.shape[0] != len(class_names):
        raise ValueError(f"Class count mismatch: dist={dist.shape[0]} vs class_names={len(class_names)}")

    # HDBSCAN with precomputed distances
    clusterer = hdbscan.HDBSCAN(
        metric="precomputed",
        min_cluster_size=args.min_cluster_size,
        min_samples=args.min_samples,
    )

    labels = clusterer.fit_predict(dist)

    ordered_clusters, noise = cluster_summary(labels, class_names)

    # Print structured summary
    print("=" * 80)
    print(f"HDBSCAN RESULTS | repo={args.repo}")
    print("=" * 80)
    n_clusters = len(ordered_clusters)
    print(f"min_cluster_size: {args.min_cluster_size}")
    print(f"min_samples     : {args.min_samples}")
    print(f"classes         : {len(class_names)}")
    print(f"clusters        : {n_clusters}")
    print(f"noise (-1)      : {len(noise)}")
    print("-" * 80)

    for cid, members in ordered_clusters:
        print(f"Cluster {cid} | size={len(members)}")
        for m in members:
            print(f"  - {m}")
        print("-" * 80)

    if noise:
        print("NOISE / OUTLIERS (-1)")
        for m in noise:
            print(f"  - {m}")

    # Save outputs
    clusters_json = {
        "repo": args.repo,
        "params": {
            "min_cluster_size": args.min_cluster_size,
            "min_samples": args.min_samples,
            "metric": "precomputed",
        },
        "clusters": {str(cid): members for cid, members in ordered_clusters},
        "noise": noise,
    }

    (out_dir / "hdbscan_clusters.json").write_text(json.dumps(clusters_json, indent=2), encoding="utf-8")

    # Also save label table
    df_labels = pd.DataFrame({"class_name": class_names, "cluster": labels})
    df_labels.to_csv(out_dir / "hdbscan_labels.csv", index=False)

    print(f"\nSaved: {out_dir / 'hdbscan_clusters.json'}")
    print(f"Saved: {out_dir / 'hdbscan_labels.csv'}")


if __name__ == "__main__":
    main()
