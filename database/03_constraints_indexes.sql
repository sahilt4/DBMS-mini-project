-- ============================================================================
-- BUS RESERVATION & MANAGEMENT SYSTEM (BRMS)
-- Script 03: Constraints, Foreign Keys and Performance Indexes
-- Target Database: MySQL 8.x
-- ============================================================================

USE brms_db;

-- ----------------------------------------------------------------------------
-- PERFORMANCE & INTEGRITY INDEXES
-- ----------------------------------------------------------------------------

-- Schedules searching by route and departure timestamp
CREATE INDEX idx_schedules_search 
    ON schedules (route_id, departure_datetime, schedule_status);

-- Schedule overlap prevention and bus utilization queries
CREATE INDEX idx_schedules_bus_time 
    ON schedules (bus_id, departure_datetime, arrival_datetime);

-- Fast lookup for authoritative seat availability per trip
CREATE INDEX idx_schedule_seats_status 
    ON schedule_seats (schedule_id, seat_status);

-- Booking lookups by reference, passenger, and trip
CREATE INDEX idx_bookings_ref 
    ON bookings (booking_reference);

CREATE INDEX idx_bookings_passenger 
    ON bookings (passenger_id, booking_status);

CREATE INDEX idx_bookings_schedule_seat 
    ON bookings (schedule_id, seat_number, booking_status);

-- Priority queue queries for waitlisted passengers
CREATE INDEX idx_waitlist_queue 
    ON waitlist (schedule_id, queue_position, waitlist_status);

-- Payments and audit log tracking
CREATE INDEX idx_payments_booking_status 
    ON payments (booking_id, payment_status);

CREATE INDEX idx_audit_logs_table_record 
    ON audit_logs (table_name, record_id, created_at);

-- Conductor check-in timeline queries
CREATE INDEX idx_checkins_conductor_time 
    ON ticket_checkins (conductor_id, checkin_time);

