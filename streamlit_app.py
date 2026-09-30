
import sqlite3
from datetime import datetime
from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="SmartQueue — Campus Queue Intelligence",
    page_icon="🎫",
    layout="wide",
)

DB_PATH = Path(__file__).with_name("smartqueue.db")


# -----------------------------
# Database
# -----------------------------
def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = connect()
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        anonymous_identifier TEXT UNIQUE NOT NULL,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS service_points (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT DEFAULT 'stall',
        location TEXT,
        status TEXT DEFAULT 'OPEN',
        created_by_email TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS counters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_point_id INTEGER NOT NULL,
        counter_number INTEGER NOT NULL,
        status TEXT DEFAULT 'OPEN',
        current_token TEXT,
        opened_at TEXT
    );

    CREATE TABLE IF NOT EXISTS menu_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_point_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        available INTEGER DEFAULT 1,
        category TEXT DEFAULT 'Food',
        stock_target INTEGER DEFAULT 50,
        waste_count INTEGER DEFAULT 0,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS queue_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token TEXT UNIQUE NOT NULL,
        student_id INTEGER NOT NULL,
        service_point_id INTEGER NOT NULL,
        status TEXT DEFAULT 'WAITING',
        joined_at TEXT NOT NULL,
        called_at TEXT,
        completed_at TEXT,
        cancelled_at TEXT,
        estimated_wait REAL DEFAULT 0,
        actual_wait REAL
    );

    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_number TEXT UNIQUE NOT NULL,
        student_id INTEGER NOT NULL,
        service_point_id INTEGER NOT NULL,
        queue_entry_id INTEGER,
        counter_id INTEGER,
        status TEXT DEFAULT 'PLACED',
        total REAL DEFAULT 0,
        eta_minutes REAL DEFAULT 0,
        eta_at TEXT,
        admin_message TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        menu_item_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        quantity INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        type TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at TEXT NOT NULL,
        read INTEGER DEFAULT 0
    );
    """)

    now = datetime.now().isoformat(timespec="seconds")

    if cur.execute("SELECT COUNT(*) FROM students").fetchone()[0] == 0:
        cur.execute(
            "INSERT INTO students (anonymous_identifier, created_at) VALUES (?, ?)",
            ("demo-student", now),
        )

    if cur.execute("SELECT COUNT(*) FROM service_points").fetchone()[0] == 0:
        cur.execute(
            """INSERT INTO service_points
               (name, type, location, status, created_by_email, is_active, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            ("Main Canteen", "canteen", "GCU Campus", "OPEN",
             "unser01@gmail.com", 1, now),
        )
        stall_id = cur.lastrowid

        for n in range(1, 4):
            cur.execute(
                """INSERT INTO counters
                   (service_point_id, counter_number, status, opened_at)
                   VALUES (?, ?, 'OPEN', ?)""",
                (stall_id, n, now),
            )

        menu = [
            ("Veg Sandwich", 50, "Snacks"),
            ("Masala Dosa", 70, "South Indian"),
            ("Paneer Roll", 80, "Snacks"),
            ("Cold Coffee", 60, "Beverages"),
            ("Lemon Juice", 40, "Beverages"),
        ]
        for name, price, category in menu:
            cur.execute(
                """INSERT INTO menu_items
                   (service_point_id, name, price, available, category, created_at)
                   VALUES (?, ?, 1, 1, ?, ?)""",
                (stall_id, name, price, category, now),
            )

    conn.commit()
    conn.close()


def query(sql, params=()):
    conn = connect()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return rows


def execute(sql, params=()):
    conn = connect()
    cur = conn.execute(sql, params)
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id


def seed_if_needed():
    init_db()


# -----------------------------
# SmartQueue logic
# -----------------------------
def get_stalls():
    return query(
        "SELECT * FROM service_points WHERE is_active=1 ORDER BY id"
    )


def get_menu(stall_id):
    return query(
        """SELECT * FROM menu_items
           WHERE service_point_id=? AND available=1
           ORDER BY category, name""",
        (stall_id,),
    )


def waiting_entries(stall_id):
    return query(
        """SELECT * FROM queue_entries
           WHERE service_point_id=? AND status='WAITING'
           ORDER BY joined_at, id""",
        (stall_id,),
    )


def get_eta(stall_id, people_ahead=None):
    queue = waiting_entries(stall_id)
    if people_ahead is None:
        people_ahead = len(queue)

    counters = query(
        "SELECT status FROM counters WHERE service_point_id=?",
        (stall_id,),
    )
    active = max(1, len(counters))
    recent = query(
        """SELECT actual_wait FROM queue_entries
           WHERE service_point_id=? AND actual_wait IS NOT NULL
           ORDER BY id DESC LIMIT 20""",
        (stall_id,),
    )
    avg = sum(float(r["actual_wait"]) for r in recent) / len(recent) if recent else 3.0
    return round(max(0, (people_ahead * avg) / active), 1)


def next_token(stall_id):
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"Q-{today}-"
    rows = query(
        """SELECT token FROM queue_entries
           WHERE service_point_id=? AND token LIKE ?
           ORDER BY id DESC LIMIT 1""",
        (stall_id, prefix + "%"),
    )
    number = 1
    if rows:
        try:
            number = int(rows[0]["token"].split("-")[-1]) + 1
        except Exception:
            number = len(query(
                "SELECT id FROM queue_entries WHERE service_point_id=?",
                (stall_id,)
            )) + 1
    return f"{prefix}{number:03d}"


def place_order(student_id, stall_id, selected_items):
    now = datetime.now().isoformat(timespec="seconds")
    token = next_token(stall_id)
    queue_id = execute(
        """INSERT INTO queue_entries
           (token, student_id, service_point_id, status, joined_at)
           VALUES (?, ?, ?, 'WAITING', ?)""",
        (token, student_id, stall_id, now),
    )

    total = sum(x["price"] * x["qty"] for x in selected_items)
    ahead = len(waiting_entries(stall_id))
    eta = get_eta(stall_id, max(0, ahead - 1))
    order_no = f"ORD-{datetime.now().strftime('%H%M%S')}-{queue_id:03d}"

    order_id = execute(
        """INSERT INTO orders
           (order_number, student_id, service_point_id, queue_entry_id,
            status, total, eta_minutes, eta_at, admin_message,
            created_at, updated_at)
           VALUES (?, ?, ?, ?, 'PLACED', ?, ?, ?, ?, ?, ?)""",
        (
            order_no, student_id, stall_id, queue_id, total, eta,
            datetime.now().isoformat(timespec="seconds"),
            "Order placed successfully.",
            now, now
        ),
    )

    conn = connect()
    for item in selected_items:
        conn.execute(
            """INSERT INTO order_items
               (order_id, menu_item_id, name, price, quantity)
               VALUES (?, ?, ?, ?, ?)""",
            (order_id, item["id"], item["name"], item["price"], item["qty"]),
        )
    conn.execute(
        """INSERT INTO notifications
           (student_id, type, message, created_at)
           VALUES (?, 'ORDER', ?, ?)""",
        (student_id, f"Order {order_no} placed. Token {token}. ETA {eta} min.", now),
    )
    conn.commit()
    conn.close()

    return order_no, token, eta


def student_orders(student_id):
    return query(
        """SELECT o.*, s.name AS stall_name, q.token
           FROM orders o
           JOIN service_points s ON s.id=o.service_point_id
           LEFT JOIN queue_entries q ON q.id=o.queue_entry_id
           WHERE o.student_id=?
           ORDER BY o.id DESC""",
        (student_id,),
    )


def update_order(order_id, status, eta, message):
    now = datetime.now().isoformat(timespec="seconds")
    row = query("SELECT * FROM orders WHERE id=?", (order_id,))
    if not row:
        return

    order = row[0]
    execute(
        """UPDATE orders
           SET status=?, eta_minutes=?, eta_at=?, admin_message=?, updated_at=?
           WHERE id=?""",
        (
            status, eta,
            datetime.now().isoformat(timespec="seconds"),
            message, now, order_id
        ),
    )

    if status in ("READY", "COMPLETED"):
        execute(
            """INSERT INTO notifications
               (student_id, type, message, created_at)
               VALUES (?, 'STATUS', ?, ?)""",
            (
                order["student_id"],
                f"{order['order_number']}: {status}. {message}".strip(),
                now,
            ),
        )

    if status == "COMPLETED" and order["queue_entry_id"]:
        execute(
            """UPDATE queue_entries
               SET status='COMPLETED', completed_at=?, actual_wait=?
               WHERE id=?""",
            (now, eta, order["queue_entry_id"]),
        )


# -----------------------------
# UI
# -----------------------------
seed_if_needed()

st.title("🎫 SmartQueue")
st.caption("Campus Queue Intelligence — Know Your Wait. Plan Your Time.")

with st.sidebar:
    st.header("Demo Access")
    role = st.radio("Open as", ["Student", "Admin"], index=0)
    st.info("Demo login: unser01@gmail.com / 12345678")

stalls = get_stalls()

if not stalls:
    st.error("No active service points found.")
    st.stop()

stall_names = {s["id"]: s["name"] for s in stalls}

if role == "Student":
    st.header("Student Portal")

    stall_id = st.selectbox(
        "Choose campus service point",
        list(stall_names.keys()),
        format_func=lambda x: stall_names[x],
    )

    menu = get_menu(stall_id)

    if "cart" not in st.session_state:
        st.session_state.cart = {}

    st.subheader("🍴 Menu")
    cols = st.columns(2)

    for i, item in enumerate(menu):
        with cols[i % 2]:
            with st.container(border=True):
                st.markdown(f"### {item['name']}")
                st.write(f"₹{item['price']:.0f} · {item['category']}")
                qty = st.number_input(
                    "Quantity",
                    min_value=0,
                    max_value=10,
                    value=st.session_state.cart.get(item["id"], 0),
                    key=f"qty_{item['id']}",
                )
                if qty > 0:
                    st.session_state.cart[item["id"]] = qty
                elif item["id"] in st.session_state.cart:
                    del st.session_state.cart[item["id"]]

    selected = []
    for item in menu:
        qty = st.session_state.cart.get(item["id"], 0)
        if qty:
            selected.append({
                "id": item["id"],
                "name": item["name"],
                "price": float(item["price"]),
                "qty": qty,
            })

    if selected:
        total = sum(x["price"] * x["qty"] for x in selected)
        st.metric("Cart total", f"₹{total:.0f}")

        if st.button("🚀 Place Order & Join Queue", type="primary", use_container_width=True):
            order_no, token, eta = place_order(1, stall_id, selected)
            st.session_state.cart = {}
            st.success(f"Order {order_no} placed!")
            st.metric("Your Token", token)
            st.metric("Estimated Ready Time", f"{eta} min")
            st.balloons()

    st.divider()
    st.subheader("📍 My Live Orders")

    orders = student_orders(1)
    if orders:
        for order in orders:
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Token", order["token"] or "—")
                c2.metric("Status", order["status"])
                c3.metric("ETA", f"{order['eta_minutes']:.0f} min")
                c4.metric("Total", f"₹{order['total']:.0f}")
                st.write(order["admin_message"] or "No message from counter.")
    else:
        st.info("No orders yet. Choose items above to join the queue.")

else:
    st.header("⚙️ Admin Dashboard")

    stall_id = st.selectbox(
        "Service point",
        list(stall_names.keys()),
        format_func=lambda x: stall_names[x],
    )

    queue = waiting_entries(stall_id)
    counters = query(
        "SELECT * FROM counters WHERE service_point_id=? ORDER BY counter_number",
        (stall_id,),
    )
    orders = query(
        """SELECT o.*, q.token
           FROM orders o
           LEFT JOIN queue_entries q ON q.id=o.queue_entry_id
           WHERE o.service_point_id=?
           ORDER BY o.id DESC""",
        (stall_id,),
    )

    a, b, c, d = st.columns(4)
    a.metric("People Waiting", len(queue))
    b.metric("Open Counters", sum(1 for x in counters if x["status"] == "OPEN"))
    c.metric("Active Orders", sum(1 for x in orders if x["status"] in ("PLACED", "PREPARING")))
    d.metric("Avg ETA", f"{get_eta(stall_id):.1f} min")

    st.subheader("📋 Live Queue")
    if queue:
        df = pd.DataFrame([
            {
                "Position": i + 1,
                "Token": q["token"],
                "Status": q["status"],
                "Joined": q["joined_at"],
            }
            for i, q in enumerate(queue)
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.success("Queue is currently clear.")

    st.subheader("🧾 Order Control")
    if orders:
        order_options = {
            f"{o['order_number']} · {o['token'] or 'NO TOKEN'} · {o['status']}": o["id"]
            for o in orders
        }
        selected_label = st.selectbox("Select order", list(order_options.keys()))
        selected_id = order_options[selected_label]
        selected_order = next(o for o in orders if o["id"] == selected_id)

        c1, c2 = st.columns(2)
        with c1:
            new_status = st.selectbox(
                "Status",
                ["PLACED", "PREPARING", "READY", "COLLECTED", "COMPLETED", "CANCELLED"],
                index=["PLACED", "PREPARING", "READY", "COLLECTED", "COMPLETED", "CANCELLED"]
                .index(selected_order["status"])
            )
        with c2:
            new_eta = st.number_input(
                "ETA (minutes)",
                min_value=0.0,
                max_value=180.0,
                value=float(selected_order["eta_minutes"] or 0),
                step=1.0,
            )

        message = st.text_input(
            "Message to student",
            value=selected_order["admin_message"] or "",
        )

        if st.button("Update Order", type="primary"):
            update_order(selected_id, new_status, new_eta, message)
            st.success("Order updated.")
            st.rerun()
    else:
        st.info("No orders yet.")

    st.subheader("📊 Queue Analytics")
    completed = query(
        """SELECT COUNT(*) AS n FROM orders
           WHERE service_point_id=? AND status='COMPLETED'""",
        (stall_id,),
    )[0]["n"]
    cancelled = query(
        """SELECT COUNT(*) AS n FROM orders
           WHERE service_point_id=? AND status='CANCELLED'""",
        (stall_id,),
    )[0]["n"]

    x, y, z = st.columns(3)
    x.metric("Completed", completed)
    y.metric("Cancelled", cancelled)
    z.metric("Current Queue", len(queue))

    st.caption("Streamlit deployment version of SmartQueue. Demo data is stored in SQLite.")
