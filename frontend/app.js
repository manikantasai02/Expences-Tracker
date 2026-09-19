/**
 * Expense Tracker Web Application
 * Full-featured Frontend: Multi-User Auth, Expense Isolation, Interactive Calendar,
 * Day/Month/Year Analytics, and Chart.js Visualizations.
 */

const API_BASE = "";

const CATEGORY_META = {
  Food: { index: 1, icon: "🍔", color: "#f97316", tagClass: "tag-food", pillClass: "pill-food" },
  Cloths: { index: 2, icon: "👕", color: "#6366f1", tagClass: "tag-cloths", pillClass: "pill-cloths" },
  Medical: { index: 3, icon: "💊", color: "#10b981", tagClass: "tag-medical", pillClass: "pill-medical" },
  Enjoyment: { index: 4, icon: "🎟️", color: "#ec4899", tagClass: "tag-enjoyment", pillClass: "pill-enjoyment" },
  Fees: { index: 5, icon: "🎓", color: "#f59e0b", tagClass: "tag-fees", pillClass: "pill-fees" },
  Travelling: { index: 6, icon: "✈️", color: "#06b6d4", tagClass: "tag-travelling", pillClass: "pill-travelling" },
};

const MONTH_NAMES = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December"
];

// App State
let authToken = localStorage.getItem("expense_auth_token") || null;
let currentUser = null;
let currentCurrency = "₹";

// Calendar & Filter State
const now = new Date();
let calYear = now.getFullYear();
let calMonth = now.getMonth() + 1; // 1-12
let selectedDate = null; // YYYY-MM-DD or null
let currentPeriod = "all"; // 'all', 'year', 'month', 'day'
let currentTrendType = "month"; // 'month' (daily in month) or 'year' (monthly in year)

// Chart Instances
let categoryChart = null;
let trendChart = null;

// DOM Elements
const authModal = document.getElementById("authModal");
const authForm = document.getElementById("authForm");
const authName = document.getElementById("authName");
const authEmail = document.getElementById("authEmail");
const authPassword = document.getElementById("authPassword");
const authSubmitBtn = document.getElementById("authSubmitBtn");
const signupNameGroup = document.getElementById("signupNameGroup");
const tabLoginBtn = document.getElementById("tabLoginBtn");
const tabSignupBtn = document.getElementById("tabSignupBtn");
const googleSignInBtn = document.getElementById("googleSignInBtn");
const demoLoginBtn = document.getElementById("demoLoginBtn");

const userProfileCapsule = document.getElementById("userProfileCapsule");
const userAvatar = document.getElementById("userAvatar");
const userDisplayName = document.getElementById("userDisplayName");
const userDisplayEmail = document.getElementById("userDisplayEmail");
const logoutBtn = document.getElementById("logoutBtn");

const currencySelect = document.getElementById("currencySelect");
const inputCurrencySymbol = document.getElementById("inputCurrencySymbol");
const themeToggle = document.getElementById("themeToggle");
const toastContainer = document.getElementById("toastContainer");

// Stats & Views
const totalSpentDisplay = document.getElementById("totalSpentDisplay");
const totalTransactionsCount = document.getElementById("totalTransactionsCount");
const todaySpentDisplay = document.getElementById("todaySpentDisplay");
const monthSpentDisplay = document.getElementById("monthSpentDisplay");
const yearSpentDisplay = document.getElementById("yearSpentDisplay");
const viewPeriodBadge = document.getElementById("viewPeriodBadge");
const todayDateLabel = document.getElementById("todayDateLabel");
const monthNameLabel = document.getElementById("monthNameLabel");
const yearNameLabel = document.getElementById("yearNameLabel");

// Time Filter Controls
const currentPeriodLabel = document.getElementById("currentPeriodLabel");
const prevPeriodBtn = document.getElementById("prevPeriodBtn");
const nextPeriodBtn = document.getElementById("nextPeriodBtn");
const todayNavBtn = document.getElementById("todayNavBtn");

// Calendar Elements
const calendarGrid = document.getElementById("calendarGrid");
const calendarMonthTitle = document.getElementById("calendarMonthTitle");
const calendarMonthTotal = document.getElementById("calendarMonthTotal");
const calPrevMonthBtn = document.getElementById("calPrevMonthBtn");
const calNextMonthBtn = document.getElementById("calNextMonthBtn");
const calTodayBtn = document.getElementById("calTodayBtn");
const calendarSelectedInfo = document.getElementById("calendarSelectedInfo");
const resetDayFilterBtn = document.getElementById("resetDayFilterBtn");

// Form Elements
const expenseForm = document.getElementById("expenseForm");
const expenseAmount = document.getElementById("expenseAmount");
const expenseNote = document.getElementById("expenseNote");
const expenseDate = document.getElementById("expenseDate");
const submitExpenseBtn = document.getElementById("submitExpenseBtn");

// Breakdown & History
const categoryCardsGrid = document.getElementById("categoryCardsGrid");
const expensesTableBody = document.getElementById("expensesTableBody");
const emptyTableState = document.getElementById("emptyTableState");
const emptyChartMessage = document.getElementById("emptyChartMessage");
const emptyTrendMessage = document.getElementById("emptyTrendMessage");
const categoryFilter = document.getElementById("categoryFilter");
const searchInput = document.getElementById("searchInput");
const clearAllBtn = document.getElementById("clearAllBtn");
const activeFilterTag = document.getElementById("activeFilterTag");
const chartPeriodTag = document.getElementById("chartPeriodTag");

// Trend Buttons
const trendMonthBtn = document.getElementById("trendMonthBtn");
const trendYearBtn = document.getElementById("trendYearBtn");
const trendChartTitle = document.getElementById("trendChartTitle");

// =============================================================================
// App Initialization
// =============================================================================
document.addEventListener("DOMContentLoaded", async () => {
  initTheme();
  setupEventListeners();

  // Set default date picker to today
  const todayStr = formatIsoDate(new Date());
  expenseDate.value = todayStr;
  todayDateLabel.textContent = formatDate(todayStr);
  monthNameLabel.textContent = `${MONTH_NAMES[now.getMonth()]} ${now.getFullYear()}`;
  yearNameLabel.textContent = `Year ${now.getFullYear()}`;

  // Check auth
  await checkAuthStatus();
});

function setupEventListeners() {
  // Auth Tab Toggles
  tabLoginBtn.addEventListener("click", () => setAuthTab("login"));
  tabSignupBtn.addEventListener("click", () => setAuthTab("signup"));
  authForm.addEventListener("submit", handleAuthSubmit);
  googleSignInBtn.addEventListener("click", handleGoogleSignIn);
  demoLoginBtn.addEventListener("click", handleDemoLogin);
  logoutBtn.addEventListener("click", handleLogout);

  // Currency
  currencySelect.addEventListener("change", (e) => {
    currentCurrency = e.target.value;
    inputCurrencySymbol.textContent = currentCurrency;
    refreshAllData();
  });

  // Theme
  themeToggle.addEventListener("click", toggleTheme);

  // Time Period Tabs
  document.querySelectorAll(".time-tab-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      document.querySelectorAll(".time-tab-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      currentPeriod = btn.dataset.period;
      selectedDate = null; // reset day filter when changing tab
      resetDayFilterBtn.classList.add("hidden");
      updatePeriodLabel();
      refreshAllData();
    });
  });

  // Period Navigator Buttons
  prevPeriodBtn.addEventListener("click", () => navigatePeriod(-1));
  nextPeriodBtn.addEventListener("click", () => navigatePeriod(1));
  todayNavBtn.addEventListener("click", () => {
    const today = new Date();
    calYear = today.getFullYear();
    calMonth = today.getMonth() + 1;
    selectedDate = formatIsoDate(today);
    updatePeriodLabel();
    refreshAllData();
  });

  // Calendar Month Navigation
  calPrevMonthBtn.addEventListener("click", () => {
    calMonth--;
    if (calMonth < 1) { calMonth = 12; calYear--; }
    loadCalendar();
  });
  calNextMonthBtn.addEventListener("click", () => {
    calMonth++;
    if (calMonth > 12) { calMonth = 1; calYear++; }
    loadCalendar();
  });
  calTodayBtn.addEventListener("click", () => {
    const t = new Date();
    calYear = t.getFullYear();
    calMonth = t.getMonth() + 1;
    selectedDate = formatIsoDate(t);
    loadCalendar();
    loadExpenses();
  });
  resetDayFilterBtn.addEventListener("click", () => {
    selectedDate = null;
    resetDayFilterBtn.classList.add("hidden");
    calendarSelectedInfo.textContent = "Click any day to view its specific transactions";
    activeFilterTag.classList.add("hidden");
    loadCalendar();
    loadExpenses();
    loadSummary();
  });

  // Trend Tab Toggles
  trendMonthBtn.addEventListener("click", () => {
    trendMonthBtn.classList.add("active");
    trendYearBtn.classList.remove("active");
    currentTrendType = "month";
    loadTrendChart();
  });
  trendYearBtn.addEventListener("click", () => {
    trendYearBtn.classList.add("active");
    trendMonthBtn.classList.remove("active");
    currentTrendType = "year";
    loadTrendChart();
  });

  // Expense Form
  expenseForm.addEventListener("submit", handleAddExpense);

  // Filtering & Search
  categoryFilter.addEventListener("change", loadExpenses);
  searchInput.addEventListener("input", debounce(loadExpenses, 250));
  clearAllBtn.addEventListener("click", handleClearAll);
}

// =============================================================================
// Authentication System
// =============================================================================
async function checkAuthStatus() {
  if (!authToken) {
    showAuthModal();
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/auth/me`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    if (!res.ok) throw new Error("Session expired");

    const data = await res.json();
    currentUser = data.user;
    updateUserProfileUI();
    hideAuthModal();
    updatePeriodLabel();
    refreshAllData();
  } catch (err) {
    authToken = null;
    currentUser = null;
    localStorage.removeItem("expense_auth_token");
    showAuthModal();
  }
}

function showAuthModal() {
  authModal.classList.remove("hidden");
}

function hideAuthModal() {
  authModal.classList.add("hidden");
}

function setAuthTab(tab) {
  if (tab === "signup") {
    tabSignupBtn.classList.add("active");
    tabLoginBtn.classList.remove("active");
    signupNameGroup.style.display = "flex";
    authSubmitBtn.textContent = "Create Account";
  } else {
    tabLoginBtn.classList.add("active");
    tabSignupBtn.classList.remove("active");
    signupNameGroup.style.display = "none";
    authSubmitBtn.textContent = "Sign In";
  }
}

async function handleAuthSubmit(e) {
  e.preventDefault();
  const isSignup = tabSignupBtn.classList.contains("active");
  const email = authEmail.value.trim();
  const password = authPassword.value;
  const name = authName.value.trim();

  if (!email || !password) {
    showToast("Please fill in all required fields.", "error");
    return;
  }
  if (isSignup && !name) {
    showToast("Please enter your name.", "error");
    return;
  }

  authSubmitBtn.disabled = true;
  const endpoint = isSignup ? "/api/auth/signup" : "/api/auth/login";
  const payload = isSignup ? { email, password, name } : { email, password };

  try {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Authentication failed");

    authToken = data.token;
    currentUser = data.user;
    localStorage.setItem("expense_auth_token", authToken);

    showToast(`Welcome back, ${currentUser.name}!`, "success");
    updateUserProfileUI();
    hideAuthModal();
    updatePeriodLabel();
    refreshAllData();
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    authSubmitBtn.disabled = false;
  }
}

/**
 * Handle Google Sign-In with fallback prompt
 */
async function handleGoogleSignIn() {
  // Prompt user for their name/email or simulate Google OAuth profile
  const defaultEmail = currentUser ? currentUser.email : "user@gmail.com";
  const googleEmail = prompt("Enter your Google Account email:", defaultEmail);
  if (!googleEmail) return;

  const googleName = prompt("Enter your Display Name:", googleEmail.split("@")[0]) || "Google User";

  try {
    const res = await fetch(`${API_BASE}/api/auth/google`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: googleEmail,
        name: googleName,
        google_sub: "g_" + Math.random().toString(36).substring(2, 10),
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Google sign-in failed");

    authToken = data.token;
    currentUser = data.user;
    localStorage.setItem("expense_auth_token", authToken);

    showToast(`Signed in with Google as ${currentUser.name}!`, "success");
    updateUserProfileUI();
    hideAuthModal();
    updatePeriodLabel();
    refreshAllData();
  } catch (err) {
    showToast(err.message, "error");
  }
}

/**
 * 1-Click Demo / Guest login
 */
async function handleDemoLogin() {
  try {
    const res = await fetch(`${API_BASE}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: "demo@example.com", password: "demo123" }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Demo login failed");

    authToken = data.token;
    currentUser = data.user;
    localStorage.setItem("expense_auth_token", authToken);

    showToast("Logged in as Demo User!", "success");
    updateUserProfileUI();
    hideAuthModal();
    updatePeriodLabel();
    refreshAllData();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function handleLogout() {
  if (confirm("Are you sure you want to log out?")) {
    try {
      if (authToken) {
        await fetch(`${API_BASE}/api/auth/logout`, {
          method: "POST",
          headers: { Authorization: `Bearer ${authToken}` },
        });
      }
    } catch {}

    authToken = null;
    currentUser = null;
    localStorage.removeItem("expense_auth_token");
    showToast("Logged out successfully.", "success");
    showAuthModal();
  }
}

function updateUserProfileUI() {
  if (!currentUser) return;
  const initial = (currentUser.name || currentUser.email || "U").charAt(0).toUpperCase();
  userAvatar.textContent = initial;
  userDisplayName.textContent = currentUser.name;
  userDisplayEmail.textContent = currentUser.email;
}

// =============================================================================
// Period Navigation Helpers
// =============================================================================
function navigatePeriod(delta) {
  if (currentPeriod === "month") {
    calMonth += delta;
    if (calMonth < 1) { calMonth = 12; calYear--; }
    else if (calMonth > 12) { calMonth = 1; calYear++; }
  } else if (currentPeriod === "year") {
    calYear += delta;
  } else if (currentPeriod === "day") {
    let d = selectedDate ? new Date(selectedDate) : new Date();
    d.setDate(d.getDate() + delta);
    selectedDate = formatIsoDate(d);
    calYear = d.getFullYear();
    calMonth = d.getMonth() + 1;
  }
  updatePeriodLabel();
  refreshAllData();
}

function updatePeriodLabel() {
  if (currentPeriod === "all") {
    currentPeriodLabel.textContent = "All Time";
    viewPeriodBadge.textContent = "All Time";
  } else if (currentPeriod === "year") {
    currentPeriodLabel.textContent = `Year ${calYear}`;
    viewPeriodBadge.textContent = `Year ${calYear}`;
  } else if (currentPeriod === "month") {
    currentPeriodLabel.textContent = `${MONTH_NAMES[calMonth - 1]} ${calYear}`;
    viewPeriodBadge.textContent = `${MONTH_NAMES[calMonth - 1]} ${calYear}`;
  } else if (currentPeriod === "day") {
    const curDate = selectedDate || formatIsoDate(new Date());
    currentPeriodLabel.textContent = formatDate(curDate);
    viewPeriodBadge.textContent = `Day: ${formatDate(curDate)}`;
  }
}

// =============================================================================
// Refresh All Data (Summary, Expenses, Calendar, Trends)
// =============================================================================
async function refreshAllData() {
  if (!authToken) return;
  await Promise.all([
    loadSummary(),
    loadExpenses(),
    loadCalendar(),
    loadTrendChart()
  ]);
}

// =============================================================================
// Summary & Category Breakdown Cards
// =============================================================================
async function loadSummary() {
  try {
    const params = new URLSearchParams();
    params.append("period", currentPeriod);
    if (currentPeriod === "year") params.append("year", calYear);
    if (currentPeriod === "month") {
      params.append("year", calYear);
      params.append("month", calMonth);
    }
    if (currentPeriod === "day" || selectedDate) {
      params.append("period", "day");
      params.append("date", selectedDate || formatIsoDate(new Date()));
    }

    const res = await fetch(`${API_BASE}/api/summary?${params.toString()}`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    if (!res.ok) throw new Error("Failed to load summary");

    const data = await res.json();

    // Top Stats
    totalSpentDisplay.textContent = formatCurrency(data.total_spent);
    totalTransactionsCount.textContent = data.total_count;
    todaySpentDisplay.textContent = formatCurrency(data.today_spent);
    monthSpentDisplay.textContent = formatCurrency(data.current_month_spent);
    yearSpentDisplay.textContent = formatCurrency(data.current_year_spent);

    chartPeriodTag.textContent = currentPeriodLabel.textContent;

    // Render 6 Category Cards
    renderCategoryCards(data);

    // Render Donut Chart
    renderCategoryChart(data);

  } catch (err) {
    console.error("Summary error:", err);
  }
}

function renderCategoryCards(summary) {
  categoryCardsGrid.innerHTML = "";
  const categories = Object.keys(CATEGORY_META);

  categories.forEach((cat) => {
    const meta = CATEGORY_META[cat];
    const total = summary.category_totals[cat] || 0;
    const count = summary.category_counts[cat] || 0;
    const percentage = summary.category_percentages[cat] || 0;

    const card = document.createElement("div");
    card.className = "cat-breakdown-card";
    card.style.borderTop = `3px solid ${meta.color}`;

    card.innerHTML = `
      <div class="cat-card-header">
        <div class="cat-card-title">
          <span>${meta.icon}</span>
          <span>${cat}</span>
        </div>
        <span class="cat-index-badge">#${meta.index}</span>
      </div>
      <div class="cat-card-amount" style="color: ${meta.color}">
        ${formatCurrency(total)}
      </div>
      <div class="progress-track">
        <div class="progress-fill" style="width: ${percentage}%; background-color: ${meta.color};"></div>
      </div>
      <div class="cat-card-footer">
        <span>${count} ${count === 1 ? 'entry' : 'entries'}</span>
        <span><strong>${percentage}%</strong></span>
      </div>
    `;

    card.style.cursor = "pointer";
    card.title = `Click to quick-select ${cat} in form`;
    card.addEventListener("click", () => {
      const radio = document.querySelector(`input[name="category"][value="${cat}"]`);
      if (radio) {
        radio.checked = true;
        expenseAmount.focus();
        showToast(`Selected ${meta.icon} ${cat}`, "success");
      }
    });

    categoryCardsGrid.appendChild(card);
  });
}

// =============================================================================
// Interactive Calendar Component
// =============================================================================
async function loadCalendar() {
  calendarMonthTitle.textContent = `${MONTH_NAMES[calMonth - 1]} ${calYear}`;

  try {
    const res = await fetch(`${API_BASE}/api/analytics/calendar?year=${calYear}&month=${calMonth}`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    if (!res.ok) throw new Error("Failed to load calendar data");

    const calData = await res.json();
    calendarMonthTotal.textContent = `Month: ${formatCurrency(calData.month_total)}`;
    renderCalendarGrid(calData.days);

  } catch (err) {
    console.error("Calendar error:", err);
  }
}

function renderCalendarGrid(daysMap) {
  calendarGrid.innerHTML = "";

  // First day of month (0 = Sunday, 1 = Monday, etc.)
  const firstDayIndex = new Date(calYear, calMonth - 1, 1).getDay();
  // Number of days in month
  const totalDays = new Date(calYear, calMonth, 0).getDate();
  const todayStr = formatIsoDate(new Date());

  // Empty padding cells for days before start of month
  for (let i = 0; i < firstDayIndex; i++) {
    const emptyCell = document.createElement("div");
    emptyCell.className = "calendar-day-cell empty-cell";
    calendarGrid.appendChild(emptyCell);
  }

  // Day Cells
  for (let day = 1; day <= totalDays; day++) {
    const dateStr = `${calYear}-${String(calMonth).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    const dayData = daysMap[dateStr];

    const cell = document.createElement("div");
    cell.className = "calendar-day-cell";

    if (dateStr === todayStr) cell.classList.add("today-day");
    if (dateStr === selectedDate) cell.classList.add("selected-day");

    let badgeHtml = "";
    let dotsHtml = "";

    if (dayData && dayData.total > 0) {
      cell.classList.add("has-expenses");
      badgeHtml = `<div class="cal-day-badge">${formatCurrency(dayData.total)}</div>`;

      // Render dots for categories
      const dots = dayData.categories.map(cat => {
        const color = CATEGORY_META[cat]?.color || "#888";
        return `<span class="cal-dot" style="background-color: ${color};" title="${cat}"></span>`;
      }).join("");

      dotsHtml = `<div class="cal-dots-container">${dots}</div>`;
    }

    cell.innerHTML = `
      <div class="cal-day-num">${day}</div>
      ${badgeHtml}
      ${dotsHtml}
    `;

    // Click to select day and filter transactions
    cell.addEventListener("click", () => {
      selectedDate = dateStr;
      calendarSelectedInfo.textContent = `Viewing ${formatDate(dateStr)} • ${dayData ? formatCurrency(dayData.total) : formatCurrency(0)} spent`;
      resetDayFilterBtn.classList.remove("hidden");
      activeFilterTag.textContent = `Filtered to ${formatDate(dateStr)}`;
      activeFilterTag.classList.remove("hidden");

      // Re-highlight cells
      document.querySelectorAll(".calendar-day-cell").forEach(c => c.classList.remove("selected-day"));
      cell.classList.add("selected-day");

      // Reload filtered expenses and summary for this day
      loadExpenses();
      loadSummary();
    });

    calendarGrid.appendChild(cell);
  }
}

// =============================================================================
// Charts: Category Donut & Spending Trends
// =============================================================================
function renderCategoryChart(summary) {
  const chartCanvas = document.getElementById("categoryChart");
  if (!chartCanvas) return;

  if (summary.total_spent === 0) {
    chartCanvas.classList.add("hidden");
    emptyChartMessage.classList.remove("hidden");
    if (categoryChart) {
      categoryChart.destroy();
      categoryChart = null;
    }
    return;
  }

  chartCanvas.classList.remove("hidden");
  emptyChartMessage.classList.add("hidden");

  if (typeof Chart === "undefined") return;

  const labels = Object.keys(CATEGORY_META);
  const dataValues = labels.map((cat) => summary.category_totals[cat] || 0);
  const bgColors = labels.map((cat) => CATEGORY_META[cat].color);

  if (categoryChart) {
    categoryChart.data.labels = labels;
    categoryChart.data.datasets[0].data = dataValues;
    categoryChart.data.datasets[0].backgroundColor = bgColors;
    categoryChart.update();
  } else {
    const ctx = chartCanvas.getContext("2d");
    categoryChart = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: labels,
        datasets: [{
          data: dataValues,
          backgroundColor: bgColors,
          borderWidth: 2,
          borderColor: document.body.classList.contains("light-theme") ? "#ffffff" : "#1c2541",
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
            labels: {
              boxWidth: 10,
              padding: 12,
              color: document.body.classList.contains("light-theme") ? "#475569" : "#94a3b8",
              font: { family: "'Plus Jakarta Sans', sans-serif", size: 11, weight: "600" }
            }
          },
          tooltip: {
            callbacks: {
              label: function (context) {
                const value = context.parsed;
                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                const pct = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                return ` ${context.label}: ${currentCurrency}${value.toFixed(2)} (${pct}%)`;
              }
            }
          }
        },
        cutout: "66%"
      }
    });
  }
}

async function loadTrendChart() {
  const chartCanvas = document.getElementById("trendChart");
  if (!chartCanvas || typeof Chart === "undefined") return;

  try {
    const params = new URLSearchParams();
    params.append("period", currentTrendType);
    params.append("year", calYear);
    if (currentTrendType === "month") params.append("month", calMonth);

    const res = await fetch(`${API_BASE}/api/analytics/timeseries?${params.toString()}`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    if (!res.ok) throw new Error("Failed to load trend data");

    const ts = await res.json();

    if (currentTrendType === "month") {
      trendChartTitle.textContent = `Daily Spending (${MONTH_NAMES[calMonth - 1]} ${calYear})`;
    } else {
      trendChartTitle.textContent = `Monthly Spending (${calYear})`;
    }

    if (ts.total === 0) {
      chartCanvas.classList.add("hidden");
      emptyTrendMessage.classList.remove("hidden");
      if (trendChart) {
        trendChart.destroy();
        trendChart = null;
      }
      return;
    }

    chartCanvas.classList.remove("hidden");
    emptyTrendMessage.classList.add("hidden");

    if (trendChart) {
      trendChart.data.labels = ts.labels;
      trendChart.data.datasets[0].data = ts.data;
      trendChart.data.datasets[0].label = `Spending (${currentCurrency})`;
      trendChart.update();
    } else {
      const ctx = chartCanvas.getContext("2d");
      trendChart = new Chart(ctx, {
        type: "bar",
        data: {
          labels: ts.labels,
          datasets: [{
            label: `Spending (${currentCurrency})`,
            data: ts.data,
            backgroundColor: "rgba(99, 102, 241, 0.75)",
            borderColor: "#6366f1",
            borderWidth: 1.5,
            borderRadius: 4,
            hoverBackgroundColor: "#818cf8"
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: (ctx) => ` ${currentCurrency}${ctx.parsed.y.toFixed(2)}`
              }
            }
          },
          scales: {
            x: {
              grid: { display: false },
              ticks: {
                color: document.body.classList.contains("light-theme") ? "#64748b" : "#94a3b8",
                font: { size: 10 }
              }
            },
            y: {
              beginAtZero: true,
              grid: {
                color: document.body.classList.contains("light-theme") ? "rgba(0,0,0,0.06)" : "rgba(255,255,255,0.06)"
              },
              ticks: {
                color: document.body.classList.contains("light-theme") ? "#64748b" : "#94a3b8",
                callback: (val) => `${currentCurrency}${val}`
              }
            }
          }
        }
      });
    }

  } catch (err) {
    console.error("Trend chart error:", err);
  }
}

// =============================================================================
// Expenses List & CRUD
// =============================================================================
async function loadExpenses() {
  try {
    const category = categoryFilter.value;
    const search = searchInput.value.trim();

    const params = new URLSearchParams();
    if (category && category !== "All") params.append("category", category);
    if (search) params.append("search", search);

    // Apply active time filters
    if (selectedDate) {
      params.append("date", selectedDate);
    } else if (currentPeriod === "month") {
      params.append("year", calYear);
      params.append("month", calMonth);
    } else if (currentPeriod === "year") {
      params.append("year", calYear);
    } else if (currentPeriod === "day") {
      params.append("date", formatIsoDate(new Date()));
    }

    const res = await fetch(`${API_BASE}/api/expenses?${params.toString()}`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    if (!res.ok) throw new Error("Failed to load expenses");

    const data = await res.json();
    renderExpensesTable(data.expenses);

  } catch (err) {
    console.error("Expenses error:", err);
  }
}

function renderExpensesTable(expenses) {
  expensesTableBody.innerHTML = "";

  if (!expenses || expenses.length === 0) {
    emptyTableState.classList.remove("hidden");
    return;
  }

  emptyTableState.classList.add("hidden");

  expenses.forEach((item) => {
    const meta = CATEGORY_META[item.category] || { icon: "📌", tagClass: "", color: "#888" };
    const tr = document.createElement("tr");

    tr.innerHTML = `
      <td>${formatDate(item.date)}</td>
      <td>
        <span class="category-tag ${meta.tagClass}">
          <span>${meta.icon}</span>
          <span>${item.category}</span>
        </span>
      </td>
      <td>${escapeHtml(item.note) || '<span style="color:var(--text-muted); font-style:italic;">No description</span>'}</td>
      <td><span class="amount-text" style="color: ${meta.color};">${formatCurrency(item.amount)}</span></td>
      <td class="text-right">
        <button class="btn-delete-row" title="Delete expense" data-id="${item.id}">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          </svg>
        </button>
      </td>
    `;

    const deleteBtn = tr.querySelector(".btn-delete-row");
    deleteBtn.addEventListener("click", () => handleDeleteExpense(item.id, item.category, item.amount));

    expensesTableBody.appendChild(tr);
  });
}

async function handleAddExpense(e) {
  e.preventDefault();

  const amountVal = parseFloat(expenseAmount.value);
  if (isNaN(amountVal) || amountVal <= 0) {
    showToast("Please enter a valid amount greater than zero.", "error");
    expenseAmount.focus();
    return;
  }

  const selectedCategoryEl = document.querySelector('input[name="category"]:checked');
  if (!selectedCategoryEl) {
    showToast("Please select an expense category.", "error");
    return;
  }

  const categoryVal = selectedCategoryEl.value;
  const noteVal = expenseNote.value.trim();
  const dateVal = expenseDate.value || formatIsoDate(new Date());

  const payload = {
    amount: amountVal,
    category: categoryVal,
    note: noteVal,
    date: dateVal
  };

  submitExpenseBtn.disabled = true;

  try {
    const res = await fetch(`${API_BASE}/api/expenses`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${authToken}`
      },
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Failed to add expense");

    showToast(`Added ${formatCurrency(amountVal)} to ${CATEGORY_META[categoryVal].icon} ${categoryVal}!`, "success");

    expenseAmount.value = "";
    expenseNote.value = "";
    expenseAmount.focus();

    await refreshAllData();

  } catch (err) {
    showToast(err.message, "error");
  } finally {
    submitExpenseBtn.disabled = false;
  }
}

async function handleDeleteExpense(id, category, amount) {
  if (!confirm(`Delete this ${formatCurrency(amount)} expense under ${category}?`)) return;

  try {
    const res = await fetch(`${API_BASE}/api/expenses/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${authToken}` },
    });
    if (!res.ok) throw new Error("Failed to delete expense");

    showToast("Expense deleted.", "success");
    await refreshAllData();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function handleClearAll() {
  if (!confirm("Are you sure you want to clear ALL your recorded expenses? This cannot be undone.")) return;

  try {
    const res = await fetch(`${API_BASE}/api/clear`, {
      method: "POST",
      headers: { Authorization: `Bearer ${authToken}` },
    });
    if (!res.ok) throw new Error("Failed to clear expenses");

    showToast("All your expenses have been cleared.", "success");
    await refreshAllData();
  } catch (err) {
    showToast(err.message, "error");
  }
}

// =============================================================================
// Formatters & Utilities
// =============================================================================
function formatCurrency(num) {
  return `${currentCurrency}${Number(num || 0).toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })}`;
}

function formatDate(dateStr) {
  if (!dateStr) return "";
  try {
    const [y, m, d] = dateStr.split("-");
    const dateObj = new Date(y, m - 1, d);
    return dateObj.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric"
    });
  } catch {
    return dateStr;
  }
}

function formatIsoDate(dateObj) {
  const y = dateObj.getFullYear();
  const m = String(dateObj.getMonth() + 1).padStart(2, "0");
  const d = String(dateObj.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function escapeHtml(str) {
  if (!str) return "";
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function showToast(message, type = "success") {
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <span>${type === "success" ? "✓" : "⚠️"}</span>
    <span>${escapeHtml(message)}</span>
  `;

  toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 3200);
}

function initTheme() {
  const savedTheme = localStorage.getItem("expense_theme") || "dark";
  applyTheme(savedTheme);
}

function toggleTheme() {
  const isLight = document.body.classList.contains("light-theme");
  applyTheme(isLight ? "dark" : "light");
}

function applyTheme(theme) {
  if (theme === "light") {
    document.body.classList.remove("dark-theme");
    document.body.classList.add("light-theme");
    themeToggle.querySelector(".theme-icon").textContent = "☀️";
  } else {
    document.body.classList.remove("light-theme");
    document.body.classList.add("dark-theme");
    themeToggle.querySelector(".theme-icon").textContent = "🌙";
  }
  localStorage.setItem("expense_theme", theme);

  if (categoryChart) {
    categoryChart.data.datasets[0].borderColor = theme === "light" ? "#ffffff" : "#1c2541";
    categoryChart.update();
  }
  if (trendChart) {
    trendChart.update();
  }
}

function debounce(fn, delay) {
  let timer = null;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}
