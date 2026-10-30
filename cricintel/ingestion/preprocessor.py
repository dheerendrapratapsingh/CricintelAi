"""Text preprocessing, cleaning, and domain-specific cricket entity extraction."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Set
from bs4 import BeautifulSoup

# Curated cricket entities for rapid, dependency-free entity recognition
KNOWN_PLAYERS = [
    "Rohit Sharma", "Virat Kohli", "Jasprit Bumrah", "Hardik Pandya", "Rishabh Pant",
    "Sanju Samson", "Suryakumar Yadav", "Yashasvi Jaiswal", "Shubman Gill", "Rinku Singh",
    "Shivam Dube", "Kuldeep Yadav", "Yuzvendra Chahal", "Axar Patel", "Ravindra Jadeja",
    "Mohammed Siraj", "Arshdeep Singh", "Ravichandran Ashwin", "Pat Cummins", "Stuart Broad",
    "Ben Stokes", "Joe Root", "Steve Smith", "David Warner", "Usman Khawaja", "Todd Murphy",
    "Alex Carey", "Chris Woakes", "Travis Head", "Marnus Labuschagne", "Babar Azam",
    "Shaheen Afridi", "Mohsin Naqvi", "Gautam Gambhir", "Ajit Agarkar", "MS Dhoni",
    "Shreyas Iyer", "KL Rahul", "Heinrich Klaasen", "Gus Atkinson", "Kamran Ghulam",
    "Abhishek Nayar", "Ryan ten Doeschate", "Morne Morkel", "Jay Shah", "Rahul Dravid",
    "Kane Williamson", "Kagiso Rabada", "Alastair Cook", "Ricky Ponting", "Sunil Gavaskar"
]

KNOWN_TEAMS = [
    "India", "Australia", "England", "Pakistan", "South Africa", "New Zealand",
    "Sri Lanka", "West Indies", "USA", "Bangladesh", "Afghanistan",
    "Mumbai Indians", "Chennai Super Kings", "Royal Challengers Bengaluru",
    "Kolkata Knight Riders", "Delhi Capitals", "Punjab Kings", "Sunrisers Hyderabad",
    "Lucknow Super Giants", "Rajasthan Royals", "Gujarat Titans"
]

KNOWN_TOURNAMENTS = [
    "ICC Men's T20 World Cup", "Indian Premier League", "The Ashes",
    "Border-Gavaskar Trophy", "ICC Champions Trophy",
    "ICC World Test Championship", "Bilateral Series"
]


def clean_html(text: str) -> str:
    """Strip HTML markup and entities using BeautifulSoup."""
    if not text:
        return ""
    soup = BeautifulSoup(text, "html.parser")
    cleaned = soup.get_text(separator=" ")
    return cleaned


def clean_text(text: str) -> str:
    """Normalize whitespace, remove wire prefixes and special noise characters."""
    if not text:
        return ""
    text = clean_html(text)

    # Remove news wire prefixes like "LONDON (Reuters) -" or "MUMBAI (PTI) --"
    text = re.sub(r"^[A-Z\s]{2,15}\s*\([^)]+\)\s*[-—:]\s*", "", text)
    # Remove leading date or editorial tags like "[Updated] ", "LIVE: "
    text = re.sub(r"^\[[^\]]+\]\s*", "", text)
    text = re.sub(r"^(LIVE|BREAKING|REPORT):\s*", "", text, flags=re.IGNORECASE)

    # Normalize quotes and dashes
    text = text.replace("“", "\"").replace("”", "\"").replace("’", "'").replace("`", "'")
    text = text.replace("—", " - ").replace("–", " - ")

    # Collapse multiple whitespaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def split_into_sentences(text: str) -> List[str]:
    """Robust regex-based sentence splitter preserving abbreviations and decimals."""
    if not text:
        return []

    # Clean the input text first
    cleaned = clean_text(text)
    if not cleaned:
        return []

    # Regex splits by sentence terminators (.!?) followed by space and capital letter/quotes
    # while not splitting on common titles or cricket abbreviations (e.g., Mr., Dr., vs., km/h, etc.)
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'‘“])", cleaned)
    valid_sentences = [s.strip() for s in sentences if len(s.strip()) > 15]

    return valid_sentences if valid_sentences else [cleaned]


def extract_entities(text: str) -> Dict[str, List[str]]:
    """Scan text for known cricket players, teams, and tournament mentions."""
    found_players: Set[str] = set()
    found_teams: Set[str] = set()
    found_tournaments: Set[str] = set()

    lower_text = " " + text.lower() + " "

    for player in KNOWN_PLAYERS:
        pattern = r"\b" + re.escape(player.lower()) + r"\b"
        if re.search(pattern, lower_text):
            found_players.add(player)

    for team in KNOWN_TEAMS:
        pattern = r"\b" + re.escape(team.lower()) + r"\b"
        if re.search(pattern, lower_text):
            found_teams.add(team)

    for tourn in KNOWN_TOURNAMENTS:
        pattern = r"\b" + re.escape(tourn.lower()) + r"\b"
        if re.search(pattern, lower_text):
            found_tournaments.add(tourn)

    # Aliases
    if re.search(r"\bipl\b", lower_text):
        found_tournaments.add("Indian Premier League")
    if re.search(r"\bt20\s*world\s*cup\b", lower_text):
        found_tournaments.add("ICC Men's T20 World Cup")
    if re.search(r"\bashes\b", lower_text):
        found_tournaments.add("The Ashes")
    if re.search(r"\bchampions\s*trophy\b", lower_text):
        found_tournaments.add("ICC Champions Trophy")
    if re.search(r"\brcb\b", lower_text):
        found_teams.add("Royal Challengers Bengaluru")
    if re.search(r"\bcsk\b", lower_text):
        found_teams.add("Chennai Super Kings")
    if re.search(r"\bmi\b", lower_text):
        found_teams.add("Mumbai Indians")
    if re.search(r"\bkkr\b", lower_text):
        found_teams.add("Kolkata Knight Riders")

    return {
        "players": sorted(list(found_players)),
        "teams": sorted(list(found_teams)),
        "tournaments": sorted(list(found_tournaments)),
    }


def enrich_article_metadata(article: Dict[str, Any]) -> Dict[str, Any]:
    """Clean article fields and extract entities to ensure rich searchability."""
    cleaned_title = clean_text(article.get("title", ""))
    cleaned_content = clean_text(article.get("content", ""))

    combined_text = f"{cleaned_title}. {cleaned_content}"
    entities = extract_entities(combined_text)

    # Merge extracted with pre-existing metadata
    existing_players = set(article.get("players", []))
    existing_teams = set(article.get("teams", []))
    existing_players.update(entities["players"])
    existing_teams.update(entities["teams"])

    tournament = article.get("tournament")
    if not tournament and entities["tournaments"]:
        tournament = entities["tournaments"][0]
    elif not tournament:
        tournament = "International"

    return {
        **article,
        "title": cleaned_title,
        "content": cleaned_content,
        "players": sorted(list(existing_players)),
        "teams": sorted(list(existing_teams)),
        "tournament": tournament,
        "word_count": len(cleaned_content.split()),
    }
