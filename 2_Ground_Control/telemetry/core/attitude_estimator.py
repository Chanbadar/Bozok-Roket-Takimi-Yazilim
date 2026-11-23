"""
Bozok Roket Takımı - Kuaterniyon Tabanlı AHRS / Duruş (Attitude) Kestirici
Ham BMI088 / GY-85 ivmeölçer + jiroskop verilerinden Gimbal Lock olmadan
canlı Pitch, Roll ve Yaw açılarını hesaplar.

Roket Eksen Sözleşmesi (Bozok Yer İstasyonu):
- Gövde +Z ekseni: Roket uzunlamasına ekseni (kuyruktan buruna)
- Rampa üzerinde dik duruş:
    acc = (0, 0, +1g) -> pitch = +90.0°, roll = 0.0°, yaw = 0.0°
- Yatay (apogee devrilmesi): pitch = 0.0°
- Burun aşağı dik dalış: pitch = -90.0°
- Gövde +Z etrafında dönüş (gyr_z): Roll (yuvarlanma)
"""

from __future__ import annotations

import math
import time
from typing import Optional, Tuple


class AttitudeEstimator:
    """
    Mahony benzeri kuaterniyon tamamlayıcı filtre.
    - Sabit / düşük ivmeli durumda (|a| ≈ 1g) yerçekimi vektörüyle eğim kaymasını (drift) düzeltir.
    - Motor yanışı (>1.4g) veya serbest düşüş (<0.4g) sırasında ivmeölçer düzeltmesini kapatıp
      saf jiroskop kuaterniyon entegrasyonu kullanır.
    """

    def __init__(self, kp: float = 1.6):
        self.kp = kp
        self.reset()

    def reset(self, pitch_deg: float = 90.0, roll_deg: float = 0.0, yaw_deg: float = 0.0):
        # Birim kuaterniyon (w, x, y, z): gövde ekseninden dünya ENU eksenine dönüş
        # Kimlik kuaterniyonu (1,0,0,0) gövde +Z'yi dünya +Z'ye (yukarı/zenit) hizalar -> pitch=+90°!
        self.qw = 1.0
        self.qx = 0.0
        self.qy = 0.0
        self.qz = 0.0
        self._last_time: Optional[float] = None
        self._initialized_from_acc = False

        # İstenen başlangıç açıları standart dik duruştan farklıysa uygula
        if abs(pitch_deg - 90.0) > 1e-3 or abs(roll_deg) > 1e-3 or abs(yaw_deg) > 1e-3:
            self.set_euler(roll_deg, pitch_deg, yaw_deg)

    def set_euler(self, roll_deg: float, pitch_deg: float, yaw_deg: float):
        """Roket (roll, pitch, yaw) açılarından kuaterniyonu doğrudan kurar."""
        tilt = math.radians(90.0 - pitch_deg)
        yaw = math.radians(yaw_deg)
        roll = math.radians(roll_deg)

        # q = q_z(yaw) * q_x(tilt) * q_z(roll)
        q_yaw = (math.cos(yaw * 0.5), 0.0, 0.0, math.sin(yaw * 0.5))
        q_tilt = (math.cos(tilt * 0.5), math.sin(tilt * 0.5), 0.0, 0.0)
        q_roll = (math.cos(roll * 0.5), 0.0, 0.0, math.sin(roll * 0.5))

        q = self._qmul(self._qmul(q_yaw, q_tilt), q_roll)
        self.qw, self.qx, self.qy, self.qz = self._qnorm(q)

    @staticmethod
    def _qmul(a: Tuple[float, float, float, float], b: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
        aw, ax, ay, az = a
        bw, bx, by, bz = b
        return (
            aw * bw - ax * bx - ay * by - az * bz,
            aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
        )

    @staticmethod
    def _qnorm(q: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
        w, x, y, z = q
        n = math.sqrt(w * w + x * x + y * y + z * z)
        if n < 1e-12:
            return (1.0, 0.0, 0.0, 0.0)
        return (w / n, x / n, y / n, z / n)

    def _gravity_in_body(self) -> Tuple[float, float, float]:
        """Dünya +Z (yukarı) birim vektörünü mevcut kuaterniyonla gövde eksenine çevirir."""
        w, x, y, z = self.qw, self.qx, self.qy, self.qz
        # R^T * [0, 0, 1]^T
        gx = 2.0 * (x * z - w * y)
        gy = 2.0 * (y * z + w * x)
        gz = 1.0 - 2.0 * (x * x + y * y)
        return (gx, gy, gz)

    def _init_from_gravity(self, ax: float, ay: float, az: float):
        """İlk sabit ivme ölçümünden başlangıç eğimini hizalar."""
        norm = math.sqrt(ax * ax + ay * ay + az * az)
        if norm < 0.2:
            return
        ux, uy, uz = ax / norm, ay / norm, az / norm
        # Gövde eksenindeki yerçekimi u'yu dünya +Z=(0,0,1)'e taşıyan en kısa dönüş
        dot = max(-1.0, min(1.0, uz))
        if dot > 0.9999:
            self.qw, self.qx, self.qy, self.qz = 1.0, 0.0, 0.0, 0.0
        elif dot < -0.9999:
            self.qw, self.qx, self.qy, self.qz = 0.0, 1.0, 0.0, 0.0
        else:
            # cross(u, [0,0,1]) = (uy, -ux, 0)
            cx, cy, cz = uy, -ux, 0.0
            s = math.sqrt((1.0 + dot) * 2.0)
            self.qw, self.qx, self.qy, self.qz = self._qnorm((0.5 * s, cx / s, cy / s, cz / s))

    def update(
        self,
        acc_x: float,
        acc_y: float,
        acc_z: float,
        gyr_x_dps: float,
        gyr_y_dps: float,
        gyr_z_dps: float,
        timestamp: Optional[float] = None,
    ) -> Tuple[float, float, float]:
        """
        Yeni IMU verisiyle duruşu günceller ve (roll_deg, pitch_deg, yaw_deg) döndürür.
        """
        now = timestamp if timestamp is not None else time.time()
        if self._last_time is None:
            dt = 0.02
        else:
            dt = now - self._last_time
            if dt <= 0.0 or dt > 1.0:
                dt = 0.02
        self._last_time = now

        acc_norm = math.sqrt(acc_x * acc_x + acc_y * acc_y + acc_z * acc_z)

        # İlk paket sakin 1g civarındaysa doğrudan başlangıç eğimini hizala
        if not self._initialized_from_acc and 0.6 <= acc_norm <= 1.4:
            self._init_from_gravity(acc_x, acc_y, acc_z)
            self._initialized_from_acc = True

        # Jiroskop rad/s
        wx = math.radians(gyr_x_dps) if math.isfinite(gyr_x_dps) else 0.0
        wy = math.radians(gyr_y_dps) if math.isfinite(gyr_y_dps) else 0.0
        wz = math.radians(gyr_z_dps) if math.isfinite(gyr_z_dps) else 0.0

        # Sadece 1g civarında (statik/düşük ivmeli hareket) ivmeölçer ile eğim düzeltmesi yap
        if 0.65 <= acc_norm <= 1.35:
            ax = acc_x / acc_norm
            ay = acc_y / acc_norm
            az = acc_z / acc_norm

            gx, gy, gz = self._gravity_in_body()

            # Hata vektörü = measured_g x estimated_g
            ex = ay * gz - az * gy
            ey = az * gx - ax * gz
            ez = ax * gy - ay * gx

            # Jiroskop tamamen 0 ise (örn. sadece ivmeölçer gönderen test sensörü) daha hızlı yakınsa
            gyro_mag = abs(wx) + abs(wy) + abs(wz)
            gain = 5.0 if gyro_mag < 1e-4 else self.kp

            wx += gain * ex
            wy += gain * ey
            wz += gain * ez

        # Kuaterniyon türevi: q_dot = 0.5 * q * (0, wx, wy, wz)
        w, x, y, z = self.qw, self.qx, self.qy, self.qz
        dw = 0.5 * (-x * wx - y * wy - z * wz)
        dx = 0.5 * (w * wx + y * wz - z * wy)
        dy = 0.5 * (w * wy - x * wz + z * wx)
        dz = 0.5 * (w * wz + x * wy - y * wx)

        self.qw, self.qx, self.qy, self.qz = self._qnorm(
            (w + dw * dt, x + dx * dt, y + dy * dt, z + dz * dt)
        )

        return self.get_euler_deg()

    def get_euler_deg(self) -> Tuple[float, float, float]:
        """
        Kuaterniyonu roket (roll, pitch, yaw) derece değerlerine dönüştürür.
        - pitch: +90° (dik yukarı) .. 0° (yatay) .. -90° (dik aşağı)
        - yaw:   -180° .. +180° (yatay düzlemde burun yönü / azimut)
        - roll:  -180° .. +180° (uzunlamasına eksen etrafında dönüş)
        """
        w, x, y, z = self.qw, self.qx, self.qy, self.qz

        # Gövde +Z ekseninin (roket burnu) dünya koordinatlarındaki vektörü: R * [0, 0, 1]^T
        nx = 2.0 * (x * z + w * y)
        ny = 2.0 * (y * z - w * x)
        nz = 1.0 - 2.0 * (x * x + y * y)

        # Gövde +X ekseninin dünya koordinatlarındaki vektörü: R * [1, 0, 0]^T
        xx = 1.0 - 2.0 * (y * y + z * z)
        xy = 2.0 * (x * y + w * z)
        xz = 2.0 * (x * z - w * y)

        # Pitch (elevasyon): burun vektörünün yatay düzlemle açısı [-90, +90]
        pitch = math.degrees(math.asin(max(-1.0, min(1.0, nz))))

        horiz = math.hypot(nx, ny)
        if horiz > 1e-4:
            # Yatay düzlemdeki burun azimutu (q_z(yaw) * q_x(tilt) sözleşmesine uyumlu)
            # tilt>0 için burun dünya -Y yönüne yatar -> yaw = atan2(nx, -ny)
            yaw = math.degrees(math.atan2(nx, -ny))

            # Referans sağ eksen (yaw ile dönmüş +X): [cos(yaw), sin(yaw), 0]
            yaw_rad = math.radians(yaw)
            ref_x = (math.cos(yaw_rad), math.sin(yaw_rad), 0.0)
            # Referans "up/kanat" ekseni = nose x ref_x (gövde +Y ile aynı hizada)
            # Gövde +Y ekseni dünya koordinatında:
            yx = 2.0 * (x * y - w * z)
            yy = 1.0 - 2.0 * (x * x + z * z)

            dot_x = xx * ref_x[0] + xy * ref_x[1]
            dot_y = yx * ref_x[0] + yy * ref_x[1]
            roll = math.degrees(math.atan2(-dot_y, dot_x))
        else:
            # Roket neredeyse tam dik (pitch ≈ ±90°): dönüş doğrudan roll'a aktarılır
            yaw = 0.0
            roll = math.degrees(math.atan2(xy, xx))

        return (round(roll, 1), round(pitch, 1), round(yaw, 1))
