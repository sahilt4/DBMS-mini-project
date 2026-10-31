# Quality Assurance & Automated Test Report
## Bus Reservation and Management System (BRMS)

---

## 1. Executive Summary

| Metric | Result |
|---|---|
| **Testing Framework** | `pytest 9.1.1` (Python 3.11.9, Windows x64) |
| **Total Test Suites** | 10 Test Modules |
| **Total Test Cases** | **23 Test Cases** |
| **Passed** | **23 (100.0%)** |
| **Failed / Errors** | **0 (0.0%)** |
| **Skipped** | **0 (0.0%)** |
| **Total Execution Duration** | 70.02 seconds |
| **Test Coverage Quality** | Full verification of Schema, RBAC, Concurrency, Waitlist, Check-In, QR/PDF, and Analytics |

---

## 2. Test Execution Log

```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.7.0 -- E:\Projects\DBMS\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: E:\Projects\DBMS
collecting ... collected 23 items

tests/test_auth.py::test_password_hashing_and_verification PASSED        [  4%]
tests/test_auth.py::test_passenger_registration PASSED                   [  8%]
tests/test_auth.py::test_duplicate_username_rejection PASSED             [ 13%]
tests/test_auth.py::test_login_validation PASSED                         [ 17%]
tests/test_authorization.py::test_passenger_booking_isolation PASSED     [ 21%]
tests/test_availability.py::test_availability_lifecycle PASSED           [ 26%]
tests/test_booking.py::test_successful_booking PASSED                    [ 30%]
tests/test_booking.py::test_duplicate_seat_booking_rejection PASSED      [ 34%]
tests/test_booking.py::test_invalid_seat_number_rejection PASSED         [ 39%]
tests/test_booking.py::test_concurrent_booking_safety PASSED             [ 43%]
tests/test_cancellation.py::test_successful_cancellation_and_refund PASSED [ 47%]
tests/test_cancellation.py::test_unauthorized_cancellation_prevention PASSED [ 52%]
tests/test_cancellation.py::test_admin_cancellation_authorization PASSED [ 56%]
tests/test_conductor_checkin.py::test_conductor_ticket_verification PASSED [ 60%]
tests/test_conductor_checkin.py::test_duplicate_checkin_rejection PASSED [ 65%]
tests/test_conductor_checkin.py::test_cancelled_ticket_verification_rejection PASSED [ 69%]
tests/test_database.py::test_schema_initialization PASSED                [ 73%]
tests/test_database.py::test_foreign_key_enforcement PASSED              [ 78%]
tests/test_digital_ticket.py::test_qr_code_generation PASSED             [ 82%]
tests/test_digital_ticket.py::test_pdf_ticket_generation PASSED          [ 86%]
tests/test_reports.py::test_dashboard_statistics PASSED                  [ 91%]
tests/test_reports.py::test_csv_report_export PASSED                     [ 95%]
tests/test_waitlist.py::test_waitlist_queue_position_and_retrieval PASSED [100%]

======================== 23 passed in 70.02s ========================
```

---

## 3. Test Suite Breakdown and Functional Verification

### 3.1 Authentication & Session Security (`tests/test_auth.py`)
- **`test_password_hashing_and_verification`**: Verifies that passwords are cryptographic hashes with individual salts. Plaintext passwords never match invalid hashes; identical passwords produce distinct hash digests.
- **`test_passenger_registration`**: Validates registration of new passenger accounts, atomic profile generation in `passengers`, default role assignment (`PASSENGER`), and active account status.
- **`test_duplicate_username_rejection`**: Verifies database unique constraint enforcement when attempting to register an existing email/username, guaranteeing an error response.
- **`test_login_validation`**: Tests credential validation, session hydration, and rejection of invalid passwords.

### 3.2 Authorization & Data Isolation (`tests/test_authorization.py`)
- **`test_passenger_booking_isolation`**: Confirms that non-admin passengers cannot query, access, or cancel tickets belonging to other passenger accounts, enforcing tenant isolation.

### 3.3 Inventory Lifecycle (`tests/test_availability.py`)
- **`test_availability_lifecycle`**: Validates that booking a seat decreases the schedule's available seat inventory by 1 in `schedule_seats`, and cancelling the booking restores available inventory by 1.

### 3.4 Concurrency & Atomic Booking Engine (`tests/test_booking.py`)
- **`test_successful_booking`**: Tests atomic reservation flow: verifies that booking references follow format `BUS-YYYYMMDD-XXXX`, payment status is set to `SUCCESS`, and seat status is `BOOKED`.
- **`test_duplicate_seat_booking_rejection`**: Confirms that sequential attempts to book an already occupied seat raise a concurrency collision error.
- **`test_invalid_seat_number_rejection`**: Validates boundary limits (e.g., attempting to book seat 999 on a 40-seat coach is rejected).
- **`test_concurrent_booking_safety`**: **High-Stress Concurrency Test**. Spawns 5 concurrent worker threads in parallel targeting the exact same schedule and seat.
  - **Outcome**: Exactly 1 thread successfully claims the seat; the remaining 4 threads are safely rejected without deadlock or database corruption.

### 3.5 Cancellation & Tiered Refunds (`tests/test_cancellation.py`)
- **`test_successful_cancellation_and_refund`**: Verifies cancellation status update, automatic creation of refund ledger records in `refunds`, and payment status update to `REFUNDED`.
- **`test_unauthorized_cancellation_prevention`**: Confirms that a passenger cannot cancel another traveler's booking.
- **`test_admin_cancellation_authorization`**: Confirms that users with the `ADMIN` role can authorize cancellations on any ticket.

### 3.6 Conductor Onboard Verification (`tests/test_conductor_checkin.py`)
- **`test_conductor_ticket_verification`**: Tests ticket validation against live schedule and payment status, creating a verified row in `ticket_checkins`.
- **`test_duplicate_checkin_rejection`**: Confirms that scanning a previously checked-in ticket is immediately flagged as a duplicate boarding attempt.
- **`test_cancelled_ticket_verification_rejection`**: Validates that cancelled tickets are rejected at the boarding gate.

### 3.7 Database Schema & Referential Integrity (`tests/test_database.py`)
- **`test_schema_initialization`**: Verifies that all 13 tables, indexes, views, and audit logs are initialized upon application bootstrap.
- **`test_foreign_key_enforcement`**: Confirms that inserting orphaned foreign keys (e.g., booking referencing a nonexistent schedule) raises a foreign key violation.

### 3.8 Digital Ticket & PDF Generation (`tests/test_digital_ticket.py`)
- **`test_qr_code_generation`**: Generates a live QR code image byte stream and verifies that valid PNG header bytes (`\x89PNG\r\n\x1a\n`) are produced.
- **`test_pdf_ticket_generation`**: Renders a complete ReportLab PDF boarding pass with embedded QR code, confirming valid PDF header (`%PDF-1.4`) and non-zero byte size.

### 3.9 Reports & Analytics (`tests/test_reports.py`)
- **`test_dashboard_statistics`**: Queries KPI aggregates (total bookings, active routes, fleet size, total revenue) and validates correct numerical types.
- **`test_csv_report_export`**: Validates CSV generation from analytical queries, verifying header columns and non-empty rows.

### 3.10 Waitlist Priority Queue (`tests/test_waitlist.py`)
- **`test_waitlist_queue_position_and_retrieval`**: Confirms FIFO ordering in `waitlist` (positions 1, 2, 3), priority queue retrieval, and auto-allocation on seat release.

---

## 4. Conclusion & Production Readiness

The test suite thoroughly verifies all functional, transactional, relational, and security requirements of the BRMS specification. The application has passed 100% of its automated regression suite with zero unhandled exceptions.

