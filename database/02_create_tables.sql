-- ============================================================================
-- BUS RESERVATION & MANAGEMENT SYSTEM (BRMS)
-- Script 02: Table Definitions (13 Entities + Audit Logs)
-- Target Database: MySQL 8.x
-- Storage Engine: InnoDB
-- ============================================================================

USE brms_db;

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS ticket_checkins;
DROP TABLE IF EXISTS refunds;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS bookings;
DROP TABLE IF EXISTS waitlist;
DROP TABLE IF EXISTS schedule_seats;
DROP TABLE IF EXISTS schedules;
DROP TABLE IF EXISTS route_stops;
DROP TABLE IF EXISTS bus_stops;
DROP TABLE IF EXISTS buses;
DROP TABLE IF EXISTS routes;
DROP TABLE IF EXISTS passengers;
DROP TABLE IF EXISTS users;

SET FOREIGN_KEY_CHECKS = 1;

-- ----------------------------------------------------------------------------
-- 1. USERS: User credentials and RBAC roles (ADMIN, PASSENGER, CONDUCTOR)
-- ----------------------------------------------------------------------------
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('ADMIN', 'PASSENGER', 'CONDUCTOR') NOT NULL,
    phone VARCHAR(20) NULL,
    account_status ENUM('ACTIVE', 'SUSPENDED', 'INACTIVE') NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 2. PASSENGERS: Traveler profiles linked to registered accounts
-- ----------------------------------------------------------------------------
CREATE TABLE passengers (
    passenger_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    passenger_name VARCHAR(100) NOT NULL,
    age INT NOT NULL,
    gender ENUM('Male', 'Female', 'Other') NOT NULL,
    phone VARCHAR(20) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_passenger_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL,
    CONSTRAINT chk_passenger_age CHECK (age > 0 AND age <= 120)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 3. ROUTES: Origin to destination master pairs
-- ----------------------------------------------------------------------------
CREATE TABLE routes (
    route_id INT AUTO_INCREMENT PRIMARY KEY,
    source VARCHAR(100) NOT NULL,
    destination VARCHAR(100) NOT NULL,
    distance DECIMAL(7, 2) NOT NULL,
    estimated_duration INT NOT NULL COMMENT 'Duration in minutes',
    route_status ENUM('ACTIVE', 'INACTIVE') NOT NULL DEFAULT 'ACTIVE',
    CONSTRAINT chk_route_distance CHECK (distance > 0),
    CONSTRAINT chk_route_duration CHECK (estimated_duration > 0),
    CONSTRAINT chk_route_endpoints CHECK (LOWER(TRIM(source)) <> LOWER(TRIM(destination)))
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 4. BUS_STOPS: Catalog of physical bus boarding/dropping locations
-- ----------------------------------------------------------------------------
CREATE TABLE bus_stops (
    stop_id INT AUTO_INCREMENT PRIMARY KEY,
    stop_name VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    address VARCHAR(255) NULL
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 5. ROUTE_STOPS: Sequence of intermediate stops along a route
-- ----------------------------------------------------------------------------
CREATE TABLE route_stops (
    route_stop_id INT AUTO_INCREMENT PRIMARY KEY,
    route_id INT NOT NULL,
    stop_id INT NOT NULL,
    stop_sequence INT NOT NULL,
    distance_from_origin DECIMAL(7, 2) NOT NULL DEFAULT 0.00,
    arrival_offset_minutes INT NOT NULL DEFAULT 0,
    CONSTRAINT fk_rs_route FOREIGN KEY (route_id) REFERENCES routes(route_id) ON DELETE CASCADE,
    CONSTRAINT fk_rs_stop FOREIGN KEY (stop_id) REFERENCES bus_stops(stop_id) ON DELETE RESTRICT,
    CONSTRAINT uq_route_stop_seq UNIQUE (route_id, stop_sequence),
    CONSTRAINT chk_stop_seq CHECK (stop_sequence > 0),
    CONSTRAINT chk_offset_min CHECK (arrival_offset_minutes >= 0)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 6. BUSES: Physical bus fleet inventory
-- ----------------------------------------------------------------------------
CREATE TABLE buses (
    bus_id INT AUTO_INCREMENT PRIMARY KEY,
    registration_number VARCHAR(30) NOT NULL UNIQUE,
    bus_name VARCHAR(100) NOT NULL,
    bus_type ENUM('AC Sleeper', 'Non-AC Sleeper', 'AC Seater', 'Non-AC Seater', 'Volvo Multi-Axle') NOT NULL,
    capacity INT NOT NULL,
    operational_status ENUM('ACTIVE', 'MAINTENANCE', 'DECOMMISSIONED') NOT NULL DEFAULT 'ACTIVE',
    CONSTRAINT chk_bus_capacity CHECK (capacity > 0 AND capacity <= 60)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 7. SCHEDULES: Assigned trips mapping a bus to a route on specific dates/times
-- ----------------------------------------------------------------------------
CREATE TABLE schedules (
    schedule_id INT AUTO_INCREMENT PRIMARY KEY,
    bus_id INT NOT NULL,
    route_id INT NOT NULL,
    departure_datetime DATETIME NOT NULL,
    arrival_datetime DATETIME NOT NULL,
    base_fare DECIMAL(8, 2) NOT NULL,
    schedule_status ENUM('SCHEDULED', 'IN_TRANSIT', 'COMPLETED', 'CANCELLED') NOT NULL DEFAULT 'SCHEDULED',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_sched_bus FOREIGN KEY (bus_id) REFERENCES buses(bus_id) ON DELETE RESTRICT,
    CONSTRAINT fk_sched_route FOREIGN KEY (route_id) REFERENCES routes(route_id) ON DELETE RESTRICT,
    CONSTRAINT chk_sched_fare CHECK (base_fare >= 0),
    CONSTRAINT chk_sched_times CHECK (arrival_datetime > departure_datetime)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 8. SCHEDULE_SEATS: Authoritative per-schedule seat availability inventory
-- ----------------------------------------------------------------------------
CREATE TABLE schedule_seats (
    schedule_seat_id INT AUTO_INCREMENT PRIMARY KEY,
    schedule_id INT NOT NULL,
    seat_number INT NOT NULL,
    seat_type ENUM('WINDOW', 'AISLE', 'SLEEPER_LOWER', 'SLEEPER_UPPER') NOT NULL DEFAULT 'WINDOW',
    seat_status ENUM('AVAILABLE', 'BOOKED', 'BLOCKED') NOT NULL DEFAULT 'AVAILABLE',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_ss_schedule FOREIGN KEY (schedule_id) REFERENCES schedules(schedule_id) ON DELETE CASCADE,
    CONSTRAINT uq_sched_seat UNIQUE (schedule_id, seat_number),
    CONSTRAINT chk_seat_num CHECK (seat_number > 0)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 9. WAITLIST: Queue for overbooked schedules with priority allocation
-- ----------------------------------------------------------------------------
CREATE TABLE waitlist (
    waitlist_id INT AUTO_INCREMENT PRIMARY KEY,
    passenger_id INT NOT NULL,
    schedule_id INT NOT NULL,
    preferred_seat_type VARCHAR(30) DEFAULT 'ANY',
    queue_position INT NOT NULL,
    waitlist_status ENUM('WAITING', 'ALLOCATED', 'EXPIRED', 'CANCELLED') NOT NULL DEFAULT 'WAITING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_wl_passenger FOREIGN KEY (passenger_id) REFERENCES passengers(passenger_id) ON DELETE RESTRICT,
    CONSTRAINT fk_wl_schedule FOREIGN KEY (schedule_id) REFERENCES schedules(schedule_id) ON DELETE CASCADE,
    CONSTRAINT uq_wl_passenger_sched UNIQUE (passenger_id, schedule_id),
    CONSTRAINT chk_wl_pos CHECK (queue_position > 0)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 10. BOOKINGS: Confirmed seat reservations and references
-- ----------------------------------------------------------------------------
CREATE TABLE bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    booking_reference VARCHAR(32) NOT NULL UNIQUE,
    passenger_id INT NOT NULL,
    schedule_id INT NOT NULL,
    seat_number INT NOT NULL,
    boarding_stop_id INT NULL,
    dropping_stop_id INT NULL,
    booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(8, 2) NOT NULL,
    booking_status ENUM('CONFIRMED', 'CANCELLED', 'CHECKED_IN') NOT NULL DEFAULT 'CONFIRMED',
    cancellation_reason VARCHAR(255) NULL,
    cancelled_at DATETIME NULL,
    CONSTRAINT fk_bk_passenger FOREIGN KEY (passenger_id) REFERENCES passengers(passenger_id) ON DELETE RESTRICT,
    CONSTRAINT fk_bk_schedule FOREIGN KEY (schedule_id) REFERENCES schedules(schedule_id) ON DELETE RESTRICT,
    CONSTRAINT fk_bk_bstop FOREIGN KEY (boarding_stop_id) REFERENCES bus_stops(stop_id) ON DELETE SET NULL,
    CONSTRAINT fk_bk_dstop FOREIGN KEY (dropping_stop_id) REFERENCES bus_stops(stop_id) ON DELETE SET NULL,
    CONSTRAINT chk_bk_seat CHECK (seat_number > 0),
    CONSTRAINT chk_bk_amount CHECK (total_amount >= 0)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 11. PAYMENTS: Financial ledger tracking transactions per booking
-- ----------------------------------------------------------------------------
CREATE TABLE payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL,
    amount DECIMAL(8, 2) NOT NULL,
    payment_method ENUM('UPI', 'Credit Card', 'Debit Card', 'Net Banking', 'Cash') NOT NULL,
    transaction_reference VARCHAR(64) NOT NULL UNIQUE,
    payment_status ENUM('PAID', 'REFUND_PENDING', 'REFUNDED', 'FAILED') NOT NULL DEFAULT 'PAID',
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_pmt_booking FOREIGN KEY (booking_id) REFERENCES bookings(booking_id) ON DELETE RESTRICT,
    CONSTRAINT chk_pmt_amount CHECK (amount >= 0)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 12. REFUNDS: Records of automated cancellation refunds
-- ----------------------------------------------------------------------------
CREATE TABLE refunds (
    refund_id INT AUTO_INCREMENT PRIMARY KEY,
    payment_id INT NOT NULL,
    booking_id INT NOT NULL,
    refund_amount DECIMAL(8, 2) NOT NULL,
    refund_reason VARCHAR(255) NOT NULL,
    refund_status ENUM('PROCESSED', 'PENDING', 'REJECTED') NOT NULL DEFAULT 'PROCESSED',
    refund_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_ref_payment FOREIGN KEY (payment_id) REFERENCES payments(payment_id) ON DELETE RESTRICT,
    CONSTRAINT fk_ref_booking FOREIGN KEY (booking_id) REFERENCES bookings(booking_id) ON DELETE RESTRICT,
    CONSTRAINT chk_ref_amount CHECK (refund_amount >= 0)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 13. TICKET_CHECKINS: Conductor digital QR verification ledger
-- ----------------------------------------------------------------------------
CREATE TABLE ticket_checkins (
    checkin_id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL UNIQUE,
    conductor_id INT NOT NULL,
    checkin_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    checkin_status ENUM('VERIFIED', 'FLAGGED', 'ALREADY_CHECKED_IN') NOT NULL DEFAULT 'VERIFIED',
    boarding_stop_id INT NULL,
    CONSTRAINT fk_chk_booking FOREIGN KEY (booking_id) REFERENCES bookings(booking_id) ON DELETE RESTRICT,
    CONSTRAINT fk_chk_conductor FOREIGN KEY (conductor_id) REFERENCES users(user_id) ON DELETE RESTRICT,
    CONSTRAINT fk_chk_stop FOREIGN KEY (boarding_stop_id) REFERENCES bus_stops(stop_id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 14. AUDIT_LOGS: System audit trail for critical transactions and mutations
-- ----------------------------------------------------------------------------
CREATE TABLE audit_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    action_type VARCHAR(50) NOT NULL,
    table_name VARCHAR(50) NOT NULL,
    record_id VARCHAR(50) NOT NULL,
    changed_by VARCHAR(100) NULL,
    old_values JSON NULL,
    new_values JSON NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;
