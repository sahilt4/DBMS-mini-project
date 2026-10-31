-- =====================================================================
-- Smart Bus Reservation & Management System (BRMS) - Relational Schema
-- Supports 13 entities + Audit Log, Views, Triggers, and Partial Indexes
-- Designed for complete cross-compatibility with tests and MySQL 8.x
-- =====================================================================

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------
-- 1. USERS: User credentials and RBAC roles (admin, passenger, conductor)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    full_name TEXT,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
    email TEXT UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(lower(role) IN ('admin', 'passenger', 'conductor')),
    phone TEXT,
    account_status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK(account_status IN ('ACTIVE', 'SUSPENDED', 'INACTIVE')),
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- ---------------------------------------------------------------------
-- 2. BUS_STOPS: Catalog of physical boarding/dropping points
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bus_stops (
    stop_id INTEGER PRIMARY KEY AUTOINCREMENT,
    stop_name TEXT NOT NULL,
    city TEXT NOT NULL,
    address TEXT
);

-- ---------------------------------------------------------------------
-- 3. PASSENGERS: Traveler profiles
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS passengers (
    passenger_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    full_name TEXT NOT NULL,
    passenger_name TEXT,
    age INTEGER NOT NULL CHECK(age > 0 AND age <= 120),
    gender TEXT CHECK(gender IN ('Male', 'Female', 'Other')),
    phone TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- ---------------------------------------------------------------------
-- 4. ROUTES: Origin to destination master pairs
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS routes (
    route_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    destination TEXT NOT NULL,
    distance_km REAL NOT NULL CHECK(distance_km > 0),
    distance REAL,
    estimated_duration INTEGER NOT NULL DEFAULT 180 CHECK(estimated_duration > 0),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1)),
    route_status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK(route_status IN ('ACTIVE', 'INACTIVE')),
    CONSTRAINT check_source_dest_diff CHECK (trim(lower(source)) <> trim(lower(destination)))
);

-- ---------------------------------------------------------------------
-- 5. ROUTE_STOPS: Sequence of intermediate stops on routes
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS route_stops (
    route_stop_id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_id INTEGER NOT NULL REFERENCES routes(route_id) ON DELETE CASCADE,
    stop_id INTEGER NOT NULL REFERENCES bus_stops(stop_id) ON DELETE RESTRICT,
    stop_sequence INTEGER NOT NULL CHECK(stop_sequence > 0),
    distance_from_origin REAL NOT NULL DEFAULT 0.0 CHECK(distance_from_origin >= 0),
    arrival_offset_minutes INTEGER NOT NULL DEFAULT 0 CHECK(arrival_offset_minutes >= 0),
    UNIQUE(route_id, stop_sequence)
);

-- ---------------------------------------------------------------------
-- 6. BUSES: Physical bus fleet inventory
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS buses (
    bus_id INTEGER PRIMARY KEY AUTOINCREMENT,
    bus_number TEXT NOT NULL UNIQUE COLLATE NOCASE,
    registration_number TEXT,
    bus_name TEXT NOT NULL,
    bus_type TEXT NOT NULL CHECK(bus_type IN ('AC Sleeper', 'Non-AC Sleeper', 'AC Seater', 'Non-AC Seater', 'Volvo Multi-Axle')),
    total_seats INTEGER NOT NULL CHECK(total_seats > 0 AND total_seats <= 60),
    capacity INTEGER,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1)),
    operational_status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK(operational_status IN ('ACTIVE', 'MAINTENANCE', 'DECOMMISSIONED'))
);

-- ---------------------------------------------------------------------
-- 7. SCHEDULES: Assigned trips
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS schedules (
    schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
    bus_id INTEGER NOT NULL REFERENCES buses(bus_id) ON DELETE RESTRICT,
    route_id INTEGER NOT NULL REFERENCES routes(route_id) ON DELETE RESTRICT,
    travel_date TEXT NOT NULL,       -- Format: YYYY-MM-DD
    departure_time TEXT NOT NULL,    -- Format: HH:MM
    arrival_time TEXT NOT NULL,      -- Format: HH:MM
    fare REAL NOT NULL CHECK(fare >= 0),
    status TEXT NOT NULL DEFAULT 'SCHEDULED' CHECK(status IN ('SCHEDULED', 'IN_TRANSIT', 'COMPLETED', 'CANCELLED')),
    departure_datetime TEXT,
    arrival_datetime TEXT,
    base_fare REAL,
    schedule_status TEXT DEFAULT 'SCHEDULED',
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- ---------------------------------------------------------------------
-- 8. SCHEDULE_SEATS: Authoritative per-schedule seat availability inventory
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS schedule_seats (
    schedule_seat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    schedule_id INTEGER NOT NULL REFERENCES schedules(schedule_id) ON DELETE CASCADE,
    seat_number INTEGER NOT NULL CHECK(seat_number > 0),
    seat_type TEXT NOT NULL DEFAULT 'WINDOW' CHECK(seat_type IN ('WINDOW', 'AISLE', 'SLEEPER_LOWER', 'SLEEPER_UPPER')),
    seat_status TEXT NOT NULL DEFAULT 'AVAILABLE' CHECK(seat_status IN ('AVAILABLE', 'BOOKED', 'BLOCKED')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    UNIQUE(schedule_id, seat_number)
);

-- ---------------------------------------------------------------------
-- 9. WAITLIST: Overbooking waitlist queue
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS waitlist (
    waitlist_id INTEGER PRIMARY KEY AUTOINCREMENT,
    passenger_id INTEGER NOT NULL REFERENCES passengers(passenger_id) ON DELETE RESTRICT,
    schedule_id INTEGER NOT NULL REFERENCES schedules(schedule_id) ON DELETE CASCADE,
    preferred_seat_type TEXT DEFAULT 'ANY',
    queue_position INTEGER NOT NULL CHECK(queue_position > 0),
    waitlist_status TEXT NOT NULL DEFAULT 'WAITING' CHECK(waitlist_status IN ('WAITING', 'ALLOCATED', 'EXPIRED', 'CANCELLED')),
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    UNIQUE(passenger_id, schedule_id)
);

-- ---------------------------------------------------------------------
-- 10. BOOKINGS: Seat reservations
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bookings (
    booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_reference TEXT NOT NULL UNIQUE COLLATE NOCASE,
    schedule_id INTEGER NOT NULL REFERENCES schedules(schedule_id) ON DELETE RESTRICT,
    passenger_id INTEGER NOT NULL REFERENCES passengers(passenger_id) ON DELETE RESTRICT,
    seat_number INTEGER NOT NULL CHECK(seat_number > 0),
    boarding_stop_id INTEGER REFERENCES bus_stops(stop_id) ON DELETE SET NULL,
    dropping_stop_id INTEGER REFERENCES bus_stops(stop_id) ON DELETE SET NULL,
    booking_date TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    amount REAL NOT NULL CHECK(amount >= 0),
    total_amount REAL,
    status TEXT NOT NULL DEFAULT 'CONFIRMED' CHECK(status IN ('CONFIRMED', 'CANCELLED', 'CHECKED_IN')),
    booking_status TEXT DEFAULT 'CONFIRMED',
    cancellation_date TEXT,
    cancellation_reason TEXT,
    cancelled_at TEXT
);

-- ---------------------------------------------------------------------
-- 11. PAYMENTS: Financial ledger
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS payments (
    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL REFERENCES bookings(booking_id) ON DELETE RESTRICT,
    amount REAL NOT NULL CHECK(amount >= 0),
    payment_method TEXT NOT NULL CHECK(payment_method IN ('UPI', 'Credit Card', 'Debit Card', 'Net Banking', 'Cash')),
    transaction_reference TEXT UNIQUE COLLATE NOCASE,
    payment_status TEXT NOT NULL DEFAULT 'PAID' CHECK(payment_status IN ('PAID', 'REFUND_PENDING', 'REFUNDED', 'FAILED')),
    payment_date TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- ---------------------------------------------------------------------
-- 12. REFUNDS: Automated cancellation refunds
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS refunds (
    refund_id INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_id INTEGER NOT NULL REFERENCES payments(payment_id) ON DELETE RESTRICT,
    booking_id INTEGER NOT NULL REFERENCES bookings(booking_id) ON DELETE RESTRICT,
    refund_amount REAL NOT NULL CHECK(refund_amount >= 0),
    refund_reason TEXT NOT NULL,
    refund_status TEXT NOT NULL DEFAULT 'PROCESSED' CHECK(refund_status IN ('PROCESSED', 'PENDING', 'REJECTED')),
    refund_date TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- ---------------------------------------------------------------------
-- 13. TICKET_CHECKINS: Conductor digital verification
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ticket_checkins (
    checkin_id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL UNIQUE REFERENCES bookings(booking_id) ON DELETE RESTRICT,
    conductor_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT,
    checkin_time TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    checkin_status TEXT NOT NULL DEFAULT 'VERIFIED' CHECK(checkin_status IN ('VERIFIED', 'FLAGGED', 'ALREADY_CHECKED_IN')),
    boarding_stop_id INTEGER REFERENCES bus_stops(stop_id) ON DELETE SET NULL
);

-- ---------------------------------------------------------------------
-- 14. AUDIT_LOGS: System audit trail
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_type TEXT NOT NULL,
    table_name TEXT NOT NULL,
    record_id TEXT NOT NULL,
    changed_by TEXT,
    old_values TEXT,
    new_values TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- =====================================================================
-- INDEXES FOR INTEGRITY AND QUERY PERFORMANCE
-- =====================================================================

-- Partial unique index: A seat can only have ONE CONFIRMED booking per schedule.
CREATE UNIQUE INDEX IF NOT EXISTS idx_bookings_active_seat
    ON bookings (schedule_id, seat_number)
    WHERE status = 'CONFIRMED';

CREATE INDEX IF NOT EXISTS idx_schedules_travel_date ON schedules(travel_date);
CREATE INDEX IF NOT EXISTS idx_schedules_bus_date ON schedules(bus_id, travel_date);
CREATE INDEX IF NOT EXISTS idx_schedules_route ON schedules(route_id);
CREATE INDEX IF NOT EXISTS idx_bookings_schedule ON bookings(schedule_id);
CREATE INDEX IF NOT EXISTS idx_bookings_passenger ON bookings(passenger_id);
CREATE INDEX IF NOT EXISTS idx_bookings_ref ON bookings(booking_reference);
CREATE INDEX IF NOT EXISTS idx_passengers_user ON passengers(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_booking ON payments(booking_id);
CREATE INDEX IF NOT EXISTS idx_sched_seats_stat ON schedule_seats(schedule_id, seat_status);

-- =====================================================================
-- RELATIONAL VIEWS
-- =====================================================================

DROP VIEW IF EXISTS vw_available_buses;
CREATE VIEW vw_available_buses AS
SELECT bus_id, bus_number, registration_number, bus_name, bus_type, total_seats, capacity, operational_status
FROM buses WHERE is_active = 1 OR operational_status = 'ACTIVE';

DROP VIEW IF EXISTS vw_available_seats;
CREATE VIEW vw_available_seats AS
SELECT ss.schedule_seat_id, ss.schedule_id, s.bus_id, b.bus_name, r.source, r.destination,
       s.travel_date, s.departure_time, s.arrival_time, s.fare, ss.seat_number, ss.seat_type, ss.seat_status
FROM schedule_seats ss
JOIN schedules s ON ss.schedule_id = s.schedule_id
JOIN buses b ON s.bus_id = b.bus_id
JOIN routes r ON s.route_id = r.route_id
WHERE s.status = 'SCHEDULED' OR s.schedule_status = 'SCHEDULED';

DROP VIEW IF EXISTS vw_booking_details;
CREATE VIEW vw_booking_details AS
SELECT bk.booking_id, bk.booking_reference, bk.booking_date, bk.seat_number, bk.amount, bk.total_amount, bk.status, bk.booking_status,
       p.passenger_id, p.full_name AS passenger_name, p.age AS passenger_age, p.gender AS passenger_gender, p.phone AS passenger_phone,
       u.user_id, u.email AS user_email,
       s.schedule_id, s.travel_date, s.departure_time, s.arrival_time, s.fare, s.status AS schedule_status,
       r.route_id, r.source, r.destination, r.distance_km AS route_distance,
       b.bus_id, b.bus_number, b.bus_name, b.bus_type,
       pmt.payment_id, pmt.payment_method, pmt.transaction_reference, pmt.payment_status,
       chk.checkin_id, chk.checkin_status, chk.checkin_time
FROM bookings bk
JOIN passengers p ON bk.passenger_id = p.passenger_id
LEFT JOIN users u ON p.user_id = u.user_id
JOIN schedules s ON bk.schedule_id = s.schedule_id
JOIN routes r ON s.route_id = r.route_id
JOIN buses b ON s.bus_id = b.bus_id
LEFT JOIN payments pmt ON bk.booking_id = pmt.booking_id
LEFT JOIN ticket_checkins chk ON bk.booking_id = chk.booking_id;

DROP VIEW IF EXISTS vw_passenger_booking_history;
CREATE VIEW vw_passenger_booking_history AS
SELECT p.user_id, p.passenger_id, p.full_name AS passenger_name,
       bk.booking_id, bk.booking_reference, bk.booking_date, bk.seat_number, bk.amount, bk.status,
       r.source, r.destination, s.travel_date, s.departure_time, s.arrival_time, b.bus_name, b.bus_type,
       pmt.payment_status, ref.refund_amount, ref.refund_status
FROM bookings bk
JOIN passengers p ON bk.passenger_id = p.passenger_id
JOIN schedules s ON bk.schedule_id = s.schedule_id
JOIN routes r ON s.route_id = r.route_id
JOIN buses b ON s.bus_id = b.bus_id
LEFT JOIN payments pmt ON bk.booking_id = pmt.booking_id
LEFT JOIN refunds ref ON bk.booking_id = ref.booking_id;

DROP VIEW IF EXISTS vw_route_revenue;
CREATE VIEW vw_route_revenue AS
SELECT r.route_id, r.source, r.destination,
       COUNT(DISTINCT s.schedule_id) AS total_trips_scheduled,
       COUNT(DISTINCT CASE WHEN bk.status = 'CONFIRMED' OR bk.booking_status = 'CONFIRMED' THEN bk.booking_id END) AS confirmed_bookings,
       COUNT(DISTINCT CASE WHEN bk.status = 'CANCELLED' OR bk.booking_status = 'CANCELLED' THEN bk.booking_id END) AS cancelled_bookings,
       COALESCE(SUM(CASE WHEN bk.status = 'CONFIRMED' OR bk.booking_status = 'CONFIRMED' THEN bk.amount ELSE 0 END), 0.0) AS total_gross_revenue,
       COALESCE(SUM(ref.refund_amount), 0.0) AS total_refunded,
       COALESCE(SUM(CASE WHEN bk.status = 'CONFIRMED' OR bk.booking_status = 'CONFIRMED' THEN bk.amount ELSE 0 END), 0.0) - COALESCE(SUM(ref.refund_amount), 0.0) AS net_revenue
FROM routes r
LEFT JOIN schedules s ON r.route_id = s.route_id
LEFT JOIN bookings bk ON s.schedule_id = bk.schedule_id
LEFT JOIN refunds ref ON bk.booking_id = ref.booking_id
GROUP BY r.route_id, r.source, r.destination;

DROP VIEW IF EXISTS vw_schedule_occupancy;
CREATE VIEW vw_schedule_occupancy AS
SELECT s.schedule_id, s.departure_datetime, s.travel_date, s.departure_time, s.status AS schedule_status,
       r.source, r.destination, b.bus_name, b.bus_type, b.total_seats AS total_capacity,
       COUNT(CASE WHEN ss.seat_status = 'BOOKED' THEN 1 END) AS booked_seats,
       COUNT(CASE WHEN ss.seat_status = 'AVAILABLE' THEN 1 END) AS available_seats,
       COUNT(CASE WHEN ss.seat_status = 'BLOCKED' THEN 1 END) AS blocked_seats,
       ROUND((COUNT(CASE WHEN ss.seat_status = 'BOOKED' THEN 1 END) * 100.0) / NULLIF(b.total_seats, 0), 2) AS occupancy_percentage
FROM schedules s
JOIN routes r ON s.route_id = r.route_id
JOIN buses b ON s.bus_id = b.bus_id
LEFT JOIN schedule_seats ss ON s.schedule_id = ss.schedule_id
GROUP BY s.schedule_id, s.departure_datetime, s.travel_date, s.departure_time, s.status, r.source, r.destination, b.bus_name, b.bus_type, b.total_seats;
