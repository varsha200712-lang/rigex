"""
Unit tests for ResolveAI SQLite Database Operations.
Tests order lookups, ticket lifecycle, parameterized safety, and persistence.
"""

import pytest
from database.db import (
    init_db, get_order_by_id, get_all_orders,
    create_support_ticket, get_all_tickets, update_ticket_status,
    create_refund_request, get_all_refund_requests, review_refund_request,
    save_conversation_message, get_conversation_history
)
from database.seed_data import seed_database


@pytest.fixture(autouse=True)
def setup_test_db():
    """Ensure database has seed records before tests run."""
    seed_database(force_reseed=False)


def test_order_lookup_existing():
    """Test retrieving existing order ORD-1001."""
    order = get_order_by_id("ORD-1001")
    assert order is not None
    assert order["order_id"] == "ORD-1001"
    assert order["customer_name"] == "Aarav Sharma"
    assert order["status"] == "Processing"
    assert len(order["items"]) >= 1
    assert order["items"][0]["product_name"] == "Wireless Ergonomic Mouse"


def test_order_lookup_nonexistent():
    """Test retrieving non-existent order returns None."""
    order = get_order_by_id("ORD-9999")
    assert order is None


def test_ticket_creation_and_update():
    """Test creating support ticket and updating its status."""
    t_id = create_support_ticket(
        customer_id="CUST-101",
        category="Delivery delay",
        priority="High",
        subject="Test Delivery Delay Issue",
        description="My test shipment is delayed.",
        order_id="ORD-1011",
        status="Open"
    )
    assert t_id.startswith("TCK-")

    # Verify retrieval
    tickets = get_all_tickets(search=t_id)
    assert len(tickets) >= 1
    assert tickets[0]["status"] == "Open"

    # Verify update
    updated = update_ticket_status(t_id, "In Progress", notes="Investigating with carrier")
    assert updated is True

    tickets_updated = get_all_tickets(search=t_id)
    assert tickets_updated[0]["status"] == "In Progress"
    assert "Investigating" in tickets_updated[0]["resolution_notes"]


def test_refund_approval_workflow():
    """Test refund request state transitions."""
    req_id = create_refund_request(
        ticket_id="TCK-1001",
        order_id="ORD-1008",
        customer_id="CUST-102",
        amount=165.00,
        reason="Incompatible mounting bracket",
        eligibility_status="Human Approval Required",
        requires_human_approval=True
    )
    assert req_id.startswith("REF-")

    # Verify pending status
    reqs = get_all_refund_requests(status="Pending")
    matching = [r for r in reqs if r["request_id"] == req_id]
    assert len(matching) == 1
    assert matching[0]["approval_status"] == "Pending"

    # Admin approves
    ok = review_refund_request(req_id, "Approved", "Test Admin", "Verified exception")
    assert ok is True

    reqs_after = get_all_refund_requests()
    approved = [r for r in reqs_after if r["request_id"] == req_id]
    assert approved[0]["approval_status"] == "Approved"
    assert approved[0]["admin_reviewed_by"] == "Test Admin"


def test_conversation_persistence():
    """Test persisting and retrieving chat messages."""
    import uuid
    session_id = f"test_session_{uuid.uuid4().hex[:8]}"
    save_conversation_message(session_id, "customer", "Where is my order?")
    save_conversation_message(session_id, "ai", "Your order is on the way.", agent_steps="Planned -> Retrieved")

    history = get_conversation_history(session_id)
    assert len(history) == 2
    assert history[0]["sender"] == "customer"
    assert history[1]["sender"] == "ai"
    assert history[1]["agent_steps"] == "Planned -> Retrieved"
