"""
Visual Seat Selection Dialog.
Renders an interactive, realistic bus floorplan with aisle, driver cabin indicator,
seat numbers, availability states, and accessible status labels.
"""
from typing import Dict, List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.repositories import booking_repository, schedule_repository


class SeatSelectionDialog(QDialog):
    """Interactive visual seat selection dialog."""
    seat_confirmed = Signal(int)  # Emits chosen seat_number

    def __init__(self, schedule_id: int, parent=None):
        super().__init__(parent)
        self.schedule_id = schedule_id
        self.selected_seat: Optional[int] = None
        self.seat_buttons: Dict[int, QPushButton] = {}
        self.occupied_seats: List[int] = []

        # Load fresh schedule data
        self.schedule = schedule_repository.find_schedule_by_id(self.schedule_id)
        if not self.schedule:
            raise ValueError(f"Schedule #{schedule_id} not found.")

        self.setWindowTitle(f"Select Seat - {self.schedule['bus_name']} ({self.schedule['bus_number']})")
        self.setFixedSize(620, 680)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self._init_ui()
        self._refresh_seats()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(12)

        # Header info
        header_card = QWidget()
        header_card.setObjectName("statCard")
        h_layout = QVBoxLayout(header_card)
        h_layout.setContentsMargins(12, 10, 12, 10)

        route_text = f"Journey: {self.schedule['source']} -> {self.schedule['destination']}"
        date_text = f"Date: {self.schedule['travel_date']}  |  Departure: {self.schedule['departure_time']}  |  Fare: Rs. {self.schedule['fare']:.2f}"
        
        lbl_route = QLabel(route_text)
        lbl_route.setStyleSheet("font-size: 15px; font-weight: 700; color: #0F172A;")
        lbl_meta = QLabel(date_text)
        lbl_meta.setStyleSheet("font-size: 12px; color: #475569;")
        h_layout.addWidget(lbl_route)
        h_layout.addWidget(lbl_meta)
        main_layout.addWidget(header_card)

        # Legend Bar
        legend_layout = QHBoxLayout()
        legend_layout.setAlignment(Qt.AlignCenter)
        legend_layout.setSpacing(20)

        leg_avail = QLabel("🟢 Available")
        leg_avail.setStyleSheet("color: #15803D; font-weight: 600; font-size: 12px;")
        leg_sel = QLabel("🔵 Selected")
        leg_sel.setStyleSheet("color: #1D4ED8; font-weight: 600; font-size: 12px;")
        leg_occ = QLabel("⚪ Occupied (Booked)")
        leg_occ.setStyleSheet("color: #94A3B8; font-weight: 600; font-size: 12px;")

        legend_layout.addWidget(leg_avail)
        legend_layout.addWidget(leg_sel)
        legend_layout.addWidget(leg_occ)
        main_layout.addLayout(legend_layout)

        # Scrollable Bus Interior
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: 1px solid #CBD5E1; border-radius: 8px; background: #FFFFFF; }")

        bus_widget = QWidget()
        self.bus_layout = QVBoxLayout(bus_widget)
        self.bus_layout.setContentsMargins(16, 16, 16, 16)
        self.bus_layout.setSpacing(12)

        # Front / Driver cabin indicator
        driver_bar = QHBoxLayout()
        lbl_front = QLabel("<< BUS FRONT (WINDSHIELD) <<")
        lbl_front.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B; letter-spacing: 1px;")
        driver_seat = QLabel("💺 Driver")
        driver_seat.setStyleSheet("background: #E2E8F0; padding: 4px 10px; border-radius: 4px; font-weight: 600;")
        driver_bar.addWidget(lbl_front)
        driver_bar.addStretch()
        driver_bar.addWidget(driver_seat)
        self.bus_layout.addLayout(driver_bar)

        # Seats Grid (2 left - aisle - 2 right layout)
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(8)
        self.bus_layout.addWidget(self.grid_widget)

        scroll_area.setWidget(bus_widget)
        main_layout.addWidget(scroll_area)

        # Footer selection summary & buttons
        footer_layout = QHBoxLayout()
        self.selection_label = QLabel("No seat selected")
        self.selection_label.setStyleSheet("font-size: 14px; font-weight: 700; color: #0F172A;")
        footer_layout.addWidget(self.selection_label)
        footer_layout.addStretch()

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self._refresh_seats)
        footer_layout.addWidget(self.refresh_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        footer_layout.addWidget(self.cancel_btn)

        self.confirm_btn = QPushButton("Proceed with Booking →")
        self.confirm_btn.setProperty("class", "primaryButton")
        self.confirm_btn.setMinimumHeight(34)
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.clicked.connect(self._handle_confirm)
        footer_layout.addWidget(self.confirm_btn)

        main_layout.addLayout(footer_layout)

    def _refresh_seats(self):
        """Fetches latest occupied seats from database and updates UI."""
        self.occupied_seats = booking_repository.get_occupied_seats(self.schedule_id)
        total_seats = self.schedule["total_seats"]

        # Clear existing grid
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.seat_buttons.clear()

        # Build 2x2 layout with aisle in column 2 (0, 1, [2=aisle], 3, 4)
        col_map = [0, 1, 3, 4]
        current_seat = 1
        row = 0

        while current_seat <= total_seats:
            for c_idx in col_map:
                if current_seat > total_seats:
                    break
                seat_num = current_seat
                btn = QPushButton()
                btn.setFixedSize(54, 46)
                btn.setCursor(Qt.PointingHandCursor)

                is_occupied = seat_num in self.occupied_seats
                if is_occupied:
                    btn.setText(f"{seat_num}\n[OCC]")
                    btn.setEnabled(False)
                    btn.setStyleSheet(
                        "background-color: #F1F5F9; color: #94A3B8; border: 1px dashed #CBD5E1; "
                        "border-radius: 6px; font-size: 10px; font-weight: 700;"
                    )
                else:
                    if self.selected_seat == seat_num:
                        btn.setText(f"{seat_num}\n[SEL]")
                        btn.setStyleSheet(
                            "background-color: #2563EB; color: #FFFFFF; border: 2px solid #1D4ED8; "
                            "border-radius: 6px; font-size: 10px; font-weight: 700;"
                        )
                    else:
                        btn.setText(f"{seat_num}\n[FREE]")
                        btn.setStyleSheet(
                            "background-color: #FFFFFF; color: #166534; border: 1px solid #86EFAC; "
                            "border-radius: 6px; font-size: 10px; font-weight: 600;"
                        )
                    btn.clicked.connect(lambda checked=False, s=seat_num: self._select_seat(s))

                self.grid_layout.addWidget(btn, row, c_idx)
                self.seat_buttons[seat_num] = btn
                current_seat += 1

            # Aisle label in column 2
            lbl_aisle = QLabel("Aisle")
            lbl_aisle.setAlignment(Qt.AlignCenter)
            lbl_aisle.setStyleSheet("color: #CBD5E1; font-size: 9px;")
            self.grid_layout.addWidget(lbl_aisle, row, 2)
            row += 1

        self._update_footer()

    def _select_seat(self, seat_num: int):
        self.selected_seat = seat_num
        self._refresh_seats()

    def _update_footer(self):
        if self.selected_seat:
            self.selection_label.setText(f"Selected Seat: #{self.selected_seat}  |  Fare: Rs. {self.schedule['fare']:.2f}")
            self.confirm_btn.setEnabled(True)
        else:
            self.selection_label.setText("No seat selected")
            self.confirm_btn.setEnabled(False)

    def _handle_confirm(self):
        if not self.selected_seat:
            QMessageBox.information(
                self,
                "Seat Selection Required",
                "Please click on a free seat (green) from the layout before proceeding with booking."
            )
            return
        # Re-check database availability immediately before proceeding
        if not booking_repository.is_seat_available(self.schedule_id, self.selected_seat):
            QMessageBox.warning(
                self,
                "Seat Unavailable",
                f"Seat #{self.selected_seat} was just reserved by another user. Please select another seat."
            )
            self.selected_seat = None
            self._refresh_seats()
            return

        self.seat_confirmed.emit(self.selected_seat)
        self.accept()
