"""
Reports & CSV Export Page for Administrators.
Provides interactive analytical reports powered by SQL JOINs and aggregates,
with instant CSV export to file.
"""
from typing import Any, List
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.services import report_service


class ReportsPage(QWidget):
    """Administrative analytics and CSV export reports page."""

    REPORT_OPTIONS = [
        ("confirmed_bookings", "All Active Confirmed Bookings"),
        ("cancelled_bookings", "Cancelled Bookings Audit & Refunds"),
        ("bookings_by_route", "Aggregated Bookings & Revenue by Route"),
        ("bookings_by_bus", "Aggregated Bookings & Revenue by Bus"),
        ("bus_occupancy", "Bus Occupancy Rate Analysis (%)"),
        ("audit_logs", "Security & System Audit Logs"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_headers: List[str] = []
        self.current_rows: List[List[Any]] = []
        self._init_ui()
        self.load_selected_report()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header Title
        header_row = QHBoxLayout()
        v_title = QVBoxLayout()
        title = QLabel("System Reports & Analytics")
        title.setObjectName("pageTitle")
        sub = QLabel("Run DBMS aggregate queries (JOIN, GROUP BY, SUM, COUNT) and export data to CSV")
        sub.setObjectName("pageDescription")
        v_title.addWidget(title)
        v_title.addWidget(sub)
        header_row.addLayout(v_title)
        header_row.addStretch()

        self.export_csv_btn = QPushButton("📥 Export to CSV")
        self.export_csv_btn.setProperty("class", "primaryButton")
        self.export_csv_btn.clicked.connect(self._handle_csv_export)
        header_row.addWidget(self.export_csv_btn)
        layout.addLayout(header_row)

        # Control Card
        control_card = QWidget()
        control_card.setObjectName("statCard")
        c_layout = QHBoxLayout(control_card)
        c_layout.setContentsMargins(14, 10, 14, 10)
        c_layout.setSpacing(12)

        c_layout.addWidget(QLabel("Select Report:"))
        self.report_combo = QComboBox()
        self.report_combo.setMinimumWidth(320)
        for key, name in self.REPORT_OPTIONS:
            self.report_combo.addItem(name, key)
        self.report_combo.currentIndexChanged.connect(self.load_selected_report)
        c_layout.addWidget(self.report_combo)

        self.refresh_btn = QPushButton("🔄 Re-run Query")
        self.refresh_btn.clicked.connect(self.load_selected_report)
        c_layout.addWidget(self.refresh_btn)
        c_layout.addStretch()

        layout.addWidget(control_card)

        # Record count label
        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #475569;")
        layout.addWidget(self.status_lbl)

        # Report Table
        self.table = QTableWidget()
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

    def load_selected_report(self):
        report_key = self.report_combo.currentData()
        self.current_headers, self.current_rows = report_service.get_report(report_key)

        self.table.setColumnCount(len(self.current_headers))
        self.table.setHorizontalHeaderLabels(self.current_headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.table.setRowCount(len(self.current_rows))
        for row_idx, row in enumerate(self.current_rows):
            for col_idx, val in enumerate(row):
                val_str = "" if val is None else str(val)
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(val_str))

        self.status_lbl.setText(f"Query returned {len(self.current_rows)} records.")

    def _handle_csv_export(self):
        if not self.current_rows:
            QMessageBox.information(self, "No Data", "There are no records to export in the selected report.")
            return

        report_key = self.report_combo.currentData()
        default_file = f"Report_{report_key}.csv"
        filepath, _ = QFileDialog.getSaveFileName(self, "Export Report to CSV", default_file, "CSV Files (*.csv)")
        if not filepath:
            return

        try:
            exported_path = report_service.export_report_to_csv(
                headers=self.current_headers,
                rows=self.current_rows,
                output_filepath=filepath
            )
            QMessageBox.information(
                self,
                "Export Complete",
                f"Successfully exported {len(self.current_rows)} records to:\n{exported_path}"
            )
        except Exception as err:
            QMessageBox.critical(self, "Export Error", f"Could not write CSV file:\n{err}")
