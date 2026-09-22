"""Tab Laporan Lapangan — petugas input field observations."""
from __future__ import annotations
import uuid
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QTextEdit, QDoubleSpinBox, QGroupBox, QMessageBox, QListWidget,
    QListWidgetItem, QSplitter, QFormLayout, QLineEdit, QDialog,
    QDialogButtonBox, QCheckBox, QFrame
)
from PyQt6.QtCore import Qt
from loguru import logger

from client.api.client import SpatiaNomicsClient
from client.gui.theme import COLORS


class FieldReportTab(QWidget):
    def __init__(self, api: SpatiaNomicsClient, parent=None):
        super().__init__(parent)
        self.api = api
        self._selected_var: dict | None = None
        self._build_ui()
        self._load_variables()

    # ============================================================
    # BUILD UI
    # ============================================================
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        # Header
        title = QLabel("📝  Laporan Lapangan")
        title.setObjectName("Title")
        root.addWidget(title)

        sub = QLabel(
            "Input temuan lapangan. Laporan diverifikasi supervisor sebelum masuk perhitungan composite score."
        )
        sub.setObjectName("Subtitle")
        sub.setWordWrap(True)
        root.addWidget(sub)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ========== KIRI: Variabel ==========
        left = QGroupBox("📋 Variabel Tersedia")
        left_lay = QVBoxLayout(left)
        left_lay.setSpacing(10)

        # Filter level
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Level:"))
        self.level_combo = QComboBox()
        self.level_combo.addItems([
            "desa", "dusun", "kelurahan", "kecamatan", "kabupaten", "kota", "provinsi"
        ])
        self.level_combo.currentTextChanged.connect(self._load_variables)
        filter_row.addWidget(self.level_combo, stretch=1)

        self.btn_refresh = QPushButton("🔄")
        self.btn_refresh.setFixedWidth(40)
        self.btn_refresh.clicked.connect(self._load_variables)
        filter_row.addWidget(self.btn_refresh)
        left_lay.addLayout(filter_row)

        # List variabel dengan checkbox
        self.var_list = QListWidget()
        self.var_list.itemClicked.connect(self._on_var_selected)
        left_lay.addWidget(self.var_list, stretch=1)

        # Tombol tambah variabel
        self.btn_new_var = QPushButton("➕  Tambah Variabel Baru")
        self.btn_new_var.clicked.connect(self._open_new_var_dialog)
        left_lay.addWidget(self.btn_new_var)

        splitter.addWidget(left)

        # ========== KANAN: Form ==========
        right = QGroupBox("📝 Detail Laporan")
        right_lay = QVBoxLayout(right)
        right_lay.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.wilayah_input = QLineEdit()
        self.wilayah_input.setPlaceholderText("Contoh: 11.01.01.2001")
        form.addRow("Kode Wilayah:", self.wilayah_input)

        self.var_label = QLabel("— belum dipilih —")
        self.var_label.setStyleSheet(
            f"color: {COLORS['cyan']}; font-weight: 600; padding: 4px 8px;"
            f"background-color: {COLORS['bg_panel']}; border-radius: 4px;"
        )
        form.addRow("Variabel:", self.var_label)

        self.nilai_spin = QDoubleSpinBox()
        self.nilai_spin.setRange(0.0, 1.0)
        self.nilai_spin.setSingleStep(0.1)
        self.nilai_spin.setValue(1.0)
        self.nilai_spin.setDecimals(2)
        form.addRow("Nilai (0–1):", self.nilai_spin)

        self.catatan_edit = QTextEdit()
        self.catatan_edit.setPlaceholderText("Catatan tambahan, kronologi, atau konteks lapangan...")
        self.catatan_edit.setMaximumHeight(100)
        form.addRow("Catatan:", self.catatan_edit)

        coord_lay = QHBoxLayout()
        self.lat_input = QLineEdit()
        self.lat_input.setPlaceholderText("Auto / manual")
        self.lng_input = QLineEdit()
        self.lng_input.setPlaceholderText("Auto / manual")
        coord_lay.addWidget(QLabel("Lat:"))
        coord_lay.addWidget(self.lat_input, stretch=1)
        coord_lay.addWidget(QLabel("Lng:"))
        coord_lay.addWidget(self.lng_input, stretch=1)
        form.addRow("Koordinat:", coord_lay)

        self.observer_input = QLineEdit("petugas")
        form.addRow("Observer:", self.observer_input)

        right_lay.addLayout(form)
        right_lay.addStretch()

        # Submit button
        self.btn_submit = QPushButton("📤  Kirim Laporan")
        self.btn_submit.setObjectName("Primary")
        self.btn_submit.setMinimumHeight(42)
        self.btn_submit.clicked.connect(self._submit)
        right_lay.addWidget(self.btn_submit)

        splitter.addWidget(right)
        splitter.setSizes([400, 600])

        root.addWidget(splitter, stretch=1)

        # Status
        self.status_lbl = QLabel("Siap.")
        self.status_lbl.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 11px; padding: 4px;"
        )
        root.addWidget(self.status_lbl)

    # ============================================================
    # LOAD VARIABLES (dengan checkbox style)
    # ============================================================
    def _load_variables(self):
        level = self.level_combo.currentText()
        try:
            vars = self.api.list_custom_variables(level=level, approved_only=True)
            self.var_list.clear()
            for v in vars:
                sev = v.get("severity_weight", 0.5)
                if sev >= 0.85:
                    icon, color = "🔴", "#EF4444"
                elif sev >= 0.6:
                    icon, color = "🟡", "#FACC15"
                else:
                    icon, color = "🟢", "#4ADE80"

                item = QListWidgetItem(f"{icon}  {v['nama']}")
                item.setData(Qt.ItemDataRole.UserRole, v)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
                item.setToolTip(
                    f"Kode: {v['kode']}\n"
                    f"Tipe: {v['tipe']}\n"
                    f"Severity: {sev:.2f}\n"
                    f"{v.get('deskripsi', '')}"
                )
                self.var_list.addItem(item)
            self.status_lbl.setText(
                f"✅ {len(vars)} variabel tersedia untuk level '{level}'."
            )
        except Exception as e:
            self.status_lbl.setText(f"❌ Gagal load variabel: {e}")
            logger.error(f"load_variables: {e}")

    def _on_var_selected(self, item: QListWidgetItem):
        var = item.data(Qt.ItemDataRole.UserRole)
        self._selected_var = var
        self.var_label.setText(f"{var['nama']}   [{var['kode']}]")
        self.nilai_spin.setValue(1.0 if var.get("tipe") == "boolean" else 0.5)
        self.status_lbl.setText(
            f"Terpilih: {var['nama']} | severity={var['severity_weight']:.2f} | tipe={var['tipe']}"
        )

    # ============================================================
    # DIALOG: Tambah Variabel
    # ============================================================
    def _open_new_var_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Tambah Variabel Baru")
        dlg.resize(480, 420)
        lay = QVBoxLayout(dlg)
        lay.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)

        kode_in = QLineEdit("F-")
        nama_in = QLineEdit()
        desc_in = QTextEdit()
        desc_in.setMaximumHeight(70)
        level_in = QComboBox()
        level_in.addItems(["semua", "desa", "dusun", "kelurahan",
                            "kecamatan", "kabupaten", "kota", "provinsi"])
        level_in.setCurrentText("desa")
        tipe_in = QComboBox()
        tipe_in.addItems(["boolean", "scale", "count"])
        sev_in = QDoubleSpinBox()
        sev_in.setRange(0, 1)
        sev_in.setSingleStep(0.05)
        sev_in.setValue(0.5)

        form.addRow("Kode:", kode_in)
        form.addRow("Nama:", nama_in)
        form.addRow("Deskripsi:", desc_in)
        form.addRow("Level Target:", level_in)
        form.addRow("Tipe:", tipe_in)
        form.addRow("Severity (0–1):", sev_in)
        lay.addLayout(form)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        lay.addWidget(btns)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            payload = {
                "kode": kode_in.text().strip(),
                "nama": nama_in.text().strip(),
                "deskripsi": desc_in.toPlainText().strip(),
                "level_target": level_in.currentText(),
                "tipe": tipe_in.currentText(),
                "severity_weight": sev_in.value(),
                "created_by": self.observer_input.text() or "petugas",
            }
            if not payload["kode"] or not payload["nama"]:
                QMessageBox.warning(self, "Error", "Kode & nama wajib diisi")
                return
            try:
                self.api.create_custom_variable(payload)
                QMessageBox.information(
                    self, "Sukses",
                    "Variabel dibuat. Menunggu approval supervisor."
                )
                self._load_variables()
            except Exception as e:
                QMessageBox.critical(self, "Gagal", str(e))

    # ============================================================
    # SUBMIT
    # ============================================================
    def _submit(self):
        if not self._selected_var:
            QMessageBox.information(self, "Info", "Pilih variabel dulu di panel kiri.")
            return
        kode_wil = self.wilayah_input.text().strip().replace(".", "")
        if not kode_wil:
            QMessageBox.information(self, "Info", "Isi kode wilayah.")
            return

        def _f(s):
            try:
                return float(s) if s.strip() else None
            except ValueError:
                return None

        payload = {
            "wilayah_kode": kode_wil,
            "variable_kode": self._selected_var["kode"],
            "nilai": self.nilai_spin.value(),
            "catatan": self.catatan_edit.toPlainText().strip() or None,
            "latitude": _f(self.lat_input.text()),
            "longitude": _f(self.lng_input.text()),
            "observer": self.observer_input.text() or "petugas",
            "local_uuid": str(uuid.uuid4()),
        }
        try:
            self.api.create_field_observation(payload)
            self.status_lbl.setText(
                f"✅ Terkirim: {self._selected_var['nama']} @ {kode_wil}"
            )
            self.catatan_edit.clear()
        except Exception:
            from client.core import offline_cache
            offline_cache.enqueue(payload)
            self.status_lbl.setText(
                "📥 Server offline. Laporan disimpan lokal, akan disync otomatis."
            )
        self.catatan_edit.clear()