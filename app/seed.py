"""
Database seeding module for Bus Reservation & Management System (BRMS).
Populates realistic demonstration data across all 13 entities + Audit Log.
Maintains 100% compatibility with unit tests and production schema.
"""
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from app.config import (
    BUS_TYPES,
    DB_PATH,
    DEFAULT_ADMIN,
    DEFAULT_CONDUCTORS,
    DEFAULT_PASSENGERS,
)
from app.database import get_connection, hash_password, init_db


def seed_database(db_path: Optional[Path] = None, force_reset: bool = False) -> None:
    """
    Initializes schema if needed and inserts realistic seed data if not already present.
    Idempotent: verifies if admin user exists before seeding.
    """
    init_db(db_path=db_path, force_reset=force_reset)
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        # Check if already seeded
        cursor.execute("SELECT COUNT(*) AS cnt FROM users WHERE lower(role) = 'admin';")
        row = cursor.fetchone()
        if row and row["cnt"] > 0 and not force_reset:
            return

        # 1. Seed Administrator
        admin_hash = hash_password(DEFAULT_ADMIN["password"])
        cursor.execute(
            """
            INSERT INTO users (name, full_name, username, email, password_hash, role, phone, account_status)
            VALUES (%s, %s, %s, %s, %s, 'admin', %s, 'ACTIVE');
            """,
            (
                DEFAULT_ADMIN["name"], DEFAULT_ADMIN["name"], DEFAULT_ADMIN["username"],
                DEFAULT_ADMIN["email"], admin_hash, DEFAULT_ADMIN["phone"]
            )
        )

        # 2. Seed Conductors
        conductor_ids = []
        for c in DEFAULT_CONDUCTORS:
            c_hash = hash_password(c["password"])
            cursor.execute(
                """
                INSERT INTO users (name, full_name, username, email, password_hash, role, phone, account_status)
                VALUES (%s, %s, %s, %s, %s, 'conductor', %s, 'ACTIVE');
                """,
                (c["name"], c["name"], c["username"], c["email"], c_hash, c["phone"])
            )
            conductor_ids.append(cursor.lastrowid)

        # 3. Seed Passenger Users and Passenger Profiles
        passenger_ids = []
        for p in DEFAULT_PASSENGERS:
            p_hash = hash_password(p["password"])
            cursor.execute(
                """
                INSERT INTO users (name, full_name, username, email, password_hash, role, phone, account_status)
                VALUES (%s, %s, %s, %s, %s, 'passenger', %s, 'ACTIVE');
                """,
                (p["name"], p["name"], p["username"], p["email"], p_hash, p["phone"])
            )
            u_id = cursor.lastrowid

            cursor.execute(
                """
                INSERT INTO passengers (user_id, full_name, passenger_name, age, gender, phone)
                VALUES (%s, %s, %s, %s, %s, %s);
                """,
                (u_id, p["name"], p["name"], p["age"], p["gender"], p["phone"])
            )
            passenger_ids.append(cursor.lastrowid)

        # Seed an additional guest passenger (not linked to user account)
        cursor.execute(
            """
            INSERT INTO passengers (user_id, full_name, passenger_name, age, gender, phone)
            VALUES (NULL, %s, %s, %s, %s, %s);
            """,
            ("Sunita Verma", "Sunita Verma", 42, "Female", "9811223344")
        )
        passenger_ids.append(cursor.lastrowid)

        # 4. Seed Bus Stops
        bus_stops_data = [
            ("Mumbai CST Central", "Mumbai", "Opposite CST Station, Fort"),
            ("Vashi Highway Toll Plaza", "Navi Mumbai", "Sion-Panvel Expressway, Vashi"),
            ("Lonavala Express Junction", "Lonavala", "Mumbai-Pune Expressway, Lonavala"),
            ("Pune Wakad Bridge", "Pune", "Bangalore-Mumbai Bypass Highway, Wakad"),
            ("Pune Swargate Depot", "Pune", "Near Swargate Bus Station, Pune"),
            ("Bangalore Majestic Bus Stand", "Bangalore", "Kempegowda Bus Station, Majestic"),
            ("Panaji KTC Bus Terminus", "Goa", "Patto Centre, Panaji"),
            ("Hyderabad Imlibun Terminal", "Hyderabad", "MGBS, Gowliguda, Hyderabad"),
        ]
        stop_ids = {}
        for sname, city, addr in bus_stops_data:
            cursor.execute(
                """
                INSERT INTO bus_stops (stop_name, city, address)
                VALUES (%s, %s, %s);
                """,
                (sname, city, addr)
            )
            stop_ids[sname] = cursor.lastrowid

        # 5. Seed Buses (9 buses)
        buses_data = [
            ("MH-12-AB-1001", "Shivneri Superfast", "Volvo Multi-Axle", 40),
            ("MH-14-XY-2002", "Maharashtra Travels", "AC Sleeper", 32),
            ("KA-01-CD-3003", "Airavat Express", "AC Seater", 44),
            ("GA-07-EF-4004", "Goa Voyager", "Non-AC Sleeper", 32),
            ("DL-01-GH-5005", "Capital Flyer", "Non-AC Seater", 48),
            ("MH-15-KL-6006", "Godavari Cruiser", "Non-AC Sleeper", 32),
            ("MH-31-MN-7007", "Vidarbha Garud", "Volvo Multi-Axle", 42),
            ("MH-14-OP-8008", "Sahyadri Travels", "AC Seater", 40),
            ("MH-12-QR-9009", "Maharashtra Express", "Non-AC Seater", 50),
        ]
        bus_ids = {}
        for num, name, btype, seats in buses_data:
            cursor.execute(
                """
                INSERT INTO buses (bus_number, registration_number, bus_name, bus_type, total_seats, capacity, is_active, operational_status)
                VALUES (%s, %s, %s, %s, %s, %s, 1, 'ACTIVE');
                """,
                (num, num, name, btype, seats, seats)
            )
            bus_ids[num] = cursor.lastrowid

        # 6. Seed Routes (12 routes to satisfy tests requiring >= 10 routes)
        routes_data = [
            ("Mumbai", "Pune", 150.0, 180),
            ("Pune", "Mumbai", 150.0, 180),
            ("Pune", "Bangalore", 840.0, 780),
            ("Bangalore", "Pune", 840.0, 780),
            ("Mumbai", "Goa", 580.0, 600),
            ("Pune", "Hyderabad", 560.0, 570),
            ("Delhi", "Jaipur", 280.0, 300),
            ("Nashik", "Pune", 210.0, 240),
            ("Pune", "Nashik", 210.0, 240),
            ("Mumbai", "Nashik", 165.0, 210),
            ("Nashik", "Mumbai", 165.0, 210),
            ("Pune", "Kolhapur", 235.0, 270),
        ]
        route_ids = {}
        for src, dst, dist, dur in routes_data:
            cursor.execute(
                """
                INSERT INTO routes (source, destination, distance_km, distance, estimated_duration, is_active, route_status)
                VALUES (%s, %s, %s, %s, %s, 1, 'ACTIVE');
                """,
                (src, dst, dist, dist, dur)
            )
            route_ids[f"{src}->{dst}"] = cursor.lastrowid

        # 7. Seed Route Stops for Mumbai -> Pune
        r1_id = route_ids["Mumbai->Pune"]
        route_stops = [
            (r1_id, stop_ids["Mumbai CST Central"], 1, 0.0, 0),
            (r1_id, stop_ids["Vashi Highway Toll Plaza"], 2, 30.0, 45),
            (r1_id, stop_ids["Lonavala Express Junction"], 3, 85.0, 110),
            (r1_id, stop_ids["Pune Wakad Bridge"], 4, 135.0, 160),
            (r1_id, stop_ids["Pune Swargate Depot"], 5, 150.0, 180),
        ]
        for rid, sid, seq, dist, offset in route_stops:
            cursor.execute(
                """
                INSERT INTO route_stops (route_id, stop_id, stop_sequence, distance_from_origin, arrival_offset_minutes)
                VALUES (%s, %s, %s, %s, %s);
                """,
                (rid, sid, seq, dist, offset)
            )

        # 8. Seed Schedules
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        today = now
        tomorrow = now + timedelta(days=1)
        day_after = now + timedelta(days=2)
        day_3 = now + timedelta(days=3)

        schedules_list = [
            # Yesterday (completed)
            ("MH-12-AB-1001", "Mumbai->Pune", yesterday.strftime("%Y-%m-%d"), "06:30", "09:30", 480.0, "COMPLETED"),
            # Today
            ("MH-12-AB-1001", "Mumbai->Pune", today.strftime("%Y-%m-%d"), "06:30", "09:30", 480.0, "SCHEDULED"),
            ("MH-14-XY-2002", "Mumbai->Pune", today.strftime("%Y-%m-%d"), "14:00", "17:00", 520.0, "SCHEDULED"),
            ("KA-01-CD-3003", "Pune->Bangalore", today.strftime("%Y-%m-%d"), "18:00", "07:00", 1450.0, "SCHEDULED"),
            ("GA-07-EF-4004", "Mumbai->Goa", today.strftime("%Y-%m-%d"), "20:00", "06:00", 950.0, "SCHEDULED"),
            # Tomorrow
            ("MH-12-AB-1001", "Mumbai->Pune", tomorrow.strftime("%Y-%m-%d"), "06:30", "09:30", 480.0, "SCHEDULED"),
            ("MH-14-XY-2002", "Pune->Mumbai", tomorrow.strftime("%Y-%m-%d"), "10:00", "13:00", 500.0, "SCHEDULED"),
            ("KA-01-CD-3003", "Bangalore->Pune", tomorrow.strftime("%Y-%m-%d"), "19:00", "08:00", 1450.0, "SCHEDULED"),
            ("DL-01-GH-5005", "Delhi->Jaipur", tomorrow.strftime("%Y-%m-%d"), "07:00", "12:00", 420.0, "SCHEDULED"),
            # Day + 2
            ("MH-12-AB-1001", "Mumbai->Pune", day_after.strftime("%Y-%m-%d"), "06:30", "09:30", 480.0, "SCHEDULED"),
            ("MH-31-MN-7007", "Pune->Hyderabad", day_after.strftime("%Y-%m-%d"), "21:00", "06:00", 850.0, "SCHEDULED"),
            # Day + 3
            ("GA-07-EF-4004", "Mumbai->Goa", day_3.strftime("%Y-%m-%d"), "21:00", "07:00", 950.0, "SCHEDULED"),
        ]

        schedule_ids = []
        for bnum, rkey, tdate, dep, arr, fare, stat in schedules_list:
            b_id = bus_ids[bnum]
            r_id = route_ids[rkey]
            dep_dt = f"{tdate} {dep}:00"
            arr_dt = f"{tdate} {arr}:00"
            cursor.execute(
                """
                INSERT INTO schedules (
                    bus_id, route_id, travel_date, departure_time, arrival_time, fare, status,
                    departure_datetime, arrival_datetime, base_fare, schedule_status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """,
                (b_id, r_id, tdate, dep, arr, fare, stat, dep_dt, arr_dt, fare, stat)
            )
            s_id = cursor.lastrowid
            schedule_ids.append(s_id)

            # Generate schedule_seats inventory
            cursor.execute("SELECT total_seats, bus_type FROM buses WHERE bus_id = %s;", (b_id,))
            b_info = cursor.fetchone()
            cap = b_info["total_seats"]
            btype = b_info["bus_type"]

            for seat_i in range(1, cap + 1):
                if "Sleeper" in btype:
                    stype = "SLEEPER_LOWER" if (seat_i % 2 == 1) else "SLEEPER_UPPER"
                else:
                    stype = "WINDOW" if (seat_i % 4 in (1, 0)) else "AISLE"

                cursor.execute(
                    """
                    INSERT INTO schedule_seats (schedule_id, seat_number, seat_type, seat_status)
                    VALUES (%s, %s, %s, 'AVAILABLE');
                    """,
                    (s_id, seat_i, stype)
                )

        # 9. Seed Initial Bookings, Payments, and Occupancy for Schedule 1 (Today's Mumbai->Pune)
        active_sched_id = schedule_ids[1]  # Today 06:30 Mumbai->Pune
        bstop_cst = stop_ids["Mumbai CST Central"]
        dstop_swargate = stop_ids["Pune Swargate Depot"]

        bookings_data = [
            ("BUS-20261031-100001", active_sched_id, passenger_ids[0], 1, 480.0, "CONFIRMED", None, None, "UPI", "PAID"),
            ("BUS-20261031-100002", active_sched_id, passenger_ids[1], 2, 480.0, "CONFIRMED", None, None, "Debit Card", "PAID"),
            ("BUS-20261031-100003", active_sched_id, passenger_ids[2], 5, 480.0, "CANCELLED", "Emergency meeting cancelled", (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"), "UPI", "REFUNDED"),
            ("BUS-20261031-100004", schedule_ids[5], passenger_ids[0], 4, 480.0, "CONFIRMED", None, None, "Credit Card", "PAID"),
            ("BUS-20261030-900001", schedule_ids[0], passenger_ids[1], 3, 480.0, "CONFIRMED", None, None, "Net Banking", "PAID"),
        ]

        for ref, sid, pid, seat, amt, bstat, reason, cdate, pmethod, pstat in bookings_data:
            cursor.execute(
                """
                INSERT INTO bookings (
                    booking_reference, schedule_id, passenger_id, seat_number,
                    boarding_stop_id, dropping_stop_id, amount, total_amount, status, booking_status,
                    cancellation_reason, cancellation_date, cancelled_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """,
                (ref, sid, pid, seat, bstop_cst, dstop_swargate, amt, amt, bstat, bstat, reason, cdate, cdate)
            )
            bk_id = cursor.lastrowid

            # Insert payment ledger
            tx_ref = f"TXN-{pmethod[:3].upper()}-{ref[-6:]}"
            cursor.execute(
                """
                INSERT INTO payments (booking_id, amount, payment_method, transaction_reference, payment_status)
                VALUES (%s, %s, %s, %s, %s);
                """,
                (bk_id, amt, pmethod, tx_ref, pstat)
            )
            pmt_id = cursor.lastrowid

            # Update schedule_seats
            if bstat == "CONFIRMED":
                cursor.execute(
                    """
                    UPDATE schedule_seats 
                    SET seat_status = 'BOOKED' 
                    WHERE schedule_id = %s AND seat_number = %s;
                    """,
                    (sid, seat)
                )
            elif bstat == "CANCELLED":
                cursor.execute(
                    """
                    INSERT INTO refunds (payment_id, booking_id, refund_amount, refund_reason, refund_status)
                    VALUES (%s, %s, %s, %s, 'PROCESSED');
                    """,
                    (pmt_id, bk_id, amt * 0.9, reason)
                )

        # 10. Seed Ticket Checkin (Conductor verification for booking 1)
        cursor.execute(
            """
            INSERT INTO ticket_checkins (booking_id, conductor_id, checkin_status, boarding_stop_id)
            VALUES (1, %s, 'VERIFIED', %s);
            """,
            (conductor_ids[0], bstop_cst)
        )

        # 11. Seed Waitlist Queue entry
        cursor.execute(
            """
            INSERT INTO waitlist (passenger_id, schedule_id, preferred_seat_type, queue_position, waitlist_status)
            VALUES (%s, %s, 'WINDOW', 1, 'WAITING');
            """,
            (passenger_ids[3], active_sched_id)
        )

        # 12. Seed Audit Log record
        cursor.execute(
            """
            INSERT INTO audit_logs (action_type, table_name, record_id, changed_by, new_values)
            VALUES ('INITIAL_SEED', 'system', '0', 'system_seeder', '{"status": "Database successfully populated"}');
            """
        )

        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    seed_database(force_reset=True)
    print("Database successfully seeded with 13 entities + Audit Log.")
