"""Unit and integration tests for semantic vector embeddings and clustering."""

import numpy as np
import pytest
from cricintel.clustering.clusterer import cluster_articles, derive_cluster_title
from cricintel.clustering.embedder import generate_embeddings, generate_tfidf_svd_embeddings
from cricintel.clustering.metrics import evaluate_clusters
from cricintel.ingestion.sample_loader import load_sample_articles


def test_generate_tfidf_svd_embeddings():
    """Verify TF-IDF + SVD fallback produces valid unit-normalized vectors."""
    texts = [
        "Rohit Sharma captains India in the T20 World Cup squad.",
        "Ajit Agarkar announced the 15-man Indian cricket squad.",
        "IPL mega auction rules announced with right to match card.",
        "Stuart Broad takes final wicket at The Oval in Ashes thriller.",
    ]
    emb = generate_tfidf_svd_embeddings(texts, n_components=4)
    assert emb.shape[0] == 4
    assert emb.shape[1] >= 2

    # Check L2 unit length
    norms = np.linalg.norm(emb, axis=1)
    for n in norms:
        assert np.isclose(n, 1.0, atol=1e-3)


def test_generate_embeddings_wrapper():
    """Verify top-level embedding interface returns matrix and model metadata."""
    texts = ["Cricket match report", "IPL player trade news"]
    emb, info = generate_embeddings(texts)
    assert emb.shape[0] == 2
    assert "model_type" in info
    assert "dimension" in info


def test_agglomerative_clustering():
    """Verify agglomerative clustering groups sample articles into coherent clusters."""
    articles = load_sample_articles()[:15]
    texts = [f"{a['title']}. {a['content']}" for a in articles]
    emb, _ = generate_embeddings(texts)

    res = cluster_articles(articles, emb, algorithm="agglomerative", distance_threshold=0.65)
    assert res["num_clusters"] >= 2
    assert len(res["labels"]) == len(articles)
    assert len(res["clusters"]) == res["num_clusters"]

    first_cluster = res["clusters"][0]
    assert "cluster_id" in first_cluster
    assert "title" in first_cluster
    assert "articles" in first_cluster
    assert first_cluster["article_count"] >= 1


def test_kmeans_clustering():
    """Verify KMeans produces requested number of clusters."""
    articles = load_sample_articles()[:12]
    texts = [f"{a['title']}. {a['content']}" for a in articles]
    emb, _ = generate_embeddings(texts)

    res = cluster_articles(articles, emb, algorithm="kmeans", n_clusters=3)
    assert res["num_clusters"] == 3
    assert len(res["labels"]) == 12


def test_evaluate_clusters():
    """Verify academic evaluation metrics calculation."""
    emb = np.array([
        [1.0, 0.0, 0.0],
        [0.9, 0.1, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.9, 0.1],
    ])
    labels = [0, 0, 1, 1]
    metrics = evaluate_clusters(emb, labels)

    assert "silhouette_score" in metrics
    assert "davies_bouldin_score" in metrics
    assert "calinski_harabasz_score" in metrics
    assert metrics["silhouette_score"] > 0.4
