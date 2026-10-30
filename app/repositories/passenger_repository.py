"""
Passenger repository for managing passenger records linked to bookings or users.
"""
import sqlite3
from typing import Any, Dict, List, Optional

from app.database import get_connection


def create_passenger(
    full_name: str,
    age: int,
    gender: str,
    phone: str,
    user_id: Optional[int] = None,
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
            INSERT INTO passengers (user_id, full_name, age, gender, phone)
            VALUES (?, ?, ?, ?, ?);
            """,
            (user_id, full_name.strip(), age, gender.strip() if gender else None, phone.strip() if phone else None)
        )
        passenger_id = cursor.lastrowid
        if close_after:
            conn.commit()
        return passenger_id
    finally:
        if close_after:
            conn.close()


def find_passenger_by_id(passenger_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[Dict[str, Any]]:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT passenger_id, user_id, full_name, age, gender, phone, created_at
            FROM passengers
            WHERE passenger_id = ?;
            """,
            (passenger_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        if close_after:
            conn.close()


def find_passenger_by_user_id(user_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[Dict[str, Any]]:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT passenger_id, user_id, full_name, age, gender, phone, created_at
            FROM passengers
            WHERE user_id = ?
            ORDER BY passenger_id DESC
            LIMIT 1;
            """,
            (user_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        if close_after:
            conn.close()


def update_passenger(
    passenger_id: int,
    full_name: str,
    age: int,
    gender: str,
    phone: str,
    conn: Optional[sqlite3.Connection] = None
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
            SET full_name = ?, age = ?, gender = ?, phone = ?
            WHERE passenger_id = ?;
            """,
            (full_name.strip(), age, gender.strip(), phone.strip(), passenger_id)
        )
        affected = cursor.rowcount > 0
        if close_after:
            conn.commit()
        return affected
    finally:
        if close_after:
            conn.close()


def list_passengers(search: Optional[str] = None, conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        query = [
            """
            SELECT p.passenger_id, p.user_id, p.full_name, p.age, p.gender, p.phone, p.created_at,
                   u.username,
                   (SELECT COUNT(*) FROM bookings b WHERE b.passenger_id = p.passenger_id) AS total_bookings
            FROM passengers p
            LEFT JOIN users u ON p.user_id = u.user_id
            WHERE 1=1
            """
        ]
        params = []
        if search:
            query.append("AND (lower(p.full_name) LIKE ? OR lower(p.phone) LIKE ? OR lower(u.username) LIKE ?)")
            pat = f"%{search.strip().lower()}%"
            params.extend([pat, pat, pat])
        query.append("ORDER BY p.passenger_id DESC")

        cursor.execute(" ".join(query), params)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        if close_after:
            conn.close()
