# 💸 Expense Tracker

> **Personal Finance & Analytics — Live Demo:** [expences-tracker-3.onrender.com](https://expences-tracker-3.onrender.com)

A full-stack personal expense management web app inspired by a C-based expense management program. Features multi-user isolated storage, a visual expense calendar, category analytics, and dual authentication (Email/Password + Google Sign-In).

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔐 **Multi-User Auth** | Email/password registration & login, plus **Google Sign-In** (Google Identity Services) |
| 📅 **Expense Calendar** | Month-by-month calendar view to visualise daily spending at a glance |
| ➕ **Add Expenses** | Log expenses by amount, description, date, and category |
| 🗂️ **6 Core Categories** | Food · Clothes · Medical · Enjoyment · Fees · Travelling |
| 📊 **Category Distribution** | Pie / doughnut chart showing spend breakdown per category |
| 📈 **Spending Trend** | Line chart of cumulative spending over time |
| 🧾 **Expense History** | Chronological list of all recorded expenses with delete support |
| 🌙 **Dark Theme UI** | Modern dark-mode interface with smooth animations |
| 🔒 **Isolated Storage** | Every user's data is fully separated — no data leakage between accounts |

---

## 🛠️ Tech Stack

### Backend
- **Python 3.13** — pure standard library, zero external dependencies
- **`http.server` / `socketserver`** — lightweight built-in HTTP server
- **SQLite** — embedded relational database via `sqlite3`
- **PBKDF2-HMAC-SHA256** — secure password hashing (`hashlib` + `secrets`)
- **Session tokens** — bearer-token & cookie-based session management
- **Google Identity Services JWT** — server-side decoding for Google OAuth

### Frontend
- **Vanilla HTML5 / CSS3 / JavaScript** — no framework required
- **Chart.js 4.4** — interactive pie and line charts
- **Google Identity Services** — one-tap Google Sign-In
- **Plus Jakarta Sans** — Google Fonts typography

### Deployment
- **Docker** (`python:3.13-slim`) — containerised for consistency
- **Render** — deployed as a Docker web service on the free plan

---

## 📁 Project Structure

```
ExpencesTracker/
├── backend/
│   ├── server.py          # HTTP request handler & REST API routes
│   ├── db.py              # SQLite schema, user auth & expense CRUD
│   └── test_backend.py    # Backend unit tests
├── frontend/
│   ├── index.html         # Single-page application shell
│   ├── app.js             # All client-side logic & API calls
│   └── styles.css         # Dark-theme CSS styles
├── Dockerfile             # Container build instructions
├── render.yaml            # Render deployment configuration
├── docker-compose.yml     # Local Docker Compose setup
├── requirements.txt       # No external packages needed
└── start.bat              # Windows local-run convenience script
```

---

## 🚀 Running Locally

### Option 1 — Plain Python (no Docker)

```bash
# Clone the repo
git clone https://github.com/manikantasai02/Expences-Tracker.git
cd Expences-Tracker

# Start the server (Python 3.13+ required)
python backend/server.py
```

Then open **http://localhost:5000** in your browser.

### Option 2 — Docker Compose

```bash
docker-compose up --build
```

App will be available at **http://localhost:5000**.

### Option 3 — Windows Quick Start

Double-click `start.bat` — it starts the server and opens the browser automatically.

---

## 🗄️ Database

- Uses **SQLite** (`expenses.db`) — no setup required.
- On **Render**, the DB is stored in `/tmp` (writable at runtime).
- Locally, the DB is stored next to `backend/db.py`.

### Schema Overview

```
users      — id, email, name, password_hash, salt, auth_provider, google_sub
sessions   — token, user_id, created_at
expenses   — id, user_id, amount, description, category, date, created_at
```

---

## 🔐 Authentication Flow

```
Email/Password          Google Sign-In
     │                        │
  Register / Login     Google Identity Services
     │                  (JWT decoded server-side)
     └──────────┬────────────┘
                ▼
         Session Token issued
         (Bearer header / Cookie)
                ▼
         All API calls authenticated
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/register` | Create a new account |
| `POST` | `/api/login` | Email/password login |
| `POST` | `/api/google-login` | Google JWT sign-in |
| `POST` | `/api/logout` | Invalidate session |
| `GET`  | `/api/me` | Get current user info |
| `GET`  | `/api/expenses` | List user's expenses |
| `POST` | `/api/expenses` | Add a new expense |
| `DELETE` | `/api/expenses/{id}` | Delete an expense |
| `GET`  | `/api/summary` | Category totals summary |

---

## 🎨 Expense Categories

The 6 categories mirror the original C program:

- 🍔 **Food**
- 👗 **Clothes**
- 💊 **Medical**
- 🎉 **Enjoyment**
- 📚 **Fees**
- ✈️ **Travelling**

---

## ☁️ Deployment on Render

The app is live at **https://expences-tracker-3.onrender.com** and deployed via Docker on Render's free plan.

To deploy your own instance:

1. Fork this repository.
2. Create a new **Web Service** on [render.com](https://render.com).
3. Connect your GitHub repo — Render auto-detects `render.yaml`.
4. Set the environment variable `RENDER=true` (already in `render.yaml`).
5. Deploy! 🚀

> **Note:** Render's free tier spins down after inactivity. The first request after idle may take ~30 seconds to wake up.

---

## 🧪 Running Tests

```bash
python backend/test_backend.py
```

---

## 📄 License

This project is open source. Feel free to fork and customise it for your own expense tracking needs.

---

<p align="center">
  Made with ❤️ | Multi-User Isolated Storage | Powered by Python &amp; SQLite
</p>
