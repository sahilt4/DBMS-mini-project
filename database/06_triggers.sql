-- ============================================================================
-- BUS RESERVATION & MANAGEMENT SYSTEM (BRMS)
-- Script 06: Database Triggers for Integrity, Automation and Auditing
-- Target Database: MySQL 8.x
-- ============================================================================

USE brms_db;

DELIMITER $$

-- ----------------------------------------------------------------------------
-- 1. trg_schedule_after_insert
-- Automatically populates schedule_seats inventory when a new schedule is inserted
-- ----------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_schedule_after_insert$$
CREATE TRIGGER trg_schedule_after_insert
AFTER INSERT ON schedules
FOR EACH ROW
BEGIN
    DECLARE v_capacity INT;
    DECLARE v_seat_num INT DEFAULT 1;
    DECLARE v_seat_type VARCHAR(20);
    DECLARE v_bus_type VARCHAR(50);

    -- Get capacity and bus type
    SELECT capacity, bus_type INTO v_capacity, v_bus_type
    FROM buses 
    WHERE bus_id = NEW.bus_id;

    -- Generate seats for this schedule
    WHILE v_seat_num <= v_capacity DO
        IF v_bus_type LIKE '%Sleeper%' THEN
            IF (v_seat_num % 2) = 1 THEN
                SET v_seat_type = 'SLEEPER_LOWER';
            ELSE
                SET v_seat_type = 'SLEEPER_UPPER';
            END IF;
        ELSE
            IF (v_seat_num % 4 = 1) OR (v_seat_num % 4 = 0) THEN
                SET v_seat_type = 'WINDOW';
            ELSE
                SET v_seat_type = 'AISLE';
            END IF;
        END IF;

        INSERT INTO schedule_seats (schedule_id, seat_number, seat_type, seat_status)
        VALUES (NEW.schedule_id, v_seat_num, v_seat_type, 'AVAILABLE');

        SET v_seat_num = v_seat_num + 1;
    END WHILE;
END$$

-- ----------------------------------------------------------------------------
-- 2. trg_booking_status_audit
-- Records an audit log entry whenever a booking status changes
-- ----------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_booking_status_audit$$
CREATE TRIGGER trg_booking_status_audit
AFTER UPDATE ON bookings
FOR EACH ROW
BEGIN
    IF OLD.booking_status <> NEW.booking_status THEN
        INSERT INTO audit_logs (
            action_type, table_name, record_id, changed_by, old_values, new_values
        ) VALUES (
            'STATUS_CHANGE',
            'bookings',
            CAST(NEW.booking_id AS CHAR),
            CURRENT_USER(),
            JSON_OBJECT('status', OLD.booking_status, 'cancelled_at', OLD.cancelled_at),
            JSON_OBJECT('status', NEW.booking_status, 'cancelled_at', NEW.cancelled_at, 'reason', NEW.cancellation_reason)
        );
    END IF;
END$$

-- ----------------------------------------------------------------------------
-- 3. trg_payment_insert_audit
-- Audit log entry when payment is created
-- ----------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_payment_insert_audit$$
CREATE TRIGGER trg_payment_insert_audit
AFTER INSERT ON payments
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (
        action_type, table_name, record_id, changed_by, old_values, new_values
    ) VALUES (
        'PAYMENT_RECORDED',
        'payments',
        CAST(NEW.payment_id AS CHAR),
        CURRENT_USER(),
        NULL,
        JSON_OBJECT('booking_id', NEW.booking_id, 'amount', NEW.amount, 'method', NEW.payment_method, 'status', NEW.payment_status)
    );
END$$

DELIMITER ;
