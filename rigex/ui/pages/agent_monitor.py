"""
AI Agent Monitor Dashboard for ResolveAI.
Visualizes actual operational health, configured model IDs, real latency,
and immutable execution logs for Planner, Worker, and Reviewer models.
"""

import streamlit as st
from config.settings import get_role_credentials
from database.db import get_audit_logs
from ui.components import render_header


def render_agent_monitor_page():
    render_header(
        title="ResolveAI Multi-Agent System Monitor",
        subtitle="Live telemetry, role responsibilities, model assignments, and audit trails",
        badge="LangGraph Agents"
    )

    p_creds = get_role_credentials("planner")
    w_creds = get_role_credentials("worker")
    r_creds = get_role_credentials("reviewer")

    # Three Agent Cards
    col_p, col_w, col_r = st.columns(3)

    # 1. PLANNER
    with col_p:
        p_status = "🟢 Connected (Gemini API)" if p_creds["is_configured"] else "🟡 Demo / Offline"
        st.markdown(f"""
        <div class="agent-card">
            <div class="agent-card-header">
                <span class="agent-title">🧠 Planner Model</span>
                <span class="agent-status-dot"></span>
            </div>
            <div style="font-size: 0.82rem; color: #64748B; margin-bottom: 0.75rem;">
                <b>Role:</b> Intent triage, entity extraction, policy routing & plan formulation.
            </div>
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 0.75rem; font-size: 0.8rem;">
                <div><b>Assigned Model:</b> <code>{p_creds['model']}</code></div>
                <div style="margin-top: 0.25rem;"><b>API Key:</b> {p_creds['masked_key']}</div>
                <div style="margin-top: 0.25rem;"><b>Status:</b> {p_status}</div>
                <div style="margin-top: 0.25rem;"><b>Output Schema:</b> Pydantic <code>PlannerOutput</code></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 2. WORKER
    with col_w:
        w_status = "🟢 Connected (Gemini API)" if w_creds["is_configured"] else "🟡 Demo / Offline"
        st.markdown(f"""
        <div class="agent-card">
            <div class="agent-card-header">
                <span class="agent-title">🛠️ Worker Model</span>
                <span class="agent-status-dot" style="background: #0284C7;"></span>
            </div>
            <div style="font-size: 0.82rem; color: #64748B; margin-bottom: 0.75rem;">
                <b>Role:</b> Fact synthesis, SQLite queries, RAG search & deterministic rules.
            </div>
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 0.75rem; font-size: 0.8rem;">
                <div><b>Assigned Model:</b> <code>{w_creds['model']}</code></div>
                <div style="margin-top: 0.25rem;"><b>API Key:</b> {w_creds['masked_key']}</div>
                <div style="margin-top: 0.25rem;"><b>Status:</b> {w_status}</div>
                <div style="margin-top: 0.25rem;"><b>Tools:</b> SQLite Orders, RAG Ingest, Refund Engine</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 3. REVIEWER
    with col_r:
        r_status = "🟢 Connected (Gemini API)" if r_creds["is_configured"] else "🟡 Demo / Offline"
        st.markdown(f"""
        <div class="agent-card">
            <div class="agent-card-header">
                <span class="agent-title">🛡️ Reviewer Model</span>
                <span class="agent-status-dot" style="background: #7E22CE;"></span>
            </div>
            <div style="font-size: 0.82rem; color: #64748B; margin-bottom: 0.75rem;">
                <b>Role:</b> Quality auditor, anti-hallucination check, policy consistency & scoring.
            </div>
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 0.75rem; font-size: 0.8rem;">
                <div><b>Assigned Model:</b> <code>{r_creds['model']}</code></div>
                <div style="margin-top: 0.25rem;"><b>API Key:</b> {r_creds['masked_key']}</div>
                <div style="margin-top: 0.25rem;"><b>Status:</b> {r_status}</div>
                <div style="margin-top: 0.25rem;"><b>Correction:</b> Bounded 1-Cycle Correction Loop</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    # Actual Execution Logs
    st.subheader("📋 Real Multi-Agent Execution Audit Stream")
    logs = get_audit_logs(limit=50)

    if not logs:
        st.info("No agent executions logged yet. Start a conversation in the AI Customer Chat to observe live agent telemetry.")
    else:
        table_rows = []
        for l in logs:
            table_rows.append({
                "Timestamp": l["timestamp"],
                "Agent": l["agent_name"],
                "Action": l["action_type"],
                "Model Used": l.get("model_used") or "Default",
                "Input Summary": l["input_summary"],
                "Output / Verdict": l["output_summary"],
                "Status": l["status"]
            })
        st.dataframe(table_rows, use_container_width=True)
