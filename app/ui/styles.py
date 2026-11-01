"""
Modern luxury desktop styling and themes for SmartBus BRMS (EasyBus Luxe Edition).
Features deep wine-plum gradient sidebar, top search & profile header bar, vibrant multi-color
gradient KPI cards, rounded pill badges, and clean white card containers.
"""

MAIN_STYLESHEET = """
/* Global Window and Base Typography */
QWidget {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
    color: #1E293B;
}

QMainWindow, QDialog {
    background-color: #F4F5F9;
}

/* -------------------------------------------------------------------------
   Sidebar Navigation (EasyBus Deep Wine-Plum Gradient)
   ------------------------------------------------------------------------- */
#sidebar {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2C0B30, stop:0.45 #220826, stop:1 #140317);
    border: none;
    min-width: 245px;
    max-width: 245px;
}

#sidebarTitle {
    color: #FFFFFF;
    font-size: 18px;
    font-weight: 800;
    padding: 20px 18px 2px 18px;
    letter-spacing: 0.5px;
}

#sidebarSubtitle {
    color: #D1B8D5;
    font-size: 11px;
    font-weight: 500;
    padding: 0px 18px 16px 18px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

#sidebar QPushButton {
    text-align: left;
    padding: 12px 18px;
    font-size: 13px;
    font-weight: 500;
    color: #D1B8D5;
    background-color: transparent;
    border: none;
    border-radius: 12px;
    margin: 2px 12px;
}

#sidebar QPushButton:hover {
    background-color: rgba(255, 255, 255, 0.09);
    color: #FFFFFF;
}

#sidebar QPushButton:checked {
    background-color: #4A154B;
    color: #FFFFFF;
    font-weight: 700;
}

#userRoleBadge {
    background-color: rgba(255, 255, 255, 0.12);
    color: #F3E8FF;
    font-size: 11px;
    font-weight: 600;
    padding: 6px 14px;
    border-radius: 14px;
    margin: 8px 14px;
}

/* Sidebar Promo Upgrade Card (Yellow Coach) */
#promoCard {
    background-color: #FFFFFF;
    border-radius: 14px;
    margin: 10px 14px;
    padding: 12px 10px;
}

#promoTitle {
    color: #111827;
    font-size: 11px;
    font-weight: 800;
    text-align: center;
}

#promoBtn {
    background-color: #2C0B30;
    color: #FFFFFF;
    border-radius: 8px;
    font-weight: 700;
    font-size: 11px;
    padding: 6px 12px;
    border: none;
}
#promoBtn:hover {
    background-color: #4A154B;
}

#logoutBtn {
    text-align: left;
    padding: 10px 16px;
    font-size: 12px;
    font-weight: 600;
    color: #E2D4E5;
    background-color: transparent;
    border: none;
    border-radius: 8px;
    margin: 4px 14px;
}
#logoutBtn:hover {
    background-color: rgba(239, 68, 68, 0.2);
    color: #FCA5A5;
}

/* -------------------------------------------------------------------------
   Top Header Navigation Bar
   ------------------------------------------------------------------------- */
#topHeader {
    background-color: #FFFFFF;
    border-bottom: 1px solid #E5E7EB;
    padding: 12px 24px;
}

#topGreeting {
    font-size: 20px;
    font-weight: 800;
    color: #111827;
}

#topSearchInput {
    background-color: #F3F4F6;
    border: 1px solid #E5E7EB;
    border-radius: 18px;
    padding: 7px 16px;
    font-size: 13px;
    color: #1F2937;
    min-width: 220px;
}
#topSearchInput:focus {
    border: 1.5px solid #2563EB;
    background-color: #FFFFFF;
}

#topArrivalPill {
    background-color: #F3F4F6;
    border: 1px solid #E5E7EB;
    border-radius: 18px;
    padding: 6px 14px;
    color: #4B5563;
    font-weight: 600;
    font-size: 12px;
}

#topProfileChip {
    background-color: #F3F4F6;
    border: 1px solid #E5E7EB;
    border-radius: 18px;
    padding: 4px 12px 4px 6px;
    color: #111827;
    font-weight: 600;
    font-size: 12px;
}

/* -------------------------------------------------------------------------
   Gradient KPI Stat Cards
   ------------------------------------------------------------------------- */
#purpleStatCard {
    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #7C3AED, stop:1 #2563EB);
    border-radius: 16px;
    padding: 16px;
    color: #FFFFFF;
}

#coralStatCard {
    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #F43F5E, stop:1 #FB923C);
    border-radius: 16px;
    padding: 16px;
    color: #FFFFFF;
}

#navyStatCard {
    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #1E1B4B, stop:1 #312E81);
    border-radius: 16px;
    padding: 16px;
    color: #FFFFFF;
}

#violetStatCard {
    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #9333EA, stop:1 #C026D3);
    border-radius: 16px;
    padding: 16px;
    color: #FFFFFF;
}

.gradientStatValue {
    font-size: 26px;
    font-weight: 800;
    color: #FFFFFF;
}

.gradientStatLabel {
    font-size: 12px;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.85);
}

.gradientBadge {
    background-color: rgba(255, 255, 255, 0.22);
    color: #FFFFFF;
    font-size: 11px;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 10px;
}

/* White Container Card */
.Card {
    background-color: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 16px;
    padding: 18px;
}

/* -------------------------------------------------------------------------
   Status Pills & Badges
   ------------------------------------------------------------------------- */
.statusCompleted, .statusOnTime, .statusActive {
    background-color: #ECFDF5;
    color: #059669;
    border: 1px solid #A7F3D0;
    border-radius: 12px;
    padding: 3px 10px;
    font-weight: 700;
    font-size: 11px;
}

.statusPending, .statusDelayed {
    background-color: #FFFBEB;
    color: #D97706;
    border: 1px solid #FDE68A;
    border-radius: 12px;
    padding: 3px 10px;
    font-weight: 700;
    font-size: 11px;
}

.statusCancelled, .statusCanceled, .statusInactive {
    background-color: #FEF2F2;
    color: #DC2626;
    border: 1px solid #FECACA;
    border-radius: 12px;
    padding: 3px 10px;
    font-weight: 700;
    font-size: 11px;
}

.tierPro {
    background-color: #111827;
    color: #FBBF24;
    border-radius: 10px;
    padding: 3px 10px;
    font-weight: 800;
    font-size: 11px;
}

.tierFree {
    background-color: #F3F4F6;
    color: #6B7280;
    border-radius: 10px;
    padding: 3px 10px;
    font-weight: 600;
    font-size: 11px;
}

/* -------------------------------------------------------------------------
   Tables (Clean White Rounded Container)
   ------------------------------------------------------------------------- */
QTableWidget, QTableView {
    background-color: #FFFFFF;
    color: #0F172A;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    gridline-color: #F3F4F6;
    selection-background-color: #F5F3FF;
    selection-color: #4C1D95;
    outline: none;
}

QHeaderView::section {
    background-color: #FAFAFA;
    color: #64748B;
    font-weight: 700;
    font-size: 12px;
    padding: 10px 10px;
    border: none;
    border-bottom: 1px solid #E2E8F0;
}

QTableWidget::item {
    color: #1E293B;
    padding: 8px 10px;
    border-bottom: 1px solid #F1F5F9;
}

QTableWidget::item:selected {
    background-color: #F3E8FF;
    color: #3B0764;
}

/* -------------------------------------------------------------------------
   Form Controls & Buttons
   ------------------------------------------------------------------------- */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
    color: #0F172A;
    min-height: 22px;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus, QTimeEdit:focus {
    border: 2px solid #2563EB;
    background-color: #FFFFFF;
}

QPushButton {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 600;
    color: #334155;
}

QPushButton:hover {
    background-color: #F8FAFC;
    border-color: #94A3B8;
}

QPushButton.primaryButton, #primaryButton {
    background-color: #2563EB;
    border: 1px solid #1D4ED8;
    color: #FFFFFF;
    font-weight: 600;
    border-radius: 8px;
}
QPushButton.primaryButton:hover, #primaryButton:hover {
    background-color: #1D4ED8;
}

QPushButton.pillBtn {
    background-color: #F1F5F9;
    border: 1px solid #E2E8F0;
    color: #475569;
    border-radius: 16px;
    padding: 6px 14px;
    font-weight: 600;
    font-size: 12px;
}
QPushButton.pillBtn:checked, QPushButton.pillBtn:hover {
    background-color: #2563EB;
    color: #FFFFFF;
    border-color: #1D4ED8;
}

/* ScrollBars */
QScrollBar:vertical {
    border: none;
    background: #F1F5F9;
    width: 7px;
    margin: 0px;
    border-radius: 3px;
}
QScrollBar::handle:vertical {
    background: #CBD5E1;
    min-height: 20px;
    border-radius: 3px;
}
QScrollBar::handle:vertical:hover {
    background: #94A3B8;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
