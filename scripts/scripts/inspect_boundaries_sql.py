"""
Inspeksi format file boundaries SQL dari cahyadsn/wilayah_boundaries.
Pemakaian: python scripts/inspect_boundaries_sql.py <path_file_sql>
"""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pathlib import Path


def inspect(file_path: str, n_chars: int = 3000):
    p = Path(file_path)
    if not p.exists():
        print(f"❌ File tidak ada: {file_path}")
        return

    size = p.stat().st_size
    print(f"\n{'='*70}")
    print(f"📂 File: {p}")
    print(f"📏 Ukuran: {size:,} bytes ({size/1024:.1f} KB)")
    print(f"{'='*70}\n")

    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read(n_chars)

    print(f"🔍 {n_chars} karakter pertama:")
    print("-" * 70)
    print(content)
    print("-" * 70)

    # Statistik
    full = p.read_text(encoding="utf-8", errors="ignore")
    print(f"\n📊 Statistik:")
    print(f"   'CREATE TABLE'    : {full.count('CREATE TABLE')}")
    print(f"   'INSERT INTO'     : {full.count('INSERT INTO')}")
    print(f"   'REPLACE INTO'    : {full.count('REPLACE INTO')}")
    print(f"   'UPDATE '         : {full.count('UPDATE ')}")
    print(f"   'DROP TABLE'      : {full.count('DROP TABLE')}")
    print(f"   Total baris       : {full.count(chr(10)):,}")
    print(f"   Total karakter    : {len(full):,}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("file", help="Path file SQL")
    ap.add_argument("--chars", type=int, default=3000,
                    help="Jumlah karakter untuk preview")
    args = ap.parse_args()
    inspect(args.file, args.chars)