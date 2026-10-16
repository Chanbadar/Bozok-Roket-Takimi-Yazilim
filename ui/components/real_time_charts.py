"""
Bozok Roket Takımı - Gerçek Zamanlı Grafik Panelleri (PyQtGraph)
İrtifa, Hız, Çift Basınç, İvme ve Pil seviyelerini yüksek kare hızında canlı çizer.
"""

from collections import deque
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget, QVBoxLayout, QWidget
)
import pyqtgraph as pg

from core.telemetry_model import RocketTelemetry, PayloadTelemetry


def setup_plot_style(plot_widget: pg.PlotWidget, title: str, y_label: str, y_units: str):
    """Grafiğe koyu tema, ızgara ve modern havacılık görünümü uygular."""
    plot_widget.setBackground("#0F172A")
    plot_widget.showGrid(x=True, y=True, alpha=0.25)
    plot_widget.setTitle(
        f"<span style='color: #F8FAFC; font-weight: bold; font-size: 11pt;'>{title}</span>"
    )
    plot_widget.setLabel("left", y_label, units=y_units, **{"color": "#94A3B8", "font-size": "9pt"})
    plot_widget.setLabel("bottom", "Uçuş Süresi", units="s", **{"color": "#94A3B8", "font-size": "9pt"})
    plot_widget.getAxis("left").setPen(pg.mkPen(color="#334155", width=1))
    plot_widget.getAxis("bottom").setPen(pg.mkPen(color="#334155", width=1))
    plot_widget.getAxis("left").setTextPen("#94A3B8")
    plot_widget.getAxis("bottom").setTextPen("#94A3B8")


class RealTimeChartsWidget(QFrame):
    """İrtifa, Hız, Basınç, İvme ve Pil gerçek zamanlı grafikleri."""
    def __init__(self, parent=None, max_points: int = 300):
        super().__init__(parent)
        self.max_points = max_points

        # Veri Kuyrukları (Rolling Buffers)
        self.time_data = deque(maxlen=max_points)
        self.alt_data = deque(maxlen=max_points)
        self.speed_data = deque(maxlen=max_points)
        self.dps_press_data = deque(maxlen=max_points)
        self.bmp_press_data = deque(maxlen=max_points)
        self.acc_x_data = deque(maxlen=max_points)
        self.acc_y_data = deque(maxlen=max_points)
        self.acc_z_data = deque(maxlen=max_points)
        self.acc_tot_data = deque(maxlen=max_points)
        self.rocket_batt_data = deque(maxlen=max_points)
        self.payload_batt_data = deque(maxlen=max_points)

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(6)

        # Sekme Yapısı (Tüm Grafikler veya Büyütülmüş Sekmeler)
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        # 1. SEKME: Genel Bakış (2x2 Grid)
        grid_tab = QWidget()
        grid_layout = QGridLayout(grid_tab)
        grid_layout.setContentsMargins(6, 6, 6, 6)
        grid_layout.setSpacing(8)

        # İrtifa Grafiği
        self.alt_plot = pg.PlotWidget()
        setup_plot_style(self.alt_plot, "İRTİFA (ALTITUDE)", "İrtifa", "m")
        self.alt_curve = self.alt_plot.plot(
            pen=pg.mkPen(color="#00F0FF", width=2.2),
            fillLevel=0,
            fillBrush=pg.mkBrush(0, 240, 255, 30)
        )
        grid_layout.addWidget(self.alt_plot, 0, 0)

        # Düşey Hız Grafiği
        self.speed_plot = pg.PlotWidget()
        setup_plot_style(self.speed_plot, "DÜŞEY HIZ (VERTICAL VELOCITY)", "Hız", "m/s")
        self.speed_curve = self.speed_plot.plot(
            pen=pg.mkPen(color="#38BDF8", width=2.0),
            fillLevel=0,
            fillBrush=pg.mkBrush(56, 189, 248, 30)
        )
        grid_layout.addWidget(self.speed_plot, 0, 1)

        # Basınç Grafiği (DPS368 + BMP390)
        self.press_plot = pg.PlotWidget()
        setup_plot_style(self.press_plot, "BASINÇ (DPS368 & BMP390)", "Basınç", "hPa")
        self.press_plot.addLegend(offset=(10, 10))
        self.dps_curve = self.press_plot.plot(name="DPS368", pen=pg.mkPen(color="#4ADE80", width=2.0))
        self.bmp_curve = self.press_plot.plot(name="BMP390", pen=pg.mkPen(color="#FB923C", width=2.0, style=Qt.PenStyle.DashLine))
        grid_layout.addWidget(self.press_plot, 1, 0)

        # İvme Grafiği (AccX, AccY, AccZ)
        self.acc_plot = pg.PlotWidget()
        setup_plot_style(self.acc_plot, "İVME (BMI088)", "İvme", "g")
        self.acc_plot.addLegend(offset=(10, 10))
        self.acc_x_curve = self.acc_plot.plot(name="Acc X", pen=pg.mkPen(color="#E879F9", width=1.5))
        self.acc_y_curve = self.acc_plot.plot(name="Acc Y", pen=pg.mkPen(color="#FACC15", width=1.5))
        self.acc_z_curve = self.acc_plot.plot(name="Acc Z", pen=pg.mkPen(color="#EF4444", width=2.0))
        self.acc_tot_curve = self.acc_plot.plot(name="Bileşke", pen=pg.mkPen(color="#38BDF8", width=2.0, style=Qt.PenStyle.DotLine))
        grid_layout.addWidget(self.acc_plot, 1, 1)

        self.tabs.addTab(grid_tab, "📊 TÜM GRAFİKLER (2x2)")

        # 2. SEKME: Pil & Güç Durumu
        batt_tab = QWidget()
        batt_layout = QVBoxLayout(batt_tab)
        batt_layout.setContentsMargins(6, 6, 6, 6)
        self.batt_plot = pg.PlotWidget()
        setup_plot_style(self.batt_plot, "PİL GERİLİMLERİ (ROKET & GÖREV YÜKÜ)", "Gerilim", "V")
        self.batt_plot.addLegend(offset=(10, 10))
        self.rocket_batt_curve = self.batt_plot.plot(name="Roket Pili (3S)", pen=pg.mkPen(color="#FACC15", width=2.2))
        self.payload_batt_curve = self.batt_plot.plot(name="Görev Yükü (2S)", pen=pg.mkPen(color="#38BDF8", width=2.2))
        batt_layout.addWidget(self.batt_plot)
        self.tabs.addTab(batt_tab, "🔋 PİL GRAFİĞİ")

        main_layout.addWidget(self.tabs)

    def append_data(self, r: RocketTelemetry, p: PayloadTelemetry):
        """Yeni telemetri paketini kuyruklara ekler ve eğrileri günceller."""
        t = r.flight_time
        self.time_data.append(t)
        self.alt_data.append(r.altitude)
        self.speed_data.append(r.vertical_speed)
        self.dps_press_data.append(r.dps368_pressure)
        self.bmp_press_data.append(r.bmp390_pressure)
        self.acc_x_data.append(r.acc_x)
        self.acc_y_data.append(r.acc_y)
        self.acc_z_data.append(r.acc_z)
        self.acc_tot_data.append(r.total_acc)
        self.rocket_batt_data.append(r.battery_voltage)
        self.payload_batt_data.append(p.battery_voltage)

        times = list(self.time_data)

        # Eğrileri güncelle (Hızlı C++ çizimi)
        self.alt_curve.setData(times, list(self.alt_data))
        self.speed_curve.setData(times, list(self.speed_data))
        self.dps_curve.setData(times, list(self.dps_press_data))
        self.bmp_curve.setData(times, list(self.bmp_press_data))

        self.acc_x_curve.setData(times, list(self.acc_x_data))
        self.acc_y_curve.setData(times, list(self.acc_y_data))
        self.acc_z_curve.setData(times, list(self.acc_z_data))
        self.acc_tot_curve.setData(times, list(self.acc_tot_data))

        self.rocket_batt_curve.setData(times, list(self.rocket_batt_data))
        self.payload_batt_curve.setData(times, list(self.payload_batt_data))

    def clear(self):
        """Grafikleri sıfırlar."""
        self.time_data.clear()
        self.alt_data.clear()
        self.speed_data.clear()
        self.dps_press_data.clear()
        self.bmp_press_data.clear()
        self.acc_x_data.clear()
        self.acc_y_data.clear()
        self.acc_z_data.clear()
        self.acc_tot_data.clear()
        self.rocket_batt_data.clear()
        self.payload_batt_data.clear()

        self.alt_curve.setData([], [])
        self.speed_curve.setData([], [])
        self.dps_curve.setData([], [])
        self.bmp_curve.setData([], [])
        self.acc_x_curve.setData([], [])
        self.acc_y_curve.setData([], [])
        self.acc_z_curve.setData([], [])
        self.acc_tot_curve.setData([], [])
        self.rocket_batt_curve.setData([], [])
        self.payload_batt_curve.setData([], [])
