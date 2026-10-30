"""
Tests for user authorization boundaries and data isolation.
"""
from app.repositories import booking_repository, user_repository


def test_passenger_booking_isolation(temp_db):
    """
    Verify that query for passenger A only returns passenger A's records,
    ensuring strict data isolation between passengers.
    """
    u1 = user_repository.find_by_username("rahul_sharma")
    u2 = user_repository.find_by_username("priya_patil")

    u1_bookings = booking_repository.get_passenger_bookings(u1["user_id"])
    u2_bookings = booking_repository.get_passenger_bookings(u2["user_id"])

    u1_refs = {b["booking_reference"] for b in u1_bookings}
    u2_refs = {b["booking_reference"] for b in u2_bookings}

    # Intersecting sets must be empty
    assert len(u1_refs.intersection(u2_refs)) == 0
    assert len(u1_bookings) > 0
    assert len(u2_bookings) > 0
