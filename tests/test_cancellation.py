"""
Tests for cancellation workflow and authorization rules.
"""
import pytest
from app.services import booking_service, cancellation_service
from app.repositories import booking_repository, user_repository


def test_successful_cancellation_and_refund(temp_db):
    """Test standard cancellation workflow updating status and refund."""
    p1 = user_repository.find_by_username("rahul_sharma")
    bookings = booking_repository.get_passenger_bookings(p1["user_id"])
    assert len(bookings) > 0
    active_booking = next(b for b in bookings if b["status"] == "CONFIRMED")
    booking_id = active_booking["booking_id"]

    res = cancellation_service.cancel_booking(
        booking_id=booking_id,
        acting_user_id=p1["user_id"],
        is_admin=False,
        db_path=temp_db
    )

    assert res["status"] == "CANCELLED"
    assert res["cancellation_date"] is not None
    assert res["payment_status"] == "REFUNDED"


def test_unauthorized_cancellation_prevention(temp_db):
    """Ensure passenger A cannot cancel passenger B's reservation."""
    p1 = user_repository.find_by_username("rahul_sharma")
    p2 = user_repository.find_by_username("priya_patil")

    p1_bookings = booking_repository.get_passenger_bookings(p1["user_id"])
    target_booking = next(b for b in p1_bookings if b["status"] == "CONFIRMED")

    # Priya attempts to cancel Rahul's booking
    with pytest.raises(PermissionError, match="Access denied"):
        cancellation_service.cancel_booking(
            booking_id=target_booking["booking_id"],
            acting_user_id=p2["user_id"],
            is_admin=False,
            db_path=temp_db
        )


def test_admin_cancellation_authorization(temp_db):
    """Admin is authorized to cancel any user's booking."""
    p1 = user_repository.find_by_username("rahul_sharma")
    p1_bookings = booking_repository.get_passenger_bookings(p1["user_id"])
    target_booking = next(b for b in p1_bookings if b["status"] == "CONFIRMED")

    # Admin cancels
    res = cancellation_service.cancel_booking(
        booking_id=target_booking["booking_id"],
        acting_user_id=None,
        is_admin=True,
        db_path=temp_db
    )
    assert res["status"] == "CANCELLED"
