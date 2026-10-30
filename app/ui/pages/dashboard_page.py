"""
Admin Dashboard Page.
Displays real-time database-backed KPI statistics cards, recent bookings table,
occupancy summary, and an integrated Matplotlib analytics chart.
"""
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
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

from app.repositories import report_repository


class DashboardPage(QWidget):
    """Admin Dashboard Page with statistics and embedded Matplotlib visual."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self.refresh_data()

    def _init_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        self.layout = QVBoxLayout(container)
        self.layout.setContentsMargins(24, 20, 24, 20)
        self.layout.setSpacing(18)

        # Header bar with refresh button
        header_row = QHBoxLayout()
        v_title = QVBoxLayout()
        title = QLabel("System Dashboard")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Real-time DBMS metrics, fleet activity, and revenue statistics")
        subtitle.setObjectName("pageDescription")
        v_title.addWidget(title)
        v_title.addWidget(subtitle)
        header_row.addLayout(v_title)
        header_row.addStretch()

        self.refresh_btn = QPushButton("🔄 Refresh Dashboard")
        self.refresh_btn.clicked.connect(self.refresh_data)
        header_row.addWidget(self.refresh_btn)
        self.layout.addLayout(header_row)

        # 6 KPI Stat Cards in a Grid
        self.kpi_grid = QGridLayout()
        self.kpi_grid.setSpacing(14)
        
        self.cards = {}
        kpi_defs = [
            ("active_buses", "Active Buses", "0", 0, 0),
            ("active_routes", "Active Routes", "0", 0, 1),
            ("today_schedules", "Today's Journeys", "0", 0, 2),
            ("total_confirmed_bookings", "Total Bookings", "0", 1, 0),
            ("today_confirmed_bookings", "Today's Bookings", "0", 1, 1),
            ("total_revenue", "Total Revenue", "Rs. 0.00", 1, 2),
        ]

        for key, label, def_val, row, col in kpi_defs:
            card = QWidget()
            card.setObjectName("statCard")
            c_layout = QVBoxLayout(card)
            c_layout.setContentsMargins(16, 14, 16, 14)
            c_layout.setSpacing(4)

            lbl_title = QLabel(label)
            lbl_title.setObjectName("statLabel")
            val_lbl = QLabel(def_val)
            val_lbl.setObjectName("statValue")

            c_layout.addWidget(lbl_title)
            c_layout.addWidget(val_lbl)
            self.kpi_grid.addWidget(card, row, col)
            self.cards[key] = val_lbl

        self.layout.addLayout(self.kpi_grid)

        # Matplotlib Chart Section (Revenue & Bookings Trend)
        chart_card = QWidget()
        chart_card.setObjectName("statCard")
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(14, 10, 14, 10)
        chart_layout.setSpacing(6)

        chart_title = QLabel("Daily Confirmed Bookings & Simulated Revenue Trend")
        chart_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #0F172A;")
        chart_layout.addWidget(chart_title)

        # Reduced chart height so bottom tables have generous visible room
        self.figure = Figure(figsize=(8, 2.0), dpi=100)
        self.figure.patch.set_facecolor('#FFFFFF')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumHeight(150)
        self.canvas.setMaximumHeight(180)
        chart_layout.addWidget(self.canvas)

        self.layout.addWidget(chart_card)

        # Tables Section: Recent Bookings & High Occupancy
        tables_row = QHBoxLayout()
        tables_row.setSpacing(16)

        # Left Table: Recent Bookings
        recent_box = QGroupBox("Recent Reservations")
        recent_box.setStyleSheet(
            "QGroupBox { font-size: 13px; font-weight: 700; color: #0F172A; border: 1px solid #CBD5E1; border-radius: 8px; margin-top: 16px; padding: 14px 10px 10px 10px; background-color: #FFFFFF; } "
            "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 14px; padding: 0 6px; background-color: #FFFFFF; color: #0F172A; }"
        )
        v_rec = QVBoxLayout(recent_box)
        v_rec.setContentsMargins(8, 12, 8, 8)
        self.recent_table = QTableWidget()
        self.recent_table.setColumnCount(4)
        self.recent_table.setHorizontalHeaderLabels(["Reference", "Passenger", "Route", "Amount"])
        self.recent_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.recent_table.verticalHeader().setVisible(False)
        self.recent_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.recent_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.recent_table.setMinimumHeight(240)
        v_rec.addWidget(self.recent_table)
        tables_row.addWidget(recent_box, 1)

        # Right Table: High Occupancy Schedules
        occ_box = QGroupBox("Top Occupancy Journeys")
        occ_box.setStyleSheet(
            "QGroupBox { font-size: 13px; font-weight: 700; color: #0F172A; border: 1px solid #CBD5E1; border-radius: 8px; margin-top: 16px; padding: 14px 10px 10px 10px; background-color: #FFFFFF; } "
            "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 14px; padding: 0 6px; background-color: #FFFFFF; color: #0F172A; }"
        )
        v_occ = QVBoxLayout(occ_box)
        v_occ.setContentsMargins(8, 12, 8, 8)
        self.occ_table = QTableWidget()
        self.occ_table.setColumnCount(4)
        self.occ_table.setHorizontalHeaderLabels(["Bus", "Route", "Date & Time", "Occupancy"])
        self.occ_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.occ_table.verticalHeader().setVisible(False)
        self.occ_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.occ_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.occ_table.setMinimumHeight(240)
        v_occ.addWidget(self.occ_table)
        tables_row.addWidget(occ_box, 1)

        self.layout.addLayout(tables_row)

        scroll.setWidget(container)
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(scroll)

    def refresh_data(self):
        """Re-executes SQL aggregations and redraws dashboard metrics and charts."""
        stats = report_repository.get_dashboard_stats()

        self.cards["active_buses"].setText(str(stats["active_buses"]))
        self.cards["active_routes"].setText(str(stats["active_routes"]))
        self.cards["today_schedules"].setText(str(stats["today_schedules"]))
        self.cards["total_confirmed_bookings"].setText(str(stats["total_confirmed_bookings"]))
        self.cards["today_confirmed_bookings"].setText(str(stats["today_confirmed_bookings"]))
        self.cards["total_revenue"].setText(f"Rs. {float(stats['total_revenue']):,.2f}")

        # Update Recent Bookings Table
        recent = stats.get("recent_bookings", [])
        self.recent_table.setRowCount(len(recent))
        for row_idx, r in enumerate(recent):
            self.recent_table.setItem(row_idx, 0, QTableWidgetItem(r["booking_reference"]))
            self.recent_table.setItem(row_idx, 1, QTableWidgetItem(r["full_name"]))
            self.recent_table.setItem(row_idx, 2, QTableWidgetItem(f"{r['source']} -> {r['destination']}"))
            self.recent_table.setItem(row_idx, 3, QTableWidgetItem(f"Rs. {r['amount']:.2f}"))

        # Update Occupancy Table
        occ = stats.get("high_occupancy_schedules", [])
        self.occ_table.setRowCount(len(occ))
        for row_idx, o in enumerate(occ):
            self.occ_table.setItem(row_idx, 0, QTableWidgetItem(f"{o['bus_number']} ({o['bus_name']})"))
            self.occ_table.setItem(row_idx, 1, QTableWidgetItem(f"{o['source']} -> {o['destination']}"))
            self.occ_table.setItem(row_idx, 2, QTableWidgetItem(f"{o['travel_date']} {o['departure_time']}"))
            self.occ_table.setItem(row_idx, 3, QTableWidgetItem(f"{o['occupancy_rate']}% ({o['confirmed_seats']}/{o['total_seats']})"))

        # Redraw Matplotlib Trend Chart
        self._plot_trend_chart(stats.get("trend_data", []))

    def _plot_trend_chart(self, trend_data):
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        dates = [d["b_date"][-5:] for d in trend_data]  # MM-DD
        revenues = [d["daily_revenue"] for d in trend_data]
        counts = [d["booking_count"] for d in trend_data]

        if not dates:
            ax.text(0.5, 0.5, "No confirmed bookings recorded yet", horizontalalignment='center', verticalalignment='center', transform=ax.transAxes, color='#94A3B8')
            self.canvas.draw()
            return

        x = range(len(dates))
        bars = ax.bar([i - 0.15 for i in x], revenues, width=0.3, label="Revenue (Rs.)", color="#2563EB", alpha=0.85)
        
        ax2 = ax.twinx()
        lines = ax2.plot(list(x), counts, color="#10B981", marker="o", linewidth=2.2, label="Bookings Count")

        ax.set_xticks(list(x))
        ax.set_xticklabels(dates, fontsize=9, color="#475569")
        ax.set_ylabel("Revenue (Rs.)", color="#2563EB", fontsize=10)
        ax2.set_ylabel("Bookings Count", color="#10B981", fontsize=10)
        ax.grid(axis='y', linestyle='--', alpha=0.3)
        ax.set_facecolor('#FAFAFA')

        # Combine legends
        ax.legend(loc="upper left", frameon=False, fontsize=9)
        ax2.legend(loc="upper right", frameon=False, fontsize=9)

        self.figure.tight_layout()
        self.canvas.draw()
