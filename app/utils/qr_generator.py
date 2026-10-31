"""
QR Code generation utility for digital E-Tickets.
Encodes booking verification payload and produces image files or in-memory bytes.
"""
import io
import json
from pathlib import Path
from typing import Any, Dict, Optional

import qrcode
from PIL import Image


def generate_qr_payload(booking: Dict[str, Any]) -> str:
    """Generates a compact JSON verification payload."""
    payload = {
        "ref": booking["booking_reference"],
        "name": booking.get("passenger_name", booking.get("full_name", "")),
        "seat": booking["seat_number"],
        "route": f"{booking.get('source', '')} -> {booking.get('destination', '')}",
        "time": str(booking.get("departure_datetime", booking.get("departure_time", "")))
    }
    return json.dumps(payload, separators=(',', ':'))


def generate_qr_image(payload: str, box_size: int = 6, border: int = 2) -> Image.Image:
    """Generates a PIL Image object for the given payload."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    return qr.make_image(fill_color="#1E3A8A", back_color="white").convert("RGB")


def generate_qr_bytes(payload: str) -> bytes:
    """Generates PNG bytes for the given payload."""
    img = generate_qr_image(payload)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def save_qr_file(payload: str, destination_path: Path) -> Path:
    """Saves the QR code image to a target file path."""
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    img = generate_qr_image(payload)
    img.save(str(destination_path), format="PNG")
    return destination_path
