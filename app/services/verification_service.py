"""
Verification service for digital QR tickets and conductor boarding workflows.
"""
import json
from typing import Any, Dict, Optional
from app.repositories import checkin_repository, booking_repository


def verify_ticket(
    raw_payload_or_reference: str,
    conductor_id: int,
    boarding_stop_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Parses a QR payload (JSON) or direct booking reference string,
    validates the ticket against the database, and records the check-in.
    """
    cleaned = raw_payload_or_reference.strip()
    booking_ref = cleaned

    # Try parsing as JSON QR payload
    if cleaned.startswith("{") and cleaned.endswith("}"):
        try:
            payload = json.loads(cleaned)
            booking_ref = payload.get("ref", cleaned)
        except Exception:
            pass

    return checkin_repository.verify_and_checkin(
        booking_reference=booking_ref,
        conductor_id=conductor_id,
        boarding_stop_id=boarding_stop_id
    )


def get_conductor_history(conductor_id: int) -> list:
    """Returns past check-ins by this conductor."""
    return checkin_repository.list_conductor_checkins(conductor_id)
