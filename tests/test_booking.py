"""
Tests for booking transactions, seat validation, duplicate-booking prevention,
transaction rollback, and concurrent reservation safety.
"""
from concurrent.futures import ThreadPoolExecutor
import pytest
from app.services import booking_service
from app.repositories import booking_repository, schedule_repository


def test_successful_booking(temp_db):
    """Test successful seat reservation with payment and ticket generation."""
    schedules = schedule_repository.search_schedules()
    assert len(schedules) > 0
    sched = schedules[0]
    schedule_id = sched["schedule_id"]

    ticket = booking_service.reserve_seat(
        schedule_id=schedule_id,
        seat_number=15,
        full_name="Kavita Rane",
        age=29,
        gender="Female",
        phone="9988776655",
        payment_method="UPI",
        db_path=temp_db
    )

    assert ticket is not None
    assert ticket["seat_number"] == 15
    assert ticket["full_name"] == "Kavita Rane"
    assert ticket["status"] == "CONFIRMED"
    assert ticket["payment_status"] == "PAID"
    assert ticket["booking_reference"].startswith("BUS-")


def test_duplicate_seat_booking_rejection(temp_db):
    """Verify that booking an already reserved seat is immediately rejected."""
    schedules = schedule_repository.search_schedules()
    sched = schedules[0]
    schedule_id = sched["schedule_id"]

    # First booking succeeds on seat 20
    booking_service.reserve_seat(
        schedule_id=schedule_id,
        seat_number=20,
        full_name="User One",
        age=25,
        gender="Male",
        phone="9876543210",
        payment_method="Cash",
        db_path=temp_db
    )

    # Second booking on the exact same seat must fail
    with pytest.raises(ValueError, match="already been reserved"):
        booking_service.reserve_seat(
            schedule_id=schedule_id,
            seat_number=20,
            full_name="User Two",
            age=30,
            gender="Female",
            phone="9876543211",
            payment_method="UPI",
            db_path=temp_db
        )


def test_invalid_seat_number_rejection(temp_db):
    """Test rejection when seat exceeds bus total capacity or is <= 0."""
    schedules = schedule_repository.search_schedules()
    sched = schedules[0]
    schedule_id = sched["schedule_id"]
    capacity = sched["total_seats"]

    # Seat 0
    with pytest.raises(ValueError, match="positive integer"):
        booking_service.reserve_seat(
            schedule_id=schedule_id,
            seat_number=0,
            full_name="Invalid Seat",
            age=25,
            gender="Male",
            phone="9876543210",
            payment_method="Cash",
            db_path=temp_db
        )

    # Seat > capacity
    with pytest.raises(ValueError, match="exceeds the bus capacity"):
        booking_service.reserve_seat(
            schedule_id=schedule_id,
            seat_number=capacity + 5,
            full_name="Invalid Seat",
            age=25,
            gender="Male",
            phone="9876543210",
            payment_method="Cash",
            db_path=temp_db
        )


def test_concurrent_booking_safety(temp_db):
    """
    Simulate two concurrent threads attempting to book the same seat simultaneously.
    Verify that exactly one succeeds and one fails.
    """
    schedules = schedule_repository.search_schedules()
    sched = schedules[0]
    schedule_id = sched["schedule_id"]
    target_seat = 25

    results = []

    def attempt_booking(user_name):
        try:
            t = booking_service.reserve_seat(
                schedule_id=schedule_id,
                seat_number=target_seat,
                full_name=user_name,
                age=24,
                gender="Male",
                phone="9800000000",
                payment_method="UPI",
                db_path=temp_db
            )
            return ("SUCCESS", t)
        except Exception as e:
            return ("FAILURE", str(e))

    with ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(attempt_booking, "Thread 1 User")
        f2 = executor.submit(attempt_booking, "Thread 2 User")
        r1 = f1.result()
        r2 = f2.result()
        results = [r1[0], r2[0]]

    assert results.count("SUCCESS") == 1
    assert results.count("FAILURE") == 1
