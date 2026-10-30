"""
Modern desktop styling and themes for Smart Bus Reservation System.
Professional Windows business aesthetic with neutral tones and royal blue accent.
"""

MAIN_STYLESHEET = """
/* Global Window and Font Settings */
QWidget {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
    color: #1E293B;
}

QMainWindow, QDialog {
    background-color: #F8FAFC;
}

/* Sidebar Navigation */
#sidebar {
    background-color: #0F172A;
    border-right: 1px solid #1E293B;
    min-width: 230px;
    max-width: 230px;
}

#sidebarTitle {
    color: #FFFFFF;
    font-size: 17px;
    font-weight: 700;
    padding: 16px 14px 4px 14px;
}

#sidebarSubtitle {
    color: #94A3B8;
    font-size: 11px;
    font-weight: 500;
    padding: 0px 14px 16px 14px;
    border-bottom: 1px solid #1E293B;
}

#sidebar QPushButton {
    text-align: left;
    padding: 11px 16px;
    font-size: 13px;
    font-weight: 500;
    color: #CBD5E1;
    background-color: transparent;
    border: none;
    border-radius: 6px;
    margin: 2px 10px;
}

#sidebar QPushButton:hover {
    background-color: #1E293B;
    color: #FFFFFF;
}

#sidebar QPushButton:checked {
    background-color: #2563EB;
    color: #FFFFFF;
    font-weight: 600;
}

#userRoleBadge {
    background-color: #1E293B;
    color: #38BDF8;
    font-size: 11px;
    font-weight: 600;
    padding: 6px 12px;
    border-radius: 12px;
    margin: 8px 12px;
}

/* Top Header Bar */
#topHeader {
    background-color: #FFFFFF;
    border-bottom: 1px solid #E2E8F0;
    padding: 10px 24px;
}

#pageTitle {
    font-size: 20px;
    font-weight: 700;
    color: #0F172A;
}

#pageDescription {
    font-size: 12px;
    color: #64748B;
}

/* Cards and Panels */
.Card {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 16px;
}

#statCard {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 16px;
}

#statValue {
    font-size: 26px;
    font-weight: 700;
    color: #0F172A;
}

#statLabel {
    font-size: 12px;
    font-weight: 600;
    color: #64748B;
    text-transform: uppercase;
}

/* Form Controls */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    color: #0F172A;
    min-height: 20px;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus, QTimeEdit:focus {
    border: 2px solid #2563EB;
    background-color: #FFFFFF;
}

QLineEdit:disabled, QComboBox:disabled {
    background-color: #F1F5F9;
    color: #94A3B8;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QLabel {
    color: #334155;
}

QLabel.formLabel {
    font-weight: 600;
    color: #334155;
    margin-bottom: 2px;
}

/* Buttons */
QPushButton {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 600;
    color: #334155;
}

QPushButton:hover {
    background-color: #F8FAFC;
    border-color: #94A3B8;
}

QPushButton:pressed {
    background-color: #E2E8F0;
}

QPushButton:disabled {
    background-color: #F1F5F9;
    border-color: #E2E8F0;
    color: #94A3B8;
}

/* Primary Button */
QPushButton.primaryButton, #primaryButton {
    background-color: #2563EB;
    border: 1px solid #1D4ED8;
    color: #FFFFFF;
    font-weight: 600;
}

QPushButton.primaryButton:hover, #primaryButton:hover {
    background-color: #1D4ED8;
}

QPushButton.primaryButton:pressed, #primaryButton:pressed {
    background-color: #1E40AF;
}

QPushButton.primaryButton:disabled, #primaryButton:disabled {
    background-color: #E2E8F0;
    border: 1px solid #CBD5E1;
    color: #94A3B8;
}

/* Success Button */
QPushButton.successButton, #successButton {
    background-color: #10B981;
    border: 1px solid #059669;
    color: #FFFFFF;
}

QPushButton.successButton:hover, #successButton:hover {
    background-color: #059669;
}

/* Danger Button */
QPushButton.dangerButton, #dangerButton {
    background-color: #EF4444;
    border: 1px solid #DC2626;
    color: #FFFFFF;
}

QPushButton.dangerButton:hover, #dangerButton:hover {
    background-color: #DC2626;
}

/* Table View */
QTableWidget, QTableView {
    background-color: #FFFFFF;
    color: #0F172A;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    gridline-color: #F1F5F9;
    selection-background-color: #EFF6FF;
    selection-color: #1E3A8A;
    outline: none;
}

QHeaderView::section {
    background-color: #F8FAFC;
    color: #334155;
    font-weight: 700;
    font-size: 12px;
    padding: 10px 8px;
    border: none;
    border-bottom: 2px solid #CBD5E1;
}

QTableWidget::item {
    color: #0F172A;
    padding: 8px;
    border-bottom: 1px solid #F1F5F9;
}

QTableWidget::item:selected {
    background-color: #DBEAFE;
    color: #1E40AF;
}

/* GroupBox styling */
QGroupBox {
    font-weight: 700;
    font-size: 14px;
    color: #0F172A;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    margin-top: 18px;
    padding-top: 14px;
    background-color: #FFFFFF;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 2px 8px;
    background-color: #FFFFFF;
    color: #0F172A;
}

/* ScrollBars */
QScrollBar:vertical {
    border: none;
    background: #F1F5F9;
    width: 8px;
    margin: 0px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #CBD5E1;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #94A3B8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Status Badges */
QLabel.statusConfirmed {
    background-color: #DCFCE7;
    color: #15803D;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 12px;
    border: 1px solid #86EFAC;
}

QLabel.statusCancelled {
    background-color: #FEE2E2;
    color: #B91C1C;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 12px;
    border: 1px solid #FCA5A5;
}

QLabel.statusScheduled {
    background-color: #DBEAFE;
    color: #1D4ED8;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 12px;
    border: 1px solid #93C5FD;
}
"""
