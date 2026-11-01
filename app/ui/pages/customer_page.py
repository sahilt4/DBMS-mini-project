"""
Customer Management Page for SmartBus BRMS (EasyBus Luxe Edition).
Displays passenger profiles, tier classification (Pro / Free),
and customer profile drawer with real-time booking history.
"""
from typing import Any, Dict, List, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.repositories import passenger_repository


class CustomerPage(QWidget):
    """Customer Management page with passenger directory and detail drawer."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.customers: List[Dict[str, Any]] = []
        self.selected_customer: Optional[Dict[str, Any]] = None
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 24)
        main_layout.setSpacing(20)

        # 1. Top Stat Cards (4 Gradient Cards matching Image 4)
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)

        self.card_total, self.val_total = self._create_gradient_card("purpleStatCard", "Total Customer", "0", "+10% this year")
        self.card_active, self.val_active = self._create_gradient_card("coralStatCard", "Active Customer", "0", "+7% this month")
        self.card_pro, self.val_pro = self._create_gradient_card("navyStatCard", "Pro Members", "0", "VIP tier")
        self.card_new, self.val_new = self._create_gradient_card("violetStatCard", "New Customer", "0", "+2% this month")

        stats_layout.addWidget(self.card_total)
        stats_layout.addWidget(self.card_active)
        stats_layout.addWidget(self.card_pro)
        stats_layout.addWidget(self.card_new)
        main_layout.addLayout(stats_layout)

        # 2. Main Content Split View (65% Table, 35% Profile Drawer)
        content_split = QHBoxLayout()
        content_split.setSpacing(20)

        # Left Container: Customer List
        left_container = QFrame()
        left_container.setProperty("class", "Card")
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(18, 18, 18, 18)
        left_layout.setSpacing(14)

        table_header = QHBoxLayout()
        title_label = QLabel("Customer List")
        title_label.setStyleSheet("font-size: 17px; font-weight: 800; color: #111827;")
        table_header.addWidget(title_label)
        table_header.addStretch()

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh_data)
        table_header.addWidget(refresh_btn)
        left_layout.addLayout(table_header)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Customer", "Email", "Phone", "Bookings", "Account"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self._on_row_selected)
        left_layout.addWidget(self.table)

        content_split.addWidget(left_container, 65)

        # Right Container: Customer Profile Drawer
        self.right_drawer = QFrame()
        self.right_drawer.setProperty("class", "Card")
        self.drawer_layout = QVBoxLayout(self.right_drawer)
        self.drawer_layout.setContentsMargins(20, 20, 20, 20)
        self.drawer_layout.setSpacing(14)

        # Drawer Content (populated on customer select)
        self._build_drawer_skeleton()
        content_split.addWidget(self.right_drawer, 35)

        main_layout.addLayout(content_split, 1)

    def _create_gradient_card(self, obj_name: str, label_text: str, value_text: str, badge_text: str):
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

        lbl = QLabel(label_text, card)
        lbl.setStyleSheet("color: rgba(255, 255, 255, 0.9); font-size: 12px; font-weight: 600; background: transparent;")
        layout.addWidget(lbl)

        val = QLabel(value_text, card)
        val.setStyleSheet("color: #FFFFFF; font-size: 26px; font-weight: 800; background: transparent;")
        layout.addWidget(val)

        badge_row = QHBoxLayout()
        badge = QLabel(badge_text, card)
        badge.setStyleSheet("background: rgba(255, 255, 255, 0.22); color: #FFFFFF; font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 10px;")
        badge_row.addWidget(badge)
        badge_row.addStretch()
        layout.addLayout(badge_row)

        return card, val

    def _build_drawer_skeleton(self):
        # 1. Avatar + Name Header (Compact, modern design)
        avatar_box = QVBoxLayout()
        avatar_box.setAlignment(Qt.AlignCenter)
        avatar_box.setSpacing(4)

        self.drawer_avatar = QLabel("👤")
        self.drawer_avatar.setAlignment(Qt.AlignCenter)
        self.drawer_avatar.setFixedSize(56, 56)
        self.drawer_avatar.setStyleSheet(
            "font-size: 28px; background: #F3F4F6; border: 2px solid #E5E7EB; border-radius: 28px;"
        )
        avatar_box.addWidget(self.drawer_avatar, alignment=Qt.AlignCenter)

        self.drawer_name = QLabel("Select a Customer")
        self.drawer_name.setAlignment(Qt.AlignCenter)
        self.drawer_name.setStyleSheet("font-size: 16px; font-weight: 800; color: #111827;")
        avatar_box.addWidget(self.drawer_name)

        self.drawer_id = QLabel("CUST# ---")
        self.drawer_id.setAlignment(Qt.AlignCenter)
        self.drawer_id.setStyleSheet("font-size: 11px; font-weight: 600; color: #94A3B8;")
        avatar_box.addWidget(self.drawer_id)

        self.drawer_layout.addLayout(avatar_box)

        # 2. Contact Info (Single compact row)
        self.drawer_contact = QLabel("✉️ ---  |  📞 ---")
        self.drawer_contact.setAlignment(Qt.AlignCenter)
        self.drawer_contact.setStyleSheet("color: #4B5563; font-size: 12px; font-weight: 500; padding: 4px 0px;")
        self.drawer_layout.addWidget(self.drawer_contact)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("color: #E5E7EB; max-height: 1px;")
        self.drawer_layout.addWidget(divider)

        # 4. Booking History Header
        self.history_title = QLabel("Booking History")
        self.history_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #111827;")
        self.drawer_layout.addWidget(self.history_title)

        # 5. History Scrollable List (Generous minimum height so cards are fully visible)
        self.history_scroll = QScrollArea()
        self.history_scroll.setWidgetResizable(True)
        self.history_scroll.setMinimumHeight(260)
        self.history_scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; } "
            "QScrollBar:vertical { width: 6px; background: #F1F5F9; border-radius: 3px; } "
            "QScrollBar::handle:vertical { background: #CBD5E1; border-radius: 3px; min-height: 20px; }"
        )

        self.history_container = QWidget()
        self.history_container.setStyleSheet("background: transparent;")
        self.history_layout = QVBoxLayout(self.history_container)
        self.history_layout.setContentsMargins(0, 0, 4, 0)
        self.history_layout.setSpacing(8)
        self.history_scroll.setWidget(self.history_container)

        self.drawer_layout.addWidget(self.history_scroll, 1)

    def refresh_data(self):
        """Loads live customer records from database."""
        self.customers = passenger_repository.list_customers_with_metrics()

        # Update Stat Cards
        total_count = len(self.customers)
        active_count = sum(1 for c in self.customers if c.get("total_bookings", 0) > 0)
        pro_count = sum(1 for c in self.customers if c.get("total_bookings", 0) >= 2 or float(c.get("total_spent", 0)) > 800)
        new_count = max(1, total_count // 3)

        self.val_total.setText(str(total_count))
        self.val_active.setText(str(active_count))
        self.val_pro.setText(str(pro_count))
        self.val_new.setText(str(new_count))

        # Populate Table
        self.table.setRowCount(len(self.customers))
        for row, c in enumerate(self.customers):
            name_str = f"👤  {c['full_name']}  (ID: #{c['passenger_id']})"
            self.table.setItem(row, 0, QTableWidgetItem(name_str))
            self.table.setItem(row, 1, QTableWidgetItem(str(c.get("email", ""))))
            self.table.setItem(row, 2, QTableWidgetItem(str(c.get("phone", "N/A"))))
            
            b_cnt = c.get("total_bookings", 0)
            self.table.setItem(row, 3, QTableWidgetItem(f"{b_cnt} Bookings"))

            # Account Tier badge
            is_pro = b_cnt >= 2 or float(c.get("total_spent", 0)) > 800
            tier_item = QTableWidgetItem("⭐ Pro" if is_pro else "Free")
            if is_pro:
                tier_item.setForeground(Qt.darkYellow)
            else:
                tier_item.setForeground(Qt.gray)
            self.table.setItem(row, 4, tier_item)

        if self.customers:
            self.table.selectRow(0)

    def _on_row_selected(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            return
        row = self.table.currentRow()
        if 0 <= row < len(self.customers):
            self.selected_customer = self.customers[row]
            self._update_drawer_details(self.selected_customer)

    def _update_drawer_details(self, c: Dict[str, Any]):
        p_id = c["passenger_id"]
        self.drawer_name.setText(c["full_name"])
        self.drawer_id.setText(f"CUST#{p_id:05d}")
        self.drawer_contact.setText(f"✉️  {c.get('email', 'N/A')}   |   📞  {c.get('phone', 'N/A')}")

        # Fetch customer's recent booking history
        history = passenger_repository.get_customer_booking_history(p_id)
        self.history_title.setText(f"Booking History ({len(history)})")

        # Clear existing history cards and stretches
        while self.history_layout.count():
            item = self.history_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not history:
            no_hist = QLabel("No booking history found.")
            no_hist.setStyleSheet("color: #94A3B8; font-style: italic; padding: 12px;")
            self.history_layout.addWidget(no_hist)
            self.history_layout.addStretch()
            return

        for bk in history:
            card = QFrame()
            card.setStyleSheet(
                "background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 10px 14px;"
            )
            c_layout = QVBoxLayout(card)
            c_layout.setContentsMargins(10, 8, 10, 8)
            c_layout.setSpacing(6)

            top_row = QHBoxLayout()
            route_lbl = QLabel(f"{bk['source']} ➔ {bk['destination']}")
            route_lbl.setStyleSheet("font-weight: 700; color: #1E293B; font-size: 13px;")
            top_row.addWidget(route_lbl)
            top_row.addStretch()

            stat = str(bk["status"]).upper()
            stat_lbl = QLabel(stat)
            if stat == "CONFIRMED":
                stat_lbl.setStyleSheet("background: #DCFCE7; color: #15803D; padding: 3px 10px; border-radius: 10px; font-weight: 700; font-size: 10px;")
            elif stat == "CANCELLED":
                stat_lbl.setStyleSheet("background: #FEE2E2; color: #B91C1C; padding: 3px 10px; border-radius: 10px; font-weight: 700; font-size: 10px;")
            else:
                stat_lbl.setStyleSheet("background: #FEF3C7; color: #B45309; padding: 3px 10px; border-radius: 10px; font-weight: 700; font-size: 10px;")
            top_row.addWidget(stat_lbl)
            c_layout.addLayout(top_row)

            bot_row = QHBoxLayout()
            fare_lbl = QLabel(f"₹ {float(bk['amount']):.2f} • Seat {bk['seat_number']}")
            fare_lbl.setStyleSheet("color: #2563EB; font-weight: 700; font-size: 12px;")
            date_lbl = QLabel(f"{bk['travel_date']}")
            date_lbl.setStyleSheet("color: #64748B; font-size: 11px; font-weight: 500;")
            bot_row.addWidget(fare_lbl)
            bot_row.addStretch()
            bot_row.addWidget(date_lbl)
            c_layout.addLayout(bot_row)

            self.history_layout.addWidget(card)

        self.history_layout.addStretch()
