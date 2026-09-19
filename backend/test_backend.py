import os
import unittest
import tempfile
import threading
import urllib.request
import urllib.error
import json
import socketserver

import db
from server import ExpenseRequestHandler

class TestExpenseTrackerAuthAndIsolation(unittest.TestCase):
    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.temp_db_fd)
        db.init_db(self.temp_db_path)

    def tearDown(self):
        if os.path.exists(self.temp_db_path):
            try:
                os.remove(self.temp_db_path)
            except OSError:
                pass

    def test_user_signup_and_auth(self):
        # Create user
        user = db.create_user("alice@test.com", "Alice", "secret123", db_path=self.temp_db_path)
        self.assertEqual(user["email"], "alice@test.com")
        self.assertEqual(user["name"], "Alice")

        # Duplicate email should fail
        with self.assertRaises(ValueError):
            db.create_user("alice@test.com", "Alice 2", "secret123", db_path=self.temp_db_path)

        # Authenticate success
        auth_user = db.authenticate_user("alice@test.com", "secret123", db_path=self.temp_db_path)
        self.assertIsNotNone(auth_user)
        self.assertEqual(auth_user["id"], user["id"])

        # Authenticate failure (wrong password)
        bad_auth = db.authenticate_user("alice@test.com", "wrongpass", db_path=self.temp_db_path)
        self.assertIsNone(bad_auth)

        # Session lifecycle
        token = db.create_session(user["id"], db_path=self.temp_db_path)
        session_user = db.get_user_by_session(token, db_path=self.temp_db_path)
        self.assertIsNotNone(session_user)
        self.assertEqual(session_user["id"], user["id"])

        # Delete session
        self.assertTrue(db.delete_session(token, db_path=self.temp_db_path))
        self.assertIsNone(db.get_user_by_session(token, db_path=self.temp_db_path))

    def test_user_expense_isolation(self):
        user_a = db.create_user("a@test.com", "User A", "pass123", db_path=self.temp_db_path)
        user_b = db.create_user("b@test.com", "User B", "pass123", db_path=self.temp_db_path)

        # User A adds expense
        exp_a = db.add_expense(user_a["id"], 100.0, "Food", "Dinner", date="2026-09-19", db_path=self.temp_db_path)
        # User B adds expense
        exp_b = db.add_expense(user_b["id"], 50.0, "Travelling", "Bus ticket", date="2026-09-19", db_path=self.temp_db_path)

        # Verify User A only sees their own expenses
        expenses_a = db.get_expenses(user_a["id"], db_path=self.temp_db_path)
        self.assertEqual(len(expenses_a), 1)
        self.assertEqual(expenses_a[0]["id"], exp_a["id"])

        # Verify User B only sees their own expenses
        expenses_b = db.get_expenses(user_b["id"], db_path=self.temp_db_path)
        self.assertEqual(len(expenses_b), 1)
        self.assertEqual(expenses_b[0]["id"], exp_b["id"])

        # User A cannot delete User B's expense
        deleted = db.delete_expense(user_a["id"], exp_b["id"], db_path=self.temp_db_path)
        self.assertFalse(deleted)
        self.assertEqual(len(db.get_expenses(user_b["id"], db_path=self.temp_db_path)), 1)

    def test_calendar_and_time_analytics(self):
        user = db.create_user("charlie@test.com", "Charlie", "pass123", db_path=self.temp_db_path)
        uid = user["id"]

        db.add_expense(uid, 50.0, "Food", "Breakfast", date="2026-09-10", db_path=self.temp_db_path)
        db.add_expense(uid, 75.0, "Medical", "Clinic", date="2026-09-10", db_path=self.temp_db_path)
        db.add_expense(uid, 120.0, "Travelling", "Taxi", date="2026-09-15", db_path=self.temp_db_path)
        db.add_expense(uid, 300.0, "Fees", "Exam", date="2026-08-01", db_path=self.temp_db_path)

        # Calendar data for 2026-09
        cal = db.get_calendar_data(uid, 2026, 9, db_path=self.temp_db_path)
        self.assertEqual(cal["month_total"], 245.0)
        self.assertIn("2026-09-10", cal["days"])
        self.assertEqual(cal["days"]["2026-09-10"]["total"], 125.0)
        self.assertEqual(cal["days"]["2026-09-10"]["count"], 2)

        # Time series for month
        ts_month = db.get_time_series(uid, period="month", year=2026, month=9, db_path=self.temp_db_path)
        self.assertEqual(ts_month["total"], 245.0)

        # Time series for year
        ts_year = db.get_time_series(uid, period="year", year=2026, db_path=self.temp_db_path)
        self.assertEqual(ts_year["total"], 545.0)


class TestAPIIntegrationWithAuth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server_port = 5056
        socketserver.TCPServer.allow_reuse_address = True
        cls.httpd = socketserver.TCPServer(("127.0.0.1", cls.server_port), ExpenseRequestHandler)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever)
        cls.thread.daemon = True
        cls.thread.start()
        db.init_db()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def test_auth_api_workflow(self):
        base_url = f"http://127.0.0.1:{self.server_port}"

        # 1. Unauthenticated request to /api/expenses should return 401
        try:
            req = urllib.request.Request(f"{base_url}/api/expenses")
            urllib.request.urlopen(req)
            self.fail("Expected HTTP 401 Unauthorized")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 401)

        # 2. Signup new user
        import secrets
        unique_email = f"test_{secrets.token_hex(4)}@example.com"
        signup_payload = json.dumps({
            "email": unique_email,
            "name": "Test User",
            "password": "password123"
        }).encode("utf-8")

        signup_req = urllib.request.Request(
            f"{base_url}/api/auth/signup",
            data=signup_payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(signup_req) as resp:
            self.assertEqual(resp.status, 201)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data["success"])
            token = data["token"]
            self.assertTrue(token)

        # 3. Add expense with Bearer token
        exp_payload = json.dumps({
            "amount": 85.0,
            "category": "Food",
            "note": "Dinner with family",
            "date": "2026-09-19"
        }).encode("utf-8")

        exp_req = urllib.request.Request(
            f"{base_url}/api/expenses",
            data=exp_payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
        )
        with urllib.request.urlopen(exp_req) as resp:
            self.assertEqual(resp.status, 201)
            exp_data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(exp_data["expense"]["amount"], 85.0)

        # 4. Fetch summary with Bearer token
        sum_req = urllib.request.Request(
            f"{base_url}/api/summary",
            headers={"Authorization": f"Bearer {token}"}
        )
        with urllib.request.urlopen(sum_req) as resp:
            self.assertEqual(resp.status, 200)
            sum_data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(sum_data["total_spent"], 85.0)
            self.assertEqual(sum_data["category_totals"]["Food"], 85.0)

if __name__ == "__main__":
    unittest.main()
