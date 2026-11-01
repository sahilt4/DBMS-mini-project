"""
My Bookings Page for Passengers (and All Bookings lookup for Admin).
Enforces user-level data isolation, displays digital ticket receipts,
and provides atomic cancellation with automatic refund and seat release.
"""
from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.repositories import booking_repository
from app.services import auth_service, cancellation_service
from app.ui.dialogs.ticket_dialog import TicketDialog


class MyBookingsPage(QWidget):
    """Passenger booking history and cancellation management."""
    booking_status_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.bookings = []
        self._init_ui()
        self.refresh_bookings()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header Title
        v_title = QVBoxLayout()
        self.title_lbl = QLabel("My Ticket Bookings")
        self.title_lbl.setObjectName("pageTitle")
        self.sub_lbl = QLabel("View your confirmed and historical bus reservations and digital receipts")
        self.sub_lbl.setObjectName("pageDescription")
        v_title.addWidget(self.title_lbl)
        v_title.addWidget(self.sub_lbl)
        layout.addLayout(v_title)

        # Filters Card
        filter_card = QWidget()
        filter_card.setObjectName("statCard")
        f_layout = QHBoxLayout(filter_card)
        f_layout.setContentsMargins(14, 10, 14, 10)
        f_layout.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by booking reference (e.g. BUS-20261026-...)")
        self.search_input.textChanged.connect(self.refresh_bookings)
        f_layout.addWidget(self.search_input, 2)

        self.status_combo = QComboBox()
        self.status_combo.addItem("All Statuses", "All")
        self.status_combo.addItem("CONFIRMED Only", "CONFIRMED")
        self.status_combo.addItem("CANCELLED Only", "CANCELLED")
        self.status_combo.currentIndexChanged.connect(self.refresh_bookings)
        f_layout.addWidget(self.status_combo, 1)

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh_bookings)
        f_layout.addWidget(self.refresh_btn)

        layout.addWidget(filter_card)

        # Bookings Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Booking Reference", "Passenger", "Bus Details", "Route",
            "Travel Date", "Seat #", "Amount", "Status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self._view_selected_ticket)
        layout.addWidget(self.table)

        # Actions Row
        action_row = QHBoxLayout()
        self.view_ticket_btn = QPushButton("🎫 View & Print Ticket")
        self.view_ticket_btn.setProperty("class", "primaryButton")
        self.view_ticket_btn.clicked.connect(self._view_selected_ticket)
        action_row.addWidget(self.view_ticket_btn)

        self.cancel_btn = QPushButton("❌ Cancel Reservation")
        self.cancel_btn.setProperty("class", "dangerButton")
        self.cancel_btn.clicked.connect(self._cancel_selected_booking)
        action_row.addWidget(self.cancel_btn)

        action_row.addStretch()
        layout.addLayout(action_row)

    def refresh_bookings(self):
        cur_user = auth_service.get_current_user()
        if not cur_user:
            self.table.setRowCount(0)
            return

        is_admin_user = auth_service.is_admin()
        search = self.search_input.text().strip()
        status = self.status_combo.currentData()

        if is_admin_user:
            self.title_lbl.setText("All Customer Bookings (Admin View)")
            self.sub_lbl.setText("Auditing all bookings across the entire bus reservation network")
            self.bookings = booking_repository.get_all_bookings(
                search=search if search else None,
                status=status if status != "All" else None
            )
        else:
            self.title_lbl.setText("My Ticket Bookings")
            self.sub_lbl.setText("View your confirmed reservations and access digital boarding passes")
            self.bookings = booking_repository.get_passenger_bookings(
                user_id=cur_user["user_id"],
                search_ref=search if search else None,
                status=status if status != "All" else None
            )

        self.table.setRowCount(len(self.bookings))
        for row_idx, b in enumerate(self.bookings):
            bus_str = f"{b['bus_name']} ({b['bus_number']})"
            route_str = f"{b['source']} → {b['destination']}"
            seat_str = f"Seat #{b['seat_number']}"
            amt_str = f"Rs. {b['amount']:.2f}"

            self.table.setItem(row_idx, 0, QTableWidgetItem(b["booking_reference"]))
            self.table.setItem(row_idx, 1, QTableWidgetItem(b["full_name"]))
            self.table.setItem(row_idx, 2, QTableWidgetItem(bus_str))
            self.table.setItem(row_idx, 3, QTableWidgetItem(route_str))
            self.table.setItem(row_idx, 4, QTableWidgetItem(f"{b['travel_date']} {b['departure_time']}"))
            self.table.setItem(row_idx, 5, QTableWidgetItem(seat_str))
            self.table.setItem(row_idx, 6, QTableWidgetItem(amt_str))

            stat = str(b.get("status", "CONFIRMED")).upper()
            if stat == "CONFIRMED":
                status_item = QTableWidgetItem("🟢 Completed")
                status_item.setForeground(Qt.darkGreen)
            elif stat == "CANCELLED":
                status_item = QTableWidgetItem("🔴 Cancelled")
                status_item.setForeground(Qt.darkRed)
            else:
                status_item = QTableWidgetItem("🟡 Pending")
                status_item.setForeground(Qt.darkYellow)
            self.table.setItem(row_idx, 7, status_item)

    def _view_selected_ticket(self):
        cur_row = self.table.currentRow()
        if cur_row < 0 or cur_row >= len(self.bookings):
            QMessageBox.information(self, "Selection Required", "Please select a booking to view its ticket.")
            return

        b = self.bookings[cur_row]
        ticket = booking_repository.find_booking_by_id(b["booking_id"])
        if ticket:
            dialog = TicketDialog(ticket=ticket, parent=self)
            dialog.exec()

    def _cancel_selected_booking(self):
        cur_row = self.table.currentRow()
        if cur_row < 0 or cur_row >= len(self.bookings):
            QMessageBox.information(self, "Selection Required", "Please select a booking to cancel.")
            return

        selected_b = self.bookings[cur_row]
        if selected_b["status"] == "CANCELLED":
            QMessageBox.information(self, "Already Cancelled", "This reservation has already been cancelled.")
            return

        cur_user = auth_service.get_current_user()
        confirm = QMessageBox.question(
            self,
            "Confirm Cancellation",
            f"Are you sure you want to cancel booking '{selected_b['booking_reference']}'?\n\n"
            f"Passenger: {selected_b['full_name']}\n"
            f"Seat: #{selected_b['seat_number']}\n"
            f"Refund Amount: Rs. {selected_b['amount']:.2f}\n\n"
            f"Note: This will release your seat for other passengers.",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            try:
                cancellation_service.cancel_booking(
                    booking_id=selected_b["booking_id"],
                    acting_user_id=cur_user["user_id"] if cur_user else None,
                    is_admin=auth_service.is_admin()
                )
                QMessageBox.information(
                    self,
                    "Cancellation Complete",
                    f"Booking '{selected_b['booking_reference']}' has been cancelled.\n"
                    f"Refund status set to 'REFUNDED' and Seat #{selected_b['seat_number']} is released."
                )
                self.refresh_bookings()
                self.booking_status_changed.emit()
            except Exception as err:
                QMessageBox.critical(self, "Cancellation Failed", str(err))
