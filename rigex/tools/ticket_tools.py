"""
Support ticket management tools for ResolveAI.
Creates tickets, attaches refund requests, and updates states deterministically.
"""

from typing import Dict, Any, Optional
from database.db import create_support_ticket, update_ticket_status, create_refund_request, get_all_tickets


def create_customer_ticket(
    customer_id: str,
    category: str,
    priority: str,
    subject: str,
    description: str,
    order_id: Optional[str] = None,
    status: str = "Open"
) -> Dict[str, Any]:
    """
    Create a new support ticket in SQLite with assigned priority and category.
    Returns structured ticket creation receipt.
    """
    clean_cust = customer_id or "CUST-GUEST"
    ticket_id = create_support_ticket(
        customer_id=clean_cust,
        category=category,
        priority=priority,
        subject=subject,
        description=description,
        order_id=order_id,
        status=status
    )
    return {
        "success": True,
        "ticket_id": ticket_id,
        "category": category,
        "priority": priority,
        "status": status,
        "subject": subject,
        "customer_id": clean_cust,
        "order_id": order_id
    }


def record_refund_request_tool(
    ticket_id: str,
    order_id: str,
    customer_id: str,
    amount: float,
    reason: str,
    eligibility_status: str,
    requires_human_approval: bool
) -> Dict[str, Any]:
    """
    Log a refund request tied to a ticket.
    If human approval is required, sets ticket status to 'Awaiting Approval'.
    """
    req_id = create_refund_request(
        ticket_id=ticket_id,
        order_id=order_id,
        customer_id=customer_id or "CUST-GUEST",
        amount=amount,
        reason=reason,
        eligibility_status=eligibility_status,
        requires_human_approval=requires_human_approval
    )

    if requires_human_approval:
        update_ticket_status(ticket_id, "Awaiting Approval", "Refund requires administrator sign-off.")

    return {
        "success": True,
        "request_id": req_id,
        "ticket_id": ticket_id,
        "status": "Pending" if requires_human_approval else "Approved",
        "requires_human_approval": requires_human_approval,
        "amount": amount
    }
