"""
Route Dialog for Adding or Editing bus routes.
"""
from typing import Any, Dict, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from app.repositories import route_repository


class RouteDialog(QDialog):
    """Modal for creating or editing a route."""

    def __init__(self, route: Optional[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        self.route = route
        self.is_edit = route is not None

        title = "Edit Route" if self.is_edit else "Add New Route"
        self.setWindowTitle(title)
        self.setMinimumWidth(440)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        header = QLabel("Edit Route" if self.is_edit else "Add New Route")
        header.setStyleSheet("font-size: 16px; font-weight: 700; color: #0F172A;")
        layout.addWidget(header)

        # Source
        layout.addWidget(QLabel("Source City *"))
        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText("e.g. Nashik")
        if self.is_edit:
            self.source_input.setText(self.route["source"])
        layout.addWidget(self.source_input)

        # Destination
        layout.addWidget(QLabel("Destination City *"))
        self.dest_input = QLineEdit()
        self.dest_input.setPlaceholderText("e.g. Pune")
        if self.is_edit:
            self.dest_input.setText(self.route["destination"])
        layout.addWidget(self.dest_input)

        # Distance
        layout.addWidget(QLabel("Distance (Kilometers) *"))
        self.dist_input = QDoubleSpinBox()
        self.dist_input.setRange(1.0, 5000.0)
        self.dist_input.setDecimals(1)
        self.dist_input.setValue(self.route["distance_km"] if self.is_edit else 210.0)
        layout.addWidget(self.dist_input)

        layout.addSpacing(10)

        # Buttons
        btn_row = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("Save Route")
        self.save_btn.setProperty("class", "primaryButton")
        self.save_btn.clicked.connect(self._handle_save)
        btn_row.addWidget(self.save_btn)

        layout.addLayout(btn_row)

    def _handle_save(self):
        src = self.source_input.text().strip()
        dst = self.dest_input.text().strip()
        dist = self.dist_input.value()

        if not src or not dst:
            QMessageBox.warning(self, "Validation", "Source and Destination are required.")
            return
        if src.lower() == dst.lower():
            QMessageBox.warning(self, "Validation", "Source and Destination cities cannot be identical.")
            return

        try:
            if self.is_edit:
                route_repository.update_route(
                    route_id=self.route["route_id"],
                    source=src,
                    destination=dst,
                    distance_km=dist
                )
            else:
                existing = route_repository.find_route_by_cities(src, dst)
                if existing:
                    QMessageBox.warning(self, "Duplicate", f"Route from '{src}' to '{dst}' already exists.")
                    return
                route_repository.create_route(
                    source=src,
                    destination=dst,
                    distance_km=dist
                )
            self.accept()
        except Exception as err:
            QMessageBox.critical(self, "Error", f"Could not save route: {err}")
