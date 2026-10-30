"""
Bus repository for managing buses table.
Supports search, filtering, update, and soft-deactivation.
"""
import sqlite3
from typing import Any, Dict, List, Optional

from app.database import get_connection


def create_bus(
    bus_number: str,
    bus_name: str,
    bus_type: str,
    total_seats: int,
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
            INSERT INTO buses (bus_number, bus_name, bus_type, total_seats, is_active)
            VALUES (?, ?, ?, ?, 1);
            """,
            (bus_number.strip().upper(), bus_name.strip(), bus_type.strip(), total_seats)
        )
        bus_id = cursor.lastrowid
        if close_after:
            conn.commit()
        return bus_id
    finally:
        if close_after:
            conn.close()


def update_bus(
    bus_id: int,
    bus_number: str,
    bus_name: str,
    bus_type: str,
    total_seats: int,
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
            UPDATE buses
            SET bus_number = ?, bus_name = ?, bus_type = ?, total_seats = ?
            WHERE bus_id = ?;
            """,
            (bus_number.strip().upper(), bus_name.strip(), bus_type.strip(), total_seats, bus_id)
        )
        affected = cursor.rowcount > 0
        if close_after:
            conn.commit()
        return affected
    finally:
        if close_after:
            conn.close()


def set_bus_status(
    bus_id: int,
    is_active: int,
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
            UPDATE buses
            SET is_active = ?
            WHERE bus_id = ?;
            """,
            (1 if is_active else 0, bus_id)
        )
        affected = cursor.rowcount > 0
        if close_after:
            conn.commit()
        return affected
    finally:
        if close_after:
            conn.close()


def find_bus_by_id(bus_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[Dict[str, Any]]:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT bus_id, bus_number, bus_name, bus_type, total_seats, is_active
            FROM buses
            WHERE bus_id = ?;
            """,
            (bus_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        if close_after:
            conn.close()


def find_bus_by_number(bus_number: str, conn: Optional[sqlite3.Connection] = None) -> Optional[Dict[str, Any]]:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT bus_id, bus_number, bus_name, bus_type, total_seats, is_active
            FROM buses
            WHERE lower(bus_number) = lower(?);
            """,
            (bus_number.strip(),)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        if close_after:
            conn.close()


def list_buses(
    search: Optional[str] = None,
    bus_type: Optional[str] = None,
    is_active: Optional[int] = None,
    conn: Optional[sqlite3.Connection] = None
) -> List[Dict[str, Any]]:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        query = ["SELECT bus_id, bus_number, bus_name, bus_type, total_seats, is_active FROM buses WHERE 1=1"]
        params = []

        if search:
            query.append("AND (lower(bus_number) LIKE ? OR lower(bus_name) LIKE ?)")
            pattern = f"%{search.strip().lower()}%"
            params.extend([pattern, pattern])

        if bus_type and bus_type != "All":
            query.append("AND bus_type = ?")
            params.append(bus_type)

        if is_active is not None:
            query.append("AND is_active = ?")
            params.append(1 if is_active else 0)

        query.append("ORDER BY bus_name ASC")
        cursor.execute(" ".join(query), params)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        if close_after:
            conn.close()
