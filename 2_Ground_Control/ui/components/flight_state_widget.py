"""
Bozok Roket Takımı - Uçuş Durum Çubuğu (Flight State Machine Indicator)
Roketin uçuş aşamalarını (Rampa, Ateşleme, Tırmanma, Drog, Ayrılma, Ana Paraşüt, İniş) canlı gösterir.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget
)


STAGES = [
    ("RAMPA", "Rampa Bekleme"),
    ("MOTOR", "Motor Yanışı"),
    ("TIRMANMA", "Serbest Tırmanış"),
    ("DROG", "1. Paraşüt (Drog)"),
    ("AYRILMA", "Görev Yükü Ayrıldı"),
    ("ANA", "2. Paraşüt (Ana)"),
    ("İNİŞ", "Kurtarma / İniş")
]


class FlightStateWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("FlightStateWidget")
        self.setStyleSheet(
            "background-color: #0F172A; border: 1px solid #1E293B; border-radius: 8px; padding: 6px;"
        )
        self.stage_boxes = []
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        title = QLabel("UÇUŞ DURUMU:")
        title.setStyleSheet("font-weight: 800; font-size: 11px; color: #94A3B8; letter-spacing: 0.5px;")
        layout.addWidget(title)

        for key, name in STAGES:
            box = QLabel(f"○ {key}")
            box.setAlignment(Qt.AlignmentFlag.AlignCenter)
            box.setToolTip(name)
            box.setStyleSheet(
                "background-color: #131C31; color: #64748B; border: 1px solid #1E293B; "
                "border-radius: 4px; padding: 4px 10px; font-weight: 700; font-size: 11px;"
            )
            layout.addWidget(box)
            self.stage_boxes.append((key, box))

        layout.addStretch()

    def set_state(self, current_state: str):
        """Aktif uçuş fazına göre butonların renklerini günceller."""
        state_map = {
            "RAMPA_BEKLEME": 0,
            "MOTOR_YANISI": 1,
            "TIRMANMA": 2,
            "APOGEE": 3,
            "DROG_PARASUT": 3,
            "GOREV_YUKU_AYRILDI": 4,
            "GOREV_YUKU_AYRILMA": 4,
            "ANA_PARASUT": 5,
            "KURTARMA_INIS": 6,
            "INIS": 6
        }

        active_idx = state_map.get(current_state, 0)

        for i, (key, box) in enumerate(self.stage_boxes):
            if i < active_idx:
                # Tamamlanan aşamalar (Yeşil onay)
                box.setText(f"✓ {key}")
                box.setStyleSheet(
                    "background-color: #064E3B; color: #34D399; border: 1px solid #059669; "
                    "border-radius: 4px; padding: 4px 10px; font-weight: 700; font-size: 11px;"
                )
            elif i == active_idx:
                # Aktif aşama (Parlayan Neon Mavi / Turkuaz)
                box.setText(f"● {key}")
                box.setStyleSheet(
                    "background-color: #0369A1; color: #FFFFFF; border: 2px solid #38BDF8; "
                    "border-radius: 4px; padding: 4px 10px; font-weight: 800; font-size: 11px;"
                )
            else:
                # Gelecek aşamalar (Koyu gri)
                box.setText(f"○ {key}")
                box.setStyleSheet(
                    "background-color: #131C31; color: #64748B; border: 1px solid #1E293B; "
                    "border-radius: 4px; padding: 4px 10px; font-weight: 700; font-size: 11px;"
                )
