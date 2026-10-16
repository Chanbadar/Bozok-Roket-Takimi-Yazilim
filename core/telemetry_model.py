"""
Bozok Roket Takımı - Telemetri Veri Modeli
Roket ve Görev Yükü sensör verilerini, uçuş durumlarını ve zaman bilgilerini tutar.
"""

from dataclasses import dataclass, field
import time
from typing import Optional


@dataclass
class RocketTelemetry:
    # Zaman ve Paket Bilgileri
    packet_id: int = 0
    flight_time: float = 0.0  # Fırlatmadan itibaren geçen süre (sn)
    timestamp: float = field(default_factory=time.time)

    # İrtifa, Hız ve Basınç Sensörleri
    altitude: float = 0.0          # İrtifa (m)
    max_altitude: float = 0.0      # Ulaşılan maksimum irtifa / Apogee (m)
    vertical_speed: float = 0.0    # Düşey hız (m/s)
    dps368_pressure: float = 1013.25  # DPS368 Basınç (hPa)
    bmp390_pressure: float = 1013.25  # BMP390 Basınç (hPa)
    temperature: float = 24.0      # Sıcaklık (°C)

    # BMI088 İvmeölçer ve Jiroskop
    acc_x: float = 0.0  # g
    acc_y: float = 0.0  # g
    acc_z: float = 1.0  # g
    total_acc: float = 1.0  # sqrt(x^2 + y^2 + z^2)

    gyr_x: float = 0.0  # °/s
    gyr_y: float = 0.0  # °/s
    gyr_z: float = 0.0  # °/s

    # Oryantasyon (Roll, Pitch, Yaw)
    roll: float = 0.0
    pitch: float = 90.0
    yaw: float = 0.0

    # Çift GPS Verileri
    neo_m9n_lat: float = 39.925533
    neo_m9n_lng: float = 32.866287
    neo_m9n_alt: float = 900.0
    neo_m9n_satellites: int = 0
    neo_m9n_status: str = "NO FIX"

    quectel_lat: float = 39.925533
    quectel_lng: float = 32.866287
    quectel_alt: float = 900.0
    quectel_satellites: int = 0
    quectel_status: str = "NO FIX"

    # Pil ve Güç Durumu
    battery_voltage: float = 12.6  # 3S LiPo ~12.6V - 9.9V
    battery_percentage: int = 100

    # Uçuş Durumu (Flight State)
    flight_state: str = "RAMPA_BEKLEME"
    # RAMPA_BEKLEME -> MOTOR_YANISI -> TIRMANMA -> APOGEE -> DROG_PARASUT -> GOREV_YUKU_AYRILMA -> ANA_PARASUT -> KURTARMA


@dataclass
class PayloadTelemetry:
    packet_id: int = 0
    flight_time: float = 0.0
    timestamp: float = field(default_factory=time.time)

    # Titreşim İvmeleri (Dış / İç)
    vibration_ext: float = 0.0  # g
    vibration_int: float = 0.0  # g

    # LSM6 IMU Dış Sensör
    lsm6_ext_x: float = 0.0
    lsm6_ext_y: float = 0.0
    lsm6_ext_z: float = 0.0

    # LSM6 IMU İç Sensör
    lsm6_int_x: float = 0.0
    lsm6_int_y: float = 0.0
    lsm6_int_z: float = 0.0

    # Görev Yükü GPS
    latitude: float = 39.925533
    longitude: float = 32.866287
    altitude: float = 900.0
    satellites: int = 0
    is_separated: bool = False

    # Pil Durumu
    battery_voltage: float = 8.4  # 2S LiPo
    battery_percentage: int = 100
