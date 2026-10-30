"""Offline sample dataset loader for CricIntel AI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
from cricintel.ingestion.preprocessor import enrich_article_metadata

DATA_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "sample_cricket_news.json"


def load_sample_articles(data_path: Path | str | None = None) -> List[Dict[str, Any]]:
    """Load, validate, and enrich the offline sample cricket news dataset.

    Guarantees a successful load even if the external JSON file is missing.
    """
    file_path = Path(data_path) if data_path else DATA_FILE

    articles: List[Dict[str, Any]] = []

    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_articles = json.load(f)
                if isinstance(raw_articles, list) and len(raw_articles) > 0:
                    articles = raw_articles
        except Exception:
            articles = []

    if not articles:
        # Emergency embedded fallback with 5 core stories
        articles = [
            {
                "id": "embed_01",
                "title": "India announce 15-man squad for T20 World Cup with Rohit Sharma as captain",
                "source": "ESPNcricinfo",
                "url": "https://www.espncricinfo.com",
                "published_at": "2025-05-01T12:00:00Z",
                "tournament": "ICC Men's T20 World Cup",
                "teams": ["India"],
                "players": ["Rohit Sharma", "Hardik Pandya", "Rishabh Pant", "Virat Kohli"],
                "content": "BCCI has announced the 15-member squad for the ICC Men's T20 World Cup. Rohit Sharma leads the squad with Hardik Pandya named vice-captain. Rishabh Pant returns as wicketkeeper."
            },
            {
                "id": "embed_02",
                "title": "IPL Mega Auction rules confirmed with INR 120 crore team purse",
                "source": "Cricbuzz",
                "url": "https://www.cricbuzz.com",
                "published_at": "2025-10-31T15:00:00Z",
                "tournament": "Indian Premier League",
                "teams": ["Mumbai Indians", "Royal Challengers Bengaluru"],
                "players": ["Virat Kohli", "Rohit Sharma", "Jasprit Bumrah"],
                "content": "The IPL Governing Council unveiled auction guidelines with team purses hiked to INR 120 crore and Right To Match options returning."
            },
            {
                "id": "embed_03",
                "title": "Stuart Broad retires in fairytale Ashes win as England level series 2-2",
                "source": "BBC Sport",
                "url": "https://www.bbc.com/sport",
                "published_at": "2025-07-31T18:00:00Z",
                "tournament": "The Ashes",
                "teams": ["England", "Australia"],
                "players": ["Stuart Broad", "Pat Cummins", "Ben Stokes"],
                "content": "Stuart Broad claimed the final wicket of the fifth Test at The Oval to help England defeat Australia and draw the epic series 2-2."
            }
        ]

    # Enrich metadata for each article
    enriched = [enrich_article_metadata(art) for art in articles]
    return enriched


def get_dataset_statistics(articles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute summary statistics for the dataset."""
    if not articles:
        return {
            "total_articles": 0,
            "unique_sources": 0,
            "sources": [],
            "unique_tournaments": 0,
            "tournaments": [],
            "total_players_tracked": 0,
            "total_teams_tracked": 0,
        }

    sources = sorted(list({a.get("source", "Unknown") for a in articles}))
    tournaments = sorted(list({a.get("tournament", "Other") for a in articles}))
    players = set()
    teams = set()

    for a in articles:
        players.update(a.get("players", []))
        teams.update(a.get("teams", []))

    return {
        "total_articles": len(articles),
        "unique_sources": len(sources),
        "sources": sources,
        "unique_tournaments": len(tournaments),
        "tournaments": tournaments,
        "total_players_tracked": len(players),
        "total_teams_tracked": len(teams),
    }
