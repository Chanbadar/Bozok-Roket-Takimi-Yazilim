"""
Bozok Roket Takımı - Canlı 3D Roket Duruş (Pitch, Roll, Yaw) Bileşeni
OpenRocket (.ork) dosyasından okunan gerçek 1:1 geometriyi çevrimdışı Three.js (WebGL)
ile 60 FPS döndürür. Tek tıkla bağımsız pencereye ayırma (Pop-out) ve geri yerleştirme (Dock)
desteği sunar; QtWebEngine yoksa dahili 3D projeksiyonlu QPainter yedek görünümüne düşer.
"""

from __future__ import annotations

import json
import math
import os
from typing import Any, Dict, Optional

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QLabel, QMainWindow,
    QMessageBox, QPushButton, QSlider, QVBoxLayout, QWidget,
)

from core.ork_parser import load_rocket_spec, parse_ork_file

try:
    from PySide6.QtWebEngineCore import QWebEngineSettings
    from PySide6.QtWebEngineWidgets import QWebEngineView
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False


class Fallback3DRocketView(QWidget):
    """QtWebEngine kurulu olmadığında çalışan dahili 3D perspektif projeksiyonlu roket görünümü."""

    def __init__(self, spec: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.spec = spec
        self.pitch = 90.0
        self.roll = 0.0
        self.yaw = 0.0
        self.flight_state = "RAMPA_BEKLEME"
        self.setMinimumSize(240, 220)

    def set_spec(self, spec: Dict[str, Any]):
        self.spec = spec
        self.update()

    def update_attitude(self, pitch: float, roll: float, yaw: float, flight_state: str):
        self.pitch = pitch
        self.roll = roll
        self.yaw = yaw
        self.flight_state = flight_state
        self.update()

    def _rotate_point(self, x: float, y: float, z: float) -> tuple[float, float, float]:
        # Roll (Y ekseni), Tilt = 90 - pitch (X ekseni), Yaw (-Y ekseni)
        rr = math.radians(self.roll)
        tr = -math.radians(90.0 - self.pitch)
        yr = -math.radians(self.yaw)

        # 1. Roll around local Y
        x1 = x * math.cos(rr) + z * math.sin(rr)
        y1 = y
        z1 = -x * math.sin(rr) + z * math.cos(rr)

        # 2. Tilt around X
        x2 = x1
        y2 = y1 * math.cos(tr) - z1 * math.sin(tr)
        z2 = y1 * math.sin(tr) + z1 * math.cos(tr)

        # 3. Yaw around World Y
        x3 = x2 * math.cos(yr) + z2 * math.sin(yr)
        y3 = y2
        z3 = -x2 * math.sin(yr) + z2 * math.cos(yr)

        # Sabit 3/4 kamera eğimi
        cam_p = math.radians(22.0)
        cam_y = math.radians(-30.0)
        cx = x3 * math.cos(cam_y) + z3 * math.sin(cam_y)
        cz = -x3 * math.sin(cam_y) + z3 * math.cos(cam_y)
        cy = y3 * math.cos(cam_p) - cz * math.sin(cam_p)
        cz2 = y3 * math.sin(cam_p) + cz * math.cos(cam_p)
        return (cx, cy, cz2)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w * 0.5, h * 0.48
        scale = min(w, h) * 0.34

        painter.fillRect(0, 0, w, h, QColor("#091124"))

        def proj(pt):
            x, y, z = self._rotate_point(*pt)
            persp = 3.8 / (3.8 - z)
            return (cx + x * scale * persp, cy - y * scale * persp)

        # Ufuk halkası
        painter.setPen(QPen(QColor(56, 189, 248, 70), 1, Qt.PenStyle.DashLine))
        painter.drawEllipse(int(cx - scale * 0.9), int(cy - scale * 0.35), int(scale * 1.8), int(scale * 0.7))

        # Roket eksen çizgisi (kuyruk -> burun)
        tail = proj((0.0, -1.0, 0.0))
        nose_base = proj((0.0, 0.65, 0.0))
        nose_tip = proj((0.0, 1.0, 0.0))

        # Kanatçıklar (3 adet 120°)
        painter.setPen(QPen(QColor("#CBD5E1"), 2))
        for i in range(3):
            ang = math.radians(i * 120.0)
            r_in, r_out = 0.06, 0.24
            p1 = proj((math.cos(ang) * r_in, -0.78, math.sin(ang) * r_in))
            p2 = proj((math.cos(ang) * r_out, -0.92, math.sin(ang) * r_out))
            p3 = proj((math.cos(ang) * r_out, -1.0, math.sin(ang) * r_out))
            p4 = proj((math.cos(ang) * r_in, -0.98, math.sin(ang) * r_in))
            poly = QPolygonF()
            from PySide6.QtCore import QPointF
            for px, py in (p1, p2, p3, p4):
                poly.append(QPointF(px, py))
            painter.setBrush(QBrush(QColor("#FF6B4A" if i == 0 else "#94A3B8")))
            painter.drawPolygon(poly)

        # Gövde ve Burun
        painter.setPen(QPen(QColor("#E2E8F0"), 10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
        painter.drawLine(int(tail[0]), int(tail[1]), int(nose_base[0]), int(nose_base[1]))
        painter.setPen(QPen(QColor("#38BDF8"), 6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(int(nose_base[0]), int(nose_base[1]), int(nose_tip[0]), int(nose_tip[1]))

        # HUD yazıları
        painter.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        painter.setPen(QColor("#38BDF8"))
        painter.drawText(10, h - 14, f"P:{self.pitch:+.1f}°  R:{self.roll:+.1f}°  Y:{self.yaw:+.1f}°")
        painter.setPen(QColor("#94A3B8"))
        painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        painter.drawText(10, 18, f"{self.spec.get('name', 'BOZOK')} (2D/3D Yedek Görünüm)")


class Rocket3DPopoutWindow(QMainWindow):
    """3D Roket Duruş Görünümü için bağımsız, yeniden boyutlandırılabilir pencere (2. monitör modu)."""

    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bozok Roket Takımı - Canlı 3D Duruş Penceresi")
        self.resize(960, 720)
        self.setStyleSheet(
            "QMainWindow { background-color: #080D1A; color: #F8FAFC; }"
            "QPushButton { background-color: #1E293B; color: #F8FAFC; border: 1px solid #334155; "
            "border-radius: 5px; padding: 5px 10px; font-weight: 700; font-size: 11px; }"
            "QPushButton:hover { background-color: #2E3D56; border-color: #38BDF8; }"
        )
        self._closing_silently = False

    def closeEvent(self, event):
        if not self._closing_silently:
            self.closed.emit()
        event.accept()


class Rocket3DWidget(QFrame):
    """
    Dashboard'da canlı 3D roket duruşu (Pitch, Roll, Yaw) gösterir ve tek tıkla
    bağımsız pencereye ayrılıp (Pop-out) tekrar dashboard'a yerleştirilebilir (Dock).
    """

    def __init__(self, parent=None, ork_path: Optional[str] = None):
        super().__init__(parent)
        self.setProperty("class", "TeleCard")
        self.setObjectName("Rocket3DPanel")

        self._base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self._assets_dir = os.path.join(self._base_dir, "assets")
        self._html_path = os.path.join(self._assets_dir, "rocket_3d_viewer.html")

        self.rocket_spec: Dict[str, Any] = load_rocket_spec(ork_path)
        self._page_ready = False
        self._manual_test_mode = False
        self._is_popped_out = False
        self._popout_window: Optional[Rocket3DPopoutWindow] = None

        self._last_pitch = 90.0
        self._last_roll = 0.0
        self._last_yaw = 0.0
        self._last_state = "RAMPA_BEKLEME"

        self._init_ui()

    def _init_ui(self):
        self._card_layout = QVBoxLayout(self)
        self._card_layout.setContentsMargins(10, 8, 10, 8)
        self._card_layout.setSpacing(6)

        # --- Üst Başlık & Araç Çubuğu ---
        header = QHBoxLayout()
        header.setSpacing(4)

        title = QLabel("🚀 3D DURUŞ")
        title.setStyleSheet(
            "font-size: 13px; font-weight: 800; color: #00F0FF; letter-spacing: 0.4px;"
        )
        header.addWidget(title)
        header.addStretch(1)

        btn_style = (
            "QPushButton { background-color: #131C31; color: #CBD5E1; border: 1px solid #334155; "
            "border-radius: 5px; padding: 3px 7px; font-size: 10px; font-weight: 700; }"
            "QPushButton:hover { background-color: #1E293B; border-color: #38BDF8; color: #FFFFFF; }"
            "QPushButton:checked { background-color: #0369A1; border-color: #38BDF8; color: #FFFFFF; }"
        )

        # Özel .ork tasarım dosyası yükle
        self.load_ork_btn = QPushButton("📂 .ORK")
        self.load_ork_btn.setToolTip("Farklı bir OpenRocket (.ork / .ork.zip) tasarımı yükle")
        self.load_ork_btn.setStyleSheet(btn_style)
        self.load_ork_btn.clicked.connect(self._browse_ork_file)
        header.addWidget(self.load_ork_btn)

        # Manuel Pitch/Roll/Yaw Test Sürgüleri Aç/Kapa
        self.manual_btn = QPushButton("🎛 Test")
        self.manual_btn.setCheckable(True)
        self.manual_btn.setToolTip("Manuel Pitch / Roll / Yaw test sürgülerini aç/kapat")
        self.manual_btn.setStyleSheet(btn_style)
        self.manual_btn.toggled.connect(self._toggle_manual_controls)
        header.addWidget(self.manual_btn)

        # Ayrı Pencere (Pop-out) / Geri Yerleştir (Dock)
        self.popout_btn = QPushButton("⛶ Ayır")
        self.popout_btn.setToolTip("3D görünümü bağımsız pencereye ayır (ikinci monitör / tam ekran)")
        self.popout_btn.setStyleSheet(btn_style)
        self.popout_btn.clicked.connect(self.toggle_popout)
        header.addWidget(self.popout_btn)

        self._card_layout.addLayout(header)

        # --- Taşınabilir 3D İçerik Kapsayıcısı (Dashboard <-> Pop-out arasında taşınır) ---
        self._viewport_container = QWidget()
        self._viewport_container.setStyleSheet("background-color: #080D1A; border-radius: 6px;")
        vp_layout = QVBoxLayout(self._viewport_container)
        vp_layout.setContentsMargins(0, 0, 0, 0)
        vp_layout.setSpacing(4)

        if WEBENGINE_AVAILABLE and os.path.isfile(self._html_path):
            self.web_view = QWebEngineView()
            self.web_view.setMinimumHeight(210)
            settings = self.web_view.settings()
            settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
            self.web_view.page().setBackgroundColor(QColor("#080D1A"))
            self.web_view.loadFinished.connect(self._on_web_loaded)
            self.web_view.setUrl(QUrl.fromLocalFile(self._html_path))
            vp_layout.addWidget(self.web_view, 1)
            self.fallback_view = None
        else:
            self.web_view = None
            self.fallback_view = Fallback3DRocketView(self.rocket_spec)
            vp_layout.addWidget(self.fallback_view, 1)

        # Manuel Test Sürgü Paneli (Varsayılan gizli)
        self._manual_panel = self._build_manual_panel()
        self._manual_panel.setVisible(False)
        vp_layout.addWidget(self._manual_panel)

        self._card_layout.addWidget(self._viewport_container, 1)

        # --- Pop-out Açıkken Dashboard'da Görünen Yer Tutucu ---
        self._dock_placeholder = QFrame()
        self._dock_placeholder.setStyleSheet(
            "background-color: #0B132B; border: 1px dashed #334155; border-radius: 8px;"
        )
        ph_layout = QVBoxLayout(self._dock_placeholder)
        ph_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ph_layout.setSpacing(8)

        ph_lbl = QLabel("3D Roket Duruş Görünümü\nAyrı Pencerede Açık")
        ph_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ph_lbl.setStyleSheet("color: #94A3B8; font-weight: 700; font-size: 12px; border: none;")
        ph_layout.addWidget(ph_lbl)

        ph_btn_row = QHBoxLayout()
        focus_btn = QPushButton("🗔 Pencereyi Öne Getir")
        focus_btn.clicked.connect(self._focus_popout)
        dock_btn = QPushButton("↙ Dashboard'a Geri Al")
        dock_btn.setStyleSheet("background-color: #0284C7; border: 1px solid #38BDF8; color: white;")
        dock_btn.clicked.connect(self.dock_back)
        ph_btn_row.addWidget(focus_btn)
        ph_btn_row.addWidget(dock_btn)
        ph_layout.addLayout(ph_btn_row)

        self._dock_placeholder.setVisible(False)
        self._card_layout.addWidget(self._dock_placeholder, 1)

    def _build_manual_panel(self) -> QFrame:
        panel = QFrame()
        panel.setStyleSheet(
            "QFrame { background-color: #0F172A; border: 1px solid #1E293B; border-radius: 6px; padding: 4px; }"
            "QLabel { color: #CBD5E1; font-size: 10px; font-weight: 700; font-family: Consolas, monospace; border: none; }"
        )
        vbox = QVBoxLayout(panel)
        vbox.setContentsMargins(6, 4, 6, 4)
        vbox.setSpacing(3)

        def make_slider_row(name: str, color: str, vmin: int, vmax: int, initial: int):
            row = QHBoxLayout()
            row.setSpacing(6)
            lbl = QLabel(name)
            lbl.setFixedWidth(42)
            lbl.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: 800; border: none;")
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(vmin, vmax)
            slider.setValue(initial)
            val_lbl = QLabel(f"{initial:+d}°")
            val_lbl.setFixedWidth(44)
            val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            row.addWidget(lbl)
            row.addWidget(slider, 1)
            row.addWidget(val_lbl)
            vbox.addLayout(row)
            return slider, val_lbl

        self._sl_pitch, self._lbl_pitch = make_slider_row("PITCH", "#38BDF8", -90, 90, 90)
        self._sl_roll, self._lbl_roll = make_slider_row("ROLL", "#FACC15", -180, 180, 0)
        self._sl_yaw, self._lbl_yaw = make_slider_row("YAW", "#FB923C", -180, 180, 0)

        for sl in (self._sl_pitch, self._sl_roll, self._sl_yaw):
            sl.valueChanged.connect(self._on_manual_slider_changed)

        btn_row = QHBoxLayout()
        reset_angles_btn = QPushButton("Dik Konum (90/0/0)")
        reset_angles_btn.setStyleSheet("padding: 2px 8px; font-size: 10px;")
        reset_angles_btn.clicked.connect(self._reset_manual_sliders)
        btn_row.addStretch(1)
        btn_row.addWidget(reset_angles_btn)
        vbox.addLayout(btn_row)

        return panel

    def _toggle_manual_controls(self, checked: bool):
        self._manual_test_mode = checked
        self._manual_panel.setVisible(checked)
        if checked:
            self._sl_pitch.blockSignals(True)
            self._sl_roll.blockSignals(True)
            self._sl_yaw.blockSignals(True)
            self._sl_pitch.setValue(int(round(max(-90.0, min(90.0, self._last_pitch)))))
            self._sl_roll.setValue(int(round(max(-180.0, min(180.0, self._last_roll)))))
            self._sl_yaw.setValue(int(round(max(-180.0, min(180.0, self._last_yaw)))))
            self._sl_pitch.blockSignals(False)
            self._sl_roll.blockSignals(False)
            self._sl_yaw.blockSignals(False)
            self._on_manual_slider_changed()
        else:
            # Canlı telemetri durumuna geri dön
            self._push_attitude_to_view(self._last_pitch, self._last_roll, self._last_yaw, self._last_state)

    def _reset_manual_sliders(self):
        self._sl_pitch.setValue(90)
        self._sl_roll.setValue(0)
        self._sl_yaw.setValue(0)

    def _on_manual_slider_changed(self):
        p = float(self._sl_pitch.value())
        r = float(self._sl_roll.value())
        y = float(self._sl_yaw.value())
        self._lbl_pitch.setText(f"{int(p):+d}°")
        self._lbl_roll.setText(f"{int(r):+d}°")
        self._lbl_yaw.setText(f"{int(y):+d}°")
        if self._manual_test_mode:
            self._push_attitude_to_view(p, r, y, "MANUEL_TEST")

    def _on_web_loaded(self, ok: bool):
        if not ok:
            return
        self._page_ready = True
        self._push_spec_to_view()
        self._push_attitude_to_view(self._last_pitch, self._last_roll, self._last_yaw, self._last_state)

    def _push_spec_to_view(self):
        if self.web_view and self._page_ready:
            spec_json = json.dumps(self.rocket_spec, ensure_ascii=False)
            self.web_view.page().runJavaScript(
                f"if (typeof setRocketSpec === 'function') setRocketSpec({spec_json});"
            )
        elif self.fallback_view:
            self.fallback_view.set_spec(self.rocket_spec)

    def _push_attitude_to_view(self, pitch: float, roll: float, yaw: float, flight_state: str):
        if self.web_view and self._page_ready:
            state_json = json.dumps(str(flight_state))
            js = (
                "if (typeof updateAttitude === 'function') "
                f"updateAttitude({pitch:.2f}, {roll:.2f}, {yaw:.2f}, {state_json});"
            )
            self.web_view.page().runJavaScript(js)
        elif self.fallback_view:
            self.fallback_view.update_attitude(pitch, roll, yaw, flight_state)

    def update_attitude(self, pitch: float, roll: float, yaw: float, flight_state: str = "RAMPA_BEKLEME"):
        """Canlı telemetri / simülasyondan gelen Pitch, Roll, Yaw açılarını 3D modele uygular."""
        self._last_pitch = pitch
        self._last_roll = roll
        self._last_yaw = yaw
        self._last_state = flight_state

        if self._manual_test_mode:
            return
        self._push_attitude_to_view(pitch, roll, yaw, flight_state)

    def _browse_ork_file(self):
        start_dir = self._assets_dir
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "OpenRocket Tasarım Dosyası Seç (.ork / .ork.zip)",
            start_dir,
            "OpenRocket Dosyaları (*.ork *.ork.zip *.zip);;Tüm Dosyalar (*)",
        )
        if not file_path:
            return
        try:
            self.rocket_spec = parse_ork_file(file_path)
            self._push_spec_to_view()
        except Exception as err:
            QMessageBox.warning(
                self,
                "OpenRocket Yükleme Hatası",
                f"Dosya ayrıştırılamadı:\n{err}",
            )

    def toggle_popout(self):
        if self._is_popped_out:
            self.dock_back()
        else:
            self.pop_out()

    def pop_out(self):
        """3D görünümü bağımsız, yeniden boyutlandırılabilir bir pencereye ayırır."""
        if self._is_popped_out:
            self._focus_popout()
            return

        self._popout_window = Rocket3DPopoutWindow()
        self._popout_window.closed.connect(self._on_popout_closed)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(6)

        bar = QHBoxLayout()
        bar_title = QLabel("🚀 BOZOK ROKET TAKIMI — CANLI 3D DURUŞ (BAĞIMSIZ PENCERE)")
        bar_title.setStyleSheet("font-size: 13px; font-weight: 800; color: #00F0FF; letter-spacing: 0.6px;")
        bar.addWidget(bar_title)
        bar.addStretch(1)

        ork_btn = QPushButton("📂 .ORK Yükle")
        ork_btn.clicked.connect(self._browse_ork_file)
        bar.addWidget(ork_btn)

        pop_manual_btn = QPushButton("🎛 Manuel Test")
        pop_manual_btn.setCheckable(True)
        pop_manual_btn.setChecked(self.manual_btn.isChecked())
        pop_manual_btn.toggled.connect(self.manual_btn.setChecked)
        self.manual_btn.toggled.connect(pop_manual_btn.setChecked)
        bar.addWidget(pop_manual_btn)

        dock_btn = QPushButton("↙ Dashboard'a Yerleştir")
        dock_btn.setStyleSheet("background-color: #0284C7; border: 1px solid #38BDF8; color: white;")
        dock_btn.clicked.connect(self.dock_back)
        bar.addWidget(dock_btn)

        layout.addLayout(bar)

        # Mevcut WebGL viewport'unu sıfırdan yeniden yüklemeden yeni pencereye taşı
        self._card_layout.removeWidget(self._viewport_container)
        self._viewport_container.setParent(container)
        layout.addWidget(self._viewport_container, 1)

        self._popout_window.setCentralWidget(container)
        self._dock_placeholder.setVisible(True)
        self._is_popped_out = True
        self.popout_btn.setText("↙ Yerleştir")
        self._popout_window.show()

    def _focus_popout(self):
        if self._popout_window:
            self._popout_window.raise_()
            self._popout_window.activateWindow()

    def _on_popout_closed(self):
        if self._is_popped_out:
            self._reclaim_viewport()

    def _reclaim_viewport(self):
        if self._popout_window is not None:
            central = self._popout_window.centralWidget()
            if central and central.layout():
                central.layout().removeWidget(self._viewport_container)
        self._viewport_container.setParent(self)
        self._dock_placeholder.setVisible(False)
        self._card_layout.insertWidget(1, self._viewport_container, 1)
        self._viewport_container.show()
        self._is_popped_out = False
        self.popout_btn.setText("⛶ Ayır")

    def dock_back(self):
        """Ayrılmış 3D pencereyi kapatıp görünümü dashboard kartına geri yerleştirir."""
        if not self._is_popped_out:
            return
        self._reclaim_viewport()
        if self._popout_window is not None:
            self._popout_window._closing_silently = True
            self._popout_window.close()
            self._popout_window.deleteLater()
            self._popout_window = None

    def close_popout(self):
        """Ana pencere kapanırken açık pop-out penceresini güvenle kapatır."""
        if self._popout_window is not None:
            self._popout_window._closing_silently = True
            self._popout_window.close()
            self._popout_window.deleteLater()
            self._popout_window = None
            self._is_popped_out = False
