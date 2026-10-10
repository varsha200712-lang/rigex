"""
Pydantic data models for ResolveAI.
Validates inputs and outputs across Database, Tools, and Multi-Agent steps.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class OrderItem(BaseModel):
    item_id: str
    product_name: str
    category: str
    quantity: int = 1
    unit_price: float
    is_perishable: bool = False
    serial_number: Optional[str] = None


class Order(BaseModel):
    order_id: str
    customer_id: str
    customer_name: str
    customer_email: str
    customer_phone: Optional[str] = None
    order_date: str
    status: str  # Processing, Shipped, In transit, Delivered, Delayed, Cancelled
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    shipping_address: str
    estimated_delivery: Optional[str] = None
    actual_delivery: Optional[str] = None
    total_amount: float
    items: List[OrderItem] = Field(default_factory=list)
    delay_reason: Optional[str] = None


class SupportTicket(BaseModel):
    ticket_id: str
    customer_id: str
    order_id: Optional[str] = None
    category: str  # Delivery delay, Damaged product, Missing item, Wrong item, Return request, Refund request, Payment issue, General inquiry, Other
    priority: str  # Low, Medium, High, Urgent
    status: str    # Open, In Progress, Awaiting Customer, Awaiting Approval, Escalated, Resolved, Closed
    subject: str
    description: str
    created_at: str
    updated_at: str
    assigned_agent: Optional[str] = "ResolveAI Worker"
    resolution_notes: Optional[str] = None


class RefundRequest(BaseModel):
    request_id: str
    ticket_id: str
    order_id: str
    customer_id: str
    amount: float
    reason: str
    eligibility_status: str  # Eligible, Ineligible, Human Approval Required
    approval_status: str     # Pending, Approved, Rejected
    admin_reviewed_by: Optional[str] = None
    admin_review_reason: Optional[str] = None
    admin_reviewed_at: Optional[str] = None
    created_at: str


class AuditLogRecord(BaseModel):
    log_id: Optional[int] = None
    timestamp: str
    agent_name: str  # Planner, Worker, Reviewer, Admin, System
    action_type: str
    model_used: Optional[str] = None
    input_summary: str
    output_summary: str
    status: str      # Success, Failed, Flagged, Escalated
    metadata_json: Optional[str] = None


class ConversationMessage(BaseModel):
    message_id: Optional[int] = None
    session_id: str
    sender: str  # customer, ai, system
    text: str
    timestamp: str
    agent_steps: Optional[str] = None
    ticket_id: Optional[str] = None


# Multi-Agent Structured Communication Schemas
class PlannerOutput(BaseModel):
    intent: str = Field(description="Primary intent: order_tracking, delayed_delivery, damaged_product, return_request, refund_request, general_faq, complaint, escalation, or greeting")
    priority: str = Field(description="Priority level: Low, Medium, High, Urgent")
    complaint_category: Optional[str] = Field(default="General inquiry", description="Complaint category if applicable")
    requires_order_lookup: bool = Field(default=False)
    requires_rag: bool = Field(default=False)
    requires_ticket: bool = Field(default=False)
    requires_human_approval: bool = Field(default=False)
    missing_information: List[str] = Field(default_factory=list, description="Missing required fields, e.g. order_id")
    order_id_extracted: Optional[str] = Field(default=None, description="Extracted order ID from message if present")
    steps: List[str] = Field(default_factory=list, description="Sequential actions the worker should execute")
    reasoning_summary: str = Field(default="Standard intent execution plan", description="Brief safe summary of why this plan was chosen")


class ReviewerOutput(BaseModel):
    approved: bool = Field(description="Whether the response is factually grounded and policy compliant")
    score: int = Field(ge=0, le=100, description="Quality score from 0 to 100")
    issues: List[str] = Field(default_factory=list, description="List of detected inconsistencies or hallucinations")
    corrected_response: Optional[str] = Field(default=None, description="Corrected customer response if approval failed")
    escalation_required: bool = Field(default=False, description="Whether this case requires human supervisor intervention")
    feedback: str = Field(default="Quality verified against business policies", description="Safe review commentary")
