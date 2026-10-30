"""
Route Management Page for Administrators.
Supports route creation, editing, searching, and activation status management.
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

from app.repositories import route_repository
from app.ui.dialogs.route_dialog import RouteDialog


class RouteManagementPage(QWidget):
    """Route administration page."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.routes = []
        self._init_ui()
        self.refresh_routes()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header Title and Add Button
        header_row = QHBoxLayout()
        v_title = QVBoxLayout()
        title = QLabel("Bus Route Management")
        title.setObjectName("pageTitle")
        sub = QLabel("Manage origin-destination pairs, distances in kilometers, and active route lines")
        sub.setObjectName("pageDescription")
        v_title.addWidget(title)
        v_title.addWidget(sub)
        header_row.addLayout(v_title)
        header_row.addStretch()

        self.add_btn = QPushButton("➕ Add New Route")
        self.add_btn.setProperty("class", "primaryButton")
        self.add_btn.clicked.connect(self._open_add_route)
        header_row.addWidget(self.add_btn)
        layout.addLayout(header_row)

        # Search Bar
        filter_card = QWidget()
        filter_card.setObjectName("statCard")
        f_layout = QHBoxLayout(filter_card)
        f_layout.setContentsMargins(14, 10, 14, 10)
        f_layout.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by source or destination city name...")
        self.search_input.textChanged.connect(self.refresh_routes)
        f_layout.addWidget(self.search_input, 3)

        self.status_combo = QComboBox()
        self.status_combo.addItem("All Statuses", None)
        self.status_combo.addItem("Active Only", 1)
        self.status_combo.addItem("Inactive (Deactivated)", 0)
        self.status_combo.currentIndexChanged.connect(self.refresh_routes)
        f_layout.addWidget(self.status_combo, 1)

        layout.addWidget(filter_card)

        # Routes Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Route ID", "Source City", "Destination City", "Distance (km)", "Status"
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
        self.edit_btn = QPushButton("✏ Edit Selected")
        self.edit_btn.clicked.connect(self._open_edit_selected)
        action_row.addWidget(self.edit_btn)

        self.toggle_status_btn = QPushButton("Toggle Active / Deactivate")
        self.toggle_status_btn.clicked.connect(self._toggle_status)
        action_row.addWidget(self.toggle_status_btn)

        action_row.addStretch()
        layout.addLayout(action_row)

    def refresh_routes(self):
        search = self.search_input.text().strip()
        status = self.status_combo.currentData()

        self.routes = route_repository.list_routes(
            search=search if search else None,
            is_active=status
        )

        self.table.setRowCount(len(self.routes))
        for row_idx, r in enumerate(self.routes):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(r["route_id"])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(r["source"]))
            self.table.setItem(row_idx, 2, QTableWidgetItem(r["destination"]))
            self.table.setItem(row_idx, 3, QTableWidgetItem(f"{r['distance_km']} km"))

            status_str = "ACTIVE" if r["is_active"] else "INACTIVE"
            status_item = QTableWidgetItem(status_str)
            if r["is_active"]:
                status_item.setForeground(Qt.darkGreen)
            else:
                status_item.setForeground(Qt.red)
            self.table.setItem(row_idx, 4, status_item)

    def _open_add_route(self):
        dialog = RouteDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_routes()

    def _open_edit_selected(self):
        cur_row = self.table.currentRow()
        if cur_row < 0 or cur_row >= len(self.routes):
            QMessageBox.information(self, "Selection Required", "Please select a route from the table to edit.")
            return

        selected_route = self.routes[cur_row]
        dialog = RouteDialog(route=selected_route, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_routes()

    def _toggle_status(self):
        cur_row = self.table.currentRow()
        if cur_row < 0 or cur_row >= len(self.routes):
            QMessageBox.information(self, "Selection Required", "Please select a route to change active status.")
            return

        selected_route = self.routes[cur_row]
        new_status = 0 if selected_route["is_active"] else 1
        status_word = "deactivate" if new_status == 0 else "activate"

        confirm = QMessageBox.question(
            self,
            "Confirm Status Change",
            f"Are you sure you want to {status_word} route '{selected_route['source']} → {selected_route['destination']}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            route_repository.set_route_status(selected_route["route_id"], new_status)
            self.refresh_routes()
