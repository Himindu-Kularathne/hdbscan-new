from pathlib import Path
from typing import Dict

from src.class_universe import load_class_universe
from src.semantic.loader import load_semantic_dataframe
from src.semantic.documents import build_class_documents
from src.semantic.tfidf import build_tfidf_matrix
from src.semantic.similarity import compute_semantic_similarity


def run_semantic_pipeline(repo_path: Path) -> Dict:
    # STEP 1 — class universe
    class_names = load_class_universe(repo_path)
    class_index = {c: i for i, c in enumerate(class_names)}

    # STEP 2 — semantic analysis
    semantic_df = load_semantic_dataframe(repo_path)
    class_docs = build_class_documents(semantic_df, class_names)
    tfidf_matrix, vectorizer = build_tfidf_matrix(class_docs, class_names)
    sim_sem = compute_semantic_similarity(tfidf_matrix)

    return {
        "repo": repo_path.name,
        "class_names": class_names,
        "class_index": class_index,
        "tfidf": tfidf_matrix,
        "semantic_similarity": sim_sem,
        "vectorizer": vectorizer,
    }
