"""
Bozok Roket Takımı - Koyu Havacılık & Uzay Arayüz Teması (QSS)
"""

DARK_THEME_QSS = """
QMainWindow {
    background-color: #080D1A;
    color: #F8FAFC;
    font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif;
}

QWidget {
    color: #F8FAFC;
    font-size: 13px;
}

/* Üst Kontrol Barı */
#HeaderBar {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0F172A, stop:0.5 #131F37, stop:1 #0F172A);
    border-bottom: 1px solid #1E293B;
    padding: 8px 16px;
}

#AppTitle {
    font-size: 18px;
    font-weight: 800;
    letter-spacing: 1.5px;
    color: #38BDF8;
}

#AppSubtitle {
    font-size: 11px;
    font-weight: 600;
    color: #94A3B8;
    letter-spacing: 0.5px;
}

/* Kart Panelleri */
.TeleCard {
    background-color: #0F172A;
    border: 1px solid #1E293B;
    border-radius: 10px;
    padding: 12px;
}

.TeleCard:hover {
    border: 1px solid #334155;
}

/* Başlıklar */
#RocketTitle {
    font-size: 15px;
    font-weight: 800;
    color: #00F0FF;
    letter-spacing: 1px;
}

#PayloadTitle {
    font-size: 15px;
    font-weight: 800;
    color: #FF6B4A;
    letter-spacing: 1px;
}

#SectionHeader {
    font-size: 11px;
    font-weight: 700;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 6px;
}

/* Veri Alanları */
.DataFieldLabel {
    color: #94A3B8;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
}

.DataFieldValue {
    color: #F1F5F9;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 13px;
    font-weight: 700;
    background-color: #131C31;
    border: 1px solid #1E293B;
    border-radius: 5px;
    padding: 4px 8px;
}

.ValueHighlightCyan {
    color: #38BDF8;
}

.ValueHighlightOrange {
    color: #FB923C;
}

.ValueHighlightGreen {
    color: #4ADE80;
}

.ValueHighlightYellow {
    color: #FACC15;
}

/* Butonlar */
QPushButton {
    background-color: #1E293B;
    color: #F8FAFC;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 600;
    font-size: 12px;
}

QPushButton:hover {
    background-color: #2E3D56;
    border-color: #475569;
}

QPushButton:pressed {
    background-color: #0F172A;
}

#ConnectButton {
    background-color: #0284C7;
    border: 1px solid #38BDF8;
    color: #FFFFFF;
}

#ConnectButton:hover {
    background-color: #0369A1;
}

#DisconnectButton {
    background-color: #991B1B;
    border: 1px solid #EF4444;
    color: #FFFFFF;
}

#SimulateButton {
    background-color: #15803D;
    border: 1px solid #22C55E;
    color: #FFFFFF;
}

#SimulateButton:hover {
    background-color: #166534;
}

#SimulateStopButton {
    background-color: #B45309;
    border: 1px solid #F59E0B;
    color: #FFFFFF;
}

#RefreshPortsButton {
    padding: 0;
    font-size: 13px;
}

#RefreshPortsButton:hover {
    background-color: #2E3D56;
    border-color: #0284C7;
}

/* Seçim Kutuları (ComboBox) */
QComboBox {
    background-color: #0F172A;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 5px 12px;
    color: #F8FAFC;
    font-weight: 600;
    min-width: 120px;
}

QComboBox:hover {
    border-color: #0284C7;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox QAbstractItemView {
    background-color: #0F172A;
    color: #F8FAFC;
    selection-background-color: #0284C7;
    border: 1px solid #334155;
}

/* Sekmeler (TabWidget) */
QTabWidget::pane {
    border: 1px solid #1E293B;
    border-radius: 8px;
    background-color: #080D1A;
}

QTabBar::tab {
    background-color: #0F172A;
    color: #94A3B8;
    border: 1px solid #1E293B;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 8px 18px;
    font-weight: 700;
    margin-right: 4px;
}

QTabBar::tab:selected {
    background-color: #1E293B;
    color: #38BDF8;
    border-bottom: 2px solid #38BDF8;
}

QTabBar::tab:hover:!selected {
    background-color: #162032;
    color: #F1F5F9;
}

/* Durum Rozeti (Badge) */
.StatusBadge {
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.5px;
}

/* ScrollBar */
QScrollBar:vertical {
    border: none;
    background: #080D1A;
    width: 8px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #334155;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #475569;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
