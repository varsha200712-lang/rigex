"""
Order Tracking & Investigation Page for ResolveAI.
Visualizes order timeline, carrier tracking updates, items, and provides
direct complaint escalation.
"""

import streamlit as st
from database.db import get_all_orders, get_order_by_id, create_support_ticket
from tools.order_tools import lookup_order
from ui.components import render_header, render_status_badge, render_order_timeline


def render_orders_page():
    render_header(
        title="Live Order Tracking & Inspection",
        subtitle="Search verified orders, inspect carrier checkpoints, and file instant incident tickets",
        badge="SQLite Grounded"
    )

    all_orders = get_all_orders(limit=30)
    order_ids = [o["order_id"] for o in all_orders]

    col_search, col_select = st.columns([2, 1])
    with col_search:
        searched_id = st.text_input("🔍 Search by Order ID", placeholder="e.g. ORD-1001, ORD-1007, ORD-1011").strip().upper()
    with col_select:
        selected_dropdown = st.selectbox("Or Quick-Select Order:", [""] + order_ids)

    target_id = searched_id if searched_id else (selected_dropdown if selected_dropdown else "ORD-1001")

    order_result = lookup_order(target_id)

    if not order_result["found"]:
        st.error(order_result["error"])
        st.info("💡 Try selecting one of our fictional orders: `ORD-1001`, `ORD-1007`, `ORD-1011`, or `ORD-1012`.")
        return

    order = get_order_by_id(target_id)

    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

    # Order Header Card
    st.markdown(f"""
    <div style="background: white; border: 1px solid #E2E8F0; border-radius: 14px; padding: 1.5rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 1.5rem;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
            <div>
                <h3 style="margin: 0; color: #0F172A; font-size: 1.4rem;">Order #{order['order_id']}</h3>
                <div style="color: #64748B; font-size: 0.85rem; margin-top: 0.2rem;">
                    Placed on: <b>{order['order_date']}</b> • Customer: <b>{order['customer_name']}</b> ({order['customer_email']})
                </div>
            </div>
            <div>
                {render_status_badge(order['status'])}
            </div>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; border-top: 1px solid #F1F5F9; padding-top: 1rem;">
            <div>
                <div style="font-size: 0.75rem; color: #64748B; font-weight: 600;">CARRIER</div>
                <div style="font-weight: 700; color: #1E293B;">{order['carrier'] or 'Not Assigned'}</div>
            </div>
            <div>
                <div style="font-size: 0.75rem; color: #64748B; font-weight: 600;">TRACKING NUMBER</div>
                <div style="font-weight: 700; color: #047857;">{order['tracking_number'] or 'Pending'}</div>
            </div>
            <div>
                <div style="font-size: 0.75rem; color: #64748B; font-weight: 600;">ESTIMATED DELIVERY</div>
                <div style="font-weight: 700; color: #1E293B;">{order['estimated_delivery'] or 'N/A'}</div>
            </div>
            <div>
                <div style="font-size: 0.75rem; color: #64748B; font-weight: 600;">TOTAL AMOUNT</div>
                <div style="font-weight: 700; color: #064E3B; font-size: 1.1rem;">${order['total_amount']:.2f}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Fulfillment Timeline
    st.subheader("🚚 Fulfillment & Delivery Progress")
    render_order_timeline(order["status"])

    if order.get("delay_reason"):
        st.error(f"⚠️ **Carrier Exception Flag**: {order['delay_reason']}")

    # Items Table
    st.subheader("📦 Order Line Items")
    items = order.get("items", [])
    if items:
        item_table = []
        for it in items:
            item_table.append({
                "Item ID": it["item_id"],
                "Product": it["product_name"],
                "Category": it["category"],
                "Quantity": it["quantity"],
                "Unit Price": f"${it['unit_price']:.2f}",
                "Perishable": "Yes" if it.get("is_perishable") else "No",
                "Serial Number": it.get("serial_number") or "N/A"
            })
        st.dataframe(item_table, use_container_width=True)

    # Direct Complaint Escalation
    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    with st.expander("🚨 Report an Issue with this Order", expanded=False):
        st.write("File a support ticket directly against this order:")
        cat = st.selectbox(
            "Select Issue Category",
            ["Delivery delay", "Damaged product", "Missing item", "Wrong item", "Return request", "Refund request", "Other"]
        )
        desc = st.text_area("Describe the issue in detail", placeholder="e.g. Package arrived crushed, item is chipped.")
        if st.button("Submit Order Complaint Ticket", type="primary"):
            if not desc.strip():
                st.warning("Please provide a description.")
            else:
                prio = "Urgent" if cat in ("Damaged product", "Refund request") else "High"
                t_id = create_support_ticket(
                    customer_id=order["customer_id"],
                    category=cat,
                    priority=prio,
                    subject=f"{cat} - {order['order_id']}",
                    description=desc,
                    order_id=order["order_id"],
                    status="Open"
                )
                st.success(f"Support ticket **{t_id}** created successfully! Our AI agent and supervisor will investigate.")
