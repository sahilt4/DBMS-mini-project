"""
Pytest configuration and temporary database fixtures.
"""
import os
from pathlib import Path
import tempfile
import pytest

from app.database import init_db
from app.seed import seed_database
import app.config as config


@pytest.fixture
def temp_db(monkeypatch):
    """
    Creates an isolated temporary SQLite database for each test,
    seeds it with test data, and ensures the real application database is untouched.
    """
    with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as tf:
        temp_path = Path(tf.name)

    monkeypatch.setattr(config, "DB_PATH", temp_path)
    seed_database(db_path=temp_path, force_reset=True)

    yield temp_path

    # Teardown
    try:
        if temp_path.exists():
            temp_path.unlink()
        wal = temp_path.with_suffix(temp_path.suffix + "-wal")
        shm = temp_path.with_suffix(temp_path.suffix + "-shm")
        if wal.exists():
            wal.unlink()
        if shm.exists():
            shm.unlink()
    except Exception:
        pass
