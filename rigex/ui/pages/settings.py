"""
System Settings & Diagnostics Page for ResolveAI.
Manages 3 separate Gemini API Keys and 3 separate Gemini Models for Planner, Worker, and Reviewer.
"""

import streamlit as st
import os
from config.settings import (
    SQLITE_DB_PATH, CHROMA_PERSIST_DIR, POLICIES_DIR, EMBEDDING_MODEL,
    get_role_credentials, test_gemini_connection, save_role_configuration,
    SUPPORTED_GEMINI_MODELS
)
from database.seed_data import seed_database
from rag.ingest import index_knowledge_base
from ui.components import render_header


def render_settings_page():
    render_header(
        title="ResolveAI Multi-Model & Key Configuration",
        subtitle="Configure 3 dedicated Gemini API keys and models for Planner, Worker, and Reviewer roles",
        badge="Multi-Key System"
    )

    p_creds = get_role_credentials("planner")
    w_creds = get_role_credentials("worker")
    r_creds = get_role_credentials("reviewer")

    tab_keys, tab_diag, tab_storage, tab_reset = st.tabs([
        "🔑 3 Keys & Model Assignments",
        "🧪 Individual Role Connection Tests",
        "📂 Storage & Paths",
        "⚠️ Reset Demo Data"
    ])

    with tab_keys:
        st.subheader("Assign 3 Separate Gemini Keys & Models")
        st.write("Each role can have its own dedicated Google Gemini API key and distinct model version:")

        with st.form("three_keys_form"):
            st.markdown("#### 1️⃣ Planner Agent (Intent Analysis & Workflow Orchestration)")
            c1_m, c1_k = st.columns([1, 2])
            with c1_m:
                planner_model = st.selectbox(
                    "Planner Model",
                    SUPPORTED_GEMINI_MODELS,
                    index=SUPPORTED_GEMINI_MODELS.index(p_creds["model"]) if p_creds["model"] in SUPPORTED_GEMINI_MODELS else 0,
                    key="p_model_select"
                )
            with c1_k:
                planner_key = st.text_input(
                    "Planner Gemini API Key",
                    value=p_creds["api_key"] if p_creds["is_configured"] else "",
                    type="password",
                    placeholder="Enter dedicated API key for Planner...",
                    help="Active masked key: " + p_creds["masked_key"]
                )

            st.markdown("---")
            st.markdown("#### 2️⃣ Worker Agent (Fact Synthesis, SQLite & RAG Execution)")
            c2_m, c2_k = st.columns([1, 2])
            with c2_m:
                worker_model = st.selectbox(
                    "Worker Model",
                    SUPPORTED_GEMINI_MODELS,
                    index=SUPPORTED_GEMINI_MODELS.index(w_creds["model"]) if w_creds["model"] in SUPPORTED_GEMINI_MODELS else 1,
                    key="w_model_select"
                )
            with c2_k:
                worker_key = st.text_input(
                    "Worker Gemini API Key",
                    value=w_creds["api_key"] if w_creds["is_configured"] else "",
                    type="password",
                    placeholder="Enter dedicated API key for Worker...",
                    help="Active masked key: " + w_creds["masked_key"]
                )

            st.markdown("---")
            st.markdown("#### 3️⃣ Reviewer Agent (Quality & Policy Auditor)")
            c3_m, c3_k = st.columns([1, 2])
            with c3_m:
                reviewer_model = st.selectbox(
                    "Reviewer Model",
                    SUPPORTED_GEMINI_MODELS,
                    index=SUPPORTED_GEMINI_MODELS.index(r_creds["model"]) if r_creds["model"] in SUPPORTED_GEMINI_MODELS else 2,
                    key="r_model_select"
                )
            with c3_k:
                reviewer_key = st.text_input(
                    "Reviewer Gemini API Key",
                    value=r_creds["api_key"] if r_creds["is_configured"] else "",
                    type="password",
                    placeholder="Enter dedicated API key for Reviewer...",
                    help="Active masked key: " + r_creds["masked_key"]
                )

            save_btn = st.form_submit_button("💾 Save 3 Keys & Models Configuration", type="primary")

            if save_btn:
                save_role_configuration(
                    planner_key=planner_key,
                    planner_model=planner_model,
                    worker_key=worker_key,
                    worker_model=worker_model,
                    reviewer_key=reviewer_key,
                    reviewer_model=reviewer_model
                )
                st.success("✅ Configuration saved successfully! Environment updated.")
                st.rerun()

    with tab_diag:
        st.subheader("Test Connectivity for Each Role Independently")
        st.write("Perform real generation calls to verify each role's API key and model independently:")

        col_tp, col_tw, col_tr = st.columns(3)

        with col_tp:
            st.markdown("##### 🧠 Planner")
            st.caption(f"Model: `{p_creds['model']}`\nKey: `{p_creds['masked_key']}`")
            if st.button("Test Planner Model", key="btn_test_p"):
                with st.spinner("Connecting to Planner model..."):
                    ok, msg = test_gemini_connection(role="planner")
                if ok:
                    st.success(f"✅ {msg}")
                else:
                    st.error(f"❌ {msg}")

        with col_tw:
            st.markdown("##### 🛠️ Worker")
            st.caption(f"Model: `{w_creds['model']}`\nKey: `{w_creds['masked_key']}`")
            if st.button("Test Worker Model", key="btn_test_w"):
                with st.spinner("Connecting to Worker model..."):
                    ok, msg = test_gemini_connection(role="worker")
                if ok:
                    st.success(f"✅ {msg}")
                else:
                    st.error(f"❌ {msg}")

        with col_tr:
            st.markdown("##### 🛡️ Reviewer")
            st.caption(f"Model: `{r_creds['model']}`\nKey: `{r_creds['masked_key']}`")
            if st.button("Test Reviewer Model", key="btn_test_r"):
                with st.spinner("Connecting to Reviewer model..."):
                    ok, msg = test_gemini_connection(role="reviewer")
                if ok:
                    st.success(f"✅ {msg}")
                else:
                    st.error(f"❌ {msg}")

    with tab_storage:
        st.subheader("Storage Locations & Knowledge Base Status")
        st.markdown(f"- **SQLite Database:** `{SQLITE_DB_PATH}`")
        st.markdown(f"- **ChromaDB Vector Store:** `{CHROMA_PERSIST_DIR}`")
        st.markdown(f"- **Policy Directory:** `{POLICIES_DIR}`")
        st.markdown(f"- **Embedding Model:** `{EMBEDDING_MODEL}`")

        if st.button("🔄 Re-index Knowledge Base Now"):
            with st.spinner("Indexing policies..."):
                ok, msg = index_knowledge_base()
            if ok:
                st.success(msg)
            else:
                st.error(msg)

    with tab_reset:
        st.subheader("Reset Demo Database")
        st.write("Restore the SQLite database to the pristine state with 16 sample orders, customers, initial tickets, and refund records.")

        confirm_reset = st.checkbox("I understand that this will erase new chat conversations and reset test tickets.")
        if st.button("🚨 Re-Seed Database", type="secondary"):
            if not confirm_reset:
                st.warning("Please check the confirmation box above.")
            else:
                seed_database(force_reseed=True)
                st.success("Database successfully reset and re-seeded with 16 orders!")
                st.rerun()
