"""Seed default field variables."""
from __future__ import annotations           # ← HARUS paling atas

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import datetime
from server.database import init_db, SessionLocal
from server.models import CustomVariable

DEFAULTS = [
    # === Desa/Dusun ===
    ("F-JEMBATAN-RUSAK", "Jembatan Rusak", "desa,dusun", "boolean", 0.7,
     "Jembatan penghubung antar dusun/desa dalam kondisi rusak"),
    ("F-BANJIR-LOKAL", "Banjir Lokal", "desa,dusun,kelurahan", "boolean", 0.8,
     "Banjir yang merendam pemukiman/lahan dalam 7 hari terakhir"),
    ("F-ALIH-FUNGSI-LAHAN", "Alih Fungsi Lahan", "desa,kecamatan", "boolean", 0.7,
     "Perubahan fungsi lahan signifikan (mis. sawah → kebun)"),
    ("F-ALIH-FUNGSI-HUTAN", "Alih Fungsi Hutan", "desa,kecamatan,kabupaten", "boolean", 0.9,
     "Deforestasi atau konversi hutan signifikan"),
    ("F-KEBUN-MONOKULTUR", "Kebun Monokultur Skala Besar", "desa", "boolean", 0.5,
     "Ekspansi perkebunan monokultur skala besar"),
    ("F-AKSES-JALAN-TERPUTUS", "Akses Jalan Terputus", "desa,dusun", "boolean", 0.7,
     "Jalan utama terputus/rusak berat"),
    ("F-PENGUNGSIAN", "Ada Pengungsian", "semua", "boolean", 0.95,
     "Terdapat pengungsian aktif di wilayah ini"),
    ("F-KONFLIK-LAHAN", "Konflik Lahan", "desa,kecamatan,kabupaten", "boolean", 0.8,
     "Konflik agraria / lahan aktif"),
    # === Kelurahan/Kota ===
    ("F-KEMACETAN-LOKAL", "Kemacetan Lokal", "kelurahan,kota", "scale", 0.5,
     "Tingkat kemacetan lokal (0=tidak ada, 1=sangat padat)"),
    ("F-BANJIR-URBAN", "Banjir Urban", "kelurahan,kota", "boolean", 0.8,
     "Banjir akibat drainase buruk"),
    ("F-SAMPAH-MENUMPUK", "Sampah Menumpuk", "kelurahan,kota,kecamatan", "boolean", 0.4,
     "Tumpukan sampah tidak terkelola"),
    ("F-PKL-LIAR", "PKL Liar", "kelurahan,kota", "boolean", 0.3,
     "PKL menempati area publik secara liar"),
    # === Semua Level ===
    ("F-BENCANA-ALAM", "Bencana Alam Terkini", "semua", "boolean", 0.95,
     "Bencana alam dalam 30 hari terakhir (gempa, longsor, dll)"),
    ("F-WABAH-PENYAKIT", "Wabah Penyakit", "semua", "boolean", 0.9,
     "Wabah penyakit menular aktif"),
    ("F-KRIMINALITAS", "Lonjakan Kriminalitas", "semua", "boolean", 0.7,
     "Peningkatan kriminalitas signifikan"),
    # === Kabupaten/Kota ===
    ("F-POLUSI-UDARA", "Polusi Udara", "kabupaten,kota,provinsi", "scale", 0.6,
     "Indeks kualitas udara buruk (0=baik, 1=sangat buruk)"),
    ("F-KEMARAU", "Kemarau Panjang", "kabupaten,kota,provinsi", "boolean", 0.7,
     "Kemarau berkepanjangan (BMKG)"),
    # === Ekonomi ===
    ("F-PABRIK-TUTUP", "Pabrik Tutup", "kabupaten,kota", "boolean", 0.8,
     "Penutupan pabrik/industri besar dalam 90 hari terakhir"),
    ("F-HARGA-PANGAN-NAIK", "Harga Pangan Melonjak", "semua", "scale", 0.6,
     "Kenaikan harga pangan pokok signifikan (0=tidak, 1=sangat)"),
    ("F-PH-KRITIS", "PHK Massal", "kabupaten,kota", "boolean", 0.85,
     "Pemutusan hubungan kerja massal di wilayah"),
]


def seed():
    init_db()
    db = SessionLocal()
    created = 0
    try:
        for kode, nama, targets, tipe, sev, desk in DEFAULTS:
            exists = db.query(CustomVariable).filter(CustomVariable.kode == kode).first()
            if exists:
                continue
            # Untuk level_target: kalau "semua", simpan "semua"; kalau multi, simpan CSV
            db.add(CustomVariable(
                kode=kode, nama=nama, deskripsi=desk,
                level_target=targets, tipe=tipe,
                severity_weight=sev,
                is_active=True,
                is_approved=True,
                created_by="system",
                approved_by="system",
                approved_at=datetime.utcnow(),
            ))
            created += 1
        db.commit()
        total = db.query(CustomVariable).count()
        print(f"✅ Seed: {created} baru, total {total} variabel field.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()