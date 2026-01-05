from typing import Dict, List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from src.config import TFIDF_TOKEN_PATTERN, TFIDF_MIN_DF


def build_tfidf_matrix(
    class_docs: Dict[str, List[str]],
    class_names: List[str]
):
    documents = [
        " ".join(class_docs[c]) for c in class_names
    ]

    vectorizer = TfidfVectorizer(
        lowercase=True,
        token_pattern=TFIDF_TOKEN_PATTERN,
        min_df=TFIDF_MIN_DF
    )

    tfidf_matrix = vectorizer.fit_transform(documents)
    return tfidf_matrix, vectorizer
