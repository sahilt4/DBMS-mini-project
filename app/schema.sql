-- =====================================================================
-- Smart Bus Reservation System - Relational Database Schema
-- DBMS Mini Project
-- =====================================================================

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------
-- Table 1: users
-- Stores authentication credentials and role-based access information.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'passenger')),
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- ---------------------------------------------------------------------
-- Table 2: routes
-- Stores bus routes from source to destination with distance.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS routes (
    route_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    destination TEXT NOT NULL,
    distance_km REAL NOT NULL CHECK(distance_km > 0),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1)),
    CONSTRAINT check_source_dest_diff CHECK (trim(lower(source)) <> trim(lower(destination)))
);

-- ---------------------------------------------------------------------
-- Table 3: buses
-- Stores physical bus fleet inventory, seat capacity and type.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS buses (
    bus_id INTEGER PRIMARY KEY AUTOINCREMENT,
    bus_number TEXT NOT NULL UNIQUE COLLATE NOCASE,
    bus_name TEXT NOT NULL,
    bus_type TEXT NOT NULL CHECK(bus_type IN ('AC Sleeper', 'Non-AC Sleeper', 'AC Seater', 'Non-AC Seater', 'Volvo Multi-Axle')),
    total_seats INTEGER NOT NULL CHECK(total_seats > 0 AND total_seats <= 60),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1))
);

-- ---------------------------------------------------------------------
-- Table 4: schedules
-- Maps buses to routes with specific travel dates, timings, and fares.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS schedules (
    schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
    bus_id INTEGER NOT NULL REFERENCES buses(bus_id) ON DELETE RESTRICT,
    route_id INTEGER NOT NULL REFERENCES routes(route_id) ON DELETE RESTRICT,
    travel_date TEXT NOT NULL,       -- Format: YYYY-MM-DD
    departure_time TEXT NOT NULL,    -- Format: HH:MM (24-hour)
    arrival_time TEXT NOT NULL,      -- Format: HH:MM (24-hour)
    fare REAL NOT NULL CHECK(fare >= 0),
    status TEXT NOT NULL DEFAULT 'SCHEDULED' CHECK(status IN ('SCHEDULED', 'COMPLETED', 'CANCELLED')),
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- ---------------------------------------------------------------------
-- Table 5: passengers
-- Stores traveler profiles linked optionally to registered user accounts.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS passengers (
    passenger_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    full_name TEXT NOT NULL,
    age INTEGER NOT NULL CHECK(age > 0 AND age <= 120),
    gender TEXT CHECK(gender IN ('Male', 'Female', 'Other')),
    phone TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- ---------------------------------------------------------------------
-- Table 6: bookings
-- Records individual seat reservations, references, and statuses.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bookings (
    booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_reference TEXT NOT NULL UNIQUE COLLATE NOCASE,
    schedule_id INTEGER NOT NULL REFERENCES schedules(schedule_id) ON DELETE RESTRICT,
    passenger_id INTEGER NOT NULL REFERENCES passengers(passenger_id) ON DELETE RESTRICT,
    seat_number INTEGER NOT NULL CHECK(seat_number > 0),
    booking_date TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    amount REAL NOT NULL CHECK(amount >= 0),
    status TEXT NOT NULL DEFAULT 'CONFIRMED' CHECK(status IN ('CONFIRMED', 'CANCELLED')),
    cancellation_date TEXT
);

-- ---------------------------------------------------------------------
-- Table 7: payments
-- Simulated financial ledger records linked to bookings.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS payments (
    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL REFERENCES bookings(booking_id) ON DELETE CASCADE,
    amount REAL NOT NULL CHECK(amount >= 0),
    payment_method TEXT NOT NULL CHECK(payment_method IN ('UPI', 'Credit Card', 'Debit Card', 'Net Banking', 'Cash')),
    payment_status TEXT NOT NULL CHECK(payment_status IN ('PAID', 'REFUND_PENDING', 'REFUNDED')),
    payment_date TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- =====================================================================
-- INDEXES FOR INTEGRITY AND QUERY PERFORMANCE
-- =====================================================================

-- Partial unique index: A seat can only have ONE CONFIRMED booking per schedule.
-- When a booking is CANCELLED, this index allows the seat to be re-booked while
-- preserving historical booking records without deletion.
CREATE UNIQUE INDEX IF NOT EXISTS idx_bookings_active_seat
    ON bookings (schedule_id, seat_number)
    WHERE status = 'CONFIRMED';

-- High-performance query indexes
CREATE INDEX IF NOT EXISTS idx_schedules_travel_date ON schedules(travel_date);
CREATE INDEX IF NOT EXISTS idx_schedules_bus_date ON schedules(bus_id, travel_date);
CREATE INDEX IF NOT EXISTS idx_schedules_route ON schedules(route_id);
CREATE INDEX IF NOT EXISTS idx_bookings_schedule ON bookings(schedule_id);
CREATE INDEX IF NOT EXISTS idx_bookings_passenger ON bookings(passenger_id);
CREATE INDEX IF NOT EXISTS idx_bookings_ref ON bookings(booking_reference);
CREATE INDEX IF NOT EXISTS idx_passengers_user ON passengers(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_booking ON payments(booking_id);
