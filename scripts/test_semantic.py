from pathlib import Path
import logging

from src.repo_discovery import discover_repos
from src.pipeline.semantic_pipeline import run_semantic_pipeline
from src.utils.logging import setup_logging
from src.config import OUTPUTS_ROOT


def main():
    logger = setup_logging(
        level=logging.INFO,
        log_file=OUTPUTS_ROOT / "run_logs" / "semantic_run.log"
    )

    repos = discover_repos()

    for repo in repos:
        logger.info(f"\n▶ Running semantic pipeline for: {repo.name}")
        result = run_semantic_pipeline(repo, logger=logger)

        sim = result["semantic_similarity"]
        assert sim.shape[0] == sim.shape[1]
        assert sim.shape[0] == len(result["class_names"])
        assert (sim.diagonal() == 1.0).all()

        logger.info(f"✔ Semantic analysis OK for {repo.name}")


if __name__ == "__main__":
    main()
