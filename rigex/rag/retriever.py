"""
RAG Semantic Retriever for ResolveAI.
Queries ChromaDB vector collection using Gemini embeddings, with robust
term-weighted cosine similarity fallback to guarantee zero runtime failures.
"""

import os
import json
import re
import math
from typing import List, Dict, Any, Optional
from config.settings import CHROMA_PERSIST_DIR, EMBEDDING_MODEL, is_api_key_configured
from rag.ingest import get_all_policy_chunks, generate_gemini_embeddings


def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two float vectors."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


def _keyword_semantic_score(query: str, text: str) -> float:
    """Calculate normalized token-overlap and keyword relevance score."""
    q_words = set(re.findall(r"\w+", query.lower()))
    if not q_words:
        return 0.0
    t_words = set(re.findall(r"\w+", text.lower()))
    matches = q_words.intersection(t_words)
    # Boost if key policy terms match
    bonus = 0.0
    key_terms = ["return", "refund", "delayed", "delay", "damaged", "damage", "shipping", "warranty", "cancel", "exchange", "hours", "days"]
    for kt in key_terms:
        if kt in q_words and kt in t_words:
            bonus += 0.15
    base = len(matches) / len(q_words)
    return min(1.0, base + bonus)


def query_policies(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Search policy knowledge base.
    Attempts ChromaDB semantic retrieval first; falls back gracefully to
    keyword-semantic ranking if ChromaDB is initializing or offline.
    """
    if not query or not query.strip():
        return []

    results = []

    # 1. Try ChromaDB
    try:
        import chromadb
        if CHROMA_PERSIST_DIR.exists():
            client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
            collection = client.get_or_create_collection(name="resolveai_policies")

            if collection.count() > 0:
                if is_api_key_configured():
                    query_vecs = generate_gemini_embeddings([query])
                    if query_vecs and len(query_vecs[0]) > 0:
                        chroma_res = collection.query(
                            query_embeddings=query_vecs,
                            n_results=min(top_k, collection.count())
                        )
                    else:
                        chroma_res = collection.query(
                            query_texts=[query],
                            n_results=min(top_k, collection.count())
                        )
                else:
                    chroma_res = collection.query(
                        query_texts=[query],
                        n_results=min(top_k, collection.count())
                    )

                docs = chroma_res.get("documents", [[]])[0]
                metas = chroma_res.get("metadatas", [[]])[0]
                dists = chroma_res.get("distances", [[]])[0] if "distances" in chroma_res else [0.2] * len(docs)

                for doc, meta, dist in zip(docs, metas, dists):
                    score = round(max(0.0, 1.0 - (dist if dist is not None else 0.2)), 3)
                    results.append({
                        "content": doc,
                        "source": meta.get("source", "company_policy.txt"),
                        "section": meta.get("section", "General Policy"),
                        "score": score
                    })

                if results:
                    return results[:top_k]
    except Exception as e:
        # Graceful fallback without crashing
        pass

    # 2. Resilient Fallback: JSON Chunk Semantic Ranking
    chunks = []
    backup_file = CHROMA_PERSIST_DIR / "policy_chunks.json"
    if backup_file.exists():
        try:
            with open(backup_file, "r", encoding="utf-8") as f:
                chunks = json.load(f)
        except Exception:
            chunks = []
    if not chunks:
        chunks = get_all_policy_chunks()

    scored = []
    for c in chunks:
        score = _keyword_semantic_score(query, c["text"] + " " + c.get("section", ""))
        if score > 0.1:
            scored.append({
                "content": c["text"],
                "source": c["source"],
                "section": c.get("section", "General"),
                "score": round(score, 3)
            })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


def format_retrieved_context(results: List[Dict[str, Any]]) -> str:
    """Format retrieved passages into structured evidence citations for models."""
    if not results:
        return "No specific company policy document directly verified this request. Standard human verification required."

    formatted_parts = []
    for idx, item in enumerate(results, 1):
        formatted_parts.append(
            f"--- [EVIDENCE {idx}: {item['source']} | Section: {item['section']} (Relevance: {item['score']})] ---\n"
            f"{item['content']}"
        )
    return "\n\n".join(formatted_parts)
