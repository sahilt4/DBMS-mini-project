"""
Cancellation transaction service for Bus Reservation and Management System (BRMS).
Handles cancellation, authorization checks, automated tiered refund calculation,
and automatic waitlist allocation upon seat release.
"""
from typing import Any, Dict, Optional
from pathlib import Path

import app.config as config
from app.database import get_connection
from app.repositories import booking_repository


def cancel_booking(
    booking_id: int,
    acting_user_id: Optional[int] = None,
    is_admin: bool = False,
    reason: str = "Customer requested cancellation",
    db_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Cancels an existing CONFIRMED booking in an atomic transaction:
    - Authorization check (passenger can only cancel own booking, admin can cancel any)
    - Releases seat in schedule_seats inventory
    - Computes refund tier based on departure time
    - Inserts refund record
    - Triggers waitlist allocation
    """
    conn = get_connection(db_path or config.DB_PATH)
    try:
        booking = booking_repository.find_booking_by_id(booking_id, conn=conn)
        if not booking:
            raise ValueError(f"Booking with ID {booking_id} was not found.")

        # 1. Authorization check
        if not is_admin and acting_user_id is not None:
            if booking.get("user_id") != acting_user_id:
                raise PermissionError("Access denied: You are not authorized to cancel this reservation.")

        # 2. Status checks
        if booking["status"] == "CANCELLED":
            raise ValueError("This booking has already been cancelled.")

        if booking["schedule_status"] == "COMPLETED":
            raise ValueError("Cannot cancel a booking for a journey that has already been completed.")

        # 3. Atomic cancellation & refund calculation
        res = booking_repository.cancel_booking_atomic(
            booking_id=booking_id,
            reason=reason,
            conn=conn
        )

        updated = booking_repository.find_booking_by_id(booking_id, conn=conn)
        if updated:
            updated["refund_amount"] = res["refund_amount"]
            return updated
        return res
    finally:
        conn.close()
