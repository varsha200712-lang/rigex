"""
AI Customer Chat Interface for ResolveAI.
Interactive conversational experience featuring quick action prompt cards,
multi-agent live progress indicators, ticket generation badges, and persistent chat history.
"""

import streamlit as st
from datetime import datetime
from database.db import save_conversation_message, get_conversation_history
from workflows.customer_service_graph import run_customer_service_workflow
from ui.components import render_header, render_chat_bubble


def render_chat_page():
    render_header(
        title="ResolveAI Customer Care Chat",
        subtitle="Empathetic, fact-grounded resolution powered by Planner, Worker & Reviewer AI",
        badge="Multi-Agent Live"
    )

    # Session ID management
    if "chat_session_id" not in st.session_state:
        st.session_state["chat_session_id"] = "session_" + datetime.now().strftime("%Y%m%d_%H%M%S")

    session_id = st.session_state["chat_session_id"]

    # Quick action prompt handler
    def send_prompt(prompt_text: str):
        st.session_state["pending_prompt"] = prompt_text

    # Top Quick Action Cards
    st.markdown("#### ⚡ Quick Inquiries")
    q1, q2, q3, q4 = st.columns(4)
    with q1:
        if st.button("📦 Track My Order\n(ORD-1001)", use_container_width=True):
            send_prompt("Where is my order ORD-1001? Can you show me the tracking status?")
    with q2:
        if st.button("🔄 Return Policy\n(30-Day Window)", use_container_width=True):
            send_prompt("What is your 30-day return policy, and do I have to pay return shipping?")
    with q3:
        if st.button("💥 Damaged Item Refund\n(ORD-1007 < $50)", use_container_width=True):
            send_prompt("My ceramic coffee dripper for order ORD-1007 arrived chipped and damaged. Can I get a refund?")
    with q4:
        if st.button("⚠️ High-Value / Delay\n(ORD-1008 > $150)", use_container_width=True):
            send_prompt("I want to return and get a refund for ORD-1008 ($165) because the doorbell doesn't fit my wall.")

    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

    # Retrieve persistent messages from SQLite
    history = get_conversation_history(session_id)

    # Render Welcome message if history is empty
    if not history:
        render_chat_bubble(
            sender="ai",
            text="Hello! Welcome to ResolveAI Customer Care. I am your automated AI support concierge.\n\n"
                 "I can help you:\n"
                 "• Track active orders and estimated carrier arrival dates\n"
                 "• Search our return, shipping, and warranty policies\n"
                 "• Resolve damaged products and file instant refunds\n"
                 "• File formal support tickets or request human supervisor escalation\n\n"
                 "You can ask in English or Tanglish (e.g., *'En order ORD-1001 enga irukku?'*). How may I help you today?",
            timestamp="Just now"
        )
    else:
        for msg in history:
            render_chat_bubble(
                sender=msg["sender"],
                text=msg["text"],
                timestamp=msg.get("timestamp", ""),
                steps=msg.get("agent_steps"),
                ticket_id=msg.get("ticket_id")
            )

    # Check for pending prompt from quick action buttons
    user_input = None
    if "pending_prompt" in st.session_state and st.session_state["pending_prompt"]:
        user_input = st.session_state["pending_prompt"]
        st.session_state["pending_prompt"] = None
    else:
        user_input = st.chat_input("Type your question, order issue, or Tanglish message here (e.g., 'Status of ORD-1005')...")

    if user_input:
        # 1. Immediately display user bubble & save to SQLite
        save_conversation_message(
            session_id=session_id,
            sender="customer",
            text=user_input
        )
        render_chat_bubble(
            sender="customer",
            text=user_input,
            timestamp=datetime.now().strftime("%H:%M:%S")
        )

        # 2. Multi-Agent Execution with Progress Indicator
        status_box = st.status("🤖 Resolving with Multi-Agent AI...", expanded=True)
        with status_box:
            st.write("1️⃣ **Planner AI**: Detecting intent, urgency, and required tools...")
            st.write("2️⃣ **Worker AI & Tools**: Querying verified database, policies, and business rules...")
            st.write("3️⃣ **Reviewer AI**: Auditing answer against factual context for 100% compliance...")
            
            result = run_customer_service_workflow(
                message=user_input,
                session_id=session_id,
                customer_id="CUST-101"
            )
            status_box.update(label="✅ Resolution Complete & Verified", state="complete", expanded=False)

        final_text = result.get("final_response", "")
        ticket_id = result.get("ticket_receipt", {}).get("ticket_id") if result.get("ticket_receipt") else None
        agent_steps = " -> ".join(result.get("status_steps", []))

        # 3. Render AI Response
        render_chat_bubble(
            sender="ai",
            text=final_text,
            timestamp=datetime.now().strftime("%H:%M:%S"),
            steps=agent_steps,
            ticket_id=ticket_id
        )

        # Suggested follow-ups
        st.markdown("<div style='margin-top: 0.8rem;'></div>", unsafe_allow_html=True)
        st.caption("💡 **Suggested Next Actions:**")
        f_cols = st.columns(3)
        with f_cols[0]:
            if st.button("📋 Check active tickets", key="su_1"):
                send_prompt("Can you show me the status of my open support tickets?")
                st.rerun()
        with f_cols[1]:
            if st.button("🔄 Return window policy", key="su_2"):
                send_prompt("What items are not eligible for return?")
                st.rerun()
        with f_cols[2]:
            if st.button("👤 Speak with a human", key="su_3"):
                send_prompt("I would like to speak to a human supervisor regarding this case.")
                st.rerun()

        st.rerun()
