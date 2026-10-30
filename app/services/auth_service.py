"""
Authentication and session management service.
Handles login, registration, password verification, and role-based checks.
"""
from typing import Any, Dict, Optional

from app.database import hash_password, verify_password
from app.repositories import passenger_repository, user_repository

# In-memory session state for desktop application
_CURRENT_USER: Optional[Dict[str, Any]] = None


def get_current_user() -> Optional[Dict[str, Any]]:
    return _CURRENT_USER


def set_current_user(user: Optional[Dict[str, Any]]) -> None:
    global _CURRENT_USER
    _CURRENT_USER = user


def is_authenticated() -> bool:
    return _CURRENT_USER is not None


def is_admin() -> bool:
    return _CURRENT_USER is not None and _CURRENT_USER.get("role") == "admin"


def login(username: str, password: str) -> Dict[str, Any]:
    """
    Validates username and password against PBKDF2-HMAC hash.
    Sets user in current session upon success.
    """
    u = username.strip()
    p = password.strip()
    if not u or not p:
        raise ValueError("Username and password are required.")

    user = user_repository.find_by_username(u)
    if not user:
        raise ValueError("Invalid username or password.")

    if not verify_password(p, user["password_hash"]):
        raise ValueError("Invalid username or password.")

    # Remove password hash from session object
    session_user = {k: v for k, v in user.items() if k != "password_hash"}
    
    # Also load passenger profile details if this is a passenger user
    if session_user["role"] == "passenger":
        passenger_profile = passenger_repository.find_passenger_by_user_id(session_user["user_id"])
        session_user["passenger_profile"] = passenger_profile

    set_current_user(session_user)
    return session_user


def logout() -> None:
    set_current_user(None)


def register(
    name: str,
    username: str,
    password: str,
    confirm_password: str,
    age: int,
    gender: Optional[str] = None,
    phone: Optional[str] = None
) -> Dict[str, Any]:
    """
    Registers a new passenger user account and corresponding passenger profile.
    """
    n = name.strip()
    u = username.strip()
    p = password.strip()
    cp = confirm_password.strip()

    if not n:
        raise ValueError("Full name is required.")
    if len(u) < 3:
        raise ValueError("Username must be at least 3 characters long.")
    if len(p) < 6:
        raise ValueError("Password must be at least 6 characters long.")
    if p != cp:
        raise ValueError("Password and confirmation do not match.")
    if age < 1 or age > 120:
        raise ValueError("Age must be between 1 and 120.")
    if phone and len(phone.strip()) < 10:
        raise ValueError("Phone number must have at least 10 digits.")

    existing = user_repository.find_by_username(u)
    if existing:
        raise ValueError(f"Username '{u}' is already taken. Please choose another.")

    pwd_hash = hash_password(p)
    user_id = user_repository.create_user(
        name=n,
        username=u,
        password_hash=pwd_hash,
        role="passenger"
    )

    passenger_repository.create_passenger(
        full_name=n,
        age=age,
        gender=gender or "Other",
        phone=phone or "",
        user_id=user_id
    )

    user = user_repository.find_by_id(user_id)
    session_user = {k: v for k, v in user.items() if k != "password_hash"}
    session_user["passenger_profile"] = passenger_repository.find_passenger_by_user_id(user_id)
    set_current_user(session_user)
    return session_user
