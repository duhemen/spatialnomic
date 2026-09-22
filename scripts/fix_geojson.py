"""
Fix polygon depth mismatch di DB SpatiaNomics.
Konversi semua geojson ke MultiPolygon depth 4 yang valid.
"""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import sqlite3
from loguru import logger
from config.settings import settings


def is_point(x) -> bool:
    return (isinstance(x, list) and len(x) == 2
            and isinstance(x[0], (int, float)) and not isinstance(x[0], bool)
            and isinstance(x[1], (int, float)) and not isinstance(x[1], bool))


def clean_ring(x):
    """Bersihkan ring: buang titik invalid, minimal 4 titik."""
    if not isinstance(x, list):
        return None
    pts = [p for p in x if is_point(p)]
    if len(pts) < 4:
        return None
    # Pastikan ring tertutup
    if pts[0] != pts[-1]:
        pts.append(pts[0])
    return pts


def clean_polygon(x):
    """Bersihkan polygon: minimal 1 ring."""
    if not isinstance(x, list):
        return None
    rings = [clean_ring(r) for r in x]
    rings = [r for r in rings if r is not None]
    return rings if rings else None


def to_multipolygon(coords):
    """
    Konversi apapun ke MultiPolygon depth 4.
    Return: list of polygons, atau None kalau gagal.
    """
    if not isinstance(coords, list) or not coords:
        return None

    first = coords[0]
    if not isinstance(first, list):
        return None

    # Case 1: coords = single ring [pt, pt, ...]
    if is_point(first):
        r = clean_ring(coords)
        return [[r]] if r else None

    first_inner = first[0] if first else None
    if not isinstance(first_inner, list):
        return None

    # Case 2: coords = list of rings (Polygon) → [pt, pt, ...][...]
    if is_point(first_inner):
        p = clean_polygon(coords)
        return [p] if p else None

    # Case 3: coords = list of polygons (MultiPolygon) → [[pt,...],...]
    polygons = [clean_polygon(p) for p in coords]
    polygons = [p for p in polygons if p is not None]
    return polygons if polygons else None


def fix_geojson(gj_str: str) -> str | None:
    """Terima string geojson, return string geojson yang sudah dinormalisasi."""
    try:
        gj = json.loads(gj_str)
    except Exception:
        return None

    if not isinstance(gj, dict):
        return None

    coords = gj.get("coordinates")
    new_coords = to_multipolygon(coords)
    if not new_coords:
        return None

    return json.dumps({
        "type": "MultiPolygon",
        "coordinates": new_coords,
    }, separators=(",", ":"))


def main():
    con = sqlite3.connect(settings.DB_PATH)
    cur = con.cursor()

    print("🔧 Memperbaiki polygon di DB...\n")

    total_stats = {}
    for level in ["provinsi", "kabupaten", "kecamatan", "desa"]:
        rows = cur.execute(
            "SELECT kode, nama, geojson FROM wilayah "
            "WHERE level = ? AND geojson IS NOT NULL",
            (level,)
        ).fetchall()

        fixed = 0
        skipped = 0
        for kode, nama, gj_str in rows:
            new_gj = fix_geojson(gj_str)
            if new_gj:
                cur.execute(
                    "UPDATE wilayah SET geojson = ? WHERE kode = ?",
                    (new_gj, kode)
                )
                fixed += 1
            else:
                # Kalau gagal fix, set NULL biar fallback ke dummy
                cur.execute(
                    "UPDATE wilayah SET geojson = NULL WHERE kode = ?",
                    (kode,)
                )
                skipped += 1

        con.commit()
        total_stats[level] = (fixed, skipped)
        print(f"📊 {level}: {fixed} fixed, {skipped} di-NULL-kan (dari {len(rows)})")

    print("\n✅ Selesai!")
    con.close()


if __name__ == "__main__":
    main()