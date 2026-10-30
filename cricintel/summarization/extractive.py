"""Extractive TextRank and MMR multi-article summarizer with source provenance."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from cricintel.ingestion.preprocessor import split_into_sentences


def compute_pagerank(
    similarity_matrix: np.ndarray, damping: float = 0.85, max_iter: int = 60, tol: float = 1e-4
) -> np.ndarray:
    """Compute PageRank scores using power iteration over sentence similarity graph."""
    n = similarity_matrix.shape[0]
    if n == 0:
        return np.zeros(0)
    if n == 1:
        return np.ones(1)

    # Zero out diagonal (no self-loops)
    np.fill_diagonal(similarity_matrix, 0.0)

    row_sums = similarity_matrix.sum(axis=1)
    # Handle disconnected nodes
    zero_rows = row_sums == 0
    row_sums[zero_rows] = 1.0

    transition_matrix = similarity_matrix / row_sums[:, np.newaxis]
    transition_matrix[zero_rows] = 1.0 / n

    scores = np.ones(n) / n
    uniform_vector = np.ones(n) / n

    for _ in range(max_iter):
        next_scores = (1 - damping) * uniform_vector + damping * transition_matrix.T.dot(scores)
        if np.linalg.norm(next_scores - scores, 1) < tol:
            break
        scores = next_scores

    return scores


def select_sentences_mmr(
    sentence_vectors: np.ndarray,
    doc_vector: np.ndarray,
    lambda_param: float = 0.65,
    num_sentences: int = 4,
) -> List[int]:
    """Maximal Marginal Relevance (MMR) for selecting salient and non-redundant sentences."""
    n_sentences = sentence_vectors.shape[0]
    if n_sentences <= num_sentences:
        return list(range(n_sentences))

    # Similarity of each sentence to the overall story vector
    relevance_scores = cosine_similarity(sentence_vectors, doc_vector).flatten()

    selected_indices: List[int] = []
    unselected_indices = list(range(n_sentences))

    # First pick sentence with highest overall relevance
    first_pick = int(np.argmax(relevance_scores))
    selected_indices.append(first_pick)
    unselected_indices.remove(first_pick)

    # Iteratively pick sentences balancing relevance and novelty
    for _ in range(min(num_sentences - 1, len(unselected_indices))):
        best_score = -float("inf")
        best_candidate = unselected_indices[0]

        for cand in unselected_indices:
            cand_vector = sentence_vectors[cand:cand + 1]
            selected_vectors = sentence_vectors[selected_indices]

            # Max similarity to already selected sentences
            redundancy = np.max(cosine_similarity(cand_vector, selected_vectors))
            relevance = relevance_scores[cand]

            # MMR formula
            mmr_score = lambda_param * relevance - (1 - lambda_param) * redundancy

            if mmr_score > best_score:
                best_score = mmr_score
                best_candidate = cand

        selected_indices.append(best_candidate)
        unselected_indices.remove(best_candidate)

    # Sort selected indices by their original appearance order for coherence
    return sorted(selected_indices)


def summarize_cluster_extractive(
    articles: List[Dict[str, Any]],
    target_sentences: int = 4,
    use_mmr: bool = True,
) -> Dict[str, Any]:
    """Synthesize multi-article cluster into an extractive summary with source tracking."""
    if not articles:
        return {
            "summary_text": "No articles available to summarize.",
            "bullet_takeaways": [],
            "method": "Extractive TextRank",
            "sentence_count": 0,
            "provenance": [],
        }

    # Collect sentences from all articles in cluster
    candidate_sentences: List[Tuple[str, str, str]] = []  # (sentence_text, source_name, article_title)
    seen_norm_sentences = set()

    for art in articles:
        source_name = art.get("source", "Unknown")
        art_title = art.get("title", "")
        body = art.get("content", "")

        sentences = split_into_sentences(body)
        for s in sentences:
            norm_s = re.sub(r"[^\w\s]", "", s.lower()).strip()
            # Deduplicate cross-source identical sentences
            if norm_s and len(norm_s) > 25 and norm_s not in seen_norm_sentences:
                seen_norm_sentences.add(norm_s)
                candidate_sentences.append((s, source_name, art_title))

    if not candidate_sentences:
        # Fallback to article titles
        candidate_sentences = [(art.get("title", ""), art.get("source", "Unknown"), art.get("title", "")) for art in articles]

    if len(candidate_sentences) <= target_sentences:
        summary_text = " ".join([item[0] for item in candidate_sentences])
        bullet_takeaways = [item[0] for item in candidate_sentences]
        provenance = [{"sentence": item[0], "source": item[1], "headline": item[2]} for item in candidate_sentences]
        return {
            "summary_text": summary_text,
            "bullet_takeaways": bullet_takeaways,
            "method": "Extractive Pass-through",
            "sentence_count": len(candidate_sentences),
            "provenance": provenance,
        }

    # Vectorize sentences with TF-IDF
    texts = [item[0] for item in candidate_sentences]
    try:
        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1)
        sentence_matrix = vectorizer.fit_transform(texts)
    except Exception:
        vectorizer = TfidfVectorizer(min_df=1)
        sentence_matrix = vectorizer.fit_transform(texts)

    if use_mmr and sentence_matrix.shape[0] > target_sentences:
        # Overall cluster document vector
        doc_vector = np.asarray(sentence_matrix.mean(axis=0))
        selected_indices = select_sentences_mmr(
            sentence_matrix.toarray(), doc_vector, num_sentences=target_sentences
        )
        method_name = "Extractive MMR (Maximal Marginal Relevance)"
    else:
        # Graph-based TextRank
        sim_matrix = cosine_similarity(sentence_matrix)
        scores = compute_pagerank(sim_matrix)
        ranked_indices = np.argsort(scores)[::-1]
        top_k = ranked_indices[:target_sentences]
        selected_indices = sorted(top_k.tolist())
        method_name = "Extractive TextRank (Graph Centrality)"

    selected_items = [candidate_sentences[i] for i in selected_indices]
    summary_text = " ".join([item[0] for item in selected_items])
    bullet_takeaways = [item[0] for item in selected_items]
    provenance = [
        {"sentence": item[0], "source": item[1], "headline": item[2]}
        for item in selected_items
    ]

    return {
        "summary_text": summary_text,
        "bullet_takeaways": bullet_takeaways,
        "method": method_name,
        "sentence_count": len(selected_items),
        "provenance": provenance,
    }
