"""
Unit tests for ResolveAI Pydantic Validation, Entity Parsing, and Safety Checks.
"""

import pytest
from pydantic import ValidationError
from database.models import PlannerOutput, ReviewerOutput
from tools.order_tools import extract_order_id_from_text
from agents.reviewer import run_reviewer


def test_order_id_extraction_regex():
    """Verify regex correctly extracts various representations of order ID."""
    assert extract_order_id_from_text("Where is my order ORD-1001?") == "ORD-1001"
    assert extract_order_id_from_text("Status for ord-1005 please") == "ORD-1005"
    assert extract_order_id_from_text("Can I cancel #1002?") == "ORD-1002"
    assert extract_order_id_from_text("Package for order 1011 is delayed") == "ORD-1011"
    assert extract_order_id_from_text("Hello, how are you?") is None


def test_planner_output_pydantic_validation():
    """Validate that PlannerOutput enforces schema types."""
    valid_data = {
        "intent": "delayed_delivery",
        "priority": "High",
        "complaint_category": "Delivery delay",
        "requires_order_lookup": True,
        "requires_rag": True,
        "requires_ticket": True,
        "requires_human_approval": False,
        "missing_information": [],
        "order_id_extracted": "ORD-1011",
        "steps": ["Step 1", "Step 2"],
        "reasoning_summary": "Order is marked delayed."
    }
    plan = PlannerOutput(**valid_data)
    assert plan.intent == "delayed_delivery"
    assert plan.priority == "High"
    assert plan.requires_ticket is True


def test_reviewer_rejection_of_unsupported_refund():
    """
    Reviewer must reject worker responses that promise instant refunds
    when deterministic business rules require human approval.
    """
    plan = PlannerOutput(
        intent="refund_request",
        priority="High",
        steps=["Evaluate refund"]
    )
    unauthorized_worker_response = "Great news! Your refund has been processed immediately and money has been sent to your bank account."
    
    refund_context = {
        "status": "Human Approval Required",
        "requires_human_approval": True,
        "amount": 165.00,
        "rule_applied": "High-Value Order Protection ($150+)"
    }
    ticket_receipt = {"ticket_id": "TCK-1002", "status": "Awaiting Approval"}

    review: ReviewerOutput = run_reviewer(
        customer_message="I want my refund now",
        worker_response=unauthorized_worker_response,
        plan=plan,
        refund_context=refund_context,
        ticket_receipt=ticket_receipt
    )

    assert review.approved is False
    assert review.score < 60
    assert len(review.issues) >= 1
    assert review.escalation_required is True
    assert "human administrator approval" in review.issues[0].lower() or "approval" in review.issues[0].lower()
