# Smart Bus Reservation System - Project Report
## DBMS Mini Project Report

---

### 1. Title and Problem Statement
**Title**: Smart Bus Reservation System  
**Domain**: Database Management Systems (DBMS), Desktop Application Engineering  
**Technology Stack**: Python 3.11, PySide6 (Qt for Python), SQLite 3, Matplotlib, Pytest  

**Problem Statement**:
Inter-city bus travel in India requires accurate scheduling, real-time seat inventory management, and reliable booking records. Manual reservation systems and naive database architectures suffer from:
1. Double-booking errors caused by race conditions during simultaneous reservation attempts.
2. Loss of historical financial and audit data when cancelled bookings are physically deleted to free up seats.
3. Update anomalies where cached availability counters drift away from actual ticket records.
4. Vulnerability to SQL injection and unvalidated input.

---

### 2. Objectives
1. Implement a normalized relational schema in SQLite that enforces data integrity using Primary/Foreign Keys, CHECK constraints, and Partial Unique Indexes.
2. Develop a native desktop GUI using PySide6 featuring a modern Windows sidebar layout, dynamic role-based access, and an interactive visual seat selection dialog with aisle representation.
3. Implement an ACID transaction workflow using `BEGIN IMMEDIATE` to prevent race conditions and duplicate seat reservations.
4. Provide administrative features for fleet management, route configuration, journey scheduling with conflict prevention, dashboard analytics with embedded Matplotlib trend charts, and CSV report export.
5. Create comprehensive automated unit and integration tests using pytest covering constraints, authentication, concurrency, and transactions.

---

### 3. Methodology & Architecture
The system employs a 4-tier layered architecture:
- **Presentation Layer (`app/ui/`)**: Built using PySide6 widgets, modern Windows QSS stylesheets, interactive table views, and modal dialogs.
- **Service Layer (`app/services/`)**: Enforces business logic, session management, input validation, and explicit SQLite transaction lifecycles (`BEGIN IMMEDIATE`, `COMMIT`, `ROLLBACK`).
- **Data Access Layer (`app/repositories/`)**: Encapsulates parameterized SQL queries and database operations for each entity.
- **Database Layer (`app/schema.sql`, `app/database.py`)**: SQLite 3 database operating with WAL mode and `PRAGMA foreign_keys = ON;`.

---

### 4. Database Design & Schema
The relational database consists of 7 normalized tables:
- `users`: Authentication and roles (`admin`, `passenger`).
- `routes`: City origins, destinations, distances in km with `CHECK(source <> destination)`.
- `buses`: Physical fleet inventory with capacity limits (`CHECK(total_seats BETWEEN 1 AND 60)`).
- `schedules`: Date and departure/arrival timestamps mapping buses to routes.
- `passengers`: Traveler demographics linked to bookings.
- `bookings`: Seat reservations with unique reference code (`BUS-YYYYMMDD-XXXXXXXX`).
- `payments`: Simulated transaction records.

**Key Database Innovation - Partial Unique Index**:
```sql
CREATE UNIQUE INDEX idx_bookings_active_seat
ON bookings (schedule_id, seat_number)
WHERE status = 'CONFIRMED';
```
This guarantees that while a seat can never have more than one confirmed booking simultaneously, a cancelled booking releases its seat immediately without deleting historical booking records.

---

### 5. Implementation Highlights
- **Visual Seat Selector**: Dynamically generates a realistic 2x2 coach layout with an aisle from `buses.total_seats`, marking occupied seats as disabled and allowing single-click seat allocation.
- **Live Seat Availability Calculation**: Avoids stored counters. Availability is always calculated dynamically as:
  $$\text{Available} = \text{total\_seats} - \text{COUNT(CONFIRMED bookings)}$$
- **Admin Dashboard & Analytics**: Features real-time KPI cards and an embedded Matplotlib trend chart showing daily revenues and booking volume.
- **Export to CSV**: Utilizes Python's standard `csv` module to export reports directly to spreadsheets.

---

### 6. Testing & Quality Assurance
The application includes 17 automated pytest test cases covering:
1. Database schema initialization & table creation.
2. Foreign key enforcement & constraint violations.
3. Passenger account registration & profile generation.
4. PBKDF2-HMAC password hashing and verification.
5. Login authentication & bad credential rejection.
6. Successful booking transaction execution.
7. Immediate duplicate seat-booking rejection.
8. Invalid seat number range validation.
9. Concurrent multi-threaded booking safety.
10. Seat availability reduction after booking.
11. Seat availability restoration after cancellation.
12. Successful cancellation & simulated refund.
13. Prevention of unauthorized cancellation.
14. Passenger booking data isolation.
15. Dashboard aggregate metrics calculation.
16. CSV report export and content verification.

**Test Results**: `17 passed in 5.70s` (100% pass rate).

---

### 7. Conclusion
The Smart Bus Reservation System demonstrates how relational database principles, transactions, and desktop user interfaces integrate into a complete, professional business application. It satisfies all college DBMS curriculum requirements and provides an outstanding demonstration platform for DBMS viva examinations.
