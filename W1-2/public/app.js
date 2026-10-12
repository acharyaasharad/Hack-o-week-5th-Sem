// ==========================================================================
// FinTrack Client Application
// Modern REST API Client with Analytics, Theme Switcher & Rich UX
// ==========================================================================

const API_BASE = '/api';

// Category Configuration & Colors
const CATEGORY_META = {
  Food: { emoji: '🍔', color: '#f97316' },
  Entertainment: { emoji: '🎬', color: '#8b5cf6' },
  Health: { emoji: '💊', color: '#14b8a6' },
  Shopping: { emoji: '🛍️', color: '#ec4899' },
  Travel: { emoji: '✈️', color: '#0ea5e9' },
  Bills: { emoji: '⚡', color: '#eab308' },
  Others: { emoji: '📦', color: '#64748b' }
};

// DOM References
const htmlElement = document.documentElement;
const themeToggleBtn = document.getElementById('themeToggleBtn');
const exportCsvBtn = document.getElementById('exportCsvBtn');
const apiStatus = document.getElementById('apiStatus');

const expenseForm = document.getElementById('expenseForm');
const formHeading = document.getElementById('formHeading');
const formSubtext = document.getElementById('formSubtext');
const editingBadgeGroup = document.getElementById('editingBadgeGroup');
const submitBtn = document.getElementById('submitBtn');
const submitBtnText = document.getElementById('submitBtnText');
const clearBtn = document.getElementById('clearBtn');
const cancelEditBtn = document.getElementById('cancelEditBtn');

const expenseIdInput = document.getElementById('expenseId');
const titleInput = document.getElementById('expenseTitle');
const amountInput = document.getElementById('expenseAmount');
const categoryInput = document.getElementById('expenseCategory');
const dateInput = document.getElementById('expenseDate');
const descriptionInput = document.getElementById('expenseDescription');
const categoryChips = document.querySelectorAll('.category-chip');
const amountChips = document.querySelectorAll('.amount-chip');
const todayDateBtn = document.getElementById('todayDateBtn');
const yesterdayDateBtn = document.getElementById('yesterdayDateBtn');

const searchInput = document.getElementById('searchInput');
const clearSearchBtn = document.getElementById('clearSearchBtn');
const categoryFilter = document.getElementById('categoryFilter');
const sortSelect = document.getElementById('sortSelect');

const totalSpendingValue = document.getElementById('totalSpendingValue');
const totalTransactionsValue = document.getElementById('totalTransactionsValue');
const highestExpenseValue = document.getElementById('highestExpenseValue');
const avgTransactionText = document.getElementById('avgTransactionText');
const highestExpenseName = document.getElementById('highestExpenseName');

const breakdownProgressBar = document.getElementById('breakdownProgressBar');
const breakdownLegend = document.getElementById('breakdownLegend');
const breakdownCategoryCount = document.getElementById('breakdownCategoryCount');

const transactionsCountBadge = document.getElementById('transactionsCountBadge');
const visibleSubtotalText = document.getElementById('visibleSubtotalText');
const expensesListContainer = document.getElementById('expensesList');

const toastNotification = document.getElementById('toastNotification');
const toastIcon = document.getElementById('toastIcon');
const toastMessage = document.getElementById('toastMessage');

// State
let rawExpenses = [];
let currentEditingId = null;
let searchDebounceTimer = null;
let toastTimeout = null;

// --------------------------------------------------------------------------
// 1. Theme Management (Dark / Light)
// --------------------------------------------------------------------------
function initTheme() {
  const savedTheme = localStorage.getItem('fintrack_theme');
  if (savedTheme) {
    htmlElement.setAttribute('data-theme', savedTheme);
  } else {
    // Default to dark theme for modern FinTech aesthetic
    htmlElement.setAttribute('data-theme', 'dark');
  }
}

themeToggleBtn.addEventListener('click', () => {
  const currentTheme = htmlElement.getAttribute('data-theme') || 'dark';
  const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
  htmlElement.setAttribute('data-theme', newTheme);
  localStorage.setItem('fintrack_theme', newTheme);
  showToast(`Switched to ${newTheme} mode`, 'success');
});

// --------------------------------------------------------------------------
// 2. Formatters & Helpers
// --------------------------------------------------------------------------
function formatCurrency(amount) {
  const num = Number(amount) || 0;
  return `₹${num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatDateDisplay(dateStr) {
  if (!dateStr) return '';
  const parts = dateStr.split('-');
  if (parts.length === 3) {
    const year = parseInt(parts[0], 10);
    const month = parseInt(parts[1], 10);
    const day = parseInt(parts[2], 10);
    if (!isNaN(year) && !isNaN(month) && !isNaN(day)) {
      return `${month}/${day}/${year}`;
    }
  }
  return dateStr;
}

function getTodayString(offsetDays = 0) {
  const d = new Date();
  if (offsetDays !== 0) d.setDate(d.getDate() + offsetDays);
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
}

function showToast(msg, type = 'success') {
  clearTimeout(toastTimeout);
  toastMessage.textContent = msg;
  toastIcon.textContent = type === 'error' ? '!' : '✓';
  toastNotification.className = `toast show ${type === 'error' ? 'toast-error' : ''}`;

  toastTimeout = setTimeout(() => {
    toastNotification.className = 'toast';
  }, 3200);
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// --------------------------------------------------------------------------
// 3. REST API Interaction
// --------------------------------------------------------------------------
async function fetchExpenses() {
  try {
    const query = new URLSearchParams();
    const searchTerm = searchInput.value.trim();
    const cat = categoryFilter.value;

    if (searchTerm) query.append('search', searchTerm);
    if (cat && cat !== 'all') query.append('category', cat);

    const res = await fetch(`${API_BASE}/expenses?${query.toString()}`);
    const result = await res.json();

    if (result.success) {
      rawExpenses = result.data;
      applySortingAndRender();
      updateCategoryBreakdown(rawExpenses);
    } else {
      showToast(result.message || 'Failed to fetch expenses', 'error');
    }
  } catch (err) {
    console.error('Fetch expenses error:', err);
    apiStatus.innerHTML = '<span class="status-dot" style="background:#ef4444"></span> Offline';
    expensesListContainer.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">⚡</div>
        <h4 class="empty-state-title">Connection Error</h4>
        <p>Could not connect to the REST API server at <code>http://localhost:3000</code>.</p>
      </div>
    `;
  }
}

async function fetchStats() {
  try {
    const res = await fetch(`${API_BASE}/stats`);
    const result = await res.json();

    if (result.success) {
      const stats = result.data;
      totalSpendingValue.textContent = formatCurrency(stats.totalSpending);
      totalTransactionsValue.textContent = stats.totalTransactions;
      highestExpenseValue.textContent = formatCurrency(stats.highestExpense);

      // Average calculation
      if (stats.totalTransactions > 0) {
        const avg = stats.totalSpending / stats.totalTransactions;
        avgTransactionText.innerHTML = `<span>Avg: ${formatCurrency(avg)}</span>`;
      } else {
        avgTransactionText.innerHTML = `<span>Avg: ₹0</span>`;
      }

      // Identify highest expense item name if available
      if (rawExpenses.length > 0) {
        const maxExp = rawExpenses.reduce((prev, curr) => (Number(curr.amount) > Number(prev.amount) ? curr : prev), rawExpenses[0]);
        highestExpenseName.innerHTML = `<span>${escapeHtml(maxExp.title.slice(0, 12))}</span>`;
      }
    }
  } catch (err) {
    console.error('Fetch stats error:', err);
  }
}

// --------------------------------------------------------------------------
// 4. Client-side Sorting & Rendering
// --------------------------------------------------------------------------
function applySortingAndRender() {
  const sortBy = sortSelect.value;
  let sorted = [...rawExpenses];

  if (sortBy === 'date-desc') {
    sorted.sort((a, b) => new Date(b.date) - new Date(a.date));
  } else if (sortBy === 'date-asc') {
    sorted.sort((a, b) => new Date(a.date) - new Date(b.date));
  } else if (sortBy === 'amount-desc') {
    sorted.sort((a, b) => Number(b.amount) - Number(a.amount));
  } else if (sortBy === 'amount-asc') {
    sorted.sort((a, b) => Number(a.amount) - Number(b.amount));
  }

  renderExpenseList(sorted);
}

function renderExpenseList(items) {
  transactionsCountBadge.textContent = `${items.length} ${items.length === 1 ? 'item' : 'items'}`;
  
  const subtotal = items.reduce((sum, item) => sum + Number(item.amount || 0), 0);
  visibleSubtotalText.textContent = `Subtotal: ${formatCurrency(subtotal)}`;

  if (items.length === 0) {
    expensesListContainer.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">🔍</div>
        <h4 class="empty-state-title">No transactions found</h4>
        <p>Try clearing your search query or add a new transaction above.</p>
      </div>
    `;
    return;
  }

  expensesListContainer.innerHTML = items
    .map((exp) => {
      const catKey = exp.category || 'Others';
      const meta = CATEGORY_META[catKey] || CATEGORY_META.Others;
      const formattedDate = formatDateDisplay(exp.date);
      const noteHtml = exp.description
        ? `<div class="expense-note">${escapeHtml(exp.description)}</div>`
        : '';

      return `
        <article class="expense-item" data-id="${exp.id}">
          <div class="expense-left">
            <div class="expense-avatar avatar-${catKey}" title="${catKey}">
              ${meta.emoji}
            </div>
            <div class="expense-body">
              <h4 class="expense-title">${escapeHtml(exp.title)}</h4>
              <div class="expense-meta">
                <span class="category-pill pill-${catKey}">${escapeHtml(exp.category)}</span>
                <span class="expense-date">${formattedDate}</span>
              </div>
              ${noteHtml}
              <div class="expense-actions">
                <button class="btn-action btn-action-edit" data-id="${exp.id}" aria-label="Edit ${escapeHtml(exp.title)}">Edit</button>
                <button class="btn-action btn-action-delete" data-id="${exp.id}" aria-label="Delete ${escapeHtml(exp.title)}">Delete</button>
              </div>
            </div>
          </div>
          <div class="expense-right">
            <div class="expense-amount">${formatCurrency(exp.amount)}</div>
          </div>
        </article>
      `;
    })
    .join('');

  // Attach click listeners to edit & delete buttons
  document.querySelectorAll('.btn-action-edit').forEach((btn) => {
    btn.addEventListener('click', () => handleEditClick(btn.dataset.id));
  });

  document.querySelectorAll('.btn-action-delete').forEach((btn) => {
    btn.addEventListener('click', () => handleDeleteClick(btn.dataset.id));
  });
}

// --------------------------------------------------------------------------
// 5. Visual Category Distribution Breakdown Bar
// --------------------------------------------------------------------------
function updateCategoryBreakdown(items) {
  if (!items || items.length === 0) {
    breakdownProgressBar.innerHTML = `<div class="breakdown-segment" style="width: 100%; background: var(--border-medium);"></div>`;
    breakdownLegend.innerHTML = `<span style="font-size: 11px; color: var(--text-muted);">No spending data</span>`;
    breakdownCategoryCount.textContent = '0 Categories';
    return;
  }

  const categoryTotals = {};
  let grandTotal = 0;

  items.forEach((exp) => {
    const cat = exp.category || 'Others';
    const amt = Number(exp.amount || 0);
    categoryTotals[cat] = (categoryTotals[cat] || 0) + amt;
    grandTotal += amt;
  });

  const categories = Object.keys(categoryTotals);
  breakdownCategoryCount.textContent = `${categories.length} ${categories.length === 1 ? 'Category' : 'Categories'}`;

  if (grandTotal === 0) return;

  // Build segments
  let segmentsHtml = '';
  let legendHtml = '';

  categories.sort((a, b) => categoryTotals[b] - categoryTotals[a]);

  categories.forEach((cat) => {
    const total = categoryTotals[cat];
    const pct = ((total / grandTotal) * 100).toFixed(1);
    const meta = CATEGORY_META[cat] || CATEGORY_META.Others;

    segmentsHtml += `
      <div class="breakdown-segment" style="width: ${pct}%; background: ${meta.color};" title="${cat}: ${pct}% (${formatCurrency(total)})"></div>
    `;

    legendHtml += `
      <div class="legend-item">
        <span class="legend-dot" style="background: ${meta.color}"></span>
        <span>${meta.emoji} ${cat}</span>
        <span class="legend-percentage">${pct}%</span>
      </div>
    `;
  });

  breakdownProgressBar.innerHTML = segmentsHtml;
  breakdownLegend.innerHTML = legendHtml;
}

// --------------------------------------------------------------------------
// 6. Interactive Category & Amount Chips
// --------------------------------------------------------------------------
categoryChips.forEach((chip) => {
  chip.addEventListener('click', () => {
    const targetCat = chip.dataset.category;
    categoryInput.value = targetCat;
    highlightSelectedCategoryChip(targetCat);
  });
});

function highlightSelectedCategoryChip(selectedCat) {
  categoryChips.forEach((chip) => {
    if (chip.dataset.category === selectedCat) {
      chip.classList.add('active');
    } else {
      chip.classList.remove('active');
    }
  });
}

categoryInput.addEventListener('change', () => {
  highlightSelectedCategoryChip(categoryInput.value);
});

amountChips.forEach((chip) => {
  chip.addEventListener('click', () => {
    const addAmt = parseFloat(chip.dataset.add);
    const current = parseFloat(amountInput.value) || 0;
    amountInput.value = (current + addAmt).toFixed(0);
    amountInput.focus();
  });
});

todayDateBtn.addEventListener('click', () => {
  dateInput.value = getTodayString(0);
});

yesterdayDateBtn.addEventListener('click', () => {
  dateInput.value = getTodayString(-1);
});

// --------------------------------------------------------------------------
// 7. Form Submission (Add & Edit via REST API)
// --------------------------------------------------------------------------
expenseForm.addEventListener('submit', async (e) => {
  e.preventDefault();

  const title = titleInput.value.trim();
  const amount = parseFloat(amountInput.value);
  const category = categoryInput.value;
  const date = dateInput.value;
  const description = descriptionInput.value.trim();

  if (!title) {
    showToast('Please enter an expense title', 'error');
    titleInput.focus();
    return;
  }

  if (isNaN(amount) || amount <= 0) {
    showToast('Please specify a valid amount greater than ₹0', 'error');
    amountInput.focus();
    return;
  }

  if (!category) {
    showToast('Please select a category', 'error');
    categoryInput.focus();
    return;
  }

  if (!date) {
    showToast('Please pick a date', 'error');
    dateInput.focus();
    return;
  }

  const payload = { title, amount, category, date, description };

  submitBtn.disabled = true;
  submitBtnText.textContent = currentEditingId ? 'Updating...' : 'Adding...';

  try {
    if (currentEditingId) {
      // PUT /api/expenses/:id
      const res = await fetch(`${API_BASE}/expenses/${currentEditingId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const result = await res.json();

      if (result.success) {
        showToast('Expense updated successfully!');
        resetForm();
        await fetchExpenses();
        await fetchStats();
      } else {
        showToast(result.message || 'Error updating expense', 'error');
      }
    } else {
      // POST /api/expenses
      const res = await fetch(`${API_BASE}/expenses`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const result = await res.json();

      if (result.success) {
        showToast('Expense logged successfully!');
        resetForm();
        await fetchExpenses();
        await fetchStats();
      } else {
        showToast(result.message || 'Error adding expense', 'error');
      }
    }
  } catch (err) {
    console.error('Submit error:', err);
    showToast('Network error while saving expense', 'error');
  } finally {
    submitBtn.disabled = false;
    submitBtnText.textContent = currentEditingId ? 'Update Expense' : 'Add Expense';
  }
});

// --------------------------------------------------------------------------
// 8. Edit & Delete Handlers
// --------------------------------------------------------------------------
async function handleEditClick(id) {
  try {
    const res = await fetch(`${API_BASE}/expenses/${id}`);
    const result = await res.json();

    if (result.success && result.data) {
      const exp = result.data;
      currentEditingId = exp.id;
      expenseIdInput.value = exp.id;
      titleInput.value = exp.title;
      amountInput.value = exp.amount;
      categoryInput.value = exp.category;
      dateInput.value = exp.date;
      descriptionInput.value = exp.description || '';

      highlightSelectedCategoryChip(exp.category);

      // Toggle edit UI state
      formHeading.textContent = 'Edit Expense';
      formSubtext.textContent = `Modifying #${exp.id} • ${exp.title}`;
      editingBadgeGroup.style.display = 'flex';
      submitBtnText.textContent = 'Update Expense';
      cancelEditBtn.style.display = 'inline-flex';

      document.querySelector('.form-card').scrollIntoView({ behavior: 'smooth' });
      titleInput.focus();
    }
  } catch (err) {
    console.error('Error fetching expense for edit:', err);
    showToast('Failed to load expense for editing', 'error');
  }
}

async function handleDeleteClick(id) {
  const item = rawExpenses.find((e) => e.id === id);
  const itemName = item ? item.title : 'this expense';

  if (!confirm(`Are you sure you want to delete "${itemName}"?`)) {
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/expenses/${id}`, { method: 'DELETE' });
    const result = await res.json();

    if (result.success) {
      showToast(`Deleted "${itemName}"`);
      if (currentEditingId === id) resetForm();
      await fetchExpenses();
      await fetchStats();
    } else {
      showToast(result.message || 'Failed to delete expense', 'error');
    }
  } catch (err) {
    console.error('Delete error:', err);
    showToast('Network error while deleting expense', 'error');
  }
}

function resetForm() {
  expenseForm.reset();
  currentEditingId = null;
  expenseIdInput.value = '';
  formHeading.textContent = 'Add Expense';
  formSubtext.textContent = 'Log a new transaction to your vault';
  editingBadgeGroup.style.display = 'none';
  submitBtnText.textContent = 'Add Expense';
  cancelEditBtn.style.display = 'none';
  highlightSelectedCategoryChip('');
}

clearBtn.addEventListener('click', () => {
  resetForm();
  showToast('Form cleared');
});

cancelEditBtn.addEventListener('click', () => {
  resetForm();
});

// --------------------------------------------------------------------------
// 9. Search, Filter & CSV Export
// --------------------------------------------------------------------------
searchInput.addEventListener('input', () => {
  const val = searchInput.value;
  clearSearchBtn.style.display = val ? 'flex' : 'none';

  clearTimeout(searchDebounceTimer);
  searchDebounceTimer = setTimeout(() => {
    fetchExpenses();
  }, 220);
});

clearSearchBtn.addEventListener('click', () => {
  searchInput.value = '';
  clearSearchBtn.style.display = 'none';
  fetchExpenses();
});

categoryFilter.addEventListener('change', () => {
  fetchExpenses();
});

sortSelect.addEventListener('change', () => {
  applySortingAndRender();
});

// CSV Export
exportCsvBtn.addEventListener('click', () => {
  if (rawExpenses.length === 0) {
    showToast('No transactions to export', 'error');
    return;
  }

  const headers = ['ID', 'Title', 'Amount (INR)', 'Category', 'Date', 'Description'];
  const rows = rawExpenses.map((exp) => [
    `"${exp.id}"`,
    `"${(exp.title || '').replace(/"/g, '""')}"`,
    exp.amount,
    `"${exp.category}"`,
    `"${exp.date}"`,
    `"${(exp.description || '').replace(/"/g, '""')}"`
  ]);

  const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', `fintrack-expenses-${getTodayString()}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  showToast('Exported transactions CSV');
});

// --------------------------------------------------------------------------
// 10. Initialization
// --------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  fetchExpenses();
  fetchStats();
});
