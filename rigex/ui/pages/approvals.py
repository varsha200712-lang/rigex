"""
Refund Approval & Supervisor Dashboard for ResolveAI.
Restricted human-in-the-loop workflow requiring explicit admin PIN authentication,
mandatory rejection reason, order & policy evidence audit, and transaction logging.
"""

import streamlit as st
from config.settings import ADMIN_PIN
from database.db import get_all_refund_requests, review_refund_request, get_order_by_id
from ui.components import render_header, render_status_badge


def render_approvals_page():
    render_header(
        title="Restricted Refund Approval Dashboard",
        subtitle="Human-in-the-loop supervision for high-value orders, exceptions, and non-receipt claims",
        badge="Admin Supervision"
    )

    # Admin PIN Authentication Check
    if "admin_authenticated" not in st.session_state:
        st.session_state["admin_authenticated"] = False

    if not st.session_state["admin_authenticated"]:
        st.warning("🔒 This portal manages restricted financial disbursements. Enter your Admin PIN to proceed.")
        col_pin, col_btn = st.columns([2, 1])
        with col_pin:
            entered_pin = st.text_input("Administrator Security PIN", type="password", placeholder="Enter PIN (Default: 1234)")
        with col_btn:
            st.markdown("<div style='margin-top: 1.7rem;'></div>", unsafe_allow_html=True)
            if st.button("Unlock Admin Dashboard", type="primary"):
                if entered_pin.strip() == ADMIN_PIN:
                    st.session_state["admin_authenticated"] = True
                    st.success("Admin authorized successfully!")
                    st.rerun()
                else:
                    st.error("Invalid Admin PIN. Please verify your credentials.")
        return

    # Admin Header & Controls
    c_head, c_lock = st.columns([4, 1])
    with c_head:
        st.caption("👤 Logged in as **Authorized Support Supervisor**")
    with c_lock:
        if st.button("🔒 Lock Dashboard"):
            st.session_state["admin_authenticated"] = False
            st.rerun()

    tab_pending, tab_history = st.tabs(["⏳ Pending Approval Queue", "📜 Refund Audit History"])

    with tab_pending:
        pending_requests = get_all_refund_requests(status="Pending")
        st.subheader(f"Pending Supervisor Decisions ({len(pending_requests)})")

        if not pending_requests:
            st.success("🎉 No pending refund approval requests in queue. All customer requests are up to date.")
        else:
            for req in pending_requests:
                with st.container():
                    st.markdown(f"""
                    <div style="background: white; border: 1px solid #CBD5E1; border-radius: 12px; padding: 1.25rem; margin-bottom: 1.25rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
                        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #F1F5F9; padding-bottom: 0.75rem;">
                            <div>
                                <span style="font-weight: 700; font-size: 1.1rem; color: #0F172A;">Request #{req['request_id']}</span>
                                <span style="color: #64748B; font-size: 0.85rem; margin-left: 0.75rem;">Order: <b>{req['order_id']}</b></span>
                            </div>
                            <div style="font-size: 1.2rem; font-weight: 800; color: #B91C1C;">
                                ${req['amount']:.2f}
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Order verification facts
                    order = get_order_by_id(req["order_id"])
                    col_info1, col_info2 = st.columns(2)
                    with col_info1:
                        st.markdown(f"**Customer:** `{req['customer_id']}` ({order['customer_name'] if order else 'N/A'})")
                        st.markdown(f"**Linked Ticket:** `{req['ticket_id']}`")
                        st.markdown(f"**Eligibility Evaluation:** `{req['eligibility_status']}`")
                        st.markdown(f"**Customer Stated Reason:** {req['reason']}")
                    with col_info2:
                        if order:
                            st.markdown(f"**Order Status:** `{order['status']}`")
                            st.markdown(f"**Carrier:** {order.get('carrier') or 'N/A'} (Tracking: `{order.get('tracking_number') or 'None'}`)")
                            st.markdown(f"**Actual Delivery Date:** `{order.get('actual_delivery') or 'Pending'}`")

                    # Decision Action Form
                    with st.form(key=f"decision_form_{req['request_id']}"):
                        st.markdown("##### Administrative Decision:")
                        d_col1, d_col2 = st.columns([1, 2])
                        with d_col1:
                            decision = st.radio("Action", ["Approve Refund", "Reject Refund"], key=f"radio_{req['request_id']}")
                        with d_col2:
                            reason = st.text_area(
                                "Justification / Audit Reason (Required for rejection)",
                                placeholder="e.g. Approved per 30-day policy exception; item verified defective.",
                                key=f"reason_{req['request_id']}"
                            )

                        confirm = st.checkbox("I confirm that I have reviewed the order facts and policy evidence.", key=f"chk_{req['request_id']}")
                        submit_btn = st.form_submit_button("Execute Decision", type="primary")

                        if submit_btn:
                            if not confirm:
                                st.warning("Please check the confirmation box before submitting.")
                            elif decision == "Reject Refund" and not reason.strip():
                                st.error("A justification reason is mandatory when rejecting a refund request.")
                            else:
                                final_stat = "Approved" if decision == "Approve Refund" else "Rejected"
                                review_refund_request(
                                    request_id=req["request_id"],
                                    decision=final_stat,
                                    admin_user="Supervisor Admin",
                                    reason=reason.strip() or "Standard policy approval"
                                )
                                st.success(f"Request {req['request_id']} has been successfully {final_stat}! Ticket updated.")
                                st.rerun()

    with tab_history:
        st.subheader("All Refund Decisions Audit Log")
        all_reqs = get_all_refund_requests()
        if not all_reqs:
            st.info("No refund history recorded.")
        else:
            table_data = []
            for r in all_reqs:
                table_data.append({
                    "Request ID": r["request_id"],
                    "Order ID": r["order_id"],
                    "Customer": r["customer_id"],
                    "Amount": f"${r['amount']:.2f}",
                    "Status": r["approval_status"],
                    "Reviewed By": r.get("admin_reviewed_by") or "Automated / Pending",
                    "Audit Notes": r.get("admin_review_reason") or "N/A",
                    "Timestamp": r.get("admin_reviewed_at") or r["created_at"]
                })
            st.dataframe(table_data, use_container_width=True)
