"""
Schedule Dialog for Creating or Editing bus schedules with conflict validation.
"""
from datetime import date, datetime
from typing import Any, Dict, Optional
from PySide6.QtCore import QDate, QTime, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTimeEdit,
    QVBoxLayout,
)

from app.repositories import bus_repository, route_repository, schedule_repository
from app.services import schedule_service


class ScheduleDialog(QDialog):
    """Modal for scheduling a bus on a route with departure/arrival timings and fare."""

    def __init__(self, schedule: Optional[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        self.schedule = schedule
        self.is_edit = schedule is not None

        title = "Edit Schedule" if self.is_edit else "Create Bus Schedule"
        self.setWindowTitle(title)
        self.setMinimumWidth(480)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # Load available buses and routes
        self.buses = bus_repository.list_buses(is_active=1)
        self.routes = route_repository.list_routes(is_active=1)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        header = QLabel("Edit Schedule" if self.is_edit else "Create New Schedule")
        header.setStyleSheet("font-size: 16px; font-weight: 700; color: #0F172A;")
        layout.addWidget(header)

        # Bus Select
        layout.addWidget(QLabel("Select Active Bus *"))
        self.bus_combo = QComboBox()
        for b in self.buses:
            self.bus_combo.addItem(f"{b['bus_number']} - {b['bus_name']} ({b['bus_type']})", b["bus_id"])
        if self.is_edit:
            idx = self.bus_combo.findData(self.schedule["bus_id"])
            if idx >= 0:
                self.bus_combo.setCurrentIndex(idx)
        layout.addWidget(self.bus_combo)

        # Route Select
        layout.addWidget(QLabel("Select Active Route *"))
        self.route_combo = QComboBox()
        for r in self.routes:
            self.route_combo.addItem(f"{r['source']} → {r['destination']} ({r['distance_km']} km)", r["route_id"])
        if self.is_edit:
            idx = self.route_combo.findData(self.schedule["route_id"])
            if idx >= 0:
                self.route_combo.setCurrentIndex(idx)
        layout.addWidget(self.route_combo)

        # Travel Date
        layout.addWidget(QLabel("Travel Date *"))
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("yyyy-MM-dd")
        if self.is_edit:
            dt = datetime.strptime(self.schedule["travel_date"], "%Y-%m-%d")
            self.date_input.setDate(QDate(dt.year, dt.month, dt.day))
        else:
            today = date.today()
            self.date_input.setDate(QDate(today.year, today.month, today.day))
        layout.addWidget(self.date_input)

        # Timings Row
        time_row = QHBoxLayout()
        time_row.setSpacing(14)
        v_dep = QVBoxLayout()
        v_dep.setSpacing(4)
        v_dep.addWidget(QLabel("Departure Time *"))
        self.dep_time = QTimeEdit()
        self.dep_time.setDisplayFormat("HH:mm")
        if self.is_edit:
            t = datetime.strptime(self.schedule["departure_time"], "%H:%M")
            self.dep_time.setTime(QTime(t.hour, t.minute))
        else:
            self.dep_time.setTime(QTime(8, 0))
        v_dep.addWidget(self.dep_time)
        time_row.addLayout(v_dep)

        v_arr = QVBoxLayout()
        v_arr.setSpacing(4)
        v_arr.addWidget(QLabel("Arrival Time *"))
        self.arr_time = QTimeEdit()
        self.arr_time.setDisplayFormat("HH:mm")
        if self.is_edit:
            t = datetime.strptime(self.schedule["arrival_time"], "%H:%M")
            self.arr_time.setTime(QTime(t.hour, t.minute))
        else:
            self.arr_time.setTime(QTime(12, 30))
        v_arr.addWidget(self.arr_time)
        time_row.addLayout(v_arr)
        layout.addLayout(time_row)

        # Ticket Fare
        layout.addWidget(QLabel("Ticket Fare (Rs.) *"))
        self.fare_input = QDoubleSpinBox()
        self.fare_input.setRange(10.0, 10000.0)
        self.fare_input.setDecimals(2)
        self.fare_input.setValue(self.schedule["fare"] if self.is_edit else 450.0)
        layout.addWidget(self.fare_input)

        # Status (if edit)
        if self.is_edit:
            layout.addWidget(QLabel("Schedule Status"))
            self.status_combo = QComboBox()
            self.status_combo.addItems(["SCHEDULED", "COMPLETED", "CANCELLED"])
            self.status_combo.setCurrentText(self.schedule["status"])
            layout.addWidget(self.status_combo)

        layout.addSpacing(10)

        # Buttons
        btn_row = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("Save Schedule")
        self.save_btn.setProperty("class", "primaryButton")
        self.save_btn.clicked.connect(self._handle_save)
        btn_row.addWidget(self.save_btn)

        layout.addLayout(btn_row)

    def _handle_save(self):
        bus_id = self.bus_combo.currentData()
        route_id = self.route_combo.currentData()
        tdate = self.date_input.date().toString("yyyy-MM-dd")
        deptime = self.dep_time.time().toString("HH:mm")
        arrtime = self.arr_time.time().toString("HH:mm")
        fare = self.fare_input.value()

        if not bus_id:
            QMessageBox.warning(self, "Validation", "Please select a bus.")
            return
        if not route_id:
            QMessageBox.warning(self, "Validation", "Please select a route.")
            return

        try:
            if self.is_edit:
                status = self.status_combo.currentText()
                schedule_repository.update_schedule(
                    schedule_id=self.schedule["schedule_id"],
                    bus_id=bus_id,
                    route_id=route_id,
                    travel_date=tdate,
                    departure_time=deptime,
                    arrival_time=arrtime,
                    fare=fare,
                    status=status
                )
            else:
                schedule_service.create_new_schedule(
                    bus_id=bus_id,
                    route_id=route_id,
                    travel_date=tdate,
                    departure_time=deptime,
                    arrival_time=arrtime,
                    fare=fare
                )
            self.accept()
        except Exception as err:
            QMessageBox.critical(self, "Schedule Error", str(err))
