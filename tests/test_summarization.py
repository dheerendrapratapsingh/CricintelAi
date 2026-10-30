"""Unit and integration tests for multi-article summarization engines."""

import pytest
from cricintel.ingestion.sample_loader import load_sample_articles
from cricintel.summarization.extractive import summarize_cluster_extractive
from cricintel.summarization.abstractive import summarize_cluster_abstractive
from cricintel.summarization.multi_doc import synthesize_cluster_briefing


def test_summarize_cluster_extractive():
    """Verify extractive TextRank and MMR produce a concise summary with bullet takeaways."""
    articles = load_sample_articles()[:4]
    res = summarize_cluster_extractive(articles, target_sentences=3, use_mmr=True)

    assert "summary_text" in res
    assert "bullet_takeaways" in res
    assert len(res["bullet_takeaways"]) <= 4
    assert len(res["summary_text"]) > 40
    assert "provenance" in res
    assert len(res["provenance"]) > 0


def test_synthesize_cluster_briefing():
    """Verify end-to-end multi-document intelligence briefing with compression ratio and citations."""
    sample_arts = load_sample_articles()[:5]
    mock_cluster = {
        "cluster_id": 1,
        "title": "T20 World Cup Squad Selection",
        "articles": sample_arts,
    }

    briefing = synthesize_cluster_briefing(mock_cluster, method="extractive", target_sentences=3)

    assert briefing["cluster_id"] == 1
    assert briefing["article_count"] == 5
    assert len(briefing["summary_text"]) > 20
    assert briefing["compression_ratio_pct"] > 0
    assert len(briefing["citations"]) == 5
    assert len(briefing["unique_sources"]) >= 2
    assert len(briefing["timeline"]) == 5


def test_abstractive_fallback_resilience():
    """Verify abstractive engine gracefully falls back without throwing exceptions."""
    articles = load_sample_articles()[:3]
    # Forcing fallback or running pipeline
    res = summarize_cluster_abstractive(articles, force_fallback=True)
    assert res is not None
    assert "summary_text" in res
    assert len(res["summary_text"]) > 20
    assert res.get("fallback_used") is True
