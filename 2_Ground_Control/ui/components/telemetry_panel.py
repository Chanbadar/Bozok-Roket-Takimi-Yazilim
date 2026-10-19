"""
Bozok Roket Takımı - Telemetri Bilgi Panelleri
Kullanıcının gönderdiği fotoğraflardaki "ROKET VERİLERİ" ve "GÖREV YÜKÜ VERİLERİ" tasarımına tam sadık kalınarak oluşturulmuştur.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QProgressBar, QVBoxLayout, QWidget
)

from core.telemetry_model import RocketTelemetry, PayloadTelemetry


def create_data_row(label_text: str, default_val: str = "--") -> tuple[QWidget, QLabel]:
    """Fotoğraftaki gibi başlık üstte, veri altta kutulu satır bileşeni üretir."""
    container = QWidget()
    vbox = QVBoxLayout(container)
    vbox.setContentsMargins(0, 3, 0, 3)
    vbox.setSpacing(2)

    lbl = QLabel(label_text)
    lbl.setProperty("class", "DataFieldLabel")
    lbl.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")

    val = QLabel(default_val)
    val.setProperty("class", "DataFieldValue")
    val.setAlignment(Qt.AlignmentFlag.AlignCenter)
    val.setStyleSheet(
        "background-color: #111A2E; color: #F8FAFC; border: 1px solid #1E293B; "
        "border-radius: 5px; padding: 4px 6px; font-family: 'Consolas', monospace; font-size: 12px; font-weight: 700;"
    )

    vbox.addWidget(lbl)
    vbox.addWidget(val)
    return container, val


class RocketTelemetryWidget(QFrame):
    """Sol Kolon: ROKET VERİLERİ"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "TeleCard")
        self.setObjectName("RocketPanel")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        # Başlık (Fotoğraftaki gibi Turkuaz / Cyan renkte)
        title_box = QHBoxLayout()
        icon_lbl = QLabel("🚀")
        icon_lbl.setStyleSheet("font-size: 18px;")
        title_lbl = QLabel("ROKET VERİLERİ")
        title_lbl.setObjectName("RocketTitle")
        title_lbl.setStyleSheet("color: #00F0FF; font-size: 15px; font-weight: 800; letter-spacing: 1px;")
        title_box.addWidget(icon_lbl)
        title_box.addWidget(title_lbl)
        title_box.addStretch()
        layout.addLayout(title_box)

        # Hızlı Özet (İrtifa & Hız Rozetleri)
        summary_grid = QGridLayout()
        summary_grid.setContentsMargins(0, 4, 0, 8)
        summary_grid.setHorizontalSpacing(8)

        self.w_alt, self.val_alt = create_data_row("İRTİFA (m)", "0.0 m")
        self.val_alt.setStyleSheet(self.val_alt.styleSheet() + " color: #38BDF8; font-size: 15px;")
        self.w_speed, self.val_speed = create_data_row("DÜŞEY HIZ (m/s)", "0.0 m/s")
        self.val_speed.setStyleSheet(self.val_speed.styleSheet() + " color: #38BDF8; font-size: 15px;")

        summary_grid.addWidget(self.w_alt, 0, 0)
        summary_grid.addWidget(self.w_speed, 0, 1)
        layout.addLayout(summary_grid)

        # Basınç Sensörleri
        self.w_dps, self.val_dps = create_data_row("DPS368 BASINÇ", "-- hPa")
        self.w_bmp, self.val_bmp = create_data_row("BMP390 BASINÇ", "-- hPa")
        layout.addWidget(self.w_dps)
        layout.addWidget(self.w_bmp)

        # İvme ve Jiroskop (Fotoğraftaki gibi)
        self.w_acc, self.val_acc = create_data_row("BMI088 İVME (AccX | AccY | AccZ)", "0.00 | 0.00 | 1.00 g")
        self.w_gyr, self.val_gyr = create_data_row("BMI088 JİROSKOP (GyrX | GyrY | GyrZ)", "0.0 | 0.0 | 0.0 °/s")
        layout.addWidget(self.w_acc)
        layout.addWidget(self.w_gyr)

        # Çift GPS Verileri
        self.w_neo_gps, self.val_neo_gps = create_data_row("NEO M9N GPS (Lat, Lng)", "-- , --")
        self.w_neo_stat, self.val_neo_stat = create_data_row("NEO M9N UYDU DURUMU", "NO FIX")
        self.val_neo_stat.setStyleSheet(self.val_neo_stat.styleSheet() + " color: #4ADE80;")

        self.w_quec_gps, self.val_quec_gps = create_data_row("QUECTEL GPS (Lat, Lng)", "-- , --")
        self.w_quec_stat, self.val_quec_stat = create_data_row("QUECTEL UYDU DURUMU", "NO FIX")
        self.val_quec_stat.setStyleSheet(self.val_quec_stat.styleSheet() + " color: #4ADE80;")

        layout.addWidget(self.w_neo_gps)
        layout.addWidget(self.w_neo_stat)
        layout.addWidget(self.w_quec_gps)
        layout.addWidget(self.w_quec_stat)

        # Pil ve Sıcaklık
        batt_box = QHBoxLayout()
        self.w_batt, self.val_batt = create_data_row("ROKET PİLİ", "12.6V (%100)")
        self.val_batt.setStyleSheet(self.val_batt.styleSheet() + " color: #FACC15;")
        self.w_temp, self.val_temp = create_data_row("SICAKLIK", "24.0 °C")
        batt_box.addWidget(self.w_batt)
        batt_box.addWidget(self.w_temp)
        layout.addLayout(batt_box)

        layout.addStretch()

    def update_telemetry(self, data: RocketTelemetry):
        self.val_alt.setText(f"{data.altitude:.1f} m (Maks: {data.max_altitude:.1f})")
        self.val_speed.setText(f"{data.vertical_speed:+.1f} m/s")
        self.val_dps.setText(f"{data.dps368_pressure:.2f} hPa")
        self.val_bmp.setText(f"{data.bmp390_pressure:.2f} hPa")
        self.val_acc.setText(f"{data.acc_x:.2f} | {data.acc_y:.2f} | {data.acc_z:.2f} g")
        self.val_gyr.setText(f"{data.gyr_x:.1f} | {data.gyr_y:.1f} | {data.gyr_z:.1f} °/s")
        self.val_neo_gps.setText(f"{data.neo_m9n_lat:.5f} | {data.neo_m9n_lng:.5f}")
        self.val_neo_stat.setText(data.neo_m9n_status)
        self.val_quec_gps.setText(f"{data.quectel_lat:.5f} | {data.quectel_lng:.5f}")
        self.val_quec_stat.setText(data.quectel_status)
        self.val_batt.setText(f"{data.battery_voltage:.2f}V (%{data.battery_percentage})")
        self.val_temp.setText(f"{data.temperature:.1f} °C")


class PayloadTelemetryWidget(QFrame):
    """Orta Kolon: GÖREV YÜKÜ VERİLERİ"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "TeleCard")
        self.setObjectName("PayloadPanel")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        # Başlık (Fotoğraftaki gibi Turuncu / Kırmızı renkte)
        title_box = QHBoxLayout()
        icon_lbl = QLabel("📦")
        icon_lbl.setStyleSheet("font-size: 18px;")
        title_lbl = QLabel("GÖREV YÜKÜ VERİLERİ")
        title_lbl.setObjectName("PayloadTitle")
        title_lbl.setStyleSheet("color: #FF6B4A; font-size: 15px; font-weight: 800; letter-spacing: 1px;")
        title_box.addWidget(icon_lbl)
        title_box.addWidget(title_lbl)
        title_box.addStretch()
        layout.addLayout(title_box)

        # Ayrılma Durum Rozeti
        self.sep_badge = QLabel("DURUM: ROKET İÇİNDE (AYRILMADI)")
        self.sep_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sep_badge.setStyleSheet(
            "background-color: #1E293B; color: #F59E0B; padding: 6px; border-radius: 5px; font-weight: 800; font-size: 11px;"
        )
        layout.addWidget(self.sep_badge)

        # Titreşim İvmeleri (Fotoğraftaki gibi: DIŞ: 0.00 g | İÇ: 0.01 g)
        self.w_vib, self.val_vib = create_data_row("TİTREŞİM İVMELERİ (DIŞ | İÇ)", "DIŞ: 0.00 g | İÇ: 0.00 g")
        self.val_vib.setStyleSheet(self.val_vib.styleSheet() + " color: #4ADE80; font-size: 13px;")
        layout.addWidget(self.w_vib)

        # LSM6 Dış Sensör
        self.w_lsm_ext, self.val_lsm_ext = create_data_row("LSM6-DIŞ (X | Y | Z)", "X: 0.00 | Y: 0.00 | Z: 0.00")
        self.val_lsm_ext.setStyleSheet(self.val_lsm_ext.styleSheet() + " color: #FB923C;")
        layout.addWidget(self.w_lsm_ext)

        # LSM6 İç Sensör
        self.w_lsm_int, self.val_lsm_int = create_data_row("LSM6-İÇ (X | Y | Z)", "X: 0.00 | Y: 0.00 | Z: 0.00")
        self.val_lsm_int.setStyleSheet(self.val_lsm_int.styleSheet() + " color: #38BDF8;")
        layout.addWidget(self.w_lsm_int)

        # GPS Konumu
        self.w_gps, self.val_gps = create_data_row("GPS KONUMU (Lat, Lng)", "Lat: -- | Lng: --")
        self.val_gps.setStyleSheet(self.val_gps.styleSheet() + " color: #E879F9;")
        layout.addWidget(self.w_gps)

        # Bağlı Uydu Sayısı
        self.w_sat, self.val_sat = create_data_row("BAĞLI UYDU SAYISI", "Bağlı Uydu: 0")
        self.val_sat.setStyleSheet(self.val_sat.styleSheet() + " color: #38BDF8;")
        layout.addWidget(self.w_sat)

        # Görev Yükü Pili
        self.w_batt, self.val_batt = create_data_row("GÖREV YÜKÜ PİLİ", "8.4V (%100)")
        self.val_batt.setStyleSheet(self.val_batt.styleSheet() + " color: #FACC15;")
        layout.addWidget(self.w_batt)

        layout.addStretch()

    def update_telemetry(self, data: PayloadTelemetry):
        self.val_vib.setText(f"DIŞ: {data.vibration_ext:.2f} g | İÇ: {data.vibration_int:.2f} g")
        self.val_lsm_ext.setText(f"X: {data.lsm6_ext_x:+.2f} | Y: {data.lsm6_ext_y:+.2f} | Z: {data.lsm6_ext_z:+.2f}")
        self.val_lsm_int.setText(f"X: {data.lsm6_int_x:+.2f} | Y: {data.lsm6_int_y:+.2f} | Z: {data.lsm6_int_z:+.2f}")
        self.val_gps.setText(f"Lat: {data.latitude:.5f} | Lng: {data.longitude:.5f}")
        self.val_sat.setText(f"Bağlı Uydu: {data.satellites}")
        self.val_batt.setText(f"{data.battery_voltage:.2f}V (%{data.battery_percentage})")

        if data.is_separated:
            self.sep_badge.setText("DURUM: GÖREV YÜKÜ AYRILDI ✅")
            self.sep_badge.setStyleSheet(
                "background-color: #14532D; color: #4ADE80; padding: 6px; border-radius: 5px; font-weight: 800; font-size: 11px;"
            )
        else:
            self.sep_badge.setText("DURUM: ROKET İÇİNDE (AYRILMADI)")
            self.sep_badge.setStyleSheet(
                "background-color: #1E293B; color: #F59E0B; padding: 6px; border-radius: 5px; font-weight: 800; font-size: 11px;"
            )
