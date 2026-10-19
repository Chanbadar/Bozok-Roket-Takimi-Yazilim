"""
Bozok Roket Takımı - Veri Kaydedici (Data Logger)
Uçuş telemetrisini otomatik olarak zaman damgalı CSV dosyalarına kaydeder.
"""

import csv
from datetime import datetime
import os
from typing import Optional
from core.telemetry_model import RocketTelemetry, PayloadTelemetry


class DataLogger:
    def __init__(self, log_dir: str = "flight_data"):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        self.file_handle = None
        self.writer = None
        self.is_logging = False

    def start_logging(self, prefix: str = "ucus_kaydi") -> str:
        """Yeni bir uçuş kayıt CSV dosyası oluşturur."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.log_dir, f"{prefix}_{timestamp}.csv")
        self.file_handle = open(filename, mode="w", newline="", encoding="utf-8")
        self.writer = csv.writer(self.file_handle)

        # Başlıklar
        headers = [
            "Zaman", "Paket_ID", "Ucus_Suresi",
            "Irtifa_m", "Dusey_Hiz_ms", "DPS368_Basinc_hPa", "BMP390_Basinc_hPa", "Sicaklik_C",
            "Acc_X_g", "Acc_Y_g", "Acc_Z_g", "Gyr_X_ds", "Gyr_Y_ds", "Gyr_Z_ds",
            "NEO_Lat", "NEO_Lng", "NEO_Uydu", "Quectel_Lat", "Quectel_Lng", "Quectel_Uydu",
            "Roket_Pil_V", "Ucus_Durumu",
            "GY_Titresim_Dis", "GY_Titresim_Ic",
            "GY_LSM6_Ext_X", "GY_LSM6_Ext_Y", "GY_LSM6_Ext_Z",
            "GY_Lat", "GY_Lng", "GY_Uydu", "GY_Pil_V"
        ]
        self.writer.writerow(headers)
        self.file_handle.flush()
        self.is_logging = True
        return filename

    def log_telemetry(self, r: RocketTelemetry, p: PayloadTelemetry):
        """Telemetri paketini CSV dosyasına yazar."""
        if not self.is_logging or not self.writer:
            return

        row = [
            datetime.now().strftime("%H:%M:%S.%f")[:-3],
            r.packet_id, round(r.flight_time, 2),
            r.altitude, r.vertical_speed, r.dps368_pressure, r.bmp390_pressure, r.temperature,
            r.acc_x, r.acc_y, r.acc_z, r.gyr_x, r.gyr_y, r.gyr_z,
            r.neo_m9n_lat, r.neo_m9n_lng, r.neo_m9n_satellites,
            r.quectel_lat, r.quectel_lng, r.quectel_satellites,
            r.battery_voltage, r.flight_state,
            p.vibration_ext, p.vibration_int,
            p.lsm6_ext_x, p.lsm6_ext_y, p.lsm6_ext_z,
            p.latitude, p.longitude, p.satellites, p.battery_voltage
        ]
        self.writer.writerow(row)
        self.file_handle.flush()

    def stop_logging(self):
        """Dosyayı güvenli bir şekilde kapatır."""
        self.is_logging = False
        if self.file_handle:
            try:
                self.file_handle.close()
            except Exception:
                pass
            self.file_handle = None
            self.writer = None
