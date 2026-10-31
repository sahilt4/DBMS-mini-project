# Bus Reservation and Management System (BRMS)
### Advanced Python Desktop Application | Relational DBMS Mini Project

A complete, enterprise-grade **Bus Reservation and Management System (BRMS)** built with **PySide6 (Qt for Python)**, **MySQL 8.x (InnoDB)** (with unified SQLite fallback portability), **OpenCV**, and **ReportLab**. 

Developed as an advanced academic DBMS project demonstrating normalized 13-table relational architecture, ACID transactions, row-level concurrency locking, waitlist queue management, QR-based digital ticketing, live camera conductor boarding verification, and role-based access control (RBAC).

---

## 1. Key Features Overview

### A. Three Operational Roles (RBAC)
- **Administrator**:
  - Executive dashboard with 6 KPI cards, load factors, recent bookings, and an embedded Matplotlib sales trend chart.
  - Fleet management (CRUD operations, registration validation, capacity constraints, and operational status).
  - Route & Intermediate Stops management (city pairs, sequential waypoints, distance, and duration offsets).
  - Schedule management (journey timetable creation, bus assignment, time conflict prevention, and trip cancellations).
  - Network-wide booking audit ledger and security audit log explorer.
  - Comprehensive analytical reports with one-click **CSV Export**.
- **Passenger**:
  - Account registration and login with salted cryptographic password hashing (bcrypt / PBKDF2).
  - Multi-criteria bus search (origin, destination, travel date, coach class).
  - **Interactive 2x2 Visual Seat Selector**: Realistic coach seating layout with driver cabin, aisle, color-coded availability (`[FREE]`, `[SEL]`, `[OCC]`), and responsive sizing.
  - Booking checkout with payment method selection (UPI, Credit Card, Debit Card, Net Banking, Cash).
  - **Digital Boarding Pass / E-Ticket Modal**: High-contrast QR code rendering and one-click **ReportLab PDF Boarding Pass** download.
  - Self-service booking management with cancellation and tiered refund computation (100%, 75%, 50%).
- **Conductor**:
  - Trip selector and real-time passenger manifest table.
  - **Live Camera QR Code Scanner**: Onboard verification using OpenCV (`cv2.VideoCapture` + `cv2.QRCodeDetector`).
  - Manual reference code check-in fallback.
  - Duplicate check-in prevention and cancelled ticket boarding rejection.
  - Real-time check-in audit history.

---

## 2. Relational Database Architecture

The application implements a 13-table (+ Audit Log) relational schema in pure **3NF / BCNF**:

```
+---------------------------------------------------------------+
|                       13 CORE RELATIONS                       |
+---------------------------------------------------------------+
| 1. USERS            | Master credentials & RBAC roles         |
| 2. PASSENGERS       | Passenger demographic profiles          |
| 3. BUSES            | Fleet inventory & seating capacity      |
| 4. ROUTES           | Travel corridors & distances            |
| 5. BUS_STOPS        | Physical terminals & boarding points    |
| 6. ROUTE_STOPS      | Sequential route waypoints              |
| 7. SCHEDULES        | Departure timetable & fares             |
| 8. SCHEDULE_SEATS   | Authoritative per-trip seat inventory   |
| 9. BOOKINGS         | Reservation ledger (unique reference)   |
| 10. PAYMENTS        | Payment transaction records             |
| 11. REFUNDS         | Cancellation penalty & refund ledger    |
| 12. WAITLIST        | FIFO priority queue for sold-out trips  |
| 13. TICKET_CHECKINS | Conductor verification log (QR/manual)  |
| 14. AUDIT_LOGS      | System-wide change tracking log         |
+---------------------------------------------------------------+
```

### Relational Views:
1. `vw_available_buses`: Active fleet inventory and scheduled trip count.
2. `vw_available_seats`: Live seat availability count per trip.
3. `vw_booking_details`: Denormalized view joining traveler, schedule, vehicle, route, and payment records.
4. `vw_passenger_booking_history`: Passenger lifetime travel statistics and spend.
5. `vw_route_revenue`: Route load factors, gross revenue, refunds, and net profit.
6. `vw_schedule_occupancy`: Real-time coach load factor and seat occupancy percentage.

### Stored Procedures & Triggers:
- `sp_search_buses`: Query trips with real-time seat availability calculation.
- `sp_book_seat`: Atomic reservation procedure with row-level locking.
- `sp_cancel_booking`: Tiered refund computation and waitlist auto-allocation trigger.
- `sp_process_waitlist`: FIFO queue allocation for released seats.
- `sp_generate_revenue_report`: Aggregated financial metrics for a date range.
- `trg_after_schedule_insert`: Automatic seat inventory generation (1 to capacity) in `schedule_seats`.
- `trg_audit_*`: System mutation audit logging.

---

## 3. Technology Stack

- **Language**: Python 3.11+
- **Desktop GUI**: PySide6 (Qt for Python 6.12)
- **Relational Databases**: MySQL 8.x (InnoDB) / Portable SQLite 3 (WAL mode)
- **QR Generation & Verification**: `qrcode[pil]` 8.2 & OpenCV (`cv2`) 5.0
- **Document Generation**: ReportLab 5.1 (PDF Boarding Passes)
- **Visual Analytics**: Matplotlib 3.11 (`FigureCanvasQTAgg`)
- **Security**: Cryptographic hashing (bcrypt / PBKDF2-HMAC-SHA256)
- **Testing**: Pytest 9.1 (23 Automated Tests, 100% Pass Rate)

---

## 4. Default Credentials (RBAC)

The system includes pre-seeded accounts for instant evaluation:

| Role | Full Name | Username / Email | Password | Permissions & Notes |
|---|---|---|---|---|
| **ADMIN** | System Administrator | `admin` | `Admin@123` | Full system control, fleet, routes, schedules, reports |
| **CONDUCTOR** | Ramesh Shinde | `conductor` | `Conductor@123` | Trip manifests, live camera QR scanning, passenger boarding |
| **PASSENGER** | Rahul Sharma | `rahul_sharma` | `Rahul@123` | Pre-seeded with confirmed reservations |
| **PASSENGER** | Priya Patil | `priya_patil` | `Priya@123` | Pre-seeded with confirmed reservations |
| **PASSENGER** | Amit Deshmukh | `amit_d` | `Amit@123` | Pre-seeded with cancelled reservation |

---

## 5. Installation & Setup Guide

### Option A: Quickstart Mode (Instant Zero-Config SQLite)
The application includes an embedded dual-database adapter. If MySQL is not configured, it automatically launches with the fully featured portable database:

```powershell
# 1. Clone repository
git clone https://github.com/sahilt4/DBMS-mini-project.git
cd DBMS-mini-project

# 2. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the desktop application
python main.py
```

### Option B: Production Setup with MySQL 8.x
To connect the application to a local or remote MySQL 8.x server:

1. Open MySQL Workbench or the MySQL Command Line Client:
   ```powershell
   mysql -u root -p
   ```
2. Execute the migration scripts in sequential order from the `database/` folder:
   ```sql
   SOURCE database/01_create_database.sql;
   SOURCE database/02_create_tables.sql;
   SOURCE database/03_constraints_indexes.sql;
   SOURCE database/04_views.sql;
   SOURCE database/05_stored_procedures.sql;
   SOURCE database/06_triggers.sql;
   SOURCE database/07_sample_data.sql;
   ```
3. Configure your MySQL credentials in `app/config.py` (or set environment variables `BRMS_DB_USER`, `BRMS_DB_PASSWORD`, `BRMS_DB_HOST`, `BRMS_DB_PORT`).
4. Launch the application:
   ```powershell
   python main.py
   ```

---

## 6. Running the Automated Test Suite

Run all 23 unit, integration, and concurrency tests:

```powershell
# Run the complete test suite
pytest -v

# Run concurrency tests only
pytest -v tests/test_booking.py -k "concurrent"

# Run conductor QR and ticket verification tests
pytest -v tests/test_conductor_checkin.py tests/test_digital_ticket.py
```

**Test Verification Summary:**
```
======================== 23 passed in 70.02s ========================
```

---

## 7. Step-by-Step Viva Demonstration Script

1. **Launch & Admin Overview**:
   - Run `python main.py`.
   - Log in with `admin` / `Admin@123`.
   - Review the Dashboard KPI cards (Total Revenue, Active Routes, Fleet Size) and Matplotlib sales trend chart.
   - Navigate to **Reports**: demonstrate relational views (`vw_route_revenue`, `vw_schedule_occupancy`), security audit logs, and click **Export CSV**.
2. **Passenger Search & Interactive Seat Booking**:
   - Log out or switch to passenger account `rahul_sharma` / `Rahul@123`.
   - In **Search Buses**, choose `Pune` -> `Mumbai`.
   - Click **Book Seats** to launch the interactive 2x2 coach seat selector.
   - Select an available seat (`[FREE]` turns to blue `[SEL]`) and click **Proceed to Booking**.
   - Review the passenger details, choose a payment method, and confirm the booking.
   - Inspect the **Digital E-Ticket** modal: note the live QR code and click **Download PDF Boarding Pass** to generate the official ReportLab ticket.
3. **Conductor Verification & Live QR Scan**:
   - Log out and log in as conductor `conductor` / `Conductor@123`.
   - Navigate to the **Conductor Verification** portal.
   - Select the journey schedule from the dropdown to inspect the real-time passenger manifest.
   - Paste the booking reference (or scan via webcam) and click **Verify & Check-In Ticket**.
   - Note the instant verification success banner and updated boarding log.
   - Attempt to verify the same ticket again: demonstrate the **Duplicate Check-In Rejection** safety mechanism.
4. **Concurrency Safety & Waitlist Demonstration**:
   - Run `pytest -v tests/test_booking.py::test_concurrent_booking_safety` to show 5 simultaneous threads competing for one seat, proving that exactly 1 succeeds and 4 fail gracefully.

---

## 8. Academic Documentation Suite

- [`ER_DIAGRAM.md`](file:///E:/Projects/DBMS/ER_DIAGRAM.md): 13-table Entity-Relationship diagram, attributes, and cardinality matrix.
- [`DATABASE_DESIGN.md`](file:///E:/Projects/DBMS/DATABASE_DESIGN.md): Complete data dictionary, 6 views, 5 stored procedures, and triggers.
- [`NORMALIZATION.md`](file:///E:/Projects/DBMS/NORMALIZATION.md): Step-by-step 1NF, 2NF, 3NF, and BCNF normalization proofs with anomaly resolutions.
- [`ARCHITECTURE.md`](file:///E:/Projects/DBMS/ARCHITECTURE.md): 4-tier layered architecture, concurrency locking model, and RBAC matrix.
- [`TEST_REPORT.md`](file:///E:/Projects/DBMS/TEST_REPORT.md): Comprehensive test results and coverage logs (23/23 tests passing).
- [`DEVELOPMENT_STATUS.md`](file:///E:/Projects/DBMS/DEVELOPMENT_STATUS.md): Incremental development logs and phase completion tracking.
