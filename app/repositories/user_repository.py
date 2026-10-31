"""
User repository for managing users table queries and operations.
Supports RBAC (admin, passenger, conductor) and dual-backend database abstraction.
"""
from typing import Any, Dict, List, Optional
from app.database import get_connection, DatabaseConnection


def find_by_username_or_email(identifier: str, conn: Optional[DatabaseConnection] = None) -> Optional[Dict[str, Any]]:
    """Look up user by email or username (case-insensitive)."""
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        clean = identifier.strip().lower()
        clean_email = clean if "@" in clean else f"{clean}@example.com"
        cursor.execute(
            """
            SELECT user_id, name, full_name, username, email,
                   password_hash, role, phone, account_status, created_at
            FROM users
            WHERE LOWER(username) = %s OR LOWER(email) = %s OR LOWER(email) LIKE %s;
            """,
            (clean, clean_email, f"{clean}@%")
        )
        return cursor.fetchone()
    finally:
        if close_after:
            conn.close()


def find_by_username(username: str, conn: Optional[DatabaseConnection] = None) -> Optional[Dict[str, Any]]:
    """Backward compatible alias for find_by_username_or_email."""
    return find_by_username_or_email(username, conn=conn)


def find_by_id(user_id: int, conn: Optional[DatabaseConnection] = None) -> Optional[Dict[str, Any]]:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT user_id, name, full_name, username, email,
                   password_hash, role, phone, account_status, created_at
            FROM users
            WHERE user_id = %s;
            """,
            (user_id,)
        )
        return cursor.fetchone()
    finally:
        if close_after:
            conn.close()


def create_user(
    name: str,
    username_or_email: str,
    password_hash: str,
    role: str = "passenger",
    phone: Optional[str] = None,
    conn: Optional[DatabaseConnection] = None
) -> int:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        clean = username_or_email.strip()
        email = clean if "@" in clean else f"{clean}@example.com"
        username = clean.split("@")[0] if "@" in clean else clean

        cursor.execute(
            """
            INSERT INTO users (name, full_name, username, email, password_hash, role, phone, account_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'ACTIVE');
            """,
            (name.strip(), name.strip(), username, email, password_hash, role.lower(), phone)
        )
        user_id = cursor.lastrowid
        if close_after:
            conn.commit()
        return user_id
    finally:
        if close_after:
            conn.close()


def list_users(role: Optional[str] = None, conn: Optional[DatabaseConnection] = None) -> List[Dict[str, Any]]:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        cursor = conn.cursor()
        if role:
            cursor.execute(
                """
                SELECT user_id, name, full_name, username, email,
                       role, phone, account_status, created_at
                FROM users
                WHERE LOWER(role) = %s
                ORDER BY created_at DESC;
                """,
                (role.lower(),)
            )
        else:
            cursor.execute(
                """
                SELECT user_id, name, full_name, username, email,
                       role, phone, account_status, created_at
                FROM users
                ORDER BY created_at DESC;
                """
            )
        return cursor.fetchall()
    finally:
        if close_after:
            conn.close()


def list_conductors(conn: Optional[DatabaseConnection] = None) -> List[Dict[str, Any]]:
    return list_users(role="conductor", conn=conn)
