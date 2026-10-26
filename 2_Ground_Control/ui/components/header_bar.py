"""
Bozok Roket Takımı - Üst Kontrol Barı (Header Bar)
Port seçimi, baudrate, bağlantı, simülasyon ve durum göstergelerini içerir.
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QPushButton, QWidget
)


class HeaderBar(QWidget):
    # Sinyaller
    connect_requested = Signal(str, int)     # port, baudrate
    disconnect_requested = Signal()
    simulation_toggle_requested = Signal(bool) # True: Başlat, False: Durdur
    record_toggle_requested = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HeaderBar")
        self.is_connected = False
        self.is_simulating = False
        self.is_recording = False
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)

        # Takım & Uygulama Başlığı
        title_box = QWidget()
        title_layout = QHBoxLayout(title_box)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(8)

        logo_label = QLabel("🚀")
        logo_label.setStyleSheet("font-size: 22px;")
        title_layout.addWidget(logo_label)

        text_box = QWidget()
        text_layout = QHBoxLayout(text_box)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(4)

        app_title = QLabel("BOZOK ROKET TAKIMI")
        app_title.setObjectName("AppTitle")
        sub_title = QLabel("• YER İSTASYONU")
        sub_title.setObjectName("AppSubtitle")
        text_layout.addWidget(app_title)
        text_layout.addWidget(sub_title)
        title_layout.addWidget(text_box)

        layout.addWidget(title_box)
        layout.addStretch(1)

        # Seri Port Seçimi
        port_label = QLabel("PORT:")
        port_label.setStyleSheet("font-weight: 700; color: #94A3B8; font-size: 11px;")
        layout.addWidget(port_label)

        self.port_combo = QComboBox()
        self.port_combo.setToolTip("Alıcı modülün (XBee/LoRa) bağlı olduğu seri port")
        layout.addWidget(self.port_combo)

        # Port Yenile Butonu
        self.refresh_ports_btn = QPushButton("🔄")
        self.refresh_ports_btn.setObjectName("RefreshPortsButton")
        self.refresh_ports_btn.setToolTip("Port listesini yenile")
        self.refresh_ports_btn.setFixedSize(31, 31)
        layout.addWidget(self.refresh_ports_btn)

        # Baudrate Seçimi
        baud_label = QLabel("BAUD:")
        baud_label.setStyleSheet("font-weight: 700; color: #94A3B8; font-size: 11px;")
        layout.addWidget(baud_label)

        self.baud_combo = QComboBox()
        for baud in ["115200", "57600", "38400", "19200", "9600"]:
            self.baud_combo.addItem(baud)
        layout.addWidget(self.baud_combo)

        # Bağlan / Kes Butonu
        self.connect_btn = QPushButton("BAĞLAN")
        self.connect_btn.setObjectName("ConnectButton")
        self.connect_btn.clicked.connect(self._toggle_connection)
        layout.addWidget(self.connect_btn)

        # Simülasyon Butonu
        self.sim_btn = QPushButton("▶ TEST SİMÜLASYONU")
        self.sim_btn.setObjectName("SimulateButton")
        self.sim_btn.setToolTip("Donanım olmadan gerçekçi uçuş simülasyonunu başlat")
        self.sim_btn.clicked.connect(self._toggle_simulation)
        layout.addWidget(self.sim_btn)

        # CSV Kayıt Butonu
        self.record_btn = QPushButton("🔴 KAYIT (CSV)")
        self.record_btn.setStyleSheet("background-color: #1E293B; border: 1px solid #475569;")
        self.record_btn.setToolTip("Uçuş verilerini CSV dosyasına kaydetmeyi başlat/durdur")
        self.record_btn.clicked.connect(self._toggle_recording)
        layout.addWidget(self.record_btn)

        # Hakem İstasyonu Durum Rozeti
        self.referee_badge = QLabel("HAKEM: PASİF")
        self.referee_badge.setStyleSheet(
            "background-color: #1E293B; color: #94A3B8; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 700;"
        )
        layout.addWidget(self.referee_badge)

    def set_ports(self, ports: list):
        current = self.port_combo.currentText()
        self.port_combo.clear()
        if not ports:
            self.port_combo.addItem("Port Bulunamadı")
        else:
            for p in ports:
                self.port_combo.addItem(p)
            idx = self.port_combo.findText(current)
            if idx >= 0:
                self.port_combo.setCurrentIndex(idx)

    def _toggle_connection(self):
        if not self.is_connected:
            port = self.port_combo.currentText()
            baud = int(self.baud_combo.currentText())
            self.connect_requested.emit(port, baud)
        else:
            self.disconnect_requested.emit()

    def set_connected(self, connected: bool):
        self.is_connected = connected
        if connected:
            self.connect_btn.setText("BAĞLANTIYI KES")
            self.connect_btn.setObjectName("DisconnectButton")
            self.port_combo.setEnabled(False)
            self.baud_combo.setEnabled(False)
        else:
            self.connect_btn.setText("BAĞLAN")
            self.connect_btn.setObjectName("ConnectButton")
            self.port_combo.setEnabled(True)
            self.baud_combo.setEnabled(True)
        # Stil güncelle
        self.connect_btn.style().unpolish(self.connect_btn)
        self.connect_btn.style().polish(self.connect_btn)

    def _toggle_simulation(self):
        self.is_simulating = not self.is_simulating
        if self.is_simulating:
            self.sim_btn.setText("⏹ SİMÜLASYONU DURDUR")
            self.sim_btn.setObjectName("SimulateStopButton")
        else:
            self.sim_btn.setText("▶ TEST SİMÜLASYONU")
            self.sim_btn.setObjectName("SimulateButton")
        self.sim_btn.style().unpolish(self.sim_btn)
        self.sim_btn.style().polish(self.sim_btn)
        self.simulation_toggle_requested.emit(self.is_simulating)

    def _toggle_recording(self):
        self.is_recording = not self.is_recording
        if self.is_recording:
            self.record_btn.setText("⏹ KAYIT DURDUR")
            self.record_btn.setStyleSheet("background-color: #991B1B; border: 1px solid #EF4444; color: white;")
        else:
            self.record_btn.setText("🔴 KAYIT (CSV)")
            self.record_btn.setStyleSheet("background-color: #1E293B; border: 1px solid #475569; color: white;")
        self.record_toggle_requested.emit(self.is_recording)
