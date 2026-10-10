"""
Overview Dashboard for ResolveAI.
Visualizes real-time metrics, ticket distribution, and complaint resolution rates
using Plotly charts and live SQLite statistics.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from database.db import get_analytics_summary, get_all_tickets, get_all_orders
from ui.components import render_header, render_metric_card, render_status_badge, render_priority_badge


def render_dashboard_page():
    render_header(
        title="ResolveAI Overview Dashboard",
        subtitle="Real-time operations, customer sentiment, ticket lifecycle & resolution velocity",
        badge="Live Metrics"
    )

    stats = get_analytics_summary()

    # KPI Metric Cards
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        render_metric_card("Total Sessions", stats["total_conversations"], "Active chat history", "💬")
    with c2:
        render_metric_card("Open Tickets", stats["open_tickets"], "In triage/progress", "🎫")
    with c3:
        render_metric_card("Resolved", stats["resolved_tickets"], "Cases successfully closed", "✅")
    with c4:
        render_metric_card("Pending Refunds", stats["pending_refunds"], "Awaiting admin sign-off", "💳")
    with c5:
        render_metric_card("Resolution Rate", f"{stats['resolution_rate']}%", "Quality benchmark", "📈")
    with c6:
        render_metric_card("Avg Latency", stats["avg_response_time"], "Multi-agent runtime", "⚡")

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    # Plotly Charts
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("📊 Complaint Categories")
        cat_counts = stats.get("category_counts", {})
        if cat_counts:
            fig_cat = px.pie(
                names=list(cat_counts.keys()),
                values=list(cat_counts.values()),
                hole=0.45,
                color_discrete_sequence=["#064E3B", "#059669", "#10B981", "#34D399", "#6EE7B7", "#A7F3D0", "#0284C7", "#7E22CE"]
            )
            fig_cat.update_layout(
                margin=dict(t=20, b=20, l=20, r=20),
                height=290,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2)
            )
            st.plotly_chart(fig_cat, use_container_width=True)
        else:
            st.info("No complaint records recorded yet.")

    with chart_col2:
        st.subheader("🏷️ Ticket Lifecycle Status")
        status_counts = stats.get("status_counts", {})
        if status_counts:
            fig_stat = px.bar(
                x=list(status_counts.keys()),
                y=list(status_counts.values()),
                labels={"x": "Status", "y": "Count"},
                color=list(status_counts.keys()),
                color_discrete_sequence=["#047857", "#0284C7", "#F59E0B", "#EF4444", "#6B7280"]
            )
            fig_stat.update_layout(
                margin=dict(t=20, b=20, l=20, r=20),
                height=290,
                showlegend=False
            )
            st.plotly_chart(fig_stat, use_container_width=True)
        else:
            st.info("No ticket records available.")

    st.markdown("<div style='margin-top: 1.25rem;'></div>", unsafe_allow_html=True)

    # Recent Active Cases
    st.subheader("⚡ Live Incident Feed")
    recent_tickets = get_all_tickets(limit=5)
    if recent_tickets:
        for t in recent_tickets:
            with st.container():
                st.markdown(f"""
                <div style="background: white; border: 1px solid #E2E8F0; border-radius: 10px; padding: 0.9rem 1.2rem; margin-bottom: 0.6rem; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-weight: 700; color: #0F172A; font-size: 0.95rem;">
                            {t['ticket_id']} — {t['subject']}
                        </div>
                        <div style="font-size: 0.8rem; color: #64748B; margin-top: 0.2rem;">
                            Customer: <b>{t['customer_id']}</b> • Order: <b>{t['order_id'] or 'None'}</b> • Filed: {t['created_at']}
                        </div>
                    </div>
                    <div style="display: flex; gap: 0.5rem; align-items: center;">
                        {render_priority_badge(t['priority'])}
                        {render_status_badge(t['status'])}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.write("No active support incidents.")
