"""
Schedule repository for managing schedules table.
Performs SQL joins with buses and routes, calculates real-time seat availability,
and validates conflicting bus schedule intervals.
"""
from datetime import datetime
import sqlite3
from typing import Any, Dict, List, Optional

from app.database import get_connection


def check_bus_conflict(
    bus_id: int,
    travel_date: str,
    departure_time: str,
    arrival_time: str,
    exclude_schedule_id: Optional[int] = None,
    conn: Optional[sqlite3.Connection] = None
) -> bool:
    """
    Checks if a bus has an overlapping active schedule on the same travel date.
    Returns True if a conflict exists, False otherwise.
    Interval overlap check: (start1 < end2) and (end1 > start2).
    """
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        query = """
            SELECT schedule_id, travel_date, departure_time, arrival_time
            FROM schedules
            WHERE bus_id = ?
              AND travel_date = ?
              AND status <> 'CANCELLED'
        """
        params = [bus_id, travel_date]
        if exclude_schedule_id is not None:
            query += " AND schedule_id <> ?"
            params.append(exclude_schedule_id)

        cursor.execute(query, params)
        existing = cursor.fetchall()

        # Compare time strings (HH:MM)
        # Note: Handle overnight journeys where arrival_time < departure_time
        # For simplicity and standard validity, departure_time < arrival_time or overnight +24h
        for row in existing:
            e_dep = row["departure_time"]
            e_arr = row["arrival_time"]
            
            # If standard same-day:
            if not (arrival_time <= e_dep or departure_time >= e_arr):
                return True
        return False
    finally:
        if close_after:
            conn.close()


def create_schedule(
    bus_id: int,
    route_id: int,
    travel_date: str,
    departure_time: str,
    arrival_time: str,
    fare: float,
    status: str = "SCHEDULED",
    conn: Optional[sqlite3.Connection] = None
) -> int:
    if fare < 0:
        raise ValueError("Fare cannot be negative.")
    if check_bus_conflict(bus_id, travel_date, departure_time, arrival_time, conn=conn):
        raise ValueError("Bus is already scheduled for an overlapping journey on this date.")

    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO schedules (bus_id, route_id, travel_date, departure_time, arrival_time, fare, status)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (bus_id, route_id, travel_date, departure_time, arrival_time, fare, status)
        )
        schedule_id = cursor.lastrowid
        if close_after:
            conn.commit()
        return schedule_id
    finally:
        if close_after:
            conn.close()


def update_schedule(
    schedule_id: int,
    bus_id: int,
    route_id: int,
    travel_date: str,
    departure_time: str,
    arrival_time: str,
    fare: float,
    status: str,
    conn: Optional[sqlite3.Connection] = None
) -> bool:
    if fare < 0:
        raise ValueError("Fare cannot be negative.")

    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        # Check if schedule has confirmed bookings
        cursor.execute(
            "SELECT COUNT(*) AS cnt FROM bookings WHERE schedule_id = ? AND status = 'CONFIRMED';",
            (schedule_id,)
        )
        confirmed_count = cursor.fetchone()["cnt"]

        # Fetch current record to see if key parameters changed
        cursor.execute("SELECT bus_id, travel_date FROM schedules WHERE schedule_id = ?;", (schedule_id,))
        curr = cursor.fetchone()
        if not curr:
            return False

        if confirmed_count > 0:
            # Prevent altering bus, date or timings when active bookings exist
            if curr["bus_id"] != bus_id or curr["travel_date"] != travel_date:
                raise ValueError("Cannot alter bus or travel date when confirmed reservations exist.")

        if check_bus_conflict(bus_id, travel_date, departure_time, arrival_time, exclude_schedule_id=schedule_id, conn=conn):
            raise ValueError("Bus is already scheduled for an overlapping journey on this date.")

        cursor.execute(
            """
            UPDATE schedules
            SET bus_id = ?, route_id = ?, travel_date = ?, departure_time = ?, arrival_time = ?, fare = ?, status = ?
            WHERE schedule_id = ?;
            """,
            (bus_id, route_id, travel_date, departure_time, arrival_time, fare, status, schedule_id)
        )
        affected = cursor.rowcount > 0
        if close_after:
            conn.commit()
        return affected
    finally:
        if close_after:
            conn.close()


def set_schedule_status(
    schedule_id: int,
    status: str,
    conn: Optional[sqlite3.Connection] = None
) -> bool:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE schedules SET status = ? WHERE schedule_id = ?;",
            (status, schedule_id)
        )
        affected = cursor.rowcount > 0
        if close_after:
            conn.commit()
        return affected
    finally:
        if close_after:
            conn.close()


def find_schedule_by_id(schedule_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[Dict[str, Any]]:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                s.schedule_id, s.bus_id, s.route_id, s.travel_date, s.departure_time, s.arrival_time,
                s.fare, s.status, s.created_at,
                b.bus_number, b.bus_name, b.bus_type, b.total_seats, b.is_active AS bus_is_active,
                r.source, r.destination, r.distance_km, r.is_active AS route_is_active,
                (SELECT COUNT(*) FROM bookings bk WHERE bk.schedule_id = s.schedule_id AND bk.status = 'CONFIRMED') AS booked_seats,
                (b.total_seats - (SELECT COUNT(*) FROM bookings bk WHERE bk.schedule_id = s.schedule_id AND bk.status = 'CONFIRMED')) AS available_seats
            FROM schedules s
            INNER JOIN buses b ON s.bus_id = b.bus_id
            INNER JOIN routes r ON s.route_id = r.route_id
            WHERE s.schedule_id = ?;
            """,
            (schedule_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        if close_after:
            conn.close()


def search_schedules(
    source: Optional[str] = None,
    destination: Optional[str] = None,
    travel_date: Optional[str] = None,
    status: Optional[str] = "SCHEDULED",
    conn: Optional[sqlite3.Connection] = None
) -> List[Dict[str, Any]]:
    """
    Searches schedules matching source, destination, and travel date.
    Calculates remaining seat availability accurately from active confirmed bookings.
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
                s.schedule_id, s.bus_id, s.route_id, s.travel_date, s.departure_time, s.arrival_time,
                s.fare, s.status,
                b.bus_number, b.bus_name, b.bus_type, b.total_seats,
                r.source, r.destination, r.distance_km,
                (SELECT COUNT(*) FROM bookings bk WHERE bk.schedule_id = s.schedule_id AND bk.status = 'CONFIRMED') AS booked_seats,
                (b.total_seats - (SELECT COUNT(*) FROM bookings bk WHERE bk.schedule_id = s.schedule_id AND bk.status = 'CONFIRMED')) AS available_seats
            FROM schedules s
            INNER JOIN buses b ON s.bus_id = b.bus_id
            INNER JOIN routes r ON s.route_id = r.route_id
            WHERE b.is_active = 1 AND r.is_active = 1
            """
        ]
        params = []

        if source and source != "All":
            query.append("AND lower(r.source) = lower(?)")
            params.append(source.strip())

        if destination and destination != "All":
            query.append("AND lower(r.destination) = lower(?)")
            params.append(destination.strip())

        if travel_date:
            query.append("AND s.travel_date = ?")
            params.append(travel_date)

        if status:
            query.append("AND s.status = ?")
            params.append(status)

        query.append("ORDER BY s.travel_date ASC, s.departure_time ASC")
        cursor.execute(" ".join(query), params)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        if close_after:
            conn.close()


def list_all_schedules(
    travel_date: Optional[str] = None,
    status: Optional[str] = None,
    bus_id: Optional[int] = None,
    route_id: Optional[int] = None,
    conn: Optional[sqlite3.Connection] = None
) -> List[Dict[str, Any]]:
    """Lists all schedules for admin view with bus, route, and occupancy details."""
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        query = [
            """
            SELECT 
                s.schedule_id, s.bus_id, s.route_id, s.travel_date, s.departure_time, s.arrival_time,
                s.fare, s.status, s.created_at,
                b.bus_number, b.bus_name, b.bus_type, b.total_seats,
                r.source, r.destination, r.distance_km,
                (SELECT COUNT(*) FROM bookings bk WHERE bk.schedule_id = s.schedule_id AND bk.status = 'CONFIRMED') AS booked_seats,
                (b.total_seats - (SELECT COUNT(*) FROM bookings bk WHERE bk.schedule_id = s.schedule_id AND bk.status = 'CONFIRMED')) AS available_seats
            FROM schedules s
            INNER JOIN buses b ON s.bus_id = b.bus_id
            INNER JOIN routes r ON s.route_id = r.route_id
            WHERE 1=1
            """
        ]
        params = []

        if travel_date:
            query.append("AND s.travel_date = ?")
            params.append(travel_date)

        if status and status != "All":
            query.append("AND s.status = ?")
            params.append(status)

        if bus_id:
            query.append("AND s.bus_id = ?")
            params.append(bus_id)

        if route_id:
            query.append("AND s.route_id = ?")
            params.append(route_id)

        query.append("ORDER BY s.travel_date DESC, s.departure_time ASC")
        cursor.execute(" ".join(query), params)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        if close_after:
            conn.close()
