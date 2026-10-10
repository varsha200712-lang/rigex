"""
Knowledge Base Management & Semantic Retrieval Explorer for ResolveAI.
Allows inspection of policy documents, re-indexing of ChromaDB vector store,
and live semantic search debugging with evidence scores.
"""

import streamlit as st
from config.settings import POLICIES_DIR, CHROMA_PERSIST_DIR
from rag.ingest import index_knowledge_base
from rag.retriever import query_policies
from ui.components import render_header


def render_knowledge_base_page():
    render_header(
        title="ResolveAI Knowledge Base & RAG Index",
        subtitle="Manage company policies, test semantic vector retrieval, and ground AI responses",
        badge="ChromaDB RAG"
    )

    tab_test, tab_docs, tab_index = st.tabs([
        "🔍 Semantic Search Sandbox",
        "📄 View Policy Documents",
        "⚙️ Vector Index Operations"
    ])

    with tab_test:
        st.subheader("Test Semantic Retrieval")
        st.write("Enter a realistic customer inquiry to view which policy chunks and evidence citations the multi-agent system retrieves:")

        sample_queries = [
            "Can I return an item after 20 days?",
            "What if my order is delayed more than 2 weeks?",
            "Do I get a refund if the item arrived broken under $50?",
            "Does warranty cover water damage?",
            "How can I cancel an order that is still processing?"
        ]

        preset = st.selectbox("Or choose a sample query:", [""] + sample_queries)
        query_input = st.text_input("Customer Inquiry:", value=preset, placeholder="e.g. Can I return headphones?").strip()

        if st.button("Run Semantic Search", type="primary"):
            if not query_input:
                st.warning("Please enter a query.")
            else:
                with st.spinner("Searching vector index..."):
                    results = query_policies(query_input, top_k=3)
                if not results:
                    st.warning("No relevant policy chunks found matching this query.")
                else:
                    st.success(f"Retrieved **{len(results)}** relevant policy passages:")
                    for i, r in enumerate(results, 1):
                        with st.expander(f"Evidence #{i}: {r['source']} — {r['section']} (Score: {r['score']})", expanded=True):
                            st.caption(f"**Source Document:** `{r['source']}` | **Section:** `{r['section']}` | **Similarity Score:** `{r['score']}`")
                            st.markdown(r["content"])

    with tab_docs:
        st.subheader("Configured Enterprise Policies")
        policy_files = {
            "Return Policy": "return_policy.txt",
            "Refund Policy": "refund_policy.txt",
            "Shipping & Delivery": "shipping_policy.txt",
            "Warranty Policy": "warranty_policy.txt",
            "Customer FAQ": "faq.txt"
        }

        selected_doc = st.selectbox("Select Policy Document to View", list(policy_files.keys()))
        target_file = POLICIES_DIR / policy_files[selected_doc]

        if target_file.exists():
            with open(target_file, "r", encoding="utf-8") as f:
                content = f.read()
            st.text_area(f"Full Text — {policy_files[selected_doc]}", content, height=350)
        else:
            st.error(f"File {target_file} not found.")

    with tab_index:
        st.subheader("Knowledge Base Re-Indexing")
        st.write("Re-chunk all 5 policy documents, generate embeddings, and update the ChromaDB vector database:")

        st.info(f"📁 Vector Store Location: `{CHROMA_PERSIST_DIR}`")

        if st.button("🔄 Refresh & Re-index Knowledge Base", type="primary"):
            with st.spinner("Chunking policies & indexing in vector store..."):
                ok, msg = index_knowledge_base()
            if ok:
                st.success(f"Success! {msg}")
            else:
                st.error(f"Failed to re-index: {msg}")
