"""
Bozok Roket Takımı - Seri Port İletişim Yöneticisi
XBee / LoRa / RFD900 veya USB Seri port üzerinden telemetri okur ve ayrıştırır.
"""

import math
import re
import threading
import time
from typing import Callable, List, Optional
import serial
import serial.tools.list_ports

from core.telemetry_model import RocketTelemetry, PayloadTelemetry


class SerialManager:
    def __init__(self, data_callback: Optional[Callable[[RocketTelemetry, PayloadTelemetry], None]] = None):
        self.data_callback = data_callback
        self.serial_port: Optional[serial.Serial] = None
        self.is_connected = False
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.start_time: Optional[float] = None

        self.rocket_data = RocketTelemetry()
        self.payload_data = PayloadTelemetry()

    @staticmethod
    def get_available_ports() -> List[str]:
        """Kullanılabilir COM portlarını listeler."""
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def connect(self, port_name: str, baudrate: int = 115200) -> bool:
        """Seri porta bağlanır ve okuma thread'ini başlatır."""
        try:
            self.serial_port = serial.Serial(port=port_name, baudrate=baudrate, timeout=1.0)
            self.is_connected = True
            self.is_running = True
            self.start_time = time.time()
            self.rocket_data.flight_time = 0.0
            self.thread = threading.Thread(target=self._read_loop, daemon=True)
            self.thread.start()
            print(f"[Seri Port] {port_name} ({baudrate} baud) başarıyla bağlandı.")
            return True
        except Exception as e:
            print(f"[Seri Port Hatası] {port_name} bağlanamadı: {e}")
            self.is_connected = False
            return False

    def disconnect(self):
        """Seri port bağlantısını keser."""
        self.is_running = False
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.close()
            except Exception:
                pass
        self.is_connected = False
        self.start_time = None
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        print("[Seri Port] Bağlantı kesildi.")

    def _read_loop(self):
        """Sürekli gelen telemetri satırlarını okur."""
        buffer = ""
        while self.is_running and self.serial_port and self.serial_port.is_open:
            try:
                raw_bytes = self.serial_port.readline()
                if raw_bytes:
                    line = raw_bytes.decode("utf-8", errors="ignore").strip()
                    if line:
                        self._parse_line(line)
            except Exception as e:
                print(f"[Seri Port Okuma Hatası]: {e}")
                time.sleep(0.1)

    def _parse_line(self, line: str):
        """
        Gelen satırı ayrıştırır.
        1. GY-85 veya benzeri test formatı:
           't=13032 ms | A(g): -0.019 -0.055 0.749 | toplam=0.751 | G(dps): nan nan nan'
           (virgüllü veya boşluklu)
        2. Standart TEKNOFEST virgülle ayrılmış paket formatı (>=15 eleman)
        3. 3 veya 6 elemanlı basit CSV ivme/gyro verisi
        """
        try:
            if self.start_time is None:
                self.start_time = time.time()

            # Zaman damgası takibi: Satırda t=... ms varsa onu al, yoksa geçen süreyi hesapla
            t_match = re.search(r"t=(\d+)\s*ms", line)
            if t_match:
                self.rocket_data.flight_time = round(int(t_match.group(1)) / 1000.0, 3)
            else:
                self.rocket_data.flight_time = round(time.time() - self.start_time, 2)

            self.rocket_data.timestamp = time.time()

            # 1. GY-85 / İvmeölçer Etiketli Format Kontrolü (Virgül veya boşluk ayrımını destekler)
            if "A(g):" in line or "A:" in line:
                a_match = re.search(r"A(?:\(g\))?:\s*([-\d.]+)[,\s]+([-\d.]+)[,\s]+([-\d.]+)", line)
                if a_match:
                    self.rocket_data.acc_x = float(a_match.group(1))
                    self.rocket_data.acc_y = float(a_match.group(2))
                    self.rocket_data.acc_z = float(a_match.group(3))
                    self.rocket_data.total_acc = math.sqrt(
                        self.rocket_data.acc_x ** 2 +
                        self.rocket_data.acc_y ** 2 +
                        self.rocket_data.acc_z ** 2
                    )

                g_match = re.search(r"G(?:\(dps\))?:\s*([-\d.nanNAN]+)[,\s]+([-\d.nanNAN]+)[,\s]+([-\d.nanNAN]+)", line)
                if g_match:
                    val_x = g_match.group(1).lower()
                    val_y = g_match.group(2).lower()
                    val_z = g_match.group(3).lower()
                    self.rocket_data.gyr_x = 0.0 if "nan" in val_x else float(val_x)
                    self.rocket_data.gyr_y = 0.0 if "nan" in val_y else float(val_y)
                    self.rocket_data.gyr_z = 0.0 if "nan" in val_z else float(val_z)

                self.rocket_data.packet_id += 1
                if self.data_callback:
                    self.data_callback(self.rocket_data, self.payload_data)
                return

            # 2. Virgülle Ayrılmış Formatlar
            parts = [p.strip() for p in line.split(",") if p.strip()]
            if len(parts) >= 15:
                self.rocket_data.packet_id = int(parts[0]) if parts[0].isdigit() else self.rocket_data.packet_id + 1
                self.rocket_data.altitude = float(parts[1])
                self.rocket_data.vertical_speed = float(parts[2])
                self.rocket_data.dps368_pressure = float(parts[3])
                self.rocket_data.bmp390_pressure = float(parts[4])
                self.rocket_data.acc_x = float(parts[5])
                self.rocket_data.acc_y = float(parts[6])
                self.rocket_data.acc_z = float(parts[7])
                self.rocket_data.total_acc = math.sqrt(
                    self.rocket_data.acc_x ** 2 + self.rocket_data.acc_y ** 2 + self.rocket_data.acc_z ** 2
                )
                self.rocket_data.gyr_x = float(parts[8])
                self.rocket_data.gyr_y = float(parts[9])
                self.rocket_data.gyr_z = float(parts[10])
                self.rocket_data.neo_m9n_lat = float(parts[11])
                self.rocket_data.neo_m9n_lng = float(parts[12])
                self.rocket_data.neo_m9n_satellites = int(parts[13])
                self.rocket_data.battery_voltage = float(parts[14])
                if len(parts) > 15:
                    self.rocket_data.flight_state = parts[15]

                if self.data_callback:
                    self.data_callback(self.rocket_data, self.payload_data)
            elif 3 <= len(parts) < 15:
                # Basit ivme / gyro formatı: acc_x, acc_y, acc_z (, gyr_x, gyr_y, gyr_z)
                self.rocket_data.acc_x = float(parts[0])
                self.rocket_data.acc_y = float(parts[1])
                self.rocket_data.acc_z = float(parts[2])
                self.rocket_data.total_acc = math.sqrt(
                    self.rocket_data.acc_x ** 2 + self.rocket_data.acc_y ** 2 + self.rocket_data.acc_z ** 2
                )
                if len(parts) >= 6:
                    self.rocket_data.gyr_x = float(parts[3])
                    self.rocket_data.gyr_y = float(parts[4])
                    self.rocket_data.gyr_z = float(parts[5])
                self.rocket_data.packet_id += 1
                if self.data_callback:
                    self.data_callback(self.rocket_data, self.payload_data)
        except Exception as err:
            print(f"[Telemetri Ayrıştırma Uyarısı]: {err} | Satır: '{line}'")
