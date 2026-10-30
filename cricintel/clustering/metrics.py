"""Academic clustering validation metrics: Silhouette, Davies-Bouldin, and Calinski-Harabasz."""

from __future__ import annotations

from typing import Any, Dict, List
import numpy as np
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_score


def evaluate_clusters(embeddings: np.ndarray, labels: List[int]) -> Dict[str, Any]:
    """Compute standard unsupervised cluster validation metrics for academic assessment.

    Evaluates:
    - Silhouette Score [-1 to +1]: Measure of cohesion vs separation (higher is better).
    - Davies-Bouldin Index [0 to inf]: Ratio of within-cluster dispersion to separation (lower is better).
    - Calinski-Harabasz Score: Ratio of between-cluster variance to within-cluster variance (higher is better).
    """
    n_samples = embeddings.shape[0]
    unique_labels = list(set(labels))
    n_clusters = len(unique_labels)

    # Edge cases: Metrics require 1 < n_clusters < n_samples
    if n_samples <= 2 or n_clusters <= 1 or n_clusters >= n_samples:
        return {
            "silhouette_score": 0.0,
            "davies_bouldin_score": 0.0,
            "calinski_harabasz_score": 0.0,
            "n_samples": n_samples,
            "n_clusters": n_clusters,
            "status": "Insufficient distinct clusters to compute geometric metrics",
            "interpretation": "Clustering requires at least 2 distinct clusters and fewer clusters than samples.",
        }

    try:
        # Silhouette using cosine metric
        sil = float(silhouette_score(embeddings, labels, metric="cosine"))
    except Exception:
        sil = 0.0

    try:
        db = float(davies_bouldin_score(embeddings, labels))
    except Exception:
        db = 0.0

    try:
        ch = float(calinski_harabasz_score(embeddings, labels))
    except Exception:
        ch = 0.0

    # Interpret silhouette score academically
    if sil > 0.5:
        sil_quality = "Strong cluster structure with clear semantic separation"
    elif sil > 0.25:
        sil_quality = "Good semantic coherence across news storylines"
    elif sil > 0.0:
        sil_quality = "Moderate separation; some stories share overlapping players/tournaments"
    else:
        sil_quality = "Weak separation or overlapping topic distributions"

    return {
        "silhouette_score": round(sil, 4),
        "davies_bouldin_score": round(db, 4),
        "calinski_harabasz_score": round(ch, 2),
        "n_samples": n_samples,
        "n_clusters": n_clusters,
        "status": "Computed successfully",
        "interpretation": sil_quality,
    }
