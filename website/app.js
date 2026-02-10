/**
 * Phantom OSINT — Frontend Logic
 * Handles search, API calls, and result rendering.
 */

// ── Configuration ──────────────────────────────────────────
// Change this to your API URL when deployed
const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : 'https://api.unknowns.app';

// ── DOM Elements ───────────────────────────────────────────
const searchInput = document.getElementById('searchInput');
const searchBtn = document.getElementById('searchBtn');
const loading = document.getElementById('loading');
const errorMsg = document.getElementById('errorMsg');
const resultsCard = document.getElementById('resultsCard');
const resultsTitle = document.getElementById('resultsTitle');
const resultsTime = document.getElementById('resultsTime');
const resultsBody = document.getElementById('resultsBody');
const resultsStats = document.getElementById('resultsStats');
const responseTimeEl = document.getElementById('responseTime');

// ── Enter key support ──────────────────────────────────────
searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') doSearch();
});

// ── Clean mobile number ────────────────────────────────────
function cleanMobile(raw) {
    let digits = raw.replace(/[^\d]/g, '');
    if (digits.length === 12 && digits.startsWith('91')) digits = digits.slice(2);
    else if (digits.length === 11 && digits.startsWith('0')) digits = digits.slice(1);
    else if (digits.length === 13 && digits.startsWith('091')) digits = digits.slice(3);
    if (digits.length === 10 && '6789'.includes(digits[0])) return digits;
    return null;
}

// ── Search ─────────────────────────────────────────────────
async function doSearch() {
    const raw = searchInput.value.trim();
    if (!raw) return;

    const mobile = cleanMobile(raw);
    if (!mobile) {
        showError('Invalid number. Enter a valid 10-digit Indian mobile.');
        return;
    }

    // UI state
    hideAll();
    loading.classList.add('active');
    searchBtn.disabled = true;

    try {
        const resp = await fetch(`${API_BASE}/api/lookup?number=${mobile}`);
        const data = await resp.json();

        if (!resp.ok) {
            throw new Error(data.detail?.message || 'API error');
        }

        renderResults(data);
    } catch (err) {
        showError(err.message === 'Failed to fetch'
            ? 'Cannot reach API server. Make sure the API is running.'
            : err.message
        );
    } finally {
        loading.classList.remove('active');
        searchBtn.disabled = false;
    }
}

// ── Render results ─────────────────────────────────────────
function renderResults(data) {
    if (!data.found) {
        resultsTitle.textContent = 'TARGET NOT FOUND';
        resultsTime.textContent = `${data.response_time_ms}ms`;
        resultsBody.innerHTML = `
            <div class="not-found">
                <div class="icon">❌</div>
                <p>No records found for <strong>${escHtml(data.query)}</strong></p>
                <p style="font-size: 0.8rem; margin-top: 0.5rem; color: var(--text-muted);">
                    Verify the number and try again.
                </p>
            </div>
        `;
        resultsStats.textContent = '0 records';
        resultsCard.classList.add('active');
        return;
    }

    // Update response time display
    if (responseTimeEl) {
        responseTimeEl.textContent = `${data.response_time_ms}ms`;
    }

    resultsTitle.textContent = `TARGET LOCATED — ${data.total_records} RECORDS`;
    resultsTime.textContent = `⏱ ${data.response_time_ms}ms`;

    let html = '';

    // Phones
    if (data.phones && data.phones.length) {
        html += `<div class="result-group">
            <div class="result-label">📞 Telephones (${data.phones.length})</div>
            <div class="result-value">
                ${data.phones.map(p => `<span class="phone-tag">${escHtml(p)}</span>`).join('')}
            </div>
        </div>`;
    }

    // Names
    if (data.names && data.names.length) {
        html += `<div class="result-group">
            <div class="result-label">👤 Full Name</div>
            <div class="result-value">${data.names.map(n => escHtml(n)).join('<br>')}</div>
        </div>`;
    }

    // Father names
    if (data.father_names && data.father_names.length) {
        html += `<div class="result-group">
            <div class="result-label">👨 Father's Name</div>
            <div class="result-value">${data.father_names.map(n => escHtml(n)).join('<br>')}</div>
        </div>`;
    }

    // Emails
    if (data.emails && data.emails.length) {
        html += `<div class="result-group">
            <div class="result-label">📧 Email</div>
            <div class="result-value">${data.emails.map(e => escHtml(e)).join('<br>')}</div>
        </div>`;
    }

    // Addresses
    if (data.addresses && data.addresses.length) {
        html += `<div class="result-group">
            <div class="result-label">📍 Addresses (${data.addresses.length})</div>
            <div class="result-value">
                ${data.addresses.map(a => `<span class="addr-block">${escHtml(cleanAddress(a))}</span>`).join('')}
            </div>
        </div>`;
    }

    // Regions
    if (data.regions && data.regions.length) {
        html += `<div class="result-group">
            <div class="result-label">🗺️ Region</div>
            <div class="result-value">${data.regions.map(r => escHtml(r)).join(' · ')}</div>
        </div>`;
    }

    resultsBody.innerHTML = html;
    resultsStats.textContent = `${data.total_records} records · ${data.total_phones} phones`;
    resultsCard.classList.add('active');
}

// ── Helpers ────────────────────────────────────────────────
function hideAll() {
    resultsCard.classList.remove('active');
    errorMsg.classList.remove('active');
    loading.classList.remove('active');
}

function showError(msg) {
    hideAll();
    errorMsg.textContent = msg;
    errorMsg.classList.add('active');
}

function escHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function cleanAddress(raw) {
    if (!raw) return '';
    let addr = raw.replace(/!!/g, ', ').replace(/!/g, ', ');
    addr = addr.replace(/^[, ]+/, '');
    addr = addr.replace(/[, ]{2,}/g, ', ');
    addr = addr.replace(/[, ]+$/, '');
    return addr;
}
