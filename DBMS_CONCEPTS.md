# DBMS Concepts, Viva Guide & 15+ SQL Examples
## Smart Bus Reservation System | College Mini Project Reference

This document maps theoretical Database Management System (DBMS) principles directly to concrete implementations and SQL queries in this desktop application.

---

## 1. Core DBMS Concepts Map

### 1. Primary Keys & Foreign Keys
- **Where Used**: Every table in `app/schema.sql` possesses a surrogate integer primary key (`user_id`, `route_id`, `bus_id`, `schedule_id`, `passenger_id`, `booking_id`, `payment_id`). Foreign keys link child tables (`schedules.bus_id -> buses.bus_id`, `bookings.schedule_id -> schedules.schedule_id`, etc.).
- **Viva Explanation**: A Primary Key uniquely identifies each record in a relation without nulls. A Foreign Key maintains referential integrity by ensuring the value corresponds to a valid existing record in the referenced parent relation.
- **SQL Example**:
  ```sql
  CREATE TABLE schedules (
      schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
      bus_id INTEGER NOT NULL REFERENCES buses(bus_id) ON DELETE RESTRICT,
      route_id INTEGER NOT NULL REFERENCES routes(route_id) ON DELETE RESTRICT,
      fare REAL NOT NULL CHECK(fare >= 0)
  );
  ```

---

### 2. Database Normalization (1NF, 2NF, 3NF)
- **Where Used**: The schema decomposes bus attributes, route geographies, departure schedules, traveler demographics, and reservation tickets into distinct relations.
  - **1NF (First Normal Form)**: All column values are atomic (e.g., passenger details and routes are separated; no comma-separated seat lists).
  - **2NF (Second Normal Form)**: All non-key attributes are fully functionally dependent on the complete primary key.
  - **3NF (Third Normal Form)**: No transitive dependencies exist (e.g., bus capacity is not repeated in bookings; distance is stored in `routes`, not in `schedules`).
- **Viva Explanation**: Normalization eliminates data redundancy and update/delete anomalies while preserving functional dependencies across relations.

---

### 3. Partial Unique Index & Seat Availability
- **Where Used**: `idx_bookings_active_seat` in `app/schema.sql`.
- **Viva Explanation**: If we use a plain `UNIQUE(schedule_id, seat_number)` constraint, a cancelled booking would permanently block that seat from ever being booked again unless the row is deleted. However, deleting historical bookings destroys financial and audit records. A **Partial Unique Index** enforces uniqueness ONLY where `status = 'CONFIRMED'`. When a booking is updated to `CANCELLED`, the partial index releases that seat immediately while retaining the full historical audit trail.
- **SQL Example**:
  ```sql
  CREATE UNIQUE INDEX idx_bookings_active_seat
  ON bookings (schedule_id, seat_number)
  WHERE status = 'CONFIRMED';
  ```

---

### 4. Dynamic Seat Availability (Zero Anomalies)
- **Where Used**: In `schedule_repository.py` and `bus_search_page.py`.
- **Viva Explanation**: Storing an `available_seats` integer column in the `schedules` table creates an update anomaly risk (a race condition or missed decrement makes availability inconsistent with actual bookings). Instead, our application computes availability dynamically:
  $$\text{Available Seats} = \text{bus.total\_seats} - \text{COUNT(active confirmed bookings)}$$
- **SQL Example**:
  ```sql
  SELECT 
      s.schedule_id,
      b.bus_number,
      b.total_seats,
      (SELECT COUNT(*) FROM bookings bk WHERE bk.schedule_id = s.schedule_id AND bk.status = 'CONFIRMED') AS booked_seats,
      (b.total_seats - (SELECT COUNT(*) FROM bookings bk WHERE bk.schedule_id = s.schedule_id AND bk.status = 'CONFIRMED')) AS available_seats
  FROM schedules s
  INNER JOIN buses b ON s.bus_id = b.bus_id
  WHERE s.schedule_id = 1;
  ```

---

### 5. ACID Transactions & Concurrency Safety
- **Where Used**: `booking_service.reserve_seat` and `cancellation_service.cancel_booking`.
- **Viva Explanation**:
  - **Atomicity**: Either all 3 records (Passenger, Booking, Payment) are committed, or none are.
  - **Consistency**: Database transitions from one valid state to another, obeying all foreign keys, CHECK constraints, and partial indexes.
  - **Isolation**: Handled via `BEGIN IMMEDIATE;`, which acquires a write lock so no concurrent thread can book the same seat in the interval between availability checking and insertion.
  - **Durability**: Committed data is written to disk and SQLite WAL journal.
- **Code Pattern**:
  ```python
  conn = get_connection(autocommit_mode=True)
  with transaction(conn, mode="IMMEDIATE") as cursor:
      # Step 1: Check availability inside transaction
      cursor.execute("SELECT ... WHERE schedule_id=? AND seat_number=? AND status='CONFIRMED'", (s_id, seat))
      # Step 2: Insert passenger, booking, payment
      ...
      # Automatic COMMIT on exit or ROLLBACK on exception
  ```

---

### 6. SQL Injection Prevention
- **Where Used**: In all repositories across the codebase.
- **Viva Explanation**: SQL concatenation (`f"SELECT * WHERE username='{u}'"`) allows malicious SQL injections like `' OR '1'='1`. We use parameterized queries (`?` placeholders) which pass parameters as pure data literals to SQLite's query compiler.
- **SQL Example**:
  ```python
  cursor.execute("SELECT * FROM users WHERE lower(username) = lower(?);", (username.strip(),))
  ```

---

## 2. 15+ Comprehensive Viva SQL Queries

The following queries demonstrate the exact relational operations executed inside the Smart Bus Reservation System.

### Query 1: Database Catalog & Foreign Key Verification
```sql
PRAGMA foreign_keys;
PRAGMA foreign_key_check;
```
*Verifies SQLite foreign key constraints are active and no referential integrity violations exist.*

---

### Query 2: INNER JOIN Across 4 Tables
```sql
SELECT 
    b.booking_reference,
    p.full_name,
    p.phone,
    bs.bus_number,
    bs.bus_name,
    r.source || ' -> ' || r.destination AS route_path,
    s.travel_date,
    s.departure_time,
    b.seat_number,
    b.amount
FROM bookings b
INNER JOIN passengers p ON b.passenger_id = p.passenger_id
INNER JOIN schedules s ON b.schedule_id = s.schedule_id
INNER JOIN buses bs ON s.bus_id = bs.bus_id
INNER JOIN routes r ON s.route_id = r.route_id
WHERE b.status = 'CONFIRMED'
ORDER BY s.travel_date ASC, s.departure_time ASC;
```
*Retrieves complete passenger boarding manifest by joining bookings, passengers, schedules, buses, and routes.*

---

### Query 3: LEFT OUTER JOIN to Include Zero-Booking Routes
```sql
SELECT 
    r.route_id,
    r.source,
    r.destination,
    r.distance_km,
    COUNT(b.booking_id) AS total_bookings,
    COALESCE(SUM(CASE WHEN b.status = 'CONFIRMED' THEN b.amount ELSE 0 END), 0.0) AS route_revenue
FROM routes r
LEFT JOIN schedules s ON r.route_id = s.route_id
LEFT JOIN bookings b ON s.schedule_id = b.schedule_id
GROUP BY r.route_id, r.source, r.destination, r.distance_km
ORDER BY route_revenue DESC;
```
*Demonstrates LEFT OUTER JOIN ensuring routes without scheduled journeys still appear in management reports.*

---

### Query 4: Aggregate Function with GROUP BY and HAVING
```sql
SELECT 
    bs.bus_id,
    bs.bus_number,
    bs.bus_name,
    COUNT(b.booking_id) AS total_confirmed_bookings,
    SUM(b.amount) AS total_revenue
FROM buses bs
INNER JOIN schedules s ON bs.bus_id = s.bus_id
INNER JOIN bookings b ON s.schedule_id = b.schedule_id
WHERE b.status = 'CONFIRMED'
GROUP BY bs.bus_id, bs.bus_number, bs.bus_name
HAVING COUNT(b.booking_id) >= 1
ORDER BY total_revenue DESC;
```
*Aggregates revenue per bus vehicle and filters groups using the HAVING clause.*

---

### Query 5: Correlated Subquery for Live Seat Occupancy
```sql
SELECT 
    s.schedule_id,
    s.travel_date,
    s.departure_time,
    bs.bus_number,
    bs.total_seats,
    (SELECT COUNT(*) 
     FROM bookings bk 
     WHERE bk.schedule_id = s.schedule_id AND bk.status = 'CONFIRMED') AS booked_seats,
    ROUND(
        ((SELECT COUNT(*) FROM bookings bk WHERE bk.schedule_id = s.schedule_id AND bk.status = 'CONFIRMED') * 100.0) 
        / bs.total_seats, 1
    ) AS occupancy_percentage
FROM schedules s
INNER JOIN buses bs ON s.bus_id = bs.bus_id
WHERE s.status = 'SCHEDULED'
ORDER BY occupancy_percentage DESC;
```
*Computes occupancy rate dynamically per schedule using a correlated subquery.*

---

### Query 6: Schedule Conflict Detection Query
```sql
SELECT schedule_id, travel_date, departure_time, arrival_time
FROM schedules
WHERE bus_id = 1
  AND travel_date = '2026-10-27'
  AND status <> 'CANCELLED'
  AND NOT ('14:00' <= departure_time OR '10:00' >= arrival_time);
```
*Checks if a proposed journey for bus #1 on 2026-10-27 overlaps with an existing journey.*

---

### Query 7: Daily Sales Trend with Date Function
```sql
SELECT 
    date(b.booking_date) AS booking_day,
    COUNT(b.booking_id) AS bookings_count,
    ROUND(AVG(b.amount), 2) AS avg_ticket_fare,
    SUM(b.amount) AS daily_revenue
FROM bookings b
WHERE b.status = 'CONFIRMED'
GROUP BY date(b.booking_date)
ORDER BY booking_day DESC;
```
*Calculates daily financial metrics using aggregate functions (`COUNT`, `AVG`, `SUM`).*

---

### Query 8: Passenger Booking History with Authorization Filter
```sql
SELECT 
    b.booking_reference,
    p.full_name,
    s.travel_date,
    s.departure_time,
    r.source,
    r.destination,
    b.seat_number,
    b.amount,
    b.status
FROM bookings b
INNER JOIN passengers p ON b.passenger_id = p.passenger_id
INNER JOIN schedules s ON b.schedule_id = s.schedule_id
INNER JOIN routes r ON s.route_id = r.route_id
WHERE p.user_id = 2  -- Enforces logged-in passenger data isolation
ORDER BY b.booking_date DESC;
```
*Enforces data boundary so passengers only see their own tickets.*

---

### Query 9: Seat Occupancy Verification Before Write
```sql
SELECT booking_id, seat_number, status 
FROM bookings 
WHERE schedule_id = 3 
  AND seat_number = 12 
  AND status = 'CONFIRMED';
```
*Used inside BEGIN IMMEDIATE transaction to prevent double-booking.*

---

### Query 10: Atomic Booking Creation
```sql
BEGIN IMMEDIATE;

INSERT INTO passengers (user_id, full_name, age, gender, phone)
VALUES (2, 'Rahul Sharma', 28, 'Male', '9822012345');

INSERT INTO bookings (booking_reference, schedule_id, passenger_id, seat_number, amount, status)
VALUES ('BUS-20261026-9A1B2C3D', 3, last_insert_rowid(), 12, 480.0, 'CONFIRMED');

INSERT INTO payments (booking_id, amount, payment_method, payment_status)
VALUES (last_insert_rowid(), 480.0, 'UPI', 'PAID');

COMMIT;
```
*Demonstrates multi-table atomic write transaction with foreign key linking via `last_insert_rowid()`.*

---

### Query 11: Cancellation & Seat Release Transaction
```sql
BEGIN IMMEDIATE;

UPDATE bookings 
SET status = 'CANCELLED', cancellation_date = datetime('now', 'localtime')
WHERE booking_id = 4 AND status = 'CONFIRMED';

UPDATE payments 
SET payment_status = 'REFUNDED'
WHERE booking_id = 4;

COMMIT;
```
*Cancels booking, triggers partial index release of seat, and records simulated refund.*

---

### Query 12: Soft Deactivation of Bus Fleet
```sql
UPDATE buses 
SET is_active = 0 
WHERE bus_id = 5;
```
*Soft deactivation: preserves past booking history and referential integrity while hiding bus from new schedules.*

---

### Query 13: Subquery with IN Operator for Active City Destinations
```sql
SELECT DISTINCT destination 
FROM routes 
WHERE route_id IN (
    SELECT route_id FROM schedules WHERE status = 'SCHEDULED'
)
ORDER BY destination ASC;
```
*Finds all destinations that currently have scheduled departures using a subquery.*

---

### Query 14: Audit Report of Cancelled Bookings with Payment Status
```sql
SELECT 
    b.booking_reference,
    p.full_name,
    p.phone,
    b.cancellation_date,
    b.amount,
    pm.payment_method,
    pm.payment_status
FROM bookings b
INNER JOIN passengers p ON b.passenger_id = p.passenger_id
LEFT JOIN payments pm ON b.booking_id = pm.booking_id
WHERE b.status = 'CANCELLED'
ORDER BY b.cancellation_date DESC;
```
*Provides financial audit of cancelled tickets and issued refunds.*

---

### Query 15: Bus Capacity and Seat Layout Verification
```sql
SELECT 
    b.bus_id,
    b.bus_number,
    b.bus_type,
    b.total_seats,
    COUNT(s.schedule_id) AS total_assigned_trips
FROM buses b
LEFT JOIN schedules s ON b.bus_id = s.bus_id
GROUP BY b.bus_id, b.bus_number, b.bus_type, b.total_seats
ORDER BY b.total_seats DESC;
```
*Shows fleet capacity distribution across coach types.*
