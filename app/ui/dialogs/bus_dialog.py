"""
Bus Dialog for Adding or Editing bus fleet records.
"""
from typing import Any, Dict, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from app.config import BUS_TYPES
from app.repositories import bus_repository


class BusDialog(QDialog):
    """Modal for creating or editing a bus."""

    def __init__(self, bus: Optional[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        self.bus = bus
        self.is_edit = bus is not None

        title = "Edit Bus" if self.is_edit else "Add New Bus"
        self.setWindowTitle(title)
        self.setMinimumWidth(440)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        header = QLabel("Edit Bus Fleet" if self.is_edit else "Add New Bus Fleet")
        header.setStyleSheet("font-size: 16px; font-weight: 700; color: #0F172A;")
        layout.addWidget(header)

        # Bus Number
        layout.addWidget(QLabel("Bus Number (Plate) *"))
        self.num_input = QLineEdit()
        self.num_input.setPlaceholderText("e.g. MH-15-AB-1234")
        if self.is_edit:
            self.num_input.setText(self.bus["bus_number"])
        layout.addWidget(self.num_input)

        # Bus Name
        layout.addWidget(QLabel("Bus Operator / Name *"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Royal Travels")
        if self.is_edit:
            self.name_input.setText(self.bus["bus_name"])
        layout.addWidget(self.name_input)

        # Bus Type
        layout.addWidget(QLabel("Bus Type *"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(BUS_TYPES)
        if self.is_edit and self.bus["bus_type"] in BUS_TYPES:
            self.type_combo.setCurrentText(self.bus["bus_type"])
        layout.addWidget(self.type_combo)

        # Total Seats
        layout.addWidget(QLabel("Total Seats (Capacity) *"))
        self.seats_input = QSpinBox()
        self.seats_input.setRange(10, 60)
        self.seats_input.setValue(self.bus["total_seats"] if self.is_edit else 40)
        layout.addWidget(self.seats_input)

        layout.addSpacing(10)

        # Buttons
        btn_row = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("Save Bus")
        self.save_btn.setProperty("class", "primaryButton")
        self.save_btn.clicked.connect(self._handle_save)
        btn_row.addWidget(self.save_btn)

        layout.addLayout(btn_row)

    def _handle_save(self):
        num = self.num_input.text().strip().upper()
        name = self.name_input.text().strip()
        btype = self.type_combo.currentText()
        seats = self.seats_input.value()

        if not num:
            QMessageBox.warning(self, "Validation", "Bus number is required.")
            return
        if not name:
            QMessageBox.warning(self, "Validation", "Bus name is required.")
            return

        try:
            if self.is_edit:
                bus_repository.update_bus(
                    bus_id=self.bus["bus_id"],
                    bus_number=num,
                    bus_name=name,
                    bus_type=btype,
                    total_seats=seats
                )
            else:
                existing = bus_repository.find_bus_by_number(num)
                if existing:
                    QMessageBox.warning(self, "Duplicate", f"Bus with number '{num}' already exists.")
                    return
                bus_repository.create_bus(
                    bus_number=num,
                    bus_name=name,
                    bus_type=btype,
                    total_seats=seats
                )
            self.accept()
        except Exception as err:
            QMessageBox.critical(self, "Error", f"Could not save bus: {err}")
