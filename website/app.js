/**
 * Phantom OSINT — Frontend Logic
 * Handles search, API calls, result rendering,
 * toast notifications, particles, and engagement effects.
 */

// ── Configuration ──────────────────────────────────────────
// Change this to your API URL when deployed
const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : 'https://api.unknowns.app';

// ── Toast Notification System ──────────────────────────────
const toastIcons = {
    success: '✅',
    error: '❌',
    warning: '⚠️',
    info: '👻'
};

function showToast(message, type = 'info', duration = 4000) {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML =
        '<span class="toast-icon">' + (toastIcons[type] || toastIcons.info) + '</span>' +
        '<span class="toast-message">' + escHtml(message) + '</span>' +
        '<button class="toast-close" aria-label="Close">&times;</button>';

    toast.style.setProperty('--toast-duration', duration + 'ms');
    toast.querySelector('.toast-close').addEventListener('click', function () {
        dismissToast(toast);
    });

    container.appendChild(toast);

    var timer = setTimeout(function () { dismissToast(toast); }, duration);
    toast._timer = timer;
}

function dismissToast(toast) {
    if (toast._dismissed) return;
    toast._dismissed = true;
    clearTimeout(toast._timer);
    toast.classList.add('toast-exit');
    toast.addEventListener('animationend', function () {
        if (toast.parentNode) toast.parentNode.removeChild(toast);
    });
}

// ── DOM Elements (conditional — not all exist on every page) ─
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
if (searchInput) {
    searchInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') doSearch();
    });
}

// ── Clean mobile number ────────────────────────────────────
function cleanMobile(raw) {
    var digits = raw.replace(/[^\d]/g, '');
    if (digits.length === 12 && digits.startsWith('91')) digits = digits.slice(2);
    else if (digits.length === 11 && digits.startsWith('0')) digits = digits.slice(1);
    else if (digits.length === 13 && digits.startsWith('091')) digits = digits.slice(3);
    if (digits.length === 10 && '6789'.includes(digits[0])) return digits;
    return null;
}

// ── Search ─────────────────────────────────────────────────
async function doSearch() {
    var raw = searchInput.value.trim();
    if (!raw) {
        showToast('Please enter a mobile number.', 'warning');
        return;
    }

    var mobile = cleanMobile(raw);
    if (!mobile) {
        showToast('Invalid number. Enter a valid 10-digit Indian mobile.', 'error');
        showError('Invalid number. Enter a valid 10-digit Indian mobile.');
        return;
    }

    // UI state
    hideAll();
    loading.classList.add('active');
    searchBtn.disabled = true;
    showToast('Scanning 1.78B records...', 'info', 6000);

    try {
        var resp = await fetch(API_BASE + '/api/lookup?number=' + encodeURIComponent(mobile));
        var data = await resp.json();

        if (!resp.ok) {
            throw new Error((data.detail && data.detail.message) || 'API error');
        }

        renderResults(data);

        if (data.found) {
            showToast('Target located — ' + data.total_records + ' records found.', 'success');
        } else {
            showToast('No records found for ' + data.query, 'warning');
        }
    } catch (err) {
        var msg = err.message === 'Failed to fetch'
            ? 'Cannot reach API server. Make sure the API is running.'
            : err.message;
        showError(msg);
        showToast(msg, 'error');
    } finally {
        loading.classList.remove('active');
        searchBtn.disabled = false;
    }
}

// ── Render results ─────────────────────────────────────────
function renderResults(data) {
    if (!data.found) {
        resultsTitle.textContent = 'TARGET NOT FOUND';
        resultsTime.textContent = data.response_time_ms + 'ms';
        resultsBody.innerHTML =
            '<div class="not-found">' +
                '<div class="icon">❌</div>' +
                '<p>No records found for <strong>' + escHtml(data.query) + '</strong></p>' +
                '<p style="font-size: 0.8rem; margin-top: 0.5rem; color: var(--text-muted);">' +
                    'Verify the number and try again.' +
                '</p>' +
            '</div>';
        resultsStats.textContent = '0 records';
        resultsCard.classList.add('active');
        return;
    }

    // Update response time display
    if (responseTimeEl) {
        responseTimeEl.textContent = data.response_time_ms + 'ms';
    }

    resultsTitle.textContent = 'TARGET LOCATED — ' + data.total_records + ' RECORDS';
    resultsTime.textContent = '⏱ ' + data.response_time_ms + 'ms';

    var html = '';

    // Phones
    if (data.phones && data.phones.length) {
        html += '<div class="result-group">' +
            '<div class="result-label">📞 Telephones (' + data.phones.length + ')</div>' +
            '<div class="result-value">' +
                data.phones.map(function (p) { return '<span class="phone-tag">' + escHtml(p) + '</span>'; }).join('') +
            '</div></div>';
    }

    // Names
    if (data.names && data.names.length) {
        html += '<div class="result-group">' +
            '<div class="result-label">👤 Full Name</div>' +
            '<div class="result-value">' + data.names.map(function (n) { return escHtml(n); }).join('<br>') + '</div></div>';
    }

    // Father names
    if (data.father_names && data.father_names.length) {
        html += '<div class="result-group">' +
            '<div class="result-label">👨 Father\'s Name</div>' +
            '<div class="result-value">' + data.father_names.map(function (n) { return escHtml(n); }).join('<br>') + '</div></div>';
    }

    // Emails
    if (data.emails && data.emails.length) {
        html += '<div class="result-group">' +
            '<div class="result-label">📧 Email</div>' +
            '<div class="result-value">' + data.emails.map(function (e) { return escHtml(e); }).join('<br>') + '</div></div>';
    }

    // Addresses
    if (data.addresses && data.addresses.length) {
        html += '<div class="result-group">' +
            '<div class="result-label">📍 Addresses (' + data.addresses.length + ')</div>' +
            '<div class="result-value">' +
                data.addresses.map(function (a) { return '<span class="addr-block">' + escHtml(cleanAddress(a)) + '</span>'; }).join('') +
            '</div></div>';
    }

    // Regions
    if (data.regions && data.regions.length) {
        html += '<div class="result-group">' +
            '<div class="result-label">🗺️ Region</div>' +
            '<div class="result-value">' + data.regions.map(function (r) { return escHtml(r); }).join(' · ') + '</div></div>';
    }

    resultsBody.innerHTML = html;
    resultsStats.textContent = data.total_records + ' records · ' + data.total_phones + ' phones';
    resultsCard.classList.add('active');
}

// ── Helpers ────────────────────────────────────────────────
function hideAll() {
    if (resultsCard) resultsCard.classList.remove('active');
    if (errorMsg) errorMsg.classList.remove('active');
    if (loading) loading.classList.remove('active');
}

function showError(msg) {
    hideAll();
    if (errorMsg) {
        errorMsg.textContent = msg;
        errorMsg.classList.add('active');
    }
}

function escHtml(str) {
    var div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function cleanAddress(raw) {
    if (!raw) return '';
    var addr = raw.replace(/!!/g, ', ').replace(/!/g, ', ');
    addr = addr.replace(/^[, ]+/, '');
    addr = addr.replace(/[, ]{2,}/g, ', ');
    addr = addr.replace(/[, ]+$/, '');
    return addr;
}

// ── Floating Particles ─────────────────────────────────────
(function initParticles() {
    var canvas = document.getElementById('particlesCanvas');
    if (!canvas) return;
    var ctx = canvas.getContext('2d');
    var particles = [];
    var particleCount = 40;

    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    resize();
    window.addEventListener('resize', resize);

    for (var i = 0; i < particleCount; i++) {
        particles.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            radius: Math.random() * 1.5 + 0.5,
            vx: (Math.random() - 0.5) * 0.3,
            vy: (Math.random() - 0.5) * 0.3,
            alpha: Math.random() * 0.4 + 0.1
        });
    }

    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        for (var i = 0; i < particles.length; i++) {
            var p = particles[i];
            p.x += p.vx;
            p.y += p.vy;

            if (p.x < 0) p.x = canvas.width;
            if (p.x > canvas.width) p.x = 0;
            if (p.y < 0) p.y = canvas.height;
            if (p.y > canvas.height) p.y = 0;

            ctx.beginPath();
            ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(167, 139, 250, ' + p.alpha + ')';
            ctx.fill();
        }

        // Draw faint connections between nearby particles
        for (var i = 0; i < particles.length; i++) {
            for (var j = i + 1; j < particles.length; j++) {
                var dx = particles[i].x - particles[j].x;
                var dy = particles[i].y - particles[j].y;
                var dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 120) {
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.strokeStyle = 'rgba(167, 139, 250, ' + (0.06 * (1 - dist / 120)) + ')';
                    ctx.lineWidth = 0.5;
                    ctx.stroke();
                }
            }
        }

        requestAnimationFrame(draw);
    }
    draw();
})();

// ── Scroll Reveal ──────────────────────────────────────────
(function initScrollReveal() {
    var reveals = document.querySelectorAll('.reveal');
    if (!reveals.length) return;

    var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry, idx) {
            if (entry.isIntersecting) {
                // Stagger the animation for sibling elements
                var siblings = Array.from(entry.target.parentElement.querySelectorAll('.reveal'));
                var index = siblings.indexOf(entry.target);
                var delay = index * 100;
                setTimeout(function () {
                    entry.target.classList.add('revealed');
                }, delay);
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.15 });

    reveals.forEach(function (el) { observer.observe(el); });
})();

// ── Ripple Effect on Buttons ───────────────────────────────
(function initRipple() {
    document.addEventListener('click', function (e) {
        var target = e.target.closest('.ripple-effect');
        if (!target) return;

        var rect = target.getBoundingClientRect();
        var ripple = document.createElement('span');
        ripple.className = 'ripple';
        var size = Math.max(rect.width, rect.height);
        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = (e.clientX - rect.left - size / 2) + 'px';
        ripple.style.top = (e.clientY - rect.top - size / 2) + 'px';

        target.appendChild(ripple);
        ripple.addEventListener('animationend', function () {
            if (ripple.parentNode) ripple.parentNode.removeChild(ripple);
        });
    });
})();

// ── Typewriter Effect for Hero Subtitle ────────────────────
(function initTypewriter() {
    var heroP = document.querySelector('.hero > p');
    if (!heroP) return;

    var fullText = heroP.textContent;
    heroP.textContent = '';
    heroP.style.opacity = '1';

    var cursor = document.createElement('span');
    cursor.className = 'typewriter-cursor';
    heroP.appendChild(cursor);

    var charIndex = 0;
    function type() {
        if (charIndex < fullText.length) {
            heroP.insertBefore(document.createTextNode(fullText.charAt(charIndex)), cursor);
            charIndex++;
            setTimeout(type, 25);
        } else {
            // Remove cursor after typing finishes
            setTimeout(function () {
                if (cursor.parentNode) cursor.parentNode.removeChild(cursor);
            }, 2000);
        }
    }

    // Start after hero animations settle
    setTimeout(type, 800);
})();

// ── Welcome Toast on Page Load ─────────────────────────────
(function initWelcomeToast() {
    if (document.querySelector('.hero')) {
        setTimeout(function () {
            showToast('Welcome to Phantom OSINT — Intelligence awaits.', 'info', 5000);
        }, 1200);
    }
})();
