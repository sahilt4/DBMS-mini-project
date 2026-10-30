"""
Bus Fleet Management Page for Administrators.
Provides fleet search, filtering, add/edit modals, and soft-deactivation toggle.
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

from app.config import BUS_TYPES
from app.repositories import bus_repository
from app.ui.dialogs.bus_dialog import BusDialog


class BusManagementPage(QWidget):
    """Bus fleet administration page."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.buses = []
        self._init_ui()
        self.refresh_buses()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header Title and Add Button
        header_row = QHBoxLayout()
        v_title = QVBoxLayout()
        title = QLabel("Bus Fleet Management")
        title.setObjectName("pageTitle")
        sub = QLabel("Configure buses, seat layouts, capacities, and active inventory status")
        sub.setObjectName("pageDescription")
        v_title.addWidget(title)
        v_title.addWidget(sub)
        header_row.addLayout(v_title)
        header_row.addStretch()

        self.add_btn = QPushButton("➕ Add New Bus")
        self.add_btn.setProperty("class", "primaryButton")
        self.add_btn.clicked.connect(self._open_add_bus)
        header_row.addWidget(self.add_btn)
        layout.addLayout(header_row)

        # Filter bar
        filter_card = QWidget()
        filter_card.setObjectName("statCard")
        f_layout = QHBoxLayout(filter_card)
        f_layout.setContentsMargins(14, 10, 14, 10)
        f_layout.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by bus number or operator name...")
        self.search_input.textChanged.connect(self.refresh_buses)
        f_layout.addWidget(self.search_input, 2)

        self.type_combo = QComboBox()
        self.type_combo.addItem("All Types", "All")
        for bt in BUS_TYPES:
            self.type_combo.addItem(bt, bt)
        self.type_combo.currentIndexChanged.connect(self.refresh_buses)
        f_layout.addWidget(self.type_combo, 1)

        self.status_combo = QComboBox()
        self.status_combo.addItem("All Statuses", None)
        self.status_combo.addItem("Active Only", 1)
        self.status_combo.addItem("Inactive (Deactivated)", 0)
        self.status_combo.currentIndexChanged.connect(self.refresh_buses)
        f_layout.addWidget(self.status_combo, 1)

        layout.addWidget(filter_card)

        # Bus Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Bus ID", "Bus Number", "Operator Name", "Type", "Seats Capacity", "Status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self._open_edit_selected)
        layout.addWidget(self.table)

        # Action bar at bottom
        action_row = QHBoxLayout()
        self.edit_btn = QPushButton("✏ Edit Selected")
        self.edit_btn.clicked.connect(self._open_edit_selected)
        action_row.addWidget(self.edit_btn)

        self.toggle_status_btn = QPushButton("Toggle Active / Deactivate")
        self.toggle_status_btn.clicked.connect(self._toggle_status)
        action_row.addWidget(self.toggle_status_btn)

        action_row.addStretch()
        layout.addLayout(action_row)

    def refresh_buses(self):
        search = self.search_input.text().strip()
        btype = self.type_combo.currentData()
        status = self.status_combo.currentData()

        self.buses = bus_repository.list_buses(
            search=search if search else None,
            bus_type=btype if btype != "All" else None,
            is_active=status
        )

        self.table.setRowCount(len(self.buses))
        for row_idx, b in enumerate(self.buses):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(b["bus_id"])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(b["bus_number"]))
            self.table.setItem(row_idx, 2, QTableWidgetItem(b["bus_name"]))
            self.table.setItem(row_idx, 3, QTableWidgetItem(b["bus_type"]))
            self.table.setItem(row_idx, 4, QTableWidgetItem(f"{b['total_seats']} seats"))

            status_str = "ACTIVE" if b["is_active"] else "INACTIVE"
            status_item = QTableWidgetItem(status_str)
            if b["is_active"]:
                status_item.setForeground(Qt.darkGreen)
            else:
                status_item.setForeground(Qt.red)
            self.table.setItem(row_idx, 5, status_item)

    def _open_add_bus(self):
        dialog = BusDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_buses()

    def _open_edit_selected(self):
        cur_row = self.table.currentRow()
        if cur_row < 0 or cur_row >= len(self.buses):
            QMessageBox.information(self, "Selection Required", "Please select a bus from the table to edit.")
            return

        selected_bus = self.buses[cur_row]
        dialog = BusDialog(bus=selected_bus, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_buses()

    def _toggle_status(self):
        cur_row = self.table.currentRow()
        if cur_row < 0 or cur_row >= len(self.buses):
            QMessageBox.information(self, "Selection Required", "Please select a bus to change active status.")
            return

        selected_bus = self.buses[cur_row]
        new_status = 0 if selected_bus["is_active"] else 1
        status_word = "deactivate" if new_status == 0 else "activate"

        confirm = QMessageBox.question(
            self,
            "Confirm Status Change",
            f"Are you sure you want to {status_word} bus '{selected_bus['bus_number']}'?\n"
            f"(Historical bookings will remain preserved without deletion)",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            bus_repository.set_bus_status(selected_bus["bus_id"], new_status)
            self.refresh_buses()
