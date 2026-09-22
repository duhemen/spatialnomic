"""XAI Panel - menampilkan kontribusi variabel & narasi."""
from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QProgressBar
)
from PyQt6.QtCore import Qt
from client.gui.theme import COLORS, CATEGORY_COLORS


class XaiPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            XaiPanel {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
            }}
        """)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 14, 16, 14)
        self._layout.setSpacing(8)

        title = QLabel("🧠 Penjelasan AI (XAI)")
        title.setStyleSheet(f"color: {COLORS['cyan']}; font-weight: 700; font-size: 13px;")
        self._layout.addWidget(title)

        self._narrative = QLabel("Belum ada analisis. Hitung UERI dulu.")
        self._narrative.setWordWrap(True)
        self._narrative.setStyleSheet(f"color: {COLORS['text']}; font-size: 11px; line-height: 1.5;")
        self._layout.addWidget(self._narrative)

        self._bars_container = QVBoxLayout()
        self._layout.addLayout(self._bars_container)
        self._bars_container.addStretch()

    def update_explanation(self, exp: dict):
        """exp = hasil dari endpoint /ueri/explain."""
        self._narrative.setText(exp.get("narrative", "—").replace("**", ""))

        # Clear bars
        while self._bars_container.count() > 1:
            item = self._bars_container.takeAt(0)
            w = item.widget()
            if w: w.deleteLater()

        for d in exp.get("top_drivers", []):
            row = QWidget()
            rl = QVBoxLayout(row)
            rl.setContentsMargins(0, 4, 0, 4)
            rl.setSpacing(2)

            lbl = QLabel(f"{d['var']} — {d['label']}")
            lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: 11px; font-weight: 600;")
            rl.addWidget(lbl)

            bar = QProgressBar()
            bar.setRange(0, 100)
            val = min(100, int(abs(d['contribution']) * 200))
            bar.setValue(val)
            bar.setTextVisible(False)
            bar.setFixedHeight(6)
            color = COLORS['red'] if d['contribution'] > 0 else COLORS['green']
            bar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: {COLORS['bg_panel']};
                    border-radius: 3px;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                    border-radius: 3px;
                }}
            """)
            rl.addWidget(bar)

            info = QLabel(f"kontribusi {d['contribution']:+.3f} · nilai {d['value']:.2f} · arah: {d['direction']}")
            info.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px;")
            rl.addWidget(info)

            self._bars_container.insertWidget(self._bars_container.count() - 1, row)