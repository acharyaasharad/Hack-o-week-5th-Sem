# FinTrack — Modern Expense Tracker (REST API)

A production-ready, ultra-premium **Expense Tracker** web application backed by an Express.js REST API with real-time analytics, glassmorphic design system, and multi-theme support.

---

## ✨ Features & Upgrades

### 🎨 Visual & UI Highlights
- **Sleek FinTech Design System**: Crafted with glassmorphism, ambient glowing gradients, and micro-interactions.
- **Theme Switcher**: Seamless 1-click toggle between **Dark Mode** (obsidian slate) and **Light Mode** (clean pearl), persisted in `localStorage`.
- **KPI Summary Analytics Cards**:
  - **Total Spending**: formatted in Indian Rupees (`₹`) with average spend per transaction.
  - **Total Transactions**: real-time counter.
  - **Highest Expense**: highlights the single largest transaction with its title.
- **Category Spending Distribution**: Interactive segmented progress bar illustrating the percentage and proportion of expenses across categories.
- **Enhanced Form Experience**:
  - Interactive emoji category picker chips (`🍔 Food`, `🎬 Entertainment`, `💊 Health`, `🛍️ Shopping`, etc.).
  - Quick amount increment chips (`+₹100`, `+₹500`, `+₹1k`, `+₹5k`).
  - Quick date shortcuts (`Today`, `Yesterday`).
- **Data Filtering & Sorting**:
  - Real-time debounced search by title and description with quick clear button.
  - Category filter dropdown.
  - Multi-criteria sorting (**Newest First**, **Oldest First**, **Highest Amount**, **Lowest Amount**).
- **Export to CSV**: 1-click export of your entire transaction history to `.csv`.
- **Animated Toast Feedback**: Non-intrusive floating notifications for all CRUD operations.

---

## 🛠️ Project Structure

```
W1-2/
├── restapi.js         # Node.js Express REST API Server
├── package.json       # Project dependencies and npm scripts
├── data/
│   └── expenses.json  # JSON database file for persistence
├── public/
│   ├── index.html     # Semantic modern HTML5 layout
│   ├── style.css      # Vanilla CSS design tokens & animations
│   └── app.js         # Client-side JavaScript consuming the REST API
└── README.md          # Project documentation
```

---

## 📡 REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| **GET** | `/api/expenses` | Retrieve all expenses (supports `?search=` and `?category=`) |
| **GET** | `/api/expenses/:id` | Retrieve single expense by ID |
| **POST** | `/api/expenses` | Create a new expense (`{ title, amount, category, date, description }`) |
| **PUT** | `/api/expenses/:id` | Update an existing expense by ID |
| **DELETE** | `/api/expenses/:id` | Delete an expense by ID |
| **GET** | `/api/stats` | Retrieve aggregated metrics (`totalSpending`, `totalTransactions`, `highestExpense`) |

---

## 🏃 Running the Application

### 1. Install Dependencies
```bash
npm install
```

### 2. Start the Server
```bash
npm start
```
*or in watch mode:*
```bash
npm run dev
```

### 3. Open in Browser
Visit [http://localhost:3000](http://localhost:3000) in your web browser.
