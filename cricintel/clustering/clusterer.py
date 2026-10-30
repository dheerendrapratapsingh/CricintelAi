"""Semantic clustering algorithms for grouping related cricket news stories."""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Optional
import numpy as np
from sklearn.cluster import AgglomerativeClustering, DBSCAN, KMeans
from sklearn.metrics.pairwise import cosine_similarity


def derive_cluster_title(articles: List[Dict[str, Any]]) -> str:
    """Generate a descriptive, human-readable title for a news story cluster."""
    if not articles:
        return "Empty Cluster"

    # Aggregate extracted entities
    all_players: List[str] = []
    all_teams: List[str] = []
    all_tournaments: List[str] = []

    for art in articles:
        all_players.extend(art.get("players", []))
        all_teams.extend(art.get("teams", []))
        if art.get("tournament") and art.get("tournament") != "International":
            all_tournaments.append(art["tournament"])

    top_player = Counter(all_players).most_common(2)
    top_team = Counter(all_teams).most_common(2)
    top_tourn = Counter(all_tournaments).most_common(1)

    # Keywords from titles
    title_words = []
    stop_words = {
        "and", "the", "for", "with", "after", "over", "from", "report", "news",
        "update", "cricket", "match", "test", "first", "second", "third", "day",
        "into", "out", "make", "take", "under", "full", "reveals", "confirmed"
    }
    for art in articles:
        for w in art.get("title", "").split():
            clean_w = w.strip(":,.'\"-?").capitalize()
            if len(clean_w) > 3 and clean_w.lower() not in stop_words:
                title_words.append(clean_w)

    top_keywords = [word for word, count in Counter(title_words).most_common(3)]

    # Compose theme title
    parts = []
    if top_tourn:
        parts.append(top_tourn[0][0])
    elif top_team:
        parts.append(top_team[0][0])

    if top_keywords:
        parts.append(" ".join(top_keywords[:2]))

    player_names = [p[0] for p in top_player]
    if player_names:
        entity_suffix = f"({', '.join(player_names)})"
    elif top_team and not top_tourn:
        entity_suffix = f"({top_team[0][0]})"
    else:
        entity_suffix = ""

    headline_prefix = " — ".join([p for p in parts if p])
    if not headline_prefix:
        headline_prefix = articles[0].get("title", "News Cluster")[:50]

    return f"{headline_prefix} {entity_suffix}".strip()


def find_representative_article(
    articles: List[Dict[str, Any]], cluster_embeddings: np.ndarray
) -> Dict[str, Any]:
    """Find the central, most representative article closest to the cluster centroid."""
    if len(articles) == 1 or cluster_embeddings.shape[0] == 1:
        return articles[0]

    centroid = np.mean(cluster_embeddings, axis=0, keepdims=True)
    similarities = cosine_similarity(cluster_embeddings, centroid).flatten()
    best_idx = int(np.argmax(similarities))
    return articles[best_idx]


def cluster_articles(
    articles: List[Dict[str, Any]],
    embeddings: np.ndarray,
    algorithm: str = "agglomerative",
    n_clusters: Optional[int] = None,
    distance_threshold: float = 0.65,
    eps: float = 0.45,
) -> Dict[str, Any]:
    """Cluster cricket news articles based on their semantic vector embeddings.

    Supported algorithms:
    - 'agglomerative' (default): Hierarchical agglomerative clustering using cosine distance.
    - 'kmeans': Partitional clustering with specified or heuristic k.
    - 'dbscan': Density-based clustering that discovers clusters and isolates noise.
    """
    n_samples = len(articles)
    if n_samples == 0:
        return {"clusters": [], "labels": [], "algorithm": algorithm, "num_clusters": 0}

    if n_samples == 1:
        single_cluster = {
            "cluster_id": 0,
            "title": articles[0].get("title", "Single Article"),
            "articles": articles,
            "article_count": 1,
            "representative_article": articles[0],
            "average_similarity": 1.0,
        }
        return {
            "clusters": [single_cluster],
            "labels": [0],
            "algorithm": algorithm,
            "num_clusters": 1,
        }

    # Algorithm selection
    if algorithm.lower() == "kmeans":
        k = n_clusters or max(2, min(7, n_samples // 3))
        k = min(k, n_samples)
        model = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = model.fit_predict(embeddings)

    elif algorithm.lower() == "dbscan":
        # Metric is cosine distance: 1 - cosine_similarity
        model = DBSCAN(eps=eps, min_samples=2, metric="cosine")
        labels = model.fit_predict(embeddings)
        # Remap noise (-1) to isolated clusters
        max_label = max([lbl for lbl in labels if lbl >= 0], default=-1)
        next_label = max_label + 1
        remapped_labels = []
        for lbl in labels:
            if lbl == -1:
                remapped_labels.append(next_label)
                next_label += 1
            else:
                remapped_labels.append(lbl)
        labels = np.array(remapped_labels)

    else:
        # Default: Agglomerative Hierarchical Clustering
        # In normalized vectors, euclidean squared = 2 - 2*cos
        if n_clusters is not None:
            k = max(1, min(n_clusters, n_samples))
            model = AgglomerativeClustering(
                n_clusters=k,
                metric="cosine",
                linkage="average",
            )
        else:
            model = AgglomerativeClustering(
                n_clusters=None,
                distance_threshold=distance_threshold,
                metric="cosine",
                linkage="average",
            )
        labels = model.fit_predict(embeddings)

    # Group articles by assigned cluster
    clusters_map: Dict[int, List[int]] = {}
    for idx, lbl in enumerate(labels):
        clusters_map.setdefault(int(lbl), []).append(idx)

    # Sort clusters by size (largest story clusters first)
    sorted_cluster_ids = sorted(clusters_map.keys(), key=lambda c_id: len(clusters_map[c_id]), reverse=True)

    result_clusters: List[Dict[str, Any]] = []
    final_labels = [0] * n_samples

    for new_id, old_id in enumerate(sorted_cluster_ids):
        indices = clusters_map[old_id]
        for idx in indices:
            final_labels[idx] = new_id

        cluster_arts = [articles[i] for i in indices]
        sub_embeddings = embeddings[indices]

        # Calculate average pairwise intra-cluster similarity
        if len(indices) > 1:
            sim_matrix = cosine_similarity(sub_embeddings)
            triu_indices = np.triu_indices(len(indices), k=1)
            avg_sim = float(np.mean(sim_matrix[triu_indices]))
        else:
            avg_sim = 1.0

        rep_art = find_representative_article(cluster_arts, sub_embeddings)
        cluster_title = derive_cluster_title(cluster_arts)

        result_clusters.append({
            "cluster_id": new_id,
            "title": cluster_title,
            "articles": cluster_arts,
            "article_count": len(cluster_arts),
            "representative_article": rep_art,
            "average_similarity": round(avg_sim, 3),
        })

    return {
        "clusters": result_clusters,
        "labels": final_labels,
        "algorithm": algorithm,
        "num_clusters": len(result_clusters),
    }
