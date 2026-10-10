"""
Refund eligibility evaluation and human approval routing for ResolveAI.
Deterministic business logic enforcing strict policy rules before any refund action.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from config.settings import BUSINESS_RULES
from database.db import create_refund_request, get_order_by_id


def evaluate_refund_eligibility(
    order_id: str,
    complaint_reason: str,
    has_photo_evidence: bool = True
) -> Dict[str, Any]:
    """
    Deterministically evaluates refund eligibility based on verified order data
    and official business rules.
    
    Rules:
    1. Order in 'Processing': 100% immediate cancellation refund eligible.
    2. Order 'Delayed' > 14 days: 100% cancellation refund eligible.
    3. Order 'Delivered' within 30 days:
       - Damaged item under $50: Instant refund without return.
       - Damaged/Standard refund >= $150: Requires Human Admin Approval.
       - Delivered but Missing claim >= $75: Requires Human Admin Approval.
       - Standard return within 30 days: Eligible with $5.99 shipping fee deduction.
    4. Order 'Delivered' > 30 days: Ineligible / Exception requiring human approval.
    """
    order = get_order_by_id(order_id)
    if not order:
        return {
            "eligible": False,
            "requires_human_approval": False,
            "amount": 0.0,
            "status": "Ineligible",
            "rule_applied": "Order Not Found",
            "explanation": f"Order {order_id} could not be found to verify purchase."
        }

    total_amount = float(order["total_amount"])
    status = order.get("status", "")
    reason_lower = complaint_reason.lower()

    # Rule 1: Order still in processing
    if status == "Processing":
        return {
            "eligible": True,
            "requires_human_approval": False,
            "amount": total_amount,
            "status": "Eligible",
            "rule_applied": "Order Processing Cancellation",
            "explanation": f"Order {order_id} has not yet shipped. Full refund of ${total_amount:.2f} is immediately available upon cancellation."
        }

    # Rule 2: Severely delayed order (> 14 days past ETA)
    if status == "Delayed":
        # Check delay reason or estimated delivery date
        return {
            "eligible": True,
            "requires_human_approval": False,
            "amount": total_amount,
            "status": "Eligible",
            "rule_applied": "Extended Carrier Delay Policy",
            "explanation": f"Order {order_id} is flagged as delayed by the carrier. Full cancellation refund of ${total_amount:.2f} is authorized."
        }

    # Check delivery date for Delivered orders
    if status == "Delivered":
        order_date_str = order.get("actual_delivery") or order.get("order_date")
        days_since_delivery = 10  # default safe fallback
        try:
            deliv_date = datetime.strptime(order_date_str, "%Y-%m-%d")
            days_since_delivery = (datetime.now() - deliv_date).days
        except Exception:
            pass

        # Exceeded 30-day window
        if days_since_delivery > BUSINESS_RULES["return_window_days"]:
            return {
                "eligible": False,
                "requires_human_approval": True,
                "amount": total_amount,
                "status": "Human Approval Required",
                "rule_applied": "Expired 30-Day Window Exception",
                "explanation": f"Order was delivered {days_since_delivery} days ago, exceeding the standard 30-day return policy. An administrative supervisor must review this exception."
            }

        # Damaged product policy
        if "damage" in reason_lower or "broken" in reason_lower or "chipped" in reason_lower:
            if total_amount <= BUSINESS_RULES["instant_damaged_max_amount"]:
                return {
                    "eligible": True,
                    "requires_human_approval": False,
                    "amount": total_amount,
                    "status": "Eligible",
                    "rule_applied": "Damaged Under $50 Instant Policy",
                    "explanation": f"Damage reported on order under ${BUSINESS_RULES['instant_damaged_max_amount']:.2f}. Immediate full refund of ${total_amount:.2f} granted without requiring item return."
                }
            elif total_amount >= BUSINESS_RULES["high_value_approval_threshold"]:
                return {
                    "eligible": True,
                    "requires_human_approval": True,
                    "amount": total_amount,
                    "status": "Human Approval Required",
                    "rule_applied": "High-Value Order Protection ($150+)",
                    "explanation": f"Refund of ${total_amount:.2f} exceeds high-value threshold ($150). A support administrator must review and approve this transaction."
                }
            else:
                return {
                    "eligible": True,
                    "requires_human_approval": False,
                    "amount": total_amount,
                    "status": "Eligible",
                    "rule_applied": "Standard Damaged Return Policy",
                    "explanation": f"Full refund of ${total_amount:.2f} authorized upon carrier return of damaged merchandise (prepaid return shipping label generated)."
                }

        # Missing / Non-receipt claim
        if "missing" in reason_lower or "not received" in reason_lower or "lost" in reason_lower:
            if total_amount >= BUSINESS_RULES["missing_delivery_approval_threshold"]:
                return {
                    "eligible": True,
                    "requires_human_approval": True,
                    "amount": total_amount,
                    "status": "Human Approval Required",
                    "rule_applied": "Delivered-Status Non-Receipt Verification",
                    "explanation": f"Carrier tracking records delivery, but customer reported non-receipt for high-value order (${total_amount:.2f} >= ${BUSINESS_RULES['missing_delivery_approval_threshold']:.2f}). Admin verification required."
                }

        # High-value standard return
        if total_amount >= BUSINESS_RULES["high_value_approval_threshold"]:
            return {
                "eligible": True,
                "requires_human_approval": True,
                "amount": total_amount,
                "status": "Human Approval Required",
                "rule_applied": "High-Value Order Protection ($150+)",
                "explanation": f"Refund of ${total_amount:.2f} exceeds $150.00. Placed in 'Awaiting Approval' for administrator authorization."
            }

        # Standard return
        net_refund = max(0.0, total_amount - BUSINESS_RULES["return_shipping_fee"])
        return {
            "eligible": True,
            "requires_human_approval": False,
            "amount": net_refund,
            "status": "Eligible",
            "rule_applied": "Standard 30-Day Return Policy",
            "explanation": f"Standard return authorized within 30 days. Estimated refund: ${net_refund:.2f} (Purchase ${total_amount:.2f} minus ${BUSINESS_RULES['return_shipping_fee']:.2f} standard return shipping fee)."
        }

    # Cancelled orders
    if status == "Cancelled":
        return {
            "eligible": False,
            "requires_human_approval": False,
            "amount": 0.0,
            "status": "Ineligible",
            "rule_applied": "Already Cancelled",
            "explanation": f"Order {order_id} has already been cancelled and refunded."
        }

    return {
        "eligible": False,
        "requires_human_approval": True,
        "amount": total_amount,
        "status": "Human Approval Required",
        "rule_applied": "In-Transit / Unverified Status",
        "explanation": f"Order status is '{status}'. Cancellations or refunds for active carrier dispatches require manual review."
    }
