"""
Check-in repository for conductor ticket verification and boarding logging.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from app.database import get_connection, DatabaseConnection


def verify_and_checkin(
    booking_reference: str,
    conductor_id: int,
    boarding_stop_id: Optional[int] = None,
    conn: Optional[DatabaseConnection] = None
) -> Dict[str, Any]:
    """
    Verifies a digital ticket using booking reference or QR payload.
    Checks booking validity, ensures no duplicate checkin, and records check-in.
    """
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        clean_ref = booking_reference.strip().upper()

        # Fetch booking details
        cursor.execute(
            """
            SELECT bk.booking_id, bk.booking_reference, bk.schedule_id, bk.passenger_id,
                   bk.seat_number, bk.booking_status,
                   p.passenger_name, p.age, p.gender,
                   s.departure_datetime, r.source, r.destination, b.bus_name
            FROM bookings bk
            JOIN passengers p ON bk.passenger_id = p.passenger_id
            JOIN schedules s ON bk.schedule_id = s.schedule_id
            JOIN routes r ON s.route_id = r.route_id
            JOIN buses b ON s.bus_id = b.bus_id
            WHERE UPPER(bk.booking_reference) = %s;
            """,
            (clean_ref,)
        )
        booking = cursor.fetchone()

        if not booking:
            return {
                "success": False,
                "status": "NOT_FOUND",
                "message": f"Invalid ticket! No booking found for reference '{clean_ref}'."
            }

        if booking["booking_status"] == "CANCELLED":
            return {
                "success": False,
                "status": "CANCELLED",
                "message": f"Ticket {clean_ref} has been CANCELLED and is no longer valid for travel.",
                "booking": booking
            }

        # Check if already checked in
        cursor.execute(
            """
            SELECT chk.checkin_id, chk.checkin_time, u.full_name AS conductor_name
            FROM ticket_checkins chk
            JOIN users u ON chk.conductor_id = u.user_id
            WHERE chk.booking_id = %s;
            """,
            (booking["booking_id"],)
        )
        existing_checkin = cursor.fetchone()
        if existing_checkin:
            return {
                "success": False,
                "status": "ALREADY_CHECKED_IN",
                "message": f"ALREADY CHECKED IN at {existing_checkin['checkin_time']} by Conductor {existing_checkin['conductor_name']}.",
                "booking": booking,
                "checkin": existing_checkin
            }

        # Record verified checkin
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            """
            INSERT INTO ticket_checkins (booking_id, conductor_id, checkin_status, boarding_stop_id, checkin_time)
            VALUES (%s, %s, 'VERIFIED', %s, %s);
            """,
            (booking["booking_id"], conductor_id, boarding_stop_id, now_str)
        )
        checkin_id = cursor.lastrowid

        # Update booking status to CHECKED_IN
        cursor.execute(
            "UPDATE bookings SET booking_status = 'CHECKED_IN' WHERE booking_id = %s;",
            (booking["booking_id"],)
        )

        if close_after:
            conn.commit()

        return {
            "success": True,
            "status": "VERIFIED",
            "checkin_id": checkin_id,
            "checkin_time": now_str,
            "message": f"Boarding VERIFIED for Seat #{booking['seat_number']} ({booking['passenger_name']}).",
            "booking": booking
        }
    finally:
        if close_after:
            conn.close()


def list_conductor_checkins(conductor_id: int, conn: Optional[DatabaseConnection] = None) -> List[Dict[str, Any]]:
    """Returns history of ticket verifications performed by this conductor."""
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT chk.checkin_id, chk.checkin_time, chk.checkin_status,
                   bk.booking_reference, bk.seat_number, p.passenger_name,
                   r.source, r.destination, s.departure_datetime, b.bus_name
            FROM ticket_checkins chk
            JOIN bookings bk ON chk.booking_id = bk.booking_id
            JOIN passengers p ON bk.passenger_id = p.passenger_id
            JOIN schedules s ON bk.schedule_id = s.schedule_id
            JOIN routes r ON s.route_id = r.route_id
            JOIN buses b ON s.bus_id = b.bus_id
            WHERE chk.conductor_id = %s
            ORDER BY chk.checkin_time DESC;
            """,
            (conductor_id,)
        )
        return cursor.fetchall()
    finally:
        if close_after:
            conn.close()

