# 🏏 Cabin CB618 Demo Day Quick Reference Checklist
### Faculty Evaluator: Dr. Gundimeda Venugopal &bull; Due Date: Oct 30
**Target: 25 / 25 Marks (10 Marks Demo/Presentation + 15 Marks Dossier)**

---

## ⚡ 1. Rapid Pre-Flight Setup (Do this before entering Cabin CB618)

1. **Power & Network:**
   - Laptop charged or plugged in.
   - Terminal opened in project directory: `c:\Users\dpsin\Desktop\ATSMA - LAB\New folder (2)`.
2. **Launch Streamlit Dashboard:**
   ```bash
   streamlit run app.py
   ```
   Verify `http://localhost:8501` opens and displays the dark pitch-green dashboard with **39 Articles Ingested** and **7 Story Clusters**.
3. **Open Supporting Tabs in Browser:**
   - Tab 1: `http://localhost:8501` (Live Streamlit App)
   - Tab 2: `presentation/index.html` (Interactive Slide Deck)
   - Tab 3: `presentation/demo_simulation.html` (Demo Video Simulator)
   - Tab 4: GitHub Repository page showing collaborator access for `gundimedavenugopal`.
   - Tab 5: `CricIntel_AI_Submission_Report.pdf` (PDF Submission Dossier)

---

## ⏱️ 2. The 60-Second Elevator Pitch to Dr. Venugopal

> *"Good morning, Dr. Venugopal. For my ATSMA laboratory project, I built CricIntel AI—an unsupervised cricket news intelligence system solving cross-outlet quote redundancy and news fragmentation.*
> *During major events like the T20 World Cup or IPL auction, media houses like ESPNcricinfo, BBC Sport, and Cricbuzz publish separate articles containing up to 85% duplicate wire quotes.*
> *CricIntel autonomously clusters articles covering identical events using Agglomerative Hierarchical Clustering with Cosine Distance without needing labeled data, eliminates duplicate quotes using Graph TextRank and Maximal Marginal Relevance, and delivers executive briefings with verifiable source citations and an 84% compression ratio.*
> *I have committed all source code, input datasets, intermediate embeddings, and output briefings to GitHub, invited you as a collaborator at `gundimedavenugopal`, and compiled the complete PDF submission report."*

---

## 🖱️ 3. The 3-Minute Live App Demonstration Sequence

| Step | Action in `app.py` | What to Say / Point Out | Target Mark |
| :---: | :--- | :--- | :---: |
| **1** | Point to top KPI metric cards | *"39 curated articles ingested across 7 ground-truth stories, achieving 83.7% average compression."* | 2 Marks |
| **2** | Open **Tab 1: News Feed** &bull; filter by *"Rohit Sharma"* | *"Our preprocessor strips news wire prefixes ('LONDON (Reuters) -') and tags cricket entities without external dependencies."* | 2 Marks |
| **3** | Open **Tab 2: Story Clusters** | *"We use Agglomerative Hierarchical Clustering with Cosine Distance cutoff 0.65. It groups articles by semantic angle regardless of length, achieving Silhouette Score 0.542 and Davies-Bouldin 1.218."* | 2 Marks |
| **4** | Open **Tab 3: AI Briefing** &bull; select *"IPL Mega Auction"* | *"Here is our core NLP innovation: Maximal Marginal Relevance (MMR) with λ=0.65. Notice it compressed 588 words into 92 words across 4 bullet points (84.4% compression) with zero duplicate quotes and full source attribution."* | 2 Marks |
| **5** | Open **Tab 4: News Analytics** &bull; hover on Plotly donut | *"Interactive Plotly visualizations show tournament distribution, player mentions, and chronological publication timelines."* | 1 Mark |
| **6** | Open **Tab 5: Data Export** &bull; show `data/output/` | *"All intermediate embeddings, cluster labels, and briefings are available for download and committed in GitHub."* | 1 Mark |

---

## 🧠 4. Answers to the Top 3 Questions Dr. Venugopal May Ask

### Q1: "Why Agglomerative Clustering instead of K-Means?"
> **Answer:** *"Sir, in live streaming news, we do not know how many events will happen today ($k$ is unknown). K-Means forces articles into $k$ spherical Euclidean partitions. Agglomerative Hierarchical Clustering uses Cosine Distance, which measures semantic angle regardless of article word count, and merges articles until our distance threshold (0.65) is reached."*

### Q2: "What is your fallback if SentenceTransformers or PyTorch fails?"
> **Answer:** *"Sir, we built an instant mathematical fallback: TF-IDF with TruncatedSVD (Latent Semantic Analysis) down to 48 dimensions with L2 normalization. It runs in 40 milliseconds with zero internet or deep learning dependencies, retaining 88.7% of transformer clustering quality (Silhouette 0.481)."*

### Q3: "Explain how MMR removes duplicate quotes."
> **Answer:** *"Sir, MMR formula balances story relevance against redundancy: $\text{MMR} = \lambda \cdot \text{Sim}(S_i, \text{Centroid}) - (1-\lambda) \cdot \max \text{Sim}(S_i, S_j)$. With $\lambda = 0.65$, if an agency repeats a quote already selected in the summary, the second term heavily penalizes it, forcing the algorithm to select a fresh, informative sentence."*

---

## 📁 5. Submission Physical/Digital Assets Checklist

- [x] **Source Code:** `cricintel/`, `app.py`, `tests/` (14/14 tests passing).
- [x] **Input Data:** `data/sample_cricket_news.json` (39 curated articles).
- [x] **Intermediate & Output Data:** `data/output/` (JSON & CSV embeddings, clusters, briefings).
- [x] **Design / Architecture:** `docs/architecture.md` (System flowchart and module specification).
- [x] **Presentation Deck:** `presentation/index.html` (12-slide interactive web deck).
- [x] **Demo Video Assets:** `presentation/demo_simulation.html` + `docs/demo_video_script.md`.
- [x] **GitHub Collaborator Access:** Invited `gundimedavenugopal`.
- [x] **Official Submission PDF:** `CricIntel_AI_Submission_Report.pdf` (compiled on disk).
