"""
Order management and investigation tools for ResolveAI.
Deterministic database lookup with customer verification safeguards.
"""

import re
from typing import Dict, Any, Optional
from database.db import get_order_by_id


def extract_order_id_from_text(text: str) -> Optional[str]:
    """
    Extract order ID matching pattern ORD-XXXX or similar from customer message.
    Supports formats like ORD-1001, ord1001, #1001.
    """
    if not text:
        return None
    
    # Primary pattern: ORD-1001 or ord-1001
    match = re.search(r"\b(ORD[-\s]?\d{4})\b", text, re.IGNORECASE)
    if match:
        clean = match.group(1).upper().replace(" ", "-")
        if not clean.startswith("ORD-"):
            clean = f"ORD-{clean[-4:]}"
        return clean

    # Secondary pattern: #1001 or order 1001
    match2 = re.search(r"(?:order|#)\s*(\d{4})\b", text, re.IGNORECASE)
    if match2:
        return f"ORD-{match2.group(1)}"

    return None


def lookup_order(order_id: str, simulated_customer_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Query SQLite for order details with simulated customer authorization check.
    Returns structured order dictionary or error explanation.
    """
    if not order_id:
        return {
            "found": False,
            "error": "No Order ID provided.",
            "data": None
        }

    clean_id = order_id.strip().upper()
    order_data = get_order_by_id(clean_id)

    if not order_data:
        return {
            "found": False,
            "error": f"Order '{clean_id}' was not found in our system. Please check the ID or contact support.",
            "data": None
        }

    # Security check: simulated identity verification
    is_authorized = True
    auth_warning = None
    if simulated_customer_id and order_data.get("customer_id") != simulated_customer_id:
        # In demo mode, we flag simulated authorization
        auth_warning = "Simulated Security Warning: Requesting customer identity does not match order owner."

    # Format human-friendly summary
    item_names = [f"{it['product_name']} (Qty: {it['quantity']}, ${it['unit_price']:.2f})" for it in order_data.get("items", [])]
    items_summary = "; ".join(item_names) if item_names else "No items recorded"

    formatted_summary = (
        f"Order ID: {order_data['order_id']}\n"
        f"Customer: {order_data['customer_name']}\n"
        f"Status: {order_data['status']}\n"
        f"Order Date: {order_data['order_date']}\n"
        f"Estimated Delivery: {order_data.get('estimated_delivery') or 'N/A'}\n"
        f"Actual Delivery: {order_data.get('actual_delivery') or 'Pending'}\n"
        f"Carrier: {order_data.get('carrier') or 'Unassigned'} (Tracking: {order_data.get('tracking_number') or 'None'})\n"
        f"Total: ${order_data['total_amount']:.2f}\n"
        f"Items: {items_summary}\n"
    )
    if order_data.get("delay_reason"):
        formatted_summary += f"Delay Reason: {order_data['delay_reason']}\n"

    return {
        "found": True,
        "order_id": order_data["order_id"],
        "status": order_data["status"],
        "total_amount": order_data["total_amount"],
        "customer_id": order_data["customer_id"],
        "customer_name": order_data["customer_name"],
        "carrier": order_data.get("carrier"),
        "tracking_number": order_data.get("tracking_number"),
        "estimated_delivery": order_data.get("estimated_delivery"),
        "actual_delivery": order_data.get("actual_delivery"),
        "delay_reason": order_data.get("delay_reason"),
        "items": order_data.get("items", []),
        "formatted_summary": formatted_summary,
        "auth_warning": auth_warning
    }
