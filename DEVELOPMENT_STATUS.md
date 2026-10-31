# DEVELOPMENT STATUS — BUS RESERVATION & MANAGEMENT SYSTEM (BRMS)

Last Updated: 2026-10-31

---

## 1. Executive Summary & Project Health

This document tracks the incremental design, migration, implementation, verification, and hardening of the **Bus Reservation and Management System (BRMS)** desktop application. 

The application is transitioning from an initial 7-table prototype to a full enterprise-grade 13-table (+ Audit Log) relational DBMS architecture powered by **MySQL 8.x (InnoDB)** with full stored procedures, views, triggers, foreign keys, RBAC (Admin, Passenger, Conductor), transaction-safe seat concurrency, QR verification, ReportLab PDF ticketing, and automated unit/integration testing.

---

## 2. Phase-by-Phase Roadmap & Tracking

| Phase | Description | Status | Verification & Deliverables |
|---|---|---|---|
| **Phase 0** | Repository Audit, Environment & Dependency Analysis | **COMPLETED** | Audited repository, identified missing tables, added dependencies |
| **Phase 1** | Database Foundation & MySQL 8.x SQL Suite | **IN_PROGRESS** | `database/01-07.sql`, schema, constraints, views, procedures, triggers |
| **Phase 2** | Core Infrastructure, Database Abstraction & RBAC Auth | **PENDING** | Connection pool, unified adapter, bcrypt auth, session manager |
| **Phase 3** | Fleet, Route, Intermediate Stop & Schedule Management | **PENDING** | Buses, Routes, Bus Stops, Route Stops, Schedule Seat Generator |
| **Phase 4** | Transaction-Safe Seat Reservation & Concurrency Engine | **PENDING** | `schedule_seats` inventory, atomic bookings, isolation levels |
| **Phase 5** | Waiting List, Cancellation, Refunds & Verification | **PENDING** | Priority queue waitlist, automated refund engine, ReportLab PDF, QR generator |
| **Phase 6** | Reporting, Analytics & Visualization | **PENDING** | Occupancy & revenue analytics, Matplotlib charts, CSV/PDF export |
| **Phase 7** | Conductor Operational Workflows | **PENDING** | Trip manifests, OpenCV QR code scanner, check-in recording |
| **Phase 8** | Automated Testing Suite & Concurrency QA | **PENDING** | Pytest test suite covering auth, concurrency, waitlist, refunds |
| **Phase 9** | Documentation & Academic Package | **PENDING** | ER Diagram, Database Design, Normalization, Architecture, Test Report |

---

## 3. Phase 0 Audit Findings

### 3.1 Repository Structure
- **Current Core Modules:**
  - `app/config.py`: Application paths, credentials, and configuration defaults.
  - `app/database.py`: Initial SQLite database helper and PBKDF2 hashing.
  - `app/repositories/`: `booking_repository.py`, `bus_repository.py`, `passenger_repository.py`, `report_repository.py`, `route_repository.py`, `schedule_repository.py`, `user_repository.py`.
  - `app/services/`: `auth_service.py`, `booking_service.py`, `cancellation_service.py`, `report_service.py`, `schedule_service.py`.
  - `app/ui/pages/`: `dashboard_page.py`, `bus_search_page.py`, `bus_management_page.py`, `route_management_page.py`, `schedule_management_page.py`, `my_bookings_page.py`, `reports_page.py`.
  - `app/ui/dialogs/`: `seat_selection_dialog.py`, `booking_confirmation_dialog.py`, `ticket_dialog.py`, `login_dialog.py`, `registration_dialog.py`, `bus_dialog.py`, `route_dialog.py`, `schedule_dialog.py`.
  - `tests/`: 8 test files for auth, availability, booking, cancellation, database, reports.

### 3.2 Database Schema Gap Analysis
- **Current Tables (7):** `users`, `passengers`, `routes`, `buses`, `schedules`, `bookings`, `payments`.
- **Target Tables (13 + 1):**
  1. `USERS`: Add `phone`, `account_status`, bcrypt hashing.
  2. `PASSENGERS`: Relate cleanly to user accounts, profile details.
  3. `ROUTES`: Add route status, estimated duration.
  4. `BUSES`: Registration number, name, type, capacity, operational status.
  5. `SCHEDULES`: Bus, route, departure/arrival timestamps, base fare, status.
  6. `BOOKINGS`: Unique reference, passenger, schedule, seat, amount, status.
  7. `PAYMENTS`: Method, transaction reference, status, simulated ledger.
  8. `SCHEDULE_SEATS` (**NEW**): Authoritative per-schedule seat inventory and status.
  9. `WAITLIST` (**NEW**): Queue position, status, auto-allocation trigger/logic.
  10. `BUS_STOPS` (**NEW**): Physical stop locations and cities.
  11. `ROUTE_STOPS` (**NEW**): Ordered sequence of stops, distance, duration offsets.
  12. `REFUNDS` (**NEW**): Automated cancellation refund calculation records.
  13. `TICKET_CHECKINS` (**NEW**): Conductor verification timestamps, boarding stop.
  14. `AUDIT_LOGS` (**NEW**): System-wide change tracking and compliance.

### 3.3 Dependencies
- Existing: `PySide6`, `matplotlib`, `pytest`.
- Required Installations: `mysql-connector-python`, `qrcode[pil]`, `reportlab`, `opencv-python`, `bcrypt`.
- In-progress installation via `.venv/Scripts/pip.exe`.

### 3.4 Database Connectivity Architecture
- Target engine: **MySQL 8.x (InnoDB)**.
- Full suite of standard SQL scripts in `database/`:
  - `01_create_database.sql`
  - `02_create_tables.sql`
  - `03_constraints_indexes.sql`
  - `04_views.sql`
  - `05_stored_procedures.sql`
  - `06_triggers.sql`
  - `07_sample_data.sql`
- Unified Database Driver in `app/database.py`:
  - Supports MySQL 8.x with connection pooling, transaction isolation, and stored procedure invocation.
  - Provides seamless SQLite compatibility fallback mode for local testing without requiring a live MySQL daemon running during rapid automated test execution.

