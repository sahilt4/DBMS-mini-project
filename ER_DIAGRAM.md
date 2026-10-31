# Entity-Relationship (ER) Diagram
## Bus Reservation and Management System (BRMS) | DBMS Mini Project

---

### 1. Conceptual Schema Overview

The **Bus Reservation and Management System (BRMS)** is architected around **13 core relational entities** plus a centralized system **Audit Log**, modeled in pure **3rd Normal Form (3NF)** / **BCNF** with strict referential integrity (`ON DELETE RESTRICT` / `ON DELETE CASCADE` where appropriate) and relational constraints.

```mermaid
erDiagram
    USERS ||--o| PASSENGERS : "has_profile"
    USERS ||--o{ BOOKINGS : "manages"
    USERS ||--o{ TICKET_CHECKINS : "scanned_by"
    USERS ||--o{ AUDIT_LOGS : "performed_by"

    PASSENGERS ||--o{ BOOKINGS : "books"
    PASSENGERS ||--o{ WAITLIST : "queues_in"

    BUSES ||--o{ SCHEDULES : "assigned_to"

    ROUTES ||--o{ SCHEDULES : "scheduled_for"
    ROUTES ||--o{ ROUTE_STOPS : "contains_stops"
    BUS_STOPS ||--o{ ROUTE_STOPS : "serviced_at"

    SCHEDULES ||--o{ SCHEDULE_SEATS : "allocates_inventory"
    SCHEDULES ||--o{ BOOKINGS : "has_reservations"
    SCHEDULES ||--o{ WAITLIST : "has_queue"

    BOOKINGS ||--o| PAYMENTS : "billed_under"
    BOOKINGS ||--o| REFUNDS : "refunded_under"
    BOOKINGS ||--o| TICKET_CHECKINS : "validated_by"
    PAYMENTS ||--o| REFUNDS : "reversed_through"

    USERS {
        int user_id PK
        string full_name
        string email UK
        string password_hash
        string role
        string phone
        string account_status
        timestamp created_at
    }

    PASSENGERS {
        int passenger_id PK
        int user_id FK
        string full_name
        int age
        string gender
        string phone
        timestamp created_at
    }

    BUSES {
        int bus_id PK
        string registration_number UK
        string bus_name
        string bus_type
        int capacity
        string operational_status
        timestamp created_at
    }

    ROUTES {
        int route_id PK
        string source
        string destination
        decimal distance
        int estimated_duration
        string route_status
        timestamp created_at
    }

    BUS_STOPS {
        int stop_id PK
        string stop_name
        string city
        string address
        timestamp created_at
    }

    ROUTE_STOPS {
        int route_stop_id PK
        int route_id FK
        int stop_id FK
        int stop_sequence
        decimal distance_from_origin
        int arrival_offset_minutes
    }

    SCHEDULES {
        int schedule_id PK
        int bus_id FK
        int route_id FK
        datetime departure_datetime
        datetime arrival_datetime
        decimal base_fare
        string schedule_status
        timestamp created_at
    }

    SCHEDULE_SEATS {
        int schedule_seat_id PK
        int schedule_id FK
        int seat_number
        string seat_status
        timestamp updated_at
    }

    BOOKINGS {
        int booking_id PK
        string booking_reference UK
        int passenger_id FK
        int schedule_id FK
        int seat_number
        datetime booking_date
        decimal total_amount
        string booking_status
        datetime cancellation_date
    }

    PAYMENTS {
        int payment_id PK
        int booking_id FK
        decimal amount
        string payment_method
        string transaction_reference UK
        string payment_status
        timestamp payment_date
    }

    REFUNDS {
        int refund_id PK
        int payment_id FK
        int booking_id FK
        decimal refund_amount
        string refund_reason
        string refund_status
        timestamp refund_date
    }

    WAITLIST {
        int waitlist_id PK
        int passenger_id FK
        int schedule_id FK
        string preferred_seat_type
        int queue_position
        string waitlist_status
        timestamp created_at
    }

    TICKET_CHECKINS {
        int checkin_id PK
        int booking_id FK
        datetime checkin_datetime
        int verified_by_user_id FK
        string checkin_method
        int boarding_stop_id FK
        string remarks
    }

    AUDIT_LOGS {
        int log_id PK
        int user_id FK
        string action
        string entity_name
        int entity_id
        text old_values
        text new_values
        timestamp created_at
    }
```

---

### 2. Entity Descriptions, Attributes, and Integrity Constraints

#### 1. `USERS`
- **Role**: Centralized identity and role-based authentication repository.
- **Primary Key**: `user_id` (INT AUTO_INCREMENT)
- **Alternate / Unique Key**: `email` (VARCHAR(150), UNIQUE)
- **Constraints**:
  - `role IN ('ADMIN', 'PASSENGER', 'CONDUCTOR')`
  - `account_status IN ('ACTIVE', 'SUSPENDED', 'DEACTIVATED')`
- **Cardinality**:
  - 1 : 0..1 with `PASSENGERS` (a user may have a passenger profile).
  - 1 : N with `TICKET_CHECKINS` (conductors record multiple ticket scans).
  - 1 : N with `AUDIT_LOGS` (users trigger audit actions).

#### 2. `PASSENGERS`
- **Role**: Profile details for travelers making reservations or joining waitlists.
- **Primary Key**: `passenger_id` (INT AUTO_INCREMENT)
- **Foreign Key**: `user_id -> USERS(user_id)` ON DELETE SET NULL
- **Constraints**:
  - `age >= 1 AND age <= 120`
  - `gender IN ('MALE', 'FEMALE', 'OTHER')`
- **Cardinality**:
  - 1 : N with `BOOKINGS` (a passenger makes multiple reservations).
  - 1 : N with `WAITLIST` (a passenger can waitlist on multiple trips).

#### 3. `BUSES`
- **Role**: Fleet assets operating on trips.
- **Primary Key**: `bus_id` (INT AUTO_INCREMENT)
- **Alternate / Unique Key**: `registration_number` (VARCHAR(20), UNIQUE)
- **Constraints**:
  - `capacity BETWEEN 10 AND 60`
  - `bus_type IN ('STANDARD', 'DELUXE', 'SLEEPER', 'AC_SEATER', 'VOLVO_MULTI_AXLE')`
  - `operational_status IN ('ACTIVE', 'MAINTENANCE', 'RETIRED')`
- **Cardinality**:
  - 1 : N with `SCHEDULES` (a bus operates many journey schedules).

#### 4. `ROUTES`
- **Role**: Journey corridors connecting origin and destination cities.
- **Primary Key**: `route_id` (INT AUTO_INCREMENT)
- **Constraints**:
  - `distance > 0`
  - `estimated_duration > 0`
  - `LOWER(TRIM(source)) <> LOWER(TRIM(destination))`
  - `route_status IN ('ACTIVE', 'INACTIVE')`
- **Cardinality**:
  - 1 : N with `SCHEDULES` (a route has many scheduled trips).
  - 1 : N with `ROUTE_STOPS` (a route contains ordered intermediate stops).

#### 5. `BUS_STOPS`
- **Role**: Physical stations, terminals, and pickup/drop points.
- **Primary Key**: `stop_id` (INT AUTO_INCREMENT)
- **Cardinality**:
  - 1 : N with `ROUTE_STOPS` (a bus stop can be part of multiple routes).
  - 1 : N with `TICKET_CHECKINS` (a stop serves as the boarding location).

#### 6. `ROUTE_STOPS` (Junction Entity)
- **Role**: Ordered sequence of stops along a route with distance and time offsets.
- **Primary Key**: `route_stop_id` (INT AUTO_INCREMENT)
- **Foreign Keys**:
  - `route_id -> ROUTES(route_id)` ON DELETE CASCADE
  - `stop_id -> BUS_STOPS(stop_id)` ON DELETE RESTRICT
- **Constraints**:
  - `UNIQUE (route_id, stop_sequence)` (strictly ordered sequence per route).
  - `UNIQUE (route_id, stop_id)` (prevents repeating the same stop within a route).
  - `stop_sequence >= 1`, `distance_from_origin >= 0`, `arrival_offset_minutes >= 0`.

#### 7. `SCHEDULES`
- **Role**: Concrete journey instances binding a bus and route to a specific departure/arrival time.
- **Primary Key**: `schedule_id` (INT AUTO_INCREMENT)
- **Foreign Keys**:
  - `bus_id -> BUSES(bus_id)` ON DELETE RESTRICT
  - `route_id -> ROUTES(route_id)` ON DELETE RESTRICT
- **Constraints**:
  - `arrival_datetime > departure_datetime`
  - `base_fare > 0`
  - `schedule_status IN ('SCHEDULED', 'BOARDING', 'IN_TRANSIT', 'COMPLETED', 'CANCELLED')`
- **Cardinality**:
  - 1 : N with `SCHEDULE_SEATS` (1 row per physical seat on the bus).
  - 1 : N with `BOOKINGS` (reservations booked on this schedule).
  - 1 : N with `WAITLIST` (passengers waiting for seat availability).

#### 8. `SCHEDULE_SEATS`
- **Role**: Authoritative real-time inventory of physical seat occupancy for each scheduled trip.
- **Primary Key**: `schedule_seat_id` (INT AUTO_INCREMENT)
- **Foreign Key**: `schedule_id -> SCHEDULES(schedule_id)` ON DELETE CASCADE
- **Constraints**:
  - `UNIQUE (schedule_id, seat_number)`
  - `seat_status IN ('AVAILABLE', 'BOOKED', 'BLOCKED')`
- **Concurrency Guarantee**: Provides explicit row-level locking via `SELECT ... FOR UPDATE` during booking transactions, completely preventing double-booking race conditions.

#### 9. `BOOKINGS`
- **Role**: Reservation transactions connecting a passenger to a schedule and seat.
- **Primary Key**: `booking_id` (INT AUTO_INCREMENT)
- **Alternate / Unique Key**: `booking_reference` (VARCHAR(30), UNIQUE, e.g. `BUS-20261031-A1B2`)
- **Foreign Keys**:
  - `passenger_id -> PASSENGERS(passenger_id)` ON DELETE RESTRICT
  - `schedule_id -> SCHEDULES(schedule_id)` ON DELETE RESTRICT
- **Constraints**:
  - `seat_number >= 1`
  - `total_amount >= 0`
  - `booking_status IN ('CONFIRMED', 'CANCELLED', 'CHECKED_IN', 'NO_SHOW')`
- **Partial Unique Index**:
  - `CREATE UNIQUE INDEX idx_bookings_active_seat ON bookings (schedule_id, seat_number) WHERE booking_status = 'CONFIRMED';`
  - Guarantees that active bookings cannot clash on the same seat while preserving cancelled bookings for historical reporting.

#### 10. `PAYMENTS`
- **Role**: Financial transaction ledger for customer payments.
- **Primary Key**: `payment_id` (INT AUTO_INCREMENT)
- **Alternate / Unique Key**: `transaction_reference` (VARCHAR(60), UNIQUE, e.g. `TXN-XXXXXXXX`)
- **Foreign Key**: `booking_id -> BOOKINGS(booking_id)` ON DELETE RESTRICT
- **Constraints**:
  - `amount >= 0`
  - `payment_method IN ('UPI', 'CREDIT_CARD', 'DEBIT_CARD', 'NET_BANKING', 'CASH')`
  - `payment_status IN ('PENDING', 'SUCCESS', 'FAILED', 'REFUNDED')`

#### 11. `REFUNDS`
- **Role**: Records cancellation penalties, refund percentages, and ledger reversals.
- **Primary Key**: `refund_id` (INT AUTO_INCREMENT)
- **Foreign Keys**:
  - `payment_id -> PAYMENTS(payment_id)` ON DELETE RESTRICT
  - `booking_id -> BOOKINGS(booking_id)` ON DELETE RESTRICT
- **Constraints**:
  - `refund_amount >= 0`
  - `refund_status IN ('PENDING', 'PROCESSED', 'FAILED')`

#### 12. `WAITLIST`
- **Role**: FIFO priority queue for passengers seeking seats on fully booked departures.
- **Primary Key**: `waitlist_id` (INT AUTO_INCREMENT)
- **Foreign Keys**:
  - `passenger_id -> PASSENGERS(passenger_id)` ON DELETE CASCADE
  - `schedule_id -> SCHEDULES(schedule_id)` ON DELETE CASCADE
- **Constraints**:
  - `queue_position >= 1`
  - `waitlist_status IN ('WAITING', 'ALLOCATED', 'EXPIRED', 'CANCELLED')`
  - `UNIQUE (passenger_id, schedule_id, waitlist_status)` where status = 'WAITING'.

#### 13. `TICKET_CHECKINS`
- **Role**: Onboard conductor verification ledger capturing QR scan timestamps and boarding status.
- **Primary Key**: `checkin_id` (INT AUTO_INCREMENT)
- **Foreign Keys**:
  - `booking_id -> BOOKINGS(booking_id)` ON DELETE RESTRICT
  - `verified_by_user_id -> USERS(user_id)` ON DELETE RESTRICT
  - `boarding_stop_id -> BUS_STOPS(stop_id)` ON DELETE SET NULL
- **Constraints**:
  - `checkin_method IN ('QR_SCAN', 'MANUAL')`
  - `UNIQUE (booking_id)` (prevents duplicate passenger check-ins on the same ticket).

#### 14. `AUDIT_LOGS`
- **Role**: Immutable system-wide change data capture (CDC) trail for security and regulatory compliance.
- **Primary Key**: `log_id` (INT AUTO_INCREMENT)
- **Foreign Key**: `user_id -> USERS(user_id)` ON DELETE SET NULL

---

### 3. Relationship Cardinality Matrix

| Parent Entity | Child Entity | Relationship Type | Cardinality | Referential Integrity Rule |
|---|---|---|---|---|
| `USERS` | `PASSENGERS` | Has profile | 1 : 0..1 | `ON DELETE SET NULL` |
| `USERS` | `TICKET_CHECKINS`| Scanned by | 1 : N | `ON DELETE RESTRICT` |
| `USERS` | `AUDIT_LOGS` | Performed by | 1 : N | `ON DELETE SET NULL` |
| `PASSENGERS` | `BOOKINGS` | Reserves | 1 : N | `ON DELETE RESTRICT` |
| `PASSENGERS` | `WAITLIST` | Queues in | 1 : N | `ON DELETE CASCADE` |
| `BUSES` | `SCHEDULES` | Operates on | 1 : N | `ON DELETE RESTRICT` |
| `ROUTES` | `SCHEDULES` | Scheduled for | 1 : N | `ON DELETE RESTRICT` |
| `ROUTES` | `ROUTE_STOPS` | Comprises | 1 : N | `ON DELETE CASCADE` |
| `BUS_STOPS` | `ROUTE_STOPS` | Serviced at | 1 : N | `ON DELETE RESTRICT` |
| `BUS_STOPS` | `TICKET_CHECKINS`| Boarded at | 1 : N | `ON DELETE SET NULL` |
| `SCHEDULES` | `SCHEDULE_SEATS`| Allocates | 1 : N | `ON DELETE CASCADE` |
| `SCHEDULES` | `BOOKINGS` | Booked for | 1 : N | `ON DELETE RESTRICT` |
| `SCHEDULES` | `WAITLIST` | Waitlisted for| 1 : N | `ON DELETE CASCADE` |
| `BOOKINGS` | `PAYMENTS` | Invoiced as | 1 : 1 | `ON DELETE RESTRICT` |
| `BOOKINGS` | `REFUNDS` | Refunded via | 1 : 0..1 | `ON DELETE RESTRICT` |
| `BOOKINGS` | `TICKET_CHECKINS`| Verified via | 1 : 0..1 | `ON DELETE RESTRICT` |
| `PAYMENTS` | `REFUNDS` | Reverses | 1 : 0..1 | `ON DELETE RESTRICT` |
