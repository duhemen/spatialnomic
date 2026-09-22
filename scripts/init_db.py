"""Inisialisasi database + seed data demo."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server.database import init_db, SessionLocal
from server.models import Wilayah


def seed_wilayah():
    db = SessionLocal()
    try:
        if db.query(Wilayah).count() == 0:
            samples = [
                Wilayah(kode="11", nama="Aceh", level="provinsi"),
                Wilayah(kode="12", nama="Sumatera Utara", level="provinsi"),
                Wilayah(kode="13", nama="Sumatera Barat", level="provinsi"),
                Wilayah(kode="31", nama="DKI Jakarta", level="provinsi"),
                Wilayah(kode="32", nama="Jawa Barat", level="provinsi"),
                Wilayah(kode="33", nama="Jawa Tengah", level="provinsi"),
                Wilayah(kode="34", nama="DI Yogyakarta", level="provinsi"),
                Wilayah(kode="35", nama="Jawa Timur", level="provinsi"),
                Wilayah(kode="51", nama="Bali", level="provinsi"),
                Wilayah(kode="64", nama="Kalimantan Timur", level="provinsi"),
            ]
            db.add_all(samples)
            db.commit()
            print(f"✅ Seed {len(samples)} provinsi.")
        else:
            print("ℹ️  Data wilayah sudah ada, skip seed.")
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    seed_wilayah()
    print("🎉 Database siap.")