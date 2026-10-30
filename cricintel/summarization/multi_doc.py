"""High-level multi-document intelligence briefing and report generator."""

from __future__ import annotations

from typing import Any, Dict, List
from cricintel.summarization.abstractive import summarize_cluster_abstractive
from cricintel.summarization.extractive import summarize_cluster_extractive


def synthesize_cluster_briefing(
    cluster: Dict[str, Any],
    method: str = "extractive",
    target_sentences: int = 4,
    abstractive_model: str = "sshleifer/distilbart-cnn-12-6",
) -> Dict[str, Any]:
    """Generate an end-to-end intelligence briefing for a story cluster with compression metrics and citations."""
    articles = cluster.get("articles", [])
    if not articles:
        return {
            "cluster_id": cluster.get("cluster_id", 0),
            "title": cluster.get("title", "Empty Cluster"),
            "summary_text": "No articles available.",
            "bullet_takeaways": [],
            "compression_ratio_pct": 0.0,
            "original_word_count": 0,
            "summary_word_count": 0,
            "sources": [],
            "citations": [],
            "timeline": [],
        }

    # Word count across original articles
    original_words = sum(len(a.get("content", "").split()) for a in articles)

    # Execute selected summarization method
    if method.lower() == "abstractive":
        summary_result = summarize_cluster_abstractive(
            articles, model_name=abstractive_model, min_length=40, max_length=140
        )
    else:
        summary_result = summarize_cluster_extractive(
            articles, target_sentences=target_sentences, use_mmr=True
        )

    summary_text = summary_result.get("summary_text", "")
    summary_words = len(summary_text.split())

    # Calculate compression ratio
    if original_words > 0:
        compression_ratio = round((1.0 - (summary_words / original_words)) * 100.0, 1)
    else:
        compression_ratio = 0.0

    # Build chronological timeline
    sorted_by_date = sorted(articles, key=lambda a: a.get("published_at", ""), reverse=False)
    timeline = [
        {
            "published_at": a.get("published_at", "N/A"),
            "source": a.get("source", "Unknown"),
            "title": a.get("title", ""),
            "url": a.get("url", "#"),
        }
        for a in sorted_by_date
    ]

    # Citations
    citations = [
        {
            "id": a.get("id"),
            "title": a.get("title"),
            "source": a.get("source"),
            "author": a.get("author", "Staff Reporter"),
            "url": a.get("url", "#"),
            "published_at": a.get("published_at", ""),
        }
        for a in articles
    ]

    unique_sources = sorted(list({a.get("source", "Unknown") for a in articles}))

    # Aggregate players and teams
    all_players = sorted(list({p for a in articles for p in a.get("players", [])}))
    all_teams = sorted(list({t for a in articles for t in a.get("teams", [])}))

    return {
        "cluster_id": cluster.get("cluster_id", 0),
        "cluster_title": cluster.get("title", "News Cluster"),
        "article_count": len(articles),
        "summary_text": summary_text,
        "bullet_takeaways": summary_result.get("bullet_takeaways", []),
        "method_used": summary_result.get("method", method),
        "fallback_used": summary_result.get("fallback_used", False),
        "original_word_count": original_words,
        "summary_word_count": summary_words,
        "compression_ratio_pct": compression_ratio,
        "unique_sources": unique_sources,
        "citations": citations,
        "timeline": timeline,
        "players_involved": all_players,
        "teams_involved": all_teams,
        "provenance": summary_result.get("provenance", []),
    }
