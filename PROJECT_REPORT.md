# Bus Reservation and Management System (BRMS)
## Academic Project Report & Viva Reference Guide
### Advanced Database Management Systems (DBMS)

---

## 1. Title and Problem Statement

- **Project Title**: Bus Reservation and Management System (BRMS)
- **Domain**: Advanced Database Management Systems (DBMS), Systems Architecture & Desktop Application Engineering
- **Implementation Stack**: Python 3.11, PySide6 (Qt 6.12), MySQL 8.x (InnoDB) / Portable SQLite 3, Matplotlib, OpenCV, ReportLab, QRCode, Pytest.

### Problem Statement:
Inter-city passenger transport networks require robust scheduling, real-time seat inventory reservation, fraud-resistant ticketing, and accurate financial reporting. Naive software architectures suffer from:
1. **Double-Booking Race Conditions**: Concurrent users attempting to book the same seat simultaneously can corrupt inventory if queries lack transaction-level locking.
2. **Loss of Historical Data on Cancellation**: Systems that physically delete cancelled booking rows destroy financial ledgers, route history, and passenger audit trails.
3. **Update Anomalies**: Maintaining static `available_seats` counters leads to counter drift during unexpected failures or cancellations.
4. **Ticket Counterfeiting & Inefficient Boarding**: Paper tickets are prone to fraud, slow manual checking, and lack instant validation against real-time database state.

---

## 2. Objectives and Innovations

1. **Normalized Relational Schema**: Engineer a 13-table (+ Audit Log) relational schema in pure 3NF/BCNF enforcing referential integrity with foreign key constraints, check constraints, and partial unique indexes.
2. **Transaction-Safe Seat Inventory**: Implement per-schedule physical seat inventory (`schedule_seats`) using row-level locking (`SELECT ... FOR UPDATE` / `BEGIN IMMEDIATE`) to prevent double-booking.
3. **Role-Based Access Control (RBAC)**: Enforce distinct operational interfaces and permissions for **ADMIN**, **PASSENGER**, and **CONDUCTOR**.
4. **Automated Waitlist Queue**: Maintain a FIFO waitlist priority queue (`waitlist`) that automatically allocates released seats to waitlisted passengers upon trip cancellation.
5. **Digital Ticketing & QR Verification**: Generate cryptographically verifiable digital QR codes and downloadable ReportLab PDF boarding passes; provide live OpenCV camera scanning for onboard conductor verification.
6. **Relational Views & Stored Procedures**: Encapsulate complex analytics in 6 relational views (`vw_route_revenue`, `vw_schedule_occupancy`, etc.) and 5 stored procedures.
7. **Comprehensive Automated Testing**: Guarantee quality through 23 automated tests covering constraints, auth, concurrency, refunds, and ticket check-ins.

---

## 3. System Architecture & Component Design

The application follows a clean 4-tier modular layered architecture:

```
+-----------------------------------------------------------------+
|                   1. Presentation Layer (PySide6)               |
|  - Modern Windows Navigation Sidebar (RBAC View Switching)      |
|  - Bus Search & 2x2 Coach Seating Dialog with Aisle             |
|  - Fleet, Route, Schedule & Stop Management                     |
|  - Conductor Onboard Portal (OpenCV Camera Scanner & Manifest)  |
|  - Executive Dashboard, KPI Cards & Embedded Matplotlib Charts  |
+-----------------------------------------------------------------+
                                |
+-----------------------------------------------------------------+
|                   2. Business Logic Layer (Services)            |
|  - AuthService: Bcrypt / PBKDF2 Password Hashing & RBAC Sessions|
|  - BookingService: Atomic Transactions & Concurrency Locks      |
|  - CancellationService: Tiered Refunds (100% / 75% / 50%)       |
|  - WaitlistService: FIFO Queue Priority & Auto-Allocation       |
|  - VerificationService: QR Token Parsing & Boarding Validation  |
|  - ReportService: Analytical Queries & CSV Report Export        |
+-----------------------------------------------------------------+
                                |
+-----------------------------------------------------------------+
|                   3. Data Access Layer (Repositories)           |
|  - Parameterized SQL execution (SQL Injection Prevention)       |
|  - Repositories: User, Passenger, Bus, Route, Schedule, Seats,   |
|    Booking, Payment, Refund, Waitlist, Checkin, Report          |
+-----------------------------------------------------------------+
                                |
+-----------------------------------------------------------------+
|                   4. Relational Database Engine                 |
|  - MySQL 8.x (InnoDB Engine, utf8mb4, Stored Procedures, Views) |
|  - Unified SQLite 3 Fallback Engine (WAL Mode, BEGIN IMMEDIATE) |
+-----------------------------------------------------------------+
```

---

## 4. Database Schema & Normalization

The schema is normalized to **Third Normal Form (3NF)** and **Boyce-Codd Normal Form (BCNF)**:

```
+---------------------------------------------------------------+
|                       13 CORE RELATIONS                       |
+---------------------------------------------------------------+
| 1. USERS            | Master accounts & RBAC roles            |
| 2. PASSENGERS       | Passenger demographic details           |
| 3. BUSES            | Fleet assets, capacities & types        |
| 4. ROUTES           | Corridors, origins, destinations & km   |
| 5. BUS_STOPS        | Physical stations & pickup points       |
| 6. ROUTE_STOPS      | Ordered sequence of route waypoints     |
| 7. SCHEDULES        | Timetable linking bus + route + times   |
| 8. SCHEDULE_SEATS   | Authoritative per-trip seat inventory   |
| 9. BOOKINGS         | Reservation records (unique reference)  |
| 10. PAYMENTS        | Payment transaction ledger              |
| 11. REFUNDS         | Cancellation penalty & refund ledger    |
| 12. WAITLIST        | FIFO priority queue for sold-out trips  |
| 13. TICKET_CHECKINS | Conductor verification log (QR / manual)|
| 14. AUDIT_LOGS      | System-wide change data capture trail   |
+---------------------------------------------------------------+
```

### Relational Views:
1. `vw_available_buses`: Active buses with assigned schedule counts.
2. `vw_available_seats`: Live available, booked, and blocked seat counts.
3. `vw_booking_details`: Full denormalized booking, passenger, route, and payment details.
4. `vw_passenger_booking_history`: Passenger lifetime trips, total spend, and recency.
5. `vw_route_revenue`: Route gross revenue, refunds issued, net profit, and passenger volume.
6. `vw_schedule_occupancy`: Trip load factors and seat occupancy percentages.

---

## 5. Key DBMS Highlights for Academic Viva

### Q1: How does your system prevent the "Double-Booking" anomaly?
**Answer**:
1. We utilize an authoritative per-schedule seat inventory table (`schedule_seats`).
2. Booking operations execute inside an explicit atomic transaction (`START TRANSACTION` / `BEGIN IMMEDIATE`).
3. The selected seat row is acquired using row-level locking (`SELECT ... FOR UPDATE`).
4. If two concurrent users attempt to reserve the same seat simultaneously, the first transaction acquires the lock, updates the seat to `BOOKED`, and commits. The second transaction is blocked until the lock releases, sees that the seat is now `BOOKED`, and aborts with a graceful concurrency error.
5. As a defense-in-depth measure, we enforce a partial unique index on the `bookings` table:
   ```sql
   CREATE UNIQUE INDEX idx_bookings_active_seat
   ON bookings (schedule_id, seat_number)
   WHERE booking_status = 'CONFIRMED';
   ```

### Q2: Why did you separate `USERS` and `PASSENGERS` into distinct tables?
**Answer**:
This satisfies **3NF and BCNF**:
- A single user account (e.g., a family head or administrator) can book tickets for multiple individual passengers (spouses, children, senior citizens).
- Authentication attributes (`email`, `password_hash`, `role`) depend on `user_id`.
- Traveler attributes (`passenger_name`, `age`, `gender`, `phone`) depend on `passenger_id`.
- Combining them into a single relation would create transitive functional dependencies and duplicate user accounts for every passenger profile.

### Q3: How is historical data retained when a booking is cancelled?
**Answer**:
We never physically execute `DELETE FROM bookings`. Instead:
1. The booking record is updated: `booking_status = 'CANCELLED'`.
2. The corresponding seat in `schedule_seats` is updated back to `AVAILABLE`.
3. A refund record is generated in `refunds` detailing the calculated refund amount and penalty percentage.
4. The payment record status is updated to `REFUNDED`.
5. Because our partial unique index only indexes rows where `booking_status = 'CONFIRMED'`, cancelling the booking immediately releases the seat for new reservations while preserving the complete historical, financial, and audit trail.

### Q4: How does your waitlist auto-allocation mechanism work?
**Answer**:
When a confirmed booking is cancelled, the system inspects the schedule's remaining capacity:
- If the schedule was at 100% capacity prior to cancellation, the system queries the `waitlist` table for the passenger with `queue_position = 1` and `waitlist_status = 'WAITING'`.
- The released seat is automatically allocated to that passenger, updating their status to `ALLOCATED` and advancing subsequent queue positions.

---

## 6. Verification and Test Results

The test suite consists of **23 automated pytest test cases** passing with 100% success:
- Multi-threaded concurrency race condition testing.
- Password hashing and authentication isolation.
- Referential integrity and constraint validation.
- Conductor check-in and duplicate scan rejection.
- Digital QR code and ReportLab PDF boarding pass generation.
- Analytics and CSV report exports.
