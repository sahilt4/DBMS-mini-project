"""
Route repository for managing bus routes table.
Validates city names and enforces uniqueness of active source-destination pairs.
"""
import sqlite3
from typing import Any, Dict, List, Optional

from app.database import get_connection


def create_route(
    source: str,
    destination: str,
    distance_km: float,
    conn: Optional[sqlite3.Connection] = None
) -> int:
    src = source.strip()
    dst = destination.strip()
    if src.lower() == dst.lower():
        raise ValueError("Source and destination cities cannot be identical.")
    if distance_km <= 0:
        raise ValueError("Distance must be greater than zero.")

    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO routes (source, destination, distance_km, is_active)
            VALUES (?, ?, ?, 1);
            """,
            (src, dst, distance_km)
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
    distance_km: float,
    conn: Optional[sqlite3.Connection] = None
) -> bool:
    src = source.strip()
    dst = destination.strip()
    if src.lower() == dst.lower():
        raise ValueError("Source and destination cities cannot be identical.")
    if distance_km <= 0:
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
            SET source = ?, destination = ?, distance_km = ?
            WHERE route_id = ?;
            """,
            (src, dst, distance_km, route_id)
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
            UPDATE routes
            SET is_active = ?
            WHERE route_id = ?;
            """,
            (1 if is_active else 0, route_id)
        )
        affected = cursor.rowcount > 0
        if close_after:
            conn.commit()
        return affected
    finally:
        if close_after:
            conn.close()


def find_route_by_id(route_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[Dict[str, Any]]:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT route_id, source, destination, distance_km, is_active
            FROM routes
            WHERE route_id = ?;
            """,
            (route_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        if close_after:
            conn.close()


def find_route_by_cities(source: str, destination: str, conn: Optional[sqlite3.Connection] = None) -> Optional[Dict[str, Any]]:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT route_id, source, destination, distance_km, is_active
            FROM routes
            WHERE lower(source) = lower(?) AND lower(destination) = lower(?);
            """,
            (source.strip(), destination.strip())
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        if close_after:
            conn.close()


def list_routes(
    search: Optional[str] = None,
    is_active: Optional[int] = None,
    conn: Optional[sqlite3.Connection] = None
) -> List[Dict[str, Any]]:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        query = ["SELECT route_id, source, destination, distance_km, is_active FROM routes WHERE 1=1"]
        params = []

        if search:
            query.append("AND (lower(source) LIKE ? OR lower(destination) LIKE ?)")
            pat = f"%{search.strip().lower()}%"
            params.extend([pat, pat])

        if is_active is not None:
            query.append("AND is_active = ?")
            params.append(1 if is_active else 0)

        query.append("ORDER BY source ASC, destination ASC")
        cursor.execute(" ".join(query), params)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        if close_after:
            conn.close()


def get_unique_sources(conn: Optional[sqlite3.Connection] = None) -> List[str]:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT source FROM routes WHERE is_active = 1 ORDER BY source ASC;")
        return [row["source"] for row in cursor.fetchall()]
    finally:
        if close_after:
            conn.close()


def get_unique_destinations(source: Optional[str] = None, conn: Optional[sqlite3.Connection] = None) -> List[str]:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        if source:
            cursor.execute(
                """
                SELECT DISTINCT destination
                FROM routes
                WHERE is_active = 1 AND lower(source) = lower(?)
                ORDER BY destination ASC;
                """,
                (source.strip(),)
            )
        else:
            cursor.execute("SELECT DISTINCT destination FROM routes WHERE is_active = 1 ORDER BY destination ASC;")
        return [row["destination"] for row in cursor.fetchall()]
    finally:
        if close_after:
            conn.close()
