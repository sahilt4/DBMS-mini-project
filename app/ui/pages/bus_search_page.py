"""
Passenger Bus Search Page.
Allows travelers to search upcoming bus schedules by source, destination, and travel date,
view live seat availability, and initiate visual seat booking.
"""
from datetime import date, datetime
from typing import Optional
from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.repositories import route_repository, schedule_repository
from app.ui.dialogs.booking_confirmation_dialog import BookingConfirmationDialog
from app.ui.dialogs.seat_selection_dialog import SeatSelectionDialog
from app.ui.dialogs.ticket_dialog import TicketDialog


class BusSearchPage(QWidget):
    """Bus and schedule discovery page for passengers."""
    booking_made = Signal()  # Emitted when a booking successfully completes

    def __init__(self, parent=None):
        super().__init__(parent)
        self.schedules = []
        self._init_ui()
        self.populate_city_filters()
        self.perform_search()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Header Title
        title_box = QVBoxLayout()
        title = QLabel("Find & Book Bus Tickets")
        title.setObjectName("pageTitle")
        sub = QLabel("Search scheduled bus journeys, check live seat availability, and book your seat")
        sub.setObjectName("pageDescription")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        layout.addLayout(title_box)

        # Search Controls Card
        search_card = QWidget()
        search_card.setObjectName("statCard")
        sc_layout = QHBoxLayout(search_card)
        sc_layout.setContentsMargins(16, 12, 16, 12)
        sc_layout.setSpacing(12)

        # Source
        v_src = QVBoxLayout()
        v_src.addWidget(QLabel("Departure City (Source)"))
        self.source_combo = QComboBox()
        self.source_combo.setMinimumWidth(160)
        v_src.addWidget(self.source_combo)
        sc_layout.addLayout(v_src)

        # Destination
        v_dst = QVBoxLayout()
        v_dst.addWidget(QLabel("Arrival City (Destination)"))
        self.dest_combo = QComboBox()
        self.dest_combo.setMinimumWidth(160)
        v_dst.addWidget(self.dest_combo)
        sc_layout.addLayout(v_dst)

        # Travel Date
        v_date = QVBoxLayout()
        v_date.addWidget(QLabel("Travel Date"))
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("yyyy-MM-dd")
        today = date.today()
        self.date_input.setDate(QDate(today.year, today.month, today.day))
        v_date.addWidget(self.date_input)
        sc_layout.addLayout(v_date)

        # Search Button
        v_btn = QVBoxLayout()
        v_btn.addSpacing(16)
        self.search_btn = QPushButton("🔍 Search Buses")
        self.search_btn.setProperty("class", "primaryButton")
        self.search_btn.setFixedHeight(36)
        self.search_btn.clicked.connect(self.perform_search)
        v_btn.addWidget(self.search_btn)
        sc_layout.addLayout(v_btn)

        # Show All Button
        v_all = QVBoxLayout()
        v_all.addSpacing(16)
        self.show_all_btn = QPushButton("Show All")
        self.show_all_btn.setFixedHeight(36)
        self.show_all_btn.clicked.connect(self.show_all_schedules)
        v_all.addWidget(self.show_all_btn)
        sc_layout.addLayout(v_all)

        layout.addWidget(search_card)

        # Results summary label
        self.results_label = QLabel("Available Journeys")
        self.results_label.setStyleSheet("font-size: 14px; font-weight: 700; color: #0F172A;")
        layout.addWidget(self.results_label)

        # Schedules Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Bus Operator & Number", "Type", "Route", "Timings",
            "Travel Date", "Fare", "Available Seats", "Action"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Fixed)
        self.table.setColumnWidth(7, 130)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(48)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

    def populate_city_filters(self):
        """Populates source and destination dropdowns with active routes from DB."""
        sources = route_repository.get_unique_sources()
        destinations = route_repository.get_unique_destinations()

        self.source_combo.clear()
        self.source_combo.addItem("All Sources", "")
        for s in sources:
            self.source_combo.addItem(s, s)

        self.dest_combo.clear()
        self.dest_combo.addItem("All Destinations", "")
        for d in destinations:
            self.dest_combo.addItem(d, d)

    def perform_search(self):
        src = self.source_combo.currentData()
        dst = self.dest_combo.currentData()
        tdate = self.date_input.date().toString("yyyy-MM-dd")

        self.schedules = schedule_repository.search_schedules(
            source=src if src else None,
            destination=dst if dst else None,
            travel_date=tdate,
            status="SCHEDULED"
        )
        self._populate_table()

    def show_all_schedules(self):
        self.source_combo.setCurrentIndex(0)
        self.dest_combo.setCurrentIndex(0)
        self.schedules = schedule_repository.search_schedules(status="SCHEDULED")
        self._populate_table()

    def _populate_table(self):
        self.table.setRowCount(len(self.schedules))
        self.results_label.setText(f"Found {len(self.schedules)} Available Schedules")

        for row_idx, s in enumerate(self.schedules):
            bus_info = f"{s['bus_name']} ({s['bus_number']})"
            route_info = f"{s['source']} → {s['destination']}"
            timings = f"{s['departure_time']} - {s['arrival_time']}"
            fare_str = f"Rs. {s['fare']:.2f}"
            avail_str = f"{s['available_seats']} of {s['total_seats']} seats"

            self.table.setItem(row_idx, 0, QTableWidgetItem(bus_info))
            self.table.setItem(row_idx, 1, QTableWidgetItem(s["bus_type"]))
            self.table.setItem(row_idx, 2, QTableWidgetItem(route_info))
            self.table.setItem(row_idx, 3, QTableWidgetItem(timings))
            self.table.setItem(row_idx, 4, QTableWidgetItem(s["travel_date"]))
            self.table.setItem(row_idx, 5, QTableWidgetItem(fare_str))
            
            avail_item = QTableWidgetItem(avail_str)
            if s["available_seats"] <= 5:
                avail_item.setForeground(Qt.red)
            else:
                avail_item.setForeground(Qt.darkGreen)
            self.table.setItem(row_idx, 6, avail_item)

            # Book button
            book_btn = QPushButton("Select Seat")
            book_btn.setCursor(Qt.PointingHandCursor)
            book_btn.setStyleSheet(
                "QPushButton { background-color: #2563EB; color: #FFFFFF; font-weight: 600; "
                "font-size: 12px; border-radius: 6px; padding: 6px 12px; min-height: 28px; min-width: 100px; border: 1px solid #1D4ED8; } "
                "QPushButton:hover { background-color: #1D4ED8; } "
                "QPushButton:pressed { background-color: #1E40AF; } "
                "QPushButton:disabled { background-color: #CBD5E1; color: #64748B; border: 1px solid #94A3B8; }"
            )
            if s["available_seats"] <= 0:
                book_btn.setText("Sold Out")
                book_btn.setEnabled(False)
            else:
                book_btn.clicked.connect(lambda checked=False, sched=s: self._start_seat_selection(sched))

            self.table.setCellWidget(row_idx, 7, book_btn)

    def _start_seat_selection(self, sched):
        """Opens Visual Seat Selection dialog, followed by confirmation and ticket receipt."""
        dialog = SeatSelectionDialog(schedule_id=sched["schedule_id"], parent=self.window())
        res = dialog.exec()
        if (res == QDialog.Accepted or res == 1) and dialog.selected_seat:
            chosen_seat = dialog.selected_seat
            # Open booking confirmation
            confirm_dialog = BookingConfirmationDialog(schedule=sched, seat_number=chosen_seat, parent=self.window())
            c_res = confirm_dialog.exec()
            if (c_res == QDialog.Accepted or c_res == 1) and confirm_dialog.confirmed_ticket:
                # Show confirmed ticket
                ticket_dialog = TicketDialog(ticket=confirm_dialog.confirmed_ticket, parent=self.window())
                ticket_dialog.exec()
                self.booking_made.emit()
                self.perform_search()  # Refresh available seats table
