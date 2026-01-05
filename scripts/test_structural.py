import logging
import numpy as np

from src.repo_discovery import discover_repos
from src.class_universe import load_class_universe
from src.structural.loader import load_structural_dataframe
from src.structural.similarity import compute_structural_similarity_from_matrix
from src.utils.logging import setup_logging
from src.config import OUTPUTS_ROOT
from src.utils.artifacts import save_numpy


def main():
    logger = setup_logging(level=logging.INFO, log_file=OUTPUTS_ROOT / "run_logs" / "structural_run.log")
    repos = discover_repos()

    for repo in repos:
        logger.info(f"\n▶ Running structural pipeline for: {repo.name}")

        class_names = load_class_universe(repo)
        df = load_structural_dataframe(repo)

        logger.info(f"[{repo.name}] Structural matrix shape: {df.shape}")
        logger.info(f"[{repo.name}] Structural nonzeros: {(df.to_numpy()!=0).sum()}")

        sim_str = compute_structural_similarity_from_matrix(df, class_names)

        logger.info(f"[{repo.name}] Sim_str shape: {sim_str.shape} | diag mean: {float(np.mean(np.diag(sim_str))):.3f}")

        out_dir = OUTPUTS_ROOT / repo.name / "structural"
        save_numpy(out_dir / "sim_str.npy", sim_str)
        logger.info(f"[{repo.name}] Saved: {out_dir / 'sim_str.npy'}")

        assert sim_str.shape == (len(class_names), len(class_names))
        assert np.allclose(np.diag(sim_str), 1.0, atol=1e-12)

        logger.info(f"✔ Structural analysis OK for {repo.name}")


if __name__ == "__main__":
    main()
