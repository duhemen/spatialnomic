"""Dashboard Tab - KPI + perhitungan UERI interaktif."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QDoubleSpinBox, QGroupBox, QMessageBox,
)
from client.gui.widgets.kpi_card import KpiCard
from client.api.client import SpatiaNomicsClient
from client.gui.theme import COLORS, CATEGORY_COLORS

from client.gui.tabs.xai_panel import XaiPanel

VARS = ["USAI", "LLI", "IAI", "PEI", "ZCEI", "FSI", "UOTI", "ISI"]
VAR_LABELS = {
    "USAI": "Urban Space Availability",
    "LLI":  "Local Liquidity",
    "IAI":  "Infrastructure Access",
    "PEI":  "Productivity & Employment",
    "ZCEI": "Zoning & Capital Expenditure",
    "FSI":  "Fiscal Stimulus",
    "UOTI": "Urban Overcrowding & Traffic",
    "ISI":  "Inflation Shock",
}


class DashboardTab(QWidget):
    def __init__(self, api: SpatiaNomicsClient, parent=None):
        super().__init__(parent)
        self.api = api
        self.xai_panel = XaiPanel()
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)
        self.xai_panel.setMinimumHeight(180)
        self.xai_panel.setMaximumHeight(280)
        root.addWidget(self.xai_panel)

        # Header
        header = QLabel("🏙️ Dashboard UERI — Urban-Economic Risk Index")
        header.setObjectName("Title")
        root.addWidget(header)

        sub = QLabel("Hitung indeks risiko spasial-ekonomi secara real-time.")
        sub.setObjectName("Subtitle")
        root.addWidget(sub)

        # KPI Row
        kpi_row = QHBoxLayout()
        self.kpi_ueri = KpiCard("UERI Score", "—", "/ 1.00")
        self.kpi_cat = KpiCard("Kategori", "—")
        self.kpi_status = KpiCard("Server", "…", "")
        kpi_row.addWidget(self.kpi_ueri)
        kpi_row.addWidget(self.kpi_cat)
        kpi_row.addWidget(self.kpi_status)
        root.addLayout(kpi_row)

        # Input Group
        grp = QGroupBox("Input Variabel (0.0 – 1.0)")
        grid = QGridLayout(grp)
        grid.setSpacing(10)
        self.inputs: dict[str, QDoubleSpinBox] = {}

        for i, var in enumerate(VARS):
            row, col = divmod(i, 2)
            lbl = QLabel(f"{var} — {VAR_LABELS[var]}")
            lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: 12px;")
            spin = QDoubleSpinBox()
            spin.setRange(0.0, 1.0)
            spin.setSingleStep(0.05)
            spin.setDecimals(2)
            spin.setValue(0.5)
            self.inputs[var] = spin
            grid.addWidget(lbl, row, col * 2)
            grid.addWidget(spin, row, col * 2 + 1)

        root.addWidget(grp)

        # Buttons
        btns = QHBoxLayout()
        self.btn_calc = QPushButton("⚡ Hitung UERI")
        self.btn_calc.setObjectName("Primary")
        self.btn_calc.clicked.connect(self._calculate)
        self.btn_reset = QPushButton("🔄 Reset 0.5")
        self.btn_reset.clicked.connect(self._reset)
        btns.addWidget(self.btn_calc)
        btns.addWidget(self.btn_reset)
        btns.addStretch()
        root.addLayout(btns)

        root.addStretch()

        # Cek server
        self._check_server()

    def _check_server(self):
        try:
            h = self.api.health()
            self.kpi_status.set_value("ONLINE", "AMAN")
            self.kpi_status.set_unit(h.get("version", ""))
        except Exception as e:
            self.kpi_status.set_value("OFFLINE", "BAHAYA")
            self.kpi_status.set_unit(str(e)[:60])

    def _reset(self):
        for spin in self.inputs.values():
            spin.setValue(0.5)

    def _calculate(self):
        payload = {
            "wilayah_kode": "DEMO-001",
            **{k: w.value() for k, w in self.inputs.items()},
        }
        try:
            res = self.api.calculate_ueri(payload)
            ueri = res["ueri"]; cat = res["category"]
            self.kpi_ueri.set_value(f"{ueri:.3f}", cat)
            self.kpi_cat.set_value(cat, cat)

            # Panggil XAI
            exp = self.api.explain_ueri(payload)
            self.xai_panel.update_explanation(exp)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal menghitung UERI:\n{e}")