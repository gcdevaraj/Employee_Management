# Employee Management System

A full-stack Employee Management System with **MySQL database**, **Python Flask backend**, and a **premium dark-theme frontend**.

## 🚀 Features

| Module | Description |
|---|---|
| **Dashboard** | Real-time stats cards + 3 interactive charts (department distribution, attendance, salary overview) |
| **Employees** | Full CRUD, search/filter, detailed profile with tabbed view (attendance, leaves, payroll, projects) |
| **Departments** | Card-based view with employee counts, manager info, and location |
| **Attendance** | Date-based tracking, mark attendance with check-in/check-out times |
| **Leave Management** | Submit requests, approve/reject workflow, multiple leave types |
| **Payroll** | Monthly salary processing, auto-generate payroll, mark as paid |
| **Projects** | Project cards with progress bars, team member avatars, budget tracking |

## 🛠️ Tech Stack

- **Frontend**: HTML5, CSS3 (dark theme + glassmorphism), Vanilla JavaScript, Chart.js
- **Backend**: Python Flask, Flask-CORS, MySQL Connector
- **Database**: MySQL 8.0 (with SQLite auto-fallback)

## 📦 Setup

### 1. Create MySQL Database
```bash
mysql -u root -proot -e "CREATE DATABASE IF NOT EXISTS employee_db;"
mysql -u root -proot employee_db < database/schema.sql
```

### 2. Install Python Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 3. Start the Server
```bash
cd backend
python app.py
```

### 4. Open in Browser
```
http://localhost:5000
```

## 🔑 Default Login

| Username | Password | Role |
|---|---|---|
| `admin` | `admin123` | Admin |
| `hr` | `hr123` | HR |

## 📁 Project Structure

```
Employee_Management_System/
├── backend/
│   ├── app.py              # Flask REST API (30+ endpoints)
│   └── requirements.txt    # Python dependencies
├── database/
│   └── schema.sql          # MySQL schema + seed data
├── frontend/
│   ├── index.html          # Single-page application
│   ├── style.css           # Premium dark theme
│   └── app.js              # SPA logic + API integration
└── README.md
```

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/login` | Login |
| POST | `/api/logout` | Logout |
| GET | `/api/stats` | Dashboard statistics |
| GET/POST | `/api/employees` | List / Add employees |
| GET/PUT/DELETE | `/api/employees/:id` | Get / Update / Delete employee |
| GET | `/api/employees/:id/profile` | Full employee profile |
| GET/POST | `/api/departments` | List / Add departments |
| PUT/DELETE | `/api/departments/:id` | Update / Delete department |
| GET/POST | `/api/attendance` | List / Mark attendance |
| POST | `/api/attendance/bulk` | Bulk mark attendance |
| GET/POST | `/api/leave` | List / Submit leave |
| PUT | `/api/leave/:id/status` | Approve / Reject leave |
| GET/POST | `/api/payroll` | List / Add payroll |
| POST | `/api/payroll/generate` | Auto-generate payroll |
| PUT | `/api/payroll/:id/pay` | Mark as paid |
| GET/POST | `/api/projects` | List / Create projects |
| PUT/DELETE | `/api/projects/:id` | Update / Delete project |
