-- ============================================================================
-- BUS RESERVATION & MANAGEMENT SYSTEM (BRMS)
-- Script 04: Relational Views
-- Target Database: MySQL 8.x
-- ============================================================================

USE brms_db;

DROP VIEW IF EXISTS vw_schedule_occupancy;
DROP VIEW IF EXISTS vw_route_revenue;
DROP VIEW IF EXISTS vw_passenger_booking_history;
DROP VIEW IF EXISTS vw_booking_details;
DROP VIEW IF EXISTS vw_available_seats;
DROP VIEW IF EXISTS vw_available_buses;

-- ----------------------------------------------------------------------------
-- 1. vw_available_buses
-- Active fleet summary with operational capacity and status
-- ----------------------------------------------------------------------------
CREATE VIEW vw_available_buses AS
SELECT 
    b.bus_id,
    b.registration_number,
    b.bus_name,
    b.bus_type,
    b.capacity,
    b.operational_status
FROM buses b
WHERE b.operational_status = 'ACTIVE';

-- ----------------------------------------------------------------------------
-- 2. vw_available_seats
-- Real-time seat inventory per schedule showing available seats
-- ----------------------------------------------------------------------------
CREATE VIEW vw_available_seats AS
SELECT 
    ss.schedule_seat_id,
    ss.schedule_id,
    s.bus_id,
    b.bus_name,
    r.source,
    r.destination,
    s.departure_datetime,
    s.arrival_datetime,
    s.base_fare,
    ss.seat_number,
    ss.seat_type,
    ss.seat_status
FROM schedule_seats ss
JOIN schedules s ON ss.schedule_id = s.schedule_id
JOIN buses b ON s.bus_id = b.bus_id
JOIN routes r ON s.route_id = r.route_id
WHERE s.schedule_status = 'SCHEDULED';

-- ----------------------------------------------------------------------------
-- 3. vw_booking_details
-- Full relational projection for ticket generation and passenger manifests
-- ----------------------------------------------------------------------------
CREATE VIEW vw_booking_details AS
SELECT 
    bk.booking_id,
    bk.booking_reference,
    bk.booking_date,
    bk.seat_number,
    bk.total_amount,
    bk.booking_status,
    p.passenger_id,
    p.passenger_name,
    p.age AS passenger_age,
    p.gender AS passenger_gender,
    p.phone AS passenger_phone,
    u.user_id,
    u.email AS user_email,
    s.schedule_id,
    s.departure_datetime,
    s.arrival_datetime,
    s.base_fare,
    s.schedule_status,
    r.route_id,
    r.source,
    r.destination,
    r.distance AS route_distance,
    b.bus_id,
    b.registration_number,
    b.bus_name,
    b.bus_type,
    pmt.payment_id,
    pmt.payment_method,
    pmt.transaction_reference,
    pmt.payment_status,
    chk.checkin_id,
    chk.checkin_status,
    chk.checkin_time
FROM bookings bk
JOIN passengers p ON bk.passenger_id = p.passenger_id
LEFT JOIN users u ON p.user_id = u.user_id
JOIN schedules s ON bk.schedule_id = s.schedule_id
JOIN routes r ON s.route_id = r.route_id
JOIN buses b ON s.bus_id = b.bus_id
LEFT JOIN payments pmt ON bk.booking_id = pmt.booking_id
LEFT JOIN ticket_checkins chk ON bk.booking_id = chk.booking_id;

-- ----------------------------------------------------------------------------
-- 4. vw_passenger_booking_history
-- Passenger self-service booking portal view
-- ----------------------------------------------------------------------------
CREATE VIEW vw_passenger_booking_history AS
SELECT 
    p.user_id,
    p.passenger_id,
    p.passenger_name,
    bk.booking_id,
    bk.booking_reference,
    bk.booking_date,
    bk.seat_number,
    bk.total_amount,
    bk.booking_status,
    r.source,
    r.destination,
    s.departure_datetime,
    s.arrival_datetime,
    b.bus_name,
    b.bus_type,
    pmt.payment_status,
    ref.refund_amount,
    ref.refund_status
FROM bookings bk
JOIN passengers p ON bk.passenger_id = p.passenger_id
JOIN schedules s ON bk.schedule_id = s.schedule_id
JOIN routes r ON s.route_id = r.route_id
JOIN buses b ON s.bus_id = b.bus_id
LEFT JOIN payments pmt ON bk.booking_id = pmt.booking_id
LEFT JOIN refunds ref ON bk.booking_id = ref.booking_id;

-- ----------------------------------------------------------------------------
-- 5. vw_route_revenue
-- Aggregated financial performance metrics per route
-- ----------------------------------------------------------------------------
CREATE VIEW vw_route_revenue AS
SELECT 
    r.route_id,
    r.source,
    r.destination,
    COUNT(DISTINCT s.schedule_id) AS total_trips_scheduled,
    COUNT(DISTINCT CASE WHEN bk.booking_status = 'CONFIRMED' THEN bk.booking_id END) AS confirmed_bookings,
    COUNT(DISTINCT CASE WHEN bk.booking_status = 'CANCELLED' THEN bk.booking_id END) AS cancelled_bookings,
    COALESCE(SUM(CASE WHEN bk.booking_status = 'CONFIRMED' THEN bk.total_amount ELSE 0 END), 0.00) AS total_gross_revenue,
    COALESCE(SUM(ref.refund_amount), 0.00) AS total_refunded,
    COALESCE(SUM(CASE WHEN bk.booking_status = 'CONFIRMED' THEN bk.total_amount ELSE 0 END), 0.00) - COALESCE(SUM(ref.refund_amount), 0.00) AS net_revenue
FROM routes r
LEFT JOIN schedules s ON r.route_id = s.route_id
LEFT JOIN bookings bk ON s.schedule_id = bk.schedule_id
LEFT JOIN refunds ref ON bk.booking_id = ref.booking_id
GROUP BY r.route_id, r.source, r.destination;

-- ----------------------------------------------------------------------------
-- 6. vw_schedule_occupancy
-- Real-time trip occupancy rate and inventory counters
-- ----------------------------------------------------------------------------
CREATE VIEW vw_schedule_occupancy AS
SELECT 
    s.schedule_id,
    s.departure_datetime,
    s.arrival_datetime,
    s.schedule_status,
    r.source,
    r.destination,
    b.registration_number,
    b.bus_name,
    b.bus_type,
    b.capacity AS total_capacity,
    COUNT(CASE WHEN ss.seat_status = 'BOOKED' THEN 1 END) AS booked_seats,
    COUNT(CASE WHEN ss.seat_status = 'AVAILABLE' THEN 1 END) AS available_seats,
    COUNT(CASE WHEN ss.seat_status = 'BLOCKED' THEN 1 END) AS blocked_seats,
    ROUND(
        (COUNT(CASE WHEN ss.seat_status = 'BOOKED' THEN 1 END) * 100.0) / NULLIF(b.capacity, 0),
        2
    ) AS occupancy_percentage
FROM schedules s
JOIN routes r ON s.route_id = r.route_id
JOIN buses b ON s.bus_id = b.bus_id
LEFT JOIN schedule_seats ss ON s.schedule_id = ss.schedule_id
GROUP BY s.schedule_id, s.departure_datetime, s.arrival_datetime, s.schedule_status, 
         r.source, r.destination, b.registration_number, b.bus_name, b.bus_type, b.capacity;

