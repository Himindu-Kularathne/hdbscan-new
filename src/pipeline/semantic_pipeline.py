from pathlib import Path
from typing import Dict
import time

import numpy as np

from src.class_universe import load_class_universe
from src.semantic.loader import load_semantic_dataframe
from src.semantic.documents import build_class_documents
from src.semantic.tfidf import build_tfidf_matrix
from src.semantic.similarity import compute_semantic_similarity
from src.config import OUTPUTS_ROOT, SAVE_INTERMEDIATE
from src.utils.artifacts import save_json, save_numpy, save_text


def run_semantic_pipeline(repo_path: Path, logger=None) -> Dict:
    t0 = time.time()
    repo_name = repo_path.name

    def log(msg: str):
        if logger:
            logger.info(msg)
        else:
            print(msg)

    log(f"[{repo_name}] STEP 1: Loading class universe...")
    class_names = load_class_universe(repo_path)
    class_index = {c: i for i, c in enumerate(class_names)}
    log(f"[{repo_name}] Classes loaded: {len(class_names)}")

    log(f"[{repo_name}] STEP 2: Loading semantic parquet...")
    semantic_df = load_semantic_dataframe(repo_path)
    log(f"[{repo_name}] Semantic rows: {len(semantic_df)} | cols: {list(semantic_df.columns)}")

    log(f"[{repo_name}] Building class documents...")
    class_docs = build_class_documents(semantic_df, class_names)

    empty_docs = sum(1 for c in class_names if len(class_docs.get(c, [])) == 0)
    log(f"[{repo_name}] Empty class documents: {empty_docs}/{len(class_names)}")

    log(f"[{repo_name}] Building TF-IDF matrix...")
    tfidf_matrix, vectorizer = build_tfidf_matrix(class_docs, class_names)
    log(f"[{repo_name}] TF-IDF shape: {tfidf_matrix.shape} | vocab size: {len(vectorizer.vocabulary_)}")

    # quick vocab peek
    top_terms = sorted(vectorizer.vocabulary_.items(), key=lambda x: x[1])[:20]
    log(f"[{repo_name}] Sample vocab terms: {[t for t, _ in top_terms[:10]]}")

    log(f"[{repo_name}] Computing semantic similarity (cosine)...")
    sim_sem = compute_semantic_similarity(tfidf_matrix)
    log(f"[{repo_name}] Sim_sem shape: {sim_sem.shape} | diag mean: {np.mean(np.diag(sim_sem)):.3f}")

    # Save intermediates
    if SAVE_INTERMEDIATE:
        out_dir = OUTPUTS_ROOT / repo_name / "semantic"
        save_text(out_dir / "class_names.txt", class_names)
        save_json(out_dir / "meta.json", {
            "repo": repo_name,
            "num_classes": len(class_names),
            "tfidf_shape": list(tfidf_matrix.shape),
            "vocab_size": len(vectorizer.vocabulary_),
            "empty_docs": empty_docs
        })
        save_numpy(out_dir / "sim_sem.npy", sim_sem)
        log(f"[{repo_name}] Saved intermediates to: {out_dir}")

    log(f"[{repo_name}] DONE semantic pipeline in {time.time() - t0:.2f}s")

    return {
        "repo": repo_name,
        "class_names": class_names,
        "class_index": class_index,
        "tfidf": tfidf_matrix,
        "semantic_similarity": sim_sem,
        "vectorizer": vectorizer,
    }
