"""
Ticket Details Dialog.
Renders an elegant digital boarding pass / e-ticket with printable format.
"""
from pathlib import Path
from typing import Any, Dict
from PySide6.QtCore import Qt
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


class TicketDialog(QDialog):
    """Digital E-Ticket view and export modal."""

    def __init__(self, ticket: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.ticket = ticket
        self.setWindowTitle(f"E-Ticket - {ticket['booking_reference']}")
        self.setMinimumWidth(520)
        self.setMaximumHeight(700)
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
        comp_title = QLabel("SMART BUS TRAVELS")
        comp_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #2563EB; letter-spacing: 1px;")
        h_row.addWidget(comp_title)
        h_row.addStretch()

        status_text = self.ticket.get("status", "CONFIRMED")
        status_badge = QLabel(f"● {status_text}")
        if status_text == "CONFIRMED":
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
        p_name = self.ticket.get('full_name', 'N/A')
        p_age = self.ticket.get('age', '')
        p_phone = self.ticket.get('phone', '')
        grid.addWidget(QLabel(f"{p_name} ({p_age} yrs) | {p_phone}"), 5, 1)

        grid.addWidget(QLabel("<b>Amount Paid:</b>"), 6, 0)
        amt_lbl = QLabel(f"<b>Rs. {float(self.ticket['amount']):.2f}</b> ({self.ticket.get('payment_method', 'UPI')})")
        amt_lbl.setTextFormat(Qt.RichText)
        grid.addWidget(amt_lbl, 6, 1)

        if self.ticket.get("cancellation_date"):
            grid.addWidget(QLabel("<b>Cancelled On:</b>"), 7, 0)
            grid.addWidget(QLabel(f"{self.ticket['cancellation_date']} (Refund: {self.ticket.get('payment_status', 'REFUNDED')})"), 7, 1)

        t_layout.addLayout(grid)

        # Barcode visual simulation
        barcode = QLabel("||| | ||||| || | |||| ||| |||| | ||| |||||| | ||||| |||")
        barcode.setAlignment(Qt.AlignCenter)
        barcode.setStyleSheet("font-family: monospace; font-size: 15px; color: #1E293B; margin-top: 6px;")
        t_layout.addWidget(barcode)

        scroll_area.setWidget(ticket_card)
        main_layout.addWidget(scroll_area)

        # Action Buttons (Always pinned visibly at the bottom!)
        btn_layout = QHBoxLayout()
        self.export_btn = QPushButton("📄 Save / Export Ticket (TXT)")
        self.export_btn.clicked.connect(self._handle_export_ticket)
        btn_layout.addWidget(self.export_btn)

        self.close_btn = QPushButton("Close")
        self.close_btn.setProperty("class", "primaryButton")
        self.close_btn.setMinimumHeight(34)
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)

        main_layout.addLayout(btn_layout)

    def _handle_export_ticket(self):
        default_filename = f"Ticket_{self.ticket['booking_reference']}.txt"
        filepath, _ = QFileDialog.getSaveFileName(self, "Save Ticket", default_filename, "Text Files (*.txt)")
        if not filepath:
            return

        ticket_content = f"""
============================================================
              SMART BUS RESERVATION SYSTEM
                     E-TICKET RECEIPT
============================================================
Booking Reference : {self.ticket['booking_reference']}
Booking Status    : {self.ticket['status']}
Booking Date      : {self.ticket.get('booking_date', '')}

PASSENGER DETAILS:
Passenger Name    : {self.ticket.get('full_name', '')}
Age / Gender      : {self.ticket.get('age', '')} / {self.ticket.get('gender', '')}
Contact Phone     : {self.ticket.get('phone', '')}

JOURNEY DETAILS:
Route             : {self.ticket['source']} to {self.ticket['destination']}
Travel Date       : {self.ticket['travel_date']}
Departure Time    : {self.ticket['departure_time']}
Arrival Time      : {self.ticket['arrival_time']}
Bus Name & Number : {self.ticket['bus_name']} ({self.ticket['bus_number']})
Bus Type          : {self.ticket['bus_type']}
Seat Number       : #{self.ticket['seat_number']}

PAYMENT DETAILS:
Fare Amount       : Rs. {float(self.ticket['amount']):.2f}
Payment Method    : {self.ticket.get('payment_method', 'UPI')}
Payment Status    : {self.ticket.get('payment_status', 'PAID')}
============================================================
           Thank you for traveling with Smart Bus!
============================================================
"""
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(ticket_content)
            QMessageBox.information(self, "Export Successful", f"Ticket successfully saved to:\n{filepath}")
        except Exception as err:
            QMessageBox.critical(self, "Export Failed", f"Could not save ticket: {err}")
