"""
Bozok Roket Takımı - Yer İstasyonu Arayüzü
Başlatma Dosyası (Application Entry Point)
"""

import os
import sys

# Proje ve telemetry dizinini sys.path'e ekle (core ve ui modüllerinin bulunabilmesi için)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TELEMETRY_DIR = os.path.join(BASE_DIR, "telemetry")

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if TELEMETRY_DIR not in sys.path:
    sys.path.insert(0, TELEMETRY_DIR)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from ui.main_window import MainWindow


def main():
    # QtWebEngine (3D Three.js + Harita) ve Pop-out pencere geçişleri için OpenGL bağlam paylaşımı
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

    # Yüksek DPI ekranlar için optimizasyon
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("BOZALP - Yer İstasyonu")

    logo_path = os.path.join(BASE_DIR, "assets", "bozalp_logo.jpeg")
    if os.path.isfile(logo_path):
        app.setWindowIcon(QIcon(logo_path))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
