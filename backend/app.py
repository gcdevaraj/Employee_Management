import os
import sqlite3
import secrets
import hashlib
from datetime import date, timedelta
from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS

try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

try:
    import bcrypt as _bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False

_frontend = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
app = Flask(__name__, static_folder=_frontend, static_url_path="")
app.secret_key = os.environ.get("SECRET_KEY", "ems-secret-key-2026")
CORS(app, supports_credentials=True)

# ─── Active Tokens (in-memory) ───────────────────────────────────
ACTIVE_TOKENS = {}   # token -> {"user_id":…, "username":…, "role":…}

# ─── DB Configuration ────────────────────────────────────────────
MYSQL_CONFIG = {
    "host":            os.environ.get("MYSQL_HOST",     "localhost"),
    "user":            os.environ.get("MYSQL_USER",     "root"),
    "password":        os.environ.get("MYSQL_PASSWORD", "Deva@8934"),
    "database":        os.environ.get("MYSQL_DB",       "employee_db"),
    "port":            int(os.environ.get("MYSQL_PORT", 3306)),
    "connect_timeout": 3,
}

# ─── Database Connection ─────────────────────────────────────────
def get_db():
    if MYSQL_AVAILABLE:
        try:
            conn = mysql.connector.connect(**MYSQL_CONFIG)
            return conn, "mysql"
        except Exception as e:
            print(f"[MySQL Fallback] {e}")
    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), "ems_fallback.db"), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    _init_sqlite(conn)
    return conn, "sqlite"

def _init_sqlite(conn):
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS departments (
            dept_id INTEGER PRIMARY KEY AUTOINCREMENT,
            dept_name TEXT UNIQUE NOT NULL,
            manager_name TEXT DEFAULT '',
            location TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS employees (
            emp_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            phone TEXT,
            dept_id INTEGER,
            designation TEXT,
            salary REAL DEFAULT 0,
            hire_date TEXT,
            gender TEXT,
            address TEXT,
            status TEXT DEFAULT 'Active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS attendance (
            attend_id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id INTEGER NOT NULL,
            attend_date TEXT NOT NULL,
            check_in TEXT,
            check_out TEXT,
            status TEXT DEFAULT 'Present',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(emp_id, attend_date)
        );
        CREATE TABLE IF NOT EXISTS leave_requests (
            leave_id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id INTEGER NOT NULL,
            leave_type TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS payroll (
            payroll_id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id INTEGER NOT NULL,
            pay_month TEXT NOT NULL,
            basic_salary REAL DEFAULT 0,
            deductions REAL DEFAULT 0,
            bonus REAL DEFAULT 0,
            net_salary REAL DEFAULT 0,
            status TEXT DEFAULT 'Pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS projects (
            project_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            start_date TEXT,
            end_date TEXT,
            status TEXT DEFAULT 'Planning',
            budget REAL DEFAULT 0,
            dept_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS project_assignments (
            assign_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            emp_id INTEGER NOT NULL,
            role TEXT DEFAULT 'Member',
            assigned_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(project_id, emp_id)
        );
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'HR',
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS audit_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT,
            table_name TEXT,
            record_id INTEGER,
            performed_by TEXT,
            logged_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # ── Seed data ──
    c.execute("SELECT COUNT(*) FROM departments")
    if c.fetchone()[0] == 0:
        today = date.today().isoformat()
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        month = date.today().strftime("%Y-%m")

        c.executemany("INSERT INTO departments (dept_name, manager_name, location) VALUES (?,?,?)", [
            ("Engineering",     "Rajesh Kumar",  "Building A, Floor 3"),
            ("Human Resources", "Priya Sharma",  "Building A, Floor 1"),
            ("Marketing",       "Anita Desai",   "Building B, Floor 2"),
            ("Finance",         "Suresh Patel",  "Building A, Floor 2"),
            ("Operations",      "Vikram Singh",  "Building C, Floor 1"),
        ])
        c.executemany("INSERT INTO employees (name,email,phone,dept_id,designation,salary,hire_date,gender,address,status) VALUES (?,?,?,?,?,?,?,?,?,?)", [
            ("Aarav Mehta",   "aarav@company.com",   "9800010001",1,"Senior Developer",  85000,"2022-03-15","Male",  "Mumbai, Maharashtra",    "Active"),
            ("Diya Sharma",   "diya@company.com",    "9800010002",1,"Frontend Developer", 65000,"2023-01-10","Female","Pune, Maharashtra",      "Active"),
            ("Rohan Gupta",   "rohan@company.com",   "9800010003",2,"HR Manager",         75000,"2021-07-20","Male",  "Delhi, NCR",             "Active"),
            ("Kavya Nair",    "kavya@company.com",   "9800010004",3,"Marketing Lead",     70000,"2022-09-05","Female","Chennai, Tamil Nadu",     "Active"),
            ("Arjun Reddy",   "arjun@company.com",   "9800010005",4,"Financial Analyst",  72000,"2023-04-12","Male",  "Hyderabad, Telangana",   "Active"),
            ("Sneha Iyer",    "sneha@company.com",   "9800010006",1,"Backend Developer",  78000,"2022-11-01","Female","Bengaluru, Karnataka",   "Active"),
            ("Vikash Yadav",  "vikash@company.com",  "9800010007",5,"Operations Manager", 80000,"2021-02-18","Male",  "Lucknow, Uttar Pradesh", "Active"),
            ("Ananya Joshi",  "ananya@company.com",  "9800010008",3,"Content Strategist", 55000,"2024-01-08","Female","Jaipur, Rajasthan",      "Active"),
            ("Rahul Verma",   "rahul@company.com",   "9800010009",4,"Accountant",         60000,"2023-06-22","Male",  "Kolkata, West Bengal",   "Active"),
            ("Meera Pillai",  "meera@company.com",   "9800010010",2,"HR Executive",       50000,"2024-03-15","Female","Kochi, Kerala",          "On Leave"),
        ])
        c.executemany("INSERT INTO attendance (emp_id,attend_date,check_in,check_out,status) VALUES (?,?,?,?,?)", [
            (1,today,"09:00","18:00","Present"),(2,today,"09:15","18:05","Present"),
            (3,today,"09:30","17:45","Late"),(4,today,"09:00","13:00","Half-Day"),
            (5,today,"08:45","18:10","Present"),(6,today,"09:05","18:00","Present"),
            (7,today,None,None,"Absent"),(8,today,"09:00","18:00","Present"),
            (9,today,"09:10","18:00","Present"),
            (1,yesterday,"09:00","18:00","Present"),(2,yesterday,"09:00","18:00","Present"),
            (3,yesterday,"09:00","18:00","Present"),(4,yesterday,"09:00","18:00","Present"),
            (5,yesterday,"08:50","18:15","Present"),(6,yesterday,None,None,"Absent"),
        ])
        c.executemany("INSERT INTO leave_requests (emp_id,leave_type,start_date,end_date,reason,status) VALUES (?,?,?,?,?,?)", [
            (10,"Sick Leave",   today,(date.today()+timedelta(days=3)).isoformat(),"Fever and cold","Approved"),
            (1, "Casual Leave", (date.today()+timedelta(days=5)).isoformat(),(date.today()+timedelta(days=6)).isoformat(),"Personal work","Pending"),
            (4, "Casual Leave", today,today,"Family function — half day","Approved"),
            (7, "Sick Leave",   today,(date.today()+timedelta(days=1)).isoformat(),"Not feeling well","Pending"),
            (3, "Annual Leave", (date.today()+timedelta(days=10)).isoformat(),(date.today()+timedelta(days=15)).isoformat(),"Vacation","Pending"),
        ])
        c.executemany("INSERT INTO payroll (emp_id,pay_month,basic_salary,deductions,bonus,net_salary,status) VALUES (?,?,?,?,?,?,?)", [
            (1,month,85000,8500,5000,81500,"Paid"),(2,month,65000,6500,3000,61500,"Paid"),
            (3,month,75000,7500,4000,71500,"Paid"),(4,month,70000,7000,2000,65000,"Paid"),
            (5,month,72000,7200,3000,67800,"Pending"),(6,month,78000,7800,4500,74700,"Pending"),
            (7,month,80000,8000,5000,77000,"Paid"),(8,month,55000,5500,1500,51000,"Pending"),
            (9,month,60000,6000,2000,56000,"Pending"),(10,month,50000,5000,1000,46000,"Pending"),
        ])
        c.executemany("INSERT INTO projects (name,description,start_date,end_date,status,budget,dept_id) VALUES (?,?,?,?,?,?,?)", [
            ("Website Redesign","Complete overhaul of company website","2026-01-15","2026-08-30","In Progress",500000,1),
            ("HR Automation","Automate leave and payroll","2026-03-01","2026-12-31","In Progress",350000,2),
            ("Q3 Marketing Campaign","Multi-channel push for Q3","2026-07-01","2026-09-30","In Progress",250000,3),
            ("Annual Audit Prep","Prepare docs for annual audit","2026-06-01","2026-07-31","Completed",150000,4),
        ])
        c.executemany("INSERT INTO project_assignments (project_id,emp_id,role) VALUES (?,?,?)", [
            (1,1,"Tech Lead"),(1,2,"Frontend Developer"),(1,6,"Backend Developer"),
            (2,3,"Project Manager"),(2,10,"Team Member"),
            (3,4,"Campaign Lead"),(3,8,"Content Creator"),
            (4,5,"Lead Analyst"),(4,9,"Accountant"),
        ])
        conn.commit()

    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users (username,password_hash,role) VALUES (?,?,?)",
                  ("admin", _hash_password("admin123"), "Admin"))
        c.execute("INSERT INTO users (username,password_hash,role) VALUES (?,?,?)",
                  ("hr", _hash_password("hr123"), "HR"))
        conn.commit()

# ─── Password helpers ────────────────────────────────────────────
def _hash_password(pw):
    if BCRYPT_AVAILABLE:
        return _bcrypt.hashpw(pw.encode(), _bcrypt.gensalt()).decode()
    return hashlib.sha256(pw.encode()).hexdigest()

def _check_password(pw, pw_hash):
    if BCRYPT_AVAILABLE:
        try:
            return _bcrypt.checkpw(pw.encode(), pw_hash.encode())
        except Exception:
            pass
    return hashlib.sha256(pw.encode()).hexdigest() == pw_hash

# ─── DB helpers ──────────────────────────────────────────────────
def fetchall_as_dict(cursor, db_type):
    if db_type == "mysql":
        cols = [d[0] for d in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]
    return [dict(row) for row in cursor.fetchall()]

def fetchone_as_dict(cursor, db_type):
    if db_type == "mysql":
        cols = [d[0] for d in cursor.description]
        row  = cursor.fetchone()
        return dict(zip(cols, row)) if row else None
    row = cursor.fetchone()
    return dict(row) if row else None

def ph(db_type):
    return "%s" if db_type == "mysql" else "?"

def _join(db_type):
    return "JOIN" if db_type == "mysql" else "LEFT JOIN"

# ─── Audit helper ────────────────────────────────────────────────
def log_action(action, table, rec_id, by="system"):
    try:
        conn, db = get_db()
        c = conn.cursor(); p = ph(db)
        c.execute(f"INSERT INTO audit_logs (action,table_name,record_id,performed_by) VALUES ({p},{p},{p},{p})",
                  (action, table, rec_id, by))
        conn.commit(); conn.close()
    except Exception:
        pass

# ─── Auth helpers ────────────────────────────────────────────────
def get_current_user():
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return ACTIVE_TOKENS.get(auth[7:])
    return None

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not get_current_user():
            return jsonify({"error": "Unauthorized. Please login."}), 401
        return f(*args, **kwargs)
    return decorated

def _username():
    u = get_current_user()
    return u["username"] if u else "system"

# ─── Serve Frontend ──────────────────────────────────────────────
@app.route("/")
def index():
    return app.send_static_file("index.html")

# ════════════════════════════════════════════════════════════════════
# HEALTH
# ════════════════════════════════════════════════════════════════════
@app.route("/api/health", methods=["GET"])
def health():
    conn, db = get_db(); conn.close()
    return jsonify({"status": "ok", "database": db})

# ════════════════════════════════════════════════════════════════════
# AUTH
# ════════════════════════════════════════════════════════════════════
@app.route("/api/login", methods=["POST"])
def login():
    d = request.json or {}
    username = d.get("username", "").strip()
    password = d.get("password", "")
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
    conn, db = get_db(); c = conn.cursor(); p = ph(db)
    c.execute(f"SELECT user_id,username,password_hash,role FROM users WHERE username={p} AND is_active=1", (username,))
    user = fetchone_as_dict(c, db); conn.close()
    if not user or not _check_password(password, user["password_hash"]):
        return jsonify({"error": "Invalid username or password"}), 401
    token = secrets.token_hex(32)
    ACTIVE_TOKENS[token] = {"user_id": user["user_id"], "username": user["username"], "role": user["role"]}
    log_action("LOGIN", "users", user["user_id"], username)
    return jsonify({"token": token, "username": user["username"], "role": user["role"]})

@app.route("/api/logout", methods=["POST"])
def logout():
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        ACTIVE_TOKENS.pop(auth[7:], None)
    return jsonify({"message": "Logged out"})

@app.route("/api/me", methods=["GET"])
@require_auth
def me():
    return jsonify(get_current_user())

# ════════════════════════════════════════════════════════════════════
# DASHBOARD STATS + CHARTS
# ════════════════════════════════════════════════════════════════════
@app.route("/api/stats", methods=["GET"])
@require_auth
def stats():
    conn, db = get_db(); c = conn.cursor(); p = ph(db)
    today = date.today().isoformat()
    c.execute("SELECT COUNT(*) FROM employees"); total_employees = c.fetchone()[0]
    c.execute(f"SELECT COUNT(*) FROM employees WHERE status={p}", ("Active",)); active_employees = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM departments"); total_departments = c.fetchone()[0]
    c.execute(f"SELECT COUNT(*) FROM attendance WHERE attend_date={p} AND status={p}", (today, "Present")); present_today = c.fetchone()[0]
    c.execute(f"SELECT COUNT(*) FROM attendance WHERE attend_date={p} AND status={p}", (today, "Absent")); absent_today = c.fetchone()[0]
    c.execute(f"SELECT COUNT(*) FROM leave_requests WHERE status={p}", ("Pending",)); pending_leaves = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(net_salary),0) FROM payroll WHERE status='Paid'" if db == "sqlite"
              else "SELECT IFNULL(SUM(net_salary),0) FROM payroll WHERE status='Paid'")
    total_paid = float(c.fetchone()[0])
    c.execute(f"SELECT COUNT(*) FROM projects WHERE status={p}", ("In Progress",)); active_projects = c.fetchone()[0]
    conn.close()
    return jsonify({
        "total_employees": total_employees, "active_employees": active_employees,
        "total_departments": total_departments, "present_today": present_today,
        "absent_today": absent_today, "pending_leaves": pending_leaves,
        "total_paid_salary": round(total_paid, 2), "active_projects": active_projects,
    })

@app.route("/api/charts/department-distribution", methods=["GET"])
@require_auth
def chart_dept_dist():
    conn, db = get_db(); c = conn.cursor()
    c.execute("SELECT d.dept_name, COUNT(e.emp_id) AS count FROM departments d LEFT JOIN employees e ON d.dept_id=e.dept_id GROUP BY d.dept_id, d.dept_name")
    data = fetchall_as_dict(c, db); conn.close()
    return jsonify(data)

@app.route("/api/charts/attendance-summary", methods=["GET"])
@require_auth
def chart_attendance():
    conn, db = get_db(); c = conn.cursor(); p = ph(db)
    today = date.today().isoformat()
    result = {}
    for s in ["Present", "Absent", "Late", "Half-Day"]:
        c.execute(f"SELECT COUNT(*) FROM attendance WHERE attend_date={p} AND status={p}", (today, s))
        result[s] = c.fetchone()[0]
    conn.close()
    return jsonify(result)

@app.route("/api/charts/salary-overview", methods=["GET"])
@require_auth
def chart_salary():
    conn, db = get_db(); c = conn.cursor()
    c.execute("SELECT d.dept_name, COALESCE(SUM(e.salary),0) AS total_salary, COUNT(e.emp_id) AS count FROM departments d LEFT JOIN employees e ON d.dept_id=e.dept_id GROUP BY d.dept_id, d.dept_name")
    data = fetchall_as_dict(c, db); conn.close()
    return jsonify(data)

# ════════════════════════════════════════════════════════════════════
# EMPLOYEES — Full CRUD
# ════════════════════════════════════════════════════════════════════
@app.route("/api/employees", methods=["GET"])
@require_auth
def list_employees():
    conn, db = get_db(); c = conn.cursor(); j = _join(db)
    c.execute(f"SELECT e.emp_id,e.name,e.email,e.phone,d.dept_name,e.designation,e.salary,e.hire_date,e.gender,e.address,e.status,e.dept_id FROM employees e {j} departments d ON e.dept_id=d.dept_id ORDER BY e.emp_id")
    data = fetchall_as_dict(c, db); conn.close()
    return jsonify(data)

@app.route("/api/employees/<int:eid>", methods=["GET"])
@require_auth
def get_employee(eid):
    conn, db = get_db(); c = conn.cursor(); p = ph(db); j = _join(db)
    c.execute(f"SELECT e.*,d.dept_name FROM employees e {j} departments d ON e.dept_id=d.dept_id WHERE e.emp_id={p}", (eid,))
    data = fetchone_as_dict(c, db); conn.close()
    return jsonify(data) if data else (jsonify({"error": "Not found"}), 404)

@app.route("/api/employees/<int:eid>/profile", methods=["GET"])
@require_auth
def employee_profile(eid):
    conn, db = get_db(); c = conn.cursor(); p = ph(db); j = _join(db)
    c.execute(f"SELECT e.*,d.dept_name FROM employees e {j} departments d ON e.dept_id=d.dept_id WHERE e.emp_id={p}", (eid,))
    employee = fetchone_as_dict(c, db)
    if not employee:
        conn.close(); return jsonify({"error": "Not found"}), 404
    c.execute(f"SELECT * FROM attendance WHERE emp_id={p} ORDER BY attend_date DESC LIMIT 30", (eid,))
    attendance = fetchall_as_dict(c, db)
    c.execute(f"SELECT * FROM leave_requests WHERE emp_id={p} ORDER BY leave_id DESC", (eid,))
    leaves = fetchall_as_dict(c, db)
    c.execute(f"SELECT * FROM payroll WHERE emp_id={p} ORDER BY pay_month DESC", (eid,))
    payroll = fetchall_as_dict(c, db)
    c.execute(f"SELECT pa.role, pr.name AS project_name, pr.status AS project_status FROM project_assignments pa {j} projects pr ON pa.project_id=pr.project_id WHERE pa.emp_id={p}", (eid,))
    projects = fetchall_as_dict(c, db)
    conn.close()
    return jsonify({"employee": employee, "attendance": attendance, "leaves": leaves, "payroll": payroll, "projects": projects})

@app.route("/api/employees", methods=["POST"])
@require_auth
def add_employee():
    d = request.json
    for f in ["name", "email", "phone", "dept_id", "designation", "salary"]:
        if not d.get(f): return jsonify({"error": f"'{f}' is required"}), 400
    conn, db = get_db(); c = conn.cursor(); p = ph(db)
    try:
        c.execute(f"INSERT INTO employees (name,email,phone,dept_id,designation,salary,hire_date,gender,address,status) VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},'Active')",
                  (d["name"],d["email"],d["phone"],d["dept_id"],d["designation"],float(d["salary"]),d.get("hire_date",date.today().isoformat()),d.get("gender",""),d.get("address","")))
        conn.commit(); new_id = c.lastrowid; conn.close()
        log_action("ADD_EMPLOYEE","employees",new_id,_username())
        return jsonify({"message": "Employee added", "emp_id": new_id}), 201
    except Exception as e:
        conn.close(); return jsonify({"error": str(e)}), 500

@app.route("/api/employees/<int:eid>", methods=["PUT"])
@require_auth
def edit_employee(eid):
    d = request.json; conn, db = get_db(); c = conn.cursor(); p = ph(db)
    try:
        c.execute(f"UPDATE employees SET name={p},email={p},phone={p},dept_id={p},designation={p},salary={p},hire_date={p},gender={p},address={p},status={p} WHERE emp_id={p}",
                  (d.get("name"),d.get("email"),d.get("phone"),d.get("dept_id"),d.get("designation"),float(d.get("salary",0)),d.get("hire_date"),d.get("gender",""),d.get("address",""),d.get("status","Active"),eid))
        conn.commit(); conn.close()
        log_action("EDIT_EMPLOYEE","employees",eid,_username())
        return jsonify({"message": "Employee updated"})
    except Exception as e:
        conn.close(); return jsonify({"error": str(e)}), 500

@app.route("/api/employees/<int:eid>", methods=["DELETE"])
@require_auth
def delete_employee(eid):
    conn, db = get_db(); c = conn.cursor(); p = ph(db)
    try:
        c.execute(f"DELETE FROM employees WHERE emp_id={p}", (eid,))
        conn.commit(); conn.close()
        log_action("DELETE_EMPLOYEE","employees",eid,_username())
        return jsonify({"message": "Employee deleted"})
    except Exception as e:
        conn.close(); return jsonify({"error": str(e)}), 500

# ════════════════════════════════════════════════════════════════════
# DEPARTMENTS — Full CRUD
# ════════════════════════════════════════════════════════════════════
@app.route("/api/departments", methods=["GET"])
@require_auth
def list_departments():
    conn, db = get_db(); c = conn.cursor()
    c.execute("SELECT d.dept_id,d.dept_name,d.manager_name,d.location,COUNT(e.emp_id) AS total_employees FROM departments d LEFT JOIN employees e ON d.dept_id=e.dept_id GROUP BY d.dept_id")
    data = fetchall_as_dict(c, db); conn.close()
    return jsonify(data)

@app.route("/api/departments/<int:did>", methods=["GET"])
@require_auth
def get_department(did):
    conn, db = get_db(); c = conn.cursor(); p = ph(db)
    c.execute(f"SELECT * FROM departments WHERE dept_id={p}", (did,))
    data = fetchone_as_dict(c, db); conn.close()
    return jsonify(data) if data else (jsonify({"error": "Not found"}), 404)

@app.route("/api/departments", methods=["POST"])
@require_auth
def add_department():
    d = request.json
    if not d.get("dept_name"): return jsonify({"error": "'dept_name' is required"}), 400
    conn, db = get_db(); c = conn.cursor(); p = ph(db)
    try:
        c.execute(f"INSERT INTO departments (dept_name,manager_name,location) VALUES ({p},{p},{p})",
                  (d["dept_name"],d.get("manager_name",""),d.get("location","")))
        conn.commit(); new_id = c.lastrowid; conn.close()
        log_action("ADD_DEPT","departments",new_id,_username())
        return jsonify({"message": "Department added", "dept_id": new_id}), 201
    except Exception as e:
        conn.close(); return jsonify({"error": str(e)}), 500

@app.route("/api/departments/<int:did>", methods=["PUT"])
@require_auth
def edit_department(did):
    d = request.json; conn, db = get_db(); c = conn.cursor(); p = ph(db)
    try:
        c.execute(f"UPDATE departments SET dept_name={p},manager_name={p},location={p} WHERE dept_id={p}",
                  (d.get("dept_name"),d.get("manager_name",""),d.get("location",""),did))
        conn.commit(); conn.close()
        log_action("EDIT_DEPT","departments",did,_username())
        return jsonify({"message": "Department updated"})
    except Exception as e:
        conn.close(); return jsonify({"error": str(e)}), 500

@app.route("/api/departments/<int:did>", methods=["DELETE"])
@require_auth
def delete_department(did):
    conn, db = get_db(); c = conn.cursor(); p = ph(db)
    try:
        c.execute(f"DELETE FROM departments WHERE dept_id={p}", (did,))
        conn.commit(); conn.close()
        log_action("DELETE_DEPT","departments",did,_username())
        return jsonify({"message": "Department deleted"})
    except Exception as e:
        conn.close(); return jsonify({"error": str(e)}), 500

# ════════════════════════════════════════════════════════════════════
# ATTENDANCE
# ════════════════════════════════════════════════════════════════════
@app.route("/api/attendance", methods=["GET"])
@require_auth
def list_attendance():
    attend_date = request.args.get("date", date.today().isoformat())
    conn, db = get_db(); c = conn.cursor(); p = ph(db); j = _join(db)
    c.execute(f"SELECT a.attend_id,e.name AS emp_name,e.designation,d.dept_name,a.attend_date,a.check_in,a.check_out,a.status,a.emp_id FROM attendance a {j} employees e ON a.emp_id=e.emp_id {j} departments d ON e.dept_id=d.dept_id WHERE a.attend_date={p} ORDER BY e.name", (attend_date,))
    data = fetchall_as_dict(c, db); conn.close()
    return jsonify(data)

@app.route("/api/attendance", methods=["POST"])
@require_auth
def mark_attendance():
    d = request.json
    if not d.get("emp_id") or not d.get("attend_date"):
        return jsonify({"error": "emp_id and attend_date required"}), 400
    conn, db = get_db(); c = conn.cursor(); p = ph(db)
    try:
        # Try to insert, on conflict update
        if db == "mysql":
            c.execute(f"INSERT INTO attendance (emp_id,attend_date,check_in,check_out,status) VALUES ({p},{p},{p},{p},{p}) ON DUPLICATE KEY UPDATE check_in=VALUES(check_in),check_out=VALUES(check_out),status=VALUES(status)",
                      (d["emp_id"],d["attend_date"],d.get("check_in"),d.get("check_out"),d.get("status","Present")))
        else:
            c.execute(f"INSERT OR REPLACE INTO attendance (emp_id,attend_date,check_in,check_out,status) VALUES ({p},{p},{p},{p},{p})",
                      (d["emp_id"],d["attend_date"],d.get("check_in"),d.get("check_out"),d.get("status","Present")))
        conn.commit(); conn.close()
        log_action("MARK_ATTENDANCE","attendance",d["emp_id"],_username())
        return jsonify({"message": "Attendance marked"}), 201
    except Exception as e:
        conn.close(); return jsonify({"error": str(e)}), 500

@app.route("/api/attendance/bulk", methods=["POST"])
@require_auth
def bulk_attendance():
    records = request.json
    if not isinstance(records, list):
        return jsonify({"error": "Expected a list of records"}), 400
    conn, db = get_db(); c = conn.cursor(); p = ph(db)
    count = 0
    try:
        for d in records:
            if db == "mysql":
                c.execute(f"INSERT INTO attendance (emp_id,attend_date,check_in,check_out,status) VALUES ({p},{p},{p},{p},{p}) ON DUPLICATE KEY UPDATE check_in=VALUES(check_in),check_out=VALUES(check_out),status=VALUES(status)",
                          (d["emp_id"],d["attend_date"],d.get("check_in"),d.get("check_out"),d.get("status","Present")))
            else:
                c.execute(f"INSERT OR REPLACE INTO attendance (emp_id,attend_date,check_in,check_out,status) VALUES ({p},{p},{p},{p},{p})",
                          (d["emp_id"],d["attend_date"],d.get("check_in"),d.get("check_out"),d.get("status","Present")))
            count += 1
        conn.commit(); conn.close()
        return jsonify({"message": f"{count} attendance records saved"}), 201
    except Exception as e:
        conn.close(); return jsonify({"error": str(e)}), 500

@app.route("/api/attendance/<int:aid>", methods=["DELETE"])
@require_auth
def delete_attendance(aid):
    conn, db = get_db(); c = conn.cursor(); p = ph(db)
    try:
        c.execute(f"DELETE FROM attendance WHERE attend_id={p}", (aid,))
        conn.commit(); conn.close()
        return jsonify({"message": "Record deleted"})
    except Exception as e:
        conn.close(); return jsonify({"error": str(e)}), 500

# ════════════════════════════════════════════════════════════════════
# LEAVE REQUESTS
# ════════════════════════════════════════════════════════════════════
@app.route("/api/leave", methods=["GET"])
@require_auth
def list_leave():
    conn, db = get_db(); c = conn.cursor(); j = _join(db)
    c.execute(f"SELECT l.leave_id,e.name AS emp_name,e.designation,l.leave_type,l.start_date,l.end_date,l.reason,l.status,l.emp_id FROM leave_requests l {j} employees e ON l.emp_id=e.emp_id ORDER BY l.leave_id DESC")
    data = fetchall_as_dict(c, db); conn.close()
    return jsonify(data)

@app.route("/api/leave", methods=["POST"])
@require_auth
def add_leave():
    d = request.json
    for f in ["emp_id","leave_type","start_date","end_date"]:
        if not d.get(f): return jsonify({"error": f"'{f}' is required"}), 400
    conn, db = get_db(); c = conn.cursor(); p = ph(db)
    try:
        c.execute(f"INSERT INTO leave_requests (emp_id,leave_type,start_date,end_date,reason,status) VALUES ({p},{p},{p},{p},{p},'Pending')",
                  (d["emp_id"],d["leave_type"],d["start_date"],d["end_date"],d.get("reason","")))
        conn.commit(); new_id = c.lastrowid; conn.close()
        log_action("ADD_LEAVE","leave_requests",new_id,_username())
        return jsonify({"message": "Leave request submitted", "leave_id": new_id}), 201
    except Exception as e:
        conn.close(); return jsonify({"error": str(e)}), 500

@app.route("/api/leave/<int:lid>/status", methods=["PUT"])
@require_auth
def update_leave_status(lid):
    d = request.json; new_status = d.get("status")
    if new_status not in ["Approved","Rejected"]:
        return jsonify({"error": "Status must be 'Approved' or 'Rejected'"}), 400
    conn, db = get_db(); c = conn.cursor(); p = ph(db)
    c.execute(f"UPDATE leave_requests SET status={p} WHERE leave_id={p}", (new_status, lid))
    conn.commit(); conn.close()
    log_action(f"LEAVE_{new_status.upper()}","leave_requests",lid,_username())
    return jsonify({"message": f"Leave {new_status.lower()}"})

@app.route("/api/leave/<int:lid>", methods=["DELETE"])
@require_auth
def delete_leave(lid):
    conn, db = get_db(); c = conn.cursor(); p = ph(db)
    try:
        c.execute(f"DELETE FROM leave_requests WHERE leave_id={p}", (lid,))
        conn.commit(); conn.close()
        return jsonify({"message": "Leave request deleted"})
    except Exception as e:
        conn.close(); return jsonify({"error": str(e)}), 500

# ════════════════════════════════════════════════════════════════════
# PAYROLL
# ════════════════════════════════════════════════════════════════════
@app.route("/api/payroll", methods=["GET"])
@require_auth
def list_payroll():
    month = request.args.get("month", date.today().strftime("%Y-%m"))
    conn, db = get_db(); c = conn.cursor(); p = ph(db); j = _join(db)
    c.execute(f"SELECT pr.payroll_id,e.name AS emp_name,e.designation,d.dept_name,pr.pay_month,pr.basic_salary,pr.deductions,pr.bonus,pr.net_salary,pr.status,pr.emp_id FROM payroll pr {j} employees e ON pr.emp_id=e.emp_id {j} departments d ON e.dept_id=d.dept_id WHERE pr.pay_month={p} ORDER BY e.name", (month,))
    data = fetchall_as_dict(c, db); conn.close()
    return jsonify(data)

@app.route("/api/payroll", methods=["POST"])
@require_auth
def add_payroll():
    d = request.json
    for f in ["emp_id","pay_month","basic_salary"]:
        if not d.get(f): return jsonify({"error": f"'{f}' is required"}), 400
    basic = float(d["basic_salary"]); ded = float(d.get("deductions",0)); bon = float(d.get("bonus",0))
    net = basic - ded + bon
    conn, db = get_db(); c = conn.cursor(); p = ph(db)
    try:
        c.execute(f"INSERT INTO payroll (emp_id,pay_month,basic_salary,deductions,bonus,net_salary,status) VALUES ({p},{p},{p},{p},{p},{p},{p})",
                  (d["emp_id"],d["pay_month"],basic,ded,bon,net,d.get("status","Pending")))
        conn.commit(); new_id = c.lastrowid; conn.close()
        log_action("ADD_PAYROLL","payroll",new_id,_username())
        return jsonify({"message": "Payroll record added","payroll_id": new_id, "net_salary": net}), 201
    except Exception as e:
        conn.close(); return jsonify({"error": str(e)}), 500

@app.route("/api/payroll/<int:pid>", methods=["PUT"])
@require_auth
def edit_payroll(pid):
    d = request.json
    basic = float(d.get("basic_salary",0)); ded = float(d.get("deductions",0)); bon = float(d.get("bonus",0))
    net = basic - ded + bon
    conn, db = get_db(); c = conn.cursor(); p = ph(db)
    try:
        c.execute(f"UPDATE payroll SET basic_salary={p},deductions={p},bonus={p},net_salary={p},status={p} WHERE payroll_id={p}",
                  (basic,ded,bon,net,d.get("status","Pending"),pid))
        conn.commit(); conn.close()
        log_action("EDIT_PAYROLL","payroll",pid,_username())
        return jsonify({"message": "Payroll updated","net_salary": net})
    except Exception as e:
        conn.close(); return jsonify({"error": str(e)}), 500

@app.route("/api/payroll/<int:pid>/pay", methods=["PUT"])
@require_auth
def mark_paid(pid):
    conn, db = get_db(); c = conn.cursor(); p = ph(db)
    c.execute(f"UPDATE payroll SET status='Paid' WHERE payroll_id={p}", (pid,))
    conn.commit(); conn.close()
    log_action("PAY_SALARY","payroll",pid,_username())
    return jsonify({"message": "Marked as paid"})

@app.route("/api/payroll/<int:pid>", methods=["DELETE"])
@require_auth
def delete_payroll(pid):
    conn, db = get_db(); c = conn.cursor(); p = ph(db)
    try:
        c.execute(f"DELETE FROM payroll WHERE payroll_id={p}", (pid,))
        conn.commit(); conn.close()
        return jsonify({"message": "Payroll record deleted"})
    except Exception as e:
        conn.close(); return jsonify({"error": str(e)}), 500

@app.route("/api/payroll/generate", methods=["POST"])
@require_auth
def generate_payroll():
    d = request.json or {}
    month = d.get("month", date.today().strftime("%Y-%m"))
    conn, db = get_db(); c = conn.cursor(); p = ph(db)
    c.execute(f"SELECT emp_id,salary FROM employees WHERE status={p}", ("Active",))
    employees = fetchall_as_dict(c, db)
    count = 0
    for emp in employees:
        ded = round(float(emp["salary"]) * 0.1, 2)
        net = float(emp["salary"]) - ded
        try:
            if db == "mysql":
                c.execute(f"INSERT INTO payroll (emp_id,pay_month,basic_salary,deductions,bonus,net_salary,status) VALUES ({p},{p},{p},{p},0,{p},'Pending') ON DUPLICATE KEY UPDATE basic_salary=VALUES(basic_salary)",
                          (emp["emp_id"], month, emp["salary"], ded, net))
            else:
                c.execute(f"INSERT OR IGNORE INTO payroll (emp_id,pay_month,basic_salary,deductions,bonus,net_salary,status) VALUES ({p},{p},{p},{p},0,{p},'Pending')",
                          (emp["emp_id"], month, emp["salary"], ded, net))
            count += 1
        except Exception:
            pass
    conn.commit(); conn.close()
    return jsonify({"message": f"Generated payroll for {count} employees", "month": month}), 201

# ════════════════════════════════════════════════════════════════════
# PROJECTS — Full CRUD
# ════════════════════════════════════════════════════════════════════
@app.route("/api/projects", methods=["GET"])
@require_auth
def list_projects():
    conn, db = get_db(); c = conn.cursor(); j = _join(db)
    c.execute(f"SELECT p.project_id,p.name,p.description,p.start_date,p.end_date,p.status,p.budget,d.dept_name,p.dept_id FROM projects p {j} departments d ON p.dept_id=d.dept_id ORDER BY p.project_id DESC")
    projects = fetchall_as_dict(c, db)
    for proj in projects:
        c.execute(f"SELECT pa.role, e.name AS emp_name FROM project_assignments pa {j} employees e ON pa.emp_id=e.emp_id WHERE pa.project_id=%s" if db=="mysql" else f"SELECT pa.role, e.name AS emp_name FROM project_assignments pa {j} employees e ON pa.emp_id=e.emp_id WHERE pa.project_id=?", (proj["project_id"],))
        proj["members"] = fetchall_as_dict(c, db)
    conn.close()
    return jsonify(projects)

@app.route("/api/projects/<int:pid>", methods=["GET"])
@require_auth
def get_project(pid):
    conn, db = get_db(); c = conn.cursor(); p = ph(db); j = _join(db)
    c.execute(f"SELECT p.*,d.dept_name FROM projects p {j} departments d ON p.dept_id=d.dept_id WHERE p.project_id={p}", (pid,))
    proj = fetchone_as_dict(c, db)
    if not proj:
        conn.close(); return jsonify({"error": "Not found"}), 404
    c.execute(f"SELECT pa.assign_id,pa.role,e.name AS emp_name,e.emp_id FROM project_assignments pa {j} employees e ON pa.emp_id=e.emp_id WHERE pa.project_id={p}", (pid,))
    proj["members"] = fetchall_as_dict(c, db)
    conn.close()
    return jsonify(proj)

@app.route("/api/projects", methods=["POST"])
@require_auth
def add_project():
    d = request.json
    if not d.get("name"): return jsonify({"error": "'name' is required"}), 400
    conn, db = get_db(); c = conn.cursor(); p = ph(db)
    try:
        c.execute(f"INSERT INTO projects (name,description,start_date,end_date,status,budget,dept_id) VALUES ({p},{p},{p},{p},{p},{p},{p})",
                  (d["name"],d.get("description",""),d.get("start_date"),d.get("end_date"),d.get("status","Planning"),float(d.get("budget",0)),d.get("dept_id")))
        conn.commit(); new_id = c.lastrowid; conn.close()
        log_action("ADD_PROJECT","projects",new_id,_username())
        return jsonify({"message": "Project created","project_id": new_id}), 201
    except Exception as e:
        conn.close(); return jsonify({"error": str(e)}), 500

@app.route("/api/projects/<int:pid>", methods=["PUT"])
@require_auth
def edit_project(pid):
    d = request.json; conn, db = get_db(); c = conn.cursor(); p = ph(db)
    try:
        c.execute(f"UPDATE projects SET name={p},description={p},start_date={p},end_date={p},status={p},budget={p},dept_id={p} WHERE project_id={p}",
                  (d.get("name"),d.get("description",""),d.get("start_date"),d.get("end_date"),d.get("status","Planning"),float(d.get("budget",0)),d.get("dept_id"),pid))
        conn.commit(); conn.close()
        log_action("EDIT_PROJECT","projects",pid,_username())
        return jsonify({"message": "Project updated"})
    except Exception as e:
        conn.close(); return jsonify({"error": str(e)}), 500

@app.route("/api/projects/<int:pid>", methods=["DELETE"])
@require_auth
def delete_project(pid):
    conn, db = get_db(); c = conn.cursor(); p = ph(db)
    try:
        c.execute(f"DELETE FROM projects WHERE project_id={p}", (pid,))
        conn.commit(); conn.close()
        log_action("DELETE_PROJECT","projects",pid,_username())
        return jsonify({"message": "Project deleted"})
    except Exception as e:
        conn.close(); return jsonify({"error": str(e)}), 500

@app.route("/api/projects/<int:pid>/assign", methods=["POST"])
@require_auth
def assign_to_project(pid):
    d = request.json
    if not d.get("emp_id"): return jsonify({"error": "'emp_id' required"}), 400
    conn, db = get_db(); c = conn.cursor(); p = ph(db)
    try:
        c.execute(f"INSERT INTO project_assignments (project_id,emp_id,role) VALUES ({p},{p},{p})",
                  (pid,d["emp_id"],d.get("role","Member")))
        conn.commit(); conn.close()
        return jsonify({"message": "Employee assigned to project"}), 201
    except Exception as e:
        conn.close(); return jsonify({"error": str(e)}), 500

@app.route("/api/projects/<int:pid>/unassign/<int:eid>", methods=["DELETE"])
@require_auth
def unassign_from_project(pid, eid):
    conn, db = get_db(); c = conn.cursor(); p = ph(db)
    try:
        c.execute(f"DELETE FROM project_assignments WHERE project_id={p} AND emp_id={p}", (pid,eid))
        conn.commit(); conn.close()
        return jsonify({"message": "Employee removed from project"})
    except Exception as e:
        conn.close(); return jsonify({"error": str(e)}), 500

# ════════════════════════════════════════════════════════════════════
# AUDIT LOGS
# ════════════════════════════════════════════════════════════════════
@app.route("/api/audit-logs", methods=["GET"])
@require_auth
def list_audit_logs():
    conn, db = get_db(); c = conn.cursor()
    c.execute("SELECT * FROM audit_logs ORDER BY log_id DESC LIMIT 100")
    data = fetchall_as_dict(c, db); conn.close()
    return jsonify(data)

# ════════════════════════════════════════════════════════════════════
# RUN
# ════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("\n  +--------------------------------------------------+")
    print("  |   Employee Management System - Backend Server    |")
    print("  +--------------------------------------------------+")
    print("  |   URL:   http://localhost:5000                   |")
    print("  |   Admin: admin / admin123                        |")
    print("  |   HR:    hr / hr123                              |")
    print("  +--------------------------------------------------+\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
