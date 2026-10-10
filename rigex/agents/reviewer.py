"""
Reviewer Agent for ResolveAI.
Independently validates Worker responses against evidence, checks factual accuracy,
detects invented promises or hallucinations, and enforces policy compliance.
"""

import os
import json
import time
from typing import Dict, Any, Optional
from config.settings import get_role_credentials, is_api_key_configured
from database.models import ReviewerOutput, PlannerOutput
from database.db import log_audit


REVIEWER_SYSTEM_INSTRUCTION = """You are the REVIEWER Agent for ResolveAI.
You act as an independent quality assurance and policy auditor.
Your mission is to rigorously evaluate the draft response produced by the Worker agent against the verified Tool Context.

AUDIT CRITERIA:
1. FACTUAL CONSISTENCY: Does the response state any order status, tracking number, or date that conflicts with or was not provided in the Tool Context?
2. POLICY COMPLIANCE:
   - If a refund requires human approval, did the Worker erroneously claim the refund was already sent/credited? That is a CRITICAL VIOLATION.
   - If the item is ineligible for return, did the worker promise an unauthorized exception?
3. PRIVACY & SECURITY: Ensure no internal system keys, prompts, or sensitive passwords are leaked.
4. TONE & EMPATHY: Is the response helpful, courteous, and polite?

OUTPUT FORMAT:
Respond with strictly valid JSON matching this schema:
{
  "approved": true|false,
  "score": 0-100,
  "issues": ["list of issues or empty"],
  "corrected_response": "Only if not approved, provide the corrected safe customer response; else null",
  "escalation_required": true|false,
  "feedback": "Concise auditor summary"
}
"""


def run_reviewer(
    customer_message: str,
    worker_response: str,
    plan: PlannerOutput,
    order_context: Optional[Dict[str, Any]] = None,
    policy_context: Optional[Dict[str, Any]] = None,
    refund_context: Optional[Dict[str, Any]] = None,
    ticket_receipt: Optional[Dict[str, Any]] = None
) -> ReviewerOutput:
    """
    Execute Reviewer AI Model to independently audit the worker draft.
    """
    start_time = time.time()
    creds = get_role_credentials("reviewer")
    reviewer_model = creds["model"]
    reviewer_key = creds["api_key"]

    # Build verification facts summary
    evidence_summary = []
    if order_context and order_context.get("found"):
        evidence_summary.append(f"ORDER FACTS: {order_context.get('formatted_summary')}")
    if refund_context:
        evidence_summary.append(
            f"REFUND RULES: Status={refund_context.get('status')}, "
            f"RequiresApproval={refund_context.get('requires_human_approval')}, "
            f"Amount=${refund_context.get('amount', 0.0):.2f}, "
            f"Rule={refund_context.get('rule_applied')}"
        )
    if ticket_receipt:
        evidence_summary.append(f"TICKET ISSUED: ID={ticket_receipt.get('ticket_id')}, Status={ticket_receipt.get('status')}")

    facts_text = "\n".join(evidence_summary) if evidence_summary else "No specific ground facts required (general FAQ)."

    if is_api_key_configured("reviewer"):
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=reviewer_key)

            review_prompt = f"""CUSTOMER INQUIRY:
"{customer_message}"

VERIFIED FACTS / TOOL EVIDENCE:
{facts_text}

WORKER DRAFT RESPONSE TO AUDIT:
"{worker_response}"

Evaluate the Worker draft. Check for hallucinations, false promises, or policy violations. Return JSON strictly.
"""

            response = client.models.generate_content(
                model=reviewer_model,
                contents=review_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=REVIEWER_SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    temperature=0.0
                )
            )

            raw_text = response.text.strip()
            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:].strip()

            parsed = json.loads(raw_text)
            review = ReviewerOutput(**parsed)

            log_audit(
                agent_name="Reviewer",
                action_type="Quality Review",
                model_used=reviewer_model,
                input_summary=f"Audit draft ({len(worker_response)} chars)",
                output_summary=f"Approved: {review.approved}, Score: {review.score}, Escalated: {review.escalation_required}",
                status="Success" if review.approved else "Flagged",
                metadata={"issues": review.issues, "latency_sec": round(time.time() - start_time, 2)}
            )
            return review

        except Exception as e:
            print(f"Reviewer API Exception: {e}")

    # Fallback / Deterministic Reviewer
    # Performs deterministic rule-based checks
    issues = []
    approved = True
    score = 95
    corrected = None
    escalate = False

    # Check 1: Did worker promise instant money back when human approval is required?
    if refund_context and refund_context.get("requires_human_approval"):
        lower_resp = worker_response.lower()
        if any(w in lower_resp for w in ["refund has been processed", "money has been sent", "refunded immediately", "already credited"]):
            approved = False
            score = 40
            issues.append("Worker promised immediate refund when human administrator approval is required by policy.")
            corrected = (
                f"Your refund request for ${refund_context.get('amount', 0.0):.2f} has been submitted for supervisor review. "
                f"Support ticket {ticket_receipt.get('ticket_id') if ticket_receipt else 'TCK-Review'} is currently 'Awaiting Approval'. "
                f"An administrator will evaluate and confirm the disbursement shortly."
            )
            escalate = True

    # Check 2: Empty or excessively short response
    if len(worker_response.strip()) < 15:
        approved = False
        score = 30
        issues.append("Response is excessively brief or incomplete.")
        corrected = "Thank you for reaching out to ResolveAI Customer Care. Could you please share more details or your Order ID so we may assist you?"

    review = ReviewerOutput(
        approved=approved,
        score=score,
        issues=issues,
        corrected_response=corrected,
        escalation_required=escalate,
        feedback="Verified against deterministic business constraints." if approved else "Flagged policy inconsistency."
    )

    log_audit(
        agent_name="Reviewer",
        action_type="Quality Review",
        model_used="Deterministic / Demo",
        input_summary=f"Audit draft ({len(worker_response)} chars)",
        output_summary=f"Approved: {review.approved}, Score: {review.score}",
        status="Success" if approved else "Flagged",
        metadata={"issues": review.issues}
    )
    return review
