"""
Tests for seat availability calculation, booking impact, and seat release on cancellation.
"""
from app.services import booking_service, cancellation_service
from app.repositories import booking_repository, schedule_repository


def test_availability_lifecycle(temp_db):
    """
    Verify seat availability decreases upon booking and is restored upon cancellation,
    demonstrating the partial unique index and dynamic availability calculation.
    """
    schedules = schedule_repository.search_schedules()
    sched = schedules[0]
    schedule_id = sched["schedule_id"]
    test_seat = 18

    # 1. Check initially available
    initial_sched = schedule_repository.find_schedule_by_id(schedule_id)
    initial_available = initial_sched["available_seats"]
    assert booking_repository.is_seat_available(schedule_id, test_seat) is True

    # 2. Book the seat
    ticket = booking_service.reserve_seat(
        schedule_id=schedule_id,
        seat_number=test_seat,
        full_name="Lifecycle Tester",
        age=30,
        gender="Male",
        phone="9876543210",
        payment_method="UPI",
        db_path=temp_db
    )
    booking_id = ticket["booking_id"]

    # Seat must now be unavailable
    after_book_sched = schedule_repository.find_schedule_by_id(schedule_id)
    assert after_book_sched["available_seats"] == initial_available - 1
    assert booking_repository.is_seat_available(schedule_id, test_seat) is False
    assert test_seat in booking_repository.get_occupied_seats(schedule_id)

    # 3. Cancel the booking
    cancelled_ticket = cancellation_service.cancel_booking(booking_id=booking_id, is_admin=True, db_path=temp_db)
    assert cancelled_ticket["status"] == "CANCELLED"

    # Seat must be released and available again for a new passenger
    after_cancel_sched = schedule_repository.find_schedule_by_id(schedule_id)
    assert after_cancel_sched["available_seats"] == initial_available
    assert booking_repository.is_seat_available(schedule_id, test_seat) is True
    assert test_seat not in booking_repository.get_occupied_seats(schedule_id)

    # 4. A new passenger can now book the same seat without integrity conflict!
    new_ticket = booking_service.reserve_seat(
        schedule_id=schedule_id,
        seat_number=test_seat,
        full_name="New Passenger",
        age=22,
        gender="Female",
        phone="9123456780",
        payment_method="Debit Card",
        db_path=temp_db
    )
    assert new_ticket["seat_number"] == test_seat
    assert new_ticket["status"] == "CONFIRMED"
