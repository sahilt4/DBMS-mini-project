"""
Tests for QR code generation and ReportLab PDF boarding pass compilation.
"""
from pathlib import Path
import tempfile
import pytest

from app.repositories import booking_repository
from app.utils.qr_generator import generate_qr_payload, generate_qr_bytes, generate_qr_image
from app.utils.pdf_generator import generate_ticket_pdf


def test_qr_code_generation(temp_db):
    """Verify QR code generates valid PNG image and compact JSON payload."""
    booking = booking_repository.find_booking_by_ref("BUS-20261031-100001")
    assert booking is not None

    payload = generate_qr_payload(booking)
    assert "BUS-20261031-100001" in payload
    assert "seat" in payload

    qr_img = generate_qr_image(payload)
    assert qr_img.size[0] > 0
    assert qr_img.size[1] > 0

    qr_bytes = generate_qr_bytes(payload)
    assert len(qr_bytes) > 100
    assert qr_bytes.startswith(b"\x89PNG")


def test_pdf_ticket_generation(temp_db):
    """Verify ReportLab compiles an official PDF document with embedded QR code."""
    booking = booking_repository.find_booking_by_ref("BUS-20261031-100001")
    assert booking is not None

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
        pdf_path = Path(tf.name)

    try:
        out = generate_ticket_pdf(booking, output_path=pdf_path)
        assert out.exists()
        assert out.stat().st_size > 500  # Non-trivial PDF size

        with open(out, "rb") as f:
            header = f.read(5)
            assert header == b"%PDF-"
    finally:
        if pdf_path.exists():
            try:
                pdf_path.unlink()
            except Exception:
                pass

