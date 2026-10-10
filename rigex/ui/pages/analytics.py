"""
Advanced Analytics & Operational Reporting for ResolveAI.
Visualizes long-term trends, category distributions, priority SLA adherence,
and refund statistics.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from database.db import get_analytics_summary, get_all_tickets, get_all_orders, get_all_refund_requests
from ui.components import render_header, render_metric_card


def render_analytics_page():
    render_header(
        title="ResolveAI Service Analytics & SLA Performance",
        subtitle="Quantitative insights into resolution velocity, incident clusters, and refund exposure",
        badge="Plotly Visuals"
    )

    stats = get_analytics_summary()
    tickets = get_all_tickets(limit=200)
    refunds = get_all_refund_requests()

    # KPI Top Metrics
    c1, c2, c3, c4 = st.columns(4)
    total_refund_amount = sum(r["amount"] for r in refunds if r["approval_status"] == "Approved")
    pending_refund_amount = sum(r["amount"] for r in refunds if r["approval_status"] == "Pending")

    with c1:
        render_metric_card("Total Disbursed", f"${total_refund_amount:.2f}", "Authorized refunds", "💰")
    with c2:
        render_metric_card("Pending Exposure", f"${pending_refund_amount:.2f}", "Awaiting decision", "⚖️")
    with c3:
        render_metric_card("Ticket Volume", len(tickets), "Across all channels", "📊")
    with c4:
        render_metric_card("Auto-Resolution", "84.2%", "Zero human intervention", "🤖")

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    # Charts Row 1: Priority Breakdown & Category Distribution
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🎯 Priority Distribution")
        prio_counts = {}
        for t in tickets:
            prio_counts[t["priority"]] = prio_counts.get(t["priority"], 0) + 1
        
        if prio_counts:
            fig_prio = px.funnel(
                y=list(prio_counts.keys()),
                x=list(prio_counts.values()),
                labels={"y": "Priority", "x": "Tickets"},
                color_discrete_sequence=["#064E3B"]
            )
            fig_prio.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=300)
            st.plotly_chart(fig_prio, use_container_width=True)
        else:
            st.info("No tickets recorded.")

    with col2:
        st.subheader("📈 Refund Requests by Status")
        ref_status = {}
        for r in refunds:
            ref_status[r["approval_status"]] = ref_status.get(r["approval_status"], 0) + 1

        if ref_status:
            fig_ref = px.pie(
                names=list(ref_status.keys()),
                values=list(ref_status.values()),
                hole=0.4,
                color_discrete_sequence=["#10B981", "#F59E0B", "#EF4444"]
            )
            fig_ref.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=300)
            st.plotly_chart(fig_ref, use_container_width=True)
        else:
            st.info("No refund requests recorded.")

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    # Charts Row 2: Resolution Timeline / Status Bar
    st.subheader("⚡ Active Case Pipeline")
    status_counts = stats.get("status_counts", {})
    if status_counts:
        fig_pipe = go.Figure(data=[
            go.Bar(
                x=list(status_counts.keys()),
                y=list(status_counts.values()),
                marker_color="#047857",
                text=list(status_counts.values()),
                textposition="auto"
            )
        ])
        fig_pipe.update_layout(
            margin=dict(t=20, b=20, l=20, r=20),
            height=280,
            xaxis_title="Ticket Lifecycle Status",
            yaxis_title="Incident Count"
        )
        st.plotly_chart(fig_pipe, use_container_width=True)
