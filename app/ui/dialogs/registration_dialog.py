"""
Passenger Registration Dialog with full profile details.
"""
from PySide6.QtCore import Qt, Signal
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

from app.services import auth_service


class RegistrationDialog(QDialog):
    """Passenger account registration dialog."""
    registration_successful = Signal(dict)
    open_login_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Register New Passenger Account")
        self.setFixedSize(440, 580)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(10)

        title = QLabel("Create Account")
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #0F172A;")
        layout.addWidget(title)

        sub = QLabel("Sign up to reserve bus tickets and manage your trips")
        sub.setStyleSheet("font-size: 12px; color: #64748B; margin-bottom: 6px;")
        layout.addWidget(sub)

        # Full Name
        layout.addWidget(QLabel("Full Name *"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Ramesh Kulkarni")
        layout.addWidget(self.name_input)

        # Username
        layout.addWidget(QLabel("Username *"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("e.g. ramesh_k")
        layout.addWidget(self.username_input)

        # Password & Confirm Password
        pass_row = QHBoxLayout()
        v1 = QVBoxLayout()
        v1.addWidget(QLabel("Password *"))
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.pass_input.setPlaceholderText("Min 6 chars")
        v1.addWidget(self.pass_input)
        pass_row.addLayout(v1)

        v2 = QVBoxLayout()
        v2.addWidget(QLabel("Confirm Password *"))
        self.confirm_pass_input = QLineEdit()
        self.confirm_pass_input.setEchoMode(QLineEdit.Password)
        self.confirm_pass_input.setPlaceholderText("Re-type password")
        v2.addWidget(self.confirm_pass_input)
        pass_row.addLayout(v2)
        layout.addLayout(pass_row)

        # Age & Gender
        details_row = QHBoxLayout()
        v_age = QVBoxLayout()
        v_age.addWidget(QLabel("Age *"))
        self.age_input = QSpinBox()
        self.age_input.setRange(1, 120)
        self.age_input.setValue(25)
        v_age.addWidget(self.age_input)
        details_row.addLayout(v_age)

        v_gen = QVBoxLayout()
        v_gen.addWidget(QLabel("Gender"))
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["Male", "Female", "Other"])
        v_gen.addWidget(self.gender_combo)
        details_row.addLayout(v_gen)
        layout.addLayout(details_row)

        # Phone Number
        layout.addWidget(QLabel("Phone Number"))
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("e.g. 9822012345")
        layout.addWidget(self.phone_input)

        # Error label
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #DC2626; font-size: 12px; font-weight: 600;")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)

        layout.addSpacing(6)

        # Submit Button
        self.submit_btn = QPushButton("Register & Sign In")
        self.submit_btn.setProperty("class", "primaryButton")
        self.submit_btn.setFixedHeight(38)
        self.submit_btn.clicked.connect(self._handle_register)
        layout.addWidget(self.submit_btn)

        # Back to Login
        self.back_btn = QPushButton("Already have an account? Sign In")
        self.back_btn.setStyleSheet("border: none; background: transparent; color: #2563EB; font-weight: 600;")
        self.back_btn.clicked.connect(self._handle_back_login)
        layout.addWidget(self.back_btn)

    def _handle_register(self):
        name = self.name_input.text()
        user = self.username_input.text()
        pwd = self.pass_input.text()
        cpwd = self.confirm_pass_input.text()
        age = self.age_input.value()
        gen = self.gender_combo.currentText()
        phone = self.phone_input.text()
        self.error_label.hide()

        try:
            new_user = auth_service.register(
                name=name,
                username=user,
                password=pwd,
                confirm_password=cpwd,
                age=age,
                gender=gen,
                phone=phone
            )
            QMessageBox.information(self, "Success", "Registration successful! You are now logged in.")
            self.registration_successful.emit(new_user)
            self.accept()
        except ValueError as err:
            self.error_label.setText(str(err))
            self.error_label.show()

    def _handle_back_login(self):
        self.reject()
        self.open_login_requested.emit()
