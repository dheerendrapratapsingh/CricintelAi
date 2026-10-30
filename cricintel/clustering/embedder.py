"""Semantic vector embedding generation with automatic TF-IDF + SVD fallback."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple
import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

logger = logging.getLogger(__name__)

# Cached model instance
_ST_MODEL = None
_ST_MODEL_NAME = None


def _get_sentence_transformer(model_name: str = "all-MiniLM-L6-v2"):
    global _ST_MODEL, _ST_MODEL_NAME
    if _ST_MODEL is not None and _ST_MODEL_NAME == model_name:
        return _ST_MODEL
    try:
        from sentence_transformers import SentenceTransformer
        _ST_MODEL = SentenceTransformer(model_name)
        _ST_MODEL_NAME = model_name
        return _ST_MODEL
    except Exception as e:
        logger.warning(f"Could not load SentenceTransformer ({model_name}): {e}")
        return None


def generate_tfidf_svd_embeddings(
    texts: List[str], n_components: int = 48
) -> np.ndarray:
    """Generate dense semantic vectors using TF-IDF + TruncatedSVD (LSA) with L2 normalization."""
    if not texts:
        return np.zeros((0, n_components), dtype=np.float32)

    # Clean empty strings
    clean_texts = [t.strip() if t and t.strip() else "cricket news update" for t in texts]

    # Stopwords list including domain boilerplate
    custom_stopwords = [
        "said", "told", "reporters", "also", "one", "two", "three", "first",
        "last", "new", "team", "cricket", "match", "game", "year", "series"
    ]

    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        sublinear_tf=True,
        stop_words="english",
        max_features=2500,
        min_df=1,
    )
    tfidf_matrix = vectorizer.fit_transform(clean_texts)

    n_samples, n_features = tfidf_matrix.shape
    components = max(2, min(n_components, n_samples - 1, n_features - 1))

    if components < 2 or n_samples < 3:
        # If dataset is very small, return dense TF-IDF directly
        dense = tfidf_matrix.toarray()
        return normalize(dense)

    svd = TruncatedSVD(n_components=components, random_state=42)
    dense_embeddings = svd.fit_transform(tfidf_matrix)

    # Normalize vectors to unit length so dot product == cosine similarity
    normalized = normalize(dense_embeddings, norm="l2")
    return normalized.astype(np.float32)


def generate_embeddings(
    texts: List[str],
    model_name: str = "all-MiniLM-L6-v2",
    force_fallback: bool = False,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Compute dense semantic embeddings for a list of texts.

    Tries SentenceTransformers first; if unavailable or force_fallback is True,
    falls back cleanly to TF-IDF + Latent Semantic Analysis (SVD).
    """
    if not texts:
        return np.zeros((0, 384), dtype=np.float32), {
            "model_type": "empty",
            "dimension": 0,
            "fallback_used": False,
        }

    if not force_fallback:
        st_model = _get_sentence_transformer(model_name)
        if st_model is not None:
            try:
                embeddings = st_model.encode(
                    texts,
                    show_progress_bar=False,
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                )
                return embeddings.astype(np.float32), {
                    "model_type": f"SentenceTransformer ({model_name})",
                    "dimension": int(embeddings.shape[1]),
                    "fallback_used": False,
                }
            except Exception as e:
                logger.warning(f"Error encoding with SentenceTransformer: {e}")

    # Fallback to TF-IDF + SVD
    embeddings = generate_tfidf_svd_embeddings(texts)
    return embeddings, {
        "model_type": "TF-IDF + Latent Semantic Analysis (SVD)",
        "dimension": int(embeddings.shape[1]),
        "fallback_used": True,
    }
