"""
Tests for database schema initialization, foreign-key enforcement, and table constraints.
"""
import sqlite3
import pytest
from app.database import get_connection, init_db


def test_schema_initialization(temp_db):
    """Verify that all core tables and partial indexes are initialized."""
    conn = get_connection(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = [row["name"] for row in cursor.fetchall()]
    
    expected_tables = ["bookings", "buses", "passengers", "payments", "routes", "schedules", "users"]
    for t in expected_tables:
        assert t in tables, f"Expected table '{t}' was not created."

    # Check partial unique index on bookings
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_bookings_active_seat';")
    idx = cursor.fetchone()
    assert idx is not None, "Partial unique index 'idx_bookings_active_seat' is missing."
    conn.close()


def test_foreign_key_enforcement(temp_db):
    """Verify that SQLite foreign-key enforcement prevents orphaned records."""
    conn = get_connection(temp_db)
    cursor = conn.cursor()

    # Attempt to insert a schedule with non-existent bus_id
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            """
            INSERT INTO schedules (bus_id, route_id, travel_date, departure_time, arrival_time, fare)
            VALUES (99999, 1, '2026-10-27', '10:00', '14:00', 500.0);
            """
        )

    # Attempt to insert a route where source == destination
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            """
            INSERT INTO routes (source, destination, distance_km)
            VALUES ('Pune', 'Pune', 10.0);
            """
        )
    conn.close()
