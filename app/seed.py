"""
Database seeding module for Smart Bus Reservation System.
Populates realistic demonstration data if the database is unpopulated,
without duplicating records on subsequent runs.
"""
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from app.config import (
    BUS_TYPES,
    DB_PATH,
    DEFAULT_ADMIN,
    DEFAULT_PASSENGERS,
)
from app.database import get_connection, hash_password, init_db


def seed_database(db_path: Optional[Path] = None, force_reset: bool = False) -> None:
    """
    Initializes schema if needed and inserts realistic seed data if not already present.
    Ensures idempotency: checks if admin user exists before seeding.
    """
    init_db(db_path=db_path, force_reset=force_reset)
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        # Check if already seeded
        cursor.execute("SELECT COUNT(*) AS cnt FROM users WHERE role = 'admin';")
        if cursor.fetchone()["cnt"] > 0 and not force_reset:
            return  # Already seeded, don't duplicate

        # 1. Seed Administrator
        admin_hash = hash_password(DEFAULT_ADMIN["password"])
        cursor.execute(
            """
            INSERT INTO users (name, username, password_hash, role)
            VALUES (?, ?, ?, ?);
            """,
            (DEFAULT_ADMIN["name"], DEFAULT_ADMIN["username"], admin_hash, DEFAULT_ADMIN["role"])
        )

        # 2. Seed Passenger Users & Passenger Profiles
        passenger_user_ids = []
        for p in DEFAULT_PASSENGERS:
            p_hash = hash_password(p["password"])
            cursor.execute(
                """
                INSERT INTO users (name, username, password_hash, role)
                VALUES (?, ?, ?, ?);
                """,
                (p["name"], p["username"], p_hash, p["role"])
            )
            u_id = cursor.lastrowid
            passenger_user_ids.append((u_id, p))

            # Corresponding passenger record
            cursor.execute(
                """
                INSERT INTO passengers (user_id, full_name, age, gender, phone)
                VALUES (?, ?, ?, ?, ?);
                """,
                (u_id, p["name"], p["age"], p["gender"], p["phone"])
            )

        # 3. Seed Buses (at least 9 buses of various types)
        buses_data = [
            ("MH-15-AB-1001", "Royal Star Travels", "Volvo Multi-Axle", 40),
            ("MH-15-CD-2002", "Shivneri Express", "AC Sleeper", 32),
            ("MH-12-EF-3003", "Pune Voyager", "AC Seater", 44),
            ("MH-04-GH-4004", "Mumbai SuperFast", "Non-AC Seater", 48),
            ("MH-20-IJ-5005", "Deccan Queen Bus", "AC Sleeper", 36),
            ("MH-15-KL-6006", "Godavari Cruiser", "Non-AC Sleeper", 32),
            ("MH-31-MN-7007", "Vidarbha Garud", "Volvo Multi-Axle", 42),
            ("MH-14-OP-8008", "Sahyadri Travels", "AC Seater", 40),
            ("MH-12-QR-9009", "Maharashtra Express", "Non-AC Seater", 50),
        ]
        bus_ids = {}
        for num, name, btype, seats in buses_data:
            cursor.execute(
                """
                INSERT INTO buses (bus_number, bus_name, bus_type, total_seats, is_active)
                VALUES (?, ?, ?, ?, 1);
                """,
                (num, name, btype, seats)
            )
            bus_ids[num] = cursor.lastrowid

        # 4. Seed Routes (12 realistic Maharashtra city routes)
        routes_data = [
            ("Nashik", "Pune", 210.0),
            ("Pune", "Nashik", 210.0),
            ("Pune", "Mumbai", 150.0),
            ("Mumbai", "Pune", 150.0),
            ("Mumbai", "Nashik", 165.0),
            ("Nashik", "Mumbai", 165.0),
            ("Nashik", "Chhatrapati Sambhajinagar", 180.0),
            ("Chhatrapati Sambhajinagar", "Nashik", 180.0),
            ("Pune", "Nagpur", 710.0),
            ("Nagpur", "Pune", 710.0),
            ("Nashik", "Kolhapur", 440.0),
            ("Pune", "Kolhapur", 235.0),
        ]
        route_ids = {}
        for src, dst, dist in routes_data:
            cursor.execute(
                """
                INSERT INTO routes (source, destination, distance_km, is_active)
                VALUES (?, ?, ?, 1);
                """,
                (src, dst, dist)
            )
            route_ids[f"{src}->{dst}"] = cursor.lastrowid

        # 5. Seed Schedules (at least 24 schedules spanning today, future days, and yesterday)
        today = date.today()
        yesterday = today - timedelta(days=1)
        day_1 = today + timedelta(days=1)
        day_2 = today + timedelta(days=2)
        day_3 = today + timedelta(days=3)

        schedules_template = [
            # Yesterday (completed/historical)
            ("MH-15-AB-1001", "Nashik->Pune", yesterday.isoformat(), "06:30", "11:30", 450.0, "COMPLETED"),
            ("MH-15-CD-2002", "Pune->Mumbai", yesterday.isoformat(), "07:00", "10:30", 350.0, "COMPLETED"),
            # Today
            ("MH-15-AB-1001", "Nashik->Pune", today.isoformat(), "06:30", "11:30", 480.0, "SCHEDULED"),
            ("MH-15-AB-1001", "Pune->Nashik", today.isoformat(), "14:30", "19:30", 480.0, "SCHEDULED"),
            ("MH-15-CD-2002", "Nashik->Mumbai", today.isoformat(), "07:00", "11:00", 420.0, "SCHEDULED"),
            ("MH-12-EF-3003", "Pune->Mumbai", today.isoformat(), "08:00", "11:45", 350.0, "SCHEDULED"),
            ("MH-04-GH-4004", "Mumbai->Pune", today.isoformat(), "09:00", "13:00", 280.0, "SCHEDULED"),
            ("MH-20-IJ-5005", "Nashik->Chhatrapati Sambhajinagar", today.isoformat(), "10:00", "14:30", 380.0, "SCHEDULED"),
            ("MH-31-MN-7007", "Pune->Nagpur", today.isoformat(), "18:00", "07:00", 1150.0, "SCHEDULED"),
            ("MH-14-OP-8008", "Pune->Kolhapur", today.isoformat(), "16:00", "21:00", 360.0, "SCHEDULED"),
            # Day + 1 (Tomorrow)
            ("MH-15-AB-1001", "Nashik->Pune", day_1.isoformat(), "06:30", "11:30", 480.0, "SCHEDULED"),
            ("MH-15-CD-2002", "Mumbai->Nashik", day_1.isoformat(), "08:30", "12:30", 420.0, "SCHEDULED"),
            ("MH-12-EF-3003", "Pune->Mumbai", day_1.isoformat(), "07:30", "11:15", 350.0, "SCHEDULED"),
            ("MH-04-GH-4004", "Mumbai->Pune", day_1.isoformat(), "15:00", "19:00", 280.0, "SCHEDULED"),
            ("MH-15-KL-6006", "Chhatrapati Sambhajinagar->Nashik", day_1.isoformat(), "08:00", "12:30", 380.0, "SCHEDULED"),
            ("MH-31-MN-7007", "Nagpur->Pune", day_1.isoformat(), "17:30", "06:30", 1150.0, "SCHEDULED"),
            ("MH-14-OP-8008", "Nashik->Kolhapur", day_1.isoformat(), "21:00", "06:30", 650.0, "SCHEDULED"),
            ("MH-12-QR-9009", "Pune->Nashik", day_1.isoformat(), "11:00", "16:00", 320.0, "SCHEDULED"),
            # Day + 2
            ("MH-15-AB-1001", "Pune->Nashik", day_2.isoformat(), "08:00", "13:00", 480.0, "SCHEDULED"),
            ("MH-15-CD-2002", "Nashik->Pune", day_2.isoformat(), "13:00", "18:00", 450.0, "SCHEDULED"),
            ("MH-12-EF-3003", "Pune->Mumbai", day_2.isoformat(), "09:30", "13:15", 350.0, "SCHEDULED"),
            ("MH-20-IJ-5005", "Nashik->Mumbai", day_2.isoformat(), "06:00", "10:00", 400.0, "SCHEDULED"),
            # Day + 3
            ("MH-31-MN-7007", "Pune->Nagpur", day_3.isoformat(), "19:00", "08:00", 1150.0, "SCHEDULED"),
            ("MH-14-OP-8008", "Pune->Kolhapur", day_3.isoformat(), "07:00", "12:00", 360.0, "SCHEDULED"),
        ]

        schedule_ids = []
        for bnum, rkey, tdate, deptime, arrtime, fare, status in schedules_template:
            b_id = bus_ids[bnum]
            r_id = route_ids[rkey]
            cursor.execute(
                """
                INSERT INTO schedules (bus_id, route_id, travel_date, departure_time, arrival_time, fare, status)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (b_id, r_id, tdate, deptime, arrtime, fare, status)
            )
            schedule_ids.append(cursor.lastrowid)

        # 6. Seed Initial Bookings & Payments
        # Fetch passenger IDs
        cursor.execute("SELECT passenger_id, full_name FROM passengers ORDER BY passenger_id;")
        p_rows = cursor.fetchall()
        p1_id = p_rows[0]["passenger_id"]  # Rahul Sharma
        p2_id = p_rows[1]["passenger_id"]  # Priya Patil
        p3_id = p_rows[2]["passenger_id"]  # Amit Deshmukh

        # Seed bookings for today's Nashik->Pune (schedule_ids[2])
        sched_today_np = schedule_ids[2]
        bookings_seed = [
            # (ref, sched_id, pass_id, seat, amount, status, cancel_date, pay_method, pay_status)
            (
                "BUS-20261026-A1B2C3D4",
                sched_today_np,
                p1_id,
                1,
                480.0,
                "CONFIRMED",
                None,
                "UPI",
                "PAID"
            ),
            (
                "BUS-20261026-E5F6G7H8",
                sched_today_np,
                p2_id,
                2,
                480.0,
                "CONFIRMED",
                None,
                "Debit Card",
                "PAID"
            ),
            (
                "BUS-20261026-J9K0L1M2",
                sched_today_np,
                p3_id,
                5,
                480.0,
                "CANCELLED",
                (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
                "UPI",
                "REFUNDED"
            ),
            # Seed booking on tomorrow's schedule
            (
                "BUS-20261027-N3P4Q5R6",
                schedule_ids[10],
                p1_id,
                12,
                480.0,
                "CONFIRMED",
                None,
                "Credit Card",
                "PAID"
            ),
            # Seed booking on historical schedule
            (
                "BUS-20261025-S7T8U9V0",
                schedule_ids[0],
                p2_id,
                4,
                450.0,
                "CONFIRMED",
                None,
                "Net Banking",
                "PAID"
            )
        ]

        for ref, s_id, pass_id, seat, amt, bstatus, cdate, pmethod, pstatus in bookings_seed:
            cursor.execute(
                """
                INSERT INTO bookings (booking_reference, schedule_id, passenger_id, seat_number, amount, status, cancellation_date)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (ref, s_id, pass_id, seat, amt, bstatus, cdate)
            )
            b_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO payments (booking_id, amount, payment_method, payment_status)
                VALUES (?, ?, ?, ?);
                """,
                (b_id, amt, pmethod, pstatus)
            )

        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    seed_database(force_reset=True)
    print("Database seeded successfully.")
