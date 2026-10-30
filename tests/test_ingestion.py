"""Unit and integration tests for CricIntel AI data ingestion and preprocessing."""

import pytest
from cricintel.ingestion.preprocessor import clean_text, extract_entities, split_into_sentences
from cricintel.ingestion.sample_loader import get_dataset_statistics, load_sample_articles
from cricintel.ingestion.rss_fetcher import fetch_all_cricket_news


def test_load_sample_articles():
    """Verify offline sample dataset loads correctly with enriched metadata."""
    articles = load_sample_articles()
    assert len(articles) >= 30, f"Expected at least 30 articles, got {len(articles)}"

    first = articles[0]
    required_keys = ["id", "title", "source", "url", "published_at", "tournament", "content"]
    for k in required_keys:
        assert k in first, f"Missing required key: {k}"

    assert len(first["title"]) > 10
    assert len(first["content"]) > 30


def test_clean_text():
    """Test text cleaning strips HTML and wire service headers."""
    dirty = "LONDON (Reuters) - <b>Stuart Broad</b> took 604 Test wickets! [Updated] "
    cleaned = clean_text(dirty)
    assert "<b>" not in cleaned
    assert "Reuters" not in cleaned
    assert "Stuart Broad took 604 Test wickets!" in cleaned


def test_split_into_sentences():
    """Test sentence tokenization splits cleanly while respecting abbreviations."""
    text = "Rohit Sharma leads the team. Hardik Pandya was named vice-captain. Rishabh Pant is back."
    sentences = split_into_sentences(text)
    assert len(sentences) == 3
    assert "Rohit Sharma leads the team." in sentences[0]


def test_extract_entities():
    """Test domain-specific entity extraction for cricket players, teams, and tournaments."""
    text = "Rohit Sharma and Jasprit Bumrah guided Mumbai Indians to victory in the Indian Premier League."
    entities = extract_entities(text)

    assert "Rohit Sharma" in entities["players"]
    assert "Jasprit Bumrah" in entities["players"]
    assert "Mumbai Indians" in entities["teams"]
    assert "Indian Premier League" in entities["tournaments"]


def test_dataset_statistics():
    """Test summary statistics calculation."""
    articles = load_sample_articles()
    stats = get_dataset_statistics(articles)

    assert stats["total_articles"] == len(articles)
    assert stats["unique_sources"] >= 3
    assert stats["unique_tournaments"] >= 3
    assert stats["total_players_tracked"] > 5


def test_rss_fetcher_fallback():
    """Test that fetch_all_cricket_news seamlessly uses fallback if needed."""
    # Pass an invalid feed URL to verify fallback behavior
    bogus_feeds = [{"name": "InvalidFeed", "url": "https://localhost:9999/does-not-exist.xml"}]
    result = fetch_all_cricket_news(feeds=bogus_feeds, timeout_per_feed=1, include_sample_if_low=True)

    assert result["total_count"] > 0
    assert result["used_fallback"] is True
    assert len(result["articles"]) >= 30
