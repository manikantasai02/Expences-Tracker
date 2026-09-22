import sqlite3
import os
import hashlib
import secrets
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

CATEGORIES = [
    "Food",
    "Cloths",
    "Medical",
    "Enjoyment",
    "Fees",
    "Travelling"
]

# On Render, the app directory is read-only; use /tmp which is writable.
# Locally, store the DB next to db.py for convenience.
if os.environ.get("RENDER"):
    DB_DIR = "/tmp"
else:
    DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "expenses.db")

@contextmanager
def get_connection(db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()

def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    if not salt:
        salt = secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return derived.hex(), salt

def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return secrets.compare_digest(derived.hex(), stored_hash)

def init_db(db_path: str = DB_PATH) -> None:
    """Initialize the tables with user isolation and session management."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        # 1. Users Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                password_hash TEXT,
                salt TEXT,
                auth_provider TEXT DEFAULT 'email',
                google_sub TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. Sessions Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # 3. Check if expenses table exists and if user_id column exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='expenses'")
        table_exists = cursor.fetchone()

        if not table_exists:
            cursor.execute("""
                CREATE TABLE expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    note TEXT DEFAULT '',
                    date TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
        else:
            # Check for user_id column
            cursor.execute("PRAGMA table_info(expenses)")
            columns = [row["name"] for row in cursor.fetchall()]
            if "user_id" not in columns:
                # Ensure a default demo user exists
                cursor.execute("SELECT id FROM users WHERE email = 'demo@example.com'")
                demo_user = cursor.fetchone()
                if not demo_user:
                    p_hash, salt = hash_password("demo123")
                    cursor.execute(
                        "INSERT INTO users (email, name, password_hash, salt, auth_provider) VALUES (?, ?, ?, ?, ?)",
                        ("demo@example.com", "Demo User", p_hash, salt, "email")
                    )
                    default_uid = cursor.lastrowid
                else:
                    default_uid = demo_user["id"]

                cursor.execute(f"ALTER TABLE expenses ADD COLUMN user_id INTEGER DEFAULT {default_uid}")

        # Ensure demo user exists for immediate guest access
        cursor.execute("SELECT id FROM users WHERE email = 'demo@example.com'")
        if not cursor.fetchone():
            p_hash, salt = hash_password("demo123")
            cursor.execute(
                "INSERT INTO users (email, name, password_hash, salt, auth_provider) VALUES (?, ?, ?, ?, ?)",
                ("demo@example.com", "Demo User", p_hash, salt, "email")
            )

        conn.commit()

# ==============================================================================
# Authentication & User Management
# ==============================================================================

def create_user(email: str, name: str, password: Optional[str] = None, auth_provider: str = "email", google_sub: Optional[str] = None, db_path: str = DB_PATH) -> Dict[str, Any]:
    email = email.strip().lower()
    name = name.strip()

    if not email:
        raise ValueError("Email is required.")
    if not name:
        raise ValueError("Name is required.")

    p_hash, salt = None, None
    if password:
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters long.")
        p_hash, salt = hash_password(password)

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            raise ValueError("An account with this email already exists.")

        cursor.execute(
            "INSERT INTO users (email, name, password_hash, salt, auth_provider, google_sub) VALUES (?, ?, ?, ?, ?, ?)",
            (email, name, p_hash, salt, auth_provider, google_sub)
        )
        user_id = cursor.lastrowid
        conn.commit()

        cursor.execute("SELECT id, email, name, auth_provider, created_at FROM users WHERE id = ?", (user_id,))
        return dict(cursor.fetchone())

def authenticate_user(email: str, password: str, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    email = email.strip().lower()
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        if not user:
            return None

        if not user["password_hash"] or not user["salt"]:
            return None

        if verify_password(password, user["password_hash"], user["salt"]):
            return {
                "id": user["id"],
                "email": user["email"],
                "name": user["name"],
                "auth_provider": user["auth_provider"],
                "created_at": user["created_at"]
            }
        return None

def create_or_get_google_user(email: str, name: str, google_sub: Optional[str] = None, db_path: str = DB_PATH) -> Dict[str, Any]:
    email = email.strip().lower()
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, name, auth_provider, created_at FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        if user:
            # Update name or google_sub if needed
            cursor.execute("UPDATE users SET google_sub = COALESCE(?, google_sub) WHERE email = ?", (google_sub, email))
            conn.commit()
            return dict(user)

        # Create new user
        cursor.execute(
            "INSERT INTO users (email, name, auth_provider, google_sub) VALUES (?, ?, 'google', ?)",
            (email, name or email.split("@")[0], google_sub)
        )
        user_id = cursor.lastrowid
        conn.commit()
        cursor.execute("SELECT id, email, name, auth_provider, created_at FROM users WHERE id = ?", (user_id,))
        return dict(cursor.fetchone())

def create_session(user_id: int, db_path: str = DB_PATH) -> str:
    token = secrets.token_hex(32)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO sessions (token, user_id) VALUES (?, ?)", (token, user_id))
        conn.commit()
    return token

def get_user_by_session(token: str, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    if not token:
        return None
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.email, u.name, u.auth_provider, u.created_at
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.token = ?
        """, (token,))
        row = cursor.fetchone()
        return dict(row) if row else None

def delete_session(token: str, db_path: str = DB_PATH) -> bool:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()
        return cursor.rowcount > 0

# ==============================================================================
# User-Scoped Expenses CRUD
# ==============================================================================

def add_expense(user_id: int, amount: float, category: str, note: str = "", date: Optional[str] = None, db_path: str = DB_PATH) -> Dict[str, Any]:
    """Add a new expense scoped to a specific user."""
    if category not in CATEGORIES:
        matched = next((c for c in CATEGORIES if c.lower() == category.lower()), None)
        if matched:
            category = matched
        else:
            raise ValueError(f"Invalid category '{category}'. Must be one of: {', '.join(CATEGORIES)}")

    if amount <= 0:
        raise ValueError("Amount must be greater than 0.")

    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO expenses (user_id, amount, category, note, date) VALUES (?, ?, ?, ?, ?)",
            (user_id, round(float(amount), 2), category, note.strip(), date)
        )
        expense_id = cursor.lastrowid
        conn.commit()

        cursor.execute("SELECT * FROM expenses WHERE id = ? AND user_id = ?", (expense_id, user_id))
        row = cursor.fetchone()
        return dict(row)

def get_expenses(user_id: int, category: Optional[str] = None, search: Optional[str] = None,
                 date: Optional[str] = None, year: Optional[int] = None, month: Optional[int] = None,
                 db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """Retrieve expenses strictly belonging to the user with optional filters."""
    query = "SELECT * FROM expenses WHERE user_id = ?"
    params = [user_id]

    if category and category.lower() != "all":
        query += " AND category = ?"
        params.append(category)

    if search:
        query += " AND (note LIKE ? OR category LIKE ?)"
        pattern = f"%{search}%"
        params.extend([pattern, pattern])

    if date:
        query += " AND date = ?"
        params.append(date)
    elif year and month:
        month_str = f"{year:04d}-{month:02d}"
        query += " AND date LIKE ?"
        params.append(f"{month_str}%")
    elif year:
        query += " AND date LIKE ?"
        params.append(f"{year:04d}%")

    query += " ORDER BY date DESC, id DESC"

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def delete_expense(user_id: int, expense_id: int, db_path: str = DB_PATH) -> bool:
    """Delete an expense only if it belongs to the authenticated user."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expenses WHERE id = ? AND user_id = ?", (expense_id, user_id))
        conn.commit()
        return cursor.rowcount > 0

def clear_all(user_id: int, db_path: str = DB_PATH) -> None:
    """Clear all records for this specific user."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expenses WHERE user_id = ?", (user_id,))
        conn.commit()

# ==============================================================================
# Analytics & Time-Based Aggregations (Day, Month, Year, Calendar)
# ==============================================================================

def get_summary(user_id: int, period: str = "all", year: Optional[int] = None, month: Optional[int] = None, date: Optional[str] = None, db_path: str = DB_PATH) -> Dict[str, Any]:
    """Calculate summary and category breakdowns scoped to user and time period."""
    base_query = "FROM expenses WHERE user_id = ?"
    params = [user_id]

    if period == "day" and date:
        base_query += " AND date = ?"
        params.append(date)
    elif period == "month" and year and month:
        base_query += " AND date LIKE ?"
        params.append(f"{year:04d}-{month:02d}%")
    elif period == "year" and year:
        base_query += " AND date LIKE ?"
        params.append(f"{year:04d}%")

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT category, SUM(amount) as total, COUNT(id) as count {base_query} GROUP BY category", params)
        rows = cursor.fetchall()

    category_totals = {cat: 0.0 for cat in CATEGORIES}
    category_counts = {cat: 0 for cat in CATEGORIES}
    total_spent = 0.0
    total_count = 0

    for row in rows:
        cat = row["category"]
        total = float(row["total"]) if row["total"] else 0.0
        count = int(row["count"]) if row["count"] else 0
        if cat in category_totals:
            category_totals[cat] = round(total, 2)
            category_counts[cat] = count
        total_spent += total
        total_count += count

    total_spent = round(total_spent, 2)
    category_percentages = {}
    for cat in CATEGORIES:
        if total_spent > 0:
            category_percentages[cat] = round((category_totals[cat] / total_spent) * 100, 1)
        else:
            category_percentages[cat] = 0.0

    # Quick comparative indicators
    today_str = datetime.now().strftime("%Y-%m-%d")
    current_month_str = datetime.now().strftime("%Y-%m")
    current_year_str = datetime.now().strftime("%Y")

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(amount) as t FROM expenses WHERE user_id = ? AND date = ?", (user_id, today_str))
        r_today = cursor.fetchone()
        today_spent = round(float(r_today["t"] or 0.0), 2)

        cursor.execute("SELECT SUM(amount) as t FROM expenses WHERE user_id = ? AND date LIKE ?", (user_id, f"{current_month_str}%"))
        r_month = cursor.fetchone()
        month_spent = round(float(r_month["t"] or 0.0), 2)

        cursor.execute("SELECT SUM(amount) as t FROM expenses WHERE user_id = ? AND date LIKE ?", (user_id, f"{current_year_str}%"))
        r_year = cursor.fetchone()
        year_spent = round(float(r_year["t"] or 0.0), 2)

    return {
        "period": period,
        "total_spent": total_spent,
        "total_count": total_count,
        "today_spent": today_spent,
        "current_month_spent": month_spent,
        "current_year_spent": year_spent,
        "categories": CATEGORIES,
        "category_totals": category_totals,
        "category_counts": category_counts,
        "category_percentages": category_percentages
    }

def get_calendar_data(user_id: int, year: int, month: int, db_path: str = DB_PATH) -> Dict[str, Any]:
    """Returns day-by-day totals, transaction counts, and category indicators for calendar view."""
    month_prefix = f"{year:04d}-{month:02d}%"
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date, category, SUM(amount) as total, COUNT(id) as count
            FROM expenses
            WHERE user_id = ? AND date LIKE ?
            GROUP BY date, category
        """, (user_id, month_prefix))
        rows = cursor.fetchall()

    days_map: Dict[str, Any] = {}
    month_total = 0.0

    for row in rows:
        d = row["date"]
        cat = row["category"]
        tot = float(row["total"] or 0.0)
        cnt = int(row["count"] or 0)
        month_total += tot

        if d not in days_map:
            days_map[d] = {
                "date": d,
                "total": 0.0,
                "count": 0,
                "categories": []
            }
        days_map[d]["total"] = round(days_map[d]["total"] + tot, 2)
        days_map[d]["count"] += cnt
        if cat not in days_map[d]["categories"]:
            days_map[d]["categories"].append(cat)

    return {
        "year": year,
        "month": month,
        "month_total": round(month_total, 2),
        "days": days_map
    }

def get_time_series(user_id: int, period: str = "month", year: Optional[int] = None, month: Optional[int] = None, db_path: str = DB_PATH) -> Dict[str, Any]:
    """Returns aggregated time series data for charts:
    - period='year': 12 months in the year
    - period='month': each day in the month
    - period='all_years': every distinct year
    """
    if not year:
        year = datetime.now().year
    if not month:
        month = datetime.now().month

    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        if period == "year":
            # 12 months
            month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            labels = month_names
            data = [0.0] * 12

            cursor.execute("""
                SELECT strftime('%m', date) as m, SUM(amount) as total
                FROM expenses
                WHERE user_id = ? AND date LIKE ?
                GROUP BY m
            """, (user_id, f"{year:04d}%"))
            for row in cursor.fetchall():
                try:
                    m_idx = int(row["m"]) - 1
                    if 0 <= m_idx < 12:
                        data[m_idx] = round(float(row["total"] or 0.0), 2)
                except (ValueError, TypeError):
                    pass

            return {"period": "year", "year": year, "labels": labels, "data": data, "total": round(sum(data), 2)}

        elif period == "month":
            import calendar
            _, num_days = calendar.monthrange(year, month)
            labels = [f"{d}" for d in range(1, num_days + 1)]
            data = [0.0] * num_days

            prefix = f"{year:04d}-{month:02d}%"
            cursor.execute("""
                SELECT strftime('%d', date) as d, SUM(amount) as total
                FROM expenses
                WHERE user_id = ? AND date LIKE ?
                GROUP BY d
            """, (user_id, prefix))
            for row in cursor.fetchall():
                try:
                    d_idx = int(row["d"]) - 1
                    if 0 <= d_idx < num_days:
                        data[d_idx] = round(float(row["total"] or 0.0), 2)
                except (ValueError, TypeError):
                    pass

            return {"period": "month", "year": year, "month": month, "labels": labels, "data": data, "total": round(sum(data), 2)}

        else: # all_years
            cursor.execute("""
                SELECT strftime('%Y', date) as y, SUM(amount) as total
                FROM expenses
                WHERE user_id = ?
                GROUP BY y
                ORDER BY y ASC
            """, (user_id,))
            rows = cursor.fetchall()
            labels = [row["y"] for row in rows] if rows else [str(year)]
            data = [round(float(row["total"] or 0.0), 2) for row in rows] if rows else [0.0]

            return {"period": "all_years", "labels": labels, "data": data, "total": round(sum(data), 2)}
