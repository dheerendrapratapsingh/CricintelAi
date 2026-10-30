# CricIntel AI — System Architecture & Dataflow

## 1. Executive Summary
**CricIntel AI** is an intelligent information processing pipeline and analytics dashboard engineered for cricket news intelligence. It addresses the challenges of fragmented reporting, duplicate coverage across sports outlets, and cross-source noise by combining **Dual-Source Ingestion**, **Semantic Vector Embeddings**, **Unsupervised Story Clustering**, and **Multi-Document Extractive/Abstractive Summarization**.

---

## 2. Mermaid System Architecture Diagram

```mermaid
flowchart TD
    subgraph Data_Ingestion ["1. Ingestion Layer"]
        RSS["Live RSS Feeds\n(ESPNcricinfo, BBC Sport, NDTV)"] -->|"HTTP / Timeout Guard"| Parser["RSS Parser & Sanitizer"]
        Sample["Curated Offline Dataset\n(39 Multi-Source Articles)"] --> Loader["Sample Loader"]
        Parser -->|"Fallback on Failure"| Deduper["Deduplication & Entity Tagger"]
        Loader --> Deduper
    end

    subgraph NLP_Pipeline ["2. NLP & Semantic Processing"]
        Deduper -->|"Cleaned Text & Metadata"| Embedder["Semantic Vector Embedder"]
        Embedder -->|"Priority 1: Deep Semantic"| ST["SentenceTransformers (all-MiniLM-L6-v2)"]
        Embedder -->|"Priority 2: Fast Fallback"| LSA["TF-IDF + TruncatedSVD (LSA 48-dim)"]
        ST --> Norm["L2 Unit Vector Normalization"]
        LSA --> Norm
    end

    subgraph Clustering_Engine ["3. Semantic Story Clustering"]
        Norm --> Agglom["Agglomerative Clustering\n(Cosine Distance / Average Linkage)"]
        Norm --> KMeans["K-Means Partitional Clustering"]
        Norm --> DBSCAN["DBSCAN Density Clustering"]
        Agglom --> ClusterEval["Cluster Validation Metrics\n(Silhouette, Davies-Bouldin, Calinski-Harabasz)"]
        KMeans --> ClusterEval
        DBSCAN --> ClusterEval
    end

    subgraph Summarization_Engine ["4. Multi-Article Summarization"]
        ClusterEval --> Centroid["Cluster Centroid & Representative Article"]
        Centroid --> SentFilter["Cross-Document Sentence Deduplication"]
        SentFilter --> MMR["Extractive MMR & TextRank (Graph Centrality)"]
        SentFilter --> HF["Abstractive Transformer (BART/T5)"]
        MMR --> Briefing["Synthesized Story Briefing + Citations + Compression Metric"]
        HF --> Briefing
    end

    subgraph Presentation_Layer ["5. Streamlit Dashboard & Analytics"]
        Briefing --> UI_Briefing["AI Intelligence Briefing Tab"]
        ClusterEval --> UI_Clusters["Story Clusters & Cohesion Tab"]
        Deduper --> UI_Feed["News Feed & Multi-Faceted Search Tab"]
        Deduper --> UI_Plots["Plotly Analytics (Tournaments, Players, Timeline)"]
        Briefing --> UI_Export["JSON / CSV Data Export Tab"]
    end
```

---

## 3. Component Breakdown

### 3.1 Data Ingestion (`cricintel/ingestion/`)
- **`sample_loader.py`**: Loads 39 realistic cricket articles covering 7 major events from major outlets (ESPNcricinfo, BBC Sport, Cricbuzz, Wisden, Reuters, Indian Express). Guarantees zero downtime during offline demonstrations.
- **`rss_fetcher.py`**: Queries live cricket RSS endpoints with configurable per-feed timeouts (default 4 seconds), custom user-agent headers, and automatic failover.
- **`preprocessor.py`**: Strips markup, cleans wire service prefixes (e.g., `LONDON (Reuters) -`), splits text into valid sentence boundaries, and identifies players, teams, and tournaments via curated entity pattern matching.

### 3.2 Semantic Clustering (`cricintel/clustering/`)
- **`embedder.py`**: Generates dense semantic representations. Primary: `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional). Secondary mathematical fallback: `TfidfVectorizer` (sublinear term frequency, ngram 1-2) with `TruncatedSVD` (LSA) and L2 unit-norm scaling.
- **`clusterer.py`**: Groups vectors into event clusters using Agglomerative Hierarchical Clustering with average linkage and cosine distance. Automatically extracts cluster theme titles based on top entities and salient title tokens.
- **`metrics.py`**: Computes mathematical validation metrics:
  - **Silhouette Score**: Evaluates cluster cohesion vs separation.
  - **Davies-Bouldin Index**: Evaluates similarity between each cluster and its closest peer.
  - **Calinski-Harabasz**: Computes between-to-within variance ratio.

### 3.3 Multi-Article Summarization (`cricintel/summarization/`)
- **`extractive.py`**: Implements Graph-based TextRank (eigenvector power iteration) and Maximal Marginal Relevance (MMR) with lambda balancing relevance against redundancy.
- **`abstractive.py`**: Integrates Hugging Face sequence-to-sequence pipelines (`distilbart-cnn-12-6` / `bart-large-cnn`) with token chunking.
- **`multi_doc.py`**: Synthesizes the overall briefing, chronological reporting timeline, source attribution list, and compression ratio.

### 3.4 Interactive Dashboard (`app.py` & `cricintel/analytics/`)
- Pure Streamlit application with custom CSS dark/pitch-green theme.
- Responsive Plotly charts: tournament distribution donut, top player mentions bar chart, cluster volume & cohesion viridis chart, and reporting timeline scatter plot.
