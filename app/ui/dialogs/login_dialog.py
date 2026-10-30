"""
Login Dialog with password toggle and demo credentials helper.
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from app.services import auth_service


class LoginDialog(QDialog):
    """Modal login dialog supporting username/password and convenient demo logins."""
    login_successful = Signal(dict)
    open_registration_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Smart Bus Reservation - Login")
        self.setFixedSize(420, 520)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(14)

        # Header Title
        title_label = QLabel("Welcome Back")
        title_label.setStyleSheet("font-size: 22px; font-weight: 700; color: #0F172A;")
        layout.addWidget(title_label)

        sub_label = QLabel("Sign in to your bus reservation account")
        sub_label.setStyleSheet("font-size: 13px; color: #64748B; margin-bottom: 8px;")
        layout.addWidget(sub_label)

        # Username
        u_label = QLabel("Username")
        u_label.setProperty("class", "formLabel")
        layout.addWidget(u_label)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        layout.addWidget(self.username_input)

        # Password
        p_label = QLabel("Password")
        p_label.setProperty("class", "formLabel")
        layout.addWidget(p_label)

        pass_row = QHBoxLayout()
        pass_row.setSpacing(6)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.returnPressed.connect(self._handle_login)
        pass_row.addWidget(self.password_input)

        self.toggle_pass_btn = QPushButton("👁")
        self.toggle_pass_btn.setFixedWidth(40)
        self.toggle_pass_btn.setToolTip("Toggle password visibility")
        self.toggle_pass_btn.clicked.connect(self._toggle_password_visibility)
        pass_row.addWidget(self.toggle_pass_btn)
        layout.addLayout(pass_row)

        # Error display label
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #DC2626; font-size: 12px; font-weight: 600;")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)

        # Login Button
        self.login_btn = QPushButton("Sign In")
        self.login_btn.setProperty("class", "primaryButton")
        self.login_btn.setFixedHeight(38)
        self.login_btn.clicked.connect(self._handle_login)
        layout.addWidget(self.login_btn)

        # Register Link Button
        self.register_btn = QPushButton("Don't have an account? Register Here")
        self.register_btn.setStyleSheet("border: none; background: transparent; color: #2563EB; font-weight: 600;")
        self.register_btn.clicked.connect(self._handle_open_register)
        layout.addWidget(self.register_btn)

        layout.addSpacing(10)

        # Demo Credentials Box (Extremely helpful for college viva demonstration!)
        demo_box = QVBoxLayout()
        demo_title = QLabel("Demo Accounts for College Viva:")
        demo_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase;")
        demo_box.addWidget(demo_title)

        demo_btns_row = QHBoxLayout()
        demo_btns_row.setSpacing(8)

        btn_admin = QPushButton("Admin\n(admin)")
        btn_admin.setStyleSheet("font-size: 11px; padding: 6px; text-align: center;")
        btn_admin.clicked.connect(lambda: self._fill_demo("admin", "Admin@123"))
        demo_btns_row.addWidget(btn_admin)

        btn_pass1 = QPushButton("Passenger\n(rahul_sharma)")
        btn_pass1.setStyleSheet("font-size: 11px; padding: 6px; text-align: center;")
        btn_pass1.clicked.connect(lambda: self._fill_demo("rahul_sharma", "Rahul@123"))
        demo_btns_row.addWidget(btn_pass1)

        btn_pass2 = QPushButton("Passenger\n(priya_patil)")
        btn_pass2.setStyleSheet("font-size: 11px; padding: 6px; text-align: center;")
        btn_pass2.clicked.connect(lambda: self._fill_demo("priya_patil", "Priya@123"))
        demo_btns_row.addWidget(btn_pass2)

        demo_box.addLayout(demo_btns_row)
        layout.addLayout(demo_box)

    def _toggle_password_visibility(self):
        if self.password_input.echoMode() == QLineEdit.Password:
            self.password_input.setEchoMode(QLineEdit.Normal)
            self.toggle_pass_btn.setText("🔒")
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
            self.toggle_pass_btn.setText("👁")

    def _fill_demo(self, username, password):
        self.username_input.setText(username)
        self.password_input.setText(password)
        self.error_label.hide()

    def _handle_login(self):
        u = self.username_input.text().strip()
        p = self.password_input.text()
        self.error_label.hide()

        try:
            user = auth_service.login(u, p)
            self.login_successful.emit(user)
            self.accept()
        except ValueError as err:
            self.error_label.setText(str(err))
            self.error_label.show()

    def _handle_open_register(self):
        self.reject()
        self.open_registration_requested.emit()
