"""
Route repository for managing bus routes and intermediate stops.
Validates city names and manages stops catalog.
"""
from typing import Any, Dict, List, Optional
from app.database import get_connection, DatabaseConnection


def create_route(
    source: str,
    destination: str,
    distance: float,
    estimated_duration: int = 180,
    route_status: str = "ACTIVE",
    conn: Optional[DatabaseConnection] = None
) -> int:
    src = source.strip()
    dst = destination.strip()
    if src.lower() == dst.lower():
        raise ValueError("Source and destination cities cannot be identical.")
    if distance <= 0:
        raise ValueError("Distance must be greater than zero.")

    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO routes (source, destination, distance, estimated_duration, route_status)
            VALUES (%s, %s, %s, %s, %s);
            """,
            (src, dst, distance, estimated_duration, route_status.upper())
        )
        route_id = cursor.lastrowid
        if close_after:
            conn.commit()
        return route_id
    finally:
        if close_after:
            conn.close()


def update_route(
    route_id: int,
    source: str,
    destination: str,
    distance: float,
    estimated_duration: int = 180,
    route_status: str = "ACTIVE",
    conn: Optional[DatabaseConnection] = None
) -> bool:
    src = source.strip()
    dst = destination.strip()
    if src.lower() == dst.lower():
        raise ValueError("Source and destination cities cannot be identical.")
    if distance <= 0:
        raise ValueError("Distance must be greater than zero.")

    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE routes
            SET source = %s, destination = %s, distance = %s, estimated_duration = %s, route_status = %s
            WHERE route_id = %s;
            """,
            (src, dst, distance, estimated_duration, route_status.upper(), route_id)
        )
        affected = cursor.rowcount > 0
        if close_after:
            conn.commit()
        return affected
    finally:
        if close_after:
            conn.close()


def set_route_status(
    route_id: int,
    is_active: int,
    conn: Optional[DatabaseConnection] = None
) -> bool:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        status_str = "ACTIVE" if is_active else "INACTIVE"
        cursor.execute(
            """
            UPDATE routes
            SET route_status = %s
            WHERE route_id = %s;
            """,
            (status_str, route_id)
        )
        affected = cursor.rowcount > 0
        if close_after:
            conn.commit()
        return affected
    finally:
        if close_after:
            conn.close()


def find_route_by_id(route_id: int, conn: Optional[DatabaseConnection] = None) -> Optional[Dict[str, Any]]:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT route_id, source, destination, distance, distance AS distance_km,
                   estimated_duration, route_status,
                   CASE WHEN route_status = 'ACTIVE' THEN 1 ELSE 0 END AS is_active
            FROM routes
            WHERE route_id = %s;
            """,
            (route_id,)
        )
        return cursor.fetchone()
    finally:
        if close_after:
            conn.close()


def list_routes(
    active_only: Optional[bool] = None,
    is_active: Optional[Any] = None,
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
            conditions.append("(LOWER(source) LIKE %s OR LOWER(destination) LIKE %s)")
            params.extend([f"%{search.strip().lower()}%", f"%{search.strip().lower()}%"])
        if is_active is not None and is_active != "All":
            if is_active is True or is_active == 1 or is_active == "ACTIVE":
                conditions.append("route_status = 'ACTIVE'")
            elif is_active is False or is_active == 0 or is_active == "INACTIVE":
                conditions.append("route_status <> 'ACTIVE'")
        elif active_only is True:
            conditions.append("route_status = 'ACTIVE'")

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"""
            SELECT route_id, source, destination, distance, distance AS distance_km,
                   estimated_duration, route_status,
                   CASE WHEN route_status = 'ACTIVE' THEN 1 ELSE 0 END AS is_active
            FROM routes
            {where_clause}
            ORDER BY source, destination;
        """
        cursor.execute(query, params)
        return cursor.fetchall()
    finally:
        if close_after:
            conn.close()


def get_unique_sources(conn: Optional[DatabaseConnection] = None) -> List[str]:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT source FROM routes WHERE route_status = 'ACTIVE' ORDER BY source ASC;")
        return [row["source"] for row in cursor.fetchall()]
    finally:
        if close_after:
            conn.close()


def get_unique_destinations(conn: Optional[DatabaseConnection] = None) -> List[str]:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT destination FROM routes WHERE route_status = 'ACTIVE' ORDER BY destination ASC;")
        return [row["destination"] for row in cursor.fetchall()]
    finally:
        if close_after:
            conn.close()


# ----------------------------------------------------------------------------
# BUS STOPS & ROUTE STOPS (Intermediate Points)
# ----------------------------------------------------------------------------

def list_bus_stops(conn: Optional[DatabaseConnection] = None) -> List[Dict[str, Any]]:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT stop_id, stop_name, city, address FROM bus_stops ORDER BY city, stop_name;")
        return cursor.fetchall()
    finally:
        if close_after:
            conn.close()


def get_route_stops(route_id: int, conn: Optional[DatabaseConnection] = None) -> List[Dict[str, Any]]:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT rs.route_stop_id, rs.route_id, rs.stop_id, rs.stop_sequence,
                   rs.distance_from_origin, rs.arrival_offset_minutes,
                   bs.stop_name, bs.city, bs.address
            FROM route_stops rs
            JOIN bus_stops bs ON rs.stop_id = bs.stop_id
            WHERE rs.route_id = %s
            ORDER BY rs.stop_sequence ASC;
            """,
            (route_id,)
        )
        return cursor.fetchall()
    finally:
        if close_after:
            conn.close()


def add_route_stop(
    route_id: int,
    stop_id: int,
    stop_sequence: int,
    distance_from_origin: float = 0.0,
    arrival_offset_minutes: int = 0,
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
            INSERT INTO route_stops (route_id, stop_id, stop_sequence, distance_from_origin, arrival_offset_minutes)
            VALUES (%s, %s, %s, %s, %s);
            """,
            (route_id, stop_id, stop_sequence, distance_from_origin, arrival_offset_minutes)
        )
        rs_id = cursor.lastrowid
        if close_after:
            conn.commit()
        return rs_id
    finally:
        if close_after:
            conn.close()
