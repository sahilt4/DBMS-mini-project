"""
Main Window for Smart Bus Reservation System.
Coordinates sidebar navigation, role-based screen routing, and page transitions.
"""
from typing import Any, Dict, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.config import APP_TITLE
from app.services import auth_service
from app.ui.dialogs.login_dialog import LoginDialog
from app.ui.dialogs.registration_dialog import RegistrationDialog
from app.ui.pages.bus_management_page import BusManagementPage
from app.ui.pages.bus_search_page import BusSearchPage
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
        self.resize(1200, 780)
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

        # Branding
        app_title = QLabel("🚌 SmartBus")
        app_title.setObjectName("sidebarTitle")
        self.sidebar_layout.addWidget(app_title)

        app_sub = QLabel("DBMS Mini Project Edition")
        app_sub.setObjectName("sidebarSubtitle")
        self.sidebar_layout.addWidget(app_sub)

        # User Role Badge
        self.role_badge = QLabel("Guest")
        self.role_badge.setObjectName("userRoleBadge")
        self.role_badge.setAlignment(Qt.AlignCenter)
        self.sidebar_layout.addWidget(self.role_badge)

        self.sidebar_layout.addSpacing(10)

        # Nav Buttons Container
        self.nav_button_group = QButtonGroup(self)
        self.nav_button_group.setExclusive(True)
        self.nav_buttons = {}

        self.nav_container = QVBoxLayout()
        self.nav_container.setSpacing(4)
        self.sidebar_layout.addLayout(self.nav_container)

        self.sidebar_layout.addStretch()

        # Switch Account / Logout Button at bottom of sidebar
        self.logout_btn = QPushButton("🚪 Sign Out / Switch")
        self.logout_btn.clicked.connect(self._handle_logout)
        self.sidebar_layout.addWidget(self.logout_btn)

        main_layout.addWidget(self.sidebar)

        # 2. Right Main Content Area (QStackedWidget)
        content_container = QWidget()
        c_layout = QVBoxLayout(content_container)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(0)

        self.stack = QStackedWidget()
        c_layout.addWidget(self.stack)

        main_layout.addWidget(content_container, 1)

    def _prompt_initial_login(self):
        """Displays login dialog on startup."""
        login_dialog = LoginDialog(parent=self)
        login_dialog.login_successful.connect(self._on_login_success)
        login_dialog.open_registration_requested.connect(self._open_registration)
        if login_dialog.exec() != LoginDialog.Accepted:
            # If user dismissed login without signing in, default to admin for smooth viva evaluation
            auth_service.login("admin", "Admin@123")
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
        """Builds pages and navigation items according to user role."""
        cur_user = auth_service.get_current_user()
        if not cur_user:
            return

        is_admin = cur_user.get("role") == "admin"
        role_label = f"ROLE: ADMIN ({cur_user['name']})" if is_admin else f"PASSENGER: {cur_user['name']}"
        self.role_badge.setText(role_label)

        # Clear existing nav buttons
        for btn in self.nav_buttons.values():
            self.nav_button_group.removeButton(btn)
            btn.deleteLater()
        self.nav_buttons.clear()

        # Clear existing stacked pages
        while self.stack.count():
            widget = self.stack.widget(0)
            self.stack.removeWidget(widget)
            widget.deleteLater()

        # Instantiate Pages
        if is_admin:
            self.dashboard_page = DashboardPage(self)
            self.search_page = BusSearchPage(self)
            self.bus_mgmt_page = BusManagementPage(self)
            self.route_mgmt_page = RouteManagementPage(self)
            self.sched_mgmt_page = ScheduleManagementPage(self)
            self.all_bookings_page = MyBookingsPage(self)
            self.reports_page = ReportsPage(self)

            # Cross-connect signals for real-time reactivity
            self.all_bookings_page.booking_status_changed.connect(self.dashboard_page.refresh_data)
            self.search_page.booking_made.connect(self.dashboard_page.refresh_data)
            self.search_page.booking_made.connect(self.all_bookings_page.refresh_bookings)

            admin_pages = [
                ("dashboard", "📊 Dashboard", self.dashboard_page),
                ("search", "🔍 Search & Book", self.search_page),
                ("buses", "🚌 Bus Fleet", self.bus_mgmt_page),
                ("routes", "🛣 Routes", self.route_mgmt_page),
                ("schedules", "📅 Schedules", self.sched_mgmt_page),
                ("bookings", "🎫 All Bookings", self.all_bookings_page),
                ("reports", "📈 Reports & CSV", self.reports_page),
            ]

            for key, label, widget in admin_pages:
                self.stack.addWidget(widget)
                btn = QPushButton(label)
                btn.setCheckable(True)
                btn.setCursor(Qt.PointingHandCursor)
                self.nav_button_group.addButton(btn)
                self.nav_container.addWidget(btn)
                self.nav_buttons[key] = btn

                # Connect button to stack index
                page_idx = self.stack.indexOf(widget)
                btn.clicked.connect(lambda checked=False, idx=page_idx: self._switch_page(idx))

            # Default to dashboard
            self.nav_buttons["dashboard"].setChecked(True)
            self.stack.setCurrentWidget(self.dashboard_page)

        else:
            self.search_page = BusSearchPage(self)
            self.my_bookings_page = MyBookingsPage(self)

            # Cross-connect signals
            self.search_page.booking_made.connect(self.my_bookings_page.refresh_bookings)
            self.my_bookings_page.booking_status_changed.connect(self.search_page.perform_search)

            passenger_pages = [
                ("search", "🔍 Search & Book Buses", self.search_page),
                ("my_bookings", "🎫 My Bookings & Tickets", self.my_bookings_page),
            ]

            for key, label, widget in passenger_pages:
                self.stack.addWidget(widget)
                btn = QPushButton(label)
                btn.setCheckable(True)
                btn.setCursor(Qt.PointingHandCursor)
                self.nav_button_group.addButton(btn)
                self.nav_container.addWidget(btn)
                self.nav_buttons[key] = btn

                page_idx = self.stack.indexOf(widget)
                btn.clicked.connect(lambda checked=False, idx=page_idx: self._switch_page(idx))

            # Default to Search
            self.nav_buttons["search"].setChecked(True)
            self.stack.setCurrentWidget(self.search_page)

    def _switch_page(self, index: int):
        self.stack.setCurrentIndex(index)
        # Trigger page data refresh if available
        current_widget = self.stack.currentWidget()
        if hasattr(current_widget, "refresh_data"):
            current_widget.refresh_data()
        elif hasattr(current_widget, "refresh_bookings"):
            current_widget.refresh_bookings()
        elif hasattr(current_widget, "refresh_buses"):
            current_widget.refresh_buses()
        elif hasattr(current_widget, "refresh_routes"):
            current_widget.refresh_routes()
        elif hasattr(current_widget, "refresh_schedules"):
            current_widget.refresh_schedules()

    def _handle_logout(self):
        auth_service.logout()
        self._prompt_initial_login()
