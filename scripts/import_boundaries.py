"""
Import boundaries dari cahyadsn/wilayah → SpatiaNomics
========================================================
Mendukung dua file:
1. wilayah.sql            → (kode, nama) semua level
2. wilayah_level_1_2.sql  → + koordinat, ibukota, luas, penduduk, polygon

Pemakaian:
    python scripts/import_boundaries.py --wilayah data/raw/wilayah.sql
    python scripts/import_boundaries.py --level12 data/raw/wilayah_level_1_2.sql
    python scripts/import_boundaries.py --all   # jalankan keduanya
"""
from __future__ import annotations           # ← HARUS paling atas

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
import json
import re
import sqlite3

from loguru import logger
from config.settings import settings


# ============================================================
# Helpers: derive level & parent dari kode
# ============================================================
def normalize_kode(kode: str) -> str:
    """'11.01.01.2001' → '1101012001' (hapus titik)."""
    return kode.strip().replace(".", "")


def derive_level_and_parent(kode_raw: str) -> tuple[str, str, str | None]:
    """Return (kode_bersih, level, parent_kode)."""
    kode = normalize_kode(kode_raw)
    n = len(kode)
    if n == 2:
        return kode, "provinsi", None
    elif n == 4:
        return kode, "kabupaten", kode[:2]
    elif n == 6:
        return kode, "kecamatan", kode[:4]
    elif n == 10:
        return kode, "desa", kode[:6]
    else:
        # Fallback best-effort
        return kode, f"level_{n}", kode[:-2] if n > 2 else None


# ============================================================
# Parser wilayah.sql
# ============================================================
WILAYAH_ROW_RE = re.compile(
    r"\(\s*'([^']+)'\s*,\s*'((?:[^'\\]|\\.)*)'\s*\)",
    re.DOTALL,
)


def parse_wilayah_sql(sql_path: str) -> list[tuple[str, str, str, str | None]]:
    """Return list of (kode, nama, level, parent)."""
    logger.info(f"📖 Parsing {sql_path} ...")
    content = Path(sql_path).read_text(encoding="utf-8", errors="ignore")

    records = []
    for m in WILAYAH_ROW_RE.finditer(content):
        kode_raw = m.group(1)
        nama = m.group(2).replace("\\'", "'").replace('\\"', '"')
        kode, level, parent = derive_level_and_parent(kode_raw)
        records.append((kode, nama, level, parent))

    logger.info(f"   Ditemukan {len(records)} record")
    return records


# ============================================================
# Parser wilayah_level_1_2.sql
# ============================================================
LEVEL12_ROW_RE = re.compile(
    r"\(\s*'([^']+)'\s*,\s*'((?:[^'\\]|\\.)*)'\s*,\s*'((?:[^'\\]|\\.)*)'\s*,\s*"
    r"([-\d.eE]+|NULL)\s*,\s*([-\d.eE]+|NULL)\s*,\s*([-\d.eE]+|NULL)\s*,\s*"
    r"([-\d.eE]+|NULL)\s*,\s*([-\d.eE]+|NULL)\s*,\s*([-\d.eE]+|NULL)\s*,\s*"
    r"'((?:[^'\\]|\\.)*)'\s*,\s*([-\d.eE]+|NULL)\s*\)",
    re.DOTALL,
)


def _to_float(s: str) -> float | None:
    if s.upper() == "NULL":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _path_to_geojson(path_raw: str) -> dict | None:
    """
    Konversi string path Cahya '[ [[lat,lng],...] ]' → GeoJSON MultiPolygon.
    Return dict GeoJSON atau None kalau gagal.
    """
    if not path_raw or path_raw in ("NULL", "[]", "''"):
        return None
    try:
        raw = json.loads(path_raw)
    except json.JSONDecodeError:
        # Kadang ada escaping aneh; coba bersihkan
        try:
            cleaned = path_raw.replace("\\'", "'").strip()
            raw = json.loads(cleaned)
        except Exception as e:
            logger.warning(f"Gagal parse path: {e}")
            return None

    if not isinstance(raw, list) or not raw:
        return None

    # raw = list of polygons; tiap polygon = list of [lat, lng]
    multipolygon_coords = []
    for polygon in raw:
        if not isinstance(polygon, list) or not polygon:
            continue
        # Swap lat,lng → lng,lat
        ring = []
        for pt in polygon:
            if isinstance(pt, list) and len(pt) >= 2:
                ring.append([pt[1], pt[0]])
        if len(ring) >= 4:  # ring minimal 4 titik (closed)
            multipolygon_coords.append([ring])

    if not multipolygon_coords:
        return None

    return {
        "type": "MultiPolygon",
        "coordinates": multipolygon_coords,
    }


def parse_level_1_2_sql(sql_path: str) -> list[dict]:
    """Return list of dict lengkap dengan semua kolom."""
    logger.info(f"📖 Parsing {sql_path} (ini agak lama karena 23 MB)...")
    content = Path(sql_path).read_text(encoding="utf-8", errors="ignore")

    records = []
    for m in LEVEL12_ROW_RE.finditer(content):
        kode_raw = m.group(1)
        kode, level, parent = derive_level_and_parent(kode_raw)
        nama = m.group(2).replace("\\'", "'")
        ibukota = m.group(3).replace("\\'", "'") if m.group(3) else None
        lat = _to_float(m.group(4))
        lng = _to_float(m.group(5))
        elv = _to_float(m.group(6))
        tz = _to_float(m.group(7))
        luas = _to_float(m.group(8))
        penduduk = _to_float(m.group(9))
        path_raw = m.group(10)
        status = _to_float(m.group(11))

        geojson = _path_to_geojson(path_raw)

        records.append({
            "kode": kode,
            "nama": nama,
            "level": level,
            "parent_kode": parent,
            "ibukota": ibukota,
            "latitude": lat,
            "longitude": lng,
            "elevasi": elv,
            "timezone": int(tz) if tz is not None else None,
            "luas_km2": luas,
            "penduduk": penduduk,
            "path_raw": path_raw[:5000] if path_raw else None,  # truncate agar DB tidak bengkak
            "geojson": json.dumps(geojson) if geojson else None,
            "status": int(status) if status is not None else None,
        })

    logger.info(f"   Ditemukan {len(records)} record")
    return records


# ============================================================
# Insert ke SQLite
# ============================================================
def insert_wilayah(records: list[tuple]) -> int:
    """Insert (kode, nama, level, parent) — mode wilayah.sql."""
    from server.database import init_db
    init_db()

    con = sqlite3.connect(settings.DB_PATH)
    cur = con.cursor()

    inserted = 0
    for kode, nama, level, parent in records:
        try:
            cur.execute("""
                INSERT INTO wilayah (kode, nama, level, parent_kode)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(kode) DO UPDATE SET
                    nama = excluded.nama,
                    level = excluded.level,
                    parent_kode = excluded.parent_kode
            """, (kode, nama, level, parent))
            inserted += 1
        except Exception as e:
            logger.warning(f"Skip {kode}: {e}")

    con.commit()
    total = cur.execute("SELECT COUNT(*) FROM wilayah").fetchone()[0]
    con.close()
    logger.success(f"✅ wilayah.sql: {inserted} inserted/updated, total di DB: {total}")
    return inserted


def update_level_1_2(records: list[dict]) -> int:
    """Update record existing dengan data level_1_2."""
    con = sqlite3.connect(settings.DB_PATH)
    cur = con.cursor()

    updated = 0
    for r in records:
        try:
            cur.execute("""
                UPDATE wilayah SET
                    nama = ?,
                    ibukota = ?,
                    latitude = COALESCE(?, latitude),
                    longitude = COALESCE(?, longitude),
                    elevasi = ?,
                    timezone = ?,
                    luas_km2 = ?,
                    penduduk = ?,
                    path_raw = ?,
                    geojson = ?,
                    status = ?
                WHERE kode = ?
            """, (
                r["nama"], r["ibukota"], r["latitude"], r["longitude"],
                r["elevasi"], r["timezone"], r["luas_km2"], r["penduduk"],
                r["path_raw"], r["geojson"], r["status"], r["kode"],
            ))
            if cur.rowcount > 0:
                updated += 1
        except Exception as e:
            logger.warning(f"Skip update {r['kode']}: {e}")

    con.commit()
    total = cur.execute("SELECT COUNT(*) FROM wilayah").fetchone()[0]
    con.close()
    logger.success(f"✅ level_1_2: {updated} updated, total di DB: {total}")
    return updated


# ============================================================
# Fallback: derive koordinat untuk kecamatan & desa
# ============================================================
def derive_missing_coords():
    """Isi lat/lng kecamatan & desa dengan koordinat parent-nya."""
    con = sqlite3.connect(settings.DB_PATH)
    cur = con.cursor()

    for level in ("kecamatan", "desa"):
        cur.execute(f"""
            UPDATE wilayah
            SET latitude = (SELECT w2.latitude FROM wilayah w2 WHERE w2.kode = wilayah.parent_kode),
                longitude = (SELECT w2.longitude FROM wilayah w2 WHERE w2.kode = wilayah.parent_kode)
            WHERE level = ?
              AND (latitude IS NULL OR longitude IS NULL)
        """, (level,))
        logger.info(f"   {level}: {cur.rowcount} derived coords")

    con.commit()
    con.close()


# ============================================================
# CLI
# ============================================================
def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--wilayah", type=str, help="Path ke wilayah.sql")
    p.add_argument("--level12", type=str, help="Path ke wilayah_level_1_2.sql")
    p.add_argument("--all", action="store_true", help="Import keduanya (default path data/raw/)")
    p.add_argument("--derive-coords", action="store_true", help="Isi koordinat kec/desa dari parent")
    args = p.parse_args()

    # Default paths
    base = Path("data/raw")
    f_wilayah = Path(args.wilayah) if args.wilayah else base / "wilayah.sql"
    f_level12 = Path(args.level12) if args.level12 else base / "wilayah_level_1_2.sql"

    if args.all or (args.wilayah and args.level12):
        # Keduanya
        if not f_wilayah.exists():
            logger.error(f"❌ Tidak ada: {f_wilayah}")
            return
        if not f_level12.exists():
            logger.error(f"❌ Tidak ada: {f_level12}")
            return

        # Step 1: wilayah.sql
        recs = parse_wilayah_sql(str(f_wilayah))
        insert_wilayah(recs)

        # Step 2: level_1_2
        recs12 = parse_level_1_2_sql(str(f_level12))
        update_level_1_2(recs12)

        # Step 3: derive coords untuk kecamatan & desa
        derive_missing_coords()

    elif args.wilayah:
        recs = parse_wilayah_sql(str(f_wilayah))
        insert_wilayah(recs)

    elif args.level12:
        recs12 = parse_level_1_2_sql(str(f_level12))
        update_level_1_2(recs12)

    elif args.derive_coords:
        derive_missing_coords()

    else:
        print(__doc__)
        print("\nContoh pemakaian:")
        print("  python scripts/import_boundaries.py --all")
        print("  python scripts/import_boundaries.py --wilayah data/raw/wilayah.sql")
        print("  python scripts/import_boundaries.py --level12 data/raw/wilayah_level_1_2.sql")


if __name__ == "__main__":
    main()