"""
Explainable AI (XAI) untuk UERI.
Menggunakan pendekatan kontribusi berbasis geometric decomposition
(karena formula UERI bukan model ML klasik, tapi weighted geometric mean).
Ditambah SHAP-style analysis untuk model ensemble time-series.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from loguru import logger

from server.core import index_calc

# Label ramah pengguna
VAR_LABELS_ID = {
    "USAI": "Ketersediaan Ruang Terbuka (Urban Space Availability)",
    "LLI":  "Likuiditas Ekonomi Lokal (Local Liquidity)",
    "IAI":  "Akses Infrastruktur (Infrastructure Access)",
    "PEI":  "Produktivitas & Lapangan Kerja (Productivity & Employment)",
    "ZCEI": "Tata Ruang & Belanja Modal (Zoning & Capital Expenditure)",
    "FSI":  "Stimulus Fiskal (Fiscal Stimulus)",
    "UOTI": "Kepadatan & Kemacetan (Urban Overcrowding)",
    "ISI":  "Syok Inflasi (Inflation Shock)",
}

NARRATIVE_TEMPLATES = {
    "USAI": "berkurangnya ruang terbuka & makin padatnya lahan terbangun",
    "LLI":  "melemahnya daya beli & perputaran uang di masyarakat",
    "IAI":  "buruknya aksesibilitas infrastruktur publik",
    "PEI":  "menurunnya produktivitas & penyerapan tenaga kerja",
    "ZCEI": "tidak terkendalinya tata ruang & belanja modal daerah",
    "FSI":  "ketidaktepatan stimulus fiskal (over/under)",
    "UOTI": "kemacetan & kepadatan hunian yang ekstrem",
    "ISI":  "lonjakan harga barang pokok & biaya hidup",
}


@dataclass
class Explanation:
    ueri: float
    category: str
    top_drivers: list[dict]           # [{var, label, contribution, value}]
    narrative: str                     # narasi natural language
    weights: dict
    raw_values: dict

    def to_dict(self) -> dict:
        return {
            "ueri": round(self.ueri, 4),
            "category": self.category,
            "top_drivers": self.top_drivers,
            "narrative": self.narrative,
            "weights": {k: round(v, 4) for k, v in self.weights.items()},
            "raw_values": {k: round(v, 4) for k, v in self.raw_values.items()},
        }


def explain_ueri(values: dict, weights: dict | None = None, top_k: int = 3) -> Explanation:
    """
    Hasilkan penjelasan UERI:
    - Kontribusi tiap variabel (delta dari baseline netral 0.5)
    - Top-K pendorong risiko
    - Narasi bahasa manusia
    """
    weights = weights or {v: 1 / len(index_calc.ALL_VARS) for v in index_calc.ALL_VARS}
    for v in index_calc.ALL_VARS:
        values.setdefault(v, 0.5)

    result = index_calc.calculate(values, weights)
    contributions = result.contributions

    # Baseline: hitung UERI dengan semua nilai netral 0.5
    baseline = index_calc.calculate({v: 0.5 for v in index_calc.ALL_VARS}, weights)
    base_ueri = baseline.ueri

    # Kontribusi absolut = seberapa besar var ini "mendorong" UERI dari netral
    drivers = []
    for var in index_calc.ALL_VARS:
        v = float(values[var])
        w = float(weights[var])
        # Semakin tinggi kontribusi ke risiko, semakin "mendorong" UERI naik
        # Kontribusi = w * (risk_i - 0.5)  -> positif jika var ini kontribusi ke risiko
        risk_i = (1 - v) if var in index_calc.RISK_LOW_VARS else v
        drive = w * (risk_i - 0.5)
        drivers.append({
            "var": var,
            "label": VAR_LABELS_ID.get(var, var),
            "value": round(v, 4),
            "weight": round(w, 4),
            "contribution": round(drive, 4),
            "direction": "mendorong risiko" if drive > 0 else "meredam risiko",
        })

    # Sort by |contribution| descending
    drivers.sort(key=lambda d: abs(d["contribution"]), reverse=True)
    top = drivers[:top_k]

    # Narasi
    narrative = _build_narrative(result, top, base_ueri)

    logger.info(f"XAI: UERI={result.ueri:.3f} ({result.category}), top driver: {top[0]['var']}")
    return Explanation(
        ueri=result.ueri,
        category=result.category,
        top_drivers=top,
        narrative=narrative,
        weights=weights,
        raw_values=values,
    )


def _build_narrative(result, top_drivers, base_ueri) -> str:
    cat = result.category
    ueri = result.ueri
    diff = ueri - base_ueri
    trend = "naik" if diff > 0 else "turun" if diff < 0 else "stabil"

    drivers_text = []
    for d in top_drivers:
        if d["direction"] == "mendorong risiko":
            drivers_text.append(NARRATIVE_TEMPLATES.get(d["var"], d["var"]))
    if not drivers_text:
        drivers_text = [NARRATIVE_TEMPLATES.get(d["var"], d["var"]) for d in top_drivers[:2]]

    joined = " serta ".join(drivers_text)

    return (
        f"Status wilayah saat ini: **{cat}** dengan skor UERI {ueri:.3f} "
        f"(indeks netral {base_ueri:.3f}, {trend} {abs(diff):.3f}). "
        f"Pendorong utama: {joined}. "
        f"Rekomendasi: fokuskan intervensi pada variabel {top_drivers[0]['var']} "
        f"(kontribusi {top_drivers[0]['contribution']:+.3f})."
    )


def batch_explain(samples: list[dict], weights: dict | None = None) -> list[dict]:
    """Jelaskan banyak sampel sekaligus."""
    return [explain_ueri(s, weights).to_dict() for s in samples]