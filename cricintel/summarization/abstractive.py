"""Abstractive transformer summarization using Hugging Face pipelines with extractive fallback."""

from __future__ import annotations

import logging
from typing import Any, Dict, List
from cricintel.summarization.extractive import summarize_cluster_extractive

logger = logging.getLogger(__name__)

_SUMMARIZER_PIPELINE = None
_PIPELINE_MODEL_NAME = None


def get_abstractive_pipeline(model_name: str = "sshleifer/distilbart-cnn-12-6"):
    """Lazy loader for Hugging Face summarization pipeline."""
    global _SUMMARIZER_PIPELINE, _PIPELINE_MODEL_NAME
    if _SUMMARIZER_PIPELINE is not None and _PIPELINE_MODEL_NAME == model_name:
        return _SUMMARIZER_PIPELINE

    try:
        from transformers import pipeline
        _SUMMARIZER_PIPELINE = pipeline(
            "summarization",
            model=model_name,
            device=-1,  # CPU execution for standard environments
        )
        _PIPELINE_MODEL_NAME = model_name
        return _SUMMARIZER_PIPELINE
    except Exception as e:
        logger.warning(f"Could not load Hugging Face pipeline ({model_name}): {e}")
        return None


def summarize_cluster_abstractive(
    articles: List[Dict[str, Any]],
    model_name: str = "sshleifer/distilbart-cnn-12-6",
    max_length: int = 140,
    min_length: int = 45,
    force_fallback: bool = False,
) -> Dict[str, Any]:
    """Generate an abstractive summary of multiple articles in a cluster.

    Falls back to Extractive MMR/TextRank if Hugging Face pipeline is not loaded.
    """
    if not articles:
        return {
            "summary_text": "No articles available.",
            "bullet_takeaways": [],
            "method": "Abstractive (Empty)",
            "fallback_used": False,
        }

    # Aggregate key paragraphs across the cluster
    combined_texts = [f"{a.get('title', '')}. {a.get('content', '')}" for a in articles]
    full_text = " ".join(combined_texts)

    # Truncate to approximately 800 words to respect transformer context windows
    words = full_text.split()
    truncated_input = " ".join(words[:750])

    if not force_fallback:
        pipe = get_abstractive_pipeline(model_name)
        if pipe is not None:
            try:
                res = pipe(
                    truncated_input,
                    max_length=max_length,
                    min_length=min_length,
                    do_sample=False,
                    truncation=True,
                )
                summary_text = res[0]["summary_text"].strip()

                # Generate takeaways via quick extractive split
                extractive_aux = summarize_cluster_extractive(articles, target_sentences=3)

                return {
                    "summary_text": summary_text,
                    "bullet_takeaways": extractive_aux.get("bullet_takeaways", []),
                    "method": f"Abstractive Transformer ({model_name})",
                    "fallback_used": False,
                    "provenance": extractive_aux.get("provenance", []),
                }
            except Exception as e:
                logger.warning(f"Abstractive generation failed, falling back: {e}")

    # Fallback directly to Extractive TextRank / MMR
    extractive_res = summarize_cluster_extractive(articles, target_sentences=4, use_mmr=True)
    return {
        **extractive_res,
        "method": f"{extractive_res['method']} (Abstractive Fallback)",
        "fallback_used": True,
    }
