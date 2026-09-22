"""
Cache lokal SQLite untuk field observations (offline-first).
"""
from __future__ import annotations
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from loguru import logger

CACHE_PATH = Path("data/client_cache.db")


def _conn():
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(CACHE_PATH))
    con.execute("""
        CREATE TABLE IF NOT EXISTS pending_obs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            local_uuid TEXT UNIQUE,
            payload TEXT,
            created_at TEXT,
            synced INTEGER DEFAULT 0
        )
    """)
    con.commit()
    return con


def enqueue(payload: dict) -> None:
    """Simpan laporan ke queue lokal."""
    con = _conn()
    con.execute(
        "INSERT OR IGNORE INTO pending_obs (local_uuid, payload, created_at) VALUES (?, ?, ?)",
        (payload.get("local_uuid"), json.dumps(payload), datetime.utcnow().isoformat())
    )
    con.commit()
    con.close()
    logger.info(f"📥 Laporan masuk queue lokal: {payload.get('local_uuid')}")


def pending() -> list[dict]:
    con = _conn()
    rows = con.execute(
        "SELECT id, local_uuid, payload FROM pending_obs WHERE synced = 0 ORDER BY id"
    ).fetchall()
    con.close()
    return [{"id": r[0], "local_uuid": r[1], "payload": json.loads(r[2])} for r in rows]


def mark_synced(ids: list[int]) -> None:
    if not ids:
        return
    con = _conn()
    con.executemany("UPDATE pending_obs SET synced = 1 WHERE id = ?", [(i,) for i in ids])
    con.commit()
    con.close()


def sync_all(api_client) -> int:
    """Kirim semua pending ke server. Return jumlah yang sukses."""
    items = pending()
    if not items:
        return 0
    success_ids = []
    for item in items:
        try:
            api_client.create_field_observation(item["payload"])
            success_ids.append(item["id"])
        except Exception as e:
            logger.warning(f"Sync gagal {item['local_uuid']}: {e}")
    mark_synced(success_ids)
    logger.success(f"🔄 Sync: {len(success_ids)}/{len(items)} berhasil")
    return len(success_ids)