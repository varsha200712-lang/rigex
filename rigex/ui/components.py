"""
Reusable UI Components for ResolveAI Streamlit application.
Renders consistent, high-contrast badges, cards, timelines, and message blocks.
"""

import streamlit as st
from typing import Optional, List, Dict, Any


def render_header(title: str, subtitle: str, badge: str = "Multi-Agent RAG"):
    """Render the polished gradient banner at the top of pages."""
    st.markdown(f"""
    <div class="brand-header">
        <div>
            <div class="brand-title">
                <span>🛡️</span> {title}
            </div>
            <div style="font-size: 0.95rem; opacity: 0.9; margin-top: 0.35rem; font-weight: 400;">
                {subtitle}
            </div>
        </div>
        <div class="brand-badge">
            {badge}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_status_badge(status: str) -> str:
    """Return HTML string for a colored status badge."""
    clean = (status or "").lower().replace(" ", "")
    cls_map = {
        "processing": "badge-processing",
        "shipped": "badge-shipped",
        "intransit": "badge-intransit",
        "delivered": "badge-delivered",
        "delayed": "badge-delayed",
        "cancelled": "badge-cancelled",
        "open": "badge-processing",
        "inprogress": "badge-intransit",
        "awaitingcustomer": "badge-shipped",
        "awaitingapproval": "badge-delayed",
        "escalated": "badge-urgent",
        "resolved": "badge-delivered",
        "closed": "badge-cancelled",
        "pending": "badge-delayed",
        "approved": "badge-delivered",
        "rejected": "badge-cancelled"
    }
    cls = cls_map.get(clean, "badge-low")
    return f'<span class="badge {cls}">{status}</span>'


def render_priority_badge(priority: str) -> str:
    """Return HTML string for a colored priority badge."""
    clean = (priority or "").lower()
    cls_map = {
        "low": "badge-low",
        "medium": "badge-medium",
        "high": "badge-high",
        "urgent": "badge-urgent"
    }
    cls = cls_map.get(clean, "badge-low")
    return f'<span class="badge {cls}">{priority}</span>'


def render_metric_card(label: str, value: Any, subtext: str = "", icon: str = "📊"):
    """Render an attractive responsive KPI metric card."""
    st.markdown(f"""
    <div class="metric-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span class="metric-label">{label}</span>
            <span style="font-size: 1.25rem;">{icon}</span>
        </div>
        <div class="metric-value">{value}</div>
        <div class="metric-change">{subtext}</div>
    </div>
    """, unsafe_allow_html=True)


def render_order_timeline(current_status: str):
    """Render a visual 5-step order fulfillment timeline."""
    steps = ["Processing", "Shipped", "In transit", "Delivered"]
    status_lower = (current_status or "").lower()
    
    current_idx = 0
    if status_lower == "processing":
        current_idx = 0
    elif status_lower == "shipped":
        current_idx = 1
    elif status_lower in ("in transit", "delayed"):
        current_idx = 2
    elif status_lower == "delivered":
        current_idx = 3
    elif status_lower == "cancelled":
        current_idx = -1

    if current_idx == -1:
        st.warning("⚠️ This order was **Cancelled**.")
        return

    col1, col2, col3, col4 = st.columns(4)
    cols = [col1, col2, col3, col4]

    for i, (name, col) in enumerate(zip(steps, cols)):
        with col:
            if i < current_idx:
                circle_class = "step-circle done"
                icon = "✓"
                color = "#059669"
            elif i == current_idx:
                circle_class = "step-circle active"
                icon = "●"
                color = "#047857"
            else:
                circle_class = "step-circle"
                icon = str(i + 1)
                color = "#94A3B8"

            st.markdown(f"""
            <div style="text-align: center;">
                <div class="{circle_class}" style="color: {color};">{icon}</div>
                <div class="step-label" style="color: {color};">{name}</div>
            </div>
            """, unsafe_allow_html=True)


def render_chat_bubble(sender: str, text: str, timestamp: str = "", steps: Optional[str] = None, ticket_id: Optional[str] = None):
    """Render customer and AI chat bubbles with safety badges and step pills."""
    if sender == "customer":
        st.markdown(f"""
        <div style="display: flex; justify-content: flex-end; margin-bottom: 0.8rem;">
            <div class="chat-bubble-user">
                <div style="font-weight: 600; font-size: 0.75rem; opacity: 0.85; margin-bottom: 0.2rem;">You • {timestamp}</div>
                <div>{text}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # AI bubble
        pills_html = ""
        if steps:
            parts = [s.strip() for s in steps.split("->") if s.strip()]
            pills = "".join([f'<span class="chat-step-pill">✓ {p}</span>' for p in parts[:4]])
            pills_html = f'<div style="margin-top: 0.6rem; border-top: 1px dashed #E2E8F0; padding-top: 0.4rem;">{pills}</div>'

        ticket_html = ""
        if ticket_id:
            ticket_html = f'<div style="margin-top: 0.5rem;"><span class="badge badge-delivered">🏷️ Ticket Created: {ticket_id}</span></div>'

        st.markdown(f"""
        <div style="display: flex; justify-content: flex-start; margin-bottom: 1rem;">
            <div class="chat-bubble-ai">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
                    <span style="font-weight: 700; font-size: 0.8rem; color: #064E3B;">🛡️ ResolveAI Assistant</span>
                    <span style="font-size: 0.72rem; color: #64748B;">{timestamp}</span>
                </div>
                <div style="white-space: pre-wrap;">{text}</div>
                {ticket_html}
                {pills_html}
            </div>
        </div>
        """, unsafe_allow_html=True)
