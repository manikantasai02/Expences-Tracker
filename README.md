# 💰 Expense Tracker Web Application

A modern, full-stack expense tracking web application based on the 6 core categories from the original C console program:
1. **Food** (🍔)
2. **Cloths** (👕)
3. **Medical** (💊)
4. **Enjoyment** (🎟️)
5. **Fees** (🎓)
6. **Travelling** (✈️)

---

## 🚀 Quick Start (One-Click Launch)

### Option 1: Double-click launcher (Windows)
Double-click `start.bat` in the project root. It will:
1. Start the local backend server.
2. Automatically open your default web browser to [http://localhost:5000](http://localhost:5000).

### Option 2: Command Line
Open a terminal in this directory and run:
```bash
py backend/server.py
```
Then visit [http://localhost:5000](http://localhost:5000) in your browser.

---

## 📂 Project Structure

```
ExpencesTracker/
├── backend/
│   ├── db.py               # SQLite database access layer (CRUD & analytics)
│   ├── server.py           # Python HTTP server & REST API
│   ├── test_backend.py     # Unit and integration test suite
│   └── expenses.db         # Persistent SQLite database (auto-generated)
├── frontend/
│   ├── index.html          # Responsive HTML5 dashboard UI
│   ├── styles.css          # Modern dark/light theme CSS styling
│   └── app.js              # Interactive client application & Chart.js logic
├── main.c                  # Original C console application
├── main.exe                # Compiled C executable
├── start.bat               # One-click Windows launcher
└── README.md               # Documentation
```

---

## ✨ Features

- **6 Core Categories**: Directly implements and expands the 6 categories from `main.c` with custom color codes and icons.
- **Persistent Storage**: All entries are stored safely in a local SQLite database (`expenses.db`), surviving server restarts.
- **Dashboard Analytics**: Real-time spending breakdown donut chart (Chart.js) and progress bars for each category.
- **Smart Filtering & Search**: Instant real-time search across notes and instant filtering by category.
- **Multiple Currencies**: Toggle between ₹ (INR), $ (USD), € (EUR), and £ (GBP).
- **Dark & Light Mode**: Seamless theme switching with saved user preference.
- **Zero External Dependencies**: Powered completely by Python 3.13 standard library (`http.server`, `sqlite3`, `json`) — no npm or pip installations required.

---

## 🔌 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/expenses` | Retrieve all expenses (supports `?category=...&search=...`) |
| `POST` | `/api/expenses` | Add a new expense (`amount`, `category`, `note`, `date`) |
| `DELETE` | `/api/expenses/<id>` | Delete an expense by ID |
| `GET` | `/api/summary` | Get total spending, transaction count, and category percentages |
| `GET` | `/api/categories` | List the 6 supported categories |
| `POST` | `/api/clear` | Clear all expense records |

---

## 🧪 Testing

To run the automated test suite:
```bash
py backend/test_backend.py
```

---

## 🚢 Deployment Guide

### 1. 🌐 Live Public Cloud Deployment (Active Now)
Your application is currently deployed and accessible globally over the public internet:
👉 **[https://knowledge-vendors-covers-hughes.trycloudflare.com](https://knowledge-vendors-covers-hughes.trycloudflare.com)**

- **SSL/HTTPS**: Enabled & secured with Cloudflare TLS
- **Global Access**: Accessible from any phone, laptop, or browser anywhere
- **Launcher**: You can restart the public tunnel at any time by running:
  ```powershell
  py deploy_live.py
  ```

### 2. 💻 Local Deployment
The application is also accessible locally on:
👉 **[http://localhost:5000](http://localhost:5000)**

To run silently in the background without a CMD window:
- Double-click [`run_background.vbs`](file:///c:/OneDrive/Documents/sai/ExpencesTracker/run_background.vbs).

### 3. Docker Deployment
A [`Dockerfile`](file:///c:/OneDrive/Documents/sai/ExpencesTracker/Dockerfile) and [`docker-compose.yml`](file:///c:/OneDrive/Documents/sai/ExpencesTracker/docker-compose.yml) are provided.

To build and run in Docker:
```bash
docker compose up -d --build
```
Your app will be live at `http://localhost:5000` with data persisted in a named Docker volume.

### 3. Cloud Deployment (Render / Railway / Cloud Run)
The repository includes a [`Procfile`](file:///c:/OneDrive/Documents/sai/ExpencesTracker/Procfile) and [`requirements.txt`](file:///c:/OneDrive/Documents/sai/ExpencesTracker/requirements.txt).

**Deploying to Render (Free Web Service):**
1. Push this project to GitHub.
2. Go to [Render.com](https://render.com) and create a new **Web Service**.
3. Select your repository.
4. Set:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python backend/server.py $PORT`
5. Click **Deploy**. Your app will be live on a public `.onrender.com` URL!
