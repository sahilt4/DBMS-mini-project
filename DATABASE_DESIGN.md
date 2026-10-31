# Database Design Specification
## Bus Reservation and Management System (BRMS)

---

## 1. Overview & Architectural Principles

The **Bus Reservation and Management System (BRMS)** database is engineered on **MySQL 8.x (InnoDB)** with full cross-compatibility for a unified SQLite engine. The schema employs **InnoDB** engine characteristics including:
- Row-level locking (`SELECT ... FOR UPDATE`).
- Strict ACID transaction semantics (`START TRANSACTION`, `COMMIT`, `ROLLBACK`).
- Foreign key cascading and deletion restrictions.
- Explicit UTF-8 character encoding (`utf8mb4`).
- Relational Views for secure reporting.
- Stored Procedures and Triggers for encapsulated business logic and audit compliance.

---

## 2. Data Dictionary (13 Core Tables + Audit Logs)

### 1. `users`
Centralized account identity and authentication table.

| Column | Data Type | Nullable | Key / Default | Description |
|---|---|---|---|---|
| `user_id` | INT AUTO_INCREMENT | NO | PK | Surrogate primary key |
| `full_name` | VARCHAR(100) | NO | | User's legal name |
| `email` | VARCHAR(150) | NO | UNIQUE | Login email identifier |
| `password_hash` | VARCHAR(255) | NO | | Salted bcrypt or PBKDF2-SHA256 hash |
| `role` | ENUM('ADMIN', 'PASSENGER', 'CONDUCTOR') | NO | DEFAULT 'PASSENGER' | RBAC role |
| `phone` | VARCHAR(20) | YES | NULL | Contact mobile number |
| `account_status` | ENUM('ACTIVE', 'SUSPENDED', 'DEACTIVATED') | NO | DEFAULT 'ACTIVE' | Account lifecycle state |
| `created_at` | DATETIME | NO | DEFAULT CURRENT_TIMESTAMP | Registration timestamp |

---

### 2. `passengers`
Passenger demographic details linked to user credentials.

| Column | Data Type | Nullable | Key / Default | Description |
|---|---|---|---|---|
| `passenger_id` | INT AUTO_INCREMENT | NO | PK | Primary key |
| `user_id` | INT | YES | FK -> `users(user_id)` | Linked account (NULL for guest/walk-ins) |
| `full_name` | VARCHAR(100) | NO | | Traveler name |
| `age` | INT | NO | CHECK(age BETWEEN 1 AND 120) | Traveler age |
| `gender` | ENUM('MALE', 'FEMALE', 'OTHER') | NO | | Traveler gender |
| `phone` | VARCHAR(20) | YES | NULL | Emergency contact |
| `created_at` | DATETIME | NO | DEFAULT CURRENT_TIMESTAMP | Profile creation timestamp |

---

### 3. `buses`
Fleet master table storing coach specifications.

| Column | Data Type | Nullable | Key / Default | Description |
|---|---|---|---|---|
| `bus_id` | INT AUTO_INCREMENT | NO | PK | Primary key |
| `registration_number`| VARCHAR(20) | NO | UNIQUE | Vehicle registration (e.g. MH-12-AB-1234) |
| `bus_name` | VARCHAR(100) | NO | | Marketing/Coach name |
| `bus_type` | ENUM('STANDARD', 'DELUXE', 'SLEEPER', 'AC_SEATER', 'VOLVO_MULTI_AXLE') | NO | DEFAULT 'STANDARD' | Coach seating class |
| `capacity` | INT | NO | CHECK(capacity BETWEEN 10 AND 60) | Physical seat count |
| `operational_status` | ENUM('ACTIVE', 'MAINTENANCE', 'RETIRED') | NO | DEFAULT 'ACTIVE' | Fleet service readiness |
| `created_at` | DATETIME | NO | DEFAULT CURRENT_TIMESTAMP | Asset onboarding date |

---

### 4. `routes`
Journey corridors connecting origin and destination hubs.

| Column | Data Type | Nullable | Key / Default | Description |
|---|---|---|---|---|
| `route_id` | INT AUTO_INCREMENT | NO | PK | Primary key |
| `source` | VARCHAR(100) | NO | | Origin city/terminal |
| `destination` | VARCHAR(100) | NO | | Destination city/terminal |
| `distance` | DECIMAL(8, 2) | NO | CHECK(distance > 0) | Journey distance in km |
| `estimated_duration`| INT | NO | CHECK(estimated_duration > 0) | Estimated journey time (minutes) |
| `route_status` | ENUM('ACTIVE', 'INACTIVE') | NO | DEFAULT 'ACTIVE' | Operational route flag |
| `created_at` | DATETIME | NO | DEFAULT CURRENT_TIMESTAMP | Creation date |

*Constraint*: `CHECK (LOWER(TRIM(source)) <> LOWER(TRIM(destination)))`

---

### 5. `bus_stops`
Physical boarding and dropping points.

| Column | Data Type | Nullable | Key / Default | Description |
|---|---|---|---|---|
| `stop_id` | INT AUTO_INCREMENT | NO | PK | Primary key |
| `stop_name` | VARCHAR(120) | NO | | Stop name (e.g. Shivaji Nagar) |
| `city` | VARCHAR(100) | NO | | City name (e.g. Pune) |
| `address` | TEXT | YES | NULL | Detailed street address |
| `created_at` | DATETIME | NO | DEFAULT CURRENT_TIMESTAMP | Creation timestamp |

---

### 6. `route_stops`
Ordered sequence of stops defining intermediate waypoints along a route.

| Column | Data Type | Nullable | Key / Default | Description |
|---|---|---|---|---|
| `route_stop_id` | INT AUTO_INCREMENT | NO | PK | Primary key |
| `route_id` | INT | NO | FK -> `routes(route_id)` | Route reference |
| `stop_id` | INT | NO | FK -> `bus_stops(stop_id)` | Physical stop reference |
| `stop_sequence` | INT | NO | CHECK(stop_sequence >= 1) | Sequence order index |
| `distance_from_origin`| DECIMAL(8, 2) | NO | DEFAULT 0.00 | Distance from origin in km |
| `arrival_offset_minutes`| INT | NO | DEFAULT 0 | Schedule offset in minutes |

*Constraints*:
- `UNIQUE (route_id, stop_sequence)`
- `UNIQUE (route_id, stop_id)`

---

### 7. `schedules`
Concrete bus departure timetable mapping buses to routes.

| Column | Data Type | Nullable | Key / Default | Description |
|---|---|---|---|---|
| `schedule_id` | INT AUTO_INCREMENT | NO | PK | Primary key |
| `bus_id` | INT | NO | FK -> `buses(bus_id)` | Assigned vehicle |
| `route_id` | INT | NO | FK -> `routes(route_id)` | Assigned route corridor |
| `departure_datetime`| DATETIME | NO | | Departure timestamp |
| `arrival_datetime` | DATETIME | NO | | Arrival timestamp |
| `base_fare` | DECIMAL(10, 2) | NO | CHECK(base_fare > 0) | Standard ticket price |
| `schedule_status` | ENUM('SCHEDULED', 'BOARDING', 'IN_TRANSIT', 'COMPLETED', 'CANCELLED') | NO | DEFAULT 'SCHEDULED' | Journey operational state |
| `created_at` | DATETIME | NO | DEFAULT CURRENT_TIMESTAMP | Timetable publish date |

*Constraint*: `CHECK (arrival_datetime > departure_datetime)`

---

### 8. `schedule_seats`
Authoritative real-time inventory of physical seat occupancy for each schedule.

| Column | Data Type | Nullable | Key / Default | Description |
|---|---|---|---|---|
| `schedule_seat_id` | INT AUTO_INCREMENT | NO | PK | Primary key |
| `schedule_id` | INT | NO | FK -> `schedules(schedule_id)` ON DELETE CASCADE | Associated journey |
| `seat_number` | INT | NO | CHECK(seat_number >= 1) | Physical seat number |
| `seat_status` | ENUM('AVAILABLE', 'BOOKED', 'BLOCKED') | NO | DEFAULT 'AVAILABLE' | Live occupancy status |
| `updated_at` | DATETIME | NO | DEFAULT CURRENT_TIMESTAMP | Last state change timestamp |

*Constraint*: `UNIQUE (schedule_id, seat_number)`

---

### 9. `bookings`
Reservation tickets binding passengers to scheduled seats.

| Column | Data Type | Nullable | Key / Default | Description |
|---|---|---|---|---|
| `booking_id` | INT AUTO_INCREMENT | NO | PK | Primary key |
| `booking_reference`| VARCHAR(30) | NO | UNIQUE | Public ticket reference code |
| `passenger_id` | INT | NO | FK -> `passengers(passenger_id)` | Traveler profile |
| `schedule_id` | INT | NO | FK -> `schedules(schedule_id)` | Scheduled journey |
| `seat_number` | INT | NO | CHECK(seat_number >= 1) | Allocated seat number |
| `booking_date` | DATETIME | NO | DEFAULT CURRENT_TIMESTAMP | Transaction timestamp |
| `total_amount` | DECIMAL(10, 2) | NO | CHECK(total_amount >= 0) | Paid amount |
| `booking_status` | ENUM('CONFIRMED', 'CANCELLED', 'CHECKED_IN', 'NO_SHOW') | NO | DEFAULT 'CONFIRMED' | Ticket state |
| `cancellation_date`| DATETIME | YES | NULL | Cancellation timestamp |

---

### 10. `payments`
Financial transaction ledger for payments.

| Column | Data Type | Nullable | Key / Default | Description |
|---|---|---|---|---|
| `payment_id` | INT AUTO_INCREMENT | NO | PK | Primary key |
| `booking_id` | INT | NO | FK -> `bookings(booking_id)` | Associated ticket |
| `amount` | DECIMAL(10, 2) | NO | CHECK(amount >= 0) | Invoiced transaction amount |
| `payment_method` | ENUM('UPI', 'CREDIT_CARD', 'DEBIT_CARD', 'NET_BANKING', 'CASH') | NO | | Method used |
| `transaction_reference`| VARCHAR(60) | NO | UNIQUE | Payment gateway reference |
| `payment_status` | ENUM('PENDING', 'SUCCESS', 'FAILED', 'REFUNDED') | NO | DEFAULT 'PENDING' | Transaction lifecycle |
| `payment_date` | DATETIME | NO | DEFAULT CURRENT_TIMESTAMP | Transaction completion time |

---

### 11. `refunds`
Cancellation penalty and financial reimbursement ledger.

| Column | Data Type | Nullable | Key / Default | Description |
|---|---|---|---|---|
| `refund_id` | INT AUTO_INCREMENT | NO | PK | Primary key |
| `payment_id` | INT | NO | FK -> `payments(payment_id)` | Original payment record |
| `booking_id` | INT | NO | FK -> `bookings(booking_id)` | Cancelled ticket |
| `refund_amount` | DECIMAL(10, 2) | NO | CHECK(refund_amount >= 0) | Refund sum |
| `refund_reason` | VARCHAR(255) | YES | NULL | Cancellation justification |
| `refund_status` | ENUM('PENDING', 'PROCESSED', 'FAILED') | NO | DEFAULT 'PROCESSED' | Payout state |
| `refund_date` | DATETIME | NO | DEFAULT CURRENT_TIMESTAMP | Reversal timestamp |

---

### 12. `waitlist`
FIFO priority queue for high-demand sold-out schedules.

| Column | Data Type | Nullable | Key / Default | Description |
|---|---|---|---|---|
| `waitlist_id` | INT AUTO_INCREMENT | NO | PK | Primary key |
| `passenger_id` | INT | NO | FK -> `passengers(passenger_id)` ON DELETE CASCADE | Waitlisted passenger |
| `schedule_id` | INT | NO | FK -> `schedules(schedule_id)` ON DELETE CASCADE | Sold-out departure |
| `preferred_seat_type`| VARCHAR(30) | YES | DEFAULT 'ANY' | Seating preference |
| `queue_position` | INT | NO | CHECK(queue_position >= 1) | FIFO queue sequence |
| `waitlist_status` | ENUM('WAITING', 'ALLOCATED', 'EXPIRED', 'CANCELLED') | NO | DEFAULT 'WAITING' | Queue entry status |
| `created_at` | DATETIME | NO | DEFAULT CURRENT_TIMESTAMP | Entry submission timestamp |

---

### 13. `ticket_checkins`
Onboard conductor ticket verification ledger.

| Column | Data Type | Nullable | Key / Default | Description |
|---|---|---|---|---|
| `checkin_id` | INT AUTO_INCREMENT | NO | PK | Primary key |
| `booking_id` | INT | NO | FK -> `bookings(booking_id)` | Checked-in ticket |
| `checkin_datetime` | DATETIME | NO | DEFAULT CURRENT_TIMESTAMP | Scan timestamp |
| `verified_by_user_id`| INT | NO | FK -> `users(user_id)` | Conductor user account |
| `checkin_method` | ENUM('QR_SCAN', 'MANUAL') | NO | DEFAULT 'QR_SCAN' | Verification method |
| `boarding_stop_id` | INT | YES | FK -> `bus_stops(stop_id)` | Boarding station |
| `remarks` | VARCHAR(255) | YES | NULL | Conductor notes |

*Constraint*: `UNIQUE (booking_id)`

---

### 14. `audit_logs`
System-wide security and transaction audit trail.

| Column | Data Type | Nullable | Key / Default | Description |
|---|---|---|---|---|
| `log_id` | INT AUTO_INCREMENT | NO | PK | Primary key |
| `user_id` | INT | YES | FK -> `users(user_id)` ON DELETE SET NULL | Acting actor |
| `action` | VARCHAR(50) | NO | | Operation (INSERT, UPDATE, DELETE) |
| `entity_name` | VARCHAR(60) | NO | | Affected table |
| `entity_id` | INT | YES | NULL | Affected record ID |
| `old_values` | JSON / TEXT | YES | NULL | State prior to modification |
| `new_values` | JSON / TEXT | YES | NULL | State after modification |
| `ip_address` | VARCHAR(45) | YES | NULL | Client IP/Host identifier |
| `created_at` | DATETIME | NO | DEFAULT CURRENT_TIMESTAMP | Log capture timestamp |

---

## 3. Relational Views

### View 1: `vw_available_buses`
Computes active fleet resources with assigned routes, vehicle capacity, and operating status.
```sql
CREATE OR REPLACE VIEW vw_available_buses AS
SELECT 
    b.bus_id,
    b.registration_number,
    b.bus_name,
    b.bus_type,
    b.capacity,
    b.operational_status,
    COUNT(s.schedule_id) AS total_schedules_assigned
FROM buses b
LEFT JOIN schedules s ON b.bus_id = s.bus_id AND s.schedule_status = 'SCHEDULED'
WHERE b.operational_status = 'ACTIVE'
GROUP BY b.bus_id, b.registration_number, b.bus_name, b.bus_type, b.capacity, b.operational_status;
```

### View 2: `vw_available_seats`
Computes live per-schedule seat availability directly from `schedule_seats`.
```sql
CREATE OR REPLACE VIEW vw_available_seats AS
SELECT 
    s.schedule_id,
    b.bus_id,
    b.registration_number,
    b.capacity AS total_capacity,
    COUNT(CASE WHEN ss.seat_status = 'AVAILABLE' THEN 1 END) AS available_seats,
    COUNT(CASE WHEN ss.seat_status = 'BOOKED' THEN 1 END) AS booked_seats,
    COUNT(CASE WHEN ss.seat_status = 'BLOCKED' THEN 1 END) AS blocked_seats
FROM schedules s
JOIN buses b ON s.bus_id = b.bus_id
LEFT JOIN schedule_seats ss ON s.schedule_id = ss.schedule_id
GROUP BY s.schedule_id, b.bus_id, b.registration_number, b.capacity;
```

### View 3: `vw_booking_details`
Denormalizes booking records with traveler, journey, vehicle, and payment metadata.
```sql
CREATE OR REPLACE VIEW vw_booking_details AS
SELECT 
    bk.booking_id,
    bk.booking_reference,
    bk.booking_date,
    bk.seat_number,
    bk.total_amount,
    bk.booking_status,
    p.passenger_id,
    p.full_name AS passenger_name,
    p.phone AS passenger_phone,
    r.route_id,
    r.source,
    r.destination,
    s.schedule_id,
    s.departure_datetime,
    s.arrival_datetime,
    b.bus_id,
    b.bus_name,
    b.bus_type,
    b.registration_number,
    pm.payment_id,
    pm.payment_method,
    pm.transaction_reference,
    pm.payment_status,
    tc.checkin_datetime
FROM bookings bk
JOIN passengers p ON bk.passenger_id = p.passenger_id
JOIN schedules s ON bk.schedule_id = s.schedule_id
JOIN routes r ON s.route_id = r.route_id
JOIN buses b ON s.bus_id = b.bus_id
LEFT JOIN payments pm ON bk.booking_id = pm.booking_id
LEFT JOIN ticket_checkins tc ON bk.booking_id = tc.booking_id;
```

### View 4: `vw_passenger_booking_history`
Aggregates passenger travel history with lifetime revenue and journey volume.
```sql
CREATE OR REPLACE VIEW vw_passenger_booking_history AS
SELECT 
    p.passenger_id,
    p.full_name,
    p.phone,
    u.email,
    COUNT(bk.booking_id) AS total_bookings_made,
    SUM(CASE WHEN bk.booking_status IN ('CONFIRMED', 'CHECKED_IN') THEN bk.total_amount ELSE 0 END) AS total_spend,
    MAX(bk.booking_date) AS last_booking_date
FROM passengers p
LEFT JOIN users u ON p.user_id = u.user_id
LEFT JOIN bookings bk ON p.passenger_id = bk.passenger_id
GROUP BY p.passenger_id, p.full_name, p.phone, u.email;
```

### View 5: `vw_route_revenue`
Calculates route-level financial analytics and load factors.
```sql
CREATE OR REPLACE VIEW vw_route_revenue AS
SELECT 
    r.route_id,
    r.source,
    r.destination,
    r.distance,
    COUNT(DISTINCT s.schedule_id) AS total_trips,
    COUNT(CASE WHEN bk.booking_status IN ('CONFIRMED', 'CHECKED_IN') THEN 1 END) AS total_passengers_carried,
    COALESCE(SUM(CASE WHEN bk.booking_status IN ('CONFIRMED', 'CHECKED_IN') THEN bk.total_amount ELSE 0 END), 0) AS total_gross_revenue,
    COALESCE(SUM(ref.refund_amount), 0) AS total_refunds_issued,
    COALESCE(SUM(CASE WHEN bk.booking_status IN ('CONFIRMED', 'CHECKED_IN') THEN bk.total_amount ELSE 0 END), 0) - COALESCE(SUM(ref.refund_amount), 0) AS net_revenue
FROM routes r
LEFT JOIN schedules s ON r.route_id = s.route_id
LEFT JOIN bookings bk ON s.schedule_id = bk.schedule_id
LEFT JOIN refunds ref ON bk.booking_id = ref.booking_id
GROUP BY r.route_id, r.source, r.destination, r.distance;
```

### View 6: `vw_schedule_occupancy`
Computes trip load factor percentage and seat occupancy metrics.
```sql
CREATE OR REPLACE VIEW vw_schedule_occupancy AS
SELECT 
    s.schedule_id,
    r.source,
    r.destination,
    s.departure_datetime,
    s.arrival_datetime,
    b.bus_name,
    b.capacity AS total_capacity,
    COUNT(CASE WHEN ss.seat_status = 'BOOKED' THEN 1 END) AS occupied_seats,
    COUNT(CASE WHEN ss.seat_status = 'AVAILABLE' THEN 1 END) AS vacant_seats,
    ROUND((COUNT(CASE WHEN ss.seat_status = 'BOOKED' THEN 1 END) * 100.0) / NULLIF(b.capacity, 0), 2) AS occupancy_percentage
FROM schedules s
JOIN routes r ON s.route_id = r.route_id
JOIN buses b ON s.bus_id = b.bus_id
LEFT JOIN schedule_seats ss ON s.schedule_id = ss.schedule_id
GROUP BY s.schedule_id, r.source, r.destination, s.departure_datetime, s.arrival_datetime, b.bus_name, b.capacity;
```

---

## 4. Stored Procedures

### Procedure 1: `sp_search_buses`
Searches scheduled trips by origin, destination, and travel date, calculating real-time availability.
```sql
CREATE PROCEDURE sp_search_buses(
    IN p_source VARCHAR(100),
    IN p_destination VARCHAR(100),
    IN p_travel_date DATE
)
BEGIN
    SELECT 
        s.schedule_id,
        r.route_id,
        r.source,
        r.destination,
        b.bus_id,
        b.bus_name,
        b.bus_type,
        b.capacity,
        s.departure_datetime,
        s.arrival_datetime,
        s.base_fare,
        s.schedule_status,
        COUNT(CASE WHEN ss.seat_status = 'AVAILABLE' THEN 1 END) AS available_seats
    FROM schedules s
    JOIN routes r ON s.route_id = r.route_id
    JOIN buses b ON s.bus_id = b.bus_id
    LEFT JOIN schedule_seats ss ON s.schedule_id = ss.schedule_id
    WHERE LOWER(TRIM(r.source)) = LOWER(TRIM(p_source))
      AND LOWER(TRIM(r.destination)) = LOWER(TRIM(p_destination))
      AND DATE(s.departure_datetime) = p_travel_date
      AND s.schedule_status IN ('SCHEDULED', 'BOARDING')
    GROUP BY s.schedule_id, r.route_id, r.source, r.destination, b.bus_id, b.bus_name, b.bus_type, b.capacity, s.departure_datetime, s.arrival_datetime, s.base_fare, s.schedule_status;
END;
```

### Procedure 2: `sp_book_seat`
Atomically allocates an available seat, creates the booking, records payment, and commits the transaction using row-level locking.
- **Parameters**: `p_passenger_id`, `p_schedule_id`, `p_seat_number`, `p_payment_method`, `p_amount`, `OUT p_booking_id`, `OUT p_booking_ref`, `OUT p_status_code`, `OUT p_status_message`.
- **Locking**: `SELECT ... FOR UPDATE` on `schedule_seats` row.
- **Transaction Flow**: Check seat availability -> Update `schedule_seats` to `BOOKED` -> Insert `bookings` -> Insert `payments` -> Log Audit -> `COMMIT`.

### Procedure 3: `sp_cancel_booking`
Calculates refund amount based on time until departure (100% if >24h, 75% if 12-24h, 50% if <12h), updates booking status, releases seat inventory, logs refund, and automatically allocates the released seat to the next waitlisted passenger if the trip was full.

### Procedure 4: `sp_process_waitlist`
Evaluates the FIFO waitlist queue for a schedule and allocates the newly released seat to the passenger with `queue_position = 1`.

### Procedure 5: `sp_generate_revenue_report`
Produces aggregated financial KPIs, total gross revenue, refunds, net profit, and average trip load factor for a given date range.

---

## 5. Triggers

### 1. `trg_after_schedule_insert`
Generates authoritative seat inventory in `schedule_seats` (1 through `bus.capacity`) upon schedule creation.

### 2. `trg_audit_booking_insert` & `trg_audit_booking_update`
Captures all booking creations, status transitions, and cancellations into `audit_logs`.

