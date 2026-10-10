"""
Complaint Center & Support Ticket Management for ResolveAI.
Allows customer intake, prioritization, filtering, and ticket lifecycle tracking.
"""

import streamlit as st
from database.db import create_support_ticket, get_all_tickets, update_ticket_status, get_all_orders
from ui.components import render_header, render_status_badge, render_priority_badge


def render_complaints_page():
    render_header(
        title="ResolveAI Complaint Center & Support Tickets",
        subtitle="Submit complaints, track SLAs, update ticket lifecycle states, and monitor resolution notes",
        badge="Enterprise Triage"
    )

    tab_list, tab_submit = st.tabs(["📋 Support Ticket Directory", "✍️ Submit New Complaint"])

    with tab_submit:
        st.subheader("File a Customer Service Ticket")
        with st.form("complaint_form"):
            c1, c2 = st.columns(2)
            with c1:
                category = st.selectbox(
                    "Complaint Category *",
                    [
                        "Delivery delay", "Damaged product", "Missing item", "Wrong item",
                        "Return request", "Refund request", "Payment issue", "General inquiry", "Other"
                    ]
                )
                customer_id = st.text_input("Customer ID *", value="CUST-101")
            with c2:
                priority = st.selectbox("Priority Level", ["Low", "Medium", "High", "Urgent"], index=2)
                all_orders = get_all_orders(limit=20)
                order_opts = ["None"] + [o["order_id"] for o in all_orders]
                linked_order = st.selectbox("Linked Order ID (Optional)", order_opts)

            subject = st.text_input("Subject Line *", placeholder="e.g. Broken packaging on ORD-1007")
            description = st.text_area("Detailed Complaint Description *", placeholder="Explain the incident, items affected, or questions...")

            submitted = st.form_submit_button("Submit Complaint Ticket", type="primary")

            if submitted:
                if not subject.strip() or not description.strip():
                    st.error("Please fill in both Subject Line and Description.")
                else:
                    order_val = None if linked_order == "None" else linked_order
                    t_id = create_support_ticket(
                        customer_id=customer_id.strip(),
                        category=category,
                        priority=priority,
                        subject=subject.strip(),
                        description=description.strip(),
                        order_id=order_val,
                        status="Open"
                    )
                    st.success(f"Ticket **{t_id}** created successfully! Category: `{category}`, Priority: `{priority}`.")

    with tab_list:
        st.subheader("Filter & Track Active Tickets")
        col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
        with col_f1:
            cat_filter = st.selectbox(
                "Filter by Category",
                ["All", "Delivery delay", "Damaged product", "Missing item", "Wrong item", "Return request", "Refund request", "Payment issue", "General inquiry", "Other"]
            )
        with col_f2:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All", "Open", "In Progress", "Awaiting Customer", "Awaiting Approval", "Escalated", "Resolved", "Closed"]
            )
        with col_f3:
            search_query = st.text_input("Search tickets by ID, Customer, or Keywords", placeholder="e.g. TCK-1001, damaged, ORD-1008...")

        tickets = get_all_tickets(
            category=None if cat_filter == "All" else cat_filter,
            status=None if status_filter == "All" else status_filter,
            search=search_query.strip() if search_query else None
        )

        st.caption(f"Showing **{len(tickets)}** tickets matching criteria.")

        if not tickets:
            st.info("No tickets match the selected filters.")
        else:
            for t in tickets:
                with st.expander(f"{t['ticket_id']} — {t['subject']} ({t['status']})", expanded=False):
                    c_meta1, c_meta2 = st.columns([3, 1])
                    with c_meta1:
                        st.markdown(f"""
                        **Customer:** `{t['customer_id']}` | **Order:** `{t['order_id'] or 'None'}` | **Filed:** `{t['created_at']}`
                        
                        **Description:**  
                        {t['description']}
                        """)
                        if t.get("resolution_notes"):
                            st.info(f"**Resolution Notes:** {t['resolution_notes']}")
                    with c_meta2:
                        st.markdown(f"**Category:** {t['category']}")
                        st.markdown(f"**Priority:** {render_priority_badge(t['priority'])}", unsafe_allow_html=True)
                        st.markdown(f"**Status:** {render_status_badge(t['status'])}", unsafe_allow_html=True)

                        # Status updater
                        new_stat = st.selectbox(
                            "Update Status",
                            ["Open", "In Progress", "Awaiting Customer", "Awaiting Approval", "Escalated", "Resolved", "Closed"],
                            index=["Open", "In Progress", "Awaiting Customer", "Awaiting Approval", "Escalated", "Resolved", "Closed"].index(t["status"]) if t["status"] in ["Open", "In Progress", "Awaiting Customer", "Awaiting Approval", "Escalated", "Resolved", "Closed"] else 0,
                            key=f"stat_sel_{t['ticket_id']}"
                        )
                        if new_stat != t["status"]:
                            if st.button("Save Status", key=f"btn_save_{t['ticket_id']}"):
                                update_ticket_status(t["ticket_id"], new_stat)
                                st.success(f"Status updated to {new_stat}")
                                st.rerun()
