"""
Booking transaction service for Bus Reservation and Management System (BRMS).
Guarantees duplicate-booking prevention and seat availability integrity using schedule_seats inventory.
"""
from typing import Any, Dict, Optional
from pathlib import Path

import app.config as config
from app.database import get_connection
from app.repositories import booking_repository, passenger_repository, schedule_repository


def reserve_seat(
    schedule_id: int,
    seat_number: int,
    full_name: str,
    age: int,
    gender: str,
    phone: str,
    payment_method: str,
    user_id: Optional[int] = None,
    boarding_stop_id: Optional[int] = None,
    dropping_stop_id: Optional[int] = None,
    db_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Executes an atomic seat reservation workflow:
    1. Validates passenger information.
    2. Verifies schedule exists and is ACTIVE.
    3. Creates/finds passenger profile.
    4. Executes atomic reservation in schedule_seats, bookings, payments.
    """
    if not full_name or not full_name.strip():
        raise ValueError("Passenger full name is required.")
    if age < 1 or age > 120:
        raise ValueError("Passenger age must be between 1 and 120.")
    if seat_number <= 0:
        raise ValueError("Seat number must be a positive integer.")

    schedule = schedule_repository.find_schedule_by_id(schedule_id)
    if not schedule:
        raise ValueError("Selected schedule does not exist.")
    if schedule["status"] != "SCHEDULED":
        raise ValueError(f"Cannot book schedule with status '{schedule['status']}'. Only 'SCHEDULED' trips can be booked.")

    total_seats = schedule["total_seats"]
    if seat_number > total_seats:
        raise ValueError(f"Seat number {seat_number} exceeds the bus capacity of {total_seats} seats.")

    fare_amount = float(schedule["fare"])

    # Look up or create passenger
    conn = get_connection(db_path or config.DB_PATH)
    try:
        passenger_id = passenger_repository.create_passenger(
            full_name=full_name.strip(),
            age=age,
            gender=gender.strip() if gender else "Other",
            phone=phone.strip() if phone else "",
            user_id=user_id,
            conn=conn
        )

        # Atomic reservation
        res = booking_repository.create_booking_atomic(
            schedule_id=schedule_id,
            passenger_id=passenger_id,
            seat_number=seat_number,
            amount=fare_amount,
            payment_method=payment_method,
            boarding_stop_id=boarding_stop_id,
            dropping_stop_id=dropping_stop_id,
            conn=conn
        )

        # Retrieve complete hydrated booking record
        hydrated = booking_repository.find_booking_by_id(res["booking_id"], conn=conn)
        return hydrated or res
    finally:
        conn.close()


def get_available_seats(schedule_id: int) -> int:
    """Returns live available seats for a schedule."""
    sched = schedule_repository.find_schedule_by_id(schedule_id)
    return sched["available_seats"] if sched else 0
