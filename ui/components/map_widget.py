"""
Bozok Roket Takımı - Canlı Harita ve GPS Takip Bileşeni
Fotoğraftaki gibi roket ve görev yükünün harita üzerindeki anlık konumunu ve uçuş rotasını gösterir.
QtWebEngine (Leaflet) mevcutsa etkileşimli OpenStreetMap haritası, değilse yüksek performanslı 2D Taktik Radar haritası kullanır.
"""

import math
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget
)

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False


class FallbackRadarMap(QWidget):
    """WebEngine olmadığında veya çevrimdışı durumda çalışan 2D GPS Taktik Haritası."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(280, 280)
        self.base_lat = 38.3687
        self.base_lng = 34.0370
        self.rocket_lat = 38.3687
        self.rocket_lng = 34.0370
        self.payload_lat = 38.3687
        self.payload_lng = 34.0370
        self.rocket_trail = []
        self.payload_trail = []
        self.zoom = 50000.0  # Derece başına piksel ölçeği

    def update_coordinates(self, r_lat: float, r_lng: float, p_lat: float, p_lng: float):
        self.rocket_lat = r_lat
        self.rocket_lng = r_lng
        self.payload_lat = p_lat
        self.payload_lng = p_lng

        if len(self.rocket_trail) == 0 or (abs(self.rocket_trail[-1][0] - r_lat) > 0.00002 or abs(self.rocket_trail[-1][1] - r_lng) > 0.00002):
            self.rocket_trail.append((r_lat, r_lng))
            if len(self.rocket_trail) > 400:
                self.rocket_trail.pop(0)

        if len(self.payload_trail) == 0 or (abs(self.payload_trail[-1][0] - p_lat) > 0.00002 or abs(self.payload_trail[-1][1] - p_lng) > 0.00002):
            self.payload_trail.append((p_lat, p_lng))
            if len(self.payload_trail) > 400:
                self.payload_trail.pop(0)

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2
        cy = h / 2

        # Arka plan
        painter.fillRect(0, 0, w, h, QColor("#0B132B"))

        # Radar Grid Çemberleri
        painter.setPen(QPen(QColor("#1C2A4A"), 1, Qt.PenStyle.DashLine))
        for r in [40, 80, 120, 160, 200]:
            painter.drawEllipse(QPointF(cx, cy), r, r)

        # Eksen Çizgileri
        painter.setPen(QPen(QColor("#1C2A4A"), 1))
        painter.drawLine(int(cx), 0, int(cx), h)
        painter.drawLine(0, int(cy), w, int(cy))

        # Yön Göstergeleri (K-G-D-B)
        painter.setPen(QColor("#64748B"))
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        painter.drawText(int(cx - 5), 18, "K")
        painter.drawText(int(cx - 5), h - 8, "G")
        painter.drawText(w - 18, int(cy + 4), "D")
        painter.drawText(8, int(cy + 4), "B")

        # Koordinat Dönüşümü
        def to_screen(lat, lng):
            x = cx + (lng - self.base_lng) * self.zoom
            y = cy - (lat - self.base_lat) * self.zoom
            return QPointF(x, y)

        # Fırlatma Rampası İkonu
        pad_pt = to_screen(self.base_lat, self.base_lng)
        painter.setBrush(QBrush(QColor("#64748B")))
        painter.setPen(QPen(QColor("#94A3B8"), 1))
        painter.drawRect(int(pad_pt.x() - 5), int(pad_pt.y() - 5), 10, 10)
        painter.drawText(int(pad_pt.x() + 8), int(pad_pt.y() + 4), "RAMPA")

        # Roket Rotası (Trail)
        if len(self.rocket_trail) > 1:
            painter.setPen(QPen(QColor("#00F0FF"), 2))
            for i in range(len(self.rocket_trail) - 1):
                p1 = to_screen(*self.rocket_trail[i])
                p2 = to_screen(*self.rocket_trail[i + 1])
                painter.drawLine(p1, p2)

        # Görev Yükü Rotası (Trail)
        if len(self.payload_trail) > 1:
            painter.setPen(QPen(QColor("#FF6B4A"), 2, Qt.PenStyle.DashLine))
            for i in range(len(self.payload_trail) - 1):
                p1 = to_screen(*self.payload_trail[i])
                p2 = to_screen(*self.payload_trail[i + 1])
                painter.drawLine(p1, p2)

        # Roket Anlık Konumu (Cyan Marker)
        r_pt = to_screen(self.rocket_lat, self.rocket_lng)
        painter.setBrush(QBrush(QColor("#00F0FF")))
        painter.setPen(QPen(QColor("#FFFFFF"), 2))
        painter.drawEllipse(r_pt, 7, 7)
        painter.setPen(QColor("#00F0FF"))
        painter.drawText(int(r_pt.x() + 10), int(r_pt.y() + 4), "ROKET")

        # Görev Yükü Anlık Konumu (Orange Marker)
        p_pt = to_screen(self.payload_lat, self.payload_lng)
        painter.setBrush(QBrush(QColor("#FF6B4A")))
        painter.setPen(QPen(QColor("#FFFFFF"), 2))
        painter.drawEllipse(p_pt, 6, 6)
        painter.setPen(QColor("#FF6B4A"))
        painter.drawText(int(p_pt.x() + 10), int(p_pt.y() + 4), "GÖREV YÜKÜ")

        # Mesafe Bilgisi (Rampaya Olan Uzaklık)
        dx = (self.rocket_lng - self.base_lng) * 111320.0 * math.cos(math.radians(self.base_lat))
        dy = (self.rocket_lat - self.base_lat) * 110540.0
        dist = math.sqrt(dx**2 + dy**2)

        painter.setPen(QColor("#F8FAFC"))
        painter.drawText(12, h - 14, f"Rampa Mesafesi: {dist:.1f} m")


class MapWidget(QFrame):
    """Canlı Harita Bileşeni."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "TeleCard")
        self.setObjectName("MapPanel")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        # Başlık
        header_layout = QHBoxLayout()
        map_title = QLabel("🗺️ CANLI GPS HARİTASI")
        map_title.setStyleSheet("font-size: 14px; font-weight: 800; color: #38BDF8; letter-spacing: 0.5px;")
        header_layout.addWidget(map_title)
        header_layout.addStretch()

        self.coords_label = QLabel("Lat: -- | Lng: --")
        self.coords_label.setStyleSheet("color: #94A3B8; font-size: 11px; font-family: monospace;")
        header_layout.addWidget(self.coords_label)
        layout.addLayout(header_layout)

        # Harita Görünümü
        if WEBENGINE_AVAILABLE:
            self.web_view = QWebEngineView()
            self._load_leaflet_map()
            layout.addWidget(self.web_view)
            self.radar_view = None
        else:
            self.radar_view = FallbackRadarMap()
            layout.addWidget(self.radar_view)
            self.web_view = None

    def _load_leaflet_map(self):
        """Etkileşimli Leaflet HTML sayfasını yükler."""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8" />
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
            <style>
                body, html, #map { margin: 0; padding: 0; width: 100%; height: 100%; background: #0F172A; }
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                var map = L.map('map').setView([38.3687, 34.0370], 14);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    maxZoom: 19,
                    attribution: 'OpenStreetMap'
                }).addTo(map);

                var rocketMarker = L.circleMarker([38.3687, 34.0370], {
                    color: '#00F0FF', fillColor: '#00F0FF', fillOpacity: 0.9, radius: 8
                }).addTo(map).bindPopup("<b>ROKET</b>");

                var payloadMarker = L.circleMarker([38.3687, 34.0370], {
                    color: '#FF6B4A', fillColor: '#FF6B4A', fillOpacity: 0.9, radius: 7
                }).addTo(map).bindPopup("<b>GÖREV YÜKÜ</b>");

                var rocketPath = L.polyline([], {color: '#00F0FF', weight: 3}).addTo(map);
                var payloadPath = L.polyline([], {color: '#FF6B4A', weight: 2, dashArray: '4, 4'}).addTo(map);

                function updatePositions(rLat, rLng, pLat, pLng) {
                    var rLatLng = [rLat, rLng];
                    var pLatLng = [pLat, pLng];
                    rocketMarker.setLatLng(rLatLng);
                    payloadMarker.setLatLng(pLatLng);
                    rocketPath.addLatLng(rLatLng);
                    payloadPath.addLatLng(pLatLng);
                }
            </script>
        </body>
        </html>
        """
        self.web_view.setHtml(html_content)

    def update_gps(self, r_lat: float, r_lng: float, p_lat: float, p_lng: float):
        self.coords_label.setText(f"R: {r_lat:.5f}, {r_lng:.5f} | GY: {p_lat:.5f}, {p_lng:.5f}")

        if self.web_view:
            js_call = f"if (typeof updatePositions === 'function') updatePositions({r_lat}, {r_lng}, {p_lat}, {p_lng});"
            self.web_view.page().runJavaScript(js_call)
        elif self.radar_view:
            self.radar_view.update_coordinates(r_lat, r_lng, p_lat, p_lng)
