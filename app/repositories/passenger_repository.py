"""
Passenger repository for managing passenger records linked to bookings or users.
"""
from typing import Any, Dict, List, Optional
from app.database import get_connection, DatabaseConnection


def create_passenger(
    full_name: str,
    age: int,
    gender: str,
    phone: str,
    user_id: Optional[int] = None,
    conn: Optional[DatabaseConnection] = None
) -> int:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        clean_name = full_name.strip()
        cursor.execute(
            """
            INSERT INTO passengers (user_id, full_name, passenger_name, age, gender, phone)
            VALUES (%s, %s, %s, %s, %s, %s);
            """,
            (user_id, clean_name, clean_name, age, gender.strip() if gender else "Other", phone.strip() if phone else None)
        )
        passenger_id = cursor.lastrowid
        if close_after:
            conn.commit()
        return passenger_id
    finally:
        if close_after:
            conn.close()


def find_passenger_by_id(passenger_id: int, conn: Optional[DatabaseConnection] = None) -> Optional[Dict[str, Any]]:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT passenger_id, user_id, passenger_name, passenger_name AS full_name,
                   age, gender, phone, created_at
            FROM passengers
            WHERE passenger_id = %s;
            """,
            (passenger_id,)
        )
        return cursor.fetchone()
    finally:
        if close_after:
            conn.close()


def find_passenger_by_user_id(user_id: int, conn: Optional[DatabaseConnection] = None) -> Optional[Dict[str, Any]]:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT passenger_id, user_id, passenger_name, passenger_name AS full_name,
                   age, gender, phone, created_at
            FROM passengers
            WHERE user_id = %s
            ORDER BY passenger_id DESC
            LIMIT 1;
            """,
            (user_id,)
        )
        return cursor.fetchone()
    finally:
        if close_after:
            conn.close()


def update_passenger(
    passenger_id: int,
    full_name: str,
    age: int,
    gender: str,
    phone: str,
    conn: Optional[DatabaseConnection] = None
) -> bool:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE passengers
            SET passenger_name = %s, age = %s, gender = %s, phone = %s
            WHERE passenger_id = %s;
            """,
            (full_name.strip(), age, gender.strip(), phone.strip() if phone else None, passenger_id)
        )
        if close_after:
            conn.commit()
        return cursor.rowcount > 0
    finally:
        if close_after:
            conn.close()


def list_passengers(conn: Optional[DatabaseConnection] = None) -> List[Dict[str, Any]]:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT passenger_id, user_id, passenger_name, passenger_name AS full_name,
                   age, gender, phone, created_at
            FROM passengers
            ORDER BY passenger_id DESC;
            """
        )
        return cursor.fetchall()
    finally:
        if close_after:
            conn.close()


def list_customers_with_metrics(conn: Optional[DatabaseConnection] = None) -> List[Dict[str, Any]]:
    """Fetches customer profiles with booking counts and spending for the Customer Management view."""
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                p.passenger_id, p.user_id,
                COALESCE(p.passenger_name, p.full_name) AS full_name,
                p.age, p.gender, p.phone, p.created_at,
                COALESCE(u.email, 'guest@easybus.com') AS email,
                COUNT(b.booking_id) AS total_bookings,
                COALESCE(SUM(CASE WHEN b.booking_status = 'CONFIRMED' OR b.status = 'CONFIRMED' THEN COALESCE(b.total_amount, b.amount) ELSE 0 END), 0.0) AS total_spent
            FROM passengers p
            LEFT JOIN users u ON p.user_id = u.user_id
            LEFT JOIN bookings b ON p.passenger_id = b.passenger_id
            GROUP BY p.passenger_id, p.user_id, p.passenger_name, p.full_name, p.age, p.gender, p.phone, p.created_at, u.email
            ORDER BY total_bookings DESC, p.passenger_id ASC;
            """
        )
        return cursor.fetchall()
    finally:
        if close_after:
            conn.close()


def get_customer_booking_history(passenger_id: int, conn: Optional[DatabaseConnection] = None) -> List[Dict[str, Any]]:
    """Retrieves the latest bookings for a specific customer."""
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                b.booking_id, b.booking_reference,
                COALESCE(b.booking_status, b.status) AS status,
                b.seat_number,
                COALESCE(b.total_amount, b.amount) AS amount,
                COALESCE(s.travel_date, SUBSTR(s.departure_datetime, 1, 10)) AS travel_date,
                COALESCE(s.departure_time, SUBSTR(s.departure_datetime, 12, 5)) AS departure_time,
                r.source, r.destination,
                buses.bus_name
            FROM bookings b
            JOIN schedules s ON b.schedule_id = s.schedule_id
            JOIN routes r ON s.route_id = r.route_id
            JOIN buses ON s.bus_id = buses.bus_id
            WHERE b.passenger_id = %s
            ORDER BY b.booking_id DESC
            LIMIT 6;
            """,
            (passenger_id,)
        )
        return cursor.fetchall()
    finally:
        if close_after:
            conn.close()

