"""KPI Card widget - menampilkan metrik tunggal dengan warna kategori."""
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from client.gui.theme import COLORS, CATEGORY_COLORS


class KpiCard(QFrame):
    def __init__(self, title: str, value: str = "—", unit: str = "", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(f"""
            KpiCard {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        self.setMinimumHeight(110)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        self.title_lbl = QLabel(title.upper())
        self.title_lbl.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 10px; letter-spacing: 1px; font-weight: 600;"
        )

        self.value_lbl = QLabel(value)
        self.value_lbl.setStyleSheet(
            f"color: {COLORS['cyan']}; font-size: 26px; font-weight: 700;"
        )
        self.value_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.unit_lbl = QLabel(unit)
        self.unit_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")

        layout.addWidget(self.title_lbl)
        layout.addWidget(self.value_lbl)
        layout.addWidget(self.unit_lbl)

    def set_value(self, value: str, category: str | None = None):
        self.value_lbl.setText(value)
        if category and category in CATEGORY_COLORS:
            self.value_lbl.setStyleSheet(
                f"color: {CATEGORY_COLORS[category]}; font-size: 26px; font-weight: 700;"
            )
        else:
            self.value_lbl.setStyleSheet(
                f"color: {COLORS['cyan']}; font-size: 26px; font-weight: 700;"
            )

    def set_unit(self, unit: str):
        self.unit_lbl.setText(unit)