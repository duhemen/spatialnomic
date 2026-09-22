"""Tab Verifikasi Laporan — untuk supervisor."""
from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QInputDialog,
    QComboBox, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from loguru import logger

from client.api.client import SpatiaNomicsClient
from client.gui.theme import COLORS


class VerifyTab(QWidget):
    def __init__(self, api: SpatiaNomicsClient, parent=None):
        super().__init__(parent)
        self.api = api
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        # Header
        title = QLabel("✅  Verifikasi Laporan Lapangan")
        title.setObjectName("Title")
        root.addWidget(title)

        sub = QLabel(
            "Hanya laporan yang diverifikasi yang masuk ke perhitungan composite score."
        )
        sub.setObjectName("Subtitle")
        root.addWidget(sub)

        # Toolbar
        bar = QHBoxLayout()
        bar.addWidget(QLabel("Filter:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Semua", "Pending", "Verified", "Ditolak"])
        self.filter_combo.currentTextChanged.connect(self._refresh)
        bar.addWidget(self.filter_combo)

        bar.addStretch()

        self.btn_refresh = QPushButton("🔄  Refresh")
        self.btn_refresh.clicked.connect(self._refresh)
        bar.addWidget(self.btn_refresh)
        root.addLayout(bar)

        # Table
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Wilayah", "Variabel", "Nilai", "Observer", "Status"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        root.addWidget(self.table, stretch=1)

        # Action buttons
        btns = QHBoxLayout()
        btns.addStretch()
        self.btn_verify = QPushButton("✅  Verifikasi")
        self.btn_verify.setObjectName("Primary")
        self.btn_verify.setMinimumHeight(38)
        self.btn_verify.clicked.connect(lambda: self._decide(True))
        btns.addWidget(self.btn_verify)

        self.btn_reject = QPushButton("❌  Tolak")
        self.btn_reject.setMinimumHeight(38)
        self.btn_reject.clicked.connect(lambda: self._decide(False))
        btns.addWidget(self.btn_reject)
        root.addLayout(btns)

        # Status
        self.status = QLabel("")
        self.status.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 11px; padding: 4px;"
        )
        root.addWidget(self.status)

    def _refresh(self):
        try:
            rows = self.api.list_field_observations(verified_only=False)
            filter_txt = self.filter_combo.currentText()

            self.table.setRowCount(0)
            for r in rows:
                status = ("✅ Verified" if r.get("verified")
                          else "❌ Ditolak" if r.get("rejected")
                          else "⏳ Pending")

                # Filter
                if filter_txt == "Pending" and r.get("verified") or r.get("rejected"):
                    continue
                if filter_txt == "Verified" and not r.get("verified"):
                    continue
                if filter_txt == "Ditolak" and not r.get("rejected"):
                    continue

                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(r["id"])))
                self.table.setItem(row, 1, QTableWidgetItem(r["wilayah_kode"]))
                self.table.setItem(row, 2, QTableWidgetItem(r["variable_kode"]))
                self.table.setItem(row, 3, QTableWidgetItem(f"{r['nilai']:.2f}"))
                self.table.setItem(row, 4, QTableWidgetItem(r.get("observer") or "-"))

                status_item = QTableWidgetItem(status)
                if r.get("verified"):
                    status_item.setForeground(QColor("#4ADE80"))
                elif r.get("rejected"):
                    status_item.setForeground(QColor("#EF4444"))
                else:
                    status_item.setForeground(QColor("#FACC15"))
                self.table.setItem(row, 5, status_item)

            self.status.setText(f"{self.table.rowCount()} laporan ditampilkan.")
        except Exception as e:
            self.status.setText(f"❌ {e}")
            logger.error(f"refresh: {e}")

    def _decide(self, verified: bool):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Info", "Pilih baris dulu.")
            return
        obs_id = int(self.table.item(row, 0).text())

        reason = None
        if not verified:
            reason, ok = QInputDialog.getText(self, "Alasan Penolakan", "Alasan:")
            if not ok:
                return

        try:
            self.api.verify_field_observation(
                obs_id, verified, verified_by="supervisor", reason=reason
            )
            self._refresh()
        except Exception as e:
            QMessageBox.critical(self, "Gagal", str(e))