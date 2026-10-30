"""
Tests for authentication, user registration, and PBKDF2-HMAC password hashing.
"""
import pytest
from app.database import hash_password, verify_password
from app.services import auth_service


def test_password_hashing_and_verification():
    """Verify PBKDF2-HMAC salt generation, hashing and constant-time verification."""
    pwd = "SecurePassword@123"
    hashed = hash_password(pwd)
    
    assert hashed != pwd
    assert "$" in hashed
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_passenger_registration(temp_db):
    """Test successful passenger registration and profile linkage."""
    user = auth_service.register(
        name="Sunil Gavaskar",
        username="sunil_g",
        password="Password@123",
        confirm_password="Password@123",
        age=55,
        gender="Male",
        phone="9823456789"
    )
    assert user["username"] == "sunil_g"
    assert user["role"] == "passenger"
    assert "password_hash" not in user
    assert user["passenger_profile"]["full_name"] == "Sunil Gavaskar"


def test_duplicate_username_rejection(temp_db):
    """Ensure duplicate usernames are rejected."""
    with pytest.raises(ValueError, match="already taken"):
        auth_service.register(
            name="Another Rahul",
            username="rahul_sharma",  # Already in seed
            password="Password@123",
            confirm_password="Password@123",
            age=30
        )


def test_login_validation(temp_db):
    """Test valid and invalid login flows."""
    # Valid admin login
    admin = auth_service.login("admin", "Admin@123")
    assert admin["role"] == "admin"

    # Valid passenger login
    passenger = auth_service.login("rahul_sharma", "Rahul@123")
    assert passenger["role"] == "passenger"

    # Invalid password
    with pytest.raises(ValueError, match="Invalid username or password"):
        auth_service.login("admin", "WrongPassword")

    # Non-existent user
    with pytest.raises(ValueError, match="Invalid username or password"):
        auth_service.login("non_existent_user", "SomePass")
