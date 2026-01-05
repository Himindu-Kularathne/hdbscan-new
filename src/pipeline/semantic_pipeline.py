from pathlib import Path
from typing import Dict, Optional, List, Tuple
import time
import json

import numpy as np

from src.class_universe import load_class_universe
from src.semantic.loader import load_semantic_dataframe
from src.semantic.documents import build_class_documents
from src.semantic.tfidf import build_tfidf_from_documents, build_tfidf_from_counts_wide
from src.semantic.similarity import compute_semantic_similarity

from src.config import OUTPUTS_ROOT, SAVE_INTERMEDIATE
from src.utils.artifacts import save_json, save_numpy, save_text


def _get_feature_names_for_tfidf(
    *,
    semantic_format: str,
    semantic_model,
    semantic_df,
    vocab_size: int
) -> List[str]:
    """
    Return feature names for TF-IDF columns.
    - LONG: vectorizer provides feature names
    - WIDE: prefer semantic_df.index as term names; fallback to feature_i
    """
    if semantic_format == "LONG":
        return list(semantic_model.get_feature_names_out())

    # WIDE
    if semantic_df is not None and semantic_df.index is not None and len(semantic_df.index) == vocab_size:
        # if index contains meaningful tokens/terms, use them
        return [str(x) for x in semantic_df.index]

    return [f"feature_{i}" for i in range(vocab_size)]


def _topk_tfidf_for_class(
    tfidf_matrix,
    class_idx: int,
    feature_names: List[str],
    k: int = 10
) -> List[Tuple[str, float]]:
    """
    Return top-k (term, score) for a given class row in a sparse TF-IDF matrix.
    """
    row = tfidf_matrix[class_idx]  # 1 x V sparse
    if getattr(row, "nnz", 0) == 0:
        return []

    # row.indices are column indices, row.data are values for non-zeros
    idx = row.indices
    data = row.data

    if len(data) <= k:
        order = np.argsort(-data)
        top = order
    else:
        top_idx = np.argpartition(-data, kth=k - 1)[:k]
        top = top_idx[np.argsort(-data[top_idx])]

    return [(feature_names[idx[i]], float(data[i])) for i in top]


def run_semantic_pipeline(repo_path: Path, logger: Optional[object] = None) -> Dict:
    """
    STEP 1: Load class universe (from static_analysis_results/typeData.json)
    STEP 2: Build TF-IDF vectors + semantic similarity matrix

    Supports semantic parquet in two schemas:
      - LONG: columns include [class_name/class/fullName/classname, word, count]
      - WIDE: columns are class names, rows are terms, values are counts
    """
    t0 = time.time()
    repo_name = repo_path.name

    def log(msg: str):
        if logger:
            logger.info(msg)
        else:
            print(msg)

    # -------------------------
    # STEP 1 — class universe
    # -------------------------
    log(f"[{repo_name}] STEP 1: Loading class universe...")
    class_names = load_class_universe(repo_path)
    class_index = {c: i for i, c in enumerate(class_names)}
    log(f"[{repo_name}] Classes loaded: {len(class_names)}")

    # -------------------------
    # STEP 2 — semantic parquet
    # -------------------------
    log(f"[{repo_name}] STEP 2: Loading semantic parquet...")
    semantic_df = load_semantic_dataframe(repo_path)
    log(f"[{repo_name}] Semantic rows: {len(semantic_df)} | cols: {list(semantic_df.columns)[:10]}{'...' if len(semantic_df.columns) > 10 else ''}")
    log(f"[{repo_name}] Semantic index name: {semantic_df.index.name} | index type: {type(semantic_df.index)}")

    # Detect schema
    cols = set(map(str, semantic_df.columns))
    is_long = (
        ("word" in cols) and ("count" in cols)
        and any(c in cols for c in ["class_name", "class", "fullName", "classname"])
    )
    is_wide = (len(cols & set(class_names)) > 0) and (not is_long)

    if not is_long and not is_wide:
        raise ValueError(
            f"[{repo_name}] Semantic parquet schema not recognized.\n"
            f"Columns sample: {list(semantic_df.columns)[:20]}\n"
            f"Index sample: {list(map(str, semantic_df.index[:20]))}\n"
            "Expected LONG (class_name/class/fullName + word + count) "
            "or WIDE (class names in columns)."
        )

    # Build TF-IDF using correct method
    if is_long:
        semantic_format = "LONG"
        log(f"[{repo_name}] Detected semantic format: LONG (class, word, count)")
        log(f"[{repo_name}] Building class documents...")
        class_docs = build_class_documents(semantic_df, class_names)

        empty_docs = sum(1 for c in class_names if len(class_docs.get(c, [])) == 0)
        log(f"[{repo_name}] Empty class documents: {empty_docs}/{len(class_names)}")

        log(f"[{repo_name}] Building TF-IDF (vectorizer)...")
        tfidf_matrix, semantic_model = build_tfidf_from_documents(class_docs, class_names)

    else:
        semantic_format = "WIDE"
        log(f"[{repo_name}] Detected semantic format: WIDE (terms x classes counts matrix)")
        empty_docs = None

        log(f"[{repo_name}] Building TF-IDF (transformer from counts)...")
        tfidf_matrix, semantic_model = build_tfidf_from_counts_wide(semantic_df, class_names)

    log(f"[{repo_name}] TF-IDF shape: {tfidf_matrix.shape}")

    # -------------------------
    # TF-IDF per-class logging
    # -------------------------
    TOP_K_TERMS = 10           # change this if you want more
    SAMPLE_CLASSES_TO_LOG = 5  # log only a few classes to keep console clean

    feature_names = _get_feature_names_for_tfidf(
        semantic_format=semantic_format,
        semantic_model=semantic_model,
        semantic_df=semantic_df if semantic_format == "WIDE" else None,
        vocab_size=tfidf_matrix.shape[1],
    )

    log(f"[{repo_name}] Extracting top-{TOP_K_TERMS} TF-IDF terms for classes...")

    # Log a few sample classes
    sample_indices = list(range(min(SAMPLE_CLASSES_TO_LOG, len(class_names))))
    for i in sample_indices:
        top_terms = _topk_tfidf_for_class(tfidf_matrix, i, feature_names, k=TOP_K_TERMS)
        if not top_terms:
            log(f"[{repo_name}] TF-IDF[{class_names[i]}] -> (no terms / zero vector)")
        else:
            compact = ", ".join([f"{t}:{s:.4f}" for t, s in top_terms[:8]])
            log(f"[{repo_name}] TF-IDF[{class_names[i]}] -> {compact}")

    # Build full per-class top-k structure (for saving)
    top_tfidf_per_class = {}
    for i, cname in enumerate(class_names):
        top_terms = _topk_tfidf_for_class(tfidf_matrix, i, feature_names, k=TOP_K_TERMS)
        top_tfidf_per_class[cname] = [{"term": t, "score": s} for t, s in top_terms]

    # Similarity
    log(f"[{repo_name}] Computing semantic similarity (cosine)...")
    sim_sem = compute_semantic_similarity(tfidf_matrix)
    log(f"[{repo_name}] Sim_sem shape: {sim_sem.shape} | diag mean: {float(np.mean(np.diag(sim_sem))):.3f}")

    # -------------------------
    # Save intermediates
    # -------------------------
    if SAVE_INTERMEDIATE:
        out_dir = OUTPUTS_ROOT / repo_name / "semantic"
        save_text(out_dir / "class_names.txt", class_names)

        meta = {
            "repo": repo_name,
            "num_classes": len(class_names),
            "tfidf_shape": list(tfidf_matrix.shape),
            "sim_sem_shape": list(sim_sem.shape),
            "semantic_format": semantic_format,
            "empty_docs": empty_docs,
            "tfidf_top_k": TOP_K_TERMS,
        }
        save_json(out_dir / "meta.json", meta)
        save_numpy(out_dir / "sim_sem.npy", sim_sem)

        # Save TF-IDF top terms per class
        out_path = out_dir / "top_tfidf_per_class.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(top_tfidf_per_class, indent=2), encoding="utf-8")

        log(f"[{repo_name}] Saved intermediates to: {out_dir}")
        log(f"[{repo_name}] Saved TF-IDF top terms per class to: {out_path}")

    log(f"[{repo_name}] DONE semantic pipeline in {time.time() - t0:.2f}s")

    return {
        "repo": repo_name,
        "class_names": class_names,
        "class_index": class_index,
        "tfidf": tfidf_matrix,
        "semantic_similarity": sim_sem,
        "semantic_model": semantic_model,  # vectorizer (LONG) or transformer (WIDE)
        "semantic_format": semantic_format,
        "top_tfidf_per_class": top_tfidf_per_class,  # top-k list per class
    }
