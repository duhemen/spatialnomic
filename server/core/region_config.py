"""Konfigurasi region (pulau besar) Indonesia untuk drill-down peta."""
from __future__ import annotations

REGIONS = {
    "sumatera": {
        "nama": "Sumatera", "icon": "🏝️",
        "prefixes": ["11", "12", "13", "14", "15", "16", "17", "18", "19", "21"],
        "center": [0.5, 100.0], "zoom": 5,
    },
    "jawa": {
        "nama": "Jawa", "icon": "🌋",
        "prefixes": ["31", "32", "33", "34", "35", "36"],
        "center": [-7.5, 110.0], "zoom": 7,
    },
    "bali_nusra": {
        "nama": "Bali & Nusa Tenggara", "icon": "⛱️",
        "prefixes": ["51", "52", "53"],
        "center": [-8.5, 118.0], "zoom": 7,
    },
    "kalimantan": {
        "nama": "Kalimantan", "icon": "🌴",
        "prefixes": ["61", "62", "63", "64", "65"],
        "center": [0.5, 114.0], "zoom": 6,
    },
    "sulawesi": {
        "nama": "Sulawesi", "icon": "🐚",
        "prefixes": ["71", "72", "73", "74", "75", "76"],
        "center": [-2.0, 121.0], "zoom": 6,
    },
    "maluku": {
        "nama": "Maluku", "icon": "🌶️",
        "prefixes": ["81", "82"],
        "center": [-3.0, 129.0], "zoom": 6,
    },
    "papua": {
        "nama": "Papua", "icon": "🦜",
        "prefixes": ["91", "92", "93", "94", "95", "96"],
        "center": [-5.0, 138.0], "zoom": 5,
    },
}


def get_region(region_key: str) -> dict | None:
    return REGIONS.get(region_key.lower())


def list_regions() -> list[dict]:
    return [
        {"key": k, "nama": v["nama"], "icon": v["icon"],
         "center": v["center"], "zoom": v["zoom"],
         "prefixes": v["prefixes"]}
        for k, v in REGIONS.items()
    ]


def prefix_to_region(prefix: str) -> str | None:
    for key, cfg in REGIONS.items():
        if prefix in cfg["prefixes"]:
            return key
    return None