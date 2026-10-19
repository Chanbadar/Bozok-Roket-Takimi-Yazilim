"""
Bozok Roket Takımı - Yer İstasyonu Arayüzü
Başlatma Dosyası (Application Entry Point)
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from ui.main_window import MainWindow


def main():
    # Yüksek DPI ekranlar için optimizasyon
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Bozok Roket Takımı - Yer İstasyonu")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
