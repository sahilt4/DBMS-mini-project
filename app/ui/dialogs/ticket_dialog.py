"""
Ticket Details Dialog.
Renders an elegant digital boarding pass / e-ticket with live QR code and PDF export.
"""
from pathlib import Path
from typing import Any, Dict
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.utils.qr_generator import generate_qr_payload, generate_qr_bytes
from app.utils.pdf_generator import generate_ticket_pdf


class TicketDialog(QDialog):
    """Digital E-Ticket view and export modal with QR code and PDF support."""

    def __init__(self, ticket: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.ticket = ticket
        self.setWindowTitle(f"E-Ticket - {ticket['booking_reference']}")
        self.setMinimumWidth(540)
        self.setMaximumHeight(740)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(12)

        # Scrollable area for ticket details so it never exceeds screen height
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        # Ticket Card (Boarding Pass design)
        ticket_card = QWidget()
        ticket_card.setStyleSheet(
            "background-color: #FFFFFF; border: 2px solid #2563EB; border-radius: 12px; padding: 16px;"
        )
        t_layout = QVBoxLayout(ticket_card)
        t_layout.setSpacing(10)

        # Header: Company & Reference
        h_row = QHBoxLayout()
        comp_title = QLabel("BUS RESERVATION & MANAGEMENT SYSTEM")
        comp_title.setStyleSheet("font-size: 15px; font-weight: 800; color: #1E3A8A; letter-spacing: 0.5px;")
        h_row.addWidget(comp_title)
        h_row.addStretch()

        status_text = self.ticket.get("status", self.ticket.get("booking_status", "CONFIRMED"))
        status_badge = QLabel(f"● {status_text}")
        if status_text in ("CONFIRMED", "CHECKED_IN"):
            status_badge.setStyleSheet(
                "background: #DCFCE7; color: #15803D; font-weight: 700; padding: 4px 10px; border-radius: 10px;"
            )
        else:
            status_badge.setStyleSheet(
                "background: #FEE2E2; color: #B91C1C; font-weight: 700; padding: 4px 10px; border-radius: 10px;"
            )
        h_row.addWidget(status_badge)
        t_layout.addLayout(h_row)

        ref_lbl = QLabel(f"Booking Reference: <b>{self.ticket['booking_reference']}</b>")
        ref_lbl.setTextFormat(Qt.RichText)
        ref_lbl.setStyleSheet("font-size: 13px; color: #334155;")
        t_layout.addWidget(ref_lbl)

        # Divider line
        div1 = QFrame()
        div1.setFrameShape(QFrame.HLine)
        div1.setStyleSheet("color: #E2E8F0;")
        t_layout.addWidget(div1)

        # Route & Journey
        grid = QGridLayout()
        grid.setSpacing(8)

        grid.addWidget(QLabel("<b>Route:</b>"), 0, 0)
        grid.addWidget(QLabel(f"{self.ticket['source']} → {self.ticket['destination']}"), 0, 1)

        grid.addWidget(QLabel("<b>Travel Date:</b>"), 1, 0)
        grid.addWidget(QLabel(f"{self.ticket['travel_date']}"), 1, 1)

        grid.addWidget(QLabel("<b>Timings:</b>"), 2, 0)
        grid.addWidget(QLabel(f"{self.ticket['departure_time']} - {self.ticket['arrival_time']}"), 2, 1)

        grid.addWidget(QLabel("<b>Bus Details:</b>"), 3, 0)
        grid.addWidget(QLabel(f"{self.ticket['bus_name']} ({self.ticket['bus_number']}) - {self.ticket['bus_type']}"), 3, 1)

        grid.addWidget(QLabel("<b>Seat Number:</b>"), 4, 0)
        seat_lbl = QLabel(f"<font color='#2563EB' size='+2'><b>Seat #{self.ticket['seat_number']}</b></font>")
        seat_lbl.setTextFormat(Qt.RichText)
        grid.addWidget(seat_lbl, 4, 1)

        grid.addWidget(QLabel("<b>Passenger:</b>"), 5, 0)
        p_name = self.ticket.get('passenger_name', self.ticket.get('full_name', 'N/A'))
        p_age = self.ticket.get('age', '')
        p_phone = self.ticket.get('phone', '')
        grid.addWidget(QLabel(f"{p_name} ({p_age} yrs) | {p_phone}"), 5, 1)

        grid.addWidget(QLabel("<b>Amount Paid:</b>"), 6, 0)
        amt_val = float(self.ticket.get('amount', self.ticket.get('total_amount', 0)))
        amt_lbl = QLabel(f"<b>Rs. {amt_val:.2f}</b> ({self.ticket.get('payment_method', 'UPI')})")
        amt_lbl.setTextFormat(Qt.RichText)
        grid.addWidget(amt_lbl, 6, 1)

        if self.ticket.get("cancellation_date"):
            grid.addWidget(QLabel("<b>Cancelled On:</b>"), 7, 0)
            grid.addWidget(QLabel(f"{self.ticket['cancellation_date']}"), 7, 1)

        t_layout.addLayout(grid)

        # Real QR Code Generation & Display
        qr_row = QHBoxLayout()
        qr_row.addStretch()

        qr_box = QVBoxLayout()
        qr_box.setAlignment(Qt.AlignCenter)

        try:
            payload = generate_qr_payload(self.ticket)
            qr_bytes = generate_qr_bytes(payload)
            qimg = QImage.fromData(qr_bytes)
            pixmap = QPixmap.fromImage(qimg).scaled(140, 140, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            qr_label = QLabel()
            qr_label.setPixmap(pixmap)
            qr_label.setAlignment(Qt.AlignCenter)
            qr_box.addWidget(qr_label)
        except Exception:
            qr_box.addWidget(QLabel("[QR Verification Available]"))

        caption = QLabel("Scan with Conductor App to Verify")
        caption.setStyleSheet("font-size: 11px; color: #64748B; font-weight: 500;")
        caption.setAlignment(Qt.AlignCenter)
        qr_box.addWidget(caption)

        qr_row.addLayout(qr_box)
        qr_row.addStretch()
        t_layout.addLayout(qr_row)

        scroll_area.setWidget(ticket_card)
        main_layout.addWidget(scroll_area)

        # Action Buttons (Always pinned visibly at the bottom!)
        btn_layout = QHBoxLayout()
        self.pdf_btn = QPushButton("📄 Download PDF Ticket")
        self.pdf_btn.setProperty("class", "primaryButton")
        self.pdf_btn.clicked.connect(self._handle_export_pdf)
        btn_layout.addWidget(self.pdf_btn)

        self.close_btn = QPushButton("Close")
        self.close_btn.setMinimumHeight(34)
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)

        main_layout.addLayout(btn_layout)

    def _handle_export_pdf(self):
        default_filename = f"Ticket_{self.ticket['booking_reference']}.pdf"
        filepath, _ = QFileDialog.getSaveFileName(self, "Save E-Ticket (PDF)", default_filename, "PDF Documents (*.pdf)")
        if not filepath:
            return

        try:
            target_path = Path(filepath)
            generate_ticket_pdf(self.ticket, output_path=target_path)
            QMessageBox.information(self, "Export Successful", f"Official PDF E-Ticket successfully saved to:\n{target_path}")
        except Exception as err:
            QMessageBox.critical(self, "Export Failed", f"Could not save PDF ticket: {err}")
