import http.server
import socketserver
import json
import os
import urllib.parse
import base64
from datetime import datetime

try:
    from backend import db
except ImportError:
    import db

PORT = 5000
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

class ExpenseRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def _send_json(self, data, status=200):
        response_bytes = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)

    def _send_error_json(self, message, status=400):
        self._send_json({"error": message, "status": status}, status=status)

    def _read_json_body(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length == 0:
                return {}
            body = self.rfile.read(content_length)
            return json.loads(body.decode("utf-8"))
        except Exception:
            return None

    def _get_auth_token(self):
        auth_header = self.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:].strip()

        # Check cookies
        cookie_header = self.headers.get("Cookie", "")
        for part in cookie_header.split(";"):
            part = part.strip()
            if part.startswith("session="):
                return part[8:].strip()
        return None

    def _get_current_user(self):
        token = self._get_auth_token()
        if not token:
            return None
        return db.get_user_by_session(token)

    def _decode_google_jwt(self, jwt_token: str):
        """Decode payload of Google Identity Services JWT token."""
        try:
            parts = jwt_token.split(".")
            if len(parts) != 3:
                return None
            payload_b64 = parts[1]
            # Add padding
            rem = len(payload_b64) % 4
            if rem > 0:
                payload_b64 += "=" * (4 - rem)
            decoded_bytes = base64.urlsafe_b64decode(payload_b64)
            return json.loads(decoded_bytes.decode("utf-8"))
        except Exception:
            return None

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        # Public endpoints
        if path == "/api/categories":
            self._send_json({"categories": db.CATEGORIES})
            return

        # Auth endpoint: Check current user
        if path == "/api/auth/me":
            user = self._get_current_user()
            if not user:
                self._send_error_json("Unauthorized", 401)
                return
            self._send_json({"user": user})
            return

        # Protected API Routes below require login
        if path.startswith("/api/"):
            user = self._get_current_user()
            if not user:
                self._send_error_json("Authentication required. Please log in.", 401)
                return

            user_id = user["id"]

            if path == "/api/expenses":
                category = query.get("category", [None])[0]
                search = query.get("search", [None])[0]
                date = query.get("date", [None])[0]
                year = int(query.get("year", [0])[0]) or None
                month = int(query.get("month", [0])[0]) or None

                try:
                    expenses = db.get_expenses(
                        user_id=user_id,
                        category=category,
                        search=search,
                        date=date,
                        year=year,
                        month=month
                    )
                    self._send_json({"expenses": expenses, "count": len(expenses)})
                except Exception as e:
                    self._send_error_json(str(e), 500)
                return

            elif path == "/api/summary":
                period = query.get("period", ["all"])[0]
                year = int(query.get("year", [0])[0]) or None
                month = int(query.get("month", [0])[0]) or None
                date = query.get("date", [None])[0]

                try:
                    summary = db.get_summary(user_id=user_id, period=period, year=year, month=month, date=date)
                    self._send_json(summary)
                except Exception as e:
                    self._send_error_json(str(e), 500)
                return

            elif path == "/api/analytics/calendar":
                year = int(query.get("year", [datetime.now().year])[0])
                month = int(query.get("month", [datetime.now().month])[0])
                try:
                    calendar_data = db.get_calendar_data(user_id=user_id, year=year, month=month)
                    self._send_json(calendar_data)
                except Exception as e:
                    self._send_error_json(str(e), 500)
                return

            elif path == "/api/analytics/timeseries":
                period = query.get("period", ["month"])[0]
                year = int(query.get("year", [datetime.now().year])[0])
                month = int(query.get("month", [datetime.now().month])[0])
                try:
                    ts_data = db.get_time_series(user_id=user_id, period=period, year=year, month=month)
                    self._send_json(ts_data)
                except Exception as e:
                    self._send_error_json(str(e), 500)
                return

            self._send_error_json("API endpoint not found", 404)
            return

        # Serve static frontend files
        if path == "/" or path == "":
            filepath = os.path.join(FRONTEND_DIR, "index.html")
        else:
            safe_rel_path = path.lstrip("/").replace("/", os.sep)
            filepath = os.path.join(FRONTEND_DIR, safe_rel_path)

        if os.path.isfile(filepath):
            ext = os.path.splitext(filepath)[1].lower()
            mime_types = {
                ".html": "text/html; charset=utf-8",
                ".css": "text/css; charset=utf-8",
                ".js": "application/javascript; charset=utf-8",
                ".json": "application/json; charset=utf-8",
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".svg": "image/svg+xml",
                ".ico": "image/x-icon",
            }
            content_type = mime_types.get(ext, "application/octet-stream")

            try:
                with open(filepath, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            except Exception as e:
                self._send_error_json(f"File read error: {e}", 500)
            return

        self._send_error_json(f"Path '{path}' not found", 404)

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        # -------------------------------------------------------------
        # Public Auth Routes
        # -------------------------------------------------------------
        if path == "/api/auth/signup":
            data = self._read_json_body()
            if not data:
                self._send_error_json("Invalid JSON request", 400)
                return
            email = data.get("email", "")
            name = data.get("name", "")
            password = data.get("password", "")

            try:
                user = db.create_user(email=email, name=name, password=password)
                token = db.create_session(user["id"])
                self._send_json({"success": True, "user": user, "token": token}, status=201)
            except ValueError as ve:
                self._send_error_json(str(ve), 400)
            except Exception as e:
                self._send_error_json(str(e), 500)
            return

        elif path == "/api/auth/login":
            data = self._read_json_body()
            if not data:
                self._send_error_json("Invalid JSON request", 400)
                return
            email = data.get("email", "")
            password = data.get("password", "")

            user = db.authenticate_user(email=email, password=password)
            if not user:
                self._send_error_json("Invalid email or password", 401)
                return

            token = db.create_session(user["id"])
            self._send_json({"success": True, "user": user, "token": token})
            return

        elif path == "/api/auth/google":
            data = self._read_json_body()
            if not data:
                self._send_error_json("Invalid JSON request", 400)
                return

            credential = data.get("credential")
            email = data.get("email")
            name = data.get("name")
            sub = data.get("google_sub")

            # If Google credential JWT is passed, decode it
            if credential:
                payload = self._decode_google_jwt(credential)
                if payload:
                    email = payload.get("email")
                    name = payload.get("name")
                    sub = payload.get("sub")

            if not email:
                self._send_error_json("Google authentication failed: email not found.", 400)
                return

            try:
                user = db.create_or_get_google_user(email=email, name=name or email.split("@")[0], google_sub=sub)
                token = db.create_session(user["id"])
                self._send_json({"success": True, "user": user, "token": token})
            except Exception as e:
                self._send_error_json(str(e), 500)
            return

        elif path == "/api/auth/logout":
            token = self._get_auth_token()
            if token:
                db.delete_session(token)
            self._send_json({"success": True, "message": "Logged out successfully"})
            return

        # -------------------------------------------------------------
        # Protected Routes (Require Login)
        # -------------------------------------------------------------
        user = self._get_current_user()
        if not user:
            self._send_error_json("Authentication required. Please log in.", 401)
            return

        user_id = user["id"]

        if path == "/api/expenses":
            data = self._read_json_body()
            if not data:
                self._send_error_json("Invalid JSON body", 400)
                return

            amount = data.get("amount")
            category = data.get("category")
            note = data.get("note", "")
            date = data.get("date", datetime.now().strftime("%Y-%m-%d"))

            if amount is None or category is None:
                self._send_error_json("Both 'amount' and 'category' are required.", 400)
                return

            try:
                amount_num = float(amount)
                if amount_num <= 0:
                    self._send_error_json("Amount must be a positive number.", 400)
                    return
                expense = db.add_expense(
                    user_id=user_id,
                    amount=amount_num,
                    category=str(category),
                    note=str(note),
                    date=str(date)
                )
                self._send_json({"success": True, "expense": expense}, status=201)
            except ValueError as ve:
                self._send_error_json(str(ve), 400)
            except Exception as e:
                self._send_error_json(str(e), 500)
            return

        elif path == "/api/clear":
            try:
                db.clear_all(user_id=user_id)
                self._send_json({"success": True, "message": "All your expenses have been cleared."})
            except Exception as e:
                self._send_error_json(str(e), 500)
            return

        self._send_error_json("Endpoint not found", 404)

    def do_DELETE(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        user = self._get_current_user()
        if not user:
            self._send_error_json("Authentication required. Please log in.", 401)
            return

        user_id = user["id"]

        if path.startswith("/api/expenses/"):
            expense_id_str = path[len("/api/expenses/"):]
            try:
                expense_id = int(expense_id_str)
                deleted = db.delete_expense(user_id=user_id, expense_id=expense_id)
                if deleted:
                    self._send_json({"success": True, "deleted_id": expense_id})
                else:
                    self._send_error_json(f"Expense ID {expense_id} not found or unauthorized", 404)
            except ValueError:
                self._send_error_json("Invalid expense ID format", 400)
            except Exception as e:
                self._send_error_json(str(e), 500)
            return

        self._send_error_json("Endpoint not found", 404)


def run_server(port=PORT):
    db.init_db()
    server_address = ("", port)
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer(server_address, ExpenseRequestHandler) as httpd:
        print(f"==================================================")
        print(f" Expense Tracker Server running on:")
        print(f" -> http://localhost:{port}")
        print(f" Serving frontend from: {FRONTEND_DIR}")
        print(f" Press Ctrl+C to stop the server.")
        print(f"==================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server gracefully...")
            httpd.server_close()

if __name__ == "__main__":
    import sys
    custom_port = int(os.environ.get("PORT", PORT))
    if len(sys.argv) > 1:
        try:
            custom_port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(custom_port)
