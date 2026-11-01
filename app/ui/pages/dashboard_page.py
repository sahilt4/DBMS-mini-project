"""
Admin Dashboard Page for SmartBus BRMS (EasyBus Luxe Edition).
Implements the multi-quadrant EasyBus layout:
- Top 3 Vibrant Gradient KPI Stat Cards (Earnings, Today's Bookings, Departures)
- Mid-Left: Live Bus & Route Waypoint Card (with Driver info and route details)
- Mid-Right: Hero Travel Banner ("Secure your seat and enjoy the journey!")
- Bottom-Left: All Booking List Table with pill status badges
- Bottom-Right: Activity / Departures Timeline Widget
"""
import datetime
from typing import Any, Dict, List
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QGridLayout,
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

from app.repositories import report_repository, schedule_repository


class DashboardPage(QWidget):
    """Modern EasyBus-styled executive dashboard."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.stats: Dict[str, Any] = {}
        self._init_ui()
        self.refresh_data()

    def _init_ui(self):
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setObjectName("dashboardScroll")

        self.container = QWidget()
        self.container.setObjectName("dashboardContainer")
        self.scroll.setWidget(self.container)

        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(24, 20, 24, 24)
        self.main_layout.setSpacing(20)

        # ---------------------------------------------------------------------
        # 1. Top Section: 3 Vibrant Gradient KPI Stat Cards (Matching Image 1)
        # ---------------------------------------------------------------------
        top_kpi_layout = QHBoxLayout()
        top_kpi_layout.setSpacing(18)

        # Card 1: Purple Gradient (Total Earnings)
        self.card_earnings, self.val_earnings = self._create_gradient_kpi(
            "purpleStatCard", "💰", "Total Earnings", "Rs. 0.00", "+7% vs last month"
        )
        # Card 2: Coral-Orange Gradient (Today's Bookings)
        self.card_today_bks, self.val_today_bks = self._create_gradient_kpi(
            "coralStatCard", "🎫", "Today's Bookings", "0", "Live reservations"
        )
        # Card 3: Deep Navy Gradient (Successful Departures)
        self.card_departures, self.val_departures = self._create_gradient_kpi(
            "navyStatCard", "🚌", "Successful Departures", "0 / 0", "98% on-time rate"
        )

        top_kpi_layout.addWidget(self.card_earnings)
        top_kpi_layout.addWidget(self.card_today_bks)
        top_kpi_layout.addWidget(self.card_departures)
        self.main_layout.addLayout(top_kpi_layout)

        # ---------------------------------------------------------------------
        # 2. Middle Section: Bus List & Route Waypoint Card + Hero Promo Card
        # ---------------------------------------------------------------------
        mid_layout = QHBoxLayout()
        mid_layout.setSpacing(18)

        # Mid-Left (60% width): Live Active Bus & Waypoint card
        bus_summary_card = QFrame()
        bus_summary_card.setProperty("class", "Card")
        bs_layout = QVBoxLayout(bus_summary_card)
        bs_layout.setContentsMargins(20, 18, 20, 18)
        bs_layout.setSpacing(12)

        # Header row
        bs_head = QHBoxLayout()
        bs_title = QLabel("Bus List")
        bs_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #111827;")
        self.bs_subtitle = QLabel("Today Active Buses: 0")
        self.bs_subtitle.setStyleSheet("font-size: 11px; color: #64748B; font-weight: 600;")
        head_v = QVBoxLayout()
        head_v.addWidget(bs_title)
        head_v.addWidget(self.bs_subtitle)
        bs_head.addLayout(head_v)
        bs_head.addStretch()

        active_pill = QLabel("🟢  Active Fleet")
        active_pill.setProperty("class", "statusCompleted")
        bs_head.addWidget(active_pill)

        self.driver_pill = QLabel("👤 Ramesh Shinde (Driver) | 💺 Seats: Available")
        self.driver_pill.setStyleSheet("background: #F3F4F6; color: #374151; font-weight: 600; padding: 4px 10px; border-radius: 12px; font-size: 11px;")
        bs_head.addWidget(self.driver_pill)
        bs_layout.addLayout(bs_head)

        # Route Cards Row (Highlighting primary active routes)
        routes_row = QHBoxLayout()
        routes_row.setSpacing(12)

        self.route_box1 = self._create_route_chip("Shivshahi Premium", "MH-12-RN-1001", "Pune", "Mumbai", "06:30 AM", is_active=True)
        self.route_box2 = self._create_route_chip("Ashwamedh Multi-Axle", "MH-14-BT-2002", "Mumbai", "Nashik", "07:15 AM", is_active=False)
        routes_row.addWidget(self.route_box1)
        routes_row.addWidget(self.route_box2)
        bs_layout.addLayout(routes_row)

        # Visual Waypoint Route Graphic
        waypoint_box = QFrame()
        waypoint_box.setStyleSheet("background: #F8FAFC; border: 1px dashed #CBD5E1; border-radius: 12px; padding: 10px 16px;")
        wp_layout = QHBoxLayout(waypoint_box)
        wp_layout.setContentsMargins(12, 8, 12, 8)
        wp_icon = QLabel("📍")
        wp_icon.setStyleSheet("font-size: 18px;")
        wp_layout.addWidget(wp_icon)
        self.wp_text = QLabel("Live Route: Pune Swargate Depot  ──[ Lonavala ]──>  Mumbai CST Terminal (On Schedule)")
        self.wp_text.setStyleSheet("font-weight: 700; color: #2563EB; font-size: 12px;")
        wp_layout.addWidget(self.wp_text)
        wp_layout.addStretch()
        bs_layout.addWidget(waypoint_box)

        mid_layout.addWidget(bus_summary_card, 62)

        # Mid-Right (38% width): Hero Travel Banner Card matching mockup
        hero_card = QFrame()
        hero_card.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1F2937, stop:1 #111827); "
            "border-radius: 16px; padding: 22px;"
        )
        hero_layout = QVBoxLayout(hero_card)
        hero_layout.setContentsMargins(20, 20, 20, 20)
        hero_layout.setSpacing(12)

        hero_badge = QLabel("🌟 PREMIUM EXPRESS FLEET")
        hero_badge.setStyleSheet("color: #FBBF24; font-size: 10px; font-weight: 800; letter-spacing: 1px;")
        hero_layout.addWidget(hero_badge)

        hero_text = QLabel("Secure your seat and\nenjoy the journey!")
        hero_text.setStyleSheet("color: #FFFFFF; font-size: 20px; font-weight: 800; line-height: 1.2;")
        hero_layout.addWidget(hero_text)

        hero_sub = QLabel("Comfortable sleeper berths, air-conditioned executive coaches, and contactless QR boarding.")
        hero_sub.setWordWrap(True)
        hero_sub.setStyleSheet("color: #9CA3AF; font-size: 11px;")
        hero_layout.addWidget(hero_sub)

        hero_layout.addStretch()

        btn_row = QHBoxLayout()
        book_now_btn = QPushButton("Book Tickets Now  ↗")
        book_now_btn.setStyleSheet(
            "background-color: #2563EB; color: #FFFFFF; font-weight: 700; font-size: 12px; "
            "border-radius: 20px; padding: 9px 18px; border: none;"
        )
        book_now_btn.setCursor(Qt.PointingHandCursor)
        book_now_btn.clicked.connect(self._go_to_booking)
        btn_row.addWidget(book_now_btn)
        btn_row.addStretch()
        hero_layout.addLayout(btn_row)

        mid_layout.addWidget(hero_card, 38)
        self.main_layout.addLayout(mid_layout)

        # ---------------------------------------------------------------------
        # 3. Bottom Section: All Booking List Table + Activity / Timeline Widget
        # ---------------------------------------------------------------------
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(18)

        # Bottom-Left (62% width): All Booking List Table
        bookings_card = QFrame()
        bookings_card.setProperty("class", "Card")
        bks_layout = QVBoxLayout(bookings_card)
        bks_layout.setContentsMargins(18, 18, 18, 18)
        bks_layout.setSpacing(12)

        bk_head = QHBoxLayout()
        bk_title = QLabel("All Booking List")
        bk_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #111827;")
        bk_head.addWidget(bk_title)
        bk_head.addStretch()

        add_bkg_btn = QPushButton("+ New Booking")
        add_bkg_btn.setProperty("class", "primaryButton")
        add_bkg_btn.setCursor(Qt.PointingHandCursor)
        add_bkg_btn.clicked.connect(self._go_to_booking)
        bk_head.addWidget(add_bkg_btn)
        bks_layout.addLayout(bk_head)

        self.bookings_table = QTableWidget()
        self.bookings_table.setColumnCount(5)
        self.bookings_table.setHorizontalHeaderLabels(["Passenger", "Route", "Date / Time", "Seat", "Payment"])
        self.bookings_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.bookings_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.bookings_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.bookings_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.bookings_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.bookings_table.verticalHeader().setVisible(False)
        self.bookings_table.setSelectionBehavior(QTableWidget.SelectRows)
        bks_layout.addWidget(self.bookings_table)

        bottom_layout.addWidget(bookings_card, 62)

        # Bottom-Right (38% width): Activity / Departures Timeline Widget
        activity_card = QFrame()
        activity_card.setProperty("class", "Card")
        act_layout = QVBoxLayout(activity_card)
        act_layout.setContentsMargins(18, 18, 18, 18)
        act_layout.setSpacing(12)

        act_head = QHBoxLayout()
        act_title = QLabel("Activity & Trips")
        act_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #111827;")
        act_head.addWidget(act_title)
        act_head.addStretch()
        self.date_pill = QLabel("Today's Schedule")
        self.date_pill.setStyleSheet("color: #64748B; font-weight: 600; font-size: 11px;")
        act_head.addWidget(self.date_pill)
        act_layout.addLayout(act_head)

        # Weekly calendar day strip (Mon, Tue, Wed, Thu, Fri, Sat, Sun)
        week_strip = QHBoxLayout()
        week_strip.setSpacing(6)
        self.days_list = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        self.day_button_group = QButtonGroup(self)
        self.day_button_group.setExclusive(True)
        self.day_buttons = {}

        # Default to today's weekday
        cur_day_idx = datetime.datetime.now().weekday()
        self.selected_day = self.days_list[cur_day_idx]
        self.date_pill.setText(f"{self.selected_day}'s Schedule")

        for d in self.days_list:
            btn = QPushButton(d)
            btn.setProperty("class", "pillBtn")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            if d == self.selected_day:
                btn.setChecked(True)
            btn.clicked.connect(lambda checked=False, day=d: self._on_day_filter_changed(day))
            self.day_button_group.addButton(btn)
            self.day_buttons[d] = btn
            week_strip.addWidget(btn)
        act_layout.addLayout(week_strip)

        # Trip timeline cards container
        self.timeline_container = QVBoxLayout()
        self.timeline_container.setSpacing(8)
        act_layout.addLayout(self.timeline_container)
        act_layout.addStretch()

        bottom_layout.addWidget(activity_card, 38)
        self.main_layout.addLayout(bottom_layout)

        # Main scroll setup
        scroll_layout = QVBoxLayout(self)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.addWidget(self.scroll)

    def _create_gradient_kpi(self, obj_name: str, icon_str: str, label: str, value: str, badge: str):
        card = QFrame()
        card.setObjectName(obj_name)

        # Explicit gradients to ensure vibrant color rendition across platforms
        gradients = {
            "purpleStatCard": "background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #7C3AED, stop:1 #2563EB);",
            "coralStatCard": "background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #F43F5E, stop:1 #FB923C);",
            "navyStatCard": "background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #1E1B4B, stop:1 #312E81);",
            "violetStatCard": "background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #9333EA, stop:1 #C026D3);"
        }
        grad_css = gradients.get(obj_name, "background: #2563EB;")
        card.setStyleSheet(f"QFrame#{obj_name} {{ {grad_css} border-radius: 16px; border: none; }}")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

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
        bdg.setStyleSheet("background: rgba(255, 255, 255, 0.22); color: #FFFFFF; font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 10px; background-color: rgba(255, 255, 255, 0.22);")
        bot_row.addWidget(bdg)
        bot_row.addStretch()
        layout.addLayout(bot_row)

        return card, val

    def _create_route_chip(self, name: str, reg_no: str, src: str, dst: str, dep_time: str, is_active: bool) -> QWidget:
        chip = QFrame()
        if is_active:
            chip.setStyleSheet(
                "background: #EFF6FF; border: 1.5px solid #3B82F6; border-radius: 12px; padding: 12px;"
            )
        else:
            chip.setStyleSheet(
                "background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 12px;"
            )
        layout = QVBoxLayout(chip)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        t_row = QHBoxLayout()
        b_name = QLabel(name)
        b_name.setStyleSheet("font-weight: 700; color: #0F172A; font-size: 13px;")
        t_row.addWidget(b_name)
        t_row.addStretch()
        t_route = QLabel(f"{src[:3].upper()} ➔ {dst[:3].upper()}")
        t_route.setStyleSheet("color: #2563EB; font-weight: 700; font-size: 11px;")
        t_row.addWidget(t_route)
        layout.addLayout(t_row)

        b_sub = QLabel(f"{reg_no}  •  Departure: {dep_time}")
        b_sub.setStyleSheet("color: #64748B; font-size: 11px;")
        layout.addWidget(b_sub)
        return chip

    def refresh_data(self):
        """Fetches live metrics and populates the EasyBus dashboard."""
        stats = report_repository.get_dashboard_stats()
        self.stats = stats

        # Update Top Gradient Stat Cards
        tot_rev = float(stats.get("total_revenue", 0.0))
        self.val_earnings.setText(f"Rs. {tot_rev:,.2f}")

        today_cnt = stats.get("today_confirmed_bookings", 0)
        self.val_today_bks.setText(f"{today_cnt:,} Bookings")

        today_sched = stats.get("today_schedules", 0)
        active_buses = stats.get("active_buses", 0)
        self.val_departures.setText(f"{today_sched} Journeys")
        self.bs_subtitle.setText(f"Today Active Fleet: {active_buses} Buses across Maharashtra")

        # Populate Bookings Table
        recent = stats.get("recent_bookings", [])
        self.bookings_table.setRowCount(len(recent))
        for row, r in enumerate(recent):
            p_name = r.get("full_name") or r.get("passenger_name") or "Passenger"
            ref = r.get("booking_reference", "")
            self.bookings_table.setItem(row, 0, QTableWidgetItem(f"{p_name}\n({ref})"))
            self.bookings_table.setItem(row, 1, QTableWidgetItem(f"{r.get('source')} ➔ {r.get('destination')}"))
            
            t_date = r.get("travel_date", "")
            self.bookings_table.setItem(row, 2, QTableWidgetItem(t_date))

            seat_no = r.get("seat_number", "")
            self.bookings_table.setItem(row, 3, QTableWidgetItem(f"Seat #{seat_no}"))

            status_str = str(r.get("status", "CONFIRMED")).upper()
            status_item = QTableWidgetItem("Completed" if status_str == "CONFIRMED" else "Pending")
            if status_str == "CONFIRMED":
                status_item.setForeground(Qt.darkGreen)
            else:
                status_item.setForeground(Qt.darkRed)
            self.bookings_table.setItem(row, 4, status_item)

        # Populate Activity / Timeline Widget with upcoming schedules for the selected day
        self._populate_activity_timeline()

    def _on_day_filter_changed(self, day: str):
        """Called when a user clicks on Mon, Tue, Wed, Thu, Fri, Sat, Sun."""
        self.selected_day = day
        self.date_pill.setText(f"{day}'s Schedule")
        self._populate_activity_timeline()

    def _populate_activity_timeline(self):
        """Filters schedules by the selected weekday and renders timeline cards."""
        while self.timeline_container.count():
            item = self.timeline_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        schedules = schedule_repository.list_all_schedules()
        filtered = []
        for s in schedules:
            dt_str = str(s.get("departure_datetime", ""))
            if dt_str:
                try:
                    dt = datetime.datetime.fromisoformat(dt_str)
                    if self.days_list[dt.weekday()] == self.selected_day:
                        filtered.append(s)
                except Exception:
                    pass

        # Sort filtered schedules chronologically by departure time
        filtered.sort(key=lambda x: str(x.get("departure_time", "")))

        if not filtered:
            empty_card = QFrame()
            empty_card.setStyleSheet(
                "background: #F8FAFC; border: 1px dashed #CBD5E1; border-radius: 12px; padding: 18px;"
            )
            e_layout = QVBoxLayout(empty_card)
            e_layout.setAlignment(Qt.AlignCenter)
            e_layout.setSpacing(6)

            ico = QLabel("🚌")
            ico.setAlignment(Qt.AlignCenter)
            ico.setStyleSheet("font-size: 24px; background: transparent;")
            e_layout.addWidget(ico)

            msg = QLabel(f"No scheduled trips for {self.selected_day}")
            msg.setAlignment(Qt.AlignCenter)
            msg.setStyleSheet("color: #475569; font-weight: 700; font-size: 12px; background: transparent;")
            e_layout.addWidget(msg)

            sub = QLabel("Select another day or add a new schedule.")
            sub.setAlignment(Qt.AlignCenter)
            sub.setStyleSheet("color: #94A3B8; font-size: 11px; background: transparent;")
            e_layout.addWidget(sub)

            self.timeline_container.addWidget(empty_card)
            return

        for idx, s in enumerate(filtered[:4]):
            card = QFrame()
            if idx == 0:
                card.setStyleSheet("background: #FEF3C7; border: 1.5px solid #FCD34D; border-radius: 12px; padding: 10px 14px;")
                tag_str = "⚡ NEXT DEPARTURE"
                tag_color = "#92400E"
            else:
                card.setStyleSheet("background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 12px; padding: 10px 14px;")
                tag_str = "🕒 SCHEDULED TRIP"
                tag_color = "#1E40AF"

            c_layout = QVBoxLayout(card)
            c_layout.setContentsMargins(10, 8, 10, 8)
            c_layout.setSpacing(4)

            top_row = QHBoxLayout()
            tag = QLabel(tag_str)
            tag.setStyleSheet(f"font-size: 10px; font-weight: 800; color: {tag_color}; letter-spacing: 0.5px; background: transparent;")
            top_row.addWidget(tag)
            top_row.addStretch()

            seats_left = s.get("available_seats", 0)
            seat_pill = QLabel(f"💺 {seats_left} seats")
            seat_pill.setStyleSheet("color: #475569; font-size: 10px; font-weight: 600; background: transparent;")
            top_row.addWidget(seat_pill)
            c_layout.addLayout(top_row)

            r_title = QLabel(f"{s['bus_name']} ({s['source']} ➔ {s['destination']})")
            r_title.setStyleSheet("font-weight: 700; color: #1E293B; font-size: 12px; background: transparent;")
            c_layout.addWidget(r_title)

            timing = QLabel(f"Departure: {s['departure_time']}  |  Fare: Rs. {float(s['fare']):.2f}")
            timing.setStyleSheet("color: #475569; font-size: 11px; background: transparent;")
            c_layout.addWidget(timing)

            self.timeline_container.addWidget(card)

    def _go_to_booking(self):
        parent = self.window()
        if hasattr(parent, "_switch_to_search"):
            parent._switch_to_search()
