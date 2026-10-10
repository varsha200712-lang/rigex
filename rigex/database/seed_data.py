"""
Seed script for ResolveAI SQLite Database.
Populates at least 15 fictional sample orders with diverse statuses,
sample customers, initial support tickets, and refund records.
"""

from datetime import datetime, timedelta
from database.db import get_connection, init_db


def seed_database(force_reseed: bool = False):
    """Seed the database if empty or if force_reseed is True."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    if force_reseed:
        cursor.execute("DELETE FROM audit_logs")
        cursor.execute("DELETE FROM conversations")
        cursor.execute("DELETE FROM refund_requests")
        cursor.execute("DELETE FROM support_tickets")
        cursor.execute("DELETE FROM order_items")
        cursor.execute("DELETE FROM orders")
        cursor.execute("DELETE FROM customers")
        conn.commit()

    # Check existing
    cursor.execute("SELECT COUNT(*) FROM orders")
    count = cursor.fetchone()[0]
    if count >= 15 and not force_reseed:
        conn.close()
        return

    now = datetime.now()

    # 1. Seed Customers
    customers = [
        ("CUST-101", "Aarav Sharma", "aarav.sharma@example.com", "+1-555-0192", (now - timedelta(days=90)).strftime("%Y-%m-%d")),
        ("CUST-102", "Priya Venkatesh", "priya.v@example.com", "+1-555-0145", (now - timedelta(days=60)).strftime("%Y-%m-%d")),
        ("CUST-103", "Karthik Subramanian", "karthik.sub@example.com", "+1-555-0188", (now - timedelta(days=45)).strftime("%Y-%m-%d")),
        ("CUST-104", "Ananya Iyer", "ananya.iyer@example.com", "+1-555-0123", (now - timedelta(days=30)).strftime("%Y-%m-%d")),
        ("CUST-105", "Michael Chen", "mchen@example.com", "+1-555-0177", (now - timedelta(days=20)).strftime("%Y-%m-%d")),
        ("CUST-106", "Sarah Jenkins", "sjenkins@example.com", "+1-555-0119", (now - timedelta(days=15)).strftime("%Y-%m-%d")),
    ]

    for c in customers:
        cursor.execute("""
        INSERT OR IGNORE INTO customers (customer_id, name, email, phone, created_at)
        VALUES (?, ?, ?, ?, ?)
        """, c)

    # 2. Seed 16 Fictional Orders with different statuses
    orders = [
        # Processing orders
        (
            "ORD-1001", "CUST-101", "Aarav Sharma", "aarav.sharma@example.com",
            (now - timedelta(days=1)).strftime("%Y-%m-%d"),
            "Processing", "FedEx", "FX-90210411",
            "742 Evergreen Terrace, Springfield, OR",
            (now + timedelta(days=3)).strftime("%Y-%m-%d"), None, 45.99, None
        ),
        (
            "ORD-1002", "CUST-102", "Priya Venkatesh", "priya.v@example.com",
            now.strftime("%Y-%m-%d"),
            "Processing", None, None,
            "1204 Blossom Lane, Austin, TX",
            (now + timedelta(days=4)).strftime("%Y-%m-%d"), None, 189.50, None
        ),

        # Shipped orders
        (
            "ORD-1003", "CUST-103", "Karthik Subramanian", "karthik.sub@example.com",
            (now - timedelta(days=2)).strftime("%Y-%m-%d"),
            "Shipped", "UPS", "UPS-88291034",
            "450 Marina Blvd, San Francisco, CA",
            (now + timedelta(days=2)).strftime("%Y-%m-%d"), None, 79.99, None
        ),
        (
            "ORD-1004", "CUST-104", "Ananya Iyer", "ananya.iyer@example.com",
            (now - timedelta(days=3)).strftime("%Y-%m-%d"),
            "Shipped", "DHL Express", "DHL-44019283",
            "88 Beacon Street, Boston, MA",
            (now + timedelta(days=1)).strftime("%Y-%m-%d"), None, 299.00, None
        ),

        # In Transit orders
        (
            "ORD-1005", "CUST-105", "Michael Chen", "mchen@example.com",
            (now - timedelta(days=4)).strftime("%Y-%m-%d"),
            "In transit", "FedEx", "FX-33920199",
            "1002 Lakeview Ave, Seattle, WA",
            (now + timedelta(days=1)).strftime("%Y-%m-%d"), None, 120.00, None
        ),
        (
            "ORD-1006", "CUST-106", "Sarah Jenkins", "sjenkins@example.com",
            (now - timedelta(days=3)).strftime("%Y-%m-%d"),
            "In transit", "OnTrac", "ONT-11928472",
            "55 Desert Ridge Rd, Phoenix, AZ",
            (now + timedelta(days=2)).strftime("%Y-%m-%d"), None, 34.50, None
        ),

        # Delivered orders (recent & older)
        (
            "ORD-1007", "CUST-101", "Aarav Sharma", "aarav.sharma@example.com",
            (now - timedelta(days=8)).strftime("%Y-%m-%d"),
            "Delivered", "FedEx", "FX-88201948",
            "742 Evergreen Terrace, Springfield, OR",
            (now - timedelta(days=4)).strftime("%Y-%m-%d"),
            (now - timedelta(days=4)).strftime("%Y-%m-%d"),
            42.00, None
        ),
        (
            "ORD-1008", "CUST-102", "Priya Venkatesh", "priya.v@example.com",
            (now - timedelta(days=14)).strftime("%Y-%m-%d"),
            "Delivered", "UPS", "UPS-77192834",
            "1204 Blossom Lane, Austin, TX",
            (now - timedelta(days=10)).strftime("%Y-%m-%d"),
            (now - timedelta(days=10)).strftime("%Y-%m-%d"),
            165.00, None
        ),
        (
            "ORD-1009", "CUST-103", "Karthik Subramanian", "karthik.sub@example.com",
            (now - timedelta(days=25)).strftime("%Y-%m-%d"),
            "Delivered", "DHL Express", "DHL-99201823",
            "450 Marina Blvd, San Francisco, CA",
            (now - timedelta(days=21)).strftime("%Y-%m-%d"),
            (now - timedelta(days=20)).strftime("%Y-%m-%d"),
            89.90, None
        ),
        (
            "ORD-1010", "CUST-104", "Ananya Iyer", "ananya.iyer@example.com",
            (now - timedelta(days=38)).strftime("%Y-%m-%d"),
            "Delivered", "UPS", "UPS-11209384",
            "88 Beacon Street, Boston, MA",
            (now - timedelta(days=34)).strftime("%Y-%m-%d"),
            (now - timedelta(days=33)).strftime("%Y-%m-%d"),
            210.00, None
        ),

        # Delayed orders
        (
            "ORD-1011", "CUST-105", "Michael Chen", "mchen@example.com",
            (now - timedelta(days=12)).strftime("%Y-%m-%d"),
            "Delayed", "FedEx", "FX-66291048",
            "1002 Lakeview Ave, Seattle, WA",
            (now - timedelta(days=6)).strftime("%Y-%m-%d"), None,
            145.00, "Severe regional weather hub closure in Chicago"
        ),
        (
            "ORD-1012", "CUST-106", "Sarah Jenkins", "sjenkins@example.com",
            (now - timedelta(days=20)).strftime("%Y-%m-%d"),
            "Delayed", "UPS", "UPS-55928174",
            "55 Desert Ridge Rd, Phoenix, AZ",
            (now - timedelta(days=15)).strftime("%Y-%m-%d"), None,
            49.99, "Carrier lost tracking scan at sorting facility (>14 days delayed)"
        ),
        (
            "ORD-1013", "CUST-101", "Aarav Sharma", "aarav.sharma@example.com",
            (now - timedelta(days=10)).strftime("%Y-%m-%d"),
            "Delayed", "OnTrac", "ONT-88273619",
            "742 Evergreen Terrace, Springfield, OR",
            (now - timedelta(days=3)).strftime("%Y-%m-%d"), None,
            28.50, "Courier delivery truck breakdown, re-routed"
        ),

        # Cancelled orders
        (
            "ORD-1014", "CUST-102", "Priya Venkatesh", "priya.v@example.com",
            (now - timedelta(days=15)).strftime("%Y-%m-%d"),
            "Cancelled", None, None,
            "1204 Blossom Lane, Austin, TX",
            None, None, 65.00, "Customer requested cancellation during Processing"
        ),
        (
            "ORD-1015", "CUST-103", "Karthik Subramanian", "karthik.sub@example.com",
            (now - timedelta(days=7)).strftime("%Y-%m-%d"),
            "Cancelled", None, None,
            "450 Marina Blvd, San Francisco, CA",
            None, None, 310.00, "Payment verification timeout"
        ),
        (
            "ORD-1016", "CUST-104", "Ananya Iyer", "ananya.iyer@example.com",
            (now - timedelta(days=5)).strftime("%Y-%m-%d"),
            "Delivered", "FedEx", "FX-55019284",
            "88 Beacon Street, Boston, MA",
            (now - timedelta(days=2)).strftime("%Y-%m-%d"),
            (now - timedelta(days=2)).strftime("%Y-%m-%d"),
            19.99, None
        ),
    ]

    for ord_tuple in orders:
        cursor.execute("""
        INSERT OR REPLACE INTO orders (
            order_id, customer_id, customer_name, customer_email,
            order_date, status, carrier, tracking_number,
            shipping_address, estimated_delivery, actual_delivery,
            total_amount, delay_reason
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ord_tuple)

    # 3. Seed Order Items
    order_items = [
        # ORD-1001
        ("ITM-101", "ORD-1001", "Wireless Ergonomic Mouse", "Electronics", 1, 45.99, 0, "SN-MS-8819"),
        # ORD-1002
        ("ITM-102", "ORD-1002", "Noise-Cancelling Studio Headphones", "Electronics", 1, 159.50, 0, "SN-HP-9921"),
        ("ITM-103", "ORD-1002", "Braided USB-C Cable (2-Pack)", "Accessories", 1, 30.00, 0, None),
        # ORD-1003
        ("ITM-104", "ORD-1003", "Mechanical Gaming Keyboard RGB", "Electronics", 1, 79.99, 0, "SN-KB-5501"),
        # ORD-1004
        ("ITM-105", "ORD-1004", "Ultra-Wide 34-inch Curved Monitor", "Electronics", 1, 299.00, 0, "SN-MN-4492"),
        # ORD-1005
        ("ITM-106", "ORD-1005", "Smart Home Air Purifier HEPA", "Home Appliances", 1, 120.00, 0, "SN-AP-3301"),
        # ORD-1006
        ("ITM-107", "ORD-1006", "Organic Matcha Green Tea Set", "Perishables", 1, 34.50, 1, None),
        # ORD-1007 (Delivered, under $50 - ideal for instant damaged refund demo)
        ("ITM-108", "ORD-1007", "Ceramic Pour-Over Coffee Dripper", "Kitchenware", 1, 42.00, 0, None),
        # ORD-1008 (Delivered, over $150 - ideal for human approval refund demo)
        ("ITM-109", "ORD-1008", "Smart Video Doorbell Camera Pro", "Electronics", 1, 165.00, 0, "SN-DB-2201"),
        # ORD-1009
        ("ITM-110", "ORD-1009", "Waterproof Bluetooth Hiking Speaker", "Audio", 1, 89.90, 0, "SN-SP-7712"),
        # ORD-1010 (Delivered > 30 days ago - exception case)
        ("ITM-111", "ORD-1010", "Stainless Steel Stand Mixer 5Qt", "Kitchenware", 1, 210.00, 0, "SN-MX-9988"),
        # ORD-1011 (Delayed)
        ("ITM-112", "ORD-1011", "Portable High-Speed SSD 2TB", "Electronics", 1, 145.00, 0, "SN-SD-1102"),
        # ORD-1012 (Delayed > 14 days, eligible for cancellation refund)
        ("ITM-113", "ORD-1012", "Smart Wi-Fi LED Desk Lamp", "Home", 1, 49.99, 0, None),
        # ORD-1013
        ("ITM-114", "ORD-1013", "Universal Laptop Stand Aluminum", "Office", 1, 28.50, 0, None),
        # ORD-1014
        ("ITM-115", "ORD-1014", "Wireless Fast Charging Pad", "Accessories", 1, 65.00, 0, None),
        # ORD-1015
        ("ITM-116", "ORD-1015", "Premium Noise Isolating Earbuds", "Audio", 1, 310.00, 0, "SN-EB-1200"),
        # ORD-1016
        ("ITM-117", "ORD-1016", "Gourmet Dark Chocolate Truffles", "Perishables", 1, 19.99, 1, None),
    ]

    for item in order_items:
        cursor.execute("""
        INSERT OR REPLACE INTO order_items (
            item_id, order_id, product_name, category, quantity, unit_price, is_perishable, serial_number
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, item)

    # 4. Seed Initial Sample Tickets
    sample_tickets = [
        (
            "TCK-1001", "CUST-105", "ORD-1011", "Delivery delay", "High", "In Progress",
            "Delay inquiry for portable SSD",
            "Customer reached out asking why ORD-1011 is held up in Chicago sorting facility.",
            (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
            (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
            "ResolveAI Worker", "Tracking update provided to customer with weather delay note."
        ),
        (
            "TCK-1002", "CUST-102", "ORD-1008", "Refund request", "Urgent", "Awaiting Approval",
            "Refund requested for Smart Video Doorbell",
            "Customer requested return and refund ($165.00) due to incompatible mounting bracket. High-value refund requires administrator approval.",
            (now - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S"),
            (now - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S"),
            "ResolveAI Worker", None
        ),
        (
            "TCK-1003", "CUST-101", "ORD-1007", "Damaged product", "Medium", "Resolved",
            "Ceramic coffee dripper chipped during delivery",
            "Handle was cracked upon unboxing. Value $42.00 is below $50 threshold; instant refund processed per policy.",
            (now - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"),
            (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
            "ResolveAI Worker", "Instant refund of $42.00 approved and credited."
        ),
    ]

    for tck in sample_tickets:
        cursor.execute("""
        INSERT OR REPLACE INTO support_tickets (
            ticket_id, customer_id, order_id, category, priority, status,
            subject, description, created_at, updated_at, assigned_agent, resolution_notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, tck)

    # 5. Seed Initial Refund Requests
    sample_refunds = [
        (
            "REF-501", "TCK-1002", "ORD-1008", "CUST-102", 165.00,
            "Incompatible doorframe mounting, unopened product",
            "Human Approval Required", "Pending", None, None, None,
            (now - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S")
        ),
        (
            "REF-502", "TCK-1003", "ORD-1007", "CUST-101", 42.00,
            "Chipped ceramic dripper on arrival (photo provided)",
            "Eligible", "Approved", "System Auto-Rule", "Damaged under $50 instant policy",
            (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
            (now - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")
        ),
    ]

    for ref in sample_refunds:
        cursor.execute("""
        INSERT OR REPLACE INTO refund_requests (
            request_id, ticket_id, order_id, customer_id, amount, reason,
            eligibility_status, approval_status, admin_reviewed_by, admin_review_reason,
            admin_reviewed_at, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ref)

    conn.commit()
    conn.close()
    print("Database successfully initialized with 16 sample orders, customers, and seed records.")


if __name__ == "__main__":
    seed_database(force_reseed=True)
