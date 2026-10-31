"""
PDF E-Ticket / Boarding Pass generator using ReportLab.
Produces academic-grade, printable digital tickets with embedded QR codes.
"""
import io
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as ReportLabImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from app.utils.qr_generator import generate_qr_payload, generate_qr_image


def generate_ticket_pdf(booking: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Generates a PDF boarding pass for the given booking and saves to output_path.
    If output_path is not specified, saves to a temporary file.
    """
    if output_path is None:
        temp_dir = Path(tempfile.gettempdir()) / "brms_tickets"
        temp_dir.mkdir(parents=True, exist_ok=True)
        output_path = temp_dir / f"{booking['booking_reference']}.pdf"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    story = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "TicketTitle",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1E3A8A"),
        alignment=1  # Center
    )
    subtitle_style = ParagraphStyle(
        "TicketSubTitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748B"),
        alignment=1
    )
    header_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=10,
        spaceAfter=5
    )

    # 1. Header Banner
    story.append(Paragraph("BUS RESERVATION & MANAGEMENT SYSTEM", title_style))
    story.append(Paragraph("Official E-Ticket & Digital Boarding Pass", subtitle_style))
    story.append(Spacer(1, 15))

    # 2. Key Summary Bar (Booking Ref & Seat)
    ref = booking["booking_reference"]
    seat = booking["seat_number"]
    status = booking.get("booking_status", booking.get("status", "CONFIRMED"))
    summary_data = [
        [
            Paragraph(f"<b>Booking Reference:</b><br/><font size=14 color='#1E3A8A'>{ref}</font>", styles["Normal"]),
            Paragraph(f"<b>Seat Allocated:</b><br/><font size=16 color='#2563EB'>#{seat}</font>", styles["Normal"]),
            Paragraph(f"<b>Status:</b><br/><font size=13 color='#16A34A'>{status}</font>", styles["Normal"])
        ]
    ]
    t_summary = Table(summary_data, colWidths=[220, 160, 160])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F1F5F9")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(t_summary)
    story.append(Spacer(1, 15))

    # 3. Journey & Schedule Details
    story.append(Paragraph("JOURNEY INFORMATION", header_style))
    src = booking.get("source", "")
    dst = booking.get("destination", "")
    bname = booking.get("bus_name", "")
    btype = booking.get("bus_type", "")
    dep = str(booking.get("departure_datetime", booking.get("departure_time", "")))
    arr = str(booking.get("arrival_datetime", booking.get("arrival_time", "")))

    journey_data = [
        ["Origin (Source):", src, "Destination:", dst],
        ["Departure Datetime:", dep, "Arrival Datetime:", arr],
        ["Bus Operator / Name:", bname, "Bus Category:", btype]
    ]
    t_journey = Table(journey_data, colWidths=[130, 140, 130, 140])
    t_journey.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor("#1E293B")),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_journey)
    story.append(Spacer(1, 15))

    # 4. Passenger & Payment Information
    story.append(Paragraph("PASSENGER & PAYMENT DETAILS", header_style))
    pname = booking.get("passenger_name", booking.get("full_name", ""))
    age = booking.get("age", "")
    gender = booking.get("gender", "")
    phone = booking.get("phone", "")
    amount = f"Rs. {booking.get('total_amount', booking.get('amount', 0)):.2f}"
    pmethod = booking.get("payment_method", "N/A")

    passenger_data = [
        ["Passenger Name:", pname, "Age / Gender:", f"{age} yrs / {gender}"],
        ["Contact Phone:", phone, "Payment Method:", pmethod],
        ["Total Ticket Fare:", amount, "Payment Status:", "PAID"]
    ]
    t_passenger = Table(passenger_data, colWidths=[130, 140, 130, 140])
    t_passenger.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor("#1E293B")),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_passenger)
    story.append(Spacer(1, 15))

    # 5. QR Code Section for Conductor Verification
    story.append(Paragraph("DIGITAL VERIFICATION QR CODE", header_style))
    qr_payload = generate_qr_payload(booking)
    qr_img = generate_qr_image(qr_payload, box_size=4, border=1)

    qr_temp_file = Path(tempfile.gettempdir()) / f"qr_{ref}.png"
    qr_img.save(str(qr_temp_file))

    qr_flowable = ReportLabImage(str(qr_temp_file), width=1.4*inch, height=1.4*inch)
    qr_text = Paragraph(
        "<b>Notice to Conductor:</b><br/>"
        "Scan this QR code with the BRMS Conductor Mobile/Desktop Scanner to automatically record passenger boarding.<br/><br/>"
        "<font size=8 color='#64748B'>Payload: " + ref + " | Seat #" + str(seat) + "</font>",
        styles["Normal"]
    )

    qr_table = Table([[qr_flowable, qr_text]], colWidths=[120, 420])
    qr_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 8),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#E2E8F0")),
    ]))
    story.append(qr_table)
    story.append(Spacer(1, 20))

    # 6. Terms and Conditions footer
    notice_text = Paragraph(
        "<font size=7 color='#64748B'><b>IMPORTANT PASSENGER INSTRUCTIONS:</b><br/>"
        "1. Passengers must report at the boarding terminal at least 15 minutes before the departure time.<br/>"
        "2. Please carry a valid government-issued photo identification along with this digital or printed e-ticket.<br/>"
        "3. Cancellations are permitted in accordance with the BRMS tiered refund policy (up to 90% refund if cancelled 24+ hrs prior).<br/>"
        "4. This is a computer-generated transaction record validated through the BRMS relational database.</font>",
        styles["Normal"]
    )
    story.append(notice_text)

    # Build PDF
    doc.build(story)

    # Cleanup temp QR image
    try:
        if qr_temp_file.exists():
            qr_temp_file.unlink()
    except Exception:
        pass

    return output_path
