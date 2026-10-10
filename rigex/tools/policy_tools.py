"""
Policy search and retrieval tools for ResolveAI.
Interfaces between Worker agent and RAG retriever to ground responses in facts.
"""

from typing import Dict, Any, List
from rag.retriever import query_policies, format_retrieved_context


def search_company_policies(query: str, top_k: int = 3) -> Dict[str, Any]:
    """
    Search company policies knowledge base (returns, refunds, shipping, warranty, FAQ).
    Returns grounded evidence citations for the Worker model.
    """
    if not query or not query.strip():
        return {
            "success": False,
            "evidence_text": "No search query provided.",
            "citations": []
        }

    results = query_policies(query, top_k=top_k)
    evidence_text = format_retrieved_context(results)

    citations = [
        {"source": r["source"], "section": r["section"], "score": r["score"]}
        for r in results
    ]

    return {
        "success": len(results) > 0,
        "evidence_text": evidence_text,
        "citations": citations,
        "chunk_count": len(results)
    }
