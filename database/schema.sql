-- ═══════════════════════════════════════════════════════════════════
-- Employee Management System — MySQL Schema
-- ═══════════════════════════════════════════════════════════════════

CREATE DATABASE IF NOT EXISTS employee_db;
USE employee_db;

-- ─── Departments ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS departments (
    dept_id       INT AUTO_INCREMENT PRIMARY KEY,
    dept_name     VARCHAR(100) UNIQUE NOT NULL,
    manager_name  VARCHAR(100) DEFAULT '',
    location      VARCHAR(200) DEFAULT '',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ─── Employees ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS employees (
    emp_id        INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(150) NOT NULL,
    email         VARCHAR(150) UNIQUE,
    phone         VARCHAR(20),
    dept_id       INT,
    designation   VARCHAR(100),
    salary        DECIMAL(12,2) DEFAULT 0,
    hire_date     DATE,
    gender        VARCHAR(10),
    address       TEXT,
    status        VARCHAR(20) DEFAULT 'Active',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id) ON DELETE SET NULL
);

-- ─── Attendance ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS attendance (
    attend_id     INT AUTO_INCREMENT PRIMARY KEY,
    emp_id        INT NOT NULL,
    attend_date   DATE NOT NULL,
    check_in      TIME,
    check_out     TIME,
    status        VARCHAR(20) DEFAULT 'Present',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (emp_id) REFERENCES employees(emp_id) ON DELETE CASCADE,
    UNIQUE KEY unique_emp_date (emp_id, attend_date)
);

-- ─── Leave Requests ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS leave_requests (
    leave_id      INT AUTO_INCREMENT PRIMARY KEY,
    emp_id        INT NOT NULL,
    leave_type    VARCHAR(50) NOT NULL,
    start_date    DATE NOT NULL,
    end_date      DATE NOT NULL,
    reason        TEXT,
    status        VARCHAR(20) DEFAULT 'Pending',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (emp_id) REFERENCES employees(emp_id) ON DELETE CASCADE
);

-- ─── Payroll ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS payroll (
    payroll_id    INT AUTO_INCREMENT PRIMARY KEY,
    emp_id        INT NOT NULL,
    pay_month     VARCHAR(7) NOT NULL,
    basic_salary  DECIMAL(12,2) DEFAULT 0,
    deductions    DECIMAL(12,2) DEFAULT 0,
    bonus         DECIMAL(12,2) DEFAULT 0,
    net_salary    DECIMAL(12,2) DEFAULT 0,
    status        VARCHAR(20) DEFAULT 'Pending',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (emp_id) REFERENCES employees(emp_id) ON DELETE CASCADE
);

-- ─── Projects ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS projects (
    project_id    INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(200) NOT NULL,
    description   TEXT,
    start_date    DATE,
    end_date      DATE,
    status        VARCHAR(30) DEFAULT 'Planning',
    budget        DECIMAL(14,2) DEFAULT 0,
    dept_id       INT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id) ON DELETE SET NULL
);

-- ─── Project Assignments ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS project_assignments (
    assign_id     INT AUTO_INCREMENT PRIMARY KEY,
    project_id    INT NOT NULL,
    emp_id        INT NOT NULL,
    role          VARCHAR(100) DEFAULT 'Member',
    assigned_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY (emp_id) REFERENCES employees(emp_id) ON DELETE CASCADE,
    UNIQUE KEY unique_proj_emp (project_id, emp_id)
);

-- ─── Users (Auth) ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    user_id       INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role          VARCHAR(30) DEFAULT 'HR',
    is_active     TINYINT DEFAULT 1,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ─── Audit Logs ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id        INT AUTO_INCREMENT PRIMARY KEY,
    action        VARCHAR(100),
    table_name    VARCHAR(50),
    record_id     INT,
    performed_by  VARCHAR(50),
    logged_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ═══════════════════════════════════════════════════════════════════
-- SEED DATA
-- ═══════════════════════════════════════════════════════════════════

-- ─── Departments ─────────────────────────────────────────────────
INSERT IGNORE INTO departments (dept_name, manager_name, location) VALUES
    ('Engineering',      'Rajesh Kumar',     'Building A, Floor 3'),
    ('Human Resources',  'Priya Sharma',     'Building A, Floor 1'),
    ('Marketing',        'Anita Desai',      'Building B, Floor 2'),
    ('Finance',          'Suresh Patel',     'Building A, Floor 2'),
    ('Operations',       'Vikram Singh',     'Building C, Floor 1');

-- ─── Employees ───────────────────────────────────────────────────
INSERT IGNORE INTO employees (name, email, phone, dept_id, designation, salary, hire_date, gender, address, status) VALUES
    ('Aarav Mehta',      'aarav@company.com',    '9800010001', 1, 'Senior Developer',    85000.00, '2022-03-15', 'Male',   'Mumbai, Maharashtra',     'Active'),
    ('Diya Sharma',      'diya@company.com',     '9800010002', 1, 'Frontend Developer',  65000.00, '2023-01-10', 'Female', 'Pune, Maharashtra',       'Active'),
    ('Rohan Gupta',      'rohan@company.com',    '9800010003', 2, 'HR Manager',          75000.00, '2021-07-20', 'Male',   'Delhi, NCR',              'Active'),
    ('Kavya Nair',       'kavya@company.com',    '9800010004', 3, 'Marketing Lead',      70000.00, '2022-09-05', 'Female', 'Chennai, Tamil Nadu',     'Active'),
    ('Arjun Reddy',      'arjun@company.com',    '9800010005', 4, 'Financial Analyst',   72000.00, '2023-04-12', 'Male',   'Hyderabad, Telangana',    'Active'),
    ('Sneha Iyer',       'sneha@company.com',    '9800010006', 1, 'Backend Developer',   78000.00, '2022-11-01', 'Female', 'Bengaluru, Karnataka',    'Active'),
    ('Vikash Yadav',     'vikash@company.com',   '9800010007', 5, 'Operations Manager',  80000.00, '2021-02-18', 'Male',   'Lucknow, Uttar Pradesh',  'Active'),
    ('Ananya Joshi',     'ananya@company.com',   '9800010008', 3, 'Content Strategist',  55000.00, '2024-01-08', 'Female', 'Jaipur, Rajasthan',       'Active'),
    ('Rahul Verma',      'rahul@company.com',    '9800010009', 4, 'Accountant',          60000.00, '2023-06-22', 'Male',   'Kolkata, West Bengal',    'Active'),
    ('Meera Pillai',     'meera@company.com',    '9800010010', 2, 'HR Executive',        50000.00, '2024-03-15', 'Female', 'Kochi, Kerala',           'On Leave');

-- ─── Attendance (current month sample) ───────────────────────────
INSERT IGNORE INTO attendance (emp_id, attend_date, check_in, check_out, status) VALUES
    (1, CURDATE(), '09:00:00', '18:00:00', 'Present'),
    (2, CURDATE(), '09:15:00', '18:05:00', 'Present'),
    (3, CURDATE(), '09:30:00', '17:45:00', 'Late'),
    (4, CURDATE(), '09:00:00', '13:00:00', 'Half-Day'),
    (5, CURDATE(), '08:45:00', '18:10:00', 'Present'),
    (6, CURDATE(), '09:05:00', '18:00:00', 'Present'),
    (7, CURDATE(), NULL,       NULL,       'Absent'),
    (8, CURDATE(), '09:00:00', '18:00:00', 'Present'),
    (9, CURDATE(), '09:10:00', '18:00:00', 'Present'),
    (1, DATE_SUB(CURDATE(), INTERVAL 1 DAY), '09:00:00', '18:00:00', 'Present'),
    (2, DATE_SUB(CURDATE(), INTERVAL 1 DAY), '09:00:00', '18:00:00', 'Present'),
    (3, DATE_SUB(CURDATE(), INTERVAL 1 DAY), '09:00:00', '18:00:00', 'Present'),
    (4, DATE_SUB(CURDATE(), INTERVAL 1 DAY), '09:00:00', '18:00:00', 'Present'),
    (5, DATE_SUB(CURDATE(), INTERVAL 1 DAY), '08:50:00', '18:15:00', 'Present'),
    (6, DATE_SUB(CURDATE(), INTERVAL 1 DAY), NULL,       NULL,       'Absent');

-- ─── Leave Requests ──────────────────────────────────────────────
INSERT IGNORE INTO leave_requests (emp_id, leave_type, start_date, end_date, reason, status) VALUES
    (10, 'Sick Leave',    CURDATE(), DATE_ADD(CURDATE(), INTERVAL 3 DAY), 'Fever and cold',              'Approved'),
    (1,  'Casual Leave',  DATE_ADD(CURDATE(), INTERVAL 5 DAY), DATE_ADD(CURDATE(), INTERVAL 6 DAY), 'Personal work',  'Pending'),
    (4,  'Casual Leave',  CURDATE(), CURDATE(), 'Family function — half day', 'Approved'),
    (7,  'Sick Leave',    CURDATE(), DATE_ADD(CURDATE(), INTERVAL 1 DAY), 'Not feeling well',            'Pending'),
    (3,  'Annual Leave',  DATE_ADD(CURDATE(), INTERVAL 10 DAY), DATE_ADD(CURDATE(), INTERVAL 15 DAY), 'Vacation',  'Pending');

-- ─── Payroll (current month) ─────────────────────────────────────
INSERT IGNORE INTO payroll (emp_id, pay_month, basic_salary, deductions, bonus, net_salary, status) VALUES
    (1,  DATE_FORMAT(CURDATE(), '%Y-%m'), 85000, 8500, 5000, 81500, 'Paid'),
    (2,  DATE_FORMAT(CURDATE(), '%Y-%m'), 65000, 6500, 3000, 61500, 'Paid'),
    (3,  DATE_FORMAT(CURDATE(), '%Y-%m'), 75000, 7500, 4000, 71500, 'Paid'),
    (4,  DATE_FORMAT(CURDATE(), '%Y-%m'), 70000, 7000, 2000, 65000, 'Paid'),
    (5,  DATE_FORMAT(CURDATE(), '%Y-%m'), 72000, 7200, 3000, 67800, 'Pending'),
    (6,  DATE_FORMAT(CURDATE(), '%Y-%m'), 78000, 7800, 4500, 74700, 'Pending'),
    (7,  DATE_FORMAT(CURDATE(), '%Y-%m'), 80000, 8000, 5000, 77000, 'Paid'),
    (8,  DATE_FORMAT(CURDATE(), '%Y-%m'), 55000, 5500, 1500, 51000, 'Pending'),
    (9,  DATE_FORMAT(CURDATE(), '%Y-%m'), 60000, 6000, 2000, 56000, 'Pending'),
    (10, DATE_FORMAT(CURDATE(), '%Y-%m'), 50000, 5000, 1000, 46000, 'Pending');

-- ─── Projects ────────────────────────────────────────────────────
INSERT IGNORE INTO projects (name, description, start_date, end_date, status, budget, dept_id) VALUES
    ('Website Redesign',     'Complete overhaul of company website with modern UI/UX',        '2026-01-15', '2026-08-30', 'In Progress', 500000.00, 1),
    ('HR Automation',        'Automate leave management and payroll processing',               '2026-03-01', '2026-12-31', 'In Progress', 350000.00, 2),
    ('Q3 Marketing Campaign','Multi-channel marketing push for Q3 product launch',             '2026-07-01', '2026-09-30', 'In Progress', 250000.00, 3),
    ('Annual Audit Prep',    'Prepare financial documents and reports for annual audit',        '2026-06-01', '2026-07-31', 'Completed',   150000.00, 4);

-- ─── Project Assignments ─────────────────────────────────────────
INSERT IGNORE INTO project_assignments (project_id, emp_id, role) VALUES
    (1, 1, 'Tech Lead'),
    (1, 2, 'Frontend Developer'),
    (1, 6, 'Backend Developer'),
    (2, 3, 'Project Manager'),
    (2, 10, 'Team Member'),
    (3, 4, 'Campaign Lead'),
    (3, 8, 'Content Creator'),
    (4, 5, 'Lead Analyst'),
    (4, 9, 'Accountant');
