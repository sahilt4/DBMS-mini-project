"""
Cancellation transaction service for Smart Bus Reservation System.
Handles reservation cancellation, authorization verification, refund status updates,
and releases the seat back to the availability pool.
"""
from datetime import datetime
from pathlib import Path
import sqlite3
from typing import Any, Dict, Optional

import app.config as config
from app.database import get_connection, transaction
from app.repositories import booking_repository


def cancel_booking(
    booking_id: int,
    acting_user_id: Optional[int] = None,
    is_admin: bool = False,
    db_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Cancels an existing CONFIRMED booking in an atomic transaction.
    
    Authorization check:
    - If acting_user_id is provided and user is not admin, booking must belong to acting_user_id.
    - An admin can cancel any booking.
    
    Database actions:
    - Update booking status to 'CANCELLED'
    - Record cancellation timestamp
    - Update simulated payment status to 'REFUNDED'
    """
    booking = booking_repository.find_booking_by_id(booking_id, conn=get_connection(db_path or config.DB_PATH))
    if not booking:
        raise ValueError(f"Booking with ID {booking_id} was not found.")

    # 1. Authorization check
    if not is_admin and acting_user_id is not None:
        if booking["user_id"] != acting_user_id:
            raise PermissionError("Access denied: You are not authorized to cancel this reservation.")

    # 2. Eligibility check
    if booking["status"] == "CANCELLED":
        raise ValueError("This booking has already been cancelled.")

    if booking["schedule_status"] == "COMPLETED":
        raise ValueError("Cannot cancel a booking for a journey that has already been completed.")

    now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 3. Perform cancellation in explicit write transaction
    conn = get_connection(db_path or config.DB_PATH, autocommit_mode=True)
    try:
        with transaction(conn, mode="IMMEDIATE") as cursor:
            # Update booking status and timestamp
            cursor.execute(
                """
                UPDATE bookings
                SET status = 'CANCELLED', cancellation_date = ?
                WHERE booking_id = ?;
                """,
                (now_iso, booking_id)
            )

            # Update payment record to REFUNDED
            cursor.execute(
                """
                UPDATE payments
                SET payment_status = 'REFUNDED'
                WHERE booking_id = ?;
                """,
                (booking_id,)
            )

        # Retrieve updated booking record
        updated_booking = booking_repository.find_booking_by_id(booking_id, conn=conn)
        return updated_booking
    finally:
        conn.close()
