"""
Cek kualitas data wilayah setelah import.
Pemakaian: python scripts/check_data.py
"""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sqlite3
from config.settings import settings


def main():
    con = sqlite3.connect(settings.DB_PATH)
    cur = con.cursor()

    print("=" * 60)
    print("📊  LAPORAN KUALITAS DATA SPATIANOMICS")
    print("=" * 60)

    # Total
    total = cur.execute("SELECT COUNT(*) FROM wilayah").fetchone()[0]
    print(f"\n📦 Total records: {total}")

    # Per level
    print("\n📋 Per level:")
    for r in cur.execute(
        "SELECT level, COUNT(*) FROM wilayah GROUP BY level ORDER BY COUNT(*) DESC"
    ):
        print(f"   {r[0]:12s} : {r[1]:>7,}")

    # Polygon coverage
    print("\n🗺️  Polygon coverage (dari cahyadsn level_1_2):")
    for r in cur.execute(
        "SELECT level, COUNT(*) FROM wilayah "
        "WHERE geojson IS NOT NULL GROUP BY level"
    ):
        print(f"   {r[0]:12s} : {r[1]:>7,} punya polygon")

    # Yang tidak punya polygon (level prov/kab)
    print("\n⚠️  Provinsi/Kabupaten TANPA polygon:")
    rows = cur.execute(
        "SELECT kode, nama, level FROM wilayah "
        "WHERE level IN ('provinsi', 'kabupaten') AND geojson IS NULL"
    ).fetchall()
    if not rows:
        print("   ✅ Tidak ada — semua provinsi & kabupaten punya polygon!")
    else:
        print(f"   Ditemukan {len(rows)} record:")
        for r in rows:
            print(f"     [{r[2]:9s}] {r[0]} - {r[1]}")

    # Sample data
    print("\n🔍 Sample data:")
    for level in ["provinsi", "kabupaten", "kecamatan", "desa"]:
        row = cur.execute(
            "SELECT kode, nama FROM wilayah WHERE level = ? LIMIT 1", (level,)
        ).fetchone()
        if row:
            print(f"   {level:10s}: {row[0]} → {row[1]}")

    # Field variables
    print("\n🔖 Custom variables:")
    total_var = cur.execute("SELECT COUNT(*) FROM custom_variable").fetchone()[0]
    approved = cur.execute(
        "SELECT COUNT(*) FROM custom_variable WHERE is_approved = 1"
    ).fetchone()[0]
    print(f"   Total: {total_var} | Approved: {approved}")

    # Observasi
    total_obs = cur.execute("SELECT COUNT(*) FROM observasi").fetchone()[0]
    total_field = cur.execute("SELECT COUNT(*) FROM field_observation").fetchone()[0]
    print(f"   Observasi core: {total_obs}")
    print(f"   Field observations: {total_field}")

    print("\n" + "=" * 60)
    print("✅  Cek selesai.")
    print("=" * 60)

    con.close()


if __name__ == "__main__":
    main()