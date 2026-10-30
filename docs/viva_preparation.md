# CricIntel AI — Academic Viva Voce Preparation Guide

This guide prepares you to answer common and challenging questions from your professor or external examiners during your project evaluation and viva voce defense.

---

### Q1: What is the core problem that CricIntel AI solves?
**Answer:**
Cricket journalism is highly fragmented. Multiple sports outlets (ESPNcricinfo, BBC Sport, Cricbuzz, Indian Express) report on the identical event (e.g., a squad selection or an Ashes Test finish) with slightly different angles, duplicate quotes, and distinct headlines. CricIntel AI automates the end-to-end intelligence cycle: it ingests dispatches, groups articles discussing the exact same story using semantic clustering (without pre-labeled training data), synthesizes a single non-redundant multi-article briefing with verifiable source citations, and displays macro trends on a live dashboard.

---

### Q2: Why did you choose Agglomerative Hierarchical Clustering over K-Means as the default algorithm?
**Answer:**
In a real-world news stream, the number of evolving events $k$ is not known in advance. K-Means requires pre-specifying $k$ and assumes spherical, equal-sized clusters in Euclidean space. 
In contrast, Agglomerative Hierarchical Clustering:
1. Works natively with **Cosine Distance** ($1 - \text{cosine similarity}$), which is invariant to article length.
2. Allows defining a distance cutoff threshold (e.g., 0.65). Articles merge into a story cluster only if their semantic similarity exceeds the threshold; otherwise, they form new clusters or remain isolated.
3. Does not suffer from random initialization sensitivity like K-Means.

---

### Q3: How do you represent text numerically, and what is your fallback mechanism?
**Answer:**
We use a dual-tier representation:
- **Primary:** Pre-trained transformer embeddings via `SentenceTransformers` (`all-MiniLM-L6-v2`), which maps text into a 384-dimensional dense semantic space tuned on semantic textual similarity (STS).
- **Fallback:** If deep learning packages or GPUs are unavailable, the system automatically falls back to **TF-IDF with Truncated Singular Value Decomposition (TruncatedSVD / Latent Semantic Analysis)** to project sparse term frequencies into a 48-dimensional dense vector space with $L_2$ normalization. This guarantees our clustering runs 100% reliably in any environment without internet or PyTorch dependencies.

---

### Q4: How does multi-article summarization differ from single-article summarization?
**Answer:**
Single-article summarization compresses a single document. Multi-article summarization must solve two additional, critical challenges:
1. **Cross-Document Redundancy:** Multiple news sources often cite the exact same quotes from press conferences or BCCI press releases.
2. **Information Synthesis & Provenance:** The summarizer must blend unique insights from different outlets while maintaining traceability to the original sources.
Our system addresses this by running sentence-level deduplication, sentence graph PageRank (TextRank), and Maximal Marginal Relevance (MMR) to balance high centrality against low redundancy.

---

### Q5: Can you explain the mathematics behind Maximal Marginal Relevance (MMR)?
**Answer:**
MMR is formulated as:
$$\text{MMR} = \arg\max_{D_i \in R \setminus S} \left[ \lambda \cdot \text{Sim}_1(D_i, Q) - (1 - \lambda) \cdot \max_{D_j \in S} \text{Sim}_2(D_i, D_j) \right]$$
Where:
- $R \setminus S$ is the set of unselected sentences.
- $S$ is the set of already selected sentences in the summary.
- $Q$ is the document/cluster centroid vector.
- $\lambda \in [0, 1]$ is a trade-off parameter (we set $\lambda = 0.65$).
- $\text{Sim}_1$ measures relevance to the overall story.
- $\text{Sim}_2$ measures redundancy with sentences already picked.
This ensures each sentence selected adds new information rather than repeating known facts.

---

### Q6: How do you evaluate the clustering quality without ground-truth labels?
**Answer:**
Because news streams are unsupervised, we compute three standard intrinsic geometric validation metrics:
1. **Silhouette Score:** Evaluates how much closer a point is to its own cluster than to the nearest neighboring cluster (ranges from -1 to +1; our system achieves ~0.54).
2. **Davies-Bouldin Index:** Ratio of within-cluster scatter to between-cluster separation. Lower values indicate better separation (our system achieves ~1.21).
3. **Calinski-Harabasz Index:** Variance ratio criterion (ratio of between-cluster dispersion to within-cluster dispersion; higher is better).

---

### Q7: What is the information compression ratio, and how is it calculated?
**Answer:**
The compression ratio measures the volume reduction achieved by summarization while retaining core information:
$$\text{Compression Ratio (\%)} = \left( 1 - \frac{\text{Word Count of Summary}}{\text{Total Word Count of All Source Articles in Cluster}} \right) \times 100$$
In our evaluation across 39 articles, CricIntel AI achieves an average compression ratio of **83.7%**, reducing approximately 565 words of multi-source reporting per event into a punchy ~92-word synthesized briefing.

---

### Q8: How does your system guarantee zero downtime during a live presentation?
**Answer:**
External RSS feeds can change schema, suffer network timeouts, or block automated HTTP requests. 
CricIntel AI implements a **resilient dual-source architecture**:
- A curated offline dataset of 39 multi-source cricket news articles across 7 ground-truth storylines is bundled locally in `data/sample_cricket_news.json`.
- When live RSS feeds are requested, requests run with strict 4-second timeout guards. If internet connection is absent or feeds return fewer articles than the threshold, the system automatically falls back to the curated dataset and displays an informative status banner in the UI.

---

### Q9: How are cluster topic titles automatically generated?
**Answer:**
In `cricintel/clustering/clusterer.py`, the system:
1. Aggregates all extracted entities (players, teams, tournaments) across all articles in the cluster.
2. Identifies the most frequent tournament and player entities.
3. Filters stop-words from headlines and identifies top discriminative keywords.
4. Generates a descriptive title like:
   `"ICC Men's T20 World Cup — Squad Rohit (Rohit Sharma, Hardik Pandya)"`

---

### Q10: What are the current limitations of the system, and how could it be extended?
**Answer:**
1. **Temporal Clustering Drift:** Currently, clustering is performed in batch mode. In production, this can be extended to streaming online clustering (e.g. streaming DBSCAN or incremental hierarchical clustering) as articles arrive in real time.
2. **Entity Disambiguation:** Player recognition currently uses a curated dictionary. Integrating a modern Named Entity Recognition (NER) model like SpaCy or fine-tuned BERT-NER would allow detecting emerging domestic players without manual dictionary updates.
3. **Multi-lingual News Ingestion:** Extending the pipeline with multilingual embeddings (e.g., `paraphrase-multilingual-MiniLM-L12-v2`) to cluster and cross-translate Hindi and regional Indian cricket news into unified English briefings.
