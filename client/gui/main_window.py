"""Main Window PyQt6 - SpatiaNomics Client (Data Entry Mode)."""
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QStatusBar, QLabel, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QDesktopServices
from client.api.client import SpatiaNomicsClient
from client.gui.theme import get_stylesheet, COLORS
from client.gui.tabs.dashboard_tab import DashboardTab
from client.gui.tabs.field_report_tab import FieldReportTab
from client.gui.tabs.verify_tab import VerifyTab
from client.core import offline_cache


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SpatiaNomics — Petugas Lapangan")
        self.resize(1200, 780)
        self.setStyleSheet(get_stylesheet())

        self.api = SpatiaNomicsClient()

        # Central widget
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        # ============ Top bar dengan tombol "Buka Dashboard Web" ============
        topbar = QFrame()
        topbar.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_panel']};
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)
        topbar_lay = QHBoxLayout(topbar)
        topbar_lay.setContentsMargins(16, 10, 16, 10)

        app_title = QLabel("📡  SpatiaNomics · Petugas Lapangan")
        app_title.setStyleSheet(
            f"color: {COLORS['cyan']}; font-size: 15px; font-weight: 700;"
        )
        topbar_lay.addWidget(app_title)
        topbar_lay.addStretch()

        self.btn_web = QPushButton("🌐  Buka Dashboard Web")
        self.btn_web.setObjectName("Primary")
        self.btn_web.setToolTip("Buka dashboard publik di browser (peta, prediksi, laporan)")
        self.btn_web.clicked.connect(self._open_web_dashboard)
        topbar_lay.addWidget(self.btn_web)

        layout.addWidget(topbar)

        # ============ Tabs (hanya 3 tab!) ============
        self.tabs = QTabWidget()
        self.tabs.addTab(DashboardTab(self.api), "🏙️  Dashboard")
        self.tabs.addTab(FieldReportTab(self.api), "📝  Laporan Lapangan")
        self.tabs.addTab(VerifyTab(self.api), "✅  Verifikasi")
        layout.addWidget(self.tabs, stretch=1)

        self.setCentralWidget(central)

        # Status bar
        sb = QStatusBar()
        sb.showMessage("Siap.")
        self.setStatusBar(sb)

        # Timer ping server
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._ping)
        self.timer.start(15000)

        # Timer auto-sync offline cache
        self.sync_timer = QTimer(self)
        self.sync_timer.timeout.connect(self._try_sync)
        self.sync_timer.start(60000)

    # ============================================================
    # Handlers
    # ============================================================
    def _open_web_dashboard(self):
        """Buka dashboard web di browser default."""
        # Ganti URL ini dengan URL server setelah deploy ke Cloudflare Tunnel
        url = "http://localhost:8000/dashboard"
        QDesktopServices.openUrl(QUrl(url))

    def _ping(self):
        try:
            self.api.health()
            self.statusBar().showMessage("🟢 Server online")
        except Exception:
            self.statusBar().showMessage("🔴 Server offline")

    def _try_sync(self):
        """Sync laporan offline ke server."""
        try:
            n = offline_cache.sync_all(self.api)
            if n:
                self.statusBar().showMessage(f"🔄 {n} laporan offline disync")
        except Exception:
            pass

    def closeEvent(self, event):
        self.api.close()
        super().closeEvent(event)