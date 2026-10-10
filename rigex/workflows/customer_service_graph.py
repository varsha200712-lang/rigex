"""
Multi-Agent Orchestration Graph using LangGraph.
Coordinates Planner, Tool Routing, Worker, Reviewer, and Conditional Correction Edges.
"""

import time
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END

from database.models import PlannerOutput, ReviewerOutput
from database.db import save_conversation_message
from agents.planner import run_planner
from agents.worker import run_worker
from agents.reviewer import run_reviewer
from tools.order_tools import lookup_order, extract_order_id_from_text
from tools.policy_tools import search_company_policies
from tools.refund_tools import evaluate_refund_eligibility
from tools.ticket_tools import create_customer_ticket, record_refund_request_tool


class CustomerServiceState(TypedDict):
    customer_message: str
    session_id: str
    simulated_customer_id: Optional[str]
    plan: Optional[Dict[str, Any]]
    order_context: Optional[Dict[str, Any]]
    policy_context: Optional[Dict[str, Any]]
    refund_context: Optional[Dict[str, Any]]
    ticket_receipt: Optional[Dict[str, Any]]
    worker_draft: Optional[str]
    review_output: Optional[Dict[str, Any]]
    final_response: str
    correction_attempted: bool
    status_steps: List[str]
    error: Optional[str]


# ---------------- NODE FUNCTIONS ----------------

def planner_node(state: CustomerServiceState) -> Dict[str, Any]:
    """Node 1: Planner AI model analyzes intent and produces structured plan."""
    msg = state["customer_message"]
    steps = state.get("status_steps", []) + ["Understanding request & planning intent"]
    try:
        plan: PlannerOutput = run_planner(msg, session_id=state.get("session_id"))
        return {
            "plan": plan.model_dump(),
            "status_steps": steps
        }
    except Exception as e:
        return {
            "error": f"Planner error: {str(e)}",
            "status_steps": steps + [f"Planner encountered exception: {e}"]
        }


def tool_routing_node(state: CustomerServiceState) -> Dict[str, Any]:
    """Node 2: Conditionally execute permitted Python tools based on plan."""
    plan_dict = state.get("plan", {})
    msg = state["customer_message"]
    steps = state.get("status_steps", [])
    
    order_ctx = None
    policy_ctx = None
    refund_ctx = None
    ticket_receipt = None

    order_id = plan_dict.get("order_id_extracted") or extract_order_id_from_text(msg)
    intent = plan_dict.get("intent", "general_faq")
    category = plan_dict.get("complaint_category", "General inquiry")
    priority = plan_dict.get("priority", "Medium")

    # 1. Order lookup tool
    if plan_dict.get("requires_order_lookup") or order_id:
        if order_id:
            steps.append(f"Looking up verified order details for {order_id}")
            order_ctx = lookup_order(order_id, simulated_customer_id=state.get("simulated_customer_id"))
        else:
            steps.append("Order ID missing; prompting customer for order number")

    # 2. Policy RAG tool
    if plan_dict.get("requires_rag") or intent in ("general_faq", "return_request", "refund_request", "delayed_delivery"):
        steps.append("Searching verified company policies knowledge base")
        policy_ctx = search_company_policies(msg, top_k=2)

    # 3. Deterministic Refund Eligibility Tool
    if intent in ("refund_request", "damaged_product") or plan_dict.get("requires_human_approval"):
        if order_id and order_ctx and order_ctx.get("found"):
            steps.append("Evaluating deterministic refund eligibility rules")
            refund_ctx = evaluate_refund_eligibility(order_id, msg)
        else:
            refund_ctx = None

    # 4. Ticket Creation Tool (for complaints, delays, damages, refunds, escalations)
    if plan_dict.get("requires_ticket") or intent in ("delayed_delivery", "damaged_product", "complaint", "escalation", "refund_request"):
        steps.append(f"Registering support ticket (Category: {category}, Priority: {priority})")
        subject = f"{category.title()} - {order_id or 'General'}"
        initial_status = "Open"
        if refund_ctx and refund_ctx.get("requires_human_approval"):
            initial_status = "Awaiting Approval"
        elif intent == "escalation":
            initial_status = "Escalated"

        ticket_receipt = create_customer_ticket(
            customer_id=state.get("simulated_customer_id") or "CUST-GUEST",
            category=category,
            priority=priority,
            subject=subject,
            description=msg,
            order_id=order_id,
            status=initial_status
        )

        # If refund request requires record in refund_requests table
        if refund_ctx and order_id:
            record_refund_request_tool(
                ticket_id=ticket_receipt["ticket_id"],
                order_id=order_id,
                customer_id=state.get("simulated_customer_id") or "CUST-GUEST",
                amount=refund_ctx.get("amount", 0.0),
                reason=msg,
                eligibility_status=refund_ctx.get("status", "Eligible"),
                requires_human_approval=refund_ctx.get("requires_human_approval", False)
            )

    return {
        "order_context": order_ctx,
        "policy_context": policy_ctx,
        "refund_context": refund_ctx,
        "ticket_receipt": ticket_receipt,
        "status_steps": steps
    }


def worker_node(state: CustomerServiceState) -> Dict[str, Any]:
    """Node 3: Worker AI model crafts fact-grounded response."""
    plan_dict = state.get("plan", {})
    plan = PlannerOutput(**plan_dict) if plan_dict else PlannerOutput(
        intent="general_faq", priority="Medium", steps=["Answer inquiry"]
    )
    steps = state.get("status_steps", []) + ["Worker synthesizing response from verified evidence"]

    draft = run_worker(
        customer_message=state["customer_message"],
        plan=plan,
        order_context=state.get("order_context"),
        policy_context=state.get("policy_context"),
        refund_context=state.get("refund_context"),
        ticket_receipt=state.get("ticket_receipt")
    )
    return {
        "worker_draft": draft,
        "status_steps": steps
    }


def reviewer_node(state: CustomerServiceState) -> Dict[str, Any]:
    """Node 4: Reviewer AI independently audits draft for hallucinations & policy compliance."""
    plan_dict = state.get("plan", {})
    plan = PlannerOutput(**plan_dict) if plan_dict else PlannerOutput(
        intent="general_faq", priority="Medium", steps=[]
    )
    draft = state.get("worker_draft", "")
    steps = state.get("status_steps", []) + ["Reviewer auditing answer for factual accuracy"]

    review: ReviewerOutput = run_reviewer(
        customer_message=state["customer_message"],
        worker_response=draft,
        plan=plan,
        order_context=state.get("order_context"),
        policy_context=state.get("policy_context"),
        refund_context=state.get("refund_context"),
        ticket_receipt=state.get("ticket_receipt")
    )

    steps.append(f"Review verdict: {'Approved' if review.approved else 'Issues flagged'} (Quality: {review.score}/100)")
    return {
        "review_output": review.model_dump(),
        "status_steps": steps
    }


def correction_node(state: CustomerServiceState) -> Dict[str, Any]:
    """Node 5: Controlled single correction cycle when Reviewer flags an issue."""
    review_dict = state.get("review_output", {})
    steps = state.get("status_steps", []) + ["Applying controlled correction from Reviewer feedback"]
    corrected = review_dict.get("corrected_response")
    if not corrected:
        corrected = state.get("worker_draft", "")
    return {
        "final_response": corrected,
        "correction_attempted": True,
        "status_steps": steps
    }


def finalize_node(state: CustomerServiceState) -> Dict[str, Any]:
    """Node 6: Save conversation message and return final customer response."""
    final_resp = state.get("final_response") or state.get("worker_draft") or "Thank you for contacting ResolveAI Customer Care."
    ticket_id = None
    if state.get("ticket_receipt"):
        ticket_id = state["ticket_receipt"].get("ticket_id")

    # Persist in SQLite
    session_id = state.get("session_id", "default_session")
    agent_steps_summary = " -> ".join(state.get("status_steps", []))
    save_conversation_message(
        session_id=session_id,
        sender="ai",
        text=final_resp,
        agent_steps=agent_steps_summary,
        ticket_id=ticket_id
    )

    return {
        "final_response": final_resp,
        "status_steps": state.get("status_steps", []) + ["Response delivered and conversation persisted"]
    }


# ---------------- CONDITIONAL ROUTING ----------------

def route_after_review(state: CustomerServiceState) -> str:
    """Conditional Edge: Approved -> finalize; Flagged (first time) -> correction; Else finalize."""
    review = state.get("review_output", {})
    if review.get("approved"):
        return "finalize"
    if not state.get("correction_attempted"):
        return "correction"
    return "finalize"


# ---------------- BUILD GRAPH ----------------

def build_customer_service_graph():
    """Assemble and compile the LangGraph StateGraph."""
    graph = StateGraph(CustomerServiceState)

    graph.add_node("planner", planner_node)
    graph.add_node("tool_routing", tool_routing_node)
    graph.add_node("worker", worker_node)
    graph.add_node("reviewer", reviewer_node)
    graph.add_node("correction", correction_node)
    graph.add_node("finalize", finalize_node)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "tool_routing")
    graph.add_edge("tool_routing", "worker")
    graph.add_edge("worker", "reviewer")
    
    graph.add_conditional_edges(
        "reviewer",
        route_after_review,
        {
            "finalize": "finalize",
            "correction": "correction"
        }
    )
    graph.add_edge("correction", "finalize")
    graph.add_edge("finalize", END)

    return graph.compile()


# Singleton workflow runner
_workflow_engine = None

def get_workflow_engine():
    global _workflow_engine
    if _workflow_engine is None:
        _workflow_engine = build_customer_service_graph()
    return _workflow_engine


def run_customer_service_workflow(
    message: str,
    session_id: str = "default_session",
    customer_id: Optional[str] = "CUST-101"
) -> Dict[str, Any]:
    """Execute complete multi-agent workflow for a customer message."""
    engine = get_workflow_engine()
    initial_state: CustomerServiceState = {
        "customer_message": message,
        "session_id": session_id,
        "simulated_customer_id": customer_id,
        "plan": None,
        "order_context": None,
        "policy_context": None,
        "refund_context": None,
        "ticket_receipt": None,
        "worker_draft": None,
        "review_output": None,
        "final_response": "",
        "correction_attempted": False,
        "status_steps": [],
        "error": None
    }
    result = engine.invoke(initial_state)
    return result
