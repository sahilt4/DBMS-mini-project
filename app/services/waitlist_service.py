"""
Waitlist service managing overbooked queues and allocations.
"""
from typing import Any, Dict, List, Optional
from app.repositories import waitlist_repository, passenger_repository


def join_waitlist(
    schedule_id: int,
    user_id: int,
    preferred_seat_type: str = "ANY"
) -> Dict[str, Any]:
    """Adds a logged-in passenger user to the trip waitlist queue."""
    passenger = passenger_repository.find_passenger_by_user_id(user_id)
    if not passenger:
        raise ValueError("Passenger profile not found for the active user.")

    return waitlist_repository.add_to_waitlist(
        passenger_id=passenger["passenger_id"],
        schedule_id=schedule_id,
        preferred_seat_type=preferred_seat_type
    )


def get_schedule_waitlist(schedule_id: int) -> List[Dict[str, Any]]:
    return waitlist_repository.get_waitlist_for_schedule(schedule_id)


def get_user_waitlist(user_id: int) -> List[Dict[str, Any]]:
    return waitlist_repository.get_passenger_waitlists(user_id)

