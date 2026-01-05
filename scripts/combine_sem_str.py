import logging
import numpy as np
import pandas as pd

from src.repo_discovery import discover_repos
from src.utils.logging import setup_logging
from src.config import OUTPUTS_ROOT, ALPHA_STRUCTURAL
from src.utils.artifacts import save_numpy, save_json

from src.pipeline.semantic_pipeline import run_semantic_pipeline
from src.structural.loader import load_structural_dataframe
from src.structural.similarity import compute_structural_similarity_from_matrix

from src.combine_similarity import combine_similarities, similarity_to_distance


def main():
    logger = setup_logging(
        level=logging.INFO,
        log_file=OUTPUTS_ROOT / "run_logs" / "combine_run.log"
    )

    repos = discover_repos()

    for repo in repos:
        repo_name = repo.name
        logger.info(f"\n▶ Combining semantic + structural similarities for: {repo_name}")

        # ----------------------------
        # 1) Semantic similarity
        # ----------------------------
        sem_result = run_semantic_pipeline(repo, logger=logger)
        sim_sem = sem_result["semantic_similarity"]
        class_names = sem_result["class_names"]

        logger.info(f"[{repo_name}] Sim_sem shape: {sim_sem.shape}")

        # ----------------------------
        # 2) Structural similarity
        # ----------------------------
        str_df = load_structural_dataframe(repo)  # reads class_interactions.parquet
        sim_str = compute_structural_similarity_from_matrix(str_df, class_names)

        logger.info(f"[{repo_name}] Sim_str shape: {sim_str.shape}")

        # ----------------------------
        # 3) Combine
        # ----------------------------
        sim_comb, report = combine_similarities(sim_str, sim_sem, alpha=ALPHA_STRUCTURAL)
        dist_comb = similarity_to_distance(sim_comb)

        logger.info(
            f"[{repo_name}] alpha={report.alpha} | shape={report.shape} | "
            f"sem_minmax={report.sem_minmax} | str_minmax={report.str_minmax} | comb_minmax={report.comb_minmax}"
        )

        # ----------------------------
        # 4) Save outputs in outputs/<repo>/
        # ----------------------------
        out_dir = OUTPUTS_ROOT / repo_name
        save_numpy(out_dir / "combined_score_matrix.npy", sim_comb)
        save_numpy(out_dir / "combined_distance_matrix.npy", dist_comb)

        # Optional: save labeled parquet (super useful for inspection)
        df_comb = pd.DataFrame(sim_comb, index=class_names, columns=class_names)
        df_comb.to_parquet(out_dir / "combined_score_matrix.parquet")

        save_json(out_dir / "combined_meta.json", {
            "repo": repo_name,
            "alpha": report.alpha,
            "shape": list(report.shape),
            "sem_minmax": list(report.sem_minmax),
            "str_minmax": list(report.str_minmax),
            "comb_minmax": list(report.comb_minmax),
        })

        # Sanity checks
        assert sim_comb.shape == (len(class_names), len(class_names))
        assert np.allclose(np.diag(sim_comb), 1.0, atol=1e-12)
        assert np.allclose(np.diag(dist_comb), 0.0, atol=1e-12)

        logger.info(f"[{repo_name}] Saved combined matrices to: {out_dir}")
        logger.info(f"[{repo_name}] ✔ Combine OK")


if __name__ == "__main__":
    main()
