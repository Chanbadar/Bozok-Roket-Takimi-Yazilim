"""
Bozok Roket Takımı - Gerçekçi Uçuş Simülatörü
Donanım olmadan masaüstü arayüzünü, grafikleri ve haritayı 60Hz/10Hz frekansta test etmeyi sağlar.
"""

import math
import random
import time
from typing import Callable, Optional
from core.telemetry_model import RocketTelemetry, PayloadTelemetry


class FlightSimulator:
    def __init__(self, update_callback: Optional[Callable[[RocketTelemetry, PayloadTelemetry], None]] = None):
        self.update_callback = update_callback
        self.is_running = False

        # Başlangıç Konumu (Yozgat Bozok Üniversitesi Kampüsü)
        self.base_lat = 39.779593
        self.base_lng = 34.799597
        self.base_altitude = 1050.0  # Rampa rakımı (m)

        # Uçuş Parametreleri
        self.target_apogee = 3000.0  # Hedef irtifa (m)
        self.burn_time = 3.8         # Motor yanış süresi (sn)
        self.drogue_altitude = 3000.0 # Tepe noktası
        self.separation_altitude = 2400.0 # Görev yükü ayrılma irtifası
        self.main_chute_altitude = 550.0  # Ana paraşüt açılma irtifası

        self.reset()

    def reset(self):
        self.time_elapsed = 0.0
        self.packet_id = 0
        self.current_altitude = 0.0  # Bağıl irtifa
        self.max_altitude = 0.0
        self.vertical_speed = 0.0
        self.flight_state = "RAMPA_BEKLEME"
        self.payload_separated = False

        # Rüzgar sürüklenmesi (koordinat ofseti)
        self.drift_x = 0.0
        self.drift_y = 0.0
        self.payload_drift_x = 0.0
        self.payload_drift_y = 0.0

        self.rocket_data = RocketTelemetry()
        self.payload_data = PayloadTelemetry()

    def update_physics(self, dt: float):
        self.time_elapsed += dt
        self.packet_id += 1

        t = self.time_elapsed

        # 1. Faz: Rampa Bekleme (İlk 3 saniye)
        if t < 3.0:
            self.flight_state = "RAMPA_BEKLEME"
            self.current_altitude = 0.0
            self.vertical_speed = 0.0
            acc_z = 1.0 + random.uniform(-0.02, 0.02)
            acc_x = random.uniform(-0.02, 0.02)
            acc_y = random.uniform(-0.02, 0.02)
            gyr_x = gyr_y = gyr_z = random.uniform(-0.5, 0.5)

        # 2. Faz: Motor Yanışı (3s - 6.8s)
        elif t < 3.0 + self.burn_time:
            self.flight_state = "MOTOR_YANISI"
            burn_progress = (t - 3.0) / self.burn_time
            thrust_acc = 7.5 + 4.0 * math.sin(burn_progress * math.pi)  # ~8-11G
            acc_z = thrust_acc + random.uniform(-0.3, 0.3)
            acc_x = random.uniform(-0.2, 0.2)
            acc_y = random.uniform(-0.2, 0.2)

            self.vertical_speed += (thrust_acc * 9.81 - 9.81 - 0.0008 * self.vertical_speed**2) * dt
            self.current_altitude += self.vertical_speed * dt
            gyr_x = random.uniform(-3.0, 3.0)
            gyr_y = random.uniform(-3.0, 3.0)
            gyr_z = 25.0 + random.uniform(-5.0, 5.0)  # Yuvarlanma (roll)

        # 3. Faz: Serbest Tırmanış (Apogee'ye kadar)
        elif self.vertical_speed > 0:
            self.flight_state = "TIRMANMA"
            drag = 0.0012 * self.vertical_speed**2
            decel = -9.81 - drag
            self.vertical_speed += decel * dt
            if self.vertical_speed < 0:
                self.vertical_speed = 0.0
            self.current_altitude += self.vertical_speed * dt
            acc_z = decel / 9.81 + random.uniform(-0.1, 0.1)
            acc_x = random.uniform(-0.1, 0.1)
            acc_y = random.uniform(-0.1, 0.1)
            gyr_x = random.uniform(-2.0, 2.0)
            gyr_y = random.uniform(-2.0, 2.0)
            gyr_z = random.uniform(-3.0, 3.0)

        # 4. Faz: İniş (Drogue, Ayrılma ve Ana Paraşüt)
        else:
            if self.current_altitude > self.separation_altitude:
                self.flight_state = "DROG_PARASUT"
                target_speed = -22.0  # Drogue iniş hızı
            elif self.current_altitude > self.main_chute_altitude:
                self.flight_state = "GOREV_YUKU_AYRILDI"
                self.payload_separated = True
                target_speed = -18.0
            else:
                self.flight_state = "ANA_PARASUT"
                target_speed = -6.5   # Ana paraşüt yumuşak iniş hızı

            # Hız hedefine doğru yaklaş
            self.vertical_speed += (target_speed - self.vertical_speed) * 0.1
            self.current_altitude += self.vertical_speed * dt

            if self.current_altitude <= 0.0:
                self.current_altitude = 0.0
                self.vertical_speed = 0.0
                self.flight_state = "KURTARMA_INIS"

            acc_z = 1.0 + random.uniform(-0.05, 0.05)
            acc_x = random.uniform(-0.05, 0.05)
            acc_y = random.uniform(-0.05, 0.05)
            gyr_x = random.uniform(-1.0, 1.0)
            gyr_y = random.uniform(-1.0, 1.0)
            gyr_z = random.uniform(-1.0, 1.0)

        # Maksimum irtifa takibi
        if self.current_altitude > self.max_altitude:
            self.max_altitude = self.current_altitude

        # Basınç Hesabı (Barometrik Formül)
        total_alt = self.base_altitude + self.current_altitude
        # P = P0 * (1 - L*h / T0)^(g*M / (R0*L))
        std_pressure = 1013.25 * math.pow(1.0 - 2.25577e-5 * total_alt, 5.25588)
        dps_noise = random.gauss(0, 0.15)
        bmp_noise = random.gauss(0, 0.18)
        dps368_p = std_pressure + dps_noise
        bmp390_p = std_pressure + bmp_noise

        # Rüzgar sürüklenmesi (GPS Güncellemesi)
        wind_speed_x = 0.000008  # Doğuya sürüklenme
        wind_speed_y = 0.000004  # Kuzeye sürüklenme
        if self.current_altitude > 10.0:
            self.drift_x += wind_speed_x * dt
            self.drift_y += wind_speed_y * dt

        neo_lat = self.base_lat + self.drift_y + random.gauss(0, 0.000002)
        neo_lng = self.base_lng + self.drift_x + random.gauss(0, 0.000002)
        quectel_lat = self.base_lat + self.drift_y + random.gauss(0, 0.000003)
        quectel_lng = self.base_lng + self.drift_x + random.gauss(0, 0.000003)

        # Pil Gerilimi (Hafif düşüş simülasyonu)
        batt_volt = max(11.1, 12.55 - (self.time_elapsed * 0.002))
        batt_pct = int(max(0, min(100, (batt_volt - 11.0) / (12.6 - 11.0) * 100)))

        # Roket Telemetrisini Güncelle
        self.rocket_data.packet_id = self.packet_id
        self.rocket_data.flight_time = self.time_elapsed
        self.rocket_data.timestamp = time.time()
        self.rocket_data.altitude = round(self.current_altitude, 1)
        self.rocket_data.max_altitude = round(self.max_altitude, 1)
        self.rocket_data.vertical_speed = round(self.vertical_speed, 1)
        self.rocket_data.dps368_pressure = round(dps368_p, 2)
        self.rocket_data.bmp390_pressure = round(bmp390_p, 2)
        self.rocket_data.temperature = round(24.0 - (self.current_altitude * 0.0065), 1)

        self.rocket_data.acc_x = round(acc_x, 2)
        self.rocket_data.acc_y = round(acc_y, 2)
        self.rocket_data.acc_z = round(acc_z, 2)
        self.rocket_data.total_acc = round(math.sqrt(acc_x**2 + acc_y**2 + acc_z**2), 2)

        self.rocket_data.gyr_x = round(gyr_x, 1)
        self.rocket_data.gyr_y = round(gyr_y, 1)
        self.rocket_data.gyr_z = round(gyr_z, 1)

        self.rocket_data.neo_m9n_lat = round(neo_lat, 6)
        self.rocket_data.neo_m9n_lng = round(neo_lng, 6)
        self.rocket_data.neo_m9n_satellites = 14 if t > 2 else 6
        self.rocket_data.neo_m9n_status = "3D FIX (14 Uydu)" if t > 2 else "2D FIX"

        self.rocket_data.quectel_lat = round(quectel_lat, 6)
        self.rocket_data.quectel_lng = round(quectel_lng, 6)
        self.rocket_data.quectel_satellites = 12 if t > 2 else 5
        self.rocket_data.quectel_status = "3D FIX (12 Uydu)" if t > 2 else "2D FIX"

        self.rocket_data.battery_voltage = round(batt_volt, 2)
        self.rocket_data.battery_percentage = batt_pct
        self.rocket_data.flight_state = self.flight_state

        # Görev Yükü Telemetrisi
        if self.payload_separated:
            # Kendi paraşütüyle farklı hızda ve farklı yönde sürüklenir
            self.payload_drift_x += (wind_speed_x * 1.5) * dt
            self.payload_drift_y += (wind_speed_y * 1.2) * dt
            p_lat = self.base_lat + self.payload_drift_y
            p_lng = self.base_lng + self.payload_drift_x
            p_vib_ext = abs(random.gauss(0.12, 0.05))
            p_vib_int = abs(random.gauss(0.04, 0.02))
        else:
            p_lat = neo_lat
            p_lng = neo_lng
            p_vib_ext = abs(acc_z * 0.1 + random.gauss(0, 0.05))
            p_vib_int = abs(acc_z * 0.04 + random.gauss(0, 0.02))

        self.payload_data.packet_id = self.packet_id
        self.payload_data.flight_time = self.time_elapsed
        self.payload_data.timestamp = time.time()
        self.payload_data.vibration_ext = round(p_vib_ext, 2)
        self.payload_data.vibration_int = round(p_vib_int, 2)
        self.payload_data.lsm6_ext_x = round(acc_x * 0.9 + random.gauss(0, 0.04), 2)
        self.payload_data.lsm6_ext_y = round(acc_y * 0.9 + random.gauss(0, 0.04), 2)
        self.payload_data.lsm6_ext_z = round(acc_z * 0.9 + random.gauss(0, 0.04), 2)
        self.payload_data.lsm6_int_x = round(acc_x * 0.7 + random.gauss(0, 0.02), 2)
        self.payload_data.lsm6_int_y = round(acc_y * 0.7 + random.gauss(0, 0.02), 2)
        self.payload_data.lsm6_int_z = round(acc_z * 0.7 + random.gauss(0, 0.02), 2)
        self.payload_data.latitude = round(p_lat, 6)
        self.payload_data.longitude = round(p_lng, 6)
        self.payload_data.altitude = round(self.current_altitude, 1)
        self.payload_data.satellites = 12
        self.payload_data.is_separated = self.payload_separated
        self.payload_data.battery_voltage = round(8.35 - (self.time_elapsed * 0.001), 2)
        self.payload_data.battery_percentage = int(max(0, min(100, (self.payload_data.battery_voltage - 7.0) / 1.4 * 100)))

        if self.update_callback:
            self.update_callback(self.rocket_data, self.payload_data)
