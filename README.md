# Smart Bus Reservation System
### Python Desktop Application | College DBMS Mini Project

A complete, functional, and polished **Smart Bus Reservation System** built with **PySide6 (Qt for Python)**, **SQLite 3**, and **Matplotlib**. Developed as a comprehensive college DBMS mini project demonstrating relational database concepts, ACID transactions, foreign keys, normalization, dynamic seat availability, and modern desktop UI design.

---

## 1. Features Overview

### A. Role-Based Access Control
- **Administrator**:
  - Real-time dashboard with 6 KPI metrics, recent bookings, high-occupancy journeys, and an integrated Matplotlib sales trend chart.
  - Bus fleet management (add, edit, search, filter by coach type, and soft-deactivation).
  - Route management (add, edit, search, and validate origin-destination pairs).
  - Schedule management (assign buses to routes, set timings and fares, prevent overlapping journeys, and cancel trips).
  - Master booking audit (view all customer reservations across the network).
  - Comprehensive analytical reports with one-click **CSV Export**.
- **Passenger**:
  - Account registration and login with secure PBKDF2-HMAC password hashing.
  - Search available journeys by source city, destination city, and travel date.
  - **Interactive Visual Seat Selector**: Realistic coach layout with driver cabin, 2x2 seats, aisle, and real-time color and text availability states (`[FREE]`, `[SEL]`, `[OCC]`).
  - Booking confirmation dialog with passenger detail confirmation and simulated payment methods (UPI, Card, Net Banking, Cash).
  - Digital Boarding Pass / E-Ticket view with barcode simulation and printable text export.
  - "My Bookings" page with search, ticket review, and self-service cancellation with simulated refund.

### B. Core DBMS Demonstrations
- **Relational Integrity**: 7 normalized tables enforcing primary keys, foreign keys (`PRAGMA foreign_keys = ON;`), CHECK constraints, and NOT NULL fields.
- **Partial Unique Index**:
  ```sql
  CREATE UNIQUE INDEX idx_bookings_active_seat
  ON bookings (schedule_id, seat_number)
  WHERE status = 'CONFIRMED';
  ```
  Guarantees duplicate-booking prevention while enabling cancelled bookings to release their seats without deleting historical records.
- **ACID Write Transactions**: Executes reservations using `BEGIN IMMEDIATE` to guarantee concurrency safety and prevent double-booking race conditions.
- **Dynamic Availability Calculation**: Computes available seats dynamically from total capacity minus confirmed bookings, eliminating counter update anomalies.
- **Data Protection**: Prepared statements (`?` parameters) across all repositories to prevent SQL injection.

---

## 2. Technology Stack

- **Programming Language**: Python 3.11+
- **Desktop GUI**: PySide6 6.12 (Qt for Python)
- **Database**: SQLite 3 (embedded, standard library)
- **Visual Analytics**: Matplotlib 3.11 (embedded via `FigureCanvasQTAgg`)
- **Testing**: Pytest 9.1
- **Security**: PBKDF2-HMAC with SHA-256 and random 16-byte salt
- **File Export**: Python standard library `csv` module

---

## 3. Demo Credentials

Convenient one-click demo login buttons are provided directly on the Login screen for smooth viva evaluation:

| Role | Name | Username | Password | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Administrator** | System Administrator | `admin` | `Admin@123` | Full administrative control |
| **Passenger 1** | Rahul Sharma | `rahul_sharma` | `Rahul@123` | Pre-seeded with confirmed bookings |
| **Passenger 2** | Priya Patil | `priya_patil` | `Priya@123` | Pre-seeded with historical bookings |
| **Passenger 3** | Amit Deshmukh | `amit_d` | `Amit@123` | Pre-seeded with cancelled booking |

---

## 4. Installation & Windows Setup

### Prerequisites
- Windows 10/11
- Python 3.11 installed (added to PATH or using py launcher)

### Step-by-Step Setup Commands

Open PowerShell or Command Prompt in the project folder:

```powershell
# 1. Navigate to the project directory
cd E:\Projects\DBMS

# 2. Create Python virtual environment
python -m venv .venv

# 3. Activate the virtual environment
.venv\Scripts\activate

# 4. Upgrade pip
python -m pip install --upgrade pip

# 5. Install application dependencies
pip install -r requirements.txt
```

---

## 5. Running the Application

Launch the desktop application with a single command:

```powershell
python main.py
```

*Note: On first startup, the application automatically initializes the SQLite schema and seeds realistic Maharashtra routes, buses, schedules, and demo users.*

### Database Location & Reset
The application database is stored safely in your writable application-data directory:
- **Windows**: `%LOCALAPPDATA%\SmartBusReservation\smart_bus.sqlite3`

To reset the demonstration database back to clean seed data at any time:
```powershell
python -m app.seed
```

---

## 6. Running Automated Tests

A comprehensive suite of 17 automated tests validates the database schema, constraints, authentication, transactions, seat availability lifecycle, concurrency safety, and CSV reporting:

```powershell
pytest -v
```

**Expected output:**
```text
============================= 17 passed in 5.70s ==============================
```

---

## 7. Project Structure

```text
DBMS/
│
├── main.py                     # Application startup entry point
├── requirements.txt            # Python dependencies (PySide6, matplotlib, pytest)
├── README.md                   # Complete documentation & setup instructions
├── DBMS_CONCEPTS.md            # Detailed viva guide with 15+ SQL queries
├── ER_DIAGRAM.md               # Mermaid ER diagram & schema relationship doc
├── PROJECT_REPORT.md           # Formal college mini project report
├── .gitignore                  # Git ignore rules for Python & SQLite
│
├── app/                        # Application source code package
│   ├── __init__.py
│   ├── config.py               # Constants, app data paths, demo accounts
│   ├── database.py             # SQLite connection factory & PBKDF2 hasher
│   ├── schema.sql              # 7 normalized relational tables & partial indexes
│   ├── seed.py                 # Idempotent demo dataset seeder
│   │
│   ├── repositories/           # Data Access Layer (SQL queries)
│   │   ├── user_repository.py
│   │   ├── bus_repository.py
│   │   ├── route_repository.py
│   │   ├── schedule_repository.py
│   │   ├── passenger_repository.py
│   │   ├── booking_repository.py
│   │   └── report_repository.py
│   │
│   ├── services/               # Business Logic & Transaction Layer
│   │   ├── auth_service.py
│   │   ├── booking_service.py      # ACID reservation workflow (BEGIN IMMEDIATE)
│   │   ├── cancellation_service.py # Atomic cancellation & refund
│   │   ├── schedule_service.py     # Bus interval overlap checks
│   │   └── report_service.py       # CSV report generation
│   │
│   └── ui/                     # Presentation Layer (PySide6)
│       ├── styles.py           # Modern Windows QSS stylesheet
│       ├── main_window.py      # Master layout with role-based sidebar
│       │
│       ├── dialogs/            # Modal Dialogs
│       │   ├── login_dialog.py
│       │   ├── registration_dialog.py
│       │   ├── seat_selection_dialog.py     # Visual interactive coach layout
│       │   ├── booking_confirmation_dialog.py
│       │   ├── ticket_dialog.py             # Boarding pass & text receipt export
│       │   ├── bus_dialog.py
│       │   ├── route_dialog.py
│       │   └── schedule_dialog.py
│       │
│       └── pages/              # Application Pages
│           ├── dashboard_page.py            # Admin KPI cards & Matplotlib trend
│           ├── bus_search_page.py           # Passenger journey search
│           ├── bus_management_page.py       # Bus fleet management
│           ├── route_management_page.py     # Route management
│           ├── schedule_management_page.py  # Journey schedules
│           ├── my_bookings_page.py          # Passenger history & cancellation
│           └── reports_page.py              # Reports table & CSV export
│
└── tests/                      # Automated Pytest Suite
    ├── conftest.py             # Isolated temporary database fixtures
    ├── test_database.py        # Schema & foreign key tests
    ├── test_auth.py            # PBKDF2 hashing & registration tests
    ├── test_booking.py         # Transaction & duplicate-booking tests
    ├── test_availability.py    # Dynamic availability & seat release tests
    ├── test_cancellation.py    # Cancellation & refund tests
    ├── test_authorization.py   # Passenger data isolation tests
    └── test_reports.py         # Dashboard analytics & CSV export tests
```

---

## 8. Packaging as a Standalone Executable (PyInstaller)

To bundle the application into a standalone Windows `.exe`:

```powershell
# 1. Install PyInstaller in the virtual environment
pip install pyinstaller

# 2. Build standalone executable
pyinstaller --name "SmartBusReservation" --windowed --add-data "app\schema.sql;app" main.py
```

The resulting executable will be located in the `dist\SmartBusReservation\` directory.

---

## 9. Troubleshooting

- **Error: "Python is not recognized"**: Ensure Python is added to your Windows PATH, or run via `py main.py`.
- **Database lock or permission error**: The database is stored in `%LOCALAPPDATA%\SmartBusReservation\`. Check that the user has standard folder write permissions.
- **Resetting data**: Run `python -m app.seed` to restore sample demonstration routes and users.
