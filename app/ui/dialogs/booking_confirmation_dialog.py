"""
Booking Confirmation Dialog.
Collects and confirms traveler information, simulates payment method,
and performs the ACID reservation transaction.
"""
from typing import Any, Dict, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from app.config import PAYMENT_METHODS
from app.services import auth_service, booking_service


class BookingConfirmationDialog(QDialog):
    """Booking review and confirmation dialog."""
    booking_completed = Signal(dict)  # Emits ticket dictionary

    def __init__(self, schedule: Dict[str, Any], seat_number: int, parent=None):
        super().__init__(parent)
        self.schedule = schedule
        self.seat_number = seat_number
        self.confirmed_ticket: Optional[Dict[str, Any]] = None

        self.setWindowTitle("Confirm Bus Reservation")
        self.setMinimumWidth(500)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 20, 28, 20)
        layout.setSpacing(12)

        title = QLabel("Review & Confirm Reservation")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #0F172A;")
        layout.addWidget(title)

        # Trip Summary GroupBox
        summary_group = QGroupBox("Trip Summary")
        summary_group.setStyleSheet("QGroupBox { font-weight: 700; color: #334155; }")
        sum_layout = QVBoxLayout(summary_group)
        sum_layout.setSpacing(4)

        bus_info = f"<b>Bus:</b> {self.schedule['bus_name']} ({self.schedule['bus_number']}) - {self.schedule['bus_type']}"
        route_info = f"<b>Route:</b> {self.schedule['source']} → {self.schedule['destination']}"
        time_info = f"<b>Date & Time:</b> {self.schedule['travel_date']} at {self.schedule['departure_time']}"
        seat_info = f"<b>Seat Allocated:</b> #{self.seat_number}"
        fare_info = f"<b>Total Fare:</b> <font color='#2563EB' size='+1'><b>Rs. {self.schedule['fare']:.2f}</b></font>"

        for text in [bus_info, route_info, time_info, seat_info, fare_info]:
            lbl = QLabel(text)
            lbl.setTextFormat(Qt.RichText)
            sum_layout.addWidget(lbl)

        layout.addWidget(summary_group)

        # Passenger Details GroupBox
        pass_group = QGroupBox("Passenger Information")
        pass_group.setStyleSheet("QGroupBox { font-weight: 700; color: #334155; }")
        p_layout = QVBoxLayout(pass_group)
        p_layout.setSpacing(8)

        # Autofill if passenger is logged in
        cur_user = auth_service.get_current_user()
        def_name = cur_user.get("name", "") if cur_user else ""
        profile = cur_user.get("passenger_profile") if cur_user else None
        def_age = profile["age"] if profile and profile.get("age") else 28
        def_gen = profile["gender"] if profile and profile.get("gender") else "Male"
        def_phone = profile["phone"] if profile and profile.get("phone") else ""

        p_layout.addWidget(QLabel("Full Name *"))
        self.name_input = QLineEdit(def_name)
        self.name_input.setPlaceholderText("Passenger Name")
        p_layout.addWidget(self.name_input)

        age_gen_row = QHBoxLayout()
        v_age = QVBoxLayout()
        v_age.addWidget(QLabel("Age *"))
        self.age_input = QSpinBox()
        self.age_input.setRange(1, 120)
        self.age_input.setValue(def_age)
        v_age.addWidget(self.age_input)
        age_gen_row.addLayout(v_age)

        v_gen = QVBoxLayout()
        v_gen.addWidget(QLabel("Gender"))
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["Male", "Female", "Other"])
        if def_gen in ["Male", "Female", "Other"]:
            self.gender_combo.setCurrentText(def_gen)
        v_gen.addWidget(self.gender_combo)
        age_gen_row.addLayout(v_gen)
        p_layout.addLayout(age_gen_row)

        p_layout.addWidget(QLabel("Phone Number"))
        self.phone_input = QLineEdit(def_phone)
        self.phone_input.setPlaceholderText("10-digit mobile number")
        p_layout.addWidget(self.phone_input)

        layout.addWidget(pass_group)

        # Simulated Payment Method
        pay_group = QGroupBox("Simulated Payment Method")
        pay_group.setStyleSheet("QGroupBox { font-weight: 700; color: #334155; }")
        pay_layout = QVBoxLayout(pay_group)
        self.payment_combo = QComboBox()
        self.payment_combo.addItems(PAYMENT_METHODS)
        pay_layout.addWidget(self.payment_combo)

        pay_note = QLabel("ℹ Simulated transaction for DBMS demonstration. No real money required.")
        pay_note.setStyleSheet("font-size: 11px; color: #64748B;")
        pay_layout.addWidget(pay_note)
        layout.addWidget(pay_group)

        # Action Buttons
        btn_row = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.cancel_btn)

        self.confirm_btn = QPushButton(f"Pay Rs. {self.schedule['fare']:.2f} & Confirm")
        self.confirm_btn.setProperty("class", "primaryButton")
        self.confirm_btn.setFixedHeight(38)
        self.confirm_btn.clicked.connect(self._handle_confirm_booking)
        btn_row.addWidget(self.confirm_btn)

        layout.addLayout(btn_row)

    def _handle_confirm_booking(self):
        full_name = self.name_input.text().strip()
        age = self.age_input.value()
        gender = self.gender_combo.currentText()
        phone = self.phone_input.text().strip()
        pmethod = self.payment_combo.currentText()

        if not full_name:
            QMessageBox.warning(self, "Validation Error", "Passenger full name is required.")
            return

        cur_user = auth_service.get_current_user()
        user_id = cur_user["user_id"] if cur_user else None

        try:
            ticket = booking_service.reserve_seat(
                schedule_id=self.schedule["schedule_id"],
                seat_number=self.seat_number,
                full_name=full_name,
                age=age,
                gender=gender,
                phone=phone,
                payment_method=pmethod,
                user_id=user_id
            )
            self.confirmed_ticket = ticket
            self.booking_completed.emit(ticket)
            self.accept()
        except ValueError as err:
            QMessageBox.critical(self, "Booking Failed", str(err))
