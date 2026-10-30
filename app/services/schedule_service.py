"""
Schedule service for validating and coordinating schedule operations.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.repositories import bus_repository, route_repository, schedule_repository


def create_new_schedule(
    bus_id: int,
    route_id: int,
    travel_date: str,
    departure_time: str,
    arrival_time: str,
    fare: float
) -> int:
    """Validates parameters and inserts a new journey schedule."""
    bus = bus_repository.find_bus_by_id(bus_id)
    if not bus:
        raise ValueError("Selected bus was not found.")
    if not bus["is_active"]:
        raise ValueError("Cannot schedule a deactivated bus.")

    route = route_repository.find_route_by_id(route_id)
    if not route:
        raise ValueError("Selected route was not found.")
    if not route["is_active"]:
        raise ValueError("Cannot schedule a journey on a deactivated route.")

    try:
        datetime.strptime(travel_date, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Travel date must be in YYYY-MM-DD format.")

    try:
        datetime.strptime(departure_time, "%H:%M")
        datetime.strptime(arrival_time, "%H:%M")
    except ValueError:
        raise ValueError("Times must be in HH:MM (24-hour) format.")

    if fare <= 0:
        raise ValueError("Fare must be greater than zero.")

    return schedule_repository.create_schedule(
        bus_id=bus_id,
        route_id=route_id,
        travel_date=travel_date,
        departure_time=departure_time,
        arrival_time=arrival_time,
        fare=fare,
        status="SCHEDULED"
    )


def cancel_schedule(schedule_id: int) -> bool:
    """Cancels a schedule if eligible."""
    schedule = schedule_repository.find_schedule_by_id(schedule_id)
    if not schedule:
        raise ValueError("Schedule not found.")
    if schedule["status"] == "CANCELLED":
        raise ValueError("Schedule is already cancelled.")
    return schedule_repository.set_schedule_status(schedule_id, "CANCELLED")
