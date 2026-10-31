-- ============================================================================
-- BUS RESERVATION & MANAGEMENT SYSTEM (BRMS)
-- Script 07: Realistic Seed / Sample Data
-- Target Database: MySQL 8.x
-- ============================================================================

USE brms_db;

SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------------------------------------------------------
-- 1. USERS
-- Default passwords:
-- Admin: Admin@123
-- Conductor: Conductor@123
-- Passengers: Pass@123
-- ----------------------------------------------------------------------------
INSERT INTO users (user_id, full_name, email, password_hash, role, phone, account_status) VALUES
(1, 'System Administrator', 'admin@brms.com', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855$a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', 'ADMIN', '9822000000', 'ACTIVE'),
(2, 'Ramesh Shinde (Conductor)', 'conductor@brms.com', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855$a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', 'CONDUCTOR', '9822011111', 'ACTIVE'),
(3, 'Sunil More (Conductor)', 'conductor2@brms.com', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855$a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', 'CONDUCTOR', '9822022222', 'ACTIVE'),
(4, 'Rahul Sharma', 'rahul@example.com', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855$a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', 'PASSENGER', '9822012345', 'ACTIVE'),
(5, 'Priya Patil', 'priya@example.com', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855$a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', 'PASSENGER', '9822054321', 'ACTIVE'),
(6, 'Amit Deshmukh', 'amit@example.com', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855$a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', 'PASSENGER', '9890112233', 'ACTIVE');

-- ----------------------------------------------------------------------------
-- 2. PASSENGERS
-- ----------------------------------------------------------------------------
INSERT INTO passengers (passenger_id, user_id, passenger_name, age, gender, phone) VALUES
(1, 4, 'Rahul Sharma', 28, 'Male', '9822012345'),
(2, 5, 'Priya Patil', 25, 'Female', '9822054321'),
(3, 6, 'Amit Deshmukh', 34, 'Male', '9890112233'),
(4, NULL, 'Neha Kulkarni', 29, 'Female', '9811223344');

-- ----------------------------------------------------------------------------
-- 3. ROUTES
-- ----------------------------------------------------------------------------
INSERT INTO routes (route_id, source, destination, distance, estimated_duration, route_status) VALUES
(1, 'Mumbai', 'Pune', 150.00, 180, 'ACTIVE'),
(2, 'Pune', 'Bangalore', 840.00, 780, 'ACTIVE'),
(3, 'Mumbai', 'Goa', 580.00, 600, 'ACTIVE'),
(4, 'Pune', 'Hyderabad', 560.00, 570, 'ACTIVE'),
(5, 'Delhi', 'Jaipur', 280.00, 300, 'ACTIVE');

-- ----------------------------------------------------------------------------
-- 4. BUS_STOPS
-- ----------------------------------------------------------------------------
INSERT INTO bus_stops (stop_id, stop_name, city, address) VALUES
(1, 'Mumbai CST Central', 'Mumbai', 'Opposite CST Station, Fort'),
(2, 'Vashi Highway Toll Plaza', 'Navi Mumbai', 'Sion-Panvel Expressway, Vashi'),
(3, 'Lonavala Express Junction', 'Lonavala', 'Mumbai-Pune Expressway, Lonavala'),
(4, 'Pune Wakad Bridge', 'Pune', 'Bangalore-Mumbai Bypass Highway, Wakad'),
(5, 'Pune Swargate Depot', 'Pune', 'Near Swargate Bus Station, Pune'),
(6, 'Bangalore Majestic Bus Stand', 'Bangalore', 'Kempegowda Bus Station, Majestic'),
(7, 'Panaji KTC Bus Terminus', 'Goa', 'Patto Centre, Panaji');

-- ----------------------------------------------------------------------------
-- 5. ROUTE_STOPS (Intermediate Boarding Points for Route 1)
-- ----------------------------------------------------------------------------
INSERT INTO route_stops (route_stop_id, route_id, stop_id, stop_sequence, distance_from_origin, arrival_offset_minutes) VALUES
(1, 1, 1, 1, 0.00, 0),
(2, 1, 2, 2, 30.00, 45),
(3, 1, 3, 3, 85.00, 110),
(4, 1, 4, 4, 135.00, 160),
(5, 1, 5, 5, 150.00, 180);

-- ----------------------------------------------------------------------------
-- 6. BUSES
-- ----------------------------------------------------------------------------
INSERT INTO buses (bus_id, registration_number, bus_name, bus_type, capacity, operational_status) VALUES
(1, 'MH-12-AB-1001', 'Shivneri Superfast', 'Volvo Multi-Axle', 40, 'ACTIVE'),
(2, 'MH-14-XY-2002', 'Maharashtra Travels', 'AC Sleeper', 30, 'ACTIVE'),
(3, 'KA-01-CD-3003', 'Airavat Express', 'AC Seater', 44, 'ACTIVE'),
(4, 'GA-07-EF-4004', 'Goa Voyager', 'Non-AC Sleeper', 32, 'ACTIVE'),
(5, 'DL-01-GH-5005', 'Capital Flyer', 'Non-AC Seater', 48, 'ACTIVE');

-- ----------------------------------------------------------------------------
-- 7. SCHEDULES
-- ----------------------------------------------------------------------------
INSERT INTO schedules (schedule_id, bus_id, route_id, departure_datetime, arrival_datetime, base_fare, schedule_status) VALUES
(1, 1, 1, DATE_ADD(NOW(), INTERVAL 1 DAY), DATE_ADD(DATE_ADD(NOW(), INTERVAL 1 DAY), INTERVAL 3 HOUR), 480.00, 'SCHEDULED'),
(2, 2, 1, DATE_ADD(NOW(), INTERVAL 2 DAY), DATE_ADD(DATE_ADD(NOW(), INTERVAL 2 DAY), INTERVAL 3 HOUR), 520.00, 'SCHEDULED'),
(3, 3, 2, DATE_ADD(NOW(), INTERVAL 1 DAY), DATE_ADD(DATE_ADD(NOW(), INTERVAL 1 DAY), INTERVAL 13 HOUR), 1450.00, 'SCHEDULED'),
(4, 4, 3, DATE_ADD(NOW(), INTERVAL 2 DAY), DATE_ADD(DATE_ADD(NOW(), INTERVAL 2 DAY), INTERVAL 10 HOUR), 950.00, 'SCHEDULED');

-- ----------------------------------------------------------------------------
-- 8. SCHEDULE_SEATS (Inventory generation for Schedule 1)
-- ----------------------------------------------------------------------------
INSERT INTO schedule_seats (schedule_id, seat_number, seat_type, seat_status) VALUES
(1, 1, 'WINDOW', 'BOOKED'),
(1, 2, 'AISLE', 'AVAILABLE'),
(1, 3, 'AISLE', 'AVAILABLE'),
(1, 4, 'WINDOW', 'AVAILABLE'),
(1, 5, 'WINDOW', 'BOOKED'),
(1, 6, 'AISLE', 'AVAILABLE'),
(1, 7, 'AISLE', 'AVAILABLE'),
(1, 8, 'WINDOW', 'AVAILABLE'),
(1, 9, 'WINDOW', 'AVAILABLE'),
(1, 10, 'AISLE', 'AVAILABLE');

-- ----------------------------------------------------------------------------
-- 9. BOOKINGS & PAYMENTS
-- ----------------------------------------------------------------------------
INSERT INTO bookings (booking_id, booking_reference, passenger_id, schedule_id, seat_number, boarding_stop_id, dropping_stop_id, total_amount, booking_status) VALUES
(1, 'BUS-20261031-100001', 1, 1, 1, 1, 5, 480.00, 'CONFIRMED'),
(2, 'BUS-20261031-100002', 2, 1, 5, 2, 4, 480.00, 'CONFIRMED');

INSERT INTO payments (payment_id, booking_id, amount, payment_method, transaction_reference, payment_status) VALUES
(1, 1, 480.00, 'UPI', 'TXN-UPI-20261031-998877', 'PAID'),
(2, 2, 480.00, 'Credit Card', 'TXN-CC-20261031-112233', 'PAID');

-- ----------------------------------------------------------------------------
-- 10. TICKET_CHECKINS (Conductor digital verification)
-- ----------------------------------------------------------------------------
INSERT INTO ticket_checkins (checkin_id, booking_id, conductor_id, checkin_status, boarding_stop_id) VALUES
(1, 1, 2, 'VERIFIED', 1);

-- ----------------------------------------------------------------------------
-- 11. WAITLIST
-- ----------------------------------------------------------------------------
INSERT INTO waitlist (waitlist_id, passenger_id, schedule_id, preferred_seat_type, queue_position, waitlist_status) VALUES
(1, 3, 1, 'WINDOW', 1, 'WAITING');

SET FOREIGN_KEY_CHECKS = 1;
