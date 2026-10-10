"""
Unit tests for ResolveAI Deterministic Refund Eligibility & Business Rules.
Verifies all policy thresholds ($50, $150, 30-day window, processing cancellations).
"""

import pytest
from tools.refund_tools import evaluate_refund_eligibility
from database.seed_data import seed_database


@pytest.fixture(autouse=True)
def setup_db():
    seed_database(force_reseed=False)


def test_instant_damaged_refund_under_50():
    """ORD-1007 is $42.00; damaged item qualifies for instant refund without return."""
    res = evaluate_refund_eligibility("ORD-1007", "Ceramic dripper arrived cracked and chipped.")
    assert res["eligible"] is True
    assert res["requires_human_approval"] is False
    assert res["amount"] == 42.00
    assert "Instant" in res["rule_applied"]


def test_high_value_refund_requires_human_approval():
    """ORD-1008 is $165.00 (>= $150 threshold); requires human administrator approval."""
    res = evaluate_refund_eligibility("ORD-1008", "Item doesn't fit my wall bracket.")
    assert res["eligible"] is True
    assert res["requires_human_approval"] is True
    assert res["status"] == "Human Approval Required"
    assert "High-Value" in res["rule_applied"]


def test_processing_order_cancellation():
    """ORD-1001 is Processing; qualifies for 100% immediate cancellation refund."""
    res = evaluate_refund_eligibility("ORD-1001", "I changed my mind, please cancel.")
    assert res["eligible"] is True
    assert res["requires_human_approval"] is False
    assert res["amount"] == 45.99
    assert "Processing Cancellation" in res["rule_applied"]


def test_delayed_order_cancellation():
    """ORD-1012 is Delayed (> 14 days); qualifies for full cancellation refund."""
    res = evaluate_refund_eligibility("ORD-1012", "Package is severely delayed past ETA.")
    assert res["eligible"] is True
    assert res["requires_human_approval"] is False
    assert "Delay" in res["rule_applied"]


def test_missing_order_nonexistent():
    """Non-existent order should return ineligible with clear explanation."""
    res = evaluate_refund_eligibility("ORD-9999", "I want a refund.")
    assert res["eligible"] is False
    assert res["status"] == "Ineligible"
