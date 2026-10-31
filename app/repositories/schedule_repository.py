"""
Schedule repository for managing schedules table and schedule_seats inventory.
Performs SQL joins with buses and routes, uses authoritative schedule_seats inventory,
and validates conflicting bus schedule intervals.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.database import get_connection, DatabaseConnection


def check_bus_conflict(
    bus_id: int,
    departure_datetime: str,
    arrival_datetime: str,
    exclude_schedule_id: Optional[int] = None,
    conn: Optional[DatabaseConnection] = None
) -> bool:
    """
    Checks if a bus has an overlapping active schedule.
    Interval overlap condition: (start1 < end2) and (end1 > start2).
    """
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        query = """
            SELECT schedule_id, departure_datetime, arrival_datetime
            FROM schedules
            WHERE bus_id = %s
              AND schedule_status <> 'CANCELLED'
              AND NOT (arrival_datetime <= %s OR departure_datetime >= %s)
        """
        params = [bus_id, departure_datetime, arrival_datetime]
        if exclude_schedule_id is not None:
            query += " AND schedule_id <> %s"
            params.append(exclude_schedule_id)

        cursor.execute(query, params)
        conflicts = cursor.fetchall()
        return len(conflicts) > 0
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
    conn: Optional[DatabaseConnection] = None
) -> int:
    if fare < 0:
        raise ValueError("Fare cannot be negative.")

    # Format datetime strings YYYY-MM-DD HH:MM:SS
    dep_dt = f"{travel_date} {departure_time}:00" if len(departure_time) <= 5 else departure_time
    arr_dt = f"{travel_date} {arrival_time}:00" if len(arrival_time) <= 5 else arrival_time

    if check_bus_conflict(bus_id, dep_dt, arr_dt, conn=conn):
        raise ValueError("Bus is already scheduled for an overlapping journey on this date/time.")

    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO schedules (bus_id, route_id, departure_datetime, arrival_datetime, base_fare, schedule_status)
            VALUES (%s, %s, %s, %s, %s, %s);
            """,
            (bus_id, route_id, dep_dt, arr_dt, fare, status.upper())
        )
        schedule_id = cursor.lastrowid

        # Generate schedule_seats inventory
        cursor.execute("SELECT capacity, bus_type FROM buses WHERE bus_id = %s;", (bus_id,))
        b_info = cursor.fetchone()
        if b_info:
            cap = b_info["capacity"]
            btype = b_info["bus_type"]
            for s_num in range(1, cap + 1):
                if "Sleeper" in btype:
                    stype = "SLEEPER_LOWER" if (s_num % 2 == 1) else "SLEEPER_UPPER"
                else:
                    stype = "WINDOW" if (s_num % 4 in (1, 0)) else "AISLE"

                cursor.execute(
                    """
                    INSERT INTO schedule_seats (schedule_id, seat_number, seat_type, seat_status)
                    VALUES (%s, %s, %s, 'AVAILABLE');
                    """,
                    (schedule_id, s_num, stype)
                )

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
    conn: Optional[DatabaseConnection] = None
) -> bool:
    if fare < 0:
        raise ValueError("Fare cannot be negative.")

    dep_dt = f"{travel_date} {departure_time}:00" if len(departure_time) <= 5 else departure_time
    arr_dt = f"{travel_date} {arrival_time}:00" if len(arrival_time) <= 5 else arrival_time

    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        # Check if schedule has active confirmed bookings
        cursor.execute(
            "SELECT COUNT(*) AS cnt FROM bookings WHERE schedule_id = %s AND booking_status = 'CONFIRMED';",
            (schedule_id,)
        )
        row = cursor.fetchone()
        confirmed_count = row["cnt"] if row else 0

        cursor.execute("SELECT bus_id, departure_datetime FROM schedules WHERE schedule_id = %s;", (schedule_id,))
        curr = cursor.fetchone()
        if not curr:
            return False

        if confirmed_count > 0:
            if curr["bus_id"] != bus_id:
                raise ValueError("Cannot alter bus assignment when active bookings exist.")

        if check_bus_conflict(bus_id, dep_dt, arr_dt, exclude_schedule_id=schedule_id, conn=conn):
            raise ValueError("Bus is already scheduled for an overlapping journey on this date/time.")

        cursor.execute(
            """
            UPDATE schedules
            SET bus_id = %s, route_id = %s, departure_datetime = %s, arrival_datetime = %s, base_fare = %s, schedule_status = %s
            WHERE schedule_id = %s;
            """,
            (bus_id, route_id, dep_dt, arr_dt, fare, status.upper(), schedule_id)
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
    conn: Optional[DatabaseConnection] = None
) -> bool:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE schedules SET schedule_status = %s WHERE schedule_id = %s;",
            (status.upper(), schedule_id)
        )
        affected = cursor.rowcount > 0
        if close_after:
            conn.commit()
        return affected
    finally:
        if close_after:
            conn.close()


def find_schedule_by_id(schedule_id: int, conn: Optional[DatabaseConnection] = None) -> Optional[Dict[str, Any]]:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                s.schedule_id, s.bus_id, s.route_id,
                s.departure_datetime, s.arrival_datetime,
                SUBSTR(s.departure_datetime, 1, 10) AS travel_date,
                SUBSTR(s.departure_datetime, 12, 5) AS departure_time,
                SUBSTR(s.arrival_datetime, 12, 5) AS arrival_time,
                s.base_fare, s.base_fare AS fare,
                s.schedule_status, s.schedule_status AS status, s.created_at,
                b.registration_number, b.registration_number AS bus_number,
                b.bus_name, b.bus_type, b.capacity AS total_seats,
                r.source, r.destination, r.distance AS distance_km,
                (SELECT COUNT(*) FROM schedule_seats ss WHERE ss.schedule_id = s.schedule_id AND ss.seat_status = 'BOOKED') AS booked_seats,
                (SELECT COUNT(*) FROM schedule_seats ss WHERE ss.schedule_id = s.schedule_id AND ss.seat_status = 'AVAILABLE') AS available_seats
            FROM schedules s
            INNER JOIN buses b ON s.bus_id = b.bus_id
            INNER JOIN routes r ON s.route_id = r.route_id
            WHERE s.schedule_id = %s;
            """,
            (schedule_id,)
        )
        return cursor.fetchone()
    finally:
        if close_after:
            conn.close()


def search_schedules(
    source: Optional[str] = None,
    destination: Optional[str] = None,
    travel_date: Optional[str] = None,
    status: Optional[str] = "SCHEDULED",
    conn: Optional[DatabaseConnection] = None
) -> List[Dict[str, Any]]:
    """
    Searches schedules matching source, destination, and travel date.
    Calculates remaining seat availability accurately from authoritative schedule_seats.
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
                s.schedule_id, s.bus_id, s.route_id,
                s.departure_datetime, s.arrival_datetime,
                SUBSTR(s.departure_datetime, 1, 10) AS travel_date,
                SUBSTR(s.departure_datetime, 12, 5) AS departure_time,
                SUBSTR(s.arrival_datetime, 12, 5) AS arrival_time,
                s.base_fare, s.base_fare AS fare,
                s.schedule_status, s.schedule_status AS status,
                b.registration_number, b.registration_number AS bus_number,
                b.bus_name, b.bus_type, b.capacity AS total_seats,
                r.source, r.destination, r.distance AS distance_km,
                (SELECT COUNT(*) FROM schedule_seats ss WHERE ss.schedule_id = s.schedule_id AND ss.seat_status = 'BOOKED') AS booked_seats,
                (SELECT COUNT(*) FROM schedule_seats ss WHERE ss.schedule_id = s.schedule_id AND ss.seat_status = 'AVAILABLE') AS available_seats
            FROM schedules s
            INNER JOIN buses b ON s.bus_id = b.bus_id
            INNER JOIN routes r ON s.route_id = r.route_id
            WHERE b.operational_status = 'ACTIVE' AND r.route_status = 'ACTIVE'
            """
        ]
        params = []

        if source and source != "All":
            query.append("AND LOWER(r.source) LIKE %s")
            params.append(f"%{source.strip().lower()}%")

        if destination and destination != "All":
            query.append("AND LOWER(r.destination) LIKE %s")
            params.append(f"%{destination.strip().lower()}%")

        if travel_date:
            query.append("AND SUBSTR(s.departure_datetime, 1, 10) = %s")
            params.append(travel_date)

        if status:
            query.append("AND s.schedule_status = %s")
            params.append(status.upper())

        query.append("ORDER BY s.departure_datetime ASC")
        cursor.execute(" ".join(query), params)
        return cursor.fetchall()
    finally:
        if close_after:
            conn.close()


def list_all_schedules(
    travel_date: Optional[str] = None,
    status: Optional[str] = None,
    bus_id: Optional[int] = None,
    route_id: Optional[int] = None,
    conn: Optional[DatabaseConnection] = None
) -> List[Dict[str, Any]]:
    """Lists all schedules for admin and conductor view."""
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        query = [
            """
            SELECT 
                s.schedule_id, s.bus_id, s.route_id,
                s.departure_datetime, s.arrival_datetime,
                SUBSTR(s.departure_datetime, 1, 10) AS travel_date,
                SUBSTR(s.departure_datetime, 12, 5) AS departure_time,
                SUBSTR(s.arrival_datetime, 12, 5) AS arrival_time,
                s.base_fare, s.base_fare AS fare,
                s.schedule_status, s.schedule_status AS status, s.created_at,
                b.registration_number, b.registration_number AS bus_number,
                b.bus_name, b.bus_type, b.capacity AS total_seats,
                r.source, r.destination, r.distance AS distance_km,
                (SELECT COUNT(*) FROM schedule_seats ss WHERE ss.schedule_id = s.schedule_id AND ss.seat_status = 'BOOKED') AS booked_seats,
                (SELECT COUNT(*) FROM schedule_seats ss WHERE ss.schedule_id = s.schedule_id AND ss.seat_status = 'AVAILABLE') AS available_seats
            FROM schedules s
            INNER JOIN buses b ON s.bus_id = b.bus_id
            INNER JOIN routes r ON s.route_id = r.route_id
            WHERE 1=1
            """
        ]
        params = []

        if travel_date:
            query.append("AND SUBSTR(s.departure_datetime, 1, 10) = %s")
            params.append(travel_date)

        if status and status != "All":
            query.append("AND s.schedule_status = %s")
            params.append(status.upper())

        if bus_id:
            query.append("AND s.bus_id = %s")
            params.append(bus_id)

        if route_id:
            query.append("AND s.route_id = %s")
            params.append(route_id)

        query.append("ORDER BY s.departure_datetime DESC")
        cursor.execute(" ".join(query), params)
        return cursor.fetchall()
    finally:
        if close_after:
            conn.close()


def get_schedule_seats(schedule_id: int, conn: Optional[DatabaseConnection] = None) -> List[Dict[str, Any]]:
    """Fetches seat inventory for visual seat map."""
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT schedule_seat_id, schedule_id, seat_number, seat_type, seat_status
            FROM schedule_seats
            WHERE schedule_id = %s
            ORDER BY seat_number ASC;
            """,
            (schedule_id,)
        )
        return cursor.fetchall()
    finally:
        if close_after:
            conn.close()
