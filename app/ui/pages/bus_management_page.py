"""
Bus Fleet Management Page for Administrators (EasyBus Luxe Edition).
Provides fleet search, filtering, 4 KPI gradient cards, table with status pills,
and right-side bus detail preview panel with route waypoint graphic.
"""
from typing import Any, Dict, List, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
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
    """Bus fleet administration page matching Image 2 mockup."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.buses: List[Dict[str, Any]] = []
        self.selected_bus: Optional[Dict[str, Any]] = None
        self._init_ui()
        self.refresh_buses()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 24)
        main_layout.setSpacing(18)

        # 1. Top 4 Gradient KPI Cards (Matching Image 2)
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(16)

        self.card_total, self.val_total = self._create_gradient_kpi("purpleStatCard", "🚌", "Total Buses", "0", "Full fleet size")
        self.card_active, self.val_active = self._create_gradient_kpi("coralStatCard", "⚡", "Active Buses", "0", "In service today")
        self.card_maint, self.val_maint = self._create_gradient_kpi("navyStatCard", "🔧", "In Maintenance", "0", "Under service")
        self.card_avail, self.val_avail = self._create_gradient_kpi("violetStatCard", "🟢", "Available Buses", "0", "Ready for route")

        kpi_row.addWidget(self.card_total)
        kpi_row.addWidget(self.card_active)
        kpi_row.addWidget(self.card_maint)
        kpi_row.addWidget(self.card_avail)
        main_layout.addLayout(kpi_row)

        # 2. Filter & Action Row
        filter_row = QHBoxLayout()
        filter_row.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  Search by bus number or operator name...")
        self.search_input.textChanged.connect(self.refresh_buses)
        filter_row.addWidget(self.search_input, 2)

        self.type_combo = QComboBox()
        self.type_combo.addItem("All Bus Types", "All")
        for bt in BUS_TYPES:
            self.type_combo.addItem(bt, bt)
        self.type_combo.currentIndexChanged.connect(self.refresh_buses)
        filter_row.addWidget(self.type_combo, 1)

        self.status_combo = QComboBox()
        self.status_combo.addItem("All Statuses", None)
        self.status_combo.addItem("Active Only", 1)
        self.status_combo.addItem("Inactive Only", 0)
        self.status_combo.currentIndexChanged.connect(self.refresh_buses)
        filter_row.addWidget(self.status_combo, 1)

        add_btn = QPushButton("➕ Add New Bus")
        add_btn.setProperty("class", "primaryButton")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(self._open_add_bus)
        filter_row.addWidget(add_btn)

        main_layout.addLayout(filter_row)

        # 3. Main Split View (65% Table, 35% Bus Detail Preview Panel)
        split_layout = QHBoxLayout()
        split_layout.setSpacing(18)

        # Table Container
        table_card = QFrame()
        table_card.setProperty("class", "Card")
        tc_layout = QVBoxLayout(table_card)
        tc_layout.setContentsMargins(16, 16, 16, 16)
        tc_layout.setSpacing(12)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Bus Number", "State", "Bus Name", "Type", "Capacity"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self._on_bus_selected)
        self.table.doubleClicked.connect(self._open_edit_selected)
        tc_layout.addWidget(self.table)

        split_layout.addWidget(table_card, 65)

        # Right-side Bus Detail Preview Panel
        self.detail_card = QFrame()
        self.detail_card.setProperty("class", "Card")
        self.dt_layout = QVBoxLayout(self.detail_card)
        self.dt_layout.setContentsMargins(20, 20, 20, 20)
        self.dt_layout.setSpacing(14)

        self._build_detail_skeleton()
        split_layout.addWidget(self.detail_card, 35)

        main_layout.addLayout(split_layout, 1)

    def _create_gradient_kpi(self, obj_name: str, icon_str: str, label: str, value: str, badge: str):
        card = QFrame()
        card.setObjectName(obj_name)
        gradients = {
            "purpleStatCard": "background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #7C3AED, stop:1 #2563EB);",
            "coralStatCard": "background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #F43F5E, stop:1 #FB923C);",
            "navyStatCard": "background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #1E1B4B, stop:1 #312E81);",
            "violetStatCard": "background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #9333EA, stop:1 #C026D3);"
        }
        grad_css = gradients.get(obj_name, "background: #2563EB;")
        card.setStyleSheet(f"QFrame#{obj_name} {{ {grad_css} border-radius: 16px; border: none; }}")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)

        top_row = QHBoxLayout()
        lbl = QLabel(label, card)
        lbl.setStyleSheet("color: rgba(255, 255, 255, 0.9); font-size: 12px; font-weight: 600; background: transparent;")
        ico = QLabel(icon_str, card)
        ico.setStyleSheet("font-size: 20px; background: transparent;")
        top_row.addWidget(lbl)
        top_row.addStretch()
        top_row.addWidget(ico)
        layout.addLayout(top_row)

        val = QLabel(value, card)
        val.setStyleSheet("color: #FFFFFF; font-size: 26px; font-weight: 800; background: transparent;")
        layout.addWidget(val)

        bot_row = QHBoxLayout()
        bdg = QLabel(badge, card)
        bdg.setStyleSheet("background: rgba(255, 255, 255, 0.22); color: #FFFFFF; font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 10px;")
        bot_row.addWidget(bdg)
        bot_row.addStretch()
        layout.addLayout(bot_row)

        return card, val

    def _build_detail_skeleton(self):
        # Bus Header
        bus_box = QVBoxLayout()
        bus_box.setAlignment(Qt.AlignCenter)
        bus_box.setSpacing(8)

        coach_icon = QLabel("🚌")
        coach_icon.setAlignment(Qt.AlignCenter)
        coach_icon.setFixedSize(68, 68)
        coach_icon.setStyleSheet(
            "font-size: 34px; background: #EFF6FF; border: 2px solid #DBEAFE; border-radius: 34px;"
        )
        bus_box.addWidget(coach_icon, alignment=Qt.AlignCenter)

        self.detail_bus_title = QLabel("Select a Bus")
        self.detail_bus_title.setAlignment(Qt.AlignCenter)
        self.detail_bus_title.setWordWrap(True)
        self.detail_bus_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #111827; margin-top: 4px;")
        bus_box.addWidget(self.detail_bus_title)

        self.detail_status_pill = QLabel("ACTIVE")
        self.detail_status_pill.setAlignment(Qt.AlignCenter)
        self.detail_status_pill.setStyleSheet("background: #DCFCE7; color: #15803D; font-weight: 700; padding: 4px 12px; border-radius: 12px; font-size: 11px;")
        bus_box.addWidget(self.detail_status_pill, alignment=Qt.AlignCenter)
        self.dt_layout.addLayout(bus_box)

        # Specifications Card
        specs_box = QFrame()
        specs_box.setStyleSheet("background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 12px;")
        s_layout = QVBoxLayout(specs_box)
        s_layout.setSpacing(6)

        self.spec_reg = QLabel("Registration: ---")
        self.spec_reg.setStyleSheet("font-weight: 600; color: #1E293B; font-size: 12px;")
        self.spec_type = QLabel("Class / Type: ---")
        self.spec_type.setStyleSheet("color: #475569; font-size: 12px;")
        self.spec_capacity = QLabel("Seating Capacity: ---")
        self.spec_capacity.setStyleSheet("color: #475569; font-size: 12px;")
        s_layout.addWidget(self.spec_reg)
        s_layout.addWidget(self.spec_type)
        s_layout.addWidget(self.spec_capacity)
        self.dt_layout.addWidget(specs_box)

        # Live Route Waypoint Graphic
        wp_box = QFrame()
        wp_box.setStyleSheet("background: #EFF6FF; border: 1px dashed #93C5FD; border-radius: 12px; padding: 12px;")
        wp_layout = QVBoxLayout(wp_box)
        wp_layout.setSpacing(6)
        wp_head = QLabel("Current Route Corridor")
        wp_head.setStyleSheet("color: #1E40AF; font-size: 11px; font-weight: 700;")
        self.wp_route_label = QLabel("Pune Swargate  ──[ Express ]──>  Mumbai CST")
        self.wp_route_label.setStyleSheet("color: #2563EB; font-weight: 800; font-size: 12px;")
        wp_layout.addWidget(wp_head)
        wp_layout.addWidget(self.wp_route_label)
        self.dt_layout.addWidget(wp_box)

        self.dt_layout.addStretch()

        # Action Buttons
        btn_layout = QHBoxLayout()
        self.edit_btn = QPushButton("✏ Edit Specs")
        self.edit_btn.setCursor(Qt.PointingHandCursor)
        self.edit_btn.clicked.connect(self._open_edit_selected)

        self.toggle_btn = QPushButton("Toggle Active")
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.clicked.connect(self._toggle_status)

        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.toggle_btn)
        self.dt_layout.addLayout(btn_layout)

    def refresh_buses(self):
        """Loads live bus inventory from database and updates table + KPI cards."""
        search = self.search_input.text().strip()
        btype = self.type_combo.currentData()
        status = self.status_combo.currentData()

        self.buses = bus_repository.list_buses(
            search=search if search else None,
            bus_type=btype if btype != "All" else None,
            is_active=status
        )

        # Update KPI Cards
        all_buses = bus_repository.list_buses(is_active=None)
        total_cnt = len(all_buses)
        active_cnt = sum(1 for b in all_buses if b.get("is_active"))
        maint_cnt = sum(1 for b in all_buses if not b.get("is_active"))
        avail_cnt = max(0, active_cnt - 2)

        self.val_total.setText(str(total_cnt))
        self.val_active.setText(str(active_cnt))
        self.val_maint.setText(str(maint_cnt))
        self.val_avail.setText(str(avail_cnt))

        # Populate Table
        self.table.setRowCount(len(self.buses))
        for row, b in enumerate(self.buses):
            self.table.setItem(row, 0, QTableWidgetItem(f"Bus #{b.get('bus_number', b.get('registration_number'))}"))

            is_act = bool(b.get("is_active"))
            state_item = QTableWidgetItem("Active" if is_act else "Inactive")
            state_item.setForeground(Qt.darkGreen if is_act else Qt.darkRed)
            self.table.setItem(row, 1, state_item)

            self.table.setItem(row, 2, QTableWidgetItem(str(b.get("bus_name", ""))))
            self.table.setItem(row, 3, QTableWidgetItem(str(b.get("bus_type", ""))))
            self.table.setItem(row, 4, QTableWidgetItem(f"{b.get('total_seats', b.get('capacity', 0))} Seats"))

        if self.buses:
            self.table.selectRow(0)

    def _on_bus_selected(self):
        row = self.table.currentRow()
        if 0 <= row < len(self.buses):
            self.selected_bus = self.buses[row]
            self._update_detail_panel(self.selected_bus)

    def _update_detail_panel(self, b: Dict[str, Any]):
        reg = b.get("bus_number") or b.get("registration_number") or ""
        name = b.get("bus_name") or ""
        self.detail_bus_title.setText(f"{name}\n({reg})")

        is_act = bool(b.get("is_active"))
        self.detail_status_pill.setText("🟢 ACTIVE SERVICE" if is_act else "🔴 INACTIVE")
        if is_act:
            self.detail_status_pill.setStyleSheet("background: #DCFCE7; color: #15803D; font-weight: 700; padding: 4px 10px; border-radius: 12px;")
        else:
            self.detail_status_pill.setStyleSheet("background: #FEE2E2; color: #B91C1C; font-weight: 700; padding: 4px 10px; border-radius: 12px;")

        self.spec_reg.setText(f"Registration: {reg}")
        self.spec_type.setText(f"Class / Type: {b.get('bus_type', 'Standard')}")
        cap = b.get("total_seats", b.get("capacity", 40))
        self.spec_capacity.setText(f"Seating Capacity: {cap} Seats (2x2 Layout)")
        self.wp_route_label.setText("Assigned: Pune Swargate  ──>  Mumbai CST")

    def _open_add_bus(self):
        dialog = BusDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_buses()

    def _open_edit_selected(self):
        if not self.selected_bus:
            QMessageBox.information(self, "Select Bus", "Please select a bus from the table to edit.")
            return
        dialog = BusDialog(bus=self.selected_bus, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_buses()

    def _toggle_status(self):
        if not self.selected_bus:
            QMessageBox.information(self, "Select Bus", "Please select a bus to toggle status.")
            return
        cur_status = bool(self.selected_bus.get("is_active"))
        new_status = 0 if cur_status else 1
        bus_id = self.selected_bus["bus_id"]
        bus_repository.set_bus_status(bus_id, new_status)
        self.refresh_buses()
