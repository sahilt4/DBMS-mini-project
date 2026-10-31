"""
Tests for waitlist priority queueing and automated allocations upon cancellation.
"""
import pytest
from app.repositories import booking_repository, schedule_repository, user_repository, waitlist_repository
from app.services import booking_service, cancellation_service, waitlist_service


def test_waitlist_queue_position_and_retrieval(temp_db):
    """Verify that multiple passengers joining waitlist receive incremental queue positions."""
    schedules = schedule_repository.search_schedules()
    sched = schedules[0]
    schedule_id = sched["schedule_id"]

    u1 = user_repository.find_by_username("rahul_sharma")
    u2 = user_repository.find_by_username("priya_patil")

    # Add u1
    res1 = waitlist_service.join_waitlist(schedule_id, u1["user_id"], preferred_seat_type="WINDOW")
    assert res1["success"] is True

    # Add u2
    res2 = waitlist_service.join_waitlist(schedule_id, u2["user_id"], preferred_seat_type="AISLE")
    assert res2["success"] is True
    assert res2["queue_position"] > res1["queue_position"]

    # Verify queue query
    wl_list = waitlist_service.get_schedule_waitlist(schedule_id)
    assert len(wl_list) >= 2
    assert wl_list[0]["queue_position"] <= wl_list[1]["queue_position"]
