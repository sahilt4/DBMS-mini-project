"""
Bus repository for managing buses table.
Supports search, filtering, update, and status toggling across MySQL and SQLite.
"""
from typing import Any, Dict, List, Optional
from app.database import get_connection, DatabaseConnection


def create_bus(
    registration_number: str,
    bus_name: str,
    bus_type: str,
    capacity: int,
    operational_status: str = "ACTIVE",
    conn: Optional[DatabaseConnection] = None
) -> int:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO buses (registration_number, bus_name, bus_type, capacity, operational_status)
            VALUES (%s, %s, %s, %s, %s);
            """,
            (registration_number.strip().upper(), bus_name.strip(), bus_type.strip(), capacity, operational_status.upper())
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
    registration_number: str,
    bus_name: str,
    bus_type: str,
    capacity: int,
    operational_status: str = "ACTIVE",
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
            UPDATE buses
            SET registration_number = %s, bus_name = %s, bus_type = %s, capacity = %s, operational_status = %s
            WHERE bus_id = %s;
            """,
            (registration_number.strip().upper(), bus_name.strip(), bus_type.strip(), capacity, operational_status.upper(), bus_id)
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
    conn: Optional[DatabaseConnection] = None
) -> bool:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        status_str = "ACTIVE" if is_active else "DECOMMISSIONED"
        cursor.execute(
            """
            UPDATE buses
            SET operational_status = %s
            WHERE bus_id = %s;
            """,
            (status_str, bus_id)
        )
        affected = cursor.rowcount > 0
        if close_after:
            conn.commit()
        return affected
    finally:
        if close_after:
            conn.close()


def find_bus_by_id(bus_id: int, conn: Optional[DatabaseConnection] = None) -> Optional[Dict[str, Any]]:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT bus_id, registration_number, registration_number AS bus_number,
                   bus_name, bus_type, capacity, capacity AS total_seats,
                   operational_status,
                   CASE WHEN operational_status = 'ACTIVE' THEN 1 ELSE 0 END AS is_active
            FROM buses
            WHERE bus_id = %s;
            """,
            (bus_id,)
        )
        return cursor.fetchone()
    finally:
        if close_after:
            conn.close()


def list_buses(
    active_only: Optional[bool] = None,
    is_active: Optional[Any] = None,
    bus_type: Optional[str] = None,
    search: Optional[str] = None,
    conn: Optional[DatabaseConnection] = None,
    **kwargs
) -> List[Dict[str, Any]]:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        conditions = []
        params = []
        if search:
            conditions.append("(LOWER(registration_number) LIKE %s OR LOWER(bus_name) LIKE %s)")
            params.extend([f"%{search.strip().lower()}%", f"%{search.strip().lower()}%"])
        if bus_type and bus_type != "All":
            conditions.append("bus_type = %s")
            params.append(bus_type)
        if is_active is not None and is_active != "All":
            if is_active is True or is_active == 1 or is_active == "ACTIVE":
                conditions.append("operational_status = 'ACTIVE'")
            elif is_active is False or is_active == 0 or is_active == "INACTIVE":
                conditions.append("operational_status <> 'ACTIVE'")
        elif active_only is True:
            conditions.append("operational_status = 'ACTIVE'")

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"""
            SELECT bus_id, registration_number, registration_number AS bus_number,
                   bus_name, bus_type, capacity, capacity AS total_seats,
                   operational_status,
                   CASE WHEN operational_status = 'ACTIVE' THEN 1 ELSE 0 END AS is_active
            FROM buses
            {where_clause}
            ORDER BY bus_name ASC;
        """
        cursor.execute(query, params)
        return cursor.fetchall()
    finally:
        if close_after:
            conn.close()
