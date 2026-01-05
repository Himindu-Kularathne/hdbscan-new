import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


def compute_semantic_similarity(tfidf_matrix) -> np.ndarray:
    sim = cosine_similarity(tfidf_matrix)

    # numerical safety
    sim[sim < 0] = 0.0
    sim[sim > 1] = 1.0

    return sim
