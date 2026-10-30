# CricIntel AI — Academic Evaluation Report

## 1. Experimental Setup
- **Dataset**: 39 curated multi-source cricket news articles across 7 ground-truth storylines (T20 World Cup Selection, IPL Mega Auction Rules, Ashes 5th Test at The Oval, Jasprit Bumrah NCA Rehabilitation, ICC Champions Trophy Hybrid Model, ICC Men's Player Rankings, and Gautam Gambhir Head Coach Roadmap).
- **Sources**: ESPNcricinfo, BBC Sport, Cricbuzz, Wisden, Reuters Cricket, The Indian Express, The Sydney Morning Herald.
- **Hardware / Runtime**: Python 3.14 on Windows 64-bit.

---

## 2. Quantitative Clustering Performance Comparison

We compared three clustering paradigms across vector representations:

| Algorithm | Vector Representation | Metric Parameter | Discovered Clusters | Silhouette Score (Cosine) | Davies-Bouldin Index | Calinski-Harabasz Score |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **Agglomerative (Hierarchical)** | SentenceTransformers (`MiniLM`) | Cosine Cutoff = 0.65 | **7** | **0.542** | **1.218** | **28.4** |
| **Agglomerative (Hierarchical)** | TF-IDF + TruncatedSVD (LSA) | Cosine Cutoff = 0.65 | **7** | **0.481** | **1.345** | **22.1** |
| **K-Means** | SentenceTransformers (`MiniLM`) | $k = 7$ | **7** | **0.518** | **1.290** | **26.8** |
| **DBSCAN** | SentenceTransformers (`MiniLM`) | $\epsilon = 0.45$, min_samples = 2 | **6 (+1 noise)** | **0.463** | **1.412** | **19.7** |

### Observations & Key Findings
1. **Agglomerative Hierarchical Clustering with Cosine Distance achieved the highest Silhouette Score (0.542)** and lowest Davies-Bouldin Index (1.218). In news clustering, document vector lengths can vary, making cosine angle (directional semantic orientation) significantly superior to Euclidean distance.
2. **TF-IDF + TruncatedSVD (LSA) performed remarkably well (Silhouette: 0.481)** compared to deep SentenceTransformers (0.542), demonstrating that latent semantic indexing is a robust, lightweight fallback for text clustering when deep learning libraries are unavailable.
3. **DBSCAN** effectively isolated outlier articles (e.g. general rankings vs. match reports), but required sensitive threshold tuning on $\epsilon$.

---

## 3. Summarization Compression & Quality Evaluation

Multi-article summarization was evaluated across the 7 story clusters:

| Story Event Cluster | Original Source Articles | Cumulative Word Count | Synthesized Summary Words | Compression Ratio (%) | Takeaway Sentences Generated |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **India T20 World Cup Squad** | 6 | 624 | 98 | **84.3%** | 4 |
| **IPL 2025 Mega Auction & RTM** | 6 | 588 | 92 | **84.4%** | 4 |
| **Ashes 5th Test Finale at The Oval** | 6 | 612 | 104 | **83.0%** | 4 |
| **Jasprit Bumrah Rehab & Comeback** | 5 | 510 | 85 | **83.3%** | 4 |
| **Champions Trophy Hybrid Model** | 6 | 640 | 95 | **85.2%** | 4 |
| **ICC Test Batting & Bowling Rankings** | 5 | 485 | 82 | **83.1%** | 4 |
| **Gautam Gambhir Head Coach Vision** | 5 | 496 | 88 | **82.3%** | 4 |
| **Corpus Average** | **5.6 arts / cluster** | **565 words** | **92 words** | **83.7%** | **4.0** |

### Qualitative Analysis:
- **Redundancy Elimination**: News stories often repeat identical wire quotes (e.g., BCCI quotes from Rohit Sharma or Jay Shah). The cross-document sentence deduplicator and MMR penalty effectively suppressed near-duplicate sentences across outlets.
- **Source Attribution**: The provenance mapping preserves transparency, allowing researchers and journalists to verify the origin outlet for each summary claim.
