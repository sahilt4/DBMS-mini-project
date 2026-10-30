"""
Configuration module for Smart Bus Reservation System.
Handles application directories, database paths, and demo credentials.
"""
import os
import sys
from pathlib import Path

# Application identifiers
APP_NAME = "SmartBusReservation"
APP_TITLE = "Smart Bus Reservation System - DBMS Mini Project"
APP_VERSION = "1.0.0"

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Database configuration: writable application-data directory
def get_default_db_dir() -> Path:
    """Returns a reliable writable application-data directory across OS platforms."""
    if sys.platform == "win32":
        base_dir = os.environ.get("LOCALAPPDATA")
        if not base_dir:
            base_dir = os.path.expanduser("~\\AppData\\Local")
    elif sys.platform == "darwin":
        base_dir = os.path.expanduser("~/Library/Application Support")
    else:
        base_dir = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))

    app_dir = Path(base_dir) / APP_NAME
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir

# Allow overriding DB path via environment variable (e.g., for automated testing)
DEFAULT_DB_PATH = get_default_db_dir() / "smart_bus.sqlite3"
DB_PATH = Path(os.environ.get("SMARTBUS_DB_PATH", str(DEFAULT_DB_PATH)))

# Default Seed Credentials
DEFAULT_ADMIN = {
    "name": "System Administrator",
    "username": "admin",
    "password": "Admin@123",
    "role": "admin"
}

DEFAULT_PASSENGERS = [
    {
        "name": "Rahul Sharma",
        "username": "rahul_sharma",
        "password": "Rahul@123",
        "role": "passenger",
        "age": 28,
        "gender": "Male",
        "phone": "9822012345"
    },
    {
        "name": "Priya Patil",
        "username": "priya_patil",
        "password": "Priya@123",
        "role": "passenger",
        "age": 25,
        "gender": "Female",
        "phone": "9822054321"
    },
    {
        "name": "Amit Deshmukh",
        "username": "amit_d",
        "password": "Amit@123",
        "role": "passenger",
        "age": 34,
        "gender": "Male",
        "phone": "9890112233"
    }
]

# Supported Bus Types
BUS_TYPES = [
    "AC Sleeper",
    "Non-AC Sleeper",
    "AC Seater",
    "Non-AC Seater",
    "Volvo Multi-Axle"
]

# Payment Methods
PAYMENT_METHODS = [
    "UPI",
    "Credit Card",
    "Debit Card",
    "Net Banking",
    "Cash"
]
