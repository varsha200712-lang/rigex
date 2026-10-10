"""
ResolveAI — Intelligent Customer Care
Multi-Agent AI and RAG Customer Service Automation Platform.
Main Streamlit application entrypoint.
"""

import streamlit as st
from config.settings import (
    PLANNER_MODEL, WORKER_MODEL, REVIEWER_MODEL,
    is_api_key_configured, get_masked_api_key, SQLITE_DB_PATH, CHROMA_PERSIST_DIR
)
from database.seed_data import seed_database
from rag.ingest import index_knowledge_base
from ui.styles import CUSTOM_CSS
from ui.pages.dashboard import render_dashboard_page
from ui.pages.chat import render_chat_page
from ui.pages.orders import render_orders_page
from ui.pages.complaints import render_complaints_page
from ui.pages.approvals import render_approvals_page
from ui.pages.knowledge_base import render_knowledge_base_page
from ui.pages.agent_monitor import render_agent_monitor_page
from ui.pages.analytics import render_analytics_page
from ui.pages.settings import render_settings_page


# Configure Page
st.set_page_config(
    page_title="ResolveAI — Intelligent Customer Care",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Custom CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# Auto-initialize database and knowledge base on first startup
@st.cache_resource
def bootstrap_application():
    # 1. Initialize & Seed SQLite
    seed_database(force_reseed=False)
    # 2. Ingest policies if vector cache is missing
    backup_file = CHROMA_PERSIST_DIR / "policy_chunks.json"
    if not backup_file.exists():
        index_knowledge_base()
    return True


bootstrap_application()


# Sidebar Navigation
with st.sidebar:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 0.6rem; margin-bottom: 1.25rem;">
        <span style="font-size: 1.8rem;">🛡️</span>
        <div>
            <div style="font-weight: 800; font-size: 1.25rem; color: #064E3B; letter-spacing: -0.02em;">ResolveAI</div>
            <div style="font-size: 0.72rem; color: #64748B; font-weight: 500;">INTELLIGENT CUSTOMER CARE</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    nav_options = [
        "📊 Overview",
        "💬 AI Customer Chat",
        "📦 Order Tracking",
        "🚨 Complaint Center",
        "🎫 Support Tickets",
        "💳 Refund Approvals",
        "📚 Knowledge Base",
        "🤖 AI Agent Monitor",
        "📈 Analytics",
        "⚙️ Settings"
    ]

    selected_page = st.radio(
        "Navigation",
        nav_options,
        index=1,  # Default to AI Customer Chat
        label_visibility="collapsed"
    )

    st.markdown("---")

    # 3 Gemini Roles Status in Sidebar
    from config.settings import get_role_credentials
    p_c = get_role_credentials("planner")
    w_c = get_role_credentials("worker")
    r_c = get_role_credentials("reviewer")

    all_ready = p_c["is_configured"] and w_c["is_configured"] and r_c["is_configured"]
    any_ready = p_c["is_configured"] or w_c["is_configured"] or r_c["is_configured"]

    status_badge = "🟢 3 Models Active" if all_ready else ("🟡 Partial Live / Demo" if any_ready else "🟡 Demo Mode Active")
    badge_bg = "#ECFDF5" if all_ready else "#FEF3C7"
    badge_color = "#065F46" if all_ready else "#92400E"

    st.markdown(f"""
    <div style="background: {badge_bg}; border: 1px solid rgba(0,0,0,0.08); border-radius: 8px; padding: 0.65rem 0.8rem; font-size: 0.73rem;">
        <div style="color: {badge_color}; font-weight: 700; margin-bottom: 0.35rem;">{status_badge}</div>
        <div>🧠 <b>Planner:</b> <code>{p_c['model']}</code> ({p_c['masked_key']})</div>
        <div style="margin-top: 0.2rem;">🛠️ <b>Worker:</b> <code>{w_c['model']}</code> ({w_c['masked_key']})</div>
        <div style="margin-top: 0.2rem;">🛡️ <b>Reviewer:</b> <code>{r_c['model']}</code> ({r_c['masked_key']})</div>
    </div>
    """, unsafe_allow_html=True)

    st.caption("ResolveAI Enterprise v1.0.0 • SQLite • LangGraph • ChromaDB")


# Page Routing
if selected_page == "📊 Overview":
    render_dashboard_page()
elif selected_page == "💬 AI Customer Chat":
    render_chat_page()
elif selected_page == "📦 Order Tracking":
    render_orders_page()
elif selected_page in ("🚨 Complaint Center", "🎫 Support Tickets"):
    render_complaints_page()
elif selected_page == "💳 Refund Approvals":
    render_approvals_page()
elif selected_page == "📚 Knowledge Base":
    render_knowledge_base_page()
elif selected_page == "🤖 AI Agent Monitor":
    render_agent_monitor_page()
elif selected_page == "📈 Analytics":
    render_analytics_page()
elif selected_page == "⚙️ Settings":
    render_settings_page()
