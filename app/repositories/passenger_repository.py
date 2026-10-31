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
