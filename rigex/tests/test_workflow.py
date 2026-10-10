"""
Unit & Integration tests for ResolveAI RAG Retrieval and Multi-Agent Workflow.
"""

import pytest
from rag.retriever import query_policies, format_retrieved_context
from rag.ingest import index_knowledge_base
from workflows.customer_service_graph import run_customer_service_workflow
from config.settings import test_gemini_connection as check_gemini_connection, is_api_key_configured


@pytest.fixture(scope="session", autouse=True)
def ensure_rag_indexed():
    """Ensure knowledge base is indexed before running retriever tests."""
    index_knowledge_base()


def test_rag_retrieval_returns_relevant_policy():
    """Verify retriever retrieves matching chunks with sources for return inquiry."""
    results = query_policies("What is your standard return policy window?", top_k=2)
    assert len(results) >= 1
    top_result = results[0]
    assert "source" in top_result
    assert "section" in top_result
    assert "content" in top_result
    assert top_result["score"] > 0.0

    formatted = format_retrieved_context(results)
    assert "return_policy.txt" in formatted or "EVIDENCE" in formatted


def test_workflow_order_tracking_end_to_end():
    """Verify complete LangGraph workflow executes for order inquiry."""
    res = run_customer_service_workflow(
        message="Where is my order ORD-1001?",
        session_id="test_session_workflow_01"
    )
    assert res is not None
    assert "final_response" in res
    assert len(res["final_response"]) > 20
    assert "status_steps" in res
    assert len(res["status_steps"]) >= 3
    # Verify order facts reached the response
    assert "ORD-1001" in res["final_response"] or "Processing" in res["final_response"]


def test_workflow_damaged_item_creates_ticket():
    """Verify reporting damaged product triggers support ticket and refund rule."""
    res = run_customer_service_workflow(
        message="My mug for ORD-1007 arrived broken and chipped. Please help.",
        session_id="test_session_workflow_02"
    )
    assert res is not None
    assert "final_response" in res
    assert res.get("ticket_receipt") is not None
    assert res["ticket_receipt"]["ticket_id"].startswith("TCK-")


def test_live_gemini_connection_if_configured():
    """Live API test that runs if GEMINI_API_KEY is configured."""
    if is_api_key_configured():
        ok, msg = check_gemini_connection()
        if not ok and ("quota" in msg.lower() or "429" in msg or "resource_exhausted" in msg.lower()):
            pytest.skip(f"Live Gemini API quota reached: {msg}")
        assert ok is True, f"Live Gemini API connection failed: {msg}"
    else:
        pytest.skip("GEMINI_API_KEY not configured, skipping live API call.")
