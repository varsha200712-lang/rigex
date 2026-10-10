"""
Worker Agent for ResolveAI.
Executes the approved plan by synthesizing verified facts from SQLite orders,
retrieved policy evidence, refund eligibility rules, and ticket receipts into
an empathetic, accurate customer response.
"""

import os
import time
from typing import Dict, Any, Optional
from config.settings import get_role_credentials, is_api_key_configured
from database.models import PlannerOutput
from database.db import log_audit


WORKER_SYSTEM_INSTRUCTION = """You are the WORKER Agent for ResolveAI, an intelligent customer support platform.
Your responsibility is to craft an empathetic, accurate, and completely grounded response for the customer based ONLY on the verified evidence provided to you.

STRICT OPERATING RULES:
1. FACTUAL GROUNDING: Never hallucinate or fabricate tracking numbers, refund amounts, order dates, or policy terms. Every single fact must come directly from the provided Tool Context (Orders, Policies, Tickets, or Refund Eligibility).
2. REFUND POLICY COMPLIANCE:
   - If refund status is "Human Approval Required" or "Pending", explain that the request has been submitted to a support supervisor for administrative review. Provide the Ticket ID.
   - If refund status is "Eligible", clearly explain the amount and the timeline (3-5 business days).
   - If refund is "Ineligible", kindly explain why based on verified policy.
3. COMPLAINTS & DELAYS: Provide sincere empathy, state carrier tracking details if known, and highlight the Support Ticket ID created for their case.
4. LANGUAGE ADAPTABILITY: If the customer writes in colloquial Tamil-English (Tanglish) or expresses distress, match their tone with warmth, reassurance, and clarity in polite English (or bilingual Tanglish if appropriate).
5. STRUCTURE: Use clear formatting, bullet points where helpful, and concise paragraphs.
"""


def run_worker(
    customer_message: str,
    plan: PlannerOutput,
    order_context: Optional[Dict[str, Any]] = None,
    policy_context: Optional[Dict[str, Any]] = None,
    refund_context: Optional[Dict[str, Any]] = None,
    ticket_receipt: Optional[Dict[str, Any]] = None
) -> str:
    """
    Execute Worker AI Model with assembled tool context.
    """
    start_time = time.time()
    creds = get_role_credentials("worker")
    worker_model = creds["model"]
    worker_key = creds["api_key"]

    # Build context payload
    context_blocks = []

    if order_context and order_context.get("found"):
        context_blocks.append(f"### VERIFIED ORDER DETAILS:\n{order_context.get('formatted_summary')}")
    elif order_context and not order_context.get("found"):
        context_blocks.append(f"### ORDER SEARCH RESULT:\n{order_context.get('error')}")

    if policy_context and policy_context.get("evidence_text"):
        context_blocks.append(f"### VERIFIED COMPANY POLICY EVIDENCE:\n{policy_context['evidence_text']}")

    if refund_context:
        context_blocks.append(
            f"### REFUND ELIGIBILITY EVALUATION:\n"
            f"- Status: {refund_context.get('status')}\n"
            f"- Eligible: {refund_context.get('eligible')}\n"
            f"- Requires Human Approval: {refund_context.get('requires_human_approval')}\n"
            f"- Amount: ${refund_context.get('amount', 0.0):.2f}\n"
            f"- Rule Applied: {refund_context.get('rule_applied')}\n"
            f"- Explanation: {refund_context.get('explanation')}"
        )

    if ticket_receipt and ticket_receipt.get("success"):
        context_blocks.append(
            f"### SUPPORT TICKET CREATED:\n"
            f"- Ticket ID: {ticket_receipt.get('ticket_id')}\n"
            f"- Status: {ticket_receipt.get('status')}\n"
            f"- Priority: {ticket_receipt.get('priority')}\n"
            f"- Category: {ticket_receipt.get('category')}"
        )

    combined_context = "\n\n".join(context_blocks) if context_blocks else "No specific tool context required (general response)."

    if is_api_key_configured("worker"):
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=worker_key)

            user_prompt = f"""CUSTOMER MESSAGE:
"{customer_message}"

PLANNER INTENT: {plan.intent} (Priority: {plan.priority})
MISSING INFO: {', '.join(plan.missing_information) if plan.missing_information else 'None'}

TOOL & FACTUAL EVIDENCE:
{combined_context}

Generate a clear, professional, empathetic, and 100% grounded customer service response addressing the customer's request.
"""

            response = client.models.generate_content(
                model=worker_model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=WORKER_SYSTEM_INSTRUCTION,
                    temperature=0.2
                )
            )

            response_text = response.text.strip()

            log_audit(
                agent_name="Worker",
                action_type="Response Generation",
                model_used=worker_model,
                input_summary=f"Context items: {len(context_blocks)}",
                output_summary=response_text[:120],
                status="Success",
                metadata={"latency_sec": round(time.time() - start_time, 2)}
            )
            return response_text

        except Exception as e:
            print(f"Worker API Exception: {e}")

    # Fallback / Deterministic Worker Generator
    # Used when offline or during test mocks
    response_parts = []
    
    # Greetings
    if plan.intent == "greeting":
        return "Hello! Welcome to ResolveAI Customer Care. I am your AI assistant. How can I assist you with your order, refund, return, or tracking today?"

    # Missing order ID prompt
    if "order_id" in plan.missing_information:
        return (
            "I would be glad to help you with that! Could you please share your **Order ID** (for example, `ORD-1001` or `ORD-1002`)? "
            "Once you provide the order number, I will immediately pull up the details and resolve your request."
        )

    # Order tracking response
    if plan.intent in ("order_tracking", "delayed_delivery") and order_context and order_context.get("found"):
        status = order_context.get("status")
        eta = order_context.get("estimated_delivery") or "TBD"
        carrier = order_context.get("carrier") or "Carrier partner"
        tracking = order_context.get("tracking_number") or "Pending"
        
        response_parts.append(f"Thank you for contacting us regarding Order **{order_context['order_id']}**.")
        response_parts.append(f"• **Current Status**: `{status}`\n• **Carrier**: {carrier} (Tracking: `{tracking}`)\n• **Estimated Delivery**: {eta}")
        
        if order_context.get("delay_reason"):
            response_parts.append(f"**Carrier Delay Notice**: {order_context['delay_reason']}.")
            if ticket_receipt:
                response_parts.append(f"We have registered priority ticket **{ticket_receipt.get('ticket_id')}** to monitor this shipment.")
        return "\n\n".join(response_parts)

    # Damaged product response
    if plan.intent == "damaged_product":
        response_parts.append("I am so sorry to hear that your item arrived damaged! We understand how disappointing that is.")
        if ticket_receipt:
            response_parts.append(f"A priority support ticket **{ticket_receipt.get('ticket_id')}** has been opened for your case.")
        if refund_context:
            if refund_context.get("requires_human_approval"):
                response_parts.append(f"Because the order amount is ${refund_context.get('amount', 0.0):.2f}, your refund request has been escalated to our supervisor team for immediate authorization.")
            else:
                response_parts.append(f"Per our instant damage policy, a full refund of ${refund_context.get('amount', 0.0):.2f} has been authorized to your original payment method (3-5 business days).")
        return "\n\n".join(response_parts)

    # Refund request response
    if plan.intent == "refund_request" and refund_context:
        if refund_context.get("requires_human_approval"):
            return (
                f"Thank you for your request. Refund request for **${refund_context.get('amount', 0.0):.2f}** on Order **{plan.order_id_extracted or 'your order'}** "
                f"requires supervisor approval under our security guidelines. Support ticket **{ticket_receipt.get('ticket_id') if ticket_receipt else 'TCK-Pending'}** "
                f"has been marked **'Awaiting Approval'**. An administrator will review and authorize your request shortly."
            )
        elif refund_context.get("eligible"):
            return (
                f"Good news! Your refund request has been verified and approved per policy. "
                f"An amount of **${refund_context.get('amount', 0.0):.2f}** will be returned to your original payment method within 3 to 5 business days."
            )

    # Default policy / FAQ answer
    if policy_context and policy_context.get("evidence_text"):
        return (
            f"Here is the verified information regarding our company policy:\n\n"
            f"{policy_context['evidence_text']}\n\n"
            f"Please let me know if you would like me to help file a ticket or initiate a request!"
        )

    return (
        "Thank you for contacting ResolveAI. Your inquiry has been received. "
        "A customer care specialist will follow up with you shortly."
    )
