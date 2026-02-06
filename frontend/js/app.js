/* ═══════════════════════════════════════════════════
   INTELLIPLAN — PREMIUM SPA APPLICATION
   ═══════════════════════════════════════════════════ */

const API = '';
let TOKEN = null;
let ROLE = null;
let USER = null;
let NOTIF_INTERVAL = null;

/* ── Helpers ─── */
const $ = (s, p = document) => p.querySelector(s);
const $$ = (s, p = document) => [...p.querySelectorAll(s)];
const api = async (path, opts = {}) => {
    const h = { 'Content-Type': 'application/json', ...(opts.headers || {}) };
    if (TOKEN) h['Authorization'] = `Bearer ${TOKEN}`;
    const r = await fetch(API + path, { ...opts, headers: h });
    if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.detail || r.statusText); }
    return r.json();
};
const fmtDate = d => d ? new Date(d).toLocaleDateString('sv-SE') : '—';
const fmtTime = d => { if (!d) return ''; const x = new Date(d), n = Date.now() - x.getTime(); if (n < 3600000) return `${Math.floor(n / 60000)} min sedan`; if (n < 86400000) return `${Math.floor(n / 3600000)}h sedan`; return x.toLocaleDateString('sv-SE'); };
const toast = (msg, type = 'success') => {
    let c = $('.toast-container');
    if (!c) { c = document.createElement('div'); c.className = 'toast-container'; document.body.appendChild(c); }
    const t = document.createElement('div');
    t.className = `toast ${type}`;
    t.textContent = msg;
    c.appendChild(t);
    setTimeout(() => { t.style.opacity = '0'; t.style.transform = 'translateX(40px)'; setTimeout(() => t.remove(), 300); }, 3500);
};
const statusLabel = s => ({ submitted: 'Inskickad', assessed: 'Bedömd', in_progress: 'Pågående', completed: 'Klar', cancelled: 'Avbruten' }[s] || s);
const statusBadge = s => `<span class="badge badge-${s === 'in_progress' ? 'progress' : s}">${statusLabel(s)}</span>`;

/* ═══════════════════════════════════════════════════
   AUTH
   ═══════════════════════════════════════════════════ */
function fillDemo(e, p) {
    $('#login-email').value = e;
    $('#login-password').value = p;
}

$('#login-form').addEventListener('submit', async e => {
    e.preventDefault();
    const err = $('#login-error');
    err.textContent = '';
    try {
        const data = await api('/api/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email: $('#login-email').value, password: $('#login-password').value })
        });
        TOKEN = data.token;
        ROLE = data.user.role;
        USER = data.user;
        enterApp();
    } catch (ex) { err.textContent = ex.message; }
});

function enterApp() {
    $$('.view').forEach(v => v.classList.remove('active'));
    if (ROLE === 'customer') {
        $('#view-customer').classList.add('active');
        initCustomer();
    } else {
        $('#view-handler').classList.add('active');
        initHandler();
    }
    startNotifPolling();
}

function logout() {
    TOKEN = null; ROLE = null; USER = null;
    clearInterval(NOTIF_INTERVAL);
    $$('.view').forEach(v => v.classList.remove('active'));
    $('#view-login').classList.add('active');
    $('#login-email').value = '';
    $('#login-password').value = '';
}

/* ═══════════════════════════════════════════════════
   HANDLER DASHBOARD
   ═══════════════════════════════════════════════════ */
function initHandler() {
    // Set user info
    const name = USER.full_name || USER.email.split('@')[0];
    const initials = name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
    $('#user-name').textContent = name;
    $('#user-avatar').textContent = initials;
    $('#welcome-name').textContent = name.split(' ')[0];

    // Sidebar nav
    $$('.sidebar-item[data-tab]').forEach(btn => {
        btn.addEventListener('click', () => switchHandlerTab(btn.dataset.tab, btn));
    });

    // Sidebar toggle (mobile)
    $('#sidebar-toggle').addEventListener('click', toggleSidebar);

    // Notification panel
    $('#notif-btn').addEventListener('click', () => togglePanel('notif-panel'));

    // Filter chips for requests
    $$('#tab-requests .filter-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            $$('#tab-requests .filter-chip').forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            loadAllRequests(chip.dataset.filter);
        });
    });

    // Filter chips for consultants
    $$('#tab-consultants .filter-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            $$('#tab-consultants .filter-chip').forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            loadConsultants(chip.dataset.filter);
        });
    });

    // Search
    let searchTimer;
    $('#global-search').addEventListener('input', e => {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(() => applySearch(e.target.value), 300);
    });

    loadDashboard();
    loadAllRequests('all');
    loadConsultants('all');
}

function switchHandlerTab(tabId, btn) {
    // Update sidebar active
    $$('.sidebar-item[data-tab]').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    // Switch tab content
    $$('#view-handler .tab-content').forEach(t => t.classList.remove('active'));
    $(`#${tabId}`).classList.add('active');

    // Update header
    const titles = {
        'tab-overview': ['Dashboard', 'Realtidsöversikt av bemanningsoperationer'],
        'tab-requests': ['Förfrågningar', 'Hantera alla kundförfrågningar'],
        'tab-consultants': ['Konsulter', 'Konsultpool och tillgänglighet'],
        'tab-analytics': ['Analys', 'AI-prestanda och nyckeltal']
    };
    const [t, s] = titles[tabId] || ['Dashboard', ''];
    $('#page-title').textContent = t;
    $('#page-sub').textContent = s;

    // Load data for analytics
    if (tabId === 'tab-analytics') loadAnalytics();

    // Close sidebar on mobile
    closeSidebar();
}

function toggleSidebar() {
    const sb = $('#sidebar');
    sb.classList.toggle('open');
    let bd = $('.sidebar-backdrop');
    if (!bd) { bd = document.createElement('div'); bd.className = 'sidebar-backdrop'; bd.onclick = closeSidebar; document.body.appendChild(bd); }
    bd.classList.toggle('open');
}
function closeSidebar() {
    const sb = $('#sidebar');
    sb.classList.remove('open');
    const bd = $('.sidebar-backdrop');
    if (bd) bd.classList.remove('open');
}

/* ── Dashboard Stats ─── */
async function loadDashboard() {
    try {
        const s = await api('/api/dashboard/stats');
        $('#kpi-total').textContent = s.total_requests;
        $('#kpi-active').textContent = s.active_requests;
        const consText = `${s.available_consultants} / ${s.total_consultants}`;
        $('#kpi-consultants').textContent = consText;
        $('#kpi-feasibility').textContent = `${Math.round(s.feasibility_rate)}%`;
        $('#kpi-compliance').textContent = `${Math.round(s.compliance_score)}%`;

        // Progress bars
        const maxReq = Math.max(s.total_requests, 1);
        $('#kpi-total-bar').style.width = '100%';
        $('#kpi-active-bar').style.width = (s.active_requests / maxReq * 100) + '%';
        $('#kpi-cons-bar').style.width = (s.available_consultants / Math.max(s.total_consultants, 1) * 100) + '%';
        $('#kpi-feas-bar').style.width = s.feasibility_rate + '%';
        $('#kpi-comp-bar').style.width = s.compliance_score + '%';

        // Mini stats
        $('#mini-pending').textContent = s.pending_requests;
        $('#mini-active').textContent = s.active_requests;

        // Store for analytics
        window._stats = s;

        // Load overview requests
        loadOverviewRequests();
        loadActivityFeed();
    } catch (e) { console.error('Dashboard load error:', e); }
}

async function loadOverviewRequests() {
    try {
        const reqs = await api('/api/requests');
        const recent = reqs.slice(0, 5);
        const cont = $('#overview-requests');
        if (!recent.length) { cont.innerHTML = '<div class="empty-state-sm">Inga förfrågningar ännu</div>'; return; }
        cont.innerHTML = recent.map(r => requestCardHTML(r)).join('');
        cont.querySelectorAll('.request-card').forEach((card, i) => {
            card.addEventListener('click', () => openRequestDetail(recent[i].id));
        });
    } catch (e) { console.error(e); }
}

async function loadActivityFeed() {
    try {
        const notifs = await api('/api/notifications');
        const feed = $('#activity-feed');
        if (!notifs.length) { feed.innerHTML = '<div class="empty-state-sm">Inga aktiviteter ännu</div>'; return; }
        feed.innerHTML = notifs.slice(0, 10).map(n => `
            <div class="activity-item">
                <div class="activity-dot"></div>
                <div>
                    <div>${n.message}</div>
                    <div class="activity-time">${fmtTime(n.created_at)}</div>
                </div>
            </div>
        `).join('');
    } catch (e) { console.error(e); }
}

/* ── All Requests ─── */
async function loadAllRequests(filter = 'all') {
    try {
        const reqs = await api('/api/requests');
        let filtered = reqs;
        if (filter !== 'all') filtered = reqs.filter(r => r.status === filter);
        const cont = $('#all-requests');
        const count = $('#request-count');
        count.textContent = `${filtered.length} st`;
        if (!filtered.length) { cont.innerHTML = '<div class="empty-state-sm">Inga förfrågningar matchar filtret</div>'; return; }
        cont.innerHTML = filtered.map(r => requestCardHTML(r)).join('');
        cont.querySelectorAll('.request-card').forEach((card, i) => {
            card.addEventListener('click', () => openRequestDetail(filtered[i].id));
        });
    } catch (e) { console.error(e); }
}

function requestCardHTML(r) {
    const feas = r.feasibility_score != null ? `<div class="gauge-mini" style="--pct:${r.feasibility_score}"><span>${r.feasibility_score}%</span></div>` : '';
    return `
        <div class="request-card">
            <div class="request-card-left">
                <h4>${r.title}</h4>
                <div class="request-meta">
                    <span>${r.company_name || '—'}</span>
                    <span>${r.required_skills?.join(', ') || ''}</span>
                    <span>${fmtDate(r.created_at)}</span>
                </div>
            </div>
            <div class="request-card-right">
                ${feas}
                ${statusBadge(r.status)}
            </div>
        </div>
    `;
}

/* ── Request Detail Modal ─── */
async function openRequestDetail(id) {
    try {
        const data = await api(`/api/requests/${id}`);
        // Destructure nested RequestDetail response
        const r = data.request || {};
        const customer = data.customer || {};
        const assessment = data.assessment || null;
        const matchingConsultants = data.matching_consultants || [];
        const assignments = data.assignments || [];
        const timeline = data.timeline || [];

        const modal = ROLE === 'customer' ? 'cust-detail-modal' : 'detail-modal';
        const content = ROLE === 'customer' ? 'cust-detail-content' : 'detail-content';

        // Compute feasibility score from assessment
        const feasScore = assessment ? Math.round(assessment.confidence_score * 100) : null;
        const feasClass = feasScore >= 70 ? 'feas-high' : feasScore >= 40 ? 'feas-med' : 'feas-low';

        let matchHTML = '';
        if (matchingConsultants.length) {
            matchHTML = `
                <div class="modal-section">
                    <div class="modal-section-title">AI-matchade konsulter</div>
                    <div class="match-list">${matchingConsultants.map(m => `
                        <div class="match-card">
                            <div class="match-header">
                                <span class="match-name">${m.name}</span>
                                <span class="match-score">${Math.round(m.match_score)}% match</span>
                            </div>
                            <div class="match-title">${m.title || ''}</div>
                            <div class="match-skills">${(m.skills || []).map(s => `<span class="skill-tag">${s}</span>`).join('')}</div>
                            ${ROLE !== 'customer' ? `
                            <div class="match-actions">
                                <button class="btn-primary btn-sm" onclick="assignConsultant('${id}', '${m.id}')">Tilldela</button>
                            </div>` : ''}
                        </div>
                    `).join('')}</div>
                </div>
            `;
        }

        let assignHTML = '';
        if (assignments.length) {
            assignHTML = `
                <div class="modal-section">
                    <div class="modal-section-title">Tilldelningar</div>
                    <div class="assignment-list">${assignments.map(a => {
                const statusLabels = { pending: 'Väntar', confirmed: 'Godkänd', rejected: 'Nekad', sent: 'Skickad', active: 'Aktiv', ended: 'Avslutad' };
                const sLabel = statusLabels[a.status] || a.status;
                return `
                        <div class="assignment-card">
                            <div class="assignment-info">
                                <div class="assignment-name">${a.consultant_name || 'Konsult'}</div>
                                <div class="assignment-detail">${a.consultant_title || ''} · ${a.consultant_skills?.join(', ') || ''}</div>
                            </div>
                            <div class="assignment-actions">
                                <span class="badge badge-${a.status}">${sLabel}</span>
                                ${a.status === 'pending' ? `
                                    <button class="btn-approve" onclick="approveAssignment('${id}', '${a.id}')">Godkänn</button>
                                    <button class="btn-reject" onclick="rejectAssignment('${id}', '${a.id}')">Avböj</button>
                                ` : ''}
                            </div>
                        </div>`;
            }).join('')}</div>
                </div>
            `;
        }

        let timelineHTML = '';
        if (timeline.length) {
            timelineHTML = `
                <div class="modal-section">
                    <div class="modal-section-title">Tidslinje</div>
                    <div class="timeline-list">${timeline.map(t => `
                        <div class="timeline-item">
                            <div class="timeline-dot"></div>
                            <div class="timeline-body">
                                <div class="timeline-title">${t.title}</div>
                                <div class="timeline-desc">${t.description || ''}</div>
                                <div class="timeline-meta">${t.actor || ''} · ${fmtTime(t.created_at)}</div>
                            </div>
                        </div>
                    `).join('')}</div>
                </div>
            `;
        }

        let risksHTML = '';
        if (assessment && assessment.risks?.length) {
            risksHTML = `
                <div class="modal-section">
                    <div class="modal-section-title">Risker & Rekommendationer</div>
                    <div style="display:grid;gap:12px">
                        ${assessment.risks.length ? `<div><strong style="color:var(--amber)">⚠ Risker</strong><ul style="margin:6px 0 0 18px;color:var(--text-light)">${assessment.risks.map(r => `<li>${r}</li>`).join('')}</ul></div>` : ''}
                        ${assessment.recommendations?.length ? `<div><strong style="color:var(--green)">✓ Rekommendationer</strong><ul style="margin:6px 0 0 18px;color:var(--text-light)">${assessment.recommendations.map(r => `<li>${r}</li>`).join('')}</ul></div>` : ''}
                    </div>
                </div>
            `;
        }

        $(`#${content}`).innerHTML = `
            <button class="modal-close" onclick="closeModal('${modal}')">&times;</button>
            <h2>${r.title || '—'}</h2>
            <div class="modal-sub">${customer.company || ''} · ${statusLabel(r.status)} · Skapad ${fmtDate(r.created_at)}</div>

            <div class="modal-section">
                <div class="modal-section-title">Detaljer</div>
                <div class="modal-info-grid">
                    <div class="modal-info-item"><div class="modal-info-label">Beskrivning</div><div class="modal-info-value" style="font-weight:400;font-size:.88rem">${r.description || '—'}</div></div>
                    <div class="modal-info-item"><div class="modal-info-label">Kompetenser</div><div class="modal-info-value">${(Array.isArray(r.required_skills) ? r.required_skills : []).join(', ') || '—'}</div></div>
                    <div class="modal-info-item"><div class="modal-info-label">Antal</div><div class="modal-info-value">${r.number_of_consultants || '—'}</div></div>
                    <div class="modal-info-item"><div class="modal-info-label">Budget</div><div class="modal-info-value">${r.budget_max_hourly ? r.budget_max_hourly + ' SEK/h' : '—'}</div></div>
                    <div class="modal-info-item"><div class="modal-info-label">Start</div><div class="modal-info-value">${fmtDate(r.start_date)}</div></div>
                    <div class="modal-info-item"><div class="modal-info-label">Slut</div><div class="modal-info-value">${fmtDate(r.end_date)}</div></div>
                    <div class="modal-info-item"><div class="modal-info-label">Plats</div><div class="modal-info-value">${r.location || '—'}</div></div>
                    <div class="modal-info-item"><div class="modal-info-label">Distans</div><div class="modal-info-value">${r.remote_ok ? 'Ja' : 'Nej'}</div></div>
                    <div class="modal-info-item"><div class="modal-info-label">Prioritet</div><div class="modal-info-value">${r.priority || '—'}</div></div>
                    <div class="modal-info-item"><div class="modal-info-label">AI-kategori</div><div class="modal-info-value">${r.ai_category || '—'}</div></div>
                </div>
            </div>

            ${feasScore != null ? `
            <div class="modal-section">
                <div class="modal-section-title">AI Genomförbarhetsanalys</div>
                <div class="feasibility-bar-wrap">
                    <div class="feasibility-score">
                        <div class="feasibility-pct" style="color:${feasScore >= 70 ? 'var(--green)' : feasScore >= 40 ? 'var(--amber)' : 'var(--red)'}">${feasScore}%</div>
                        <div class="feasibility-label">Genomförbarhet</div>
                    </div>
                    <div class="feas-bar"><div class="feas-bar-fill ${feasClass}" style="width:${feasScore}%"></div></div>
                    <ul class="feasibility-details">
                        <li>Kompetenstäckning: ${Math.round(assessment.skills_match_score)}%</li>
                        <li>Tillgänglighet: ${Math.round(assessment.availability_score)}%</li>
                        <li>Budgetpassning: ${Math.round(assessment.budget_fit_score)}%</li>
                        <li>Tidslinje: ${Math.round(assessment.timeline_score)}%</li>
                        <li>Compliance: ${Math.round(assessment.compliance_score)}%</li>
                    </ul>
                </div>
            </div>
            ` : ''}

            ${risksHTML}
            ${matchHTML}
            ${assignHTML}
            ${timelineHTML}
        `;

        $(`#${modal}`).classList.add('open');
    } catch (e) { toast(e.message, 'error'); }
}

function closeModal(id) { $(`#${id}`).classList.remove('open'); }

// Close modals on overlay click
document.addEventListener('click', e => {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.classList.remove('open');
    }
    // Close notif panels on outside click
    const np = $('#notif-panel');
    const cnp = $('#cust-notif-panel');
    if (np && np.classList.contains('open') && !np.contains(e.target) && !$('#notif-btn').contains(e.target)) np.classList.remove('open');
    if (cnp && cnp.classList.contains('open') && !cnp.contains(e.target) && !$('#cust-notif-btn')?.contains(e.target)) cnp.classList.remove('open');
});

/* ── Assign / Approve / Reject ─── */
async function assignConsultant(reqId, consId) {
    try {
        await api(`/api/requests/${reqId}/assign/${consId}`, { method: 'POST' });
        toast('Konsult tilldelad');
        openRequestDetail(reqId);
        loadDashboard();
    } catch (e) { toast(e.message, 'error'); }
}

async function approveAssignment(reqId, aid) {
    try {
        await api(`/api/requests/${reqId}/assignments/${aid}/approve`, { method: 'PATCH' });
        toast('Tilldelning godkänd ✓');
        if (ROLE === 'customer') { loadMyRequests(); }
        closeModal('cust-detail-modal');
        closeModal('detail-modal');
    } catch (e) { toast(e.message, 'error'); }
}

async function rejectAssignment(reqId, aid) {
    try {
        await api(`/api/requests/${reqId}/assignments/${aid}/reject`, { method: 'PATCH' });
        toast('Tilldelning avböjd');
        if (ROLE === 'customer') { loadMyRequests(); }
        closeModal('cust-detail-modal');
        closeModal('detail-modal');
    } catch (e) { toast(e.message, 'error'); }
}

/* ── Consultants ─── */
async function loadConsultants(filter = 'all') {
    try {
        const url = filter !== 'all' ? `/api/consultants?status=${filter}` : '/api/consultants';
        const cons = await api(url);
        const grid = $('#consultant-grid');
        const count = $('#consultant-count');
        count.textContent = `${cons.length} st`;
        if (!cons.length) { grid.innerHTML = '<div class="empty-state-sm">Inga konsulter matchar filtret</div>'; return; }
        grid.innerHTML = cons.map(c => {
            const initials = c.name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
            const isAvail = c.status === 'available';
            return `
                <div class="consultant-card">
                    <div class="consultant-card-header">
                        <div class="cons-avatar">${initials}</div>
                        <div>
                            <div class="cons-name">${c.name}</div>
                            <div class="cons-title">${c.title || ''}</div>
                        </div>
                    </div>
                    <div class="cons-skills">${(c.skills || []).slice(0, 6).map(s => `<span class="skill-tag">${s}</span>`).join('')}</div>
                    <div class="cons-status">
                        <span class="status-dot ${isAvail ? 'available' : 'assigned'}"></span>
                        <span>${isAvail ? 'Ledig' : 'Tilldelad'}</span>
                        ${c.hourly_rate ? `<span style="margin-left:auto;color:var(--text-faint);font-size:.75rem">${c.hourly_rate} SEK/h</span>` : ''}
                    </div>
                </div>
            `;
        }).join('');
    } catch (e) { console.error(e); }
}

/* ── Analytics ─── */
async function loadAnalytics() {
    const s = window._stats;
    if (!s) { await loadDashboard(); return loadAnalytics(); }

    // Status chart bars
    const chartData = [
        { label: 'Inskickade', value: s.pending_requests, cls: 'bar-blue' },
        { label: 'Bedömda', value: Math.max(s.total_requests - s.pending_requests - s.active_requests - s.completed_requests, 0), cls: 'bar-amber' },
        { label: 'Pågående', value: s.active_requests, cls: 'bar-green' },
        { label: 'Klara', value: s.completed_requests, cls: 'bar-purple' }
    ];
    const maxVal = Math.max(...chartData.map(d => d.value), 1);
    $('#chart-status').innerHTML = chartData.map(d => `
        <div class="chart-bar-item">
            <div class="chart-bar-label">${d.label}</div>
            <div class="chart-bar-track">
                <div class="chart-bar-fill ${d.cls}" style="width:${(d.value / maxVal * 100)}%">${d.value}</div>
            </div>
        </div>
    `).join('');

    // Donut
    const avail = s.available_consultants;
    const assigned = s.total_consultants - avail;
    const availPct = Math.round(avail / Math.max(s.total_consultants, 1) * 100);
    const assignPct = 100 - availPct;
    $('#chart-availability').innerHTML = `
        <div class="donut" style="background:conic-gradient(var(--green) 0 ${availPct * 3.6}deg, var(--amber) ${availPct * 3.6}deg 360deg)">
            <div class="donut-center">
                <span class="donut-val">${s.total_consultants}</span>
                <span class="donut-lbl">Totalt</span>
            </div>
        </div>
        <div class="donut-legend">
            <div class="legend-item"><div class="legend-dot" style="background:var(--green)"></div>Lediga (${avail})</div>
            <div class="legend-item"><div class="legend-dot" style="background:var(--amber)"></div>Tilldelade (${assigned})</div>
        </div>
    `;

    // AI Metrics
    $('#ai-metrics').innerHTML = `
        <div class="metric-item"><div class="metric-item-value">${s.total_requests}</div><div class="metric-item-label">Analyserade</div></div>
        <div class="metric-item"><div class="metric-item-value">${Math.round(s.feasibility_rate)}%</div><div class="metric-item-label">Genomförbarhet</div></div>
        <div class="metric-item"><div class="metric-item-value">${s.total_consultants}</div><div class="metric-item-label">Konsultpool</div></div>
        <div class="metric-item"><div class="metric-item-value">${s.active_requests}</div><div class="metric-item-label">Aktiva</div></div>
    `;

    // Big metrics
    $('#analytics-compliance').textContent = Math.round(s.compliance_score);
}

/* ── Search ─── */
function applySearch(q) {
    const query = q.toLowerCase().trim();
    // Search in visible request cards
    $$('.request-card').forEach(card => {
        const text = card.textContent.toLowerCase();
        card.style.display = text.includes(query) ? '' : 'none';
    });
    // Search in visible consultant cards
    $$('.consultant-card').forEach(card => {
        const text = card.textContent.toLowerCase();
        card.style.display = text.includes(query) ? '' : 'none';
    });
}

/* ═══════════════════════════════════════════════════
   NOTIFICATIONS
   ═══════════════════════════════════════════════════ */
function togglePanel(id) {
    const p = $(`#${id}`);
    p.classList.toggle('open');
    if (p.classList.contains('open')) loadNotifications();
}

async function loadNotifications() {
    try {
        const notifs = await api('/api/notifications');
        const unread = notifs.filter(n => !n.is_read).length;

        // Update badges
        const badge = ROLE === 'customer' ? $('#cust-notif-badge') : $('#notif-badge');
        if (badge) {
            badge.textContent = unread;
            badge.style.display = unread > 0 ? '' : 'none';
        }

        // Render list
        const listId = ROLE === 'customer' ? 'cust-notif-list' : 'notif-list';
        const list = $(`#${listId}`);
        if (!list) return;
        if (!notifs.length) { list.innerHTML = '<div class="empty-state-sm">Inga notifikationer</div>'; return; }
        list.innerHTML = notifs.slice(0, 20).map(n => `
            <div class="notif-item ${n.is_read ? '' : 'unread'}" onclick="readNotif('${n.id}')">
                <div class="notif-text">${n.message}</div>
                <div class="notif-time">${fmtTime(n.created_at)}</div>
            </div>
        `).join('');
    } catch (e) { console.error(e); }
}

async function readNotif(id) {
    try { await api(`/api/notifications/${id}/read`, { method: 'PATCH' }); loadNotifications(); } catch (e) { }
}

async function markAllRead() {
    try { await api('/api/notifications/mark-all-read', { method: 'POST' }); loadNotifications(); toast('Alla markerade som lästa'); } catch (e) { }
}

function startNotifPolling() {
    clearInterval(NOTIF_INTERVAL);
    loadNotifications();
    NOTIF_INTERVAL = setInterval(loadNotifications, 15000);
}

/* ═══════════════════════════════════════════════════
   CUSTOMER PORTAL
   ═══════════════════════════════════════════════════ */
function initCustomer() {
    const name = USER.full_name || USER.email.split('@')[0];
    const initials = name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
    if ($('#cust-avatar')) $('#cust-avatar').textContent = initials;
    if ($('#cust-name')) $('#cust-name').textContent = name;

    // Nav tabs
    $$('.nav-tab[data-tab]').forEach(tab => {
        tab.addEventListener('click', () => {
            $$('.nav-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            $$('#view-customer > .tab-content').forEach(t => t.classList.remove('active'));
            $(`#${tab.dataset.tab}`).classList.add('active');
            if (tab.dataset.tab === 'cust-my') loadMyRequests();
        });
    });

    // Notif panel
    if ($('#cust-notif-btn')) {
        $('#cust-notif-btn').addEventListener('click', () => togglePanel('cust-notif-panel'));
    }

    // Form submit
    $('#cust-request-form').addEventListener('submit', submitRequest);

    loadMyRequests();
}

async function submitRequest(e) {
    e.preventDefault();
    const btn = e.target.querySelector('.btn-primary');
    const btnText = btn.querySelector('.btn-text');
    const btnLoad = btn.querySelector('.btn-loading');
    btnText.style.display = 'none';
    btnLoad.style.display = 'inline-flex';
    btn.disabled = true;

    try {
        const body = {
            title: $('#cr-title').value,
            description: $('#cr-desc').value,
            required_skills: $('#cr-skills').value ? $('#cr-skills').value.split(',').map(s => s.trim()).filter(Boolean) : [],
            number_of_consultants: parseInt($('#cr-count').value) || 1,
            start_date: $('#cr-start').value || null,
            end_date: $('#cr-end').value || null,
            budget_max_hourly: parseInt($('#cr-budget').value) || null,
            location: $('#cr-location').value || null,
            remote_ok: $('#cr-remote').checked
        };

        const result = await api('/api/requests', { method: 'POST', body: JSON.stringify(body) });
        toast('Förfrågan skapad — AI-analys klar!');

        // Show result
        showRequestResult(result);

        // Reset form
        e.target.reset();
    } catch (ex) {
        toast(ex.message, 'error');
    } finally {
        btnText.style.display = '';
        btnLoad.style.display = 'none';
        btn.disabled = false;
    }
}

function showRequestResult(r) {
    const col = $('#cust-result');
    const feasScore = r.ai_complexity_score != null ? Math.round(r.ai_complexity_score * 100) : null;
    const feasClass = feasScore >= 70 ? 'feas-high' : feasScore >= 40 ? 'feas-med' : 'feas-low';

    col.innerHTML = `
        <div class="result-card glass">
            <h3>📊 AI-analys klar</h3>
            ${feasScore != null ? `
            <div class="feasibility-bar-wrap" style="background:none;border:none;padding:8px 0">
                <div class="feasibility-score">
                    <div class="feasibility-pct" style="color:${feasScore >= 70 ? 'var(--green)' : feasScore >= 40 ? 'var(--amber)' : 'var(--red)'}">${feasScore}%</div>
                    <div class="feasibility-label">Komplexitetsbedömning</div>
                </div>
                <div class="feas-bar"><div class="feas-bar-fill ${feasClass}" style="width:${feasScore}%"></div></div>
            </div>` : ''}
            <div style="margin-top:8px;color:var(--text-light);font-size:.88rem">
                ${r.ai_summary || ''}
            </div>
            <div style="margin-top:8px;font-size:.82rem;color:var(--text-faint)">
                Kategori: ${r.ai_category || '—'}
            </div>
        </div>
    `;
}

async function loadMyRequests() {
    try {
        const reqs = await api('/api/requests');
        const cont = $('#my-requests');
        if (!reqs.length) { cont.innerHTML = '<div class="empty-state-sm">Du har inga förfrågningar ännu. Skapa en ny!</div>'; return; }
        cont.innerHTML = reqs.map(r => requestCardHTML(r)).join('');
        cont.querySelectorAll('.request-card').forEach((card, i) => {
            card.addEventListener('click', () => openRequestDetail(reqs[i].id));
        });
    } catch (e) { console.error(e); }
}
