"""Plotly visualization charts for CricIntel AI cricket news analytics."""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Theme styling constants
THEME_BG = "rgba(15, 23, 42, 0.75)"
PAPER_BG = "rgba(11, 15, 25, 0.0)"
FONT_FAMILY = "Inter, -apple-system, BlinkMacSystemFont, sans-serif"
COLOR_PALETTE = [
    "#00D26A",  # Pitch Emerald
    "#38BDF8",  # Sky Blue
    "#F59E0B",  # Amber / Gold
    "#A855F7",  # Purple
    "#EC4899",  # Rose
    "#10B981",  # Mint
    "#6366F1",  # Indigo
]


def _apply_theme(fig: go.Figure, title: str) -> go.Figure:
    """Apply modern dark analytics theme to Plotly figure."""
    fig.update_layout(
        title={
            "text": f"<b>{title}</b>",
            "font": {"size": 16, "color": "#F8FAFC", "family": FONT_FAMILY},
            "x": 0.02,
        },
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=THEME_BG,
        font={"color": "#94A3B8", "family": FONT_FAMILY, "size": 12},
        margin={"l": 40, "r": 40, "t": 50, "b": 40},
        legend={"orientation": "h", "yanchor": "bottom", "y": -0.25, "xanchor": "center", "x": 0.5},
    )
    fig.update_xaxes(gridcolor="#1E293B", zerolinecolor="#334155")
    fig.update_yaxes(gridcolor="#1E293B", zerolinecolor="#334155")
    return fig


def plot_tournament_distribution(articles: List[Dict[str, Any]]) -> go.Figure:
    """Donut chart showing coverage proportion by cricket tournament/event."""
    if not articles:
        fig = go.Figure()
        return _apply_theme(fig, "Tournament Breakdown (No Data)")

    tournaments = [a.get("tournament", "Other") for a in articles]
    counts = Counter(tournaments)

    df = pd.DataFrame({
        "Tournament": list(counts.keys()),
        "Articles": list(counts.values()),
    }).sort_values("Articles", ascending=False)

    fig = px.pie(
        df,
        names="Tournament",
        values="Articles",
        hole=0.45,
        color_discrete_sequence=COLOR_PALETTE,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hoverinfo="label+value+percent",
        marker=dict(line=dict(color="#0F172A", width=2)),
    )
    return _apply_theme(fig, "Tournament & Event Coverage Distribution")


def plot_top_entities(
    articles: List[Dict[str, Any]], entity_type: str = "players", top_n: int = 8
) -> go.Figure:
    """Horizontal bar chart showing the most mentioned cricket players or teams."""
    if not articles:
        fig = go.Figure()
        return _apply_theme(fig, f"Top {entity_type.capitalize()} (No Data)")

    all_entities = []
    key = "players" if entity_type == "players" else "teams"
    for a in articles:
        all_entities.extend(a.get(key, []))

    if not all_entities:
        fig = go.Figure()
        return _apply_theme(fig, f"Top {entity_type.capitalize()} (None Detected)")

    counts = Counter(all_entities).most_common(top_n)
    df = pd.DataFrame(counts, columns=["Entity", "Mentions"]).sort_values("Mentions", ascending=True)

    fig = px.bar(
        df,
        x="Mentions",
        y="Entity",
        orientation="h",
        color="Mentions",
        color_continuous_scale=[[0, "#38BDF8"], [1, "#00D26A"]],
    )
    fig.update_layout(coloraxis_showscale=False)
    fig.update_traces(marker_line_color="#0F172A", marker_line_width=1.5)
    title = f"Top Mentioned {entity_type.capitalize()} Across Coverage"
    return _apply_theme(fig, title)


def plot_cluster_size_distribution(clusters: List[Dict[str, Any]]) -> go.Figure:
    """Bar chart showing the volume of articles per story cluster with similarity score."""
    if not clusters:
        fig = go.Figure()
        return _apply_theme(fig, "Story Cluster Volumes (No Data)")

    data = []
    for c in clusters:
        title = c.get("title", f"Cluster #{c.get('cluster_id')}")
        # Shorten title for readable chart display
        short_title = title if len(title) <= 28 else title[:25] + "..."
        data.append({
            "Cluster": f"#{c.get('cluster_id')}: {short_title}",
            "Articles": c.get("article_count", 0),
            "Cohesion": c.get("average_similarity", 1.0),
        })

    df = pd.DataFrame(data)

    fig = px.bar(
        df,
        x="Cluster",
        y="Articles",
        color="Cohesion",
        color_continuous_scale="Viridis",
        hover_data=["Cohesion"],
    )
    fig.update_layout(coloraxis_colorbar=dict(title="Cohesion", thickness=15, len=0.7))
    fig.update_traces(marker_line_color="#0F172A", marker_line_width=1.5)
    return _apply_theme(fig, "Articles Per Semantic Story Cluster")


def plot_publication_timeline(articles: List[Dict[str, Any]]) -> go.Figure:
    """Timeline visualization showing publication dispersion over time."""
    if not articles:
        fig = go.Figure()
        return _apply_theme(fig, "Reporting Timeline (No Data)")

    records = []
    for a in articles:
        pub = a.get("published_at", "")
        # Parse timestamp ensuring uniform tz-naive UTC representation across feeds
        try:
            dt = pd.to_datetime(pub, utc=True).tz_localize(None)
        except Exception:
            dt = pd.Timestamp.utcnow().tz_localize(None)

        records.append({
            "Date": dt,
            "Source": a.get("source", "Unknown"),
            "Headline": a.get("title", ""),
            "Tournament": a.get("tournament", "Other"),
        })

    df = pd.DataFrame(records).sort_values("Date")

    fig = px.scatter(
        df,
        x="Date",
        y="Source",
        color="Tournament",
        hover_name="Headline",
        size_max=12,
        color_discrete_sequence=COLOR_PALETTE,
    )
    fig.update_traces(marker=dict(size=12, line=dict(width=1.5, color="#0F172A")))
    return _apply_theme(fig, "News Ingestion Timeline by Source")
