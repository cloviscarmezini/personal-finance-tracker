document.addEventListener('DOMContentLoaded', () => {
    const chartCanvas = document.getElementById('expensesChart');
    const budgetContainer = document.getElementById('budget-progress-container');

    if (chartCanvas) initAnalyticsChart(chartCanvas);
    if (budgetContainer) loadBudgetThresholds(budgetContainer);

    setupAsyncForm('walletForm', '/api/resources/wallet/create', 'walletModal');
    setupAsyncForm('categoryForm', '/api/resources/category/create', 'categoryModal');
    setupAsyncForm('budgetForm', '/api/resources/budget/create', 'budgetModal');

    loadCurrencySelectors();
    setupTransactionGlobalListener();
});

async function fetchCurrencyOptions() {
    try {
        const response = await fetch('/api/resources/currencies/', {
            method: 'GET',
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        const data = await response.json();
        if (response.ok && data.status === 'success' && Array.isArray(data.currencies)) {
            return data.currencies;
        }
    } catch (err) {
        console.error('Failed to fetch currencies:', err);
    }
    return [];
}

function renderCurrencySelect(select, currencies) {
    if (!select || currencies.length === 0) return;
    const defaultValue = select.dataset.selected || select.value || '';
    select.innerHTML = '';

    currencies.forEach(({ code, name, symbol }) => {
        const option = document.createElement('option');
        option.value = code;
        option.textContent = symbol ? `${code} (${symbol}) - ${name}` : `${code} - ${name}`;
        if (code === defaultValue) option.selected = true;
        select.appendChild(option);
    });

    if (defaultValue && !select.value) {
        select.value = defaultValue;
    }
}

async function loadCurrencySelectors() {
    const selects = document.querySelectorAll('select.js-currency-selector');
    if (!selects.length) return;

    const currencies = await fetchCurrencyOptions();
    selects.forEach((select) => renderCurrencySelect(select, currencies));
}

function setupAsyncForm(formId, endpoint, modalId) {
    const form = document.getElementById(formId);
    if (!form) return;

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        const formData = new FormData(form);

        fetch(endpoint, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success') {
                const modalElement = document.getElementById(modalId);
                const modalInstance = bootstrap.Modal.getInstance(modalElement);
                if (modalInstance) modalInstance.hide();
                
                form.reset();

                const budgetContainer = document.getElementById('budget-progress-container');
                if (budgetContainer) loadBudgetThresholds(budgetContainer);
                
                const chartCanvas = document.getElementById('expensesChart');
                if (chartCanvas) initAnalyticsChart(chartCanvas);
                
                location.reload(); 
            } else {
                alert('Operation failed: ' + data.message);
            }
        })
        .catch(err => console.error('Error handling async mutation:', err));
    });
}

function setupTransactionGlobalListener() {
    document.addEventListener('submit', async (e) => {
        if (e.target && e.target.id === 'transactionForm') {
            const tableBody = document.getElementById('transactions-table-body');
            
            if (!tableBody) {
                return;
            }

            e.preventDefault();
            
            const form = e.target;
            const formData = new FormData(form);

            try {
                const response = await fetch(form.action, {
                    method: 'POST',
                    body: formData,
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                });
                const data = await response.json();

                if (data.status === 'success') {
                    const t = data.transaction;
                    
                    await refreshBalanceCards();

                    const modalElement = document.getElementById('transactionModal');
                    const modalInstance = bootstrap.Modal.getInstance(modalElement) || new bootstrap.Modal(modalElement);
                    if (modalInstance) modalInstance.hide();
                    form.reset();

                    if (tableBody.children.length === 1 && tableBody.querySelector('.text-center')) {
                        tableBody.innerHTML = '';
                    }

                    const newRow = document.createElement('tr');
                    const typeSign = t.transaction_type === 'INFLOW' ? '+' : '-';
                    const typeClass = t.transaction_type === 'INFLOW' ? 'text-success' : 'text-danger';
                    
                    let categoryBadge = t.category_name !== 'Uncategorized' 
                        ? `<span class="badge text-dark border small" style="background-color: ${t.category_color}22; border-color: ${t.category_color} !important;">
                                <i class="bi ${t.category_icon} me-1" style="color: ${t.category_color};"></i>${t.category_name}
                           </span>`
                        : `<span class="badge bg-light text-muted border small"><i class="bi bi-question-circle me-1"></i>Uncategorized</span>`;

                    newRow.innerHTML = `
                        <td class="text-secondary small">${t.date}</td>
                        <td><span class="badge bg-light text-dark border">${t.wallet_name}</span></td>
                        <td>${categoryBadge}</td>
                        <td class="fw-semibold text-dark">${t.description}</td>
                        <td class="fw-bold text-end ${typeClass}">
                            ${typeSign} ${t.wallet_currency} ${t.amount.toFixed(2)}
                        </td>
                        <td class="text-end no-print">
                            <a href="${t.edit_url}" class="btn btn-sm btn-outline-dark me-1"><i class="bi bi-pencil"></i></a>
                            <a href="${t.delete_url}" class="btn btn-sm btn-outline-danger" onclick="return confirm('Are you sure you want to delete this transaction?');"><i class="bi bi-trash"></i></a>
                        </td>
                    `;

                    tableBody.insertBefore(newRow, tableBody.firstChild);
                } else {
                    alert('Operation failed: ' + data.message);
                }
            } catch (err) {
                console.error('[Ledger SPA Error] Command failure:', err);
            }
        }
    });
}

async function refreshBalanceCards() {
    const accumulatedCard = document.getElementById('card-accumulated-balance');
    const balanceCard = document.getElementById('card-balance');
    
    if (!accumulatedCard && !balanceCard) return;

    let searchParams = new URLSearchParams(window.location.search);
    
    if (!searchParams.has('month') && !searchParams.has('start_date')) {
        const prevLink = document.querySelector('a[href*="month="]');
        if (prevLink) {
            const linkUrl = new URL(prevLink.href, window.location.origin);
            const linkParams = new URLSearchParams(linkUrl.search);
            
            let targetMonth = parseInt(linkParams.get('month')) + 1;
            let targetYear = parseInt(linkParams.get('year'));
            
            if (targetMonth > 12) {
                targetMonth = 1;
                targetYear += 1;
            }
            searchParams.set('month', targetMonth);
            searchParams.set('year', targetYear);
        }
    }

    const queryString = searchParams.toString();
    const finalEndpoint = `/api/analytics/balance-metrics${queryString ? '?' + queryString : ''}`;
    
    try {
        const response = await fetch(finalEndpoint, {
            method: 'GET',
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        const data = await response.json();
        
        if (data.status === 'success' && data.metrics) {
            const m = data.metrics;
            
            if (accumulatedCard) {
                const valueDisplay = accumulatedCard.querySelector('.balance-value');
                if (valueDisplay) {
                    valueDisplay.textContent = `${m.base_currency} ${m.accumulated_balance.toFixed(2)}`;
                }
            }
            
            if (balanceCard) {
                const valueDisplay = balanceCard.querySelector('.balance-value');
                if (valueDisplay) {
                    valueDisplay.textContent = `${m.base_currency} ${m.interval_balance.toFixed(2)}`;
                    
                    if (m.interval_balance >= 0) {
                        valueDisplay.classList.remove('text-danger');
                        valueDisplay.classList.add('text-success');
                    } else {
                        valueDisplay.classList.remove('text-success');
                        valueDisplay.classList.add('text-danger');
                    }
                }
            }
        }
    } catch (err) {
        console.error('[Ledger SPA Error] Query failure:', err);
    }
}

function initAnalyticsChart(canvasElement) {
    const ctx = canvasElement.getContext('2d');
    fetch('/api/analytics/chart')
        .then(res => res.json())
        .then(payload => {
            const chartData = Array.isArray(payload.data) ? payload.data : [];
            if (chartData.length === 0) {
                renderEmptyChartState(canvasElement);
                return;
            }
            const labels = chartData.map(item => item.label || 'Unknown');
            const values = chartData.map(item => Number(item.value) || 0);
            const colors = chartData.map(item => item.color || '#6c757d');

            if (window.myGlobalChart) window.myGlobalChart.destroy();
            window.myGlobalChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        backgroundColor: colors,
                        hoverOffset: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom', labels: { boxWidth: 12, padding: 16 } },
                        tooltip: { callbacks: { label: context => `${context.label}: ${context.formattedValue}` } }
                    }
                }
            });
        })
        .catch(err => {
            console.error('[Analytics Chart] Failed to load data:', err);
            renderEmptyChartState(canvasElement);
        });
}

function loadBudgetThresholds(containerElement) {
    fetch('/api/analytics/budget')
        .then(res => res.json())
        .then(data => {
            const budgets = Array.isArray(data.budgets) ? data.budgets : [];
            if (budgets.length === 0) {
                containerElement.innerHTML = '<div class="col text-center text-muted py-3 w-100">No thresholds set.</div>';
                return;
            }
            containerElement.innerHTML = '';
            budgets.forEach(b => {
                const percentage = Number(b.usage_percentage) || 0;
                const spent = Number(b.amount_spent) || 0;
                const limit = Number(b.amount_limit) || 0;
                const categoryLabel = b.category_name || 'Unknown';
                const categoryColor = b.category_color || '#6c757d';
                let progressClass = 'bg-success';
                if (percentage >= 100) progressClass = 'bg-danger';
                else if (percentage >= 80) progressClass = 'bg-warning';

                const col = document.createElement('div');
                col.className = 'col';
                col.innerHTML = `
                    <div class="p-3 border rounded bg-light shadow-sm">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <span class="fw-semibold text-dark small">${categoryLabel}</span>
                            <span class="text-muted small">${percentage.toFixed(2)}%</span>
                        </div>
                        <div class="progress mb-2" style="height: 8px;">
                            <div class="progress-bar ${progressClass}" role="progressbar" style="width: ${Math.min(percentage, 100)}%"></div>
                        </div>
                        <div class="d-flex justify-content-between text-secondary small">
                            <span>Spent: ${data.base_currency || ''} ${spent.toFixed(2)}</span>
                            <span>Limit: ${data.base_currency || ''} ${limit.toFixed(2)}</span>
                        </div>
                    </div>`;
                containerElement.appendChild(col);
            });
        })
        .catch(err => {
            console.error('[Budget Thresholds] Failed to load data:', err);
            containerElement.innerHTML = '<div class="col text-center text-muted py-3 w-100">Unable to load thresholds.</div>';
        });
}

function renderEmptyChartState(canvasElement) {
    canvasElement.parentElement.innerHTML = '<div class="text-center text-muted py-5">No expenses logged.</div>';
}
