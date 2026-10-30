"""CricIntel AI — Cricket News Intelligence System.
Interactive Streamlit Dashboard: Text Summarization + Semantic Clustering + News Analytics.
"""

from __future__ import annotations

import json
from datetime import datetime
import pandas as pd
import streamlit as st

from cricintel.analytics.visualizer import (
    plot_cluster_size_distribution,
    plot_publication_timeline,
    plot_top_entities,
    plot_tournament_distribution,
)
from cricintel.clustering.clusterer import cluster_articles
from cricintel.clustering.embedder import generate_embeddings
from cricintel.clustering.metrics import evaluate_clusters
from cricintel.ingestion.preprocessor import clean_text
from cricintel.ingestion.rss_fetcher import fetch_all_cricket_news
from cricintel.ingestion.sample_loader import get_dataset_statistics, load_sample_articles
from cricintel.summarization.multi_doc import synthesize_cluster_briefing

# -----------------------------------------------------------------------------
# Streamlit Page Configuration & Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="CricIntel AI — Cricket News Intelligence System",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main Background & Accent Colors */
    .stApp {
        background: radial-gradient(circle at 10% 20%, #0b0f19 0%, #0d1527 90%);
        color: #f1f5f9;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #f8fafc !important;
        font-weight: 700 !important;
    }
    
    /* Top Brand Hero */
    .hero-banner {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(30, 41, 59, 0.6) 100%);
        border: 1px solid rgba(0, 210, 106, 0.25);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        backdrop-filter: blur(8px);
    }
    
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #00D26A, #38BDF8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 6px;
    }
    
    .hero-subtitle {
        color: #94A3B8;
        font-size: 1.05rem;
        margin-bottom: 0px;
    }
    
    /* Metric Cards */
    .metric-card {
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid rgba(56, 189, 248, 0.2);
        border-radius: 10px;
        padding: 16px 20px;
        text-align: center;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: #00D26A;
    }
    .metric-value {
        font-size: 1.9rem;
        font-weight: 700;
        color: #38BDF8;
    }
    .metric-label {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94A3B8;
        margin-top: 4px;
    }

    /* Badges */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        font-size: 0.75rem;
        font-weight: 600;
        border-radius: 6px;
        margin-right: 6px;
        margin-bottom: 4px;
    }
    .badge-source {
        background-color: rgba(56, 189, 248, 0.15);
        color: #38BDF8;
        border: 1px solid rgba(56, 189, 248, 0.3);
    }
    .badge-tournament {
        background-color: rgba(0, 210, 106, 0.15);
        color: #00D26A;
        border: 1px solid rgba(0, 210, 106, 0.3);
    }
    .badge-entity {
        background-color: rgba(245, 158, 11, 0.15);
        color: #F59E0B;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }
    
    /* Article & Cluster Card */
    .cluster-box {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 16px;
    }
    .cluster-header {
        font-size: 1.25rem;
        font-weight: 700;
        color: #F8FAFC;
        margin-bottom: 8px;
    }

    /* Intelligence Briefing Box */
    .briefing-box {
        background: linear-gradient(145deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.85));
        border-left: 5px solid #00D26A;
        border-radius: 8px;
        padding: 22px;
        margin-top: 14px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Caching Data, Embeddings, and Clustering
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner="Ingesting cricket news data...")
def get_cached_news_data(source_mode: str, max_per_feed: int = 20) -> dict:
    if source_mode == "live":
        return fetch_all_cricket_news(
            max_articles_per_feed=max_per_feed,
            include_sample_if_low=True
        )
    articles = load_sample_articles()
    return {
        "articles": articles,
        "total_count": len(articles),
        "feed_statuses": {"Offline Curated Dataset": f"Loaded {len(articles)} articles"},
        "duration_seconds": 0.05,
        "used_fallback": False,
    }


@st.cache_data(show_spinner="Computing semantic vector representations...")
def get_cached_embeddings(texts: tuple[str, ...], model_name: str, force_fallback: bool):
    return generate_embeddings(list(texts), model_name=model_name, force_fallback=force_fallback)


# -----------------------------------------------------------------------------
# Sidebar Configuration
# -----------------------------------------------------------------------------
st.sidebar.markdown("## 🏏 **CricIntel AI**")
st.sidebar.caption("Cricket News Intelligence & Semantic Analytics")
st.sidebar.markdown("---")

# Data Source Mode
st.sidebar.subheader("📡 Ingestion Mode")
data_mode = st.sidebar.radio(
    "Select News Ingestion Source",
    options=["Offline Curated (39 Articles)", "Live RSS Ingestion"],
    index=0,
    help="Offline mode ensures complete stability without external network dependencies. Live RSS fetches live feeds with auto-fallback.",
)
is_live = data_mode == "Live RSS Ingestion"

max_per_feed = 20
if is_live:
    max_per_feed = st.sidebar.slider(
        "Max Articles per Feed",
        min_value=10,
        max_value=35,
        value=20,
        step=5,
        help="Adjust how many recent news dispatches to fetch from each publisher (up to 100+ articles total)."
    )
    if st.sidebar.button("🔄 Refresh Live Feeds", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Load or fetch news data immediately
ingestion_result = get_cached_news_data("live" if is_live else "offline", max_per_feed=max_per_feed)
all_articles = ingestion_result["articles"]
dataset_stats = get_dataset_statistics(all_articles)

if is_live:
    # Display active feed status badges in sidebar
    st.sidebar.markdown("**Live Feeds Connected (6 Outlets):**")
    for feed_name, status in ingestion_result.get("feed_statuses", {}).items():
        if "Success" in status:
            st.sidebar.caption(f"🟢 **{feed_name}**: {status}")
        else:
            st.sidebar.caption(f"🟡 **{feed_name}**: {status}")

st.sidebar.markdown("---")

# Clustering Algorithm Controls
st.sidebar.subheader("🧩 Semantic Clustering")

embed_choice = st.sidebar.selectbox(
    "Vector Embeddings Engine",
    options=[
        "⚡ Fast LSA (TF-IDF + SVD) — Instant (<0.05s)",
        "🤖 Transformer (SentenceTransformers all-MiniLM-L6-v2)",
    ],
    index=0,
    help="Fast LSA provides instant sub-second vector clustering; Transformer provides deep neural representations.",
)
force_fallback = "Fast LSA" in embed_choice

cluster_algo = st.sidebar.selectbox(
    "Clustering Algorithm",
    options=["Agglomerative (Hierarchical)", "KMeans", "DBSCAN"],
    index=0,
    help="Agglomerative is ideal for discovering natural story boundaries based on cosine distance.",
)

distance_threshold = 0.65
kmeans_k = 7
dbscan_eps = 0.45
fixed_k = None

if cluster_algo == "Agglomerative (Hierarchical)":
    use_fixed_k = st.sidebar.checkbox("Specify fixed number of clusters", value=False)
    if use_fixed_k:
        fixed_k = st.sidebar.slider("Number of clusters (k)", min_value=2, max_value=12, value=7)
    else:
        fixed_k = None
        distance_threshold = st.sidebar.slider(
            "Cosine Distance Cutoff", min_value=0.35, max_value=0.90, value=0.65, step=0.05,
            help="Higher threshold merges broader topics; lower creates tighter clusters."
        )
elif cluster_algo == "KMeans":
    kmeans_k = st.sidebar.slider("Number of clusters (k)", min_value=2, max_value=12, value=7)
    fixed_k = kmeans_k
else:
    dbscan_eps = st.sidebar.slider("DBSCAN Epsilon (Eps)", min_value=0.20, max_value=0.80, value=0.45, step=0.05)
    fixed_k = None

st.sidebar.markdown("---")

# Summarizer Settings
st.sidebar.subheader("📝 Summarizer Engine")
summary_engine = st.sidebar.selectbox(
    "Summarization Technique",
    options=["Extractive MMR (Fast & Graph-Based)", "Abstractive Transformer (Hugging Face)"],
    index=0,
    help="Extractive MMR ranks sentences by centrality with diversity penalty; Abstractive synthesizes text using deep sequence models.",
)
target_sentences = st.sidebar.slider("Target Summary Sentences", min_value=2, max_value=6, value=4)

# -----------------------------------------------------------------------------
# Main Application Content
# -----------------------------------------------------------------------------

# Hero Header
st.markdown(
    """
    <div class="hero-banner">
        <div class="hero-title">CricIntel AI — Cricket News Intelligence System</div>
        <div class="hero-subtitle">
            Autonomous multi-article text summarization, semantic vector clustering, and news trend intelligence for world cricket.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Top KPI Metric Cards
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-value">{dataset_stats['total_articles']}</div>
            <div class="metric-label">Articles Ingested</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-value">{dataset_stats['unique_sources']}</div>
            <div class="metric-label">News Sources</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-value">{dataset_stats['total_players_tracked']}</div>
            <div class="metric-label">Tracked Players</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col4:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-value">{dataset_stats['unique_tournaments']}</div>
            <div class="metric-label">Tournaments / Series</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")

# -----------------------------------------------------------------------------
# Semantic Vector Generation & Clustering Execution
# -----------------------------------------------------------------------------
# Encode headlines and lead paragraphs (optimized for sub-second execution)
texts_to_embed = tuple(f"{a['title']}. {a.get('content', '')[:250]}" for a in all_articles)

embeddings, embed_info = get_cached_embeddings(
    texts_to_embed,
    model_name="all-MiniLM-L6-v2",
    force_fallback=force_fallback,
)

algo_name = "agglomerative"
if "KMeans" in cluster_algo:
    algo_name = "kmeans"
elif "DBSCAN" in cluster_algo:
    algo_name = "dbscan"

clustering_results = cluster_articles(
    all_articles,
    embeddings,
    algorithm=algo_name,
    n_clusters=fixed_k if (cluster_algo == "KMeans" or (cluster_algo == "Agglomerative (Hierarchical)" and use_fixed_k)) else None,
    distance_threshold=distance_threshold,
    eps=dbscan_eps,
)

clusters = clustering_results["clusters"]
labels = clustering_results["labels"]
metrics = evaluate_clusters(embeddings, labels)

# -----------------------------------------------------------------------------
# Main Navigation Tabs
# -----------------------------------------------------------------------------
tab_feed, tab_clusters, tab_briefing, tab_analytics, tab_export = st.tabs([
    "📰 Ingested News Feed",
    "🧩 Story Clusters & Events",
    "📝 AI Intelligence Briefing",
    "📊 News Analytics & Trends",
    "💾 Export & Academic Methodology",
])

# =============================================================================
# TAB 1: NEWS FEED & SEARCH
# =============================================================================
with tab_feed:
    st.subheader("📰 Ingested Cricket News Feed")
    st.markdown("Browse, filter, and search through verified cricket dispatches across international cricket, IPL, and ICC tournaments.")

    # Search & Filter Controls
    search_col1, search_col2, search_col3 = st.columns([2, 1, 1])
    with search_col1:
        search_query = st.text_input("🔍 Search Headline, Story Content, or Keyword", placeholder="e.g. Rohit, Bumrah, Auction, Broad, Ashes...", key="feed_search")
    with search_col2:
        filter_tourn = st.multiselect(
            "Filter Tournament",
            options=dataset_stats["tournaments"],
            default=[],
            key="feed_tourn_filter",
        )
    with search_col3:
        filter_source = st.multiselect(
            "Filter Source",
            options=dataset_stats["sources"],
            default=[],
            key="feed_source_filter",
        )

    # Filter articles
    filtered_articles = all_articles
    if search_query:
        q = search_query.lower()
        filtered_articles = [
            a for a in filtered_articles
            if q in a.get("title", "").lower() or q in a.get("content", "").lower()
        ]
    if filter_tourn:
        filtered_articles = [a for a in filtered_articles if a.get("tournament") in filter_tourn]
    if filter_source:
        filtered_articles = [a for a in filtered_articles if a.get("source") in filter_source]

    st.markdown(f"**Showing {len(filtered_articles)} of {len(all_articles)} articles**")

    # Display Article Cards using clean Streamlit Native Bordered Containers
    for idx, art in enumerate(filtered_articles):
        with st.container(border=True):
            # Top metadata header row
            c_meta, c_link = st.columns([4, 1])
            with c_meta:
                date_str = art.get('published_at', '')[:10]
                st.markdown(
                    f"<span class='badge badge-source'>{art.get('source')}</span>"
                    f"<span class='badge badge-tournament'>{art.get('tournament')}</span>"
                    f"<span style='font-size:0.8rem; color:#94A3B8; margin-left:6px;'>📅 {date_str}</span>",
                    unsafe_allow_html=True,
                )
            with c_link:
                st.markdown(
                    f"<div style='text-align:right;'><a href='{art.get('url', '#')}' target='_blank' style='color:#38BDF8; font-size:0.85rem; font-weight:600; text-decoration:none;'>Source Link ↗</a></div>",
                    unsafe_allow_html=True,
                )

            # Headline
            st.markdown(f"### {art.get('title')}")

            # Article Body
            st.markdown(f"<p style='color:#E2E8F0; font-size:1.0rem; line-height:1.6;'>{art.get('content')}</p>", unsafe_allow_html=True)

            # Entity Tags
            tag_badges = []
            for p in art.get('players', [])[:4]:
                tag_badges.append(f"<span class='badge badge-entity'>👤 {p}</span>")
            for t in art.get('teams', [])[:2]:
                tag_badges.append(f"<span class='badge badge-source'>🏏 {t}</span>")

            if tag_badges:
                st.markdown(f"**Entities:** {' '.join(tag_badges)}", unsafe_allow_html=True)

# =============================================================================
# TAB 2: STORY CLUSTERS & EVENTS
# =============================================================================
with tab_clusters:
    st.subheader("🧩 Discovered Story Clusters & Event Groups")
    st.caption("Articles grouped automatically by semantic vector similarity.")

    # Clustering Evaluation Bar
    eval_c1, eval_c2, eval_c3, eval_c4 = st.columns(4)
    with eval_c1:
        st.metric("Total Story Clusters", f"{metrics['n_clusters']}")
    with eval_c2:
        st.metric(
            "Silhouette Score",
            f"{metrics['silhouette_score']}",
            help="Range: -1 to +1. Values > 0.3 indicate strong semantic separation between story events.",
        )
    with eval_c3:
        st.metric(
            "Davies-Bouldin Index",
            f"{metrics['davies_bouldin_score']}",
            help="Lower is better. Measures cluster compactness vs separation.",
        )
    with eval_c4:
        st.metric(
            "Calinski-Harabasz",
            f"{metrics['calinski_harabasz_score']}",
            help="Higher is better. Variance ratio criterion.",
        )

    st.info(f"💡 **Academic Evaluation Insight:** {metrics['interpretation']} (Embedding Model: `{embed_info['model_type']}`)")

    # Display Each Story Cluster
    for c in clusters:
        with st.expander(
            f"📌 **Story #{c['cluster_id'] + 1}: {c['title']}** ({c['article_count']} articles | Cohesion: {c['average_similarity']})",
            expanded=(c["cluster_id"] < 2),
        ):
            st.markdown(f"**Lead Representative Headline:** *\"{c['representative_article']['title']}\"*")
            st.markdown("---")
            for art in c["articles"]:
                st.markdown(
                    f"- **[{art['source']}]** [{art['title']}]({art['url']}) "
                    f"<span style='color:#64748B; font-size:0.8rem;'>({art['published_at'][:10]})</span>",
                    unsafe_allow_html=True,
                )

# =============================================================================
# TAB 3: AI INTELLIGENCE BRIEFING & SUMMARIES
# =============================================================================
with tab_briefing:
    st.subheader("📝 Multi-Article Intelligence Briefing")
    st.caption("Synthesizes multi-source coverage of the same cricket event into a single cohesive story with citations.")

    if not clusters:
        st.warning("No clusters available to synthesize.")
    else:
        cluster_options = {
            f"Story #{c['cluster_id'] + 1}: {c['title']} ({c['article_count']} articles)": c['cluster_id']
            for c in clusters
        }
        selected_label = st.selectbox("Select Story Cluster to Synthesize", options=list(cluster_options.keys()))
        selected_cluster_id = cluster_options[selected_label]
        target_cluster = next((c for c in clusters if c["cluster_id"] == selected_cluster_id), clusters[0])

        method_key = "abstractive" if "Abstractive" in summary_engine else "extractive"

        if st.button("⚡ Generate Synthesized Intelligence Briefing", type="primary", use_container_width=True):
            with st.spinner("Synthesizing multi-article coverage across sources..."):
                briefing = synthesize_cluster_briefing(
                    target_cluster,
                    method=method_key,
                    target_sentences=target_sentences,
                )
                st.session_state[f"briefing_{selected_cluster_id}"] = briefing

        briefing_data = st.session_state.get(f"briefing_{selected_cluster_id}")
        if not briefing_data:
            # Auto generate initial briefing for convenience
            briefing_data = synthesize_cluster_briefing(
                target_cluster,
                method=method_key,
                target_sentences=target_sentences,
            )
            st.session_state[f"briefing_{selected_cluster_id}"] = briefing_data

        if briefing_data:
            st.markdown(
                f"""
                <div class="briefing-box">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                        <span style="font-size:0.85rem; font-weight:700; color:#00D26A; text-transform:uppercase; letter-spacing:0.05em;">
                            AI Synthesized Briefing ({briefing_data['method_used']})
                        </span>
                        <span style="font-size:0.85rem; color:#94A3B8;">
                            Sources: <b>{', '.join(briefing_data['unique_sources'])}</b>
                        </span>
                    </div>
                    <div style="font-size:1.15rem; font-weight:600; color:#F8FAFC; margin-bottom:12px; line-height:1.6;">
                        {briefing_data['summary_text']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Key Takeaways
            st.markdown("#### 🎯 Key Executive Takeaways")
            for bullet in briefing_data["bullet_takeaways"]:
                st.markdown(f"• {bullet}")

            # Compression & Efficiency Metrics
            c_col1, c_col2, c_col3 = st.columns(3)
            with c_col1:
                st.metric("Original Coverage Words", f"{briefing_data['original_word_count']}")
            with c_col2:
                st.metric("Synthesized Summary Words", f"{briefing_data['summary_word_count']}")
            with c_col3:
                st.metric("Information Compression Ratio", f"{briefing_data['compression_ratio_pct']}%")

            # Source Provenance & Citations
            st.markdown("#### 🔗 Source Provenance & Citations")
            st.caption("Verifiable citations linking summary facts directly to reporting outlets.")
            for cit in briefing_data["citations"]:
                st.markdown(
                    f"- **{cit['source']}**: [{cit['title']}]({cit['url']}) "
                    f"— *Reported by {cit['author']} ({cit['published_at'][:10]})*"
                )

    # -------------------------------------------------------------------------
    # Custom Single / Multi-Text Ad-Hoc Summarizer
    # -------------------------------------------------------------------------
    st.markdown("---")
    with st.expander("📝 **Paste Any Custom Cricket News to Summarize**", expanded=False):
        st.caption("Paste any raw cricket article, match report, or press release to generate an instant AI summary.")
        custom_input = st.text_area(
            "Article Text",
            placeholder="Paste cricket news article paragraphs here...",
            height=160,
            key="custom_summarize_input"
        )
        custom_sentences = st.slider("Target Sentences", min_value=1, max_value=5, value=3, key="custom_sent_slider")
        if st.button("🚀 Summarize Pasted News", key="btn_custom_summarize"):
            if not custom_input.strip():
                st.warning("Please paste some cricket news text first.")
            else:
                from cricintel.summarization.extractive import summarize_cluster_extractive
                temp_art = [{"title": "Custom Ingested Story", "source": "User Submission", "content": custom_input}]
                custom_res = summarize_cluster_extractive(temp_art, target_sentences=custom_sentences, use_mmr=True)
                
                st.success("Summary Generated!")
                st.markdown(f"**AI Summary:**\n\n{custom_res['summary_text']}")
                st.markdown("**Key Takeaways:**")
                for t in custom_res.get("bullet_takeaways", []):
                    st.markdown(f"• {t}")
                orig_w = len(custom_input.split())
                sum_w = len(custom_res['summary_text'].split())
                comp = round((1 - sum_w / max(1, orig_w)) * 100, 1)
                st.caption(f"Compression: {comp}% ({orig_w} words ➔ {sum_w} words)")

# =============================================================================
# TAB 4: NEWS TRENDS & VISUALIZATIONS
# =============================================================================
with tab_analytics:
    st.subheader("📊 News Trends, Distribution & Topic Intelligence")
    st.caption("Statistical analytics across the ingested cricket news corpus.")

    chart_c1, chart_c2 = st.columns(2)
    with chart_c1:
        fig_tourn = plot_tournament_distribution(all_articles)
        st.plotly_chart(fig_tourn, use_container_width=True)
    with chart_c2:
        fig_cluster = plot_cluster_size_distribution(clusters)
        st.plotly_chart(fig_cluster, use_container_width=True)

    chart_c3, chart_c4 = st.columns(2)
    with chart_c3:
        fig_players = plot_top_entities(all_articles, entity_type="players", top_n=8)
        st.plotly_chart(fig_players, use_container_width=True)
    with chart_c4:
        fig_timeline = plot_publication_timeline(all_articles)
        st.plotly_chart(fig_timeline, use_container_width=True)

# =============================================================================
# TAB 5: EXPORT & ACADEMIC METHODOLOGY
# =============================================================================
with tab_export:
    st.subheader("💾 Export Clustered Dataset & Academic Report")
    st.caption("Download structured intelligence results and review project methodology for submission.")

    # Export Buttons
    export_c1, export_c2 = st.columns(2)
    with export_c1:
        # Prepare JSON export
        export_payload = {
            "metadata": {
                "system": "CricIntel AI — Cricket News Intelligence System",
                "generated_at": datetime.utcnow().isoformat(),
                "total_articles": len(all_articles),
                "total_clusters": len(clusters),
                "metrics": metrics,
            },
            "clusters": [
                {
                    "cluster_id": c["cluster_id"],
                    "title": c["title"],
                    "article_count": c["article_count"],
                    "cohesion": c["average_similarity"],
                    "articles": c["articles"],
                }
                for c in clusters
            ],
        }
        json_str = json.dumps(export_payload, indent=2)
        st.download_button(
            label="📥 Download Clustered Intelligence (JSON)",
            data=json_str,
            file_name="cricintel_clusters_export.json",
            mime="application/json",
            use_container_width=True,
        )

    with export_c2:
        # Prepare CSV export of all articles with their assigned cluster
        csv_rows = []
        for idx, art in enumerate(all_articles):
            assigned_cluster = labels[idx] if idx < len(labels) else -1
            csv_rows.append({
                "article_id": art.get("id"),
                "title": art.get("title"),
                "source": art.get("source"),
                "tournament": art.get("tournament"),
                "cluster_id": assigned_cluster,
                "published_at": art.get("published_at"),
                "url": art.get("url"),
            })
        csv_df = pd.DataFrame(csv_rows)
        csv_str = csv_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Articles with Clusters (CSV)",
            data=csv_str,
            file_name="cricintel_articles_clustered.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.markdown("---")
    st.markdown("### 🎓 Academic Methodology & Technical Explanations")
    st.markdown(
        """
        #### 1. Semantic Vector Embeddings
        - **SentenceTransformers (`all-MiniLM-L6-v2`)**: Maps news headlines and bodies into 384-dimensional dense semantic vector space tuned on semantic textual similarity.
        - **TF-IDF + Latent Semantic Analysis (SVD)**: Provides an instant, dependency-free mathematical fallback. Decomposes high-dimensional term-document frequency into dense singular vector components with $L_2$ normalization such that inner product equals cosine similarity.

        #### 2. Semantic Clustering Formulations
        - **Agglomerative Hierarchical Clustering**: Builds a bottom-up tree based on pairwise cosine distance:
          $$d(u, v) = 1 - \\frac{u \\cdot v}{\\|u\\| \\|v\\|}$$
          Using average linkage, clusters are formed when intra-cluster affinity exceeds the distance threshold.
        - **K-Means Clustering**: Minimizes within-cluster sum-of-squares (inertia):
          $$J = \\sum_{i=1}^{k} \\sum_{x \\in C_i} \\|x - \\mu_i\\|^2$$

        #### 3. Multi-Article Summarization & MMR
        - **TextRank**: Constructs a sentence graph where edge weights reflect semantic overlap. Power iteration calculates eigenvector centrality (PageRank) of sentences.
        - **Maximal Marginal Relevance (MMR)**: Balances query/document relevance against redundancy with already selected sentences:
          $$\\text{MMR} = \\arg\\max_{D_i \\in R \\setminus S} \\left[ \\lambda \\cdot \\text{Sim}_1(D_i, Q) - (1 - \\lambda) \\cdot \\max_{D_j \\in S} \\text{Sim}_2(D_i, D_j) \\right]$$

        #### 4. Validation Metrics
        - **Silhouette Score**: Evaluates if an article is more similar to its assigned cluster ($a$) than neighboring clusters ($b$):
          $$s = \\frac{b - a}{\\max(a, b)}$$
        - **Davies-Bouldin Index**: Evaluates similarity between each cluster and its most similar one (lower is better).
        """
    )
