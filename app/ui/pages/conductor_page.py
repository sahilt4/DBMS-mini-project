"""
Conductor Operational Dashboard and Digital Ticket Verification Page.
Supports Passenger Manifest inspection, OpenCV Camera QR Code Scanning,
and instant database check-in recording (ticket_checkins).
"""
import json
from typing import Optional

import cv2
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QImage, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.repositories import booking_repository, schedule_repository
from app.services import auth_service, verification_service


class ConductorPage(QWidget):
    """Operational page for conductors to verify tickets and manage manifests."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.camera_cap = None
        self.camera_timer = QTimer(self)
        self.camera_timer.timeout.connect(self._process_camera_frame)
        self.qr_detector = cv2.QRCodeDetector()
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # Header Title
        title_row = QHBoxLayout()
        header = QLabel("Conductor Verification Portal")
        header.setStyleSheet("font-size: 22px; font-weight: 700; color: #0F172A;")
        title_row.addWidget(header)
        title_row.addStretch()

        self.refresh_btn = QPushButton("🔄 Refresh Manifest")
        self.refresh_btn.clicked.connect(self.reload_data)
        title_row.addWidget(self.refresh_btn)
        main_layout.addLayout(title_row)

        # Trip Selection bar
        trip_box = QHBoxLayout()
        trip_box.addWidget(QLabel("<b>Select Active Trip:</b>"))
        self.sched_combo = QComboBox()
        self.sched_combo.setMinimumWidth(400)
        self.sched_combo.currentIndexChanged.connect(self._load_trip_manifest)
        trip_box.addWidget(self.sched_combo)
        trip_box.addStretch()
        main_layout.addLayout(trip_box)

        # Splitter: Left Manifest Table, Right Verification Tools
        splitter = QSplitter(Qt.Horizontal)

        # Left: Passenger Manifest
        manifest_widget = QWidget()
        m_layout = QVBoxLayout(manifest_widget)
        m_layout.setContentsMargins(0, 0, 8, 0)
        m_layout.addWidget(QLabel("<b>Trip Passenger Manifest:</b>"))

        self.manifest_table = QTableWidget()
        self.manifest_table.setColumnCount(6)
        self.manifest_table.setHorizontalHeaderLabels([
            "Seat #", "Passenger Name", "Gender/Age", "Contact Phone", "Boarding Point", "Check-in Status"
        ])
        self.manifest_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.manifest_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.manifest_table.setAlternatingRowColors(True)
        m_layout.addWidget(self.manifest_table)
        splitter.addWidget(manifest_widget)

        # Right: Verification Controls
        right_panel = QWidget()
        r_layout = QVBoxLayout(right_panel)
        r_layout.setContentsMargins(8, 0, 0, 0)
        r_layout.setSpacing(14)

        # Manual / Scan verification box
        verify_group = QGroupBox("Ticket Verification")
        vg_layout = QVBoxLayout(verify_group)
        vg_layout.setSpacing(10)

        vg_layout.addWidget(QLabel("<b>Scan QR or Enter Booking Reference:</b>"))
        self.ref_input = QLineEdit()
        self.ref_input.setPlaceholderText("e.g. BUS-20261031-XXXXXX")
        self.ref_input.returnPressed.connect(self._handle_manual_verify)
        vg_layout.addWidget(self.ref_input)

        btn_row = QHBoxLayout()
        self.verify_btn = QPushButton("✓ Verify & Check-In")
        self.verify_btn.setProperty("class", "primaryButton")
        self.verify_btn.clicked.connect(self._handle_manual_verify)
        btn_row.addWidget(self.verify_btn)

        self.cam_btn = QPushButton("📷 Open QR Camera")
        self.cam_btn.clicked.connect(self._toggle_camera_scanner)
        btn_row.addWidget(self.cam_btn)
        vg_layout.addLayout(btn_row)

        # Camera Feed Preview Label
        self.cam_preview = QLabel("Camera Feed Inactive")
        self.cam_preview.setAlignment(Qt.AlignCenter)
        self.cam_preview.setMinimumHeight(180)
        self.cam_preview.setStyleSheet("background: #0F172A; color: #94A3B8; border-radius: 8px;")
        vg_layout.addWidget(self.cam_preview)

        # Result Banner
        self.result_banner = QLabel("Ready to scan passenger tickets.")
        self.result_banner.setAlignment(Qt.AlignCenter)
        self.result_banner.setStyleSheet("background: #F1F5F9; color: #475569; padding: 10px; border-radius: 6px; font-weight: 600;")
        vg_layout.addWidget(self.result_banner)

        r_layout.addWidget(verify_group)

        # Conductor History
        history_group = QGroupBox("Recent Check-Ins")
        hg_layout = QVBoxLayout(history_group)
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["Time", "Ref", "Seat", "Passenger"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        hg_layout.addWidget(self.history_table)
        r_layout.addWidget(history_group)

        splitter.addWidget(right_panel)
        splitter.setSizes([550, 450])
        main_layout.addWidget(splitter)

    def reload_data(self):
        """Populates trips dropdown and reloads data."""
        self.sched_combo.blockSignals(True)
        self.sched_combo.clear()

        schedules = schedule_repository.list_all_schedules(status="SCHEDULED")
        for s in schedules:
            label = f"Trip #{s['schedule_id']} | {s['source']} → {s['destination']} ({s['travel_date']} {s['departure_time']}) - {s['bus_name']}"
            self.sched_combo.addItem(label, s["schedule_id"])

        self.sched_combo.blockSignals(False)
        self._load_trip_manifest()
        self._load_conductor_history()

    def _load_trip_manifest(self):
        sched_id = self.sched_combo.currentData()
        if not sched_id:
            self.manifest_table.setRowCount(0)
            return

        manifest = booking_repository.get_schedule_manifest(sched_id)
        self.manifest_table.setRowCount(len(manifest))

        for row, item in enumerate(manifest):
            seat_item = QTableWidgetItem(f"#{item['seat_number']}")
            seat_item.setTextAlignment(Qt.AlignCenter)
            seat_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.manifest_table.setItem(row, 0, seat_item)

            self.manifest_table.setItem(row, 1, QTableWidgetItem(str(item.get("passenger_name", ""))))
            self.manifest_table.setItem(row, 2, QTableWidgetItem(f"{item.get('gender', '')} / {item.get('age', '')}"))
            self.manifest_table.setItem(row, 3, QTableWidgetItem(str(item.get("phone", ""))))
            self.manifest_table.setItem(row, 4, QTableWidgetItem(str(item.get("boarding_stop") or "Origin Depot")))

            status_text = item.get("checkin_status") or ("CHECKED_IN" if item.get("booking_status") == "CHECKED_IN" else "CONFIRMED")
            stat_item = QTableWidgetItem(status_text)
            stat_item.setTextAlignment(Qt.AlignCenter)
            if status_text in ("VERIFIED", "CHECKED_IN"):
                stat_item.setForeground(QColor("#15803D"))
                stat_item.setBackground(QColor("#DCFCE7"))
            else:
                stat_item.setForeground(QColor("#1E3A8A"))
                stat_item.setBackground(QColor("#DBEAFE"))
            self.manifest_table.setItem(row, 5, stat_item)

    def _load_conductor_history(self):
        curr_user = auth_service.get_current_user()
        if not curr_user:
            return
        cond_id = curr_user["user_id"]
        history = verification_service.get_conductor_history(cond_id)
        self.history_table.setRowCount(len(history))
        for row, h in enumerate(history):
            self.history_table.setItem(row, 0, QTableWidgetItem(str(h.get("checkin_time", ""))[11:16]))
            self.history_table.setItem(row, 1, QTableWidgetItem(str(h.get("booking_reference", ""))))
            self.history_table.setItem(row, 2, QTableWidgetItem(f"#{h.get('seat_number', '')}"))
            self.history_table.setItem(row, 3, QTableWidgetItem(str(h.get("passenger_name", ""))))

    def _handle_manual_verify(self):
        ref = self.ref_input.text().strip()
        if not ref:
            QMessageBox.warning(self, "Input Required", "Please enter a booking reference or scan a QR code.")
            return

        curr_user = auth_service.get_current_user()
        cond_id = curr_user["user_id"] if curr_user else 2

        res = verification_service.verify_ticket(ref, conductor_id=cond_id)
        self._display_verification_result(res)

        if res.get("success"):
            self.ref_input.clear()
            self._load_trip_manifest()
            self._load_conductor_history()

    def _display_verification_result(self, res: dict):
        status = res.get("status")
        msg = res.get("message", "")

        if status == "VERIFIED":
            self.result_banner.setText(f"✓ {msg}")
            self.result_banner.setStyleSheet("background: #DCFCE7; color: #15803D; padding: 12px; border-radius: 6px; font-weight: 700; font-size: 13px;")
        elif status == "ALREADY_CHECKED_IN":
            self.result_banner.setText(f"⚠️ {msg}")
            self.result_banner.setStyleSheet("background: #FEF3C7; color: #B45309; padding: 12px; border-radius: 6px; font-weight: 700; font-size: 13px;")
        else:
            self.result_banner.setText(f"❌ {msg}")
            self.result_banner.setStyleSheet("background: #FEE2E2; color: #B91C1C; padding: 12px; border-radius: 6px; font-weight: 700; font-size: 13px;")

    def _toggle_camera_scanner(self):
        if self.camera_timer.isActive():
            self.camera_timer.stop()
            if self.camera_cap:
                self.camera_cap.release()
                self.camera_cap = None
            self.cam_btn.setText("📷 Open QR Camera")
            self.cam_preview.setText("Camera Feed Inactive")
            self.cam_preview.setStyleSheet("background: #0F172A; color: #94A3B8; border-radius: 8px;")
        else:
            try:
                self.camera_cap = cv2.VideoCapture(0)
                if not self.camera_cap.isOpened():
                    QMessageBox.information(
                        self, "Camera Device",
                        "No physical webcam was detected on this device. You can verify tickets directly by entering the Booking Reference."
                    )
                    return

                self.cam_btn.setText("⏹ Stop Camera")
                self.camera_timer.start(50)  # 20 FPS
            except Exception as err:
                QMessageBox.critical(self, "Camera Error", f"Could not initialize camera: {err}")

    def _process_camera_frame(self):
        if not self.camera_cap or not self.camera_cap.isOpened():
            return
        ret, frame = self.camera_cap.read()
        if not ret:
            return

        # Detect QR Code
        data, bbox, _ = self.qr_detector.detectAndDecode(frame)
        if data:
            # Found QR payload!
            self._toggle_camera_scanner()
            self.ref_input.setText(data)
            self._handle_manual_verify()
            return

        # Render preview in Qt label
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        qimg = QImage(rgb_frame.data, w, h, ch * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg).scaled(
            self.cam_preview.width(), self.cam_preview.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.cam_preview.setPixmap(pixmap)

    def hideEvent(self, event):
        """Stop camera when switching away from conductor page."""
        if self.camera_timer.isActive():
            self._toggle_camera_scanner()
        super().hideEvent(event)
