"""
Booking repository for managing bookings, schedule_seats, payments, and refunds.
Implements ACID transaction-safe seat allocations and cancellations across MySQL and SQLite.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
import random

from app.database import get_connection, transaction, DatabaseConnection


def get_occupied_seats(schedule_id: int, conn: Optional[DatabaseConnection] = None) -> List[int]:
    """
    Returns list of seat numbers that are currently BOOKED or BLOCKED in schedule_seats.
    """
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT seat_number
            FROM schedule_seats
            WHERE schedule_id = %s AND seat_status <> 'AVAILABLE'
            ORDER BY seat_number ASC;
            """,
            (schedule_id,)
        )
        return [row["seat_number"] for row in cursor.fetchall()]
    finally:
        if close_after:
            conn.close()


def is_seat_available(schedule_id: int, seat_number: int, conn: Optional[DatabaseConnection] = None) -> bool:
    """Checks if a specific seat is available in authoritative schedule_seats inventory."""
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT seat_status
            FROM schedule_seats
            WHERE schedule_id = %s AND seat_number = %s;
            """,
            (schedule_id, seat_number)
        )
        row = cursor.fetchone()
        return row is not None and row["seat_status"] == "AVAILABLE"
    finally:
        if close_after:
            conn.close()


def create_booking_atomic(
    schedule_id: int,
    passenger_id: int,
    seat_number: int,
    amount: float,
    payment_method: str,
    boarding_stop_id: Optional[int] = None,
    dropping_stop_id: Optional[int] = None,
    conn: Optional[DatabaseConnection] = None
) -> Dict[str, Any]:
    """
    ACID transaction: Locks seat record, validates availability, reserves seat,
    creates booking and records payment ledger.
    """
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True

    try:
        with transaction(conn) as cursor:
            # 1. Lock and verify seat status
            if conn.is_sqlite:
                cursor.execute(
                    "SELECT schedule_seat_id, seat_status FROM schedule_seats WHERE schedule_id = %s AND seat_number = %s;",
                    (schedule_id, seat_number)
                )
            else:
                cursor.execute(
                    "SELECT schedule_seat_id, seat_status FROM schedule_seats WHERE schedule_id = %s AND seat_number = %s FOR UPDATE;",
                    (schedule_id, seat_number)
                )
            seat_row = cursor.fetchone()
            if not seat_row:
                raise ValueError(f"Seat #{seat_number} does not exist for this schedule.")
            if seat_row["seat_status"] != "AVAILABLE":
                raise ValueError(f"Seat #{seat_number} has already been reserved by another passenger. Please select another seat.")

            # 2. Update schedule_seats to BOOKED
            cursor.execute(
                "UPDATE schedule_seats SET seat_status = 'BOOKED' WHERE schedule_seat_id = %s;",
                (seat_row["schedule_seat_id"],)
            )

            # 3. Generate booking reference
            now = datetime.now()
            date_part = now.strftime("%Y%m%d")
            rand_part = f"{random.randint(100000, 999999)}"
            booking_ref = f"BUS-{date_part}-{rand_part}"

            # 4. Insert booking
            cursor.execute(
                """
                INSERT INTO bookings (
                    booking_reference, schedule_id, passenger_id, seat_number,
                    boarding_stop_id, dropping_stop_id, amount, total_amount, status, booking_status, booking_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'CONFIRMED', 'CONFIRMED', %s);
                """,
                (booking_ref, schedule_id, passenger_id, seat_number, boarding_stop_id, dropping_stop_id, amount, amount, now.strftime("%Y-%m-%d %H:%M:%S"))
            )
            booking_id = cursor.lastrowid

            # 5. Insert payment ledger
            tx_ref = f"TXN-{payment_method[:3].upper()}-{rand_part}"
            cursor.execute(
                """
                INSERT INTO payments (
                    booking_id, amount, payment_method, transaction_reference, payment_status, payment_date
                ) VALUES (%s, %s, %s, %s, 'PAID', %s);
                """,
                (booking_id, amount, payment_method, tx_ref, now.strftime("%Y-%m-%d %H:%M:%S"))
            )
            payment_id = cursor.lastrowid

        return {
            "booking_id": booking_id,
            "booking_reference": booking_ref,
            "payment_id": payment_id,
            "transaction_reference": tx_ref,
            "schedule_id": schedule_id,
            "seat_number": seat_number,
            "amount": amount,
            "status": "CONFIRMED"
        }
    finally:
        if close_after:
            conn.close()


def cancel_booking_atomic(
    booking_id: int,
    reason: str,
    conn: Optional[DatabaseConnection] = None
) -> Dict[str, Any]:
    """
    ACID transaction: Cancels booking, releases seat in schedule_seats,
    computes tiered refund based on departure time, creates refund record,
    and triggers waitlist allocation.
    """
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True

    try:
        with transaction(conn) as cursor:
            # Look up booking and schedule details
            cursor.execute(
                """
                SELECT bk.booking_id, bk.booking_reference, bk.schedule_id, bk.seat_number,
                       COALESCE(bk.total_amount, bk.amount, 0.0) AS total_amount,
                       COALESCE(bk.booking_status, bk.status, 'CONFIRMED') AS booking_status,
                       COALESCE(s.departure_datetime, s.travel_date || ' ' || s.departure_time) AS departure_datetime,
                       pmt.payment_id
                FROM bookings bk
                JOIN schedules s ON bk.schedule_id = s.schedule_id
                LEFT JOIN payments pmt ON bk.booking_id = pmt.booking_id
                WHERE bk.booking_id = %s;
                """,
                (booking_id,)
            )
            b_row = cursor.fetchone()
            if not b_row:
                raise ValueError("Booking record not found.")
            if b_row["booking_status"] == "CANCELLED":
                raise ValueError("Booking is already cancelled.")

            # Calculate refund tier based on hours before departure
            dep_dt_str = str(b_row["departure_datetime"])
            try:
                dep_dt = datetime.fromisoformat(dep_dt_str)
            except Exception:
                try:
                    dep_dt = datetime.strptime(dep_dt_str, "%Y-%m-%d %H:%M:%S")
                except Exception:
                    dep_dt = datetime.now()

            hours_remaining = (dep_dt - datetime.now()).total_seconds() / 3600.0
            if hours_remaining >= 24.0:
                refund_pct = 0.90  # 90% refund (10% fee)
            elif hours_remaining >= 12.0:
                refund_pct = 0.75  # 75% refund (25% fee)
            elif hours_remaining >= 4.0:
                refund_pct = 0.50  # 50% refund (50% fee)
            else:
                refund_pct = 0.00  # No refund within 4 hours

            refund_amt = round(float(b_row["total_amount"]) * refund_pct, 2)
            cancellation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 1. Update booking
            cursor.execute(
                """
                UPDATE bookings
                SET status = 'CANCELLED', booking_status = 'CANCELLED',
                    cancellation_reason = %s, cancellation_date = %s, cancelled_at = %s
                WHERE booking_id = %s;
                """,
                (reason, cancellation_date, cancellation_date, booking_id)
            )

            # 2. Release seat in schedule_seats
            cursor.execute(
                """
                UPDATE schedule_seats
                SET seat_status = 'AVAILABLE'
                WHERE schedule_id = %s AND seat_number = %s;
                """,
                (b_row["schedule_id"], b_row["seat_number"])
            )

            # 3. Always update payment status to REFUNDED
            cursor.execute(
                "UPDATE payments SET payment_status = 'REFUNDED' WHERE booking_id = %s;",
                (booking_id,)
            )

            # 4. Create refund ledger if applicable
            if b_row["payment_id"] and refund_amt > 0:
                cursor.execute(
                    """
                    INSERT INTO refunds (payment_id, booking_id, refund_amount, refund_reason, refund_status, refund_date)
                    VALUES (%s, %s, %s, %s, 'PROCESSED', %s);
                    """,
                    (b_row["payment_id"], booking_id, refund_amt, reason, cancellation_date)
                )

            # 4. Check waitlist for allocation if the trip was at full capacity
            cursor.execute(
                "SELECT COUNT(*) AS avail FROM schedule_seats WHERE schedule_id = %s AND seat_status = 'AVAILABLE';",
                (b_row["schedule_id"],)
            )
            avail_row = cursor.fetchone()
            avail_cnt = avail_row["avail"] if avail_row else 0

            wl_row = None
            if avail_cnt == 1:
                cursor.execute(
                    """
                    SELECT waitlist_id, passenger_id 
                    FROM waitlist
                    WHERE schedule_id = %s AND waitlist_status = 'WAITING'
                    ORDER BY queue_position ASC
                    LIMIT 1;
                    """,
                    (b_row["schedule_id"],)
                )
                wl_row = cursor.fetchone()
                if wl_row:
                    # Re-book released seat for waitlisted passenger
                    cursor.execute(
                        "UPDATE schedule_seats SET seat_status = 'BOOKED' WHERE schedule_id = %s AND seat_number = %s;",
                        (b_row["schedule_id"], b_row["seat_number"])
                    )
                    cursor.execute(
                        "UPDATE waitlist SET waitlist_status = 'ALLOCATED' WHERE waitlist_id = %s;",
                        (wl_row["waitlist_id"],)
                    )

        return {
            "booking_id": booking_id,
            "refund_amount": refund_amt,
            "cancellation_date": cancellation_date,
            "waitlist_allocated": wl_row is not None
        }
    finally:
        if close_after:
            conn.close()


def find_booking_by_id(booking_id: int, conn: Optional[DatabaseConnection] = None) -> Optional[Dict[str, Any]]:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                b.booking_id, b.booking_reference, b.schedule_id, b.passenger_id,
                b.seat_number, b.booking_date,
                COALESCE(b.total_amount, b.amount, 0.0) AS total_amount,
                COALESCE(b.amount, b.total_amount, 0.0) AS amount,
                COALESCE(b.booking_status, b.status, 'CONFIRMED') AS booking_status,
                COALESCE(b.status, b.booking_status, 'CONFIRMED') AS status,
                COALESCE(b.cancelled_at, b.cancellation_date) AS cancellation_date,
                b.cancellation_reason,
                COALESCE(p.passenger_name, p.full_name, '') AS passenger_name,
                COALESCE(p.full_name, p.passenger_name, '') AS full_name,
                p.age, p.gender, p.phone, p.user_id,
                s.departure_datetime, s.arrival_datetime,
                COALESCE(s.travel_date, SUBSTR(s.departure_datetime, 1, 10)) AS travel_date,
                COALESCE(s.departure_time, SUBSTR(s.departure_datetime, 12, 5)) AS departure_time,
                COALESCE(s.arrival_time, SUBSTR(s.arrival_datetime, 12, 5)) AS arrival_time,
                COALESCE(s.fare, s.base_fare, 0.0) AS fare,
                COALESCE(s.schedule_status, s.status) AS schedule_status,
                COALESCE(bs.bus_number, bs.registration_number) AS bus_number,
                COALESCE(bs.registration_number, bs.bus_number) AS registration_number,
                bs.bus_name, bs.bus_type,
                r.source, r.destination,
                COALESCE(r.distance_km, r.distance) AS distance_km,
                pm.payment_id, pm.payment_method,
                COALESCE(pm.payment_status, 'PAID') AS payment_status,
                pm.payment_date, pm.transaction_reference,
                chk.checkin_id, chk.checkin_status, chk.checkin_time
            FROM bookings b
            INNER JOIN passengers p ON b.passenger_id = p.passenger_id
            INNER JOIN schedules s ON b.schedule_id = s.schedule_id
            INNER JOIN buses bs ON s.bus_id = bs.bus_id
            INNER JOIN routes r ON s.route_id = r.route_id
            LEFT JOIN payments pm ON b.booking_id = pm.booking_id
            LEFT JOIN ticket_checkins chk ON b.booking_id = chk.booking_id
            WHERE b.booking_id = %s;
            """,
            (booking_id,)
        )
        return cursor.fetchone()
    finally:
        if close_after:
            conn.close()


def find_booking_by_ref(booking_ref: str, conn: Optional[DatabaseConnection] = None) -> Optional[Dict[str, Any]]:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                b.booking_id, b.booking_reference, b.schedule_id, b.passenger_id,
                b.seat_number, b.booking_date, b.total_amount, b.total_amount AS amount,
                b.booking_status, b.booking_status AS status, b.cancelled_at AS cancellation_date,
                b.cancellation_reason,
                p.passenger_name, p.passenger_name AS full_name, p.age, p.gender, p.phone, p.user_id,
                s.departure_datetime, s.arrival_datetime,
                SUBSTR(s.departure_datetime, 1, 10) AS travel_date,
                SUBSTR(s.departure_datetime, 12, 5) AS departure_time,
                SUBSTR(s.arrival_datetime, 12, 5) AS arrival_time,
                s.base_fare AS fare, s.schedule_status,
                bs.registration_number AS bus_number, bs.bus_name, bs.bus_type,
                r.source, r.destination, r.distance AS distance_km,
                pm.payment_id, pm.payment_method, pm.payment_status, pm.payment_date, pm.transaction_reference,
                chk.checkin_id, chk.checkin_status, chk.checkin_time
            FROM bookings b
            INNER JOIN passengers p ON b.passenger_id = p.passenger_id
            INNER JOIN schedules s ON b.schedule_id = s.schedule_id
            INNER JOIN buses bs ON s.bus_id = bs.bus_id
            INNER JOIN routes r ON s.route_id = r.route_id
            LEFT JOIN payments pm ON b.booking_id = pm.booking_id
            LEFT JOIN ticket_checkins chk ON b.booking_id = chk.booking_id
            WHERE LOWER(b.booking_reference) = LOWER(%s);
            """,
            (booking_ref.strip(),)
        )
        return cursor.fetchone()
    finally:
        if close_after:
            conn.close()


def get_passenger_bookings(
    user_id: int,
    search_ref: Optional[str] = None,
    travel_date: Optional[str] = None,
    status: Optional[str] = None,
    conn: Optional[DatabaseConnection] = None
) -> List[Dict[str, Any]]:
    """Fetches all bookings owned by a specific logged-in passenger user."""
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        query = [
            """
            SELECT 
                b.booking_id, b.booking_reference, b.schedule_id, b.passenger_id,
                b.seat_number, b.booking_date, b.total_amount, b.total_amount AS amount,
                b.booking_status, b.booking_status AS status, b.cancelled_at AS cancellation_date,
                p.passenger_name, p.passenger_name AS full_name, p.age, p.gender, p.phone,
                s.departure_datetime, s.arrival_datetime,
                SUBSTR(s.departure_datetime, 1, 10) AS travel_date,
                SUBSTR(s.departure_datetime, 12, 5) AS departure_time,
                SUBSTR(s.arrival_datetime, 12, 5) AS arrival_time,
                s.base_fare AS fare, s.schedule_status,
                bs.registration_number AS bus_number, bs.bus_name, bs.bus_type,
                r.source, r.destination, r.distance AS distance_km,
                pm.payment_id, pm.payment_method, pm.payment_status, pm.payment_date, pm.transaction_reference,
                ref.refund_amount, ref.refund_status
            FROM bookings b
            INNER JOIN passengers p ON b.passenger_id = p.passenger_id
            INNER JOIN schedules s ON b.schedule_id = s.schedule_id
            INNER JOIN buses bs ON s.bus_id = bs.bus_id
            INNER JOIN routes r ON s.route_id = r.route_id
            LEFT JOIN payments pm ON b.booking_id = pm.booking_id
            LEFT JOIN refunds ref ON b.booking_id = ref.booking_id
            WHERE p.user_id = %s
            """
        ]
        params = [user_id]

        if search_ref:
            query.append("AND LOWER(b.booking_reference) LIKE %s")
            params.append(f"%{search_ref.strip().lower()}%")

        if travel_date:
            query.append("AND SUBSTR(s.departure_datetime, 1, 10) = %s")
            params.append(travel_date)

        if status and status != "All":
            query.append("AND b.booking_status = %s")
            params.append(status.upper())

        query.append("ORDER BY b.booking_date DESC")
        cursor.execute(" ".join(query), params)
        return cursor.fetchall()
    finally:
        if close_after:
            conn.close()


def get_all_bookings(
    search: Optional[str] = None,
    travel_date: Optional[str] = None,
    status: Optional[str] = None,
    conn: Optional[DatabaseConnection] = None
) -> List[Dict[str, Any]]:
    """Fetches all bookings in the system for admin audit."""
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        query = [
            """
            SELECT 
                b.booking_id, b.booking_reference, b.schedule_id, b.passenger_id,
                b.seat_number, b.booking_date, b.total_amount, b.total_amount AS amount,
                b.booking_status, b.booking_status AS status, b.cancelled_at AS cancellation_date,
                p.passenger_name, p.passenger_name AS full_name, p.age, p.gender, p.phone,
                s.departure_datetime, s.arrival_datetime,
                SUBSTR(s.departure_datetime, 1, 10) AS travel_date,
                SUBSTR(s.departure_datetime, 12, 5) AS departure_time,
                SUBSTR(s.arrival_datetime, 12, 5) AS arrival_time,
                s.base_fare AS fare, s.schedule_status,
                bs.registration_number AS bus_number, bs.bus_name, bs.bus_type,
                r.source, r.destination, r.distance AS distance_km,
                pm.payment_id, pm.payment_method, pm.payment_status, pm.payment_date, pm.transaction_reference,
                ref.refund_amount, ref.refund_status
            FROM bookings b
            INNER JOIN passengers p ON b.passenger_id = p.passenger_id
            INNER JOIN schedules s ON b.schedule_id = s.schedule_id
            INNER JOIN buses bs ON s.bus_id = bs.bus_id
            INNER JOIN routes r ON s.route_id = r.route_id
            LEFT JOIN payments pm ON b.booking_id = pm.booking_id
            LEFT JOIN refunds ref ON b.booking_id = ref.booking_id
            WHERE 1=1
            """
        ]
        params = []

        if search:
            query.append("AND (LOWER(b.booking_reference) LIKE %s OR LOWER(p.passenger_name) LIKE %s)")
            clean_search = f"%{search.strip().lower()}%"
            params.extend([clean_search, clean_search])

        if travel_date:
            query.append("AND SUBSTR(s.departure_datetime, 1, 10) = %s")
            params.append(travel_date)

        if status and status != "All":
            query.append("AND b.booking_status = %s")
            params.append(status.upper())

        query.append("ORDER BY b.booking_date DESC")
        cursor.execute(" ".join(query), params)
        return cursor.fetchall()
    finally:
        if close_after:
            conn.close()


def get_schedule_manifest(schedule_id: int, conn: Optional[DatabaseConnection] = None) -> List[Dict[str, Any]]:
    """Returns passenger manifest for conductor trip verification."""
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                bk.booking_id, bk.booking_reference, bk.seat_number, bk.booking_status,
                p.passenger_name, p.age, p.gender, p.phone,
                bs_b.stop_name AS boarding_stop, bs_d.stop_name AS dropping_stop,
                chk.checkin_status, chk.checkin_time
            FROM bookings bk
            JOIN passengers p ON bk.passenger_id = p.passenger_id
            LEFT JOIN bus_stops bs_b ON bk.boarding_stop_id = bs_b.stop_id
            LEFT JOIN bus_stops bs_d ON bk.dropping_stop_id = bs_d.stop_id
            LEFT JOIN ticket_checkins chk ON bk.booking_id = chk.booking_id
            WHERE bk.schedule_id = %s AND bk.booking_status <> 'CANCELLED'
            ORDER BY bk.seat_number ASC;
            """,
            (schedule_id,)
        )
        return cursor.fetchall()
    finally:
        if close_after:
            conn.close()
