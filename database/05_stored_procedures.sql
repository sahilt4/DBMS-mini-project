-- ============================================================================
-- BUS RESERVATION & MANAGEMENT SYSTEM (BRMS)
-- Script 05: Stored Procedures
-- Target Database: MySQL 8.x
-- ============================================================================

USE brms_db;

DELIMITER $$

-- ----------------------------------------------------------------------------
-- 1. sp_search_buses
-- Searches active scheduled trips between source and destination on a given date
-- ----------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_search_buses$$
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
        r.distance,
        r.estimated_duration,
        b.bus_id,
        b.registration_number,
        b.bus_name,
        b.bus_type,
        b.capacity AS total_seats,
        s.departure_datetime,
        s.arrival_datetime,
        s.base_fare,
        s.schedule_status,
        COUNT(CASE WHEN ss.seat_status = 'AVAILABLE' THEN 1 END) AS available_seats
    FROM schedules s
    JOIN routes r ON s.route_id = r.route_id
    JOIN buses b ON s.bus_id = b.bus_id
    LEFT JOIN schedule_seats ss ON s.schedule_id = ss.schedule_id
    WHERE s.schedule_status = 'SCHEDULED'
      AND DATE(s.departure_datetime) = p_travel_date
      AND LOWER(TRIM(r.source)) LIKE CONCAT('%', LOWER(TRIM(p_source)), '%')
      AND LOWER(TRIM(r.destination)) LIKE CONCAT('%', LOWER(TRIM(p_destination)), '%')
    GROUP BY 
        s.schedule_id, r.route_id, r.source, r.destination, r.distance, r.estimated_duration,
        b.bus_id, b.registration_number, b.bus_name, b.bus_type, b.capacity,
        s.departure_datetime, s.arrival_datetime, s.base_fare, s.schedule_status
    ORDER BY s.departure_datetime ASC;
END$$

-- ----------------------------------------------------------------------------
-- 2. sp_book_seat
-- Concurrency-safe transactional seat reservation with row-level locking
-- ----------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_book_seat$$
CREATE PROCEDURE sp_book_seat(
    IN p_schedule_id INT,
    IN p_passenger_id INT,
    IN p_seat_number INT,
    IN p_payment_method VARCHAR(30),
    OUT p_booking_reference VARCHAR(32),
    OUT p_status_code INT,
    OUT p_message VARCHAR(255)
)
proc_label: BEGIN
    DECLARE v_seat_id INT;
    DECLARE v_seat_status VARCHAR(20);
    DECLARE v_fare DECIMAL(8,2);
    DECLARE v_schedule_status VARCHAR(20);
    DECLARE v_booking_id INT;
    DECLARE v_tx_ref VARCHAR(64);
    
    -- Error Handler: Rollback on any SQL exception
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_booking_reference = NULL;
        SET p_status_code = 500;
        SET p_message = 'Transaction aborted due to internal database error.';
    END;

    START TRANSACTION;

    -- Verify schedule exists and is valid
    SELECT base_fare, schedule_status INTO v_fare, v_schedule_status
    FROM schedules 
    WHERE schedule_id = p_schedule_id;

    IF v_schedule_status IS NULL OR v_schedule_status <> 'SCHEDULED' THEN
        ROLLBACK;
        SET p_booking_reference = NULL;
        SET p_status_code = 400;
        SET p_message = 'Schedule is not active or does not exist.';
        LEAVE proc_label;
    END IF;

    -- Lock the requested seat record using SELECT ... FOR UPDATE
    SELECT schedule_seat_id, seat_status 
    INTO v_seat_id, v_seat_status
    FROM schedule_seats
    WHERE schedule_id = p_schedule_id AND seat_number = p_seat_number
    FOR UPDATE;

    IF v_seat_id IS NULL THEN
        ROLLBACK;
        SET p_booking_reference = NULL;
        SET p_status_code = 404;
        SET p_message = 'Requested seat number does not exist for this schedule.';
        LEAVE proc_label;
    END IF;

    IF v_seat_status <> 'AVAILABLE' THEN
        ROLLBACK;
        SET p_booking_reference = NULL;
        SET p_status_code = 409;
        SET p_message = 'Requested seat has already been booked or locked by another passenger.';
        LEAVE proc_label;
    END IF;

    -- Generate unique booking reference and transaction reference
    SET p_booking_reference = CONCAT('BUS-', DATE_FORMAT(NOW(), '%Y%m%d'), '-', LPAD(FLOOR(RAND() * 999999), 6, '0'));
    SET v_tx_ref = CONCAT('TXN-', UPPER(HEX(RANDOM_BYTES(8))));

    -- 1. Reserve seat in authoritative inventory
    UPDATE schedule_seats 
    SET seat_status = 'BOOKED' 
    WHERE schedule_seat_id = v_seat_id;

    -- 2. Insert booking record
    INSERT INTO bookings (
        booking_reference, passenger_id, schedule_id, seat_number,
        booking_date, total_amount, booking_status
    ) VALUES (
        p_booking_reference, p_passenger_id, p_schedule_id, p_seat_number,
        NOW(), v_fare, 'CONFIRMED'
    );
    SET v_booking_id = LAST_INSERT_ID();

    -- 3. Record payment ledger
    INSERT INTO payments (
        booking_id, amount, payment_method, transaction_reference,
        payment_status, payment_date
    ) VALUES (
        v_booking_id, v_fare, p_payment_method, v_tx_ref,
        'PAID', NOW()
    );

    COMMIT;
    SET p_status_code = 200;
    SET p_message = 'Booking confirmed successfully.';
END$$

-- ----------------------------------------------------------------------------
-- 3. sp_cancel_booking
-- Handles booking cancellation, tiered refund computation, and seat release
-- ----------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_cancel_booking$$
CREATE PROCEDURE sp_cancel_booking(
    IN p_booking_id INT,
    IN p_reason VARCHAR(255),
    OUT p_refund_amount DECIMAL(8,2),
    OUT p_status_code INT,
    OUT p_message VARCHAR(255)
)
proc_label: BEGIN
    DECLARE v_schedule_id INT;
    DECLARE v_seat_number INT;
    DECLARE v_amount DECIMAL(8,2);
    DECLARE v_current_status VARCHAR(20);
    DECLARE v_dep_time DATETIME;
    DECLARE v_payment_id INT;
    DECLARE v_hours_diff DECIMAL(7,2);
    DECLARE v_refund_pct DECIMAL(5,2);
    DECLARE v_waitlist_allocated INT;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_refund_amount = 0.00;
        SET p_status_code = 500;
        SET p_message = 'Cancellation transaction aborted due to database error.';
    END;

    START TRANSACTION;

    SELECT bk.schedule_id, bk.seat_number, bk.total_amount, bk.booking_status,
           s.departure_datetime, pmt.payment_id
    INTO v_schedule_id, v_seat_number, v_amount, v_current_status,
         v_dep_time, v_payment_id
    FROM bookings bk
    JOIN schedules s ON bk.schedule_id = s.schedule_id
    LEFT JOIN payments pmt ON bk.booking_id = pmt.booking_id
    WHERE bk.booking_id = p_booking_id
    FOR UPDATE;

    IF v_schedule_id IS NULL THEN
        ROLLBACK;
        SET p_refund_amount = 0.00;
        SET p_status_code = 404;
        SET p_message = 'Booking record not found.';
        LEAVE proc_label;
    END IF;

    IF v_current_status = 'CANCELLED' THEN
        ROLLBACK;
        SET p_refund_amount = 0.00;
        SET p_status_code = 400;
        SET p_message = 'This booking is already cancelled.';
        LEAVE proc_label;
    END IF;

    -- Calculate hours remaining until departure
    SET v_hours_diff = TIMESTAMPDIFF(MINUTE, NOW(), v_dep_time) / 60.0;

    IF v_hours_diff >= 24.0 THEN
        SET v_refund_pct = 0.90; -- 90% refund (10% cancellation charge)
    ELSEIF v_hours_diff >= 12.0 THEN
        SET v_refund_pct = 0.75; -- 75% refund (25% cancellation charge)
    ELSEIF v_hours_diff >= 4.0 THEN
        SET v_refund_pct = 0.50; -- 50% refund (50% cancellation charge)
    ELSE
        SET v_refund_pct = 0.00; -- No refund if cancelled less than 4 hours before
    END IF;

    SET p_refund_amount = ROUND(v_amount * v_refund_pct, 2);

    -- 1. Update booking status
    UPDATE bookings 
    SET booking_status = 'CANCELLED',
        cancellation_reason = p_reason,
        cancelled_at = NOW()
    WHERE booking_id = p_booking_id;

    -- 2. Release seat inventory
    UPDATE schedule_seats 
    SET seat_status = 'AVAILABLE'
    WHERE schedule_id = v_schedule_id AND seat_number = v_seat_number;

    -- 3. Record refund ledger
    IF v_payment_id IS NOT NULL AND p_refund_amount > 0 THEN
        INSERT INTO refunds (payment_id, booking_id, refund_amount, refund_reason, refund_status, refund_date)
        VALUES (v_payment_id, p_booking_id, p_refund_amount, p_reason, 'PROCESSED', NOW());

        UPDATE payments 
        SET payment_status = 'REFUNDED' 
        WHERE payment_id = v_payment_id;
    END IF;

    COMMIT;

    -- 4. Automatically trigger waitlist allocation
    CALL sp_process_waitlist(v_schedule_id, v_waitlist_allocated);

    SET p_status_code = 200;
    SET p_message = CONCAT('Booking cancelled successfully. Refund of Rs. ', p_refund_amount, ' processed.');
END$$

-- ----------------------------------------------------------------------------
-- 4. sp_process_waitlist
-- Checks priority queue and allocates released seats to waitlisted passengers
-- ----------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_process_waitlist$$
CREATE PROCEDURE sp_process_waitlist(
    IN p_schedule_id INT,
    OUT p_allocated_count INT
)
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE v_waitlist_id INT;
    DECLARE v_passenger_id INT;
    DECLARE v_available_seat_id INT;
    DECLARE v_seat_number INT;
    
    DECLARE cur_waitlist CURSOR FOR
        SELECT waitlist_id, passenger_id 
        FROM waitlist 
        WHERE schedule_id = p_schedule_id AND waitlist_status = 'WAITING'
        ORDER BY queue_position ASC;
    
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    SET p_allocated_count = 0;

    OPEN cur_waitlist;
    alloc_loop: LOOP
        FETCH cur_waitlist INTO v_waitlist_id, v_passenger_id;
        IF done THEN
            LEAVE alloc_loop;
        END IF;

        -- Find an available seat for this schedule
        SELECT schedule_seat_id, seat_number
        INTO v_available_seat_id, v_seat_number
        FROM schedule_seats
        WHERE schedule_id = p_schedule_id AND seat_status = 'AVAILABLE'
        LIMIT 1;

        IF v_available_seat_id IS NOT NULL THEN
            -- Allocate seat to waitlisted passenger
            UPDATE schedule_seats 
            SET seat_status = 'BOOKED' 
            WHERE schedule_seat_id = v_available_seat_id;

            UPDATE waitlist 
            SET waitlist_status = 'ALLOCATED' 
            WHERE waitlist_id = v_waitlist_id;

            SET p_allocated_count = p_allocated_count + 1;
        ELSE
            -- No more seats available
            LEAVE alloc_loop;
        END IF;
    END LOOP;
    CLOSE cur_waitlist;
END$$

-- ----------------------------------------------------------------------------
-- 5. sp_generate_revenue_report
-- Aggregates operational and financial statistics across custom date ranges
-- ----------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_generate_revenue_report$$
CREATE PROCEDURE sp_generate_revenue_report(
    IN p_start_date DATE,
    IN p_end_date DATE
)
BEGIN
    SELECT 
        r.route_id,
        CONCAT(r.source, ' -> ', r.destination) AS route_name,
        b.bus_type,
        COUNT(DISTINCT s.schedule_id) AS trips_count,
        COUNT(CASE WHEN bk.booking_status = 'CONFIRMED' THEN bk.booking_id END) AS confirmed_bookings,
        COUNT(CASE WHEN bk.booking_status = 'CANCELLED' THEN bk.booking_id END) AS cancellations_count,
        COALESCE(SUM(CASE WHEN bk.booking_status = 'CONFIRMED' THEN bk.total_amount ELSE 0 END), 0.00) AS gross_revenue,
        COALESCE(SUM(ref.refund_amount), 0.00) AS total_refunds,
        COALESCE(SUM(CASE WHEN bk.booking_status = 'CONFIRMED' THEN bk.total_amount ELSE 0 END), 0.00) - COALESCE(SUM(ref.refund_amount), 0.00) AS net_revenue
    FROM schedules s
    JOIN routes r ON s.route_id = r.route_id
    JOIN buses b ON s.bus_id = b.bus_id
    LEFT JOIN bookings bk ON s.schedule_id = bk.schedule_id
    LEFT JOIN refunds ref ON bk.booking_id = ref.booking_id
    WHERE DATE(s.departure_datetime) BETWEEN p_start_date AND p_end_date
    GROUP BY r.route_id, r.source, r.destination, b.bus_type
    ORDER BY net_revenue DESC;
END$$

DELIMITER ;

