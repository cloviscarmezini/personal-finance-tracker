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
