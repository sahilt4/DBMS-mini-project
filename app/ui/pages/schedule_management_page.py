"""
Schedule Management Page for Administrators.
Provides creation, editing, conflict checking, filtering, and cancellation of journeys.
"""
from typing import Optional
from PySide6.QtCore import Qt
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

from app.repositories import schedule_repository
from app.ui.dialogs.schedule_dialog import ScheduleDialog


class ScheduleManagementPage(QWidget):
    """Schedule administration page."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.schedules = []
        self._init_ui()
        self.refresh_schedules()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header Title and Create Button
        header_row = QHBoxLayout()
        v_title = QVBoxLayout()
        title = QLabel("Bus Schedule Management")
        title.setObjectName("pageTitle")
        sub = QLabel("Assign buses to routes, set departure timings, fares, and journey statuses")
        sub.setObjectName("pageDescription")
        v_title.addWidget(title)
        v_title.addWidget(sub)
        header_row.addLayout(v_title)
        header_row.addStretch()

        self.add_btn = QPushButton("➕ Create New Schedule")
        self.add_btn.setProperty("class", "primaryButton")
        self.add_btn.clicked.connect(self._open_create_schedule)
        header_row.addWidget(self.add_btn)
        layout.addLayout(header_row)

        # Filters Card
        filter_card = QWidget()
        filter_card.setObjectName("statCard")
        f_layout = QHBoxLayout(filter_card)
        f_layout.setContentsMargins(14, 10, 14, 10)
        f_layout.setSpacing(12)

        self.status_combo = QComboBox()
        self.status_combo.addItem("All Statuses", "All")
        self.status_combo.addItem("SCHEDULED Only", "SCHEDULED")
        self.status_combo.addItem("COMPLETED Only", "COMPLETED")
        self.status_combo.addItem("CANCELLED Only", "CANCELLED")
        self.status_combo.currentIndexChanged.connect(self.refresh_schedules)
        f_layout.addWidget(self.status_combo, 1)

        self.refresh_btn = QPushButton("🔄 Refresh List")
        self.refresh_btn.clicked.connect(self.refresh_schedules)
        f_layout.addWidget(self.refresh_btn)
        f_layout.addStretch(2)

        layout.addWidget(filter_card)

        # Schedules Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Bus Details", "Route", "Date", "Timings", "Fare", "Booked / Capacity", "Status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self._open_edit_selected)
        layout.addWidget(self.table)

        # Action Buttons
        action_row = QHBoxLayout()
        self.edit_btn = QPushButton("✏ Edit Schedule")
        self.edit_btn.clicked.connect(self._open_edit_selected)
        action_row.addWidget(self.edit_btn)

        self.cancel_sched_btn = QPushButton("Cancel Schedule")
        self.cancel_sched_btn.setProperty("class", "dangerButton")
        self.cancel_sched_btn.clicked.connect(self._cancel_selected_schedule)
        action_row.addWidget(self.cancel_sched_btn)

        action_row.addStretch()
        layout.addLayout(action_row)

    def refresh_schedules(self):
        status = self.status_combo.currentData()
        self.schedules = schedule_repository.list_all_schedules(
            status=status if status != "All" else None
        )

        self.table.setRowCount(len(self.schedules))
        for row_idx, s in enumerate(self.schedules):
            bus_str = f"{s['bus_name']} ({s['bus_number']})"
            route_str = f"{s['source']} → {s['destination']}"
            timings = f"{s['departure_time']} - {s['arrival_time']}"
            booked_str = f"{s['booked_seats']} / {s['total_seats']} seats"

            self.table.setItem(row_idx, 0, QTableWidgetItem(str(s["schedule_id"])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(bus_str))
            self.table.setItem(row_idx, 2, QTableWidgetItem(route_str))
            self.table.setItem(row_idx, 3, QTableWidgetItem(s["travel_date"]))
            self.table.setItem(row_idx, 4, QTableWidgetItem(timings))
            self.table.setItem(row_idx, 5, QTableWidgetItem(f"Rs. {s['fare']:.2f}"))
            self.table.setItem(row_idx, 6, QTableWidgetItem(booked_str))

            status_item = QTableWidgetItem(s["status"])
            if s["status"] == "SCHEDULED":
                status_item.setForeground(Qt.blue)
            elif s["status"] == "COMPLETED":
                status_item.setForeground(Qt.darkGreen)
            else:
                status_item.setForeground(Qt.red)
            self.table.setItem(row_idx, 7, status_item)

    def _open_create_schedule(self):
        dialog = ScheduleDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_schedules()

    def _open_edit_selected(self):
        cur_row = self.table.currentRow()
        if cur_row < 0 or cur_row >= len(self.schedules):
            QMessageBox.information(self, "Selection Required", "Please select a schedule to edit.")
            return

        selected = self.schedules[cur_row]
        dialog = ScheduleDialog(schedule=selected, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_schedules()

    def _cancel_selected_schedule(self):
        cur_row = self.table.currentRow()
        if cur_row < 0 or cur_row >= len(self.schedules):
            QMessageBox.information(self, "Selection Required", "Please select a schedule to cancel.")
            return

        selected = self.schedules[cur_row]
        if selected["status"] == "CANCELLED":
            QMessageBox.information(self, "Already Cancelled", "This schedule has already been cancelled.")
            return

        confirm = QMessageBox.question(
            self,
            "Confirm Schedule Cancellation",
            f"Are you sure you want to cancel schedule #{selected['schedule_id']} "
            f"({selected['source']} → {selected['destination']} on {selected['travel_date']})?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            schedule_repository.set_schedule_status(selected["schedule_id"], "CANCELLED")
            self.refresh_schedules()
