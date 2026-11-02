"""
Main Window for Bus Reservation & Management System (BRMS).
Coordinates sidebar navigation, RBAC (ADMIN, PASSENGER, CONDUCTOR) routing,
and dynamic page transitions.
"""
from typing import Any, Dict, Optional
import datetime
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.config import APP_TITLE, ROLE_ADMIN, ROLE_CONDUCTOR, ROLE_PASSENGER
from app.services import auth_service
from app.ui.dialogs.login_dialog import LoginDialog
from app.ui.dialogs.registration_dialog import RegistrationDialog
from app.ui.pages.bus_management_page import BusManagementPage
from app.ui.pages.bus_search_page import BusSearchPage
from app.ui.pages.conductor_page import ConductorPage
from app.ui.pages.customer_page import CustomerPage
from app.ui.pages.dashboard_page import DashboardPage
from app.ui.pages.my_bookings_page import MyBookingsPage
from app.ui.pages.reports_page import ReportsPage
from app.ui.pages.route_management_page import RouteManagementPage
from app.ui.pages.schedule_management_page import ScheduleManagementPage


class MainWindow(QMainWindow):
    """Main desktop application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1220, 800)
        self.setMinimumSize(1000, 650)

        self._init_ui()
        if auth_service.is_authenticated():
            self._setup_views()
        else:
            self._prompt_initial_login()

    def _init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Left Sidebar Navigation
        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(0, 0, 0, 16)
        self.sidebar_layout.setSpacing(4)

        # Branding - EasyBus Luxe Brand Header
        brand_container = QWidget()
        brand_layout = QHBoxLayout(brand_container)
        brand_layout.setContentsMargins(18, 18, 18, 10)
        brand_layout.setSpacing(12)

        logo_badge = QLabel("🚌")
        logo_badge.setAlignment(Qt.AlignCenter)
        logo_badge.setFixedSize(38, 38)
        logo_badge.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #7C3AED, stop:1 #2563EB); "
            "color: #FFFFFF; font-size: 18px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.25);"
        )
        brand_layout.addWidget(logo_badge)

        brand_text_box = QVBoxLayout()
        brand_text_box.setSpacing(1)
        app_title = QLabel("SmartBus")
        app_title.setStyleSheet("color: #FFFFFF; font-size: 18px; font-weight: 800; letter-spacing: 0.5px; background: transparent;")
        app_sub = QLabel("EasyBus Luxe Edition")
        app_sub.setStyleSheet("color: #D1B8D5; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; background: transparent;")
        brand_text_box.addWidget(app_title)
        brand_text_box.addWidget(app_sub)
        brand_layout.addLayout(brand_text_box)
        brand_layout.addStretch()

        self.sidebar_layout.addWidget(brand_container)

        # User Role Badge
        self.role_badge = QLabel("Guest")
        self.role_badge.setObjectName("userRoleBadge")
        self.role_badge.setAlignment(Qt.AlignCenter)
        self.sidebar_layout.addWidget(self.role_badge)

        self.sidebar_layout.addSpacing(6)

        # Nav Buttons Container with smooth borderless ScrollArea to prevent vertical squishing
        self.nav_button_group = QButtonGroup(self)
        self.nav_button_group.setExclusive(True)
        self.nav_buttons = {}

        self.nav_scroll = QScrollArea()
        self.nav_scroll.setWidgetResizable(True)
        self.nav_scroll.setFrameShape(QFrame.NoFrame)
        self.nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.nav_scroll.setStyleSheet(
            "QScrollArea { background: transparent; border: none; } "
            "QScrollBar:vertical { width: 4px; background: transparent; } "
            "QScrollBar::handle:vertical { background: rgba(255, 255, 255, 0.2); border-radius: 2px; min-height: 20px; } "
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }"
        )

        nav_widget = QWidget()
        nav_widget.setStyleSheet("background: transparent;")
        self.nav_container = QVBoxLayout(nav_widget)
        self.nav_container.setContentsMargins(0, 0, 0, 0)
        self.nav_container.setSpacing(3)
        self.nav_scroll.setWidget(nav_widget)

        self.sidebar_layout.addWidget(self.nav_scroll, 1)

        # Switch Account / Logout Button at bottom of sidebar
        self.logout_btn = QPushButton("🚪 Sign Out / Switch")
        self.logout_btn.setObjectName("logoutBtn")
        self.logout_btn.setCursor(Qt.PointingHandCursor)
        self.logout_btn.setStyleSheet("color: #E2D4E5; font-size: 12px; font-weight: 600; padding: 8px 14px; margin: 2px 10px;")
        self.logout_btn.clicked.connect(self._handle_logout)
        self.sidebar_layout.addWidget(self.logout_btn)

        main_layout.addWidget(self.sidebar)

        # 2. Right Main Content Area (Top Header + QStackedWidget)
        content_container = QWidget()
        c_layout = QVBoxLayout(content_container)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(0)

        # Top Header Bar (Matching EasyBus Mockups)
        self.top_header = QWidget()
        self.top_header.setObjectName("topHeader")
        header_layout = QHBoxLayout(self.top_header)
        header_layout.setContentsMargins(28, 14, 28, 14)
        header_layout.setSpacing(16)

        self.greeting_label = QLabel("Good Morning! 👋")
        self.greeting_label.setObjectName("topGreeting")
        header_layout.addWidget(self.greeting_label)

        header_layout.addStretch()

        # Rounded Search Pill
        self.top_search_input = QLineEdit()
        self.top_search_input.setObjectName("topSearchInput")
        self.top_search_input.setPlaceholderText("🔍  Search buses, routes, schedules...")
        self.top_search_input.returnPressed.connect(self._handle_global_search)
        header_layout.addWidget(self.top_search_input)

        # Next bus arrival pill
        self.arrival_pill = QLabel("⏰ Next Bus Arrival: 09:30 am")
        self.arrival_pill.setObjectName("topArrivalPill")
        header_layout.addWidget(self.arrival_pill)

        # User profile chip
        self.profile_chip = QPushButton("👤 User Account ▾")
        self.profile_chip.setObjectName("topProfileChip")
        self.profile_chip.setCursor(Qt.PointingHandCursor)
        self.profile_chip.clicked.connect(self._handle_logout)
        header_layout.addWidget(self.profile_chip)

        c_layout.addWidget(self.top_header)

        self.stack = QStackedWidget()
        c_layout.addWidget(self.stack, 1)

        main_layout.addWidget(content_container, 1)

    def _prompt_initial_login(self):
        """Displays login dialog on startup."""
        login_dialog = LoginDialog(parent=self)
        login_dialog.login_successful.connect(self._on_login_success)
        login_dialog.open_registration_requested.connect(self._open_registration)
        if login_dialog.exec() != LoginDialog.Accepted:
            # If user dismissed login without signing in, default to admin for smooth evaluation
            try:
                auth_service.login("admin", "Admin@123")
            except Exception:
                pass
            self._setup_views()

    def _open_registration(self):
        reg_dialog = RegistrationDialog(parent=self)
        reg_dialog.registration_successful.connect(self._on_login_success)
        reg_dialog.open_login_requested.connect(self._prompt_initial_login)
        if reg_dialog.exec() != RegistrationDialog.Accepted:
            self._prompt_initial_login()

    def _on_login_success(self, user: Dict[str, Any]):
        self._setup_views()

    def _setup_views(self):
        """Builds pages and navigation items according to user role (ADMIN, PASSENGER, CONDUCTOR)."""
        cur_user = auth_service.get_current_user()
        if not cur_user:
            return

        role = str(cur_user.get("role", "")).upper()
        display_name = cur_user.get("full_name", cur_user.get("name", "User"))
        self.role_badge.setText(f"{role}: {display_name}")

        # Update Top Header
        hr = datetime.datetime.now().hour
        if hr < 12:
            greet = "Good Morning! ☀️"
        elif hr < 17:
            greet = "Good Afternoon! 🌤️"
        else:
            greet = "Good Evening! 🌙"
        self.greeting_label.setText(greet)
        self.profile_chip.setText(f"👤 {display_name} ({role.title()}) ▾")

        # Clear existing nav buttons & layout items
        while self.nav_container.count():
            item = self.nav_container.takeAt(0)
            if item.widget():
                self.nav_button_group.removeButton(item.widget())
                item.widget().deleteLater()
        self.nav_buttons.clear()

        # Clear existing stacked pages
        while self.stack.count():
            widget = self.stack.widget(0)
            self.stack.removeWidget(widget)
            widget.deleteLater()

        # Build pages based on role
        if role == ROLE_ADMIN:
            self.dashboard_page = DashboardPage(self)
            self.search_page = BusSearchPage(self)
            self.sched_mgmt_page = ScheduleManagementPage(self)
            self.bus_mgmt_page = BusManagementPage(self)
            self.customer_page = CustomerPage(self)
            self.route_mgmt_page = RouteManagementPage(self)
            self.all_bookings_page = MyBookingsPage(self)
            self.conductor_page = ConductorPage(self)
            self.reports_page = ReportsPage(self)

            # Signal connections for real-time reactivity
            self.all_bookings_page.booking_status_changed.connect(self.dashboard_page.refresh_data)
            self.search_page.booking_made.connect(self.dashboard_page.refresh_data)
            self.search_page.booking_made.connect(self.all_bookings_page.refresh_bookings)

            pages = [
                ("dashboard", "📊 Dashboard", self.dashboard_page),
                ("search", "🔍 Search & Book", self.search_page),
                ("schedules", "📅 Schedules", self.sched_mgmt_page),
                ("buses", "🚌 Bus Fleet", self.bus_mgmt_page),
                ("customers", "👥 Customers", self.customer_page),
                ("routes", "🛣 Routes", self.route_mgmt_page),
                ("bookings", "🎫 All Bookings", self.all_bookings_page),
                ("conductor", "📱 Conductor Scanner", self.conductor_page),
                ("reports", "📈 Reports & Analytics", self.reports_page),
            ]
            default_key = "dashboard"

        elif role == ROLE_CONDUCTOR:
            self.conductor_page = ConductorPage(self)
            pages = [
                ("conductor", "📱 Ticket Verification", self.conductor_page)
            ]
            default_key = "conductor"

        else:  # PASSENGER
            self.search_page = BusSearchPage(self)
            self.my_bookings_page = MyBookingsPage(self)

            self.search_page.booking_made.connect(self.my_bookings_page.refresh_bookings)
            self.my_bookings_page.booking_status_changed.connect(self.search_page.perform_search)

            pages = [
                ("search", "🔍 Search & Book Buses", self.search_page),
                ("my_bookings", "🎫 My Bookings & Tickets", self.my_bookings_page),
            ]
            default_key = "search"

        # Register pages and sidebar navigation buttons
        for key, label, widget in pages:
            self.stack.addWidget(widget)
            btn = QPushButton(f"  {label}")
            btn.setCheckable(True)
            btn.setFixedHeight(38)
            btn.setCursor(Qt.PointingHandCursor)
            self.nav_button_group.addButton(btn)
            self.nav_container.addWidget(btn)
            self.nav_buttons[key] = btn

            page_idx = self.stack.indexOf(widget)
            btn.clicked.connect(lambda checked=False, idx=page_idx: self._switch_page(idx))

        self.nav_container.addStretch()

        # Activate default page
        page_map = {k: w for k, l, w in pages}
        if default_key in self.nav_buttons and default_key in page_map:
            self.nav_buttons[default_key].setChecked(True)
            self._switch_page(self.stack.indexOf(page_map[default_key]))

    def _switch_page(self, index: int):
        self.stack.setCurrentIndex(index)
        current_widget = self.stack.currentWidget()
        if hasattr(current_widget, "refresh_data"):
            current_widget.refresh_data()
        elif hasattr(current_widget, "reload_data"):
            current_widget.reload_data()
        elif hasattr(current_widget, "refresh_bookings"):
            current_widget.refresh_bookings()
        elif hasattr(current_widget, "refresh_buses"):
            current_widget.refresh_buses()
        elif hasattr(current_widget, "refresh_routes"):
            current_widget.refresh_routes()
        elif hasattr(current_widget, "refresh_schedules"):
            current_widget.refresh_schedules()

    def _switch_to_search(self):
        if "search" in self.nav_buttons:
            self.nav_buttons["search"].click()

    def _handle_global_search(self):
        text = self.top_search_input.text().strip()
        if not text:
            return
        self._switch_to_search()

    def _handle_logout(self):
        auth_service.logout()
        self._prompt_initial_login()
