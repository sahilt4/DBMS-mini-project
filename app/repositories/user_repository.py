"""
User repository for managing users table queries and operations.
"""
import sqlite3
from typing import Any, Dict, List, Optional

from app.database import get_connection


def find_by_username(username: str, conn: Optional[sqlite3.Connection] = None) -> Optional[Dict[str, Any]]:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT user_id, name, username, password_hash, role, created_at
            FROM users
            WHERE lower(username) = lower(?);
            """,
            (username.strip(),)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        if close_after:
            conn.close()


def find_by_id(user_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[Dict[str, Any]]:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT user_id, name, username, password_hash, role, created_at
            FROM users
            WHERE user_id = ?;
            """,
            (user_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        if close_after:
            conn.close()


def create_user(
    name: str,
    username: str,
    password_hash: str,
    role: str = "passenger",
    conn: Optional[sqlite3.Connection] = None
) -> int:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO users (name, username, password_hash, role)
            VALUES (?, ?, ?, ?);
            """,
            (name.strip(), username.strip(), password_hash, role)
        )
        user_id = cursor.lastrowid
        if close_after:
            conn.commit()
        return user_id
    finally:
        if close_after:
            conn.close()


def list_users(role: Optional[str] = None, conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        if role:
            cursor.execute(
                """
                SELECT user_id, name, username, role, created_at
                FROM users
                WHERE role = ?
                ORDER BY created_at DESC;
                """,
                (role,)
            )
        else:
            cursor.execute(
                """
                SELECT user_id, name, username, role, created_at
                FROM users
                ORDER BY created_at DESC;
                """
            )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        if close_after:
            conn.close()
