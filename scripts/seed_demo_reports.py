"""Seed data laporan lapangan demo untuk testing UI."""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import random
from datetime import datetime, timedelta
from server.database import init_db, SessionLocal
from server.models import FieldObservation, CustomVariable, Wilayah


def seed(n: int = 15):
    init_db()
    db = SessionLocal()
    try:
        # Ambil sample variabel
        vars = db.query(CustomVariable).filter(
            CustomVariable.is_approved == True
        ).limit(10).all()
        if not vars:
            print("❌ Tidak ada custom_variable. Jalankan seed_field_variables.py dulu.")
            return

        # Ambil sample wilayah desa
        wilayahs = db.query(Wilayah).filter(
            Wilayah.level == "desa"
        ).limit(50).all()
        if not wilayahs:
            print("❌ Tidak ada wilayah desa.")
            return

        created = 0
        for i in range(n):
            var = random.choice(vars)
            w = random.choice(wilayahs)
            obs = FieldObservation(
                wilayah_kode=w.kode,
                variable_kode=var.kode,
                nilai=round(random.uniform(0.5, 1.0), 2),
                catatan=f"Demo laporan #{i+1} — {var.nama} di {w.nama}",
                latitude=w.latitude,
                longitude=w.longitude,
                observer=random.choice(["petugas_a", "petugas_b", "petugas_c"]),
                verified=random.random() > 0.5,  # 50% verified
                rejected=False,
                timestamp=datetime.utcnow() - timedelta(hours=random.randint(1, 72)),
            )
            db.add(obs)
            created += 1

        db.commit()
        print(f"✅ Seed {created} laporan demo.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()