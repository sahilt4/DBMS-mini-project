"""
Database access, connection pooling, schema initialization, and security for BRMS.
Provides unified database abstraction supporting both MySQL 8.x (InnoDB) and local SQLite.
"""
import hashlib
import hmac
import os
import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple, Union

import app.config as config

SCHEMA_SQLITE_FILE = config.PROJECT_ROOT / "app" / "schema.sql"
SCHEMA_MYSQL_DIR = config.PROJECT_ROOT / "database"

# Optional bcrypt import
try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False

# Optional mysql.connector import
try:
    import mysql.connector
    from mysql.connector import pooling
    HAS_MYSQL = True
except ImportError:
    HAS_MYSQL = False


# ============================================================================
# PASSWORD HASHING UTILITIES (Bcrypt Primary + PBKDF2 Compatible)
# ============================================================================

def hash_password(password: str) -> str:
    """
    Hashes a plaintext password using bcrypt (primary) or PBKDF2-HMAC-SHA256 (fallback).
    """
    if not password:
        raise ValueError("Password cannot be empty.")
    
    if HAS_BCRYPT:
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")
    else:
        salt = os.urandom(16)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        return f"{salt.hex()}${dk.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """
    Verifies a plaintext password against a stored bcrypt or PBKDF2 hash.
    """
    if not password or not stored_hash:
        return False
    
    try:
        if stored_hash.startswith("$2b$") or stored_hash.startswith("$2a$"):
            if HAS_BCRYPT:
                return bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
            return False
        
        # PBKDF2 format: salt_hex$dk_hex
        salt_hex, expected_dk_hex = stored_hash.split("$")
        salt = bytes.fromhex(salt_hex)
        expected_dk = bytes.fromhex(expected_dk_hex)
        actual_dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        return hmac.compare_digest(actual_dk, expected_dk)
    except Exception:
        return False


# ============================================================================
# DATABASE ADAPTER & ENGINE MANAGEMENT
# ============================================================================

_mysql_pool: Optional[Any] = None
_active_engine: Optional[str] = None


def is_mysql_available() -> bool:
    """Tests if MySQL 8.x server is reachable with the configured credentials and database."""
    if not HAS_MYSQL:
        return False
    try:
        test_conn = mysql.connector.connect(
            host=config.MYSQL_CONFIG["host"],
            port=config.MYSQL_CONFIG["port"],
            user=config.MYSQL_CONFIG["user"],
            password=config.MYSQL_CONFIG["password"],
            database=config.MYSQL_CONFIG["database"],
            connection_timeout=2
        )
        test_conn.close()
        return True
    except Exception:
        return False


def get_active_engine() -> str:
    """Returns 'mysql' if configured and running, otherwise 'sqlite'."""
    global _active_engine
    if _active_engine is not None:
        return _active_engine
    
    env_engine = os.environ.get("SMARTBUS_DB_ENGINE", "").lower()
    if env_engine == "mysql" and is_mysql_available():
        _active_engine = "mysql"
    elif env_engine == "sqlite":
        _active_engine = "sqlite"
    elif is_mysql_available():
        _active_engine = "mysql"
    else:
        _active_engine = "sqlite"
    
    return _active_engine


def set_active_engine(engine: str) -> None:
    """Manually override active engine (e.g. for testing)."""
    global _active_engine
    if engine not in ("mysql", "sqlite"):
        raise ValueError("Engine must be 'mysql' or 'sqlite'.")
    _active_engine = engine


def get_mysql_pool():
    """Initializes and returns MySQL connection pool."""
    global _mysql_pool
    if _mysql_pool is None and HAS_MYSQL:
        _mysql_pool = pooling.MySQLConnectionPool(
            pool_name="brms_pool",
            pool_size=5,
            pool_reset_session=True,
            **config.MYSQL_CONFIG
        )
    return _mysql_pool


class DictRowCursor:
    """
    Cursor wrapper that provides dictionary access to fetched rows
    and adapts '%s' parameters to '?' for SQLite.
    """
    def __init__(self, raw_cursor, is_sqlite: bool = True):
        self._raw = raw_cursor
        self._is_sqlite = is_sqlite

    @property
    def lastrowid(self):
        return self._raw.lastrowid

    @property
    def rowcount(self):
        return self._raw.rowcount

    def execute(self, query: str, params: Union[Tuple, List, Dict] = ()):
        adapted_query = query
        if self._is_sqlite:
            # Convert MySQL %s placeholder to SQLite ?
            # Note: Do not convert if literal % is inside quotes or LIKE
            adapted_query = re.sub(r'(?<!%)(%s)(?!%)', '?', query)
        
        if params is None:
            return self._raw.execute(adapted_query)
        elif isinstance(params, (list, tuple)):
            return self._raw.execute(adapted_query, params)
        elif isinstance(params, dict):
            return self._raw.execute(adapted_query, params)
        else:
            return self._raw.execute(adapted_query, (params,))

    def executemany(self, query: str, seq_of_params):
        adapted_query = query
        if self._is_sqlite:
            adapted_query = re.sub(r'(?<!%)(%s)(?!%)', '?', query)
        return self._raw.executemany(adapted_query, seq_of_params)

    def fetchone(self) -> Optional[Dict[str, Any]]:
        row = self._raw.fetchone()
        if row is None:
            return None
        if isinstance(row, dict):
            return row
        if isinstance(row, sqlite3.Row):
            return dict(row)
        if hasattr(self._raw, "description") and self._raw.description:
            cols = [d[0] for d in self._raw.description]
            return dict(zip(cols, row))
        return dict(row)

    def fetchall(self) -> List[Dict[str, Any]]:
        rows = self._raw.fetchall()
        if not rows:
            return []
        if isinstance(rows[0], dict):
            return rows
        if isinstance(rows[0], sqlite3.Row):
            return [dict(r) for r in rows]
        if hasattr(self._raw, "description") and self._raw.description:
            cols = [d[0] for d in self._raw.description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(r) for r in rows]

    def close(self):
        self._raw.close()


class DatabaseConnection:
    """Wrapper managing transactions and cursors across MySQL and SQLite."""
    def __init__(self, raw_conn, is_sqlite: bool):
        self.raw = raw_conn
        self.is_sqlite = is_sqlite

    def cursor(self) -> DictRowCursor:
        if self.is_sqlite:
            return DictRowCursor(self.raw.cursor(), is_sqlite=True)
        else:
            return DictRowCursor(self.raw.cursor(dictionary=True), is_sqlite=False)

    def commit(self):
        self.raw.commit()

    def rollback(self):
        self.raw.rollback()

    def close(self):
        self.raw.close()


def get_connection(db_path: Optional[Path] = None, autocommit: bool = False) -> DatabaseConnection:
    """Creates a database connection using the active engine."""
    engine = get_active_engine()
    
    if engine == "mysql" and HAS_MYSQL:
        try:
            pool = get_mysql_pool()
            raw_conn = pool.get_connection() if pool else mysql.connector.connect(**config.MYSQL_CONFIG)
            raw_conn.autocommit = autocommit
            return DatabaseConnection(raw_conn, is_sqlite=False)
        except Exception:
            # Fallback to SQLite if MySQL fails
            pass

    # SQLite backend: isolation_level=None enables explicit manual transactions (BEGIN IMMEDIATE)
    target_path = Path(db_path or config.DB_PATH)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target_path), timeout=30.0, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return DatabaseConnection(conn, is_sqlite=True)


@contextmanager
def get_db_cursor(db_path: Optional[Path] = None) -> Generator[DictRowCursor, None, None]:
    """Context manager for auto-committed queries."""
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
def transaction(conn: DatabaseConnection) -> Generator[DictRowCursor, None, None]:
    """Explicit transaction context manager guaranteeing commit or rollback."""
    cursor = conn.cursor()
    started = False
    try:
        if conn.is_sqlite:
            if not conn.raw.in_transaction:
                cursor._raw.execute("BEGIN IMMEDIATE;")
                started = True
        else:
            conn.raw.start_transaction()
            started = True
        yield cursor
        if started:
            if conn.is_sqlite:
                cursor._raw.execute("COMMIT;")
            else:
                conn.raw.commit()
    except Exception:
        if started:
            if conn.is_sqlite:
                cursor._raw.execute("ROLLBACK;")
            else:
                conn.raw.rollback()
        raise
    finally:
        cursor.close()


# ============================================================================
# SCHEMA INITIALIZATION
# ============================================================================

def init_db(db_path: Optional[Path] = None, force_reset: bool = False) -> None:
    """Initializes database tables, views, and indexes."""
    engine = get_active_engine()
    
    if engine == "mysql" and HAS_MYSQL:
        # Create MySQL tables from database/02_create_tables.sql
        tables_sql_file = SCHEMA_MYSQL_DIR / "02_create_tables.sql"
        if tables_sql_file.exists():
            with open(tables_sql_file, "r", encoding="utf-8") as f:
                script = f.read()
            conn = mysql.connector.connect(**config.MYSQL_CONFIG)
            cursor = conn.cursor()
            for stmt in script.split(";"):
                stmt = stmt.strip()
                if stmt:
                    cursor.execute(stmt)
            conn.commit()
            cursor.close()
            conn.close()
            return

    # SQLite Initialization
    target_path = Path(db_path or config.DB_PATH)
    if force_reset and target_path.exists():
        try:
            target_path.unlink()
            for ext in ("-wal", "-shm"):
                p = target_path.with_name(target_path.name + ext)
                if p.exists():
                    p.unlink()
        except Exception:
            pass

    target_path.parent.mkdir(parents=True, exist_ok=True)
    with open(SCHEMA_SQLITE_FILE, "r", encoding="utf-8") as f:
        schema_script = f.read()

    conn = get_connection(target_path)
    try:
        conn.raw.executescript(schema_script)
        conn.commit()
    finally:
        conn.close()
