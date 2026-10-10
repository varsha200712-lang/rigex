"""
Planner Agent for ResolveAI.
Analyzes customer intent, extracts identifiers, assigns urgency and complaint priority,
and constructs a structured execution plan.
"""

import os
import json
import time
from typing import Dict, Any, Optional
from pydantic import ValidationError
from config.settings import get_role_credentials, is_api_key_configured
from database.models import PlannerOutput
from database.db import log_audit
from tools.order_tools import extract_order_id_from_text


PLANNER_SYSTEM_INSTRUCTION = """You are the PLANNER Agent for ResolveAI, an enterprise e-commerce customer service platform.
Your sole job is to analyze the customer's query, classify intent and urgency, identify missing information (such as order ID), and build a step-by-step execution plan.

Intent classifications:
- "order_tracking": Customer asking where their order is or tracking details.
- "delayed_delivery": Customer expressing concern about a delivery taking longer than expected.
- "damaged_product": Customer received broken, defective, or chipped items.
- "return_request": Customer wanting to send an item back.
- "refund_request": Customer demanding money back or reimbursement.
- "general_faq": Questions about shipping rates, warranty, store hours, company policies.
- "complaint": Customer angry or dissatisfied with service/courier.
- "escalation": Customer demanding a human agent or supervisor.
- "greeting": Casual hello, thank you, or general greeting.

Urgency & Priority levels:
- "Low": General FAQs, greetings.
- "Medium": Standard order status, normal return inquiry.
- "High": Delayed delivery, missing item, billing discrepancy.
- "Urgent": Damaged delivery, repeated complaint, supervisor escalation.

Identify if tools are required:
- requires_order_lookup (boolean): true if customer message involves an order.
- requires_rag (boolean): true if policy, warranty, shipping, return, or FAQ info is needed.
- requires_ticket (boolean): true if an issue needs a support ticket (delays, damages, complaints, refunds, escalations).
- requires_human_approval (boolean): true if refund is requested or escalated.

You MUST respond strictly with valid JSON conforming to the requested schema. No markdown fences or commentary.
"""


def run_planner(customer_message: str, session_id: Optional[str] = None) -> PlannerOutput:
    """
    Invoke Planner AI Model to analyze customer query and produce execution plan.
    """
    start_time = time.time()
    extracted_order_id = extract_order_id_from_text(customer_message)
    creds = get_role_credentials("planner")
    planner_model = creds["model"]
    planner_key = creds["api_key"]

    if is_api_key_configured("planner"):
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=planner_key)

            prompt = f"""Customer Message: "{customer_message}"
Detected Order ID in text: {extracted_order_id or 'None'}

Analyze this request and output JSON with the following structure:
{{
  "intent": "...",
  "priority": "Low|Medium|High|Urgent",
  "complaint_category": "Delivery delay|Damaged product|Missing item|Wrong item|Return request|Refund request|Payment issue|General inquiry|Other",
  "requires_order_lookup": true|false,
  "requires_rag": true|false,
  "requires_ticket": true|false,
  "requires_human_approval": true|false,
  "missing_information": [],
  "order_id_extracted": "{extracted_order_id or ''}",
  "steps": ["Step 1...", "Step 2..."],
  "reasoning_summary": "..."
}}
"""

            response = client.models.generate_content(
                model=planner_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=PLANNER_SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )

            raw_text = response.text.strip()
            # Clean possible markdown wrap
            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:].strip()

            parsed = json.loads(raw_text)
            if not parsed.get("order_id_extracted") and extracted_order_id:
                parsed["order_id_extracted"] = extracted_order_id

            # Check if order_id is missing when order lookup is needed
            if parsed.get("requires_order_lookup") and not parsed.get("order_id_extracted"):
                if "order_id" not in parsed.get("missing_information", []):
                    parsed.setdefault("missing_information", []).append("order_id")

            plan = PlannerOutput(**parsed)

            # Log audit
            log_audit(
                agent_name="Planner",
                action_type="Intent Planning",
                model_used=planner_model,
                input_summary=customer_message[:120],
                output_summary=f"Intent: {plan.intent}, Priority: {plan.priority}, Steps: {len(plan.steps)}",
                status="Success",
                metadata={"latency_sec": round(time.time() - start_time, 2), "steps": plan.steps}
            )
            return plan

        except Exception as e:
            # Fallback to deterministic heuristic if API encountered an error
            print(f"Planner API Exception: {e}")

    # Fallback / Demo Heuristic Planner
    lower_msg = customer_message.lower()
    intent = "general_faq"
    priority = "Medium"
    category = "General inquiry"
    requires_order = bool(extracted_order_id)
    requires_rag = True
    requires_ticket = False
    requires_approval = False
    missing_info = []

    if any(w in lower_msg for w in ["track", "status", "where is", "delivery status", "order status", "enga"]):
        intent = "order_tracking"
        priority = "Medium"
        requires_order = True
        if not extracted_order_id:
            missing_info.append("order_id")
    elif any(w in lower_msg for w in ["delay", "late", "delayed", "varala", "late aachu", "innum"]):
        intent = "delayed_delivery"
        priority = "High"
        category = "Delivery delay"
        requires_order = True
        requires_ticket = True
        if not extracted_order_id:
            missing_info.append("order_id")
    elif any(w in lower_msg for w in ["damage", "broken", "cracked", "chipped", "udanjirukku", "damaged"]):
        intent = "damaged_product"
        priority = "Urgent"
        category = "Damaged product"
        requires_order = True
        requires_ticket = True
        requires_approval = True
        if not extracted_order_id:
            missing_info.append("order_id")
    elif any(w in lower_msg for w in ["refund", "money back", "panam", "return money"]):
        intent = "refund_request"
        priority = "High"
        category = "Refund request"
        requires_order = True
        requires_ticket = True
        requires_approval = True
        if not extracted_order_id:
            missing_info.append("order_id")
    elif any(w in lower_msg for w in ["return", "exchange"]):
        intent = "return_request"
        priority = "Medium"
        category = "Return request"
        requires_order = True
        requires_ticket = True
        if not extracted_order_id:
            missing_info.append("order_id")
    elif any(w in lower_msg for w in ["human", "agent", "supervisor", "representative", "call"]):
        intent = "escalation"
        priority = "Urgent"
        category = "Other"
        requires_ticket = True
    elif any(w in lower_msg for w in ["hi", "hello", "hey", "vanakkam"]):
        intent = "greeting"
        priority = "Low"
        requires_rag = False

    plan = PlannerOutput(
        intent=intent,
        priority=priority,
        complaint_category=category,
        requires_order_lookup=requires_order,
        requires_rag=requires_rag,
        requires_ticket=requires_ticket,
        requires_human_approval=requires_approval,
        missing_information=missing_info,
        order_id_extracted=extracted_order_id,
        steps=["Validate request", "Inspect orders/policies", "Formulate grounded response"],
        reasoning_summary="Analyzed query keywords and policy domain mapping."
    )

    log_audit(
        agent_name="Planner",
        action_type="Intent Planning",
        model_used="Deterministic / Demo",
        input_summary=customer_message[:120],
        output_summary=f"Intent: {plan.intent}, Priority: {plan.priority}",
        status="Success",
        metadata={"steps": plan.steps}
    )
    return plan
