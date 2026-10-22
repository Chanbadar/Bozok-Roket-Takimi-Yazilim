"""
Bozok Roket Takımı - Ana Pencere (Main Window)
Tüm bileşenleri (Header, Roket Verileri, Görev Yükü, Canlı Grafikler, Harita ve Durum Çubuğu) bir araya getirir.
"""

import os
import sys

# core modüllerinin her koşulda import edilebilmesi için telemetry yolunu ekle
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_BASE_DIR = os.path.abspath(os.path.join(_CURRENT_DIR, ".."))
_TELEMETRY_DIR = os.path.join(_BASE_DIR, "telemetry")
if _BASE_DIR not in sys.path:
    sys.path.insert(0, _BASE_DIR)
if _TELEMETRY_DIR not in sys.path:
    sys.path.insert(0, _TELEMETRY_DIR)

from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QHBoxLayout, QMainWindow, QMessageBox, QScrollArea, QSplitter, QVBoxLayout, QWidget
)

from core.data_logger import DataLogger
from core.flight_simulator import FlightSimulator
from core.serial_manager import SerialManager
from core.telemetry_model import RocketTelemetry, PayloadTelemetry
from ui.components.flight_state_widget import FlightStateWidget
from ui.components.header_bar import HeaderBar
from ui.components.map_widget import MapWidget
from ui.components.real_time_charts import RealTimeChartsWidget
from ui.components.telemetry_panel import PayloadTelemetryWidget, RocketTelemetryWidget
from ui.styles import DARK_THEME_QSS


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bozok Roket Takımı - Yer İstasyonu")
        self.resize(1480, 880)
        self.setStyleSheet(DARK_THEME_QSS)

        # Çekirdek Modüller
        self.serial_mgr = SerialManager(data_callback=self._on_telemetry_received)
        self.simulator = FlightSimulator(update_callback=self._on_telemetry_received)
        self.data_logger = DataLogger()

        # Güncel Telemetri
        self.current_rocket = RocketTelemetry()
        self.current_payload = PayloadTelemetry()

        self._init_ui()
        self._setup_timers()
        self._refresh_ports()

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(12, 10, 12, 10)
        root_layout.setSpacing(10)

        # 1. Üst Kontrol Barı
        self.header_bar = HeaderBar()
        self.header_bar.connect_requested.connect(self._handle_connect)
        self.header_bar.disconnect_requested.connect(self._handle_disconnect)
        self.header_bar.simulation_toggle_requested.connect(self._handle_simulation_toggle)
        self.header_bar.record_toggle_requested.connect(self._handle_record_toggle)
        self.header_bar.refresh_ports_btn.clicked.connect(self._refresh_ports)
        root_layout.addWidget(self.header_bar)

        # 2. Uçuş Durum Çubuğu (State Machine)
        self.flight_state_widget = FlightStateWidget()
        root_layout.addWidget(self.flight_state_widget)

        # 3. Ana Çalışma Alanı (Splitter ile Yeniden Boyutlandırılabilir)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setHandleWidth(4)

        # Sol Panel (Roket Verileri)
        rocket_scroll = QScrollArea()
        rocket_scroll.setWidgetResizable(True)
        rocket_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.rocket_panel = RocketTelemetryWidget()
        rocket_scroll.setWidget(self.rocket_panel)
        rocket_scroll.setMinimumWidth(260)
        main_splitter.addWidget(rocket_scroll)

        # Orta Panel (Görev Yükü Verileri)
        payload_scroll = QScrollArea()
        payload_scroll.setWidgetResizable(True)
        payload_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.payload_panel = PayloadTelemetryWidget()
        payload_scroll.setWidget(self.payload_panel)
        payload_scroll.setMinimumWidth(260)
        main_splitter.addWidget(payload_scroll)

        # Sağ Alan (Grafikler + Harita)
        right_splitter = QSplitter(Qt.Orientation.Horizontal)
        right_splitter.setHandleWidth(4)

        # Canlı Grafikler (İrtifa, Hız, Basınç, İvme, Pil)
        self.charts_widget = RealTimeChartsWidget()
        right_splitter.addWidget(self.charts_widget)

        # Canlı Harita
        self.map_widget = MapWidget()
        self.map_widget.setMinimumWidth(320)
        right_splitter.addWidget(self.map_widget)

        # Orantılı boyutlar
        right_splitter.setStretchFactor(0, 3)  # Grafikler daha geniş
        right_splitter.setStretchFactor(1, 2)  # Harita

        main_splitter.addWidget(right_splitter)

        # Ana Panel Oranları (Roket: 1, Görev Yükü: 1, Sağ Alan: 3)
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 1)
        main_splitter.setStretchFactor(2, 4)

        root_layout.addWidget(main_splitter, 1)

    def _setup_timers(self):
        # UI Güncelleme Zamanlayıcısı (30 FPS)
        self.ui_timer = QTimer(self)
        self.ui_timer.setInterval(33)  # ~30 Hz
        self.ui_timer.timeout.connect(self._update_ui_tick)
        self.ui_timer.start()

        # Simülasyon Fizik Güncellemesi (20 Hz)
        self.sim_timer = QTimer(self)
        self.sim_timer.setInterval(50)  # 50 ms = 20 Hz
        self.sim_timer.timeout.connect(self._sim_step)

    def _refresh_ports(self):
        ports = SerialManager.get_available_ports()
        self.header_bar.set_ports(ports)

    def _handle_connect(self, port: str, baud: int):
        if port == "Port Bulunamadı":
            QMessageBox.warning(self, "Port Hatası", "Lütfen geçerli bir seri port seçin.")
            return

        success = self.serial_mgr.connect(port, baud)
        if success:
            self.header_bar.set_connected(True)
        else:
            QMessageBox.critical(self, "Bağlantı Hatası", f"{port} portuna bağlanılamadı.")

    def _handle_disconnect(self):
        self.serial_mgr.disconnect()
        self.header_bar.set_connected(False)

    def _handle_simulation_toggle(self, start: bool):
        if start:
            self.charts_widget.clear()
            self.simulator.reset()
            self.sim_timer.start()
        else:
            self.sim_timer.stop()

    def _sim_step(self):
        self.simulator.update_physics(0.05)

    def _handle_record_toggle(self, start: bool):
        if start:
            fn = self.data_logger.start_logging()
            print(f"[Kayıt Başladı]: {fn}")
        else:
            self.data_logger.stop_logging()
            print("[Kayıt Durduruldu]")

    def _on_telemetry_received(self, r: RocketTelemetry, p: PayloadTelemetry):
        self.current_rocket = r
        self.current_payload = p
        if self.data_logger.is_logging:
            self.data_logger.log_telemetry(r, p)

    def _update_ui_tick(self):
        """Kare hızında arayüzü ve grafikleri günceller."""
        r = self.current_rocket
        p = self.current_payload

        # Kart panellerini güncelle
        self.rocket_panel.update_telemetry(r)
        self.payload_panel.update_telemetry(p)

        # Durum Çubuğunu güncelle
        self.flight_state_widget.set_state(r.flight_state)

        # Grafikleri güncelle
        if r.packet_id > 0:
            self.charts_widget.append_data(r, p)
            self.map_widget.update_gps(r.neo_m9n_lat, r.neo_m9n_lng, p.latitude, p.longitude)

    def closeEvent(self, event):
        """Pencere kapanırken seri port ve kayıtları güvenle kapatır."""
        self.sim_timer.stop()
        self.ui_timer.stop()
        self.serial_mgr.disconnect()
        self.data_logger.stop_logging()
        event.accept()
