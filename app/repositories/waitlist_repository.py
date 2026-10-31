"""
Waitlist repository for overbooked schedules and automated queue allocations.
"""
from typing import Any, Dict, List, Optional
from app.database import get_connection, DatabaseConnection


def add_to_waitlist(
    passenger_id: int,
    schedule_id: int,
    preferred_seat_type: str = "ANY",
    conn: Optional[DatabaseConnection] = None
) -> Dict[str, Any]:
    """Adds a passenger to the schedule waitlist and determines queue position."""
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        # Check if passenger already has active waitlist on this schedule
        cursor.execute(
            """
            SELECT waitlist_id, queue_position, waitlist_status 
            FROM waitlist 
            WHERE passenger_id = %s AND schedule_id = %s;
            """,
            (passenger_id, schedule_id)
        )
        existing = cursor.fetchone()
        if existing and existing["waitlist_status"] == "WAITING":
            return {
                "success": False,
                "message": f"Already on the waiting list at position #{existing['queue_position']}.",
                "queue_position": existing["queue_position"]
            }

        # Calculate next queue position
        cursor.execute(
            """
            SELECT COALESCE(MAX(queue_position), 0) + 1 AS next_pos
            FROM waitlist
            WHERE schedule_id = %s AND waitlist_status = 'WAITING';
            """,
            (schedule_id,)
        )
        next_pos = cursor.fetchone()["next_pos"]

        cursor.execute(
            """
            INSERT INTO waitlist (passenger_id, schedule_id, preferred_seat_type, queue_position, waitlist_status)
            VALUES (%s, %s, %s, %s, 'WAITING');
            """,
            (passenger_id, schedule_id, preferred_seat_type, next_pos)
        )
        wl_id = cursor.lastrowid
        if close_after:
            conn.commit()

        return {
            "success": True,
            "waitlist_id": wl_id,
            "queue_position": next_pos,
            "message": f"Added to waiting list successfully. Your position is #{next_pos}."
        }
    finally:
        if close_after:
            conn.close()


def get_waitlist_for_schedule(schedule_id: int, conn: Optional[DatabaseConnection] = None) -> List[Dict[str, Any]]:
    """Lists all waitlisted passengers for a schedule ordered by priority queue position."""
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT wl.waitlist_id, wl.passenger_id, wl.schedule_id, wl.preferred_seat_type,
                   wl.queue_position, wl.waitlist_status, wl.created_at,
                   p.passenger_name, p.age, p.gender, p.phone
            FROM waitlist wl
            JOIN passengers p ON wl.passenger_id = p.passenger_id
            WHERE wl.schedule_id = %s
            ORDER BY wl.queue_position ASC;
            """,
            (schedule_id,)
        )
        return cursor.fetchall()
    finally:
        if close_after:
            conn.close()


def get_passenger_waitlists(user_id: int, conn: Optional[DatabaseConnection] = None) -> List[Dict[str, Any]]:
    """Lists waitlist entries for a specific passenger user."""
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT wl.waitlist_id, wl.queue_position, wl.waitlist_status, wl.preferred_seat_type, wl.created_at,
                   p.passenger_name, r.source, r.destination,
                   s.departure_datetime, b.bus_name, b.bus_type
            FROM waitlist wl
            JOIN passengers p ON wl.passenger_id = p.passenger_id
            JOIN schedules s ON wl.schedule_id = s.schedule_id
            JOIN routes r ON s.route_id = r.route_id
            JOIN buses b ON s.bus_id = b.bus_id
            WHERE p.user_id = %s
            ORDER BY wl.created_at DESC;
            """,
            (user_id,)
        )
        return cursor.fetchall()
    finally:
        if close_after:
            conn.close()
