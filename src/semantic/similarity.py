import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


def compute_semantic_similarity(tfidf_matrix) -> np.ndarray:
    """
    Cosine similarity of class vectors.
    Handles zero vectors by forcing diagonal to 1.0 (self-similarity).
    Returns an NxN matrix.
    """
    sim = cosine_similarity(tfidf_matrix)

    # numerical safety clamp
    sim[sim < 0] = 0.0
    sim[sim > 1] = 1.0

    # Force self-similarity to 1.0 even for zero vectors
    np.fill_diagonal(sim, 1.0)

    return sim
