"""
Database access, connection management, schema initialization,
and password hashing for Smart Bus Reservation System.
"""
import hashlib
import hmac
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional, Tuple

import app.config as config

SCHEMA_FILE = config.PROJECT_ROOT / "app" / "schema.sql"

# --- Password Hashing Utilities using PBKDF2-HMAC (Standard Library) ---

def hash_password(password: str) -> str:
    """
    Hashes a plaintext password using PBKDF2-HMAC with SHA-256 and a random 16-byte salt.
    Format: salt_hex$hash_hex
    """
    if not password:
        raise ValueError("Password cannot be empty.")
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"{salt.hex()}${dk.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """
    Verifies a plaintext password against a stored PBKDF2-HMAC hash using constant-time comparison.
    """
    try:
        salt_hex, expected_dk_hex = stored_hash.split("$")
        salt = bytes.fromhex(salt_hex)
        expected_dk = bytes.fromhex(expected_dk_hex)
        actual_dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        return hmac.compare_digest(actual_dk, expected_dk)
    except Exception:
        return False


# --- SQLite Connection Management ---

def get_connection(db_path: Optional[Path] = None, autocommit_mode: bool = False) -> sqlite3.Connection:
    """
    Creates and returns a SQLite connection with foreign keys enabled and row_factory configured.
    
    If autocommit_mode is True (isolation_level=None), Python's implicit transaction
    management is disabled, allowing explicit manual transactions (e.g. BEGIN IMMEDIATE).
    """
    target_path = Path(db_path or config.DB_PATH)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    iso_level = None if autocommit_mode else "DEFERRED"
    conn = sqlite3.connect(str(target_path), timeout=30.0, isolation_level=iso_level)
    conn.row_factory = sqlite3.Row
    
    # Enforce foreign key constraints on every connection
    conn.execute("PRAGMA foreign_keys = ON;")
    # Optimize journal mode for performance and safety
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


@contextmanager
def get_db_cursor(db_path: Optional[Path] = None) -> Generator[sqlite3.Cursor, None, None]:
    """Context manager for simple read/write operations with auto-commit."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


@contextmanager
def transaction(conn: sqlite3.Connection, mode: str = "IMMEDIATE") -> Generator[sqlite3.Cursor, None, None]:
    """
    Explicit transaction context manager supporting BEGIN IMMEDIATE / BEGIN EXCLUSIVE.
    Guarantees rollback on exception and commit on success.
    """
    cursor = conn.cursor()
    cursor.execute(f"BEGIN {mode};")
    try:
        yield cursor
        cursor.execute("COMMIT;")
    except Exception:
        cursor.execute("ROLLBACK;")
        raise
    finally:
        cursor.close()


# --- Schema Initialization ---

def init_db(db_path: Optional[Path] = None, force_reset: bool = False) -> None:
    """
    Initializes the database schema from schema.sql.
    If force_reset is True, existing database file is removed and recreated fresh.
    """
    target_path = Path(db_path or config.DB_PATH)
    
    if force_reset and target_path.exists():
        try:
            target_path.unlink()
            # Also clean up WAL and SHM files if present
            wal = target_path.with_suffix(target_path.suffix + "-wal")
            shm = target_path.with_suffix(target_path.suffix + "-shm")
            if wal.exists():
                wal.unlink()
            if shm.exists():
                shm.unlink()
        except Exception:
            pass

    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        schema_script = f.read()

    conn = get_connection(target_path)
    try:
        conn.executescript(schema_script)
        conn.commit()
    finally:
        conn.close()
