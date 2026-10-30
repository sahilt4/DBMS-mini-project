"""
Booking repository for managing bookings and simulated payments tables.
Handles seat queries, booking retrieval, cancellations, and status lookups.
"""
from datetime import datetime
import sqlite3
from typing import Any, Dict, List, Optional

from app.database import get_connection


def get_occupied_seats(schedule_id: int, conn: Optional[sqlite3.Connection] = None) -> List[int]:
    """
    Returns list of seat numbers that are currently CONFIRMED for the schedule.
    CANCELLED seats are released and not returned.
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
            FROM bookings
            WHERE schedule_id = ? AND status = 'CONFIRMED'
            ORDER BY seat_number ASC;
            """,
            (schedule_id,)
        )
        return [row["seat_number"] for row in cursor.fetchall()]
    finally:
        if close_after:
            conn.close()


def is_seat_available(schedule_id: int, seat_number: int, conn: Optional[sqlite3.Connection] = None) -> bool:
    """
    Checks if a specific seat is available on a given schedule.
    """
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM bookings
            WHERE schedule_id = ? AND seat_number = ? AND status = 'CONFIRMED';
            """,
            (schedule_id, seat_number)
        )
        return cursor.fetchone()["cnt"] == 0
    finally:
        if close_after:
            conn.close()


def create_booking(
    booking_reference: str,
    schedule_id: int,
    passenger_id: int,
    seat_number: int,
    amount: float,
    status: str = "CONFIRMED",
    conn: Optional[sqlite3.Connection] = None
) -> int:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO bookings (booking_reference, schedule_id, passenger_id, seat_number, amount, status)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (booking_reference, schedule_id, passenger_id, seat_number, amount, status)
        )
        booking_id = cursor.lastrowid
        if close_after:
            conn.commit()
        return booking_id
    finally:
        if close_after:
            conn.close()


def create_payment(
    booking_id: int,
    amount: float,
    payment_method: str,
    payment_status: str = "PAID",
    conn: Optional[sqlite3.Connection] = None
) -> int:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO payments (booking_id, amount, payment_method, payment_status)
            VALUES (?, ?, ?, ?);
            """,
            (booking_id, amount, payment_method, payment_status)
        )
        payment_id = cursor.lastrowid
        if close_after:
            conn.commit()
        return payment_id
    finally:
        if close_after:
            conn.close()


def find_booking_by_id(booking_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[Dict[str, Any]]:
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
                b.seat_number, b.booking_date, b.amount, b.status, b.cancellation_date,
                p.full_name, p.age, p.gender, p.phone, p.user_id,
                s.travel_date, s.departure_time, s.arrival_time, s.fare, s.status AS schedule_status,
                bs.bus_number, bs.bus_name, bs.bus_type,
                r.source, r.destination, r.distance_km,
                pm.payment_id, pm.payment_method, pm.payment_status, pm.payment_date
            FROM bookings b
            INNER JOIN passengers p ON b.passenger_id = p.passenger_id
            INNER JOIN schedules s ON b.schedule_id = s.schedule_id
            INNER JOIN buses bs ON s.bus_id = bs.bus_id
            INNER JOIN routes r ON s.route_id = r.route_id
            LEFT JOIN payments pm ON b.booking_id = pm.booking_id
            WHERE b.booking_id = ?;
            """,
            (booking_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        if close_after:
            conn.close()


def find_booking_by_ref(booking_ref: str, conn: Optional[sqlite3.Connection] = None) -> Optional[Dict[str, Any]]:
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
                b.seat_number, b.booking_date, b.amount, b.status, b.cancellation_date,
                p.full_name, p.age, p.gender, p.phone, p.user_id,
                s.travel_date, s.departure_time, s.arrival_time, s.fare, s.status AS schedule_status,
                bs.bus_number, bs.bus_name, bs.bus_type,
                r.source, r.destination, r.distance_km,
                pm.payment_id, pm.payment_method, pm.payment_status, pm.payment_date
            FROM bookings b
            INNER JOIN passengers p ON b.passenger_id = p.passenger_id
            INNER JOIN schedules s ON b.schedule_id = s.schedule_id
            INNER JOIN buses bs ON s.bus_id = bs.bus_id
            INNER JOIN routes r ON s.route_id = r.route_id
            LEFT JOIN payments pm ON b.booking_id = pm.booking_id
            WHERE lower(b.booking_reference) = lower(?);
            """,
            (booking_ref.strip(),)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        if close_after:
            conn.close()


def get_passenger_bookings(
    user_id: int,
    search_ref: Optional[str] = None,
    travel_date: Optional[str] = None,
    status: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None
) -> List[Dict[str, Any]]:
    """
    Fetches all bookings owned by a specific logged-in passenger user.
    Enforces authorization at database query level.
    """
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
                b.seat_number, b.booking_date, b.amount, b.status, b.cancellation_date,
                p.full_name, p.age, p.gender, p.phone,
                s.travel_date, s.departure_time, s.arrival_time,
                bs.bus_number, bs.bus_name, bs.bus_type,
                r.source, r.destination,
                pm.payment_method, pm.payment_status
            FROM bookings b
            INNER JOIN passengers p ON b.passenger_id = p.passenger_id
            INNER JOIN schedules s ON b.schedule_id = s.schedule_id
            INNER JOIN buses bs ON s.bus_id = bs.bus_id
            INNER JOIN routes r ON s.route_id = r.route_id
            LEFT JOIN payments pm ON b.booking_id = pm.booking_id
            WHERE p.user_id = ?
            """
        ]
        params = [user_id]

        if search_ref:
            query.append("AND lower(b.booking_reference) LIKE ?")
            params.append(f"%{search_ref.strip().lower()}%")

        if travel_date:
            query.append("AND s.travel_date = ?")
            params.append(travel_date)

        if status and status != "All":
            query.append("AND b.status = ?")
            params.append(status)

        query.append("ORDER BY b.booking_date DESC")
        cursor.execute(" ".join(query), params)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        if close_after:
            conn.close()


def get_all_bookings(
    search: Optional[str] = None,
    travel_date: Optional[str] = None,
    status: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None
) -> List[Dict[str, Any]]:
    """
    Admin lookup for all bookings across the entire system.
    """
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
                b.seat_number, b.booking_date, b.amount, b.status, b.cancellation_date,
                p.full_name, p.phone, u.username,
                s.travel_date, s.departure_time, s.arrival_time,
                bs.bus_number, bs.bus_name, bs.bus_type,
                r.source, r.destination,
                pm.payment_method, pm.payment_status
            FROM bookings b
            INNER JOIN passengers p ON b.passenger_id = p.passenger_id
            LEFT JOIN users u ON p.user_id = u.user_id
            INNER JOIN schedules s ON b.schedule_id = s.schedule_id
            INNER JOIN buses bs ON s.bus_id = bs.bus_id
            INNER JOIN routes r ON s.route_id = r.route_id
            LEFT JOIN payments pm ON b.booking_id = pm.booking_id
            WHERE 1=1
            """
        ]
        params = []

        if search:
            query.append(
                "AND (lower(b.booking_reference) LIKE ? OR lower(p.full_name) LIKE ? OR lower(r.source) LIKE ? OR lower(r.destination) LIKE ?)"
            )
            pat = f"%{search.strip().lower()}%"
            params.extend([pat, pat, pat, pat])

        if travel_date:
            query.append("AND s.travel_date = ?")
            params.append(travel_date)

        if status and status != "All":
            query.append("AND b.status = ?")
            params.append(status)

        query.append("ORDER BY b.booking_date DESC")
        cursor.execute(" ".join(query), params)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        if close_after:
            conn.close()
