/**
 * Intelliplan 2.0 — Premium Frontend
 * Auth + Customer Portal + Handler Dashboard + Notifications
 */

const API = '';
let currentUser = null;
let authToken = null;
let notifInterval = null;

// ═══════════════════════════════════════════════════
//  INIT
// ═══════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    // Check stored session
    const stored = localStorage.getItem('intelliplan_session');
    if (stored) {
        try {
            const s = JSON.parse(stored);
            authToken = s.token;
            currentUser = s.user;
            enterApp();
        } catch { showView('login'); }
    } else {
        showView('login');
    }

    // Login form
    document.getElementById('login-form').addEventListener('submit', handleLogin);

    // Tab navigation for both views
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const parent = tab.closest('.view');
            parent.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            const target = tab.dataset.tab;
            parent.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
            document.getElementById(target).classList.add('active');
            // Load data as needed
            if (target === 'tab-consultants') loadConsultants();
            if (target === 'tab-requests') loadAllRequests();
            if (target === 'cust-my') loadMyRequests();
        });
    });

    // Customer request form
    document.getElementById('cust-request-form').addEventListener('submit', handleCustomerRequest);

    // Notification buttons
    document.getElementById('notif-btn')?.addEventListener('click', () => toggleNotifPanel('notif-panel'));
    document.getElementById('cust-notif-btn')?.addEventListener('click', () => toggleNotifPanel('cust-notif-panel'));

    // Close modals on overlay click
    document.querySelectorAll('.modal-overlay').forEach(o => {
        o.addEventListener('click', e => { if (e.target === o) o.classList.remove('open'); });
    });
});

// ═══════════════════════════════════════════════════
//  AUTH
// ═══════════════════════════════════════════════════

function fillDemo(email, password) {
    document.getElementById('login-email').value = email;
    document.getElementById('login-password').value = password;
}

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    const errEl = document.getElementById('login-error');
    errEl.textContent = '';

    try {
        const res = await fetch(`${API}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
        });
        if (!res.ok) {
            const err = await res.json();
            errEl.textContent = err.detail || 'Inloggning misslyckades';
            return;
        }
        const data = await res.json();
        authToken = data.token;
        currentUser = data.user;
        localStorage.setItem('intelliplan_session', JSON.stringify(data));
        enterApp();
    } catch (err) {
        errEl.textContent = 'Kunde inte ansluta till servern';
    }
}

function logout() {
    fetch(`${API}/api/auth/logout`, {
        method: 'POST',
        headers: authHeaders(),
    }).catch(() => { });
    authToken = null;
    currentUser = null;
    localStorage.removeItem('intelliplan_session');
    if (notifInterval) clearInterval(notifInterval);
    showView('login');
}

function authHeaders() {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`,
    };
}

function enterApp() {
    if (currentUser.role === 'customer') {
        showView('customer');
        setupCustomerPortal();
    } else {
        showView('handler');
        setupHandlerDashboard();
    }
    // Start notification polling
    loadNotifications();
    if (notifInterval) clearInterval(notifInterval);
    notifInterval = setInterval(loadNotifications, 10000);
}

function showView(name) {
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.getElementById(`view-${name}`).classList.add('active');
}

// ═══════════════════════════════════════════════════
//  NOTIFICATIONS
// ═══════════════════════════════════════════════════

async function loadNotifications() {
    if (!authToken) return;
    try {
        const [notifsRes, countRes] = await Promise.all([
            fetch(`${API}/api/notifications`, { headers: authHeaders() }),
            fetch(`${API}/api/notifications/unread-count`, { headers: authHeaders() }),
        ]);
        const notifs = await notifsRes.json();
        const { count } = await countRes.json();

        // Update badges
        const badges = ['notif-badge', 'cust-notif-badge'];
        badges.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.style.display = count > 0 ? 'inline-block' : 'none';
                el.textContent = count;
            }
        });

        // Render lists
        const lists = ['notif-list', 'cust-notif-list'];
        lists.forEach(id => {
            const el = document.getElementById(id);
            if (!el) return;
            if (notifs.length === 0) {
                el.innerHTML = '<div class="notif-empty">Inga notifikationer</div>';
                return;
            }
            el.innerHTML = notifs.map(n => `
                <div class="notif-item ${n.is_read ? '' : 'unread'}" onclick="handleNotifClick('${n.id}', '${n.link || ''}')">
                    <div class="notif-item-title">${esc(n.title)}</div>
                    <div class="notif-item-msg">${esc(n.message)}</div>
                    <div class="notif-item-time">${timeAgo(n.created_at)}</div>
                </div>
            `).join('');
        });
    } catch { }
}

async function handleNotifClick(notifId, link) {
    // Mark as read
    await fetch(`${API}/api/notifications/${notifId}/read`, {
        method: 'PATCH',
        headers: authHeaders(),
    }).catch(() => { });

    // Close panels
    document.querySelectorAll('.notif-panel').forEach(p => p.classList.remove('open'));

    // Navigate to request if link provided
    if (link) {
        openRequestDetail(link);
    }

    loadNotifications();
}

async function markAllRead() {
    await fetch(`${API}/api/notifications/mark-all-read`, {
        method: 'POST',
        headers: authHeaders(),
    }).catch(() => { });
    loadNotifications();
    toast('Alla notifikationer markerade som lästa', 'success');
}

function toggleNotifPanel(panelId) {
    const panel = document.getElementById(panelId);
    panel.classList.toggle('open');
    // Close other panels
    document.querySelectorAll('.notif-panel').forEach(p => {
        if (p.id !== panelId) p.classList.remove('open');
    });
}

// ═══════════════════════════════════════════════════
//  HANDLER DASHBOARD
// ═══════════════════════════════════════════════════

async function setupHandlerDashboard() {
    // Set user info
    const initials = currentUser.full_name.split(' ').map(n => n[0]).join('').toUpperCase();
    document.getElementById('user-avatar').textContent = initials;
    document.getElementById('user-name').textContent = currentUser.full_name.split(' ')[0];

    loadDashboardStats();
    loadOverviewRequests();
}

async function loadDashboardStats() {
    try {
        const res = await fetch(`${API}/api/dashboard/stats`);
        const s = await res.json();
        document.getElementById('kpi-total').textContent = s.total_requests;
        document.getElementById('kpi-active').textContent = s.active_requests;
        document.getElementById('kpi-consultants').textContent = `${s.available_consultants}/${s.total_consultants}`;
        document.getElementById('kpi-feasibility').textContent = `${Math.round(s.feasibility_rate * 100)}%`;
        document.getElementById('kpi-compliance').textContent = `${s.compliance_score || 0}%`;
    } catch { }
}

async function loadOverviewRequests() {
    try {
        const res = await fetch(`${API}/api/requests`);
        const requests = await res.json();
        document.getElementById('overview-requests').innerHTML = requests.slice(0, 10).map(r => renderRequestCard(r)).join('');
    } catch { }
}

async function loadAllRequests() {
    try {
        const res = await fetch(`${API}/api/requests`);
        const requests = await res.json();
        document.getElementById('all-requests').innerHTML = requests.map(r => renderRequestCard(r)).join('');
    } catch { }
}

function renderRequestCard(r) {
    const skills = Array.isArray(r.required_skills) ? r.required_skills : [];
    const skillsStr = skills.slice(0, 3).join(', ') || 'AI-analyserad';
    const date = new Date(r.created_at).toLocaleDateString('sv-SE');
    return `
        <div class="request-card glass" onclick="openRequestDetail('${r.id}')">
            <div class="req-info">
                <h4>${esc(r.title)}</h4>
                <div class="req-meta">
                    <span>${skillsStr}</span>
                    <span>${date}</span>
                    <span>${r.number_of_consultants} konsult${r.number_of_consultants > 1 ? 'er' : ''}</span>
                </div>
            </div>
            <div class="req-badges">
                <span class="badge badge-${r.status}">${statusLabel(r.status)}</span>
                <span class="badge badge-${r.priority}">${r.priority}</span>
            </div>
            <div class="req-arrow">→</div>
        </div>
    `;
}

// ═══════════════════════════════════════════════════
//  REQUEST DETAIL MODAL
// ═══════════════════════════════════════════════════

async function openRequestDetail(requestId) {
    const modalId = currentUser.role === 'customer' ? 'cust-detail-modal' : 'detail-modal';
    const contentId = currentUser.role === 'customer' ? 'cust-detail-content' : 'detail-content';

    try {
        const res = await fetch(`${API}/api/requests/${requestId}`);
        if (!res.ok) throw new Error('Not found');
        const d = await res.json();

        const r = d.request;
        const a = d.assessment;
        const skills = Array.isArray(r.required_skills) ? r.required_skills : [];

        let html = `
            <button class="modal-close" onclick="this.closest('.modal-overlay').classList.remove('open')">×</button>
            <h2>${esc(r.title)}</h2>
            <div class="modal-company">${esc(d.customer.company)} — ${esc(d.customer.name)}</div>

            <div class="detail-grid">
                <!-- AI Summary -->
                <div class="detail-section full-width">
                    <h3>🤖 AI-analys</h3>
                    <div class="result-summary">${esc(r.ai_summary || 'Ingen analys tillgänglig')}</div>
                    <div style="display:flex;gap:16px;flex-wrap:wrap;">
                        <div><span class="detail-label">Kategori</span><div class="detail-value">${esc(r.ai_category || '—')}</div></div>
                        <div><span class="detail-label">Komplexitet</span><div class="detail-value">${r.ai_complexity_score ? Math.round(r.ai_complexity_score * 100) + '%' : '—'}</div></div>
                        <div><span class="detail-label">Status</span><div class="detail-value"><span class="badge badge-${r.status}">${statusLabel(r.status)}</span></div></div>
                        <div><span class="detail-label">Prioritet</span><div class="detail-value"><span class="badge badge-${r.priority}">${r.priority}</span></div></div>
                    </div>
                </div>

                <!-- Request details -->
                <div class="detail-section">
                    <h3>📋 Förfrågan</h3>
                    <div class="detail-label">Beskrivning</div>
                    <div class="detail-value">${esc(r.description)}</div>
                    <div class="detail-label">Kompetenser</div>
                    <div class="detail-value">${skills.length > 0 ? skills.map(s => `<span class="skill-tag">${esc(s)}</span>`).join(' ') : '—'}</div>
                    <div class="detail-label">Antal</div>
                    <div class="detail-value">${r.number_of_consultants}</div>
                    ${r.location ? `<div class="detail-label">Plats</div><div class="detail-value">${esc(r.location)}${r.remote_ok ? ' (distans OK)' : ''}</div>` : ''}
                    ${r.budget_max_hourly ? `<div class="detail-label">Budget</div><div class="detail-value">Max ${r.budget_max_hourly} SEK/h</div>` : ''}
                </div>
        `;

        // Feasibility assessment
        if (a) {
            const rating = a.overall_rating;
            const risks = Array.isArray(a.risks) ? a.risks : (typeof a.risks === 'string' ? JSON.parse(a.risks || '[]') : []);
            const recs = Array.isArray(a.recommendations) ? a.recommendations : (typeof a.recommendations === 'string' ? JSON.parse(a.recommendations || '[]') : []);
            const alts = Array.isArray(a.alternatives) ? a.alternatives : (typeof a.alternatives === 'string' ? JSON.parse(a.alternatives || '[]') : []);

            html += `
                <div class="detail-section">
                    <h3>📊 Genomförbarhet <span class="ai-badge ai-badge-${rating}">${feasibilityLabel(rating)}</span></h3>
                    ${gaugeRow('Tillgänglighet', a.availability_score)}
                    ${gaugeRow('Kompetens', a.skills_match_score)}
                    ${gaugeRow('Budget', a.budget_fit_score)}
                    ${gaugeRow('Tidslinje', a.timeline_score)}
                    ${gaugeRow('Compliance', a.compliance_score)}
                    <div style="margin-top:12px;font-size:13px;color:var(--text-muted);">
                        Konfidensgrad: ${Math.round((a.confidence_score || 0) * 100)}%
                    </div>
                </div>
            `;

            // Recommendations
            if (recs.length > 0) {
                html += `
                    <div class="detail-section full-width">
                        <h3>💡 AI-rekommendationer</h3>
                        ${recs.map(r => `<div class="insight-item">${esc(r)}</div>`).join('')}
                    </div>
                `;
            }
        }

        // Matching consultants
        const assignedConsultantIds = (d.assignments || []).map(a => a.consultant_id);
        if (d.matching_consultants && d.matching_consultants.length > 0) {
            html += `
                <div class="detail-section full-width">
                    <h3>👥 Matchande konsulter (${d.matching_consultants.length})</h3>
                    ${d.matching_consultants.map(c => renderMatchCard(c, r.id, skills, assignedConsultantIds)).join('')}
                </div>
            `;
        }

        // Assignments
        if (d.assignments && d.assignments.length > 0) {
            html += `
                <div class="detail-section full-width">
                    <h3>📌 Tilldelade konsulter (${d.assignments.length})</h3>
                    ${d.assignments.map(a => renderAssignmentCard(a, r.id)).join('')}
                </div>
            `;
        }

        // Actions
        if (d.actions && d.actions.length > 0) {
            html += `
                <div class="detail-section">
                    <h3>⚡ Koordinationsplan</h3>
                    ${d.actions.map(a => `
                        <div class="action-item">
                            <div class="action-icon ${a.status === 'completed' ? 'action-done' : 'action-pending'}">
                                ${a.status === 'completed' ? '✓' : '○'}
                            </div>
                            <div>
                                <div style="font-weight:500">${esc(a.description)}</div>
                                ${a.result ? `<div style="font-size:12px;color:var(--text-muted);margin-top:2px">${esc(a.result)}</div>` : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        // Timeline
        if (d.timeline && d.timeline.length > 0) {
            html += `
                <div class="detail-section">
                    <h3>📅 Tidslinje</h3>
                    ${d.timeline.map(t => `
                        <div class="timeline-item">
                            <div class="timeline-dot"></div>
                            <div>
                                <div style="font-weight:500">${esc(t.title)}</div>
                                ${t.description ? `<div style="font-size:13px;color:var(--text-secondary)">${esc(t.description)}</div>` : ''}
                                <div class="timeline-time">${timeAgo(t.created_at)} — ${esc(t.actor || 'System')}</div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        html += '</div>'; // close detail-grid

        document.getElementById(contentId).innerHTML = html;
        document.getElementById(modalId).classList.add('open');
    } catch (err) {
        toast('Kunde inte ladda förfrågan', 'error');
    }
}

function renderMatchCard(c, requestId, requiredSkills, assignedConsultantIds = []) {
    const scoreClass = c.match_score >= 70 ? 'score-high' : c.match_score >= 40 ? 'score-medium' : 'score-low';
    const cSkills = Array.isArray(c.skills) ? c.skills : [];
    const reqLower = requiredSkills.map(s => s.toLowerCase());

    const skillTags = cSkills.map(s => {
        if (reqLower.includes(s.toLowerCase())) return `<span class="skill-match skill-hit">${esc(s)}</span>`;
        return `<span class="skill-match skill-extra">${esc(s)}</span>`;
    }).join('');

    const missedTags = (c.missing_skills || []).map(s =>
        `<span class="skill-match skill-miss">${esc(s)}</span>`
    ).join('');

    const isHandler = currentUser && currentUser.role !== 'customer';
    const isAssigned = assignedConsultantIds.includes(c.id);

    let actionHtml = '';
    if (isHandler && isAssigned) {
        actionHtml = `<span class="assignment-badge badge-sent">✓ Tilldelad</span>`;
    } else if (isHandler) {
        actionHtml = `<button class="match-assign-btn" onclick="assignConsultant('${requestId}', '${c.id}')">Tilldela konsult</button>`;
    }

    return `
        <div class="match-card ${isAssigned ? 'match-card-assigned' : ''}">
            <div class="match-header">
                <div>
                    <div class="match-name">${esc(c.name)}</div>
                    <div class="match-title">${esc(c.title || '')} — ${c.hourly_rate} SEK/h</div>
                </div>
                <span class="match-score ${scoreClass}">${Math.round(c.match_score)}% match</span>
            </div>
            <div class="match-skills">${skillTags}${missedTags}</div>
            ${actionHtml}
        </div>
    `;
}

function renderAssignmentCard(a, requestId) {
    const statusMap = {
        proposed: { label: 'Föreslagen', cls: 'badge-proposed' },
        sent: { label: 'Skickad till konsult', cls: 'badge-sent' },
        confirmed: { label: 'Godkänd ✓', cls: 'badge-confirmed' },
        rejected: { label: 'Avböjd', cls: 'badge-rejected' },
        active: { label: 'Aktiv', cls: 'badge-active' },
        ended: { label: 'Avslutad', cls: 'badge-ended' },
    };
    const st = statusMap[a.status] || { label: a.status, cls: '' };
    const skills = (a.consultant_skills || []).map(s => `<span class="skill-tag">${esc(s)}</span>`).join(' ');

    const isHandler = currentUser && currentUser.role !== 'customer';
    const canApprove = isHandler && (a.status === 'sent' || a.status === 'proposed');

    return `
        <div class="assignment-card">
            <div class="assignment-header">
                <div class="assignment-consultant-info">
                    <div class="assignment-avatar">${esc(a.consultant_name.charAt(0))}</div>
                    <div>
                        <div class="assignment-name">${esc(a.consultant_name)}</div>
                        <div class="assignment-title">${esc(a.consultant_title || '')} — ${a.hourly_rate} SEK/h</div>
                    </div>
                </div>
                <span class="assignment-badge ${st.cls}">${st.label}</span>
            </div>
            ${skills ? `<div class="assignment-skills">${skills}</div>` : ''}
            ${canApprove ? `
                <div class="assignment-actions">
                    <button class="btn-approve" onclick="approveAssignment('${requestId}', '${a.id}')">
                        ✓ Godkänn (konsult accepterar)
                    </button>
                    <button class="btn-reject" onclick="rejectAssignment('${requestId}', '${a.id}')">
                        ✕ Avböj (konsult nekar)
                    </button>
                </div>
            ` : ''}
            <div class="assignment-meta">Tilldelad ${timeAgo(a.created_at)}</div>
        </div>
    `;
}

async function approveAssignment(requestId, assignmentId) {
    try {
        const res = await fetch(`${API}/api/requests/${requestId}/assignments/${assignmentId}/approve`, {
            method: 'PATCH',
            headers: authHeaders(),
        });
        if (res.ok) {
            toast('Konsult godkände uppdraget!', 'success');
            openRequestDetail(requestId);
            loadDashboardStats();
        } else {
            toast('Kunde inte godkänna', 'error');
        }
    } catch {
        toast('Serverfel', 'error');
    }
}

async function rejectAssignment(requestId, assignmentId) {
    try {
        const res = await fetch(`${API}/api/requests/${requestId}/assignments/${assignmentId}/reject`, {
            method: 'PATCH',
            headers: authHeaders(),
        });
        if (res.ok) {
            toast('Konsult avböjde uppdraget', 'warning');
            openRequestDetail(requestId);
            loadDashboardStats();
        } else {
            toast('Kunde inte avböja', 'error');
        }
    } catch {
        toast('Serverfel', 'error');
    }
}

// ═══════════════════════════════════════════════════
//  CONSULTANTS
// ═══════════════════════════════════════════════════

async function loadConsultants() {
    try {
        const res = await fetch(`${API}/api/consultants`);
        const consultants = await res.json();
        document.getElementById('consultant-grid').innerHTML = consultants.map(c => {
            const skills = Array.isArray(c.skills) ? c.skills : [];
            const statusClass = c.status.replace(' ', '_');
            return `
                <div class="consultant-card glass">
                    <div class="cons-header">
                        <div>
                            <div class="cons-name">${esc(c.name)}</div>
                            <div class="cons-title">${esc(c.title || '')}</div>
                        </div>
                        <span class="cons-status status-${statusClass}">${consultantStatusLabel(c.status)}</span>
                    </div>
                    <div class="cons-rate">${c.hourly_rate} SEK/h</div>
                    <div class="cons-skills">${skills.map(s => `<span class="skill-tag">${esc(s)}</span>`).join('')}</div>
                </div>
            `;
        }).join('');
    } catch { }
}

// ═══════════════════════════════════════════════════
//  CUSTOMER PORTAL
// ═══════════════════════════════════════════════════

function setupCustomerPortal() {
    const initials = currentUser.full_name.split(' ').map(n => n[0]).join('').toUpperCase();
    document.getElementById('cust-avatar').textContent = initials;
    document.getElementById('cust-name').textContent = currentUser.full_name.split(' ')[0];
}

async function handleCustomerRequest(e) {
    e.preventDefault();
    const btn = e.target.querySelector('.btn-primary');
    btn.classList.add('loading');
    btn.querySelector('.btn-text').style.display = 'none';
    btn.querySelector('.btn-loading').style.display = 'inline';

    const customerId = currentUser.customer_id;
    if (!customerId) {
        toast('Inget kundkonto kopplat', 'error');
        btn.classList.remove('loading');
        btn.querySelector('.btn-text').style.display = 'inline';
        btn.querySelector('.btn-loading').style.display = 'none';
        return;
    }

    const skillsRaw = document.getElementById('cr-skills').value;
    const skills = skillsRaw ? skillsRaw.split(',').map(s => s.trim()).filter(Boolean) : [];

    const payload = {
        customer_id: customerId,
        title: document.getElementById('cr-title').value,
        description: document.getElementById('cr-desc').value,
        required_skills: skills,
        number_of_consultants: parseInt(document.getElementById('cr-count').value) || 1,
        start_date: document.getElementById('cr-start').value || null,
        end_date: document.getElementById('cr-end').value || null,
        budget_max_hourly: parseFloat(document.getElementById('cr-budget').value) || null,
        location: document.getElementById('cr-location').value || null,
        remote_ok: document.getElementById('cr-remote').checked,
    };

    try {
        const res = await fetch(`${API}/api/requests`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        if (!res.ok) throw new Error('Failed');

        const request = await res.json();
        toast('Förfrågan skickad! AI analyserar...', 'success');

        // Show result - load full detail
        setTimeout(async () => {
            try {
                const detailRes = await fetch(`${API}/api/requests/${request.id}`);
                const detail = await detailRes.json();
                renderCustomerResult(detail);
            } catch {
                renderCustomerResult({ request, customer: { company: '', name: '' } });
            }
        }, 500);

        e.target.reset();
        document.getElementById('cr-count').value = '1';
    } catch (err) {
        toast('Kunde inte skicka förfrågan', 'error');
    } finally {
        btn.classList.remove('loading');
        btn.querySelector('.btn-text').style.display = 'inline';
        btn.querySelector('.btn-loading').style.display = 'none';
    }
}

function renderCustomerResult(d) {
    const r = d.request;
    const a = d.assessment;
    const resultEl = document.getElementById('cust-result');

    let html = `<div class="result-panel glass">`;
    html += `<div class="result-header">
        <h3>AI-analys klar</h3>
        ${a ? `<span class="ai-badge ai-badge-${a.overall_rating}">${feasibilityLabel(a.overall_rating)}</span>` : ''}
    </div>`;

    html += `<div class="result-summary">${esc(r.ai_summary || 'Analyserar...')}</div>`;

    // Feasibility scores
    if (a) {
        html += `<div class="result-section">
            <h4>Genomförbarhetsanalys</h4>
            ${gaugeRow('Tillgänglighet', a.availability_score)}
            ${gaugeRow('Kompetens', a.skills_match_score)}
            ${gaugeRow('Budget', a.budget_fit_score)}
            ${gaugeRow('Tidslinje', a.timeline_score)}
            ${gaugeRow('Compliance', a.compliance_score)}
        </div>`;
    }

    // Matching consultants
    if (d.matching_consultants && d.matching_consultants.length > 0) {
        const skills = Array.isArray(r.required_skills) ? r.required_skills : [];
        html += `<div class="result-section">
            <h4>Matchande konsulter (${d.matching_consultants.length})</h4>
            ${d.matching_consultants.map(c => renderMatchCard(c, r.id, skills)).join('')}
        </div>`;
    }

    // Recommendations
    if (a) {
        const recs = parseJsonField(a.recommendations);
        if (recs.length > 0) {
            html += `<div class="result-section">
                <h4>Rekommendationer</h4>
                ${recs.map(r => `<div class="insight-item">${esc(r)}</div>`).join('')}
            </div>`;
        }
    }

    html += `<button class="btn-primary" style="margin-top:16px" onclick="openRequestDetail('${r.id}')">Visa fullständig analys</button>`;
    html += `</div>`;

    resultEl.innerHTML = html;
}

async function loadMyRequests() {
    if (!currentUser || !currentUser.customer_id) return;
    try {
        const res = await fetch(`${API}/api/requests?customer_id=${currentUser.customer_id}`);
        const requests = await res.json();
        const el = document.getElementById('my-requests');
        if (requests.length === 0) {
            el.innerHTML = '<div class="empty-state glass"><div class="empty-icon">📋</div><h3>Inga förfrågningar ännu</h3><p>Skapa din första förfrågan i fliken "Ny förfrågan"</p></div>';
            return;
        }
        el.innerHTML = requests.map(r => renderRequestCard(r)).join('');
    } catch { }
}

// ═══════════════════════════════════════════════════
//  HELPERS
// ═══════════════════════════════════════════════════

function gaugeRow(label, score) {
    const s = Math.round(score || 0);
    const cls = s >= 70 ? 'fill-high' : s >= 40 ? 'fill-medium' : 'fill-low';
    return `
        <div class="gauge-row">
            <div class="gauge-label">${label}</div>
            <div class="gauge-bar"><div class="gauge-fill ${cls}" style="width:${s}%"></div></div>
            <div class="gauge-val">${s}</div>
        </div>
    `;
}

function statusLabel(s) {
    const map = {
        draft: 'Utkast', submitted: 'Inskickad', analyzing: 'Analyseras',
        assessed: 'Bedömd', in_progress: 'Pågående', completed: 'Klar',
        rejected: 'Avvisad', cancelled: 'Avbruten',
    };
    return map[s] || s;
}

function feasibilityLabel(r) {
    const map = { high: 'Hög', medium: 'Medel', low: 'Låg', not_feasible: 'Ej genomförbar' };
    return map[r] || r;
}

function consultantStatusLabel(s) {
    const map = { available: 'Ledig', assigned: 'Tilldelad', on_leave: 'Frånvarande', ending_soon: 'Avslutar snart' };
    return map[s] || s;
}

function parseJsonField(val) {
    if (Array.isArray(val)) return val;
    if (typeof val === 'string') {
        try { return JSON.parse(val); } catch { return []; }
    }
    return [];
}

function timeAgo(dateStr) {
    const d = new Date(dateStr);
    const now = new Date();
    const diff = Math.floor((now - d) / 1000);
    if (diff < 60) return 'Just nu';
    if (diff < 3600) return `${Math.floor(diff / 60)} min sedan`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h sedan`;
    return d.toLocaleDateString('sv-SE');
}

function esc(str) {
    if (!str) return '';
    const el = document.createElement('span');
    el.textContent = str;
    return el.innerHTML;
}

function toast(msg, type = 'info') {
    const t = document.createElement('div');
    t.className = `toast toast-${type}`;
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(() => t.remove(), 3000);
}
