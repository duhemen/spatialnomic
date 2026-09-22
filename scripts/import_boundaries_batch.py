"""
Import boundaries batch dari cahyadsn/wilayah_boundaries SQL files.
================================================================
Proses file .sql dari:
    data/raw/prov/*.sql
    data/raw/kab/*.sql
    data/raw/kec/*.sql
    data/raw/kel/<prov>/*.sql

Untuk setiap record (kode, path), konversi path dari
[[[lat,lng],...]] ke GeoJSON MultiPolygon [[[lng,lat],...]]
dan UPDATE kolom `geojson` di tabel `wilayah`.

Fitur:
- Bracket-aware parser (tahan nested 4-level)
- Progress log per file
- Resume (skip file yang sudah diproses)
- Filter per level (--level prov|kab|kec|kel|all)
- Preview (--dry-run)

Pemakaian:
    python scripts/import_boundaries_batch.py --level all --step
    python scripts/import_boundaries_batch.py --level prov
    python scripts/import_boundaries_batch.py --level all --reset-progress
"""
from __future__ import annotations

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
# Constants
# ============================================================
BASE_DIR = Path("data/raw")
PROGRESS_FILE = BASE_DIR / ".import_progress.json"

INSERT_PATTERN = re.compile(
    r"INSERT\s+INTO\s+`?wilayah_boundaries`?\s*"
    r"(?:\([^)]*\))?\s*VALUES\s*",
    re.IGNORECASE,
)


# ============================================================
# Helpers
# ============================================================
def normalize_kode(kode: str) -> str:
    """'11.01.01.2001' → '1101012001'."""
    return str(kode).strip().replace(".", "")


# ============================================================
# Bracket-aware parser
# ============================================================
def extract_row_tuples(content: str, start_pos: int):
    """Baca tuple (...) dari start_pos sampai ketemu ';'."""
    rows = []
    pos = start_pos
    n = len(content)

    while pos < n:
        while pos < n and content[pos] in " \t\n\r,":
            pos += 1
        if pos >= n:
            break
        c = content[pos]
        if c == ";":
            pos += 1
            break
        if c != "(":
            break

        row_start = pos
        pos += 1
        depth = 1
        in_quote = False
        escape = False

        while pos < n and depth > 0:
            ch = content[pos]
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == "'":
                in_quote = not in_quote
            elif not in_quote:
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
            pos += 1

        rows.append(content[row_start:pos])

    return rows, pos


def parse_tuple_fields(row_str: str):
    """Parse tuple string menjadi list of field values."""
    inner = row_str.strip()
    if inner.startswith("("):
        inner = inner[1:]
    if inner.endswith(")"):
        inner = inner[:-1]

    fields = []
    pos = 0
    n = len(inner)

    while pos < n:
        while pos < n and inner[pos] in " \t\n\r,":
            pos += 1
        if pos >= n:
            break

        if inner[pos] == "'":
            pos += 1
            buf = []
            escape = False
            while pos < n:
                c = inner[pos]
                if escape:
                    buf.append(c)
                    escape = False
                elif c == "\\":
                    escape = True
                elif c == "'":
                    break
                else:
                    buf.append(c)
                pos += 1
            if pos < n:
                pos += 1
            fields.append("".join(buf))
        else:
            start = pos
            while pos < n and inner[pos] != ",":
                pos += 1
            fields.append(inner[start:pos].strip())

    return fields


# ============================================================
# GeoJSON converter
# ============================================================
def swap_lat_lng(obj):
    """Recursive swap [lat,lng] → [lng,lat]."""
    if isinstance(obj, list):
        if len(obj) == 2 and all(isinstance(x, (int, float)) for x in obj):
            return [obj[1], obj[0]]
        return [swap_lat_lng(x) for x in obj]
    return obj


def convert_path_to_geojson(path_str: str):
    """'[[[[lat,lng],...]]]' → GeoJSON MultiPolygon."""
    if not path_str or path_str in ("", "NULL", "[]"):
        return None
    try:
        raw = json.loads(path_str)
    except json.JSONDecodeError:
        return None

    if not isinstance(raw, list) or not raw:
        return None

    try:
        coords = swap_lat_lng(raw)
    except Exception:
        return None

    return {"type": "MultiPolygon", "coordinates": coords}


# ============================================================
# Progress
# ============================================================
def load_progress():
    if PROGRESS_FILE.exists():
        try:
            return set(json.loads(PROGRESS_FILE.read_text(encoding="utf-8")))
        except Exception:
            return set()
    return set()


def save_progress(processed):
    PROGRESS_FILE.write_text(
        json.dumps(sorted(processed), indent=2), encoding="utf-8"
    )


# ============================================================
# Core processor
# ============================================================
def process_file(file_path: Path, resume_set, dry_run=False):
    key = str(file_path.resolve())
    if key in resume_set:
        logger.info(f"      ⏭️  Skip (resume): {file_path.name}")
        return 0, 0

    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        logger.error(f"      ❌ Gagal baca file: {e}")
        return 0, 0

    if dry_run:
        con = None
        cur = None
    else:
        con = sqlite3.connect(settings.DB_PATH)
        cur = con.cursor()

    total = 0
    updated = 0
    pos = 0
    while True:
        m = INSERT_PATTERN.search(content, pos)
        if not m:
            break
        rows, pos = extract_row_tuples(content, m.end())

        for row_str in rows:
            fields = parse_tuple_fields(row_str)
            if len(fields) < 5:
                continue
            kode_raw = fields[0]
            path_str = fields[4]
            total += 1

            if dry_run:
                continue

            kode = normalize_kode(kode_raw)
            geom = convert_path_to_geojson(path_str)
            if not geom:
                continue

            try:
                cur.execute(
                    "UPDATE wilayah SET geojson = ? WHERE kode = ?",
                    (json.dumps(geom, separators=(",", ":")), kode),
                )
                if cur.rowcount > 0:
                    updated += 1
            except Exception as e:
                logger.debug(f"      Update gagal {kode}: {e}")

    if con:
        con.commit()
        con.close()

    if not dry_run:
        resume_set.add(key)
        save_progress(resume_set)

    logger.info(f"      ✅ {file_path.name}: {updated}/{total} updates")
    return updated, total


# ============================================================
# Level processors
# ============================================================
def get_files_for_level(level: str):
    if level == "prov":
        return sorted((BASE_DIR / "prov").glob("*.sql"))
    if level == "kab":
        return sorted((BASE_DIR / "kab").glob("*.sql"))
    if level == "kec":
        return sorted((BASE_DIR / "kec").glob("*.sql"))
    if level == "kel":
        return sorted((BASE_DIR / "kel").rglob("*.sql"))
    return []


def process_level(level: str, resume_set, dry_run=False):
    logger.info(f"\n{'='*70}")
    logger.info(f"📂 LEVEL: {level.upper()}")
    logger.info(f"{'='*70}")

    files = get_files_for_level(level)
    if not files:
        logger.warning(f"   ⚠️  Tidak ada file .sql untuk level '{level}'")
        return {"files": 0, "updates": 0, "records": 0}

    logger.info(f"   Ditemukan {len(files)} file")

    total_updates = 0
    total_records = 0
    for i, f in enumerate(files, 1):
        logger.info(f"   [{i}/{len(files)}] {f.name}")
        u, r = process_file(f, resume_set, dry_run=dry_run)
        total_updates += u
        total_records += r

    logger.success(
        f"✅ {level.upper()}: {total_updates}/{total_records} updates "
        f"dari {len(files)} file"
    )
    return {"files": len(files), "updates": total_updates, "records": total_records}


# ============================================================
# CLI
# ============================================================
def main():
    p = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--level", choices=["prov", "kab", "kec", "kel", "all"],
                   default="all", help="Level yang akan diproses")
    p.add_argument("--step", action="store_true",
                   help="Pause antar level untuk verifikasi manual")
    p.add_argument("--reset-progress", action="store_true",
                   help="Hapus file progress (mulai dari awal)")
    p.add_argument("--dry-run", action="store_true",
                   help="Hanya parsing, tidak update DB")
    args = p.parse_args()

    if args.reset_progress and PROGRESS_FILE.exists():
        PROGRESS_FILE.unlink()
        logger.warning("🔄 Progress direset.")

    resume_set = load_progress()
    if resume_set:
        logger.info(f"📋 Resume: {len(resume_set)} file sudah pernah diproses")

    logger.info(f"🚀 Mode: {'DRY RUN' if args.dry_run else 'IMPORT'}")
    logger.info(f"🎯 Level: {args.level}")

    if args.level == "all":
        levels = ["prov", "kab", "kec", "kel"]
    else:
        levels = [args.level]

    summary = {}
    for i, lvl in enumerate(levels):
        summary[lvl] = process_level(lvl, resume_set, dry_run=args.dry_run)
        if args.step and i < len(levels) - 1:
            input(f"\n⏸️  Level '{lvl}' selesai. ENTER untuk lanjut...")

    logger.info(f"\n{'='*70}")
    logger.info("📊 SUMMARY AKHIR")
    logger.info(f"{'='*70}")
    for lvl, s in summary.items():
        logger.info(
            f"   {lvl:6s}: {s['files']:>4} file | "
            f"{s['updates']:>6,}/{s['records']:<6,} updates"
        )
    logger.success("🎉 Import selesai!")


if __name__ == "__main__":
    main()