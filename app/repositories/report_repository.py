"""
Report repository for database statistics, analytical queries, and CSV exports.
Leverages relational views (vw_route_revenue, vw_schedule_occupancy, audit_logs)
and standard aggregate queries.
"""
import csv
import io
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from app.database import get_connection, DatabaseConnection


def get_dashboard_stats(conn: Optional[DatabaseConnection] = None) -> Dict[str, Any]:
    """Computes real-time analytical statistics for the Admin Dashboard."""
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        stats = {}

        # 1. Active buses
        cursor.execute("SELECT COUNT(*) AS cnt FROM buses WHERE operational_status = 'ACTIVE';")
        stats["active_buses"] = cursor.fetchone()["cnt"]

        # 2. Active routes
        cursor.execute("SELECT COUNT(*) AS cnt FROM routes WHERE route_status = 'ACTIVE';")
        stats["active_routes"] = cursor.fetchone()["cnt"]

        # 3. Today's scheduled journeys
        today_str = date.today().isoformat()
        cursor.execute(
            "SELECT COUNT(*) AS cnt FROM schedules WHERE SUBSTR(departure_datetime, 1, 10) = %s AND schedule_status = 'SCHEDULED';",
            (today_str,)
        )
        row = cursor.fetchone()
        stats["today_schedules"] = row["cnt"] if row else 0

        # 4. Total confirmed bookings
        cursor.execute("SELECT COUNT(*) AS cnt FROM bookings WHERE booking_status = 'CONFIRMED';")
        stats["total_confirmed_bookings"] = cursor.fetchone()["cnt"]

        # 5. Today's confirmed bookings
        cursor.execute(
            """
            SELECT COUNT(*) AS cnt 
            FROM bookings 
            WHERE SUBSTR(booking_date, 1, 10) = %s AND booking_status = 'CONFIRMED';
            """,
            (today_str,)
        )
        row = cursor.fetchone()
        stats["today_confirmed_bookings"] = row["cnt"] if row else 0

        # 6. Total simulated revenue from confirmed bookings
        cursor.execute("SELECT COALESCE(SUM(total_amount), 0.0) AS rev FROM bookings WHERE booking_status = 'CONFIRMED';")
        stats["total_revenue"] = cursor.fetchone()["rev"]

        # 7. Recent 5 bookings
        cursor.execute(
            """
            SELECT 
                b.booking_reference, p.passenger_name AS full_name, r.source, r.destination,
                SUBSTR(s.departure_datetime, 1, 10) AS travel_date, b.seat_number,
                b.total_amount AS amount, b.booking_status AS status
            FROM bookings b
            INNER JOIN passengers p ON b.passenger_id = p.passenger_id
            INNER JOIN schedules s ON b.schedule_id = s.schedule_id
            INNER JOIN routes r ON s.route_id = r.route_id
            ORDER BY b.booking_date DESC
            LIMIT 5;
            """
        )
        stats["recent_bookings"] = cursor.fetchall()

        # 8. Occupancy statistics by schedule
        cursor.execute(
            """
            SELECT s.schedule_id, b.bus_name,
                   COALESCE(b.bus_number, b.registration_number, '') AS bus_number,
                   r.source, r.destination,
                   COALESCE(s.travel_date, SUBSTR(s.departure_datetime, 1, 10)) AS travel_date,
                   COALESCE(s.departure_time, SUBSTR(s.departure_datetime, 12, 5)) AS departure_time,
                   COUNT(CASE WHEN ss.seat_status = 'BOOKED' THEN 1 END) AS booked_seats,
                   COUNT(CASE WHEN ss.seat_status = 'BOOKED' THEN 1 END) AS confirmed_seats,
                   COALESCE(b.total_seats, b.capacity) AS total_seats,
                   ROUND((COUNT(CASE WHEN ss.seat_status = 'BOOKED' THEN 1 END) * 100.0) / NULLIF(COALESCE(b.total_seats, b.capacity), 0), 2) AS occupancy_rate
            FROM schedules s
            JOIN routes r ON s.route_id = r.route_id
            JOIN buses b ON s.bus_id = b.bus_id
            LEFT JOIN schedule_seats ss ON s.schedule_id = ss.schedule_id
            GROUP BY s.schedule_id, b.bus_name, b.bus_number, b.registration_number, r.source, r.destination, s.travel_date, s.departure_datetime, s.departure_time, b.total_seats, b.capacity
            ORDER BY occupancy_rate DESC
            LIMIT 5;
            """
        )
        stats["high_occupancy_schedules"] = cursor.fetchall()

        # 9. Bookings trend for charts
        cursor.execute(
            """
            SELECT 
                SUBSTR(b.booking_date, 1, 10) AS b_date,
                COUNT(b.booking_id) AS booking_count,
                COALESCE(SUM(b.total_amount), 0.0) AS daily_revenue
            FROM bookings b
            WHERE b.booking_status = 'CONFIRMED'
            GROUP BY SUBSTR(b.booking_date, 1, 10)
            ORDER BY b_date DESC
            LIMIT 7;
            """
        )
        trend_rows = cursor.fetchall()
        trend_rows.reverse()
        stats["booking_trends"] = trend_rows

        return stats
    finally:
        if close_after:
            conn.close()


def report_all_confirmed_bookings(conn: Optional[DatabaseConnection] = None) -> Tuple[List[str], List[List[Any]]]:
    """Report 1: Confirmed bookings with full route and payment details."""
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                b.booking_reference, p.passenger_name, p.age, p.phone,
                bs.bus_name, bs.registration_number,
                r.source, r.destination,
                SUBSTR(s.departure_datetime, 1, 10) AS travel_date,
                SUBSTR(s.departure_datetime, 12, 5) AS departure_time,
                b.seat_number, b.total_amount, pm.payment_method, pm.transaction_reference
            FROM bookings b
            JOIN passengers p ON b.passenger_id = p.passenger_id
            JOIN schedules s ON b.schedule_id = s.schedule_id
            JOIN buses bs ON s.bus_id = bs.bus_id
            JOIN routes r ON s.route_id = r.route_id
            LEFT JOIN payments pm ON b.booking_id = pm.booking_id
            WHERE b.booking_status = 'CONFIRMED'
            ORDER BY b.booking_date DESC;
            """
        )
        rows = cursor.fetchall()
        headers = [
            "Reference", "Passenger Name", "Age", "Phone",
            "Bus Name", "Bus Number", "Source", "Destination",
            "Date", "Departure", "Seat #", "Amount (Rs)", "Payment Method", "Transaction ID"
        ]
        data = [[r[k] for k in r] for r in rows]
        return headers, data
    finally:
        if close_after:
            conn.close()


def report_cancelled_bookings(conn: Optional[DatabaseConnection] = None) -> Tuple[List[str], List[List[Any]]]:
    """Report 2: Cancelled bookings and refund audit."""
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                b.booking_reference, p.passenger_name, r.source, r.destination,
                b.seat_number, b.total_amount, b.cancelled_at, b.cancellation_reason,
                ref.refund_amount, ref.refund_status
            FROM bookings b
            JOIN passengers p ON b.passenger_id = p.passenger_id
            JOIN schedules s ON b.schedule_id = s.schedule_id
            JOIN routes r ON s.route_id = r.route_id
            LEFT JOIN refunds ref ON b.booking_id = ref.booking_id
            WHERE b.booking_status = 'CANCELLED'
            ORDER BY b.cancelled_at DESC;
            """
        )
        rows = cursor.fetchall()
        headers = [
            "Reference", "Passenger Name", "Source", "Destination",
            "Seat #", "Original Fare", "Cancelled At", "Reason", "Refund Amount", "Refund Status"
        ]
        data = [[r[k] for k in r] for r in rows]
        return headers, data
    finally:
        if close_after:
            conn.close()


def report_bookings_by_route(conn: Optional[DatabaseConnection] = None) -> Tuple[List[str], List[List[Any]]]:
    """Report 3: Aggregated route performance from vw_route_revenue."""
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                route_id, CONCAT(source, ' -> ', destination) AS route_pair,
                total_trips_scheduled, confirmed_bookings, cancelled_bookings,
                total_gross_revenue, total_refunded, net_revenue
            FROM vw_route_revenue
            ORDER BY net_revenue DESC;
            """
        )
        rows = cursor.fetchall()
        headers = [
            "Route ID", "Route", "Total Scheduled Trips", "Confirmed Bookings",
            "Cancellations", "Gross Revenue (Rs)", "Refunded (Rs)", "Net Revenue (Rs)"
        ]
        data = [[r[k] for k in r] for r in rows]
        return headers, data
    finally:
        if close_after:
            conn.close()


def report_bookings_by_bus(conn: Optional[DatabaseConnection] = None) -> Tuple[List[str], List[List[Any]]]:
    """Report 4: Fleet utilization and revenue per bus."""
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                b.bus_id, b.registration_number, b.bus_name, b.bus_type, b.capacity,
                COUNT(DISTINCT s.schedule_id) AS trips_count,
                COUNT(DISTINCT CASE WHEN bk.booking_status = 'CONFIRMED' THEN bk.booking_id END) AS confirmed_passengers,
                COALESCE(SUM(CASE WHEN bk.booking_status = 'CONFIRMED' THEN bk.total_amount ELSE 0 END), 0.0) AS total_revenue
            FROM buses b
            LEFT JOIN schedules s ON b.bus_id = s.bus_id
            LEFT JOIN bookings bk ON s.schedule_id = bk.schedule_id
            GROUP BY b.bus_id, b.registration_number, b.bus_name, b.bus_type, b.capacity
            ORDER BY total_revenue DESC;
            """
        )
        rows = cursor.fetchall()
        headers = [
            "Bus ID", "Registration #", "Bus Name", "Bus Type", "Capacity",
            "Trips Count", "Passengers Served", "Total Revenue (Rs)"
        ]
        data = [[r[k] for k in r] for r in rows]
        return headers, data
    finally:
        if close_after:
            conn.close()


def report_bus_occupancy(conn: Optional[DatabaseConnection] = None) -> Tuple[List[str], List[List[Any]]]:
    """Report 5: Schedule occupancy analysis from vw_schedule_occupancy."""
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                schedule_id, departure_datetime, schedule_status,
                CONCAT(source, ' -> ', destination) AS route,
                bus_name, total_capacity, booked_seats, available_seats, occupancy_percentage
            FROM vw_schedule_occupancy
            ORDER BY departure_datetime DESC;
            """
        )
        rows = cursor.fetchall()
        headers = [
            "Schedule ID", "Departure Datetime", "Trip Status", "Route",
            "Bus Name", "Capacity", "Booked Seats", "Available Seats", "Occupancy (%)"
        ]
        data = [[r[k] for k in r] for r in rows]
        return headers, data
    finally:
        if close_after:
            conn.close()


def report_audit_logs(conn: Optional[DatabaseConnection] = None) -> Tuple[List[str], List[List[Any]]]:
    """Report 6: Audit log trail."""
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT log_id, action_type, table_name, record_id, changed_by, old_values, new_values, created_at
            FROM audit_logs
            ORDER BY log_id DESC
            LIMIT 100;
            """
        )
        rows = cursor.fetchall()
        headers = [
            "Log ID", "Action", "Table", "Record ID", "Changed By", "Old Values", "New Values", "Timestamp"
        ]
        data = [[r[k] for k in r] for r in rows]
        return headers, data
    finally:
        if close_after:
            conn.close()


def export_report_to_csv_string(rows: List[Dict[str, Any]], fieldnames: List[str]) -> str:
    """Exports any table dataset to CSV formatted string."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()
