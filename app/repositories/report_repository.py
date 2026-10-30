"""
Report repository for database statistics, analytical queries, and CSV exports.
Demonstrates SQL JOINs, GROUP BY, aggregates (COUNT, SUM, AVG), and subqueries.
"""
from datetime import date
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from app.database import get_connection


def get_dashboard_stats(conn: Optional[sqlite3.Connection] = None) -> Dict[str, Any]:
    """
    Computes real-time analytical statistics for the Admin Dashboard using aggregate queries.
    """
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        stats = {}

        # 1. Total active buses
        cursor.execute("SELECT COUNT(*) AS cnt FROM buses WHERE is_active = 1;")
        stats["active_buses"] = cursor.fetchone()["cnt"]

        # 2. Total active routes
        cursor.execute("SELECT COUNT(*) AS cnt FROM routes WHERE is_active = 1;")
        stats["active_routes"] = cursor.fetchone()["cnt"]

        # 3. Today's scheduled journeys
        today_str = date.today().isoformat()
        cursor.execute(
            "SELECT COUNT(*) AS cnt FROM schedules WHERE travel_date = ? AND status = 'SCHEDULED';",
            (today_str,)
        )
        stats["today_schedules"] = cursor.fetchone()["cnt"]

        # 4. Total confirmed bookings
        cursor.execute("SELECT COUNT(*) AS cnt FROM bookings WHERE status = 'CONFIRMED';")
        stats["total_confirmed_bookings"] = cursor.fetchone()["cnt"]

        # 5. Today's confirmed bookings
        cursor.execute(
            """
            SELECT COUNT(*) AS cnt 
            FROM bookings 
            WHERE date(booking_date) = ? AND status = 'CONFIRMED';
            """,
            (today_str,)
        )
        stats["today_confirmed_bookings"] = cursor.fetchone()["cnt"]

        # 6. Total simulated revenue from confirmed bookings
        cursor.execute("SELECT COALESCE(SUM(amount), 0.0) AS rev FROM bookings WHERE status = 'CONFIRMED';")
        stats["total_revenue"] = cursor.fetchone()["rev"]

        # 7. Recent 5 bookings
        cursor.execute(
            """
            SELECT 
                b.booking_reference, p.full_name, r.source, r.destination,
                s.travel_date, b.seat_number, b.amount, b.status
            FROM bookings b
            INNER JOIN passengers p ON b.passenger_id = p.passenger_id
            INNER JOIN schedules s ON b.schedule_id = s.schedule_id
            INNER JOIN routes r ON s.route_id = r.route_id
            ORDER BY b.booking_date DESC
            LIMIT 5;
            """
        )
        stats["recent_bookings"] = [dict(row) for row in cursor.fetchall()]

        # 8. Occupancy statistics by schedule
        cursor.execute(
            """
            SELECT 
                s.schedule_id, bs.bus_number, bs.bus_name, bs.total_seats,
                r.source, r.destination, s.travel_date, s.departure_time,
                COUNT(b.booking_id) AS confirmed_seats,
                ROUND((COUNT(b.booking_id) * 100.0) / bs.total_seats, 1) AS occupancy_rate
            FROM schedules s
            INNER JOIN buses bs ON s.bus_id = bs.bus_id
            INNER JOIN routes r ON s.route_id = r.route_id
            LEFT JOIN bookings b ON s.schedule_id = b.schedule_id AND b.status = 'CONFIRMED'
            WHERE s.status <> 'CANCELLED'
            GROUP BY s.schedule_id
            ORDER BY occupancy_rate DESC
            LIMIT 5;
            """
        )
        stats["high_occupancy_schedules"] = [dict(row) for row in cursor.fetchall()]

        # 9. Bookings trend for charts (Daily counts and revenue over the last 7 dates)
        cursor.execute(
            """
            SELECT 
                date(b.booking_date) AS b_date,
                COUNT(b.booking_id) AS booking_count,
                COALESCE(SUM(b.amount), 0.0) AS daily_revenue
            FROM bookings b
            WHERE b.status = 'CONFIRMED'
            GROUP BY date(b.booking_date)
            ORDER BY date(b.booking_date) ASC
            LIMIT 10;
            """
        )
        stats["trend_data"] = [dict(row) for row in cursor.fetchall()]

        return stats
    finally:
        if close_after:
            conn.close()


def report_all_confirmed_bookings(conn: Optional[sqlite3.Connection] = None) -> Tuple[List[str], List[List[Any]]]:
    """Generates comprehensive report of all active confirmed bookings."""
    headers = [
        "Booking Ref", "Passenger Name", "Phone", "Bus Number", "Bus Name",
        "Route", "Travel Date", "Time", "Seat", "Fare", "Payment Method", "Status"
    ]
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                b.booking_reference, p.full_name, p.phone, bs.bus_number, bs.bus_name,
                r.source || ' -> ' || r.destination AS route_name,
                s.travel_date, s.departure_time, b.seat_number, b.amount,
                COALESCE(pm.payment_method, 'N/A') AS payment_method, b.status
            FROM bookings b
            INNER JOIN passengers p ON b.passenger_id = p.passenger_id
            INNER JOIN schedules s ON b.schedule_id = s.schedule_id
            INNER JOIN buses bs ON s.bus_id = bs.bus_id
            INNER JOIN routes r ON s.route_id = r.route_id
            LEFT JOIN payments pm ON b.booking_id = pm.booking_id
            WHERE b.status = 'CONFIRMED'
            ORDER BY s.travel_date DESC, s.departure_time ASC;
            """
        )
        rows = [[row[h] for h in range(len(headers))] for row in cursor.fetchall()]
        return headers, rows
    finally:
        if close_after:
            conn.close()


def report_cancelled_bookings(conn: Optional[sqlite3.Connection] = None) -> Tuple[List[str], List[List[Any]]]:
    """Generates audit report of all cancelled bookings and refund statuses."""
    headers = [
        "Booking Ref", "Passenger Name", "Phone", "Bus Number",
        "Route", "Travel Date", "Seat", "Amount", "Cancellation Date", "Refund Status"
    ]
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                b.booking_reference, p.full_name, p.phone, bs.bus_number,
                r.source || ' -> ' || r.destination AS route_name,
                s.travel_date, b.seat_number, b.amount,
                b.cancellation_date, COALESCE(pm.payment_status, 'REFUNDED') AS refund_status
            FROM bookings b
            INNER JOIN passengers p ON b.passenger_id = p.passenger_id
            INNER JOIN schedules s ON b.schedule_id = s.schedule_id
            INNER JOIN buses bs ON s.bus_id = bs.bus_id
            INNER JOIN routes r ON s.route_id = r.route_id
            LEFT JOIN payments pm ON b.booking_id = pm.booking_id
            WHERE b.status = 'CANCELLED'
            ORDER BY b.cancellation_date DESC;
            """
        )
        rows = [[row[h] for h in range(len(headers))] for row in cursor.fetchall()]
        return headers, rows
    finally:
        if close_after:
            conn.close()


def report_bookings_by_route(conn: Optional[sqlite3.Connection] = None) -> Tuple[List[str], List[List[Any]]]:
    """Generates aggregated bookings and revenue by bus route."""
    headers = ["Route ID", "Source", "Destination", "Distance (km)", "Total Bookings", "Total Revenue (Rs.)"]
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                r.route_id, r.source, r.destination, r.distance_km,
                COUNT(b.booking_id) AS total_bookings,
                COALESCE(SUM(CASE WHEN b.status = 'CONFIRMED' THEN b.amount ELSE 0 END), 0.0) AS total_revenue
            FROM routes r
            LEFT JOIN schedules s ON r.route_id = s.route_id
            LEFT JOIN bookings b ON s.schedule_id = b.schedule_id
            GROUP BY r.route_id, r.source, r.destination, r.distance_km
            ORDER BY total_revenue DESC;
            """
        )
        rows = [[row[h] for h in range(len(headers))] for row in cursor.fetchall()]
        return headers, rows
    finally:
        if close_after:
            conn.close()


def report_bookings_by_bus(conn: Optional[sqlite3.Connection] = None) -> Tuple[List[str], List[List[Any]]]:
    """Generates aggregated booking counts and revenue by physical bus."""
    headers = ["Bus ID", "Bus Number", "Bus Name", "Bus Type", "Capacity", "Confirmed Bookings", "Total Revenue (Rs.)"]
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                bs.bus_id, bs.bus_number, bs.bus_name, bs.bus_type, bs.total_seats,
                COUNT(CASE WHEN b.status = 'CONFIRMED' THEN b.booking_id END) AS confirmed_bookings,
                COALESCE(SUM(CASE WHEN b.status = 'CONFIRMED' THEN b.amount ELSE 0 END), 0.0) AS total_revenue
            FROM buses bs
            LEFT JOIN schedules s ON bs.bus_id = s.bus_id
            LEFT JOIN bookings b ON s.schedule_id = b.schedule_id
            GROUP BY bs.bus_id, bs.bus_number, bs.bus_name, bs.bus_type, bs.total_seats
            ORDER BY total_revenue DESC;
            """
        )
        rows = [[row[h] for h in range(len(headers))] for row in cursor.fetchall()]
        return headers, rows
    finally:
        if close_after:
            conn.close()


def report_bus_occupancy(conn: Optional[sqlite3.Connection] = None) -> Tuple[List[str], List[List[Any]]]:
    """Generates occupancy rate percentage for all active schedules."""
    headers = [
        "Schedule ID", "Date", "Departure", "Bus Number", "Route",
        "Total Seats", "Booked Seats", "Available Seats", "Occupancy %"
    ]
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                s.schedule_id, s.travel_date, s.departure_time, bs.bus_number,
                r.source || ' -> ' || r.destination AS route_name,
                bs.total_seats,
                COUNT(b.booking_id) AS booked_seats,
                (bs.total_seats - COUNT(b.booking_id)) AS available_seats,
                ROUND((COUNT(b.booking_id) * 100.0) / bs.total_seats, 2) AS occupancy_pct
            FROM schedules s
            INNER JOIN buses bs ON s.bus_id = bs.bus_id
            INNER JOIN routes r ON s.route_id = r.route_id
            LEFT JOIN bookings b ON s.schedule_id = b.schedule_id AND b.status = 'CONFIRMED'
            WHERE s.status <> 'CANCELLED'
            GROUP BY s.schedule_id
            ORDER BY s.travel_date DESC, occupancy_pct DESC;
            """
        )
        rows = [[row[h] for h in range(len(headers))] for row in cursor.fetchall()]
        return headers, rows
    finally:
        if close_after:
            conn.close()
