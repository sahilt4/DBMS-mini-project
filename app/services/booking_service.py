"""
Booking transaction service for Smart Bus Reservation System.
Implements the core ACID reservation algorithm using BEGIN IMMEDIATE transactions
to guarantee duplicate-booking prevention and seat availability integrity.
"""
from datetime import datetime
import os
from pathlib import Path
import sqlite3
from typing import Any, Dict, Optional

import app.config as config
from app.database import get_connection, transaction
from app.repositories import booking_repository, passenger_repository, schedule_repository


def generate_booking_reference() -> str:
    """Generates a human-readable unique reference format: BUS-YYYYMMDD-XXXXXXXX"""
    date_str = datetime.now().strftime("%Y%m%d")
    random_str = os.urandom(4).hex().upper()
    return f"BUS-{date_str}-{random_str}"


def reserve_seat(
    schedule_id: int,
    seat_number: int,
    full_name: str,
    age: int,
    gender: str,
    phone: str,
    payment_method: str,
    user_id: Optional[int] = None,
    db_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Executes an atomic seat reservation workflow in a BEGIN IMMEDIATE SQLite transaction.
    
    Algorithm:
    1. Validate input parameters and passenger details.
    2. Verify schedule exists, is active (SCHEDULED), and fetch fare + bus total seats.
    3. Validate that seat_number is within valid range (1 to total_seats).
    4. Open connection with autocommit_mode=True and start BEGIN IMMEDIATE write lock.
    5. Recheck if seat is already occupied by a CONFIRMED booking within the transaction.
    6. If already booked, raise error and abort immediately.
    7. Insert passenger record.
    8. Insert booking record with unique booking reference.
    9. Insert simulated payment ledger record.
    10. Commit transaction.
    11. Return confirmed ticket details.
    """
    if not full_name or not full_name.strip():
        raise ValueError("Passenger full name is required.")
    if age < 1 or age > 120:
        raise ValueError("Passenger age must be between 1 and 120.")
    if seat_number <= 0:
        raise ValueError("Seat number must be a positive integer.")

    # Step 2: Fetch and validate schedule
    schedule = schedule_repository.find_schedule_by_id(schedule_id)
    if not schedule:
        raise ValueError("Selected schedule does not exist.")
    if schedule["status"] != "SCHEDULED":
        raise ValueError(f"Cannot book schedule with status '{schedule['status']}'. Only 'SCHEDULED' trips can be booked.")
    if not schedule.get("bus_is_active", 1):
        raise ValueError("Assigned bus is currently deactivated.")
    if not schedule.get("route_is_active", 1):
        raise ValueError("Assigned route is currently deactivated.")

    # Step 3: Validate seat range against bus capacity
    total_seats = schedule["total_seats"]
    if seat_number > total_seats:
        raise ValueError(f"Seat number {seat_number} exceeds the bus capacity of {total_seats} seats.")

    fare_amount = float(schedule["fare"])
    booking_ref = generate_booking_reference()

    # Step 4: Open isolated connection with autocommit mode for explicit transaction control
    conn = get_connection(db_path or config.DB_PATH, autocommit_mode=True)
    try:
        with transaction(conn, mode="IMMEDIATE") as cursor:
            # Step 5: Recheck seat availability inside the write transaction
            cursor.execute(
                """
                SELECT booking_id 
                FROM bookings 
                WHERE schedule_id = ? AND seat_number = ? AND status = 'CONFIRMED';
                """,
                (schedule_id, seat_number)
            )
            conflict = cursor.fetchone()
            if conflict:
                raise ValueError(f"Seat #{seat_number} has already been reserved by another passenger. Please select another seat.")

            # Step 7: Insert passenger record
            cursor.execute(
                """
                INSERT INTO passengers (user_id, full_name, age, gender, phone)
                VALUES (?, ?, ?, ?, ?);
                """,
                (user_id, full_name.strip(), age, gender.strip(), phone.strip() if phone else "")
            )
            passenger_id = cursor.lastrowid

            # Step 8: Insert booking record
            cursor.execute(
                """
                INSERT INTO bookings (booking_reference, schedule_id, passenger_id, seat_number, amount, status)
                VALUES (?, ?, ?, ?, ?, 'CONFIRMED');
                """,
                (booking_ref, schedule_id, passenger_id, seat_number, fare_amount)
            )
            booking_id = cursor.lastrowid

            # Step 9: Insert payment record
            cursor.execute(
                """
                INSERT INTO payments (booking_id, amount, payment_method, payment_status)
                VALUES (?, ?, ?, 'PAID');
                """,
                (booking_id, fare_amount, payment_method)
            )

        # Step 11: Transaction committed successfully! Fetch fresh complete ticket record
        confirmed_ticket = booking_repository.find_booking_by_id(booking_id, conn=conn)
        return confirmed_ticket
    except sqlite3.IntegrityError as ie:
        if "UNIQUE constraint failed" in str(ie):
            raise ValueError(f"Seat #{seat_number} was just booked by another user. Please choose a different seat.")
        raise ValueError(f"Database integrity error during booking: {str(ie)}")
    finally:
        conn.close()
