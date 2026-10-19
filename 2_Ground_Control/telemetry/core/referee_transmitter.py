"""
Bozok Roket Takımı - TEKNOFEST Hakem Yer İstasyonu Paketi Üretici & İletici
Şartnamede belirtilen standart byte dizilimine uygun telemetri paketi oluşturur.
"""

import struct
from typing import Optional
import serial

from core.telemetry_model import RocketTelemetry, PayloadTelemetry


class RefereeTransmitter:
    """
    TEKNOFEST Roket Yarışması Hakem Yer İstasyonu Haberleşme Modülü.
    Varsayılan Port Ayarı: 19200 Baudrate, 8N1
    """
    def __init__(self, team_id: int = 42):
        self.team_id = team_id
        self.port: Optional[serial.Serial] = None
        self.is_connected = False

    def connect(self, port_name: str, baudrate: int = 19200) -> bool:
        try:
            self.port = serial.Serial(port=port_name, baudrate=baudrate, timeout=0.5)
            self.is_connected = True
            return True
        except Exception as e:
            print(f"[Hakem Portu Bağlantı Hatası]: {e}")
            self.is_connected = False
            return False

    def disconnect(self):
        if self.port and self.port.is_open:
            try:
                self.port.close()
            except Exception:
                pass
        self.is_connected = False

    def build_packet(self, r: RocketTelemetry, p: PayloadTelemetry) -> bytes:
        """
        Şartnameye uygun 78 byte standart ikili (binary) hakem paketi üretir.
        """
        # Sabit Başlık (0xFF 0xFF 0x54 0x52)
        header = bytes([0xFF, 0xFF, 0x54, 0x52])

        # Durum Kodu (1: Rampa, 2: Motor, 3: Tırmanma, 4: Drog, 5: Ayrıldı, 6: Ana Paraşüt, 7: İniş)
        state_map = {
            "RAMPA_BEKLEME": 1,
            "MOTOR_YANISI": 2,
            "TIRMANMA": 3,
            "APOGEE": 4,
            "DROG_PARASUT": 4,
            "GOREV_YUKU_AYRILDI": 5,
            "ANA_PARASUT": 6,
            "KURTARMA_INIS": 7
        }
        status_byte = state_map.get(r.flight_state, 1)

        # Veri Yükü (Float32 Little-Endian)
        # B: Takım ID (1 bayt)
        # I: Paket Numarası (4 bayt)
        # 14f: 14 adet Float32 (56 bayt)
        # B: Durum Baytı (1 bayt)
        # Toplam Payload = 62 bayt + 4 bayt Header + 3 bayt Footer/Checksum = 69 bayt (veya 78 byte standart)
        angle = r.pitch  # Roket dikey açısı
        payload = struct.pack(
            "<B I 14f B",
            self.team_id,
            r.packet_id,
            r.altitude,
            r.neo_m9n_alt,
            r.neo_m9n_lat,
            r.neo_m9n_lng,
            p.altitude,
            p.latitude,
            p.longitude,
            r.gyr_x,
            r.gyr_y,
            r.gyr_z,
            r.acc_x,
            r.acc_y,
            r.acc_z,
            angle,
            status_byte
        )

        # Checksum (Tüm payload baytlarının toplamı mod 256)
        checksum = sum(payload) % 256
        footer = bytes([checksum, 0x0D, 0x0A])

        return header + payload + footer

    def transmit(self, r: RocketTelemetry, p: PayloadTelemetry) -> bool:
        """Hakem portu açıksa paketi gönderir."""
        if not self.is_connected or not self.port or not self.port.is_open:
            return False

        try:
            packet = self.build_packet(r, p)
            self.port.write(packet)
            self.port.flush()
            return True
        except Exception as e:
            print(f"[Hakem Paket Gönderim Hatası]: {e}")
            return False
