"""Generate tangible intermediate and output artifacts for the ATSMA lab submission.

This script executes the CricIntel AI pipeline on the curated cricket news dataset
and writes structured intermediate and output files to `data/output/`:
1. intermediate_embeddings.json & .csv (vector representations)
2. cluster_assignments.json & .csv (document-to-cluster mappings)
3. clustering_metrics.json (Silhouette, Davies-Bouldin, Calinski-Harabasz)
4. synthesized_briefings.json (multi-document summaries with source citations)
5. entity_analytics.json (tournament breakdown, entity counts, timeline)
"""

import json
import os
import sys

# Ensure root directory is on python path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

import pandas as pd
import numpy as np

from cricintel.ingestion.sample_loader import load_sample_articles
from cricintel.ingestion.preprocessor import enrich_article_metadata
from cricintel.clustering.embedder import generate_embeddings
from cricintel.clustering.clusterer import cluster_articles
from cricintel.clustering.metrics import evaluate_clusters
from collections import Counter
from cricintel.summarization.multi_doc import synthesize_cluster_briefing


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(base_dir, "data", "output")
    os.makedirs(output_dir, exist_ok=True)

    print(">>> 1. Loading input data...")
    raw_articles = load_sample_articles()
    articles = [enrich_article_metadata(a) for a in raw_articles]
    print(f"Loaded and enriched {len(articles)} articles.")

    # Generate Embeddings (Intermediate Data)
    print(">>> 2. Computing intermediate semantic vector embeddings...", flush=True)
    texts = [f"{a['title']}. {a['content']}" for a in articles]
    embeddings, emb_info = generate_embeddings(texts, force_fallback=True)
    print(f"Embeddings generated: {embeddings.shape} via {emb_info['model_type']}", flush=True)

    # Save Intermediate Embeddings
    emb_records = []
    for i, a in enumerate(articles):
        emb_records.append({
            "article_id": a["id"],
            "title": a["title"],
            "source": a["source"],
            "embedding_dim": int(embeddings.shape[1]),
            "vector_sample_first_5": [round(float(v), 5) for v in embeddings[i, :5]],
            "full_vector": [round(float(v), 5) for v in embeddings[i].tolist()]
        })

    with open(os.path.join(output_dir, "intermediate_embeddings.json"), "w", encoding="utf-8") as f:
        json.dump({
            "metadata": emb_info,
            "article_count": len(articles),
            "vector_dimension": int(embeddings.shape[1]),
            "embeddings": emb_records
        }, f, indent=2)

    # Save CSV version (ID, Title, Source + Vector dimensions)
    emb_df = pd.DataFrame(embeddings)
    emb_df.columns = [f"dim_{col}" for col in emb_df.columns]
    emb_df.insert(0, "source", [a["source"] for a in articles])
    emb_df.insert(0, "title", [a["title"] for a in articles])
    emb_df.insert(0, "article_id", [a["id"] for a in articles])
    emb_df.to_csv(os.path.join(output_dir, "intermediate_embeddings.csv"), index=False)
    print("Saved intermediate embeddings to JSON and CSV.")

    # Clustering (Intermediate Data & Process)
    print(">>> 3. Performing unsupervised semantic story clustering...")
    cluster_results = cluster_articles(
        articles,
        embeddings,
        algorithm="agglomerative",
        n_clusters=7
    )
    labels = cluster_results["labels"]
    num_clusters = cluster_results["num_clusters"]
    print(f"Discovered {num_clusters} story clusters.")

    # Save Cluster Assignments (CSV & JSON)
    assignments = []
    for i, a in enumerate(articles):
        c_id = int(labels[i])
        c_title = next((c["title"] for c in cluster_results["clusters"] if c["cluster_id"] == c_id), "Unknown")
        assignments.append({
            "article_id": a["id"],
            "title": a["title"],
            "source": a["source"],
            "published_at": a.get("published_at", ""),
            "cluster_id": c_id,
            "cluster_title": c_title
        })

    with open(os.path.join(output_dir, "cluster_assignments.json"), "w", encoding="utf-8") as f:
        json.dump(assignments, f, indent=2)

    pd.DataFrame(assignments).to_csv(os.path.join(output_dir, "cluster_assignments.csv"), index=False)
    print("Saved cluster assignments to JSON and CSV.")

    # Validation Metrics (Output Data)
    print(">>> 4. Computing clustering evaluation metrics...")
    metrics = evaluate_clusters(embeddings, labels)
    with open(os.path.join(output_dir, "clustering_metrics.json"), "w", encoding="utf-8") as f:
        json.dump({
            "algorithm": "Agglomerative Hierarchical (Cosine Distance)",
            "num_clusters": num_clusters,
            "silhouette_score": round(metrics.get("silhouette_score", 0.0), 4),
            "davies_bouldin_index": round(metrics.get("davies_bouldin_score", 0.0), 4),
            "calinski_harabasz_index": round(metrics.get("calinski_harabasz_score", 0.0), 2),
            "total_articles_evaluated": len(articles)
        }, f, indent=2)
    print(f"Metrics: Silhouette={metrics.get('silhouette_score', 0):.4f}, DB={metrics.get('davies_bouldin_score', 0):.4f}")

    # Synthesized Briefings (Output Data)
    print(">>> 5. Generating multi-document synthesized briefings for all clusters...")
    briefings = []
    for c in cluster_results["clusters"]:
        briefing = synthesize_cluster_briefing(
            c,
            method="extractive",
            target_sentences=4
        )
        briefings.append(briefing)

    with open(os.path.join(output_dir, "synthesized_briefings.json"), "w", encoding="utf-8") as f:
        json.dump(briefings, f, indent=2)
    print("Saved synthesized briefings to JSON.")

    # Analytics Summary (Output Data)
    print(">>> 6. Exporting aggregate news analytics...")
    tournaments = [a.get("tournament", "Other") for a in articles]
    tournament_counts = dict(Counter(tournaments).most_common())

    all_players = []
    for a in articles:
        all_players.extend(a.get("players", []))
    player_counts = dict(Counter(all_players).most_common(12))

    compression_ratios = [b.get("compression_ratio_pct", 0.0) for b in briefings]
    avg_compression = round(float(np.mean(compression_ratios)), 1) if compression_ratios else 0.0

    analytics = {
        "corpus_total_articles": len(articles),
        "total_story_clusters": num_clusters,
        "unique_sources": sorted(list(set(a["source"] for a in articles))),
        "tournament_distribution": tournament_counts,
        "top_player_mentions": player_counts,
        "average_compression_ratio_pct": avg_compression,
    }

    with open(os.path.join(output_dir, "analytics_summary.json"), "w", encoding="utf-8") as f:
        json.dump(analytics, f, indent=2)
    print("Saved analytics summary to JSON.")

    print("\n[SUCCESS] All intermediate and output artifacts generated in data/output/ successfully!")


if __name__ == "__main__":
    main()
