// ═══════════════════════════════════════════════════════════════════
// Employee Management System — Frontend Logic
// ═══════════════════════════════════════════════════════════════════

const API = '';
let TOKEN = localStorage.getItem('ems_token') || '';
let USER = JSON.parse(localStorage.getItem('ems_user') || 'null');
let employeesCache = [];
let departmentsCache = [];
let attendanceCache = [];
let leaveCache = [];
let payrollCache = [];
let chartInstances = {};

// ─── API Helper ──────────────────────────────────────────────────
async function api(endpoint, method = 'GET', body = null) {
    const opts = {
        method,
        headers: { 'Content-Type': 'application/json' }
    };
    if (TOKEN) opts.headers['Authorization'] = `Bearer ${TOKEN}`;
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(`${API}${endpoint}`, opts);
    const data = await res.json();
    if (res.status === 401) {
        handleLogout();
        throw new Error('Session expired');
    }
    if (!res.ok) throw new Error(data.error || 'Request failed');
    return data;
}

// ─── Toast Notifications ─────────────────────────────────────────
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    const icons = { success: '✅', error: '❌', info: 'ℹ️' };
    toast.innerHTML = `<span>${icons[type] || ''}</span><span>${message}</span>`;
    container.appendChild(toast);
    toast.onclick = () => { toast.classList.add('hiding'); setTimeout(() => toast.remove(), 300); };
    setTimeout(() => { toast.classList.add('hiding'); setTimeout(() => toast.remove(), 300); }, 3500);
}

// ─── Modal Helpers ───────────────────────────────────────────────
function openModal(id) { document.getElementById(id).classList.add('active'); }
function closeModal(id) { document.getElementById(id).classList.remove('active'); }

// ─── Currency Format ─────────────────────────────────────────────
function formatCurrency(n) {
    return '₹' + Number(n || 0).toLocaleString('en-IN');
}

// ─── Status Badge ────────────────────────────────────────────────
function badge(status) {
    const cls = (status || '').toLowerCase().replace(/\s+/g, '-');
    return `<span class="badge badge-${cls}">${status}</span>`;
}

// ═══════════════════════════════════════════════════════════════════
// AUTH
// ═══════════════════════════════════════════════════════════════════
async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;
    const errEl = document.getElementById('login-error');
    const btn = document.getElementById('login-btn');

    btn.innerHTML = '<span class="spinner"></span> Signing in...';
    btn.disabled = true;
    errEl.style.display = 'none';

    try {
        const data = await api('/api/login', 'POST', { username, password });
        TOKEN = data.token;
        USER = { username: data.username, role: data.role };
        localStorage.setItem('ems_token', TOKEN);
        localStorage.setItem('ems_user', JSON.stringify(USER));
        showApp();
        showToast(`Welcome back, ${data.username}!`);
    } catch (err) {
        errEl.textContent = err.message;
        errEl.style.display = 'block';
    } finally {
        btn.innerHTML = 'Sign In';
        btn.disabled = false;
    }
    return false;
}

function handleLogout() {
    api('/api/logout', 'POST').catch(() => {});
    TOKEN = '';
    USER = null;
    localStorage.removeItem('ems_token');
    localStorage.removeItem('ems_user');
    document.getElementById('login-page').style.display = 'flex';
    document.getElementById('app-container').style.display = 'none';
    document.getElementById('login-username').value = '';
    document.getElementById('login-password').value = '';
}

function showApp() {
    document.getElementById('login-page').style.display = 'none';
    document.getElementById('app-container').style.display = 'block';
    document.getElementById('user-name').textContent = USER.username;
    document.getElementById('user-role').textContent = USER.role;
    document.getElementById('user-avatar').textContent = USER.username.charAt(0).toUpperCase();
    loadDashboard();
    loadDepartmentsCache();
    loadEmployeesCache();
}

// ═══════════════════════════════════════════════════════════════════
// NAVIGATION
// ═══════════════════════════════════════════════════════════════════
function navigateTo(section) {
    document.querySelectorAll('.section-page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

    const page = document.getElementById(`section-${section}`);
    if (page) page.classList.add('active');

    const nav = document.querySelector(`.nav-item[data-section="${section}"]`);
    if (nav) nav.classList.add('active');

    switch (section) {
        case 'dashboard': loadDashboard(); break;
        case 'employees': loadEmployees(); break;
        case 'departments': loadDepartments(); break;
        case 'attendance': loadAttendance(); break;
        case 'leave': loadLeave(); break;
        case 'payroll': loadPayroll(); break;
        case 'projects': loadProjects(); break;
    }
}

// ═══════════════════════════════════════════════════════════════════
// DASHBOARD
// ═══════════════════════════════════════════════════════════════════
async function loadDashboard() {
    try {
        const stats = await api('/api/stats');
        const statsConfig = [
            { icon: '👥', label: 'Total Employees', value: stats.total_employees, color: 'blue' },
            { icon: '✅', label: 'Active Employees', value: stats.active_employees, color: 'green' },
            { icon: '🏢', label: 'Departments', value: stats.total_departments, color: 'purple' },
            { icon: '📋', label: 'Present Today', value: stats.present_today, color: 'cyan' },
            { icon: '🚫', label: 'Absent Today', value: stats.absent_today, color: 'red' },
            { icon: '🏖️', label: 'Pending Leaves', value: stats.pending_leaves, color: 'orange' },
            { icon: '💰', label: 'Total Paid Salary', value: formatCurrency(stats.total_paid_salary), color: 'green' },
            { icon: '📁', label: 'Active Projects', value: stats.active_projects, color: 'pink' },
        ];

        // Update leave badge
        const leaveBadge = document.getElementById('leave-badge');
        if (stats.pending_leaves > 0) {
            leaveBadge.textContent = stats.pending_leaves;
            leaveBadge.style.display = 'inline';
        } else {
            leaveBadge.style.display = 'none';
        }

        document.getElementById('stats-grid').innerHTML = statsConfig.map(s => `
            <div class="stat-card">
                <div class="stat-icon ${s.color}">${s.icon}</div>
                <div class="stat-info">
                    <h3>${s.value}</h3>
                    <p>${s.label}</p>
                </div>
            </div>
        `).join('');

        loadCharts();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function loadCharts() {
    const colors = {
        blue: '#3b82f6', purple: '#8b5cf6', green: '#22c55e',
        orange: '#f97316', red: '#ef4444', cyan: '#06b6d4',
        pink: '#ec4899', yellow: '#eab308'
    };
    const colorList = [colors.blue, colors.purple, colors.green, colors.orange, colors.red, colors.cyan, colors.pink, colors.yellow];

    // Destroy previous chart instances
    Object.values(chartInstances).forEach(c => c.destroy());
    chartInstances = {};

    try {
        // Department Distribution (Doughnut)
        const deptData = await api('/api/charts/department-distribution');
        const deptCtx = document.getElementById('chart-dept').getContext('2d');
        chartInstances.dept = new Chart(deptCtx, {
            type: 'doughnut',
            data: {
                labels: deptData.map(d => d.dept_name),
                datasets: [{
                    data: deptData.map(d => d.count),
                    backgroundColor: colorList.slice(0, deptData.length),
                    borderWidth: 0,
                    hoverOffset: 8
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'bottom', labels: { color: '#94a3b8', padding: 16, font: { family: 'Inter', size: 12 } } }
                },
                cutout: '65%'
            }
        });

        // Attendance (Bar)
        const attData = await api('/api/charts/attendance-summary');
        const attCtx = document.getElementById('chart-attendance').getContext('2d');
        chartInstances.attendance = new Chart(attCtx, {
            type: 'bar',
            data: {
                labels: Object.keys(attData),
                datasets: [{
                    label: 'Count',
                    data: Object.values(attData),
                    backgroundColor: [colors.green, colors.red, colors.yellow, colors.cyan],
                    borderRadius: 8,
                    borderSkipped: false,
                    maxBarThickness: 50
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: { ticks: { color: '#94a3b8', font: { family: 'Inter' } }, grid: { display: false } },
                    y: { ticks: { color: '#94a3b8', font: { family: 'Inter' }, stepSize: 1 }, grid: { color: 'rgba(148,163,184,0.08)' }, beginAtZero: true }
                }
            }
        });

        // Salary by Department (Bar)
        const salData = await api('/api/charts/salary-overview');
        const salCtx = document.getElementById('chart-salary').getContext('2d');
        chartInstances.salary = new Chart(salCtx, {
            type: 'bar',
            data: {
                labels: salData.map(d => d.dept_name),
                datasets: [{
                    label: 'Total Salary (₹)',
                    data: salData.map(d => d.total_salary),
                    backgroundColor: colorList.slice(0, salData.length).map(c => c + '80'),
                    borderColor: colorList.slice(0, salData.length),
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false,
                    maxBarThickness: 50
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: { ticks: { color: '#94a3b8', font: { family: 'Inter' } }, grid: { display: false } },
                    y: {
                        ticks: {
                            color: '#94a3b8', font: { family: 'Inter' },
                            callback: v => '₹' + (v / 1000).toFixed(0) + 'K'
                        },
                        grid: { color: 'rgba(148,163,184,0.08)' }, beginAtZero: true
                    }
                }
            }
        });
    } catch (err) {
        console.error('Charts error:', err);
    }
}

// ═══════════════════════════════════════════════════════════════════
// EMPLOYEES
// ═══════════════════════════════════════════════════════════════════
async function loadEmployeesCache() {
    try { employeesCache = await api('/api/employees'); } catch (e) {}
}

async function loadDepartmentsCache() {
    try { departmentsCache = await api('/api/departments'); } catch (e) {}
}

async function loadEmployees() {
    try {
        employeesCache = await api('/api/employees');
        renderEmployees(employeesCache);
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function renderEmployees(list) {
    document.getElementById('employees-tbody').innerHTML = list.length ? list.map(e => `
        <tr>
            <td>${e.emp_id}</td>
            <td><strong style="color:var(--text-primary);cursor:pointer" onclick="viewProfile(${e.emp_id})">${e.name}</strong></td>
            <td>${e.email || ''}</td>
            <td>${e.dept_name || '—'}</td>
            <td>${e.designation || '—'}</td>
            <td>${formatCurrency(e.salary)}</td>
            <td>${badge(e.status)}</td>
            <td>
                <div class="action-btns">
                    <button class="btn btn-sm btn-outline" onclick="viewProfile(${e.emp_id})" title="View">👁</button>
                    <button class="btn btn-sm btn-outline" onclick="editEmployee(${e.emp_id})" title="Edit">✏️</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteEmployee(${e.emp_id})" title="Delete">🗑️</button>
                </div>
            </td>
        </tr>
    `).join('') : '<tr><td colspan="8"><div class="empty-state"><div class="empty-icon">👤</div><h3>No employees found</h3><p>Add your first employee to get started</p></div></td></tr>';
}

function filterEmployees() {
    const q = document.getElementById('search-employees').value.toLowerCase();
    renderEmployees(employeesCache.filter(e =>
        (e.name || '').toLowerCase().includes(q) ||
        (e.email || '').toLowerCase().includes(q) ||
        (e.dept_name || '').toLowerCase().includes(q) ||
        (e.designation || '').toLowerCase().includes(q)
    ));
}

function populateDeptSelect(selectId, selectedId = '') {
    const sel = document.getElementById(selectId);
    sel.innerHTML = '<option value="">Select Department</option>' +
        departmentsCache.map(d => `<option value="${d.dept_id}" ${d.dept_id == selectedId ? 'selected' : ''}>${d.dept_name}</option>`).join('');
}

function populateEmpSelect(selectId, selectedId = '') {
    const sel = document.getElementById(selectId);
    sel.innerHTML = '<option value="">Select Employee</option>' +
        employeesCache.map(e => `<option value="${e.emp_id}" ${e.emp_id == selectedId ? 'selected' : ''}>${e.name} — ${e.designation || ''}</option>`).join('');
}

function openEmployeeModal(emp = null) {
    populateDeptSelect('emp-dept', emp ? emp.dept_id : '');
    document.getElementById('employee-modal-title').textContent = emp ? 'Edit Employee' : 'Add Employee';
    document.getElementById('emp-edit-id').value = emp ? emp.emp_id : '';
    document.getElementById('emp-name').value = emp ? emp.name : '';
    document.getElementById('emp-email').value = emp ? emp.email : '';
    document.getElementById('emp-phone').value = emp ? emp.phone : '';
    document.getElementById('emp-designation').value = emp ? emp.designation : '';
    document.getElementById('emp-salary').value = emp ? emp.salary : '';
    document.getElementById('emp-hire-date').value = emp ? emp.hire_date : new Date().toISOString().slice(0, 10);
    document.getElementById('emp-gender').value = emp ? emp.gender : '';
    document.getElementById('emp-address').value = emp ? emp.address : '';
    document.getElementById('emp-status').value = emp ? emp.status : 'Active';
    document.getElementById('emp-status-group').style.display = emp ? 'block' : 'none';
    openModal('employee-modal');
}

async function editEmployee(id) {
    try {
        const emp = await api(`/api/employees/${id}`);
        openEmployeeModal(emp);
    } catch (err) { showToast(err.message, 'error'); }
}

async function saveEmployee() {
    const id = document.getElementById('emp-edit-id').value;
    const body = {
        name: document.getElementById('emp-name').value.trim(),
        email: document.getElementById('emp-email').value.trim(),
        phone: document.getElementById('emp-phone').value.trim(),
        dept_id: document.getElementById('emp-dept').value,
        designation: document.getElementById('emp-designation').value.trim(),
        salary: document.getElementById('emp-salary').value,
        hire_date: document.getElementById('emp-hire-date').value,
        gender: document.getElementById('emp-gender').value,
        address: document.getElementById('emp-address').value.trim(),
        status: document.getElementById('emp-status').value,
    };
    if (!body.name || !body.email || !body.phone || !body.dept_id || !body.designation || !body.salary) {
        showToast('Please fill all required fields', 'error'); return;
    }
    try {
        if (id) {
            await api(`/api/employees/${id}`, 'PUT', body);
            showToast('Employee updated successfully');
        } else {
            await api('/api/employees', 'POST', body);
            showToast('Employee added successfully');
        }
        closeModal('employee-modal');
        loadEmployees();
        loadEmployeesCache();
    } catch (err) { showToast(err.message, 'error'); }
}

async function deleteEmployee(id) {
    if (!confirm('Are you sure you want to delete this employee?')) return;
    try {
        await api(`/api/employees/${id}`, 'DELETE');
        showToast('Employee deleted');
        loadEmployees();
        loadEmployeesCache();
    } catch (err) { showToast(err.message, 'error'); }
}

// ═══════════════════════════════════════════════════════════════════
// EMPLOYEE PROFILE
// ═══════════════════════════════════════════════════════════════════
async function viewProfile(id) {
    try {
        const data = await api(`/api/employees/${id}/profile`);
        const emp = data.employee;
        const initials = emp.name.split(' ').map(w => w[0]).join('').slice(0, 2);

        document.getElementById('profile-container').innerHTML = `
            <div class="profile-header">
                <div class="profile-avatar">${initials}</div>
                <div class="profile-info">
                    <h2>${emp.name}</h2>
                    <p style="color:var(--text-secondary)">${emp.designation || ''} ${emp.dept_name ? '• ' + emp.dept_name : ''}</p>
                    <div class="profile-meta">
                        <span>📧 ${emp.email || '—'}</span>
                        <span>📱 ${emp.phone || '—'}</span>
                        <span>📅 Joined ${emp.hire_date || '—'}</span>
                        <span>${badge(emp.status)}</span>
                    </div>
                </div>
            </div>

            <div class="profile-tabs">
                <button class="profile-tab active" onclick="switchProfileTab(this, 'tab-attendance')">Attendance</button>
                <button class="profile-tab" onclick="switchProfileTab(this, 'tab-leaves')">Leaves</button>
                <button class="profile-tab" onclick="switchProfileTab(this, 'tab-payroll')">Payroll</button>
                <button class="profile-tab" onclick="switchProfileTab(this, 'tab-projects')">Projects</button>
            </div>

            <div class="profile-content active" id="tab-attendance">
                <div class="table-card">
                    <div class="table-wrapper">
                        <table><thead><tr><th>Date</th><th>Check In</th><th>Check Out</th><th>Status</th></tr></thead>
                        <tbody>${data.attendance.length ? data.attendance.map(a => `
                            <tr>
                                <td>${a.attend_date}</td>
                                <td>${a.check_in || '—'}</td>
                                <td>${a.check_out || '—'}</td>
                                <td>${badge(a.status)}</td>
                            </tr>
                        `).join('') : '<tr><td colspan="4" style="text-align:center;color:var(--text-muted);padding:30px">No attendance records</td></tr>'}</tbody></table>
                    </div>
                </div>
            </div>

            <div class="profile-content" id="tab-leaves">
                <div class="table-card">
                    <div class="table-wrapper">
                        <table><thead><tr><th>Type</th><th>From</th><th>To</th><th>Reason</th><th>Status</th></tr></thead>
                        <tbody>${data.leaves.length ? data.leaves.map(l => `
                            <tr>
                                <td>${l.leave_type}</td>
                                <td>${l.start_date}</td>
                                <td>${l.end_date}</td>
                                <td>${l.reason || '—'}</td>
                                <td>${badge(l.status)}</td>
                            </tr>
                        `).join('') : '<tr><td colspan="5" style="text-align:center;color:var(--text-muted);padding:30px">No leave records</td></tr>'}</tbody></table>
                    </div>
                </div>
            </div>

            <div class="profile-content" id="tab-payroll">
                <div class="table-card">
                    <div class="table-wrapper">
                        <table><thead><tr><th>Month</th><th>Basic</th><th>Deductions</th><th>Bonus</th><th>Net Salary</th><th>Status</th></tr></thead>
                        <tbody>${data.payroll.length ? data.payroll.map(p => `
                            <tr>
                                <td>${p.pay_month}</td>
                                <td>${formatCurrency(p.basic_salary)}</td>
                                <td style="color:var(--accent-red)">${formatCurrency(p.deductions)}</td>
                                <td style="color:var(--accent-green)">${formatCurrency(p.bonus)}</td>
                                <td><strong>${formatCurrency(p.net_salary)}</strong></td>
                                <td>${badge(p.status)}</td>
                            </tr>
                        `).join('') : '<tr><td colspan="6" style="text-align:center;color:var(--text-muted);padding:30px">No payroll records</td></tr>'}</tbody></table>
                    </div>
                </div>
            </div>

            <div class="profile-content" id="tab-projects">
                <div class="table-card">
                    <div class="table-wrapper">
                        <table><thead><tr><th>Project</th><th>Role</th><th>Status</th></tr></thead>
                        <tbody>${data.projects.length ? data.projects.map(p => `
                            <tr>
                                <td>${p.project_name}</td>
                                <td>${p.role}</td>
                                <td>${badge(p.project_status)}</td>
                            </tr>
                        `).join('') : '<tr><td colspan="3" style="text-align:center;color:var(--text-muted);padding:30px">No project assignments</td></tr>'}</tbody></table>
                    </div>
                </div>
            </div>
        `;

        // Navigate to profile section
        document.querySelectorAll('.section-page').forEach(p => p.classList.remove('active'));
        document.getElementById('section-employee-profile').classList.add('active');
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    } catch (err) { showToast(err.message, 'error'); }
}

function switchProfileTab(btn, tabId) {
    btn.closest('.profile-tabs').querySelectorAll('.profile-tab').forEach(t => t.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.profile-content').forEach(c => c.classList.remove('active'));
    document.getElementById(tabId).classList.add('active');
}

// ═══════════════════════════════════════════════════════════════════
// DEPARTMENTS
// ═══════════════════════════════════════════════════════════════════
async function loadDepartments() {
    try {
        departmentsCache = await api('/api/departments');
        renderDepartments(departmentsCache);
    } catch (err) { showToast(err.message, 'error'); }
}

function renderDepartments(list) {
    const colors = ['🔵', '🟢', '🟣', '🟠', '🔴', '🟡', '⚪'];
    document.getElementById('dept-grid').innerHTML = list.length ? list.map((d, i) => `
        <div class="dept-card">
            <h3>${colors[i % colors.length]} ${d.dept_name}</h3>
            <div class="dept-meta">
                <span>👤 Manager: <strong>${d.manager_name || '—'}</strong></span>
                <span>📍 Location: ${d.location || '—'}</span>
                <span>👥 Employees: <strong>${d.total_employees || 0}</strong></span>
            </div>
            <div class="dept-actions">
                <button class="btn btn-sm btn-outline" onclick="editDept(${d.dept_id})">✏️ Edit</button>
                <button class="btn btn-sm btn-danger" onclick="deleteDept(${d.dept_id})">🗑️ Delete</button>
            </div>
        </div>
    `).join('') : '<div class="empty-state" style="grid-column:1/-1"><div class="empty-icon">🏢</div><h3>No departments</h3><p>Create your first department</p></div>';
}

function openDeptModal(dept = null) {
    document.getElementById('dept-modal-title').textContent = dept ? 'Edit Department' : 'Add Department';
    document.getElementById('dept-edit-id').value = dept ? dept.dept_id : '';
    document.getElementById('dept-name').value = dept ? dept.dept_name : '';
    document.getElementById('dept-manager').value = dept ? dept.manager_name : '';
    document.getElementById('dept-location').value = dept ? dept.location : '';
    openModal('dept-modal');
}

async function editDept(id) {
    try {
        const dept = await api(`/api/departments/${id}`);
        openDeptModal(dept);
    } catch (err) { showToast(err.message, 'error'); }
}

async function saveDepartment() {
    const id = document.getElementById('dept-edit-id').value;
    const body = {
        dept_name: document.getElementById('dept-name').value.trim(),
        manager_name: document.getElementById('dept-manager').value.trim(),
        location: document.getElementById('dept-location').value.trim(),
    };
    if (!body.dept_name) { showToast('Department name is required', 'error'); return; }
    try {
        if (id) {
            await api(`/api/departments/${id}`, 'PUT', body);
            showToast('Department updated');
        } else {
            await api('/api/departments', 'POST', body);
            showToast('Department added');
        }
        closeModal('dept-modal');
        loadDepartments();
        loadDepartmentsCache();
    } catch (err) { showToast(err.message, 'error'); }
}

async function deleteDept(id) {
    if (!confirm('Delete this department?')) return;
    try {
        await api(`/api/departments/${id}`, 'DELETE');
        showToast('Department deleted');
        loadDepartments();
        loadDepartmentsCache();
    } catch (err) { showToast(err.message, 'error'); }
}

// ═══════════════════════════════════════════════════════════════════
// ATTENDANCE
// ═══════════════════════════════════════════════════════════════════
async function loadAttendance() {
    const dateInput = document.getElementById('attendance-date');
    if (!dateInput.value) dateInput.value = new Date().toISOString().slice(0, 10);
    try {
        attendanceCache = await api(`/api/attendance?date=${dateInput.value}`);
        renderAttendance(attendanceCache);
    } catch (err) { showToast(err.message, 'error'); }
}

function renderAttendance(list) {
    document.getElementById('attendance-tbody').innerHTML = list.length ? list.map(a => `
        <tr>
            <td><strong style="color:var(--text-primary)">${a.emp_name}</strong><br><small style="color:var(--text-muted)">${a.designation || ''}</small></td>
            <td>${a.dept_name || '—'}</td>
            <td>${a.check_in || '—'}</td>
            <td>${a.check_out || '—'}</td>
            <td>${badge(a.status)}</td>
            <td>
                <div class="action-btns">
                    <button class="btn btn-sm btn-danger" onclick="deleteAttendance(${a.attend_id})">🗑️</button>
                </div>
            </td>
        </tr>
    `).join('') : '<tr><td colspan="6"><div class="empty-state"><div class="empty-icon">📋</div><h3>No attendance records</h3><p>Mark attendance for the selected date</p></div></td></tr>';
}

function filterAttendance() {
    const q = document.getElementById('search-attendance').value.toLowerCase();
    renderAttendance(attendanceCache.filter(a =>
        (a.emp_name || '').toLowerCase().includes(q) ||
        (a.dept_name || '').toLowerCase().includes(q) ||
        (a.status || '').toLowerCase().includes(q)
    ));
}

function openAttendanceModal() {
    populateEmpSelect('attend-emp');
    document.getElementById('attend-date').value = document.getElementById('attendance-date').value || new Date().toISOString().slice(0, 10);
    document.getElementById('attend-checkin').value = '09:00';
    document.getElementById('attend-checkout').value = '18:00';
    document.getElementById('attend-status').value = 'Present';
    openModal('attendance-modal');
}

async function saveAttendance() {
    const body = {
        emp_id: document.getElementById('attend-emp').value,
        attend_date: document.getElementById('attend-date').value,
        check_in: document.getElementById('attend-checkin').value || null,
        check_out: document.getElementById('attend-checkout').value || null,
        status: document.getElementById('attend-status').value,
    };
    if (!body.emp_id || !body.attend_date) { showToast('Employee and date are required', 'error'); return; }
    try {
        await api('/api/attendance', 'POST', body);
        showToast('Attendance marked');
        closeModal('attendance-modal');
        loadAttendance();
    } catch (err) { showToast(err.message, 'error'); }
}

async function deleteAttendance(id) {
    if (!confirm('Delete this attendance record?')) return;
    try {
        await api(`/api/attendance/${id}`, 'DELETE');
        showToast('Record deleted');
        loadAttendance();
    } catch (err) { showToast(err.message, 'error'); }
}

// ═══════════════════════════════════════════════════════════════════
// LEAVE REQUESTS
// ═══════════════════════════════════════════════════════════════════
async function loadLeave() {
    try {
        leaveCache = await api('/api/leave');
        renderLeave(leaveCache);
    } catch (err) { showToast(err.message, 'error'); }
}

function renderLeave(list) {
    document.getElementById('leave-tbody').innerHTML = list.length ? list.map(l => `
        <tr>
            <td><strong style="color:var(--text-primary)">${l.emp_name}</strong><br><small style="color:var(--text-muted)">${l.designation || ''}</small></td>
            <td>${l.leave_type}</td>
            <td>${l.start_date}</td>
            <td>${l.end_date}</td>
            <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis">${l.reason || '—'}</td>
            <td>${badge(l.status)}</td>
            <td>
                <div class="action-btns">
                    ${l.status === 'Pending' ? `
                        <button class="btn btn-sm btn-success" onclick="updateLeaveStatus(${l.leave_id}, 'Approved')">✅</button>
                        <button class="btn btn-sm btn-danger" onclick="updateLeaveStatus(${l.leave_id}, 'Rejected')">❌</button>
                    ` : ''}
                    <button class="btn btn-sm btn-danger" onclick="deleteLeave(${l.leave_id})">🗑️</button>
                </div>
            </td>
        </tr>
    `).join('') : '<tr><td colspan="7"><div class="empty-state"><div class="empty-icon">🏖️</div><h3>No leave requests</h3><p>All clear!</p></div></td></tr>';
}

function filterLeave() {
    const q = document.getElementById('search-leave').value.toLowerCase();
    renderLeave(leaveCache.filter(l =>
        (l.emp_name || '').toLowerCase().includes(q) ||
        (l.leave_type || '').toLowerCase().includes(q) ||
        (l.status || '').toLowerCase().includes(q)
    ));
}

function openLeaveModal() {
    populateEmpSelect('leave-emp');
    document.getElementById('leave-type').value = 'Casual Leave';
    document.getElementById('leave-start').value = new Date().toISOString().slice(0, 10);
    document.getElementById('leave-end').value = new Date().toISOString().slice(0, 10);
    document.getElementById('leave-reason').value = '';
    openModal('leave-modal');
}

async function saveLeave() {
    const body = {
        emp_id: document.getElementById('leave-emp').value,
        leave_type: document.getElementById('leave-type').value,
        start_date: document.getElementById('leave-start').value,
        end_date: document.getElementById('leave-end').value,
        reason: document.getElementById('leave-reason').value.trim(),
    };
    if (!body.emp_id || !body.start_date || !body.end_date) { showToast('Please fill all required fields', 'error'); return; }
    try {
        await api('/api/leave', 'POST', body);
        showToast('Leave request submitted');
        closeModal('leave-modal');
        loadLeave();
    } catch (err) { showToast(err.message, 'error'); }
}

async function updateLeaveStatus(id, status) {
    if (!confirm(`${status === 'Approved' ? 'Approve' : 'Reject'} this leave request?`)) return;
    try {
        await api(`/api/leave/${id}/status`, 'PUT', { status });
        showToast(`Leave ${status.toLowerCase()}`);
        loadLeave();
    } catch (err) { showToast(err.message, 'error'); }
}

async function deleteLeave(id) {
    if (!confirm('Delete this leave request?')) return;
    try {
        await api(`/api/leave/${id}`, 'DELETE');
        showToast('Leave request deleted');
        loadLeave();
    } catch (err) { showToast(err.message, 'error'); }
}

// ═══════════════════════════════════════════════════════════════════
// PAYROLL
// ═══════════════════════════════════════════════════════════════════
async function loadPayroll() {
    const monthInput = document.getElementById('payroll-month');
    if (!monthInput.value) monthInput.value = new Date().toISOString().slice(0, 7);
    try {
        payrollCache = await api(`/api/payroll?month=${monthInput.value}`);
        renderPayroll(payrollCache);
    } catch (err) { showToast(err.message, 'error'); }
}

function renderPayroll(list) {
    document.getElementById('payroll-tbody').innerHTML = list.length ? list.map(p => `
        <tr>
            <td><strong style="color:var(--text-primary)">${p.emp_name}</strong><br><small style="color:var(--text-muted)">${p.designation || ''}</small></td>
            <td>${p.dept_name || '—'}</td>
            <td>${formatCurrency(p.basic_salary)}</td>
            <td style="color:var(--accent-red)">${formatCurrency(p.deductions)}</td>
            <td style="color:var(--accent-green)">${formatCurrency(p.bonus)}</td>
            <td><strong>${formatCurrency(p.net_salary)}</strong></td>
            <td>${badge(p.status)}</td>
            <td>
                <div class="action-btns">
                    ${p.status === 'Pending' ? `<button class="btn btn-sm btn-success" onclick="markPaid(${p.payroll_id})" title="Mark as Paid">💵</button>` : ''}
                    <button class="btn btn-sm btn-outline" onclick="editPayroll(${p.payroll_id}, ${JSON.stringify(p).replace(/"/g, '&quot;')})" title="Edit">✏️</button>
                    <button class="btn btn-sm btn-danger" onclick="deletePayroll(${p.payroll_id})" title="Delete">🗑️</button>
                </div>
            </td>
        </tr>
    `).join('') : '<tr><td colspan="8"><div class="empty-state"><div class="empty-icon">💰</div><h3>No payroll records</h3><p>Generate payroll or add records manually</p></div></td></tr>';
}

function filterPayroll() {
    const q = document.getElementById('search-payroll').value.toLowerCase();
    renderPayroll(payrollCache.filter(p =>
        (p.emp_name || '').toLowerCase().includes(q) ||
        (p.dept_name || '').toLowerCase().includes(q) ||
        (p.status || '').toLowerCase().includes(q)
    ));
}

function openPayrollModal(p = null) {
    populateEmpSelect('payroll-emp', p ? p.emp_id : '');
    document.getElementById('payroll-modal-title').textContent = p ? 'Edit Payroll Record' : 'Add Payroll Record';
    document.getElementById('payroll-edit-id').value = p ? p.payroll_id : '';
    document.getElementById('payroll-pay-month').value = p ? p.pay_month : document.getElementById('payroll-month').value || new Date().toISOString().slice(0, 7);
    document.getElementById('payroll-basic').value = p ? p.basic_salary : '';
    document.getElementById('payroll-deductions').value = p ? p.deductions : '';
    document.getElementById('payroll-bonus').value = p ? p.bonus : '';
    document.getElementById('payroll-status').value = p ? p.status : 'Pending';
    openModal('payroll-modal');
}

function editPayroll(id, data) {
    openPayrollModal(data);
}

async function savePayroll() {
    const id = document.getElementById('payroll-edit-id').value;
    const body = {
        emp_id: document.getElementById('payroll-emp').value,
        pay_month: document.getElementById('payroll-pay-month').value,
        basic_salary: document.getElementById('payroll-basic').value,
        deductions: document.getElementById('payroll-deductions').value || 0,
        bonus: document.getElementById('payroll-bonus').value || 0,
        status: document.getElementById('payroll-status').value,
    };
    if (!body.emp_id || !body.pay_month || !body.basic_salary) { showToast('Please fill required fields', 'error'); return; }
    try {
        if (id) {
            await api(`/api/payroll/${id}`, 'PUT', body);
            showToast('Payroll updated');
        } else {
            await api('/api/payroll', 'POST', body);
            showToast('Payroll record added');
        }
        closeModal('payroll-modal');
        loadPayroll();
    } catch (err) { showToast(err.message, 'error'); }
}

async function markPaid(id) {
    if (!confirm('Mark this salary as paid?')) return;
    try {
        await api(`/api/payroll/${id}/pay`, 'PUT');
        showToast('Marked as paid');
        loadPayroll();
    } catch (err) { showToast(err.message, 'error'); }
}

async function deletePayroll(id) {
    if (!confirm('Delete this payroll record?')) return;
    try {
        await api(`/api/payroll/${id}`, 'DELETE');
        showToast('Record deleted');
        loadPayroll();
    } catch (err) { showToast(err.message, 'error'); }
}

async function generatePayroll() {
    const month = document.getElementById('payroll-month').value || new Date().toISOString().slice(0, 7);
    if (!confirm(`Generate payroll for ${month} for all active employees?`)) return;
    try {
        const data = await api('/api/payroll/generate', 'POST', { month });
        showToast(data.message);
        loadPayroll();
    } catch (err) { showToast(err.message, 'error'); }
}

// ═══════════════════════════════════════════════════════════════════
// PROJECTS
// ═══════════════════════════════════════════════════════════════════
async function loadProjects() {
    try {
        const projects = await api('/api/projects');
        renderProjects(projects);
    } catch (err) { showToast(err.message, 'error'); }
}

function renderProjects(list) {
    document.getElementById('project-grid').innerHTML = list.length ? list.map(p => {
        // Calculate progress based on dates
        let progress = 0;
        if (p.status === 'Completed') progress = 100;
        else if (p.start_date && p.end_date) {
            const start = new Date(p.start_date).getTime();
            const end = new Date(p.end_date).getTime();
            const now = Date.now();
            if (now >= end) progress = 95;
            else if (now <= start) progress = 5;
            else progress = Math.round(((now - start) / (end - start)) * 100);
        }

        const members = p.members || [];
        return `
            <div class="project-card">
                <div class="project-header">
                    <h3>${p.name}</h3>
                    ${badge(p.status)}
                </div>
                <p class="project-desc">${p.description || 'No description'}</p>
                <div class="project-meta">
                    <span>🏢 ${p.dept_name || '—'}</span>
                    <span>💰 ${formatCurrency(p.budget)}</span>
                    <span>📅 ${p.start_date || '—'}</span>
                    <span>🏁 ${p.end_date || '—'}</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width:${progress}%"></div>
                </div>
                ${members.length ? `
                    <div class="project-members">
                        ${members.slice(0, 5).map(m => {
                            const init = m.emp_name.split(' ').map(w => w[0]).join('').slice(0, 2);
                            return `<div class="member-avatar" title="${m.emp_name} — ${m.role}">${init}</div>`;
                        }).join('')}
                        ${members.length > 5 ? `<div class="member-avatar" style="background:var(--bg-input);color:var(--text-muted)">+${members.length - 5}</div>` : ''}
                    </div>
                ` : '<p style="font-size:0.8rem;color:var(--text-muted);margin-bottom:16px">No team members assigned</p>'}
                <div class="project-actions">
                    <button class="btn btn-sm btn-outline" onclick="editProject(${p.project_id})">✏️ Edit</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteProject(${p.project_id})">🗑️ Delete</button>
                </div>
            </div>
        `;
    }).join('') : '<div class="empty-state" style="grid-column:1/-1"><div class="empty-icon">📁</div><h3>No projects</h3><p>Create your first project</p></div>';
}

function openProjectModal(proj = null) {
    populateDeptSelect('project-dept', proj ? proj.dept_id : '');
    document.getElementById('project-modal-title').textContent = proj ? 'Edit Project' : 'New Project';
    document.getElementById('project-edit-id').value = proj ? proj.project_id : '';
    document.getElementById('project-name').value = proj ? proj.name : '';
    document.getElementById('project-desc').value = proj ? proj.description : '';
    document.getElementById('project-budget').value = proj ? proj.budget : '';
    document.getElementById('project-start').value = proj ? proj.start_date : new Date().toISOString().slice(0, 10);
    document.getElementById('project-end').value = proj ? proj.end_date : '';
    document.getElementById('project-status').value = proj ? proj.status : 'Planning';
    openModal('project-modal');
}

async function editProject(id) {
    try {
        const proj = await api(`/api/projects/${id}`);
        openProjectModal(proj);
    } catch (err) { showToast(err.message, 'error'); }
}

async function saveProject() {
    const id = document.getElementById('project-edit-id').value;
    const body = {
        name: document.getElementById('project-name').value.trim(),
        description: document.getElementById('project-desc').value.trim(),
        dept_id: document.getElementById('project-dept').value || null,
        budget: document.getElementById('project-budget').value || 0,
        start_date: document.getElementById('project-start').value,
        end_date: document.getElementById('project-end').value,
        status: document.getElementById('project-status').value,
    };
    if (!body.name) { showToast('Project name is required', 'error'); return; }
    try {
        if (id) {
            await api(`/api/projects/${id}`, 'PUT', body);
            showToast('Project updated');
        } else {
            await api('/api/projects', 'POST', body);
            showToast('Project created');
        }
        closeModal('project-modal');
        loadProjects();
    } catch (err) { showToast(err.message, 'error'); }
}

async function deleteProject(id) {
    if (!confirm('Delete this project?')) return;
    try {
        await api(`/api/projects/${id}`, 'DELETE');
        showToast('Project deleted');
        loadProjects();
    } catch (err) { showToast(err.message, 'error'); }
}

// ═══════════════════════════════════════════════════════════════════
// INIT — Check if already logged in
// ═══════════════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
    if (TOKEN && USER) {
        // Verify token is still valid
        api('/api/me').then(() => {
            showApp();
        }).catch(() => {
            handleLogout();
        });
    }

    // Set default dates
    const attendDate = document.getElementById('attendance-date');
    if (attendDate) attendDate.value = new Date().toISOString().slice(0, 10);

    const payMonth = document.getElementById('payroll-month');
    if (payMonth) payMonth.value = new Date().toISOString().slice(0, 7);

    // Close modals on overlay click
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) overlay.classList.remove('active');
        });
    });

    // Close modals on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal-overlay.active').forEach(m => m.classList.remove('active'));
        }
    });
});
