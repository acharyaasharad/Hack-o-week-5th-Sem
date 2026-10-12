const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;
const DATA_DIR = path.join(__dirname, 'data');
const DATA_FILE = path.join(DATA_DIR, 'expenses.json');

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Ensure data directory and initial seed data exist
function initializeData() {
  if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR, { recursive: true });
  }

  if (!fs.existsSync(DATA_FILE)) {
    const seedExpenses = [
      {
        id: "1",
        title: "Books Shopping",
        amount: 5000,
        category: "Others",
        date: "2026-07-06",
        description: ""
      },
      {
        id: "2",
        title: "Movie with Friends",
        amount: 4000,
        category: "Entertainment",
        date: "2026-07-06",
        description: "Take 1200 from Shravani"
      },
      {
        id: "3",
        title: "Lunch at Hotel",
        amount: 1200,
        category: "Food",
        date: "2026-07-01",
        description: ""
      },
      {
        id: "4",
        title: "Medicines",
        amount: 2640,
        category: "Health",
        date: "2026-06-29",
        description: ""
      }
    ];
    fs.writeFileSync(DATA_FILE, JSON.stringify(seedExpenses, null, 2), 'utf8');
  }
}

initializeData();

// Helper functions for reading/writing expenses
function readExpenses() {
  try {
    const data = fs.readFileSync(DATA_FILE, 'utf8');
    return JSON.parse(data);
  } catch (err) {
    console.error("Error reading expenses:", err);
    return [];
  }
}

function writeExpenses(expenses) {
  try {
    fs.writeFileSync(DATA_FILE, JSON.stringify(expenses, null, 2), 'utf8');
    return true;
  } catch (err) {
    console.error("Error writing expenses:", err);
    return false;
  }
}

// REST API Endpoints

/**
 * GET /api/expenses
 * Query parameters:
 *   - search: string (matches title or description case-insensitively)
 *   - category: string (matches category or 'all')
 */
app.get('/api/expenses', (req, res) => {
  let expenses = readExpenses();
  const { search, category } = req.query;

  if (category && category.toLowerCase() !== 'all') {
    expenses = expenses.filter(
      (exp) => exp.category.toLowerCase() === category.toLowerCase()
    );
  }

  if (search && search.trim() !== '') {
    const term = search.trim().toLowerCase();
    expenses = expenses.filter(
      (exp) =>
        exp.title.toLowerCase().includes(term) ||
        (exp.description && exp.description.toLowerCase().includes(term))
    );
  }

  res.json({
    success: true,
    count: expenses.length,
    data: expenses
  });
});

/**
 * GET /api/expenses/stats
 * Returns overall statistics: total spending, transaction count, highest expense
 */
app.get('/api/stats', (req, res) => {
  const expenses = readExpenses();
  const totalSpending = expenses.reduce((sum, exp) => sum + Number(exp.amount || 0), 0);
  const totalTransactions = expenses.length;
  const highestExpense = expenses.length > 0
    ? Math.max(...expenses.map((exp) => Number(exp.amount || 0)))
    : 0;

  res.json({
    success: true,
    data: {
      totalSpending,
      totalTransactions,
      highestExpense
    }
  });
});

/**
 * GET /api/expenses/:id
 * Retrieve single expense by ID
 */
app.get('/api/expenses/:id', (req, res) => {
  const expenses = readExpenses();
  const expense = expenses.find((exp) => exp.id === req.id || exp.id === req.params.id);

  if (!expense) {
    return res.status(404).json({
      success: false,
      message: `Expense with id ${req.params.id} not found`
    });
  }

  res.json({
    success: true,
    data: expense
  });
});

/**
 * POST /api/expenses
 * Create a new expense
 */
app.post('/api/expenses', (req, res) => {
  const { title, amount, category, date, description } = req.body;

  if (!title || !title.trim()) {
    return res.status(400).json({ success: false, message: 'Title is required' });
  }

  const parsedAmount = parseFloat(amount);
  if (isNaN(parsedAmount) || parsedAmount <= 0) {
    return res.status(400).json({ success: false, message: 'Valid positive amount is required' });
  }

  if (!category || !category.trim()) {
    return res.status(400).json({ success: false, message: 'Category is required' });
  }

  if (!date || !date.trim()) {
    return res.status(400).json({ success: false, message: 'Date is required' });
  }

  const expenses = readExpenses();
  const newExpense = {
    id: Date.now().toString(),
    title: title.trim(),
    amount: parsedAmount,
    category: category.trim(),
    date: date.trim(),
    description: description ? description.trim() : ''
  };

  expenses.unshift(newExpense);
  writeExpenses(expenses);

  res.status(201).json({
    success: true,
    message: 'Expense added successfully',
    data: newExpense
  });
});

/**
 * PUT /api/expenses/:id
 * Update an existing expense
 */
app.put('/api/expenses/:id', (req, res) => {
  const { id } = req.params;
  const { title, amount, category, date, description } = req.body;

  const expenses = readExpenses();
  const index = expenses.findIndex((exp) => exp.id === id);

  if (index === -1) {
    return res.status(404).json({
      success: false,
      message: `Expense with id ${id} not found`
    });
  }

  if (title !== undefined) expenses[index].title = title.trim();
  if (amount !== undefined) {
    const parsedAmount = parseFloat(amount);
    if (isNaN(parsedAmount) || parsedAmount <= 0) {
      return res.status(400).json({ success: false, message: 'Valid positive amount is required' });
    }
    expenses[index].amount = parsedAmount;
  }
  if (category !== undefined) expenses[index].category = category.trim();
  if (date !== undefined) expenses[index].date = date.trim();
  if (description !== undefined) expenses[index].description = description.trim();

  writeExpenses(expenses);

  res.json({
    success: true,
    message: 'Expense updated successfully',
    data: expenses[index]
  });
});

/**
 * DELETE /api/expenses/:id
 * Delete an expense
 */
app.delete('/api/expenses/:id', (req, res) => {
  const { id } = req.params;
  const expenses = readExpenses();
  const index = expenses.findIndex((exp) => exp.id === id);

  if (index === -1) {
    return res.status(404).json({
      success: false,
      message: `Expense with id ${id} not found`
    });
  }

  const deletedExpense = expenses.splice(index, 1)[0];
  writeExpenses(expenses);

  res.json({
    success: true,
    message: 'Expense deleted successfully',
    data: deletedExpense
  });
});

// Fallback to index.html for single page application navigation
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Start Server
app.listen(PORT, () => {
  console.log(`===============================================`);
  console.log(` Expense Tracker REST API Server Running `);
  console.log(` Port: http://localhost:${PORT}`);
  console.log(` API Docs:`);
  console.log(`  - GET    /api/expenses`);
  console.log(`  - GET    /api/stats`);
  console.log(`  - GET    /api/expenses/:id`);
  console.log(`  - POST   /api/expenses`);
  console.log(`  - PUT    /api/expenses/:id`);
  console.log(`  - DELETE /api/expenses/:id`);
  console.log(`===============================================`);
});
