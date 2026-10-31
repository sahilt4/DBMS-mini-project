"""
Configuration module for Bus Reservation and Management System (BRMS).
Handles application directories, database engine settings, credentials, and business parameters.
"""
import os
import sys
from pathlib import Path

# Application identifiers
APP_NAME = "SmartBusReservation"
APP_TITLE = "Bus Reservation & Management System (BRMS)"
APP_VERSION = "2.0.0"

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Database Engine Selection ('mysql' or 'sqlite')
# Defaults to mysql if available/configured, with automatic transparent sqlite fallback
DB_ENGINE = os.environ.get("SMARTBUS_DB_ENGINE", "sqlite").lower()

# MySQL 8.x Configuration Defaults
MYSQL_CONFIG = {
    "host": os.environ.get("SMARTBUS_DB_HOST", "localhost"),
    "port": int(os.environ.get("SMARTBUS_DB_PORT", "3306")),
    "user": os.environ.get("SMARTBUS_DB_USER", "root"),
    "password": os.environ.get("SMARTBUS_DB_PASSWORD", ""),
    "database": os.environ.get("SMARTBUS_DB_NAME", "brms_db"),
    "charset": "utf8mb4",
    "use_unicode": True,
    "autocommit": False,
}

# SQLite Configuration: writable application-data directory
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

DEFAULT_DB_PATH = get_default_db_dir() / "brms.sqlite3"
DB_PATH = Path(os.environ.get("SMARTBUS_DB_PATH", str(DEFAULT_DB_PATH)))

# Role Definitions
ROLE_ADMIN = "ADMIN"
ROLE_PASSENGER = "PASSENGER"
ROLE_CONDUCTOR = "CONDUCTOR"

ROLES = [ROLE_ADMIN, ROLE_PASSENGER, ROLE_CONDUCTOR]

# Default Seed Credentials
DEFAULT_ADMIN = {
    "name": "System Administrator",
    "email": "admin@brms.com",
    "username": "admin",
    "password": "Admin@123",
    "role": ROLE_ADMIN,
    "phone": "9822000000"
}

DEFAULT_CONDUCTORS = [
    {
        "name": "Ramesh Shinde",
        "email": "conductor@brms.com",
        "username": "conductor",
        "password": "Conductor@123",
        "role": ROLE_CONDUCTOR,
        "phone": "9822011111"
    },
    {
        "name": "Sunil More",
        "email": "conductor2@brms.com",
        "username": "conductor2",
        "password": "Conductor@123",
        "role": ROLE_CONDUCTOR,
        "phone": "9822022222"
    }
]

DEFAULT_PASSENGERS = [
    {
        "name": "Rahul Sharma",
        "email": "rahul@example.com",
        "username": "rahul_sharma",
        "password": "Rahul@123",
        "role": ROLE_PASSENGER,
        "age": 28,
        "gender": "Male",
        "phone": "9822012345"
    },
    {
        "name": "Priya Patil",
        "email": "priya@example.com",
        "username": "priya_patil",
        "password": "Priya@123",
        "role": ROLE_PASSENGER,
        "age": 25,
        "gender": "Female",
        "phone": "9822054321"
    },
    {
        "name": "Amit Deshmukh",
        "email": "amit@example.com",
        "username": "amit_d",
        "password": "Amit@123",
        "role": ROLE_PASSENGER,
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
