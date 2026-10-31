"""
Tests for Conductor digital QR verification, duplicate boarding prevention, and audit recording.
"""
import pytest
from app.repositories import booking_repository, user_repository
from app.services import verification_service


def test_conductor_ticket_verification(temp_db):
    """Test standard verification and boarding confirmation workflow."""
    cond = user_repository.find_by_username("conductor")
    assert cond is not None

    ref = "BUS-20261031-100002"
    # Booking 2 is confirmed and not yet checked in
    res = verification_service.verify_ticket(ref, conductor_id=cond["user_id"])
    assert res["success"] is True
    assert res["status"] == "VERIFIED"
    assert "checkin_id" in res


def test_duplicate_checkin_rejection(temp_db):
    """Ensure duplicate boarding check-in is flagged and prevented."""
    cond = user_repository.find_by_username("conductor")
    ref = "BUS-20261031-100001"  # Already checked in during seeding

    res = verification_service.verify_ticket(ref, conductor_id=cond["user_id"])
    assert res["success"] is False
    assert res["status"] == "ALREADY_CHECKED_IN"


def test_cancelled_ticket_verification_rejection(temp_db):
    """Ensure cancelled ticket cannot be verified for boarding."""
    cond = user_repository.find_by_username("conductor")
    ref = "BUS-20261031-100003"  # Cancelled booking in seed

    res = verification_service.verify_ticket(ref, conductor_id=cond["user_id"])
    assert res["success"] is False
    assert res["status"] == "CANCELLED"
