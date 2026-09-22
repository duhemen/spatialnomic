"""
UERI (Urban-Economic Risk Index) Calculator
============================================
Adaptasi formula PFVI dari `peatfr` (mellygsln/peatfr) ke domain
Planologi + Ekonomi.

Variabel:
    USAI  - Urban Space Availability Index       (0-1, rendah=risiko)
    LLI   - Local Liquidity Index                (0-1, rendah=risiko)
    IAI   - Infrastructure Accessibility Index   (0-1, rendah=risiko)
    PEI   - Productivity & Employment Index      (0-1, rendah=risiko)
    ZCEI  - Zoning & Capital Expenditure Index   (0-1, stimulus)
    FSI   - Fiscal Stimulus Index                (0-1, stimulus)
    UOTI  - Urban Overcrowding & Traffic Index   (0-1, tinggi=risiko)
    ISI   - Inflation Shock Index                (0-1, tinggi=risiko)

Output: UERI ∈ [0, 1], semakin tinggi semakin berisiko.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Sequence
import numpy as np
from scipy.optimize import minimize
from loguru import logger


# ============================================================
# Konstanta
# ============================================================
RISK_LOW_VARS = ["USAI", "LLI", "IAI", "PEI", "ZCEI", "FSI"]  # rendah = bahaya
RISK_HIGH_VARS = ["UOTI", "ISI"]                                # tinggi = bahaya
ALL_VARS = RISK_LOW_VARS + RISK_HIGH_VARS

# Bobot awal (uniform)
DEFAULT_WEIGHTS = np.ones(len(ALL_VARS)) / len(ALL_VARS)

# Ambang batas klasifikasi UERI
THRESHOLDS = {
    "AMAN":    0.30,
    "WASPADA": 0.60,
    "SIAGA":   0.80,
    # di atas 0.80 = BAHAYA
}


# ============================================================
# Data Classes
# ============================================================
@dataclass
class UERIResult:
    ueri: float
    category: str
    weights: dict
    contributions: dict = field(default_factory=dict)
    raw_values: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "ueri": round(self.ueri, 4),
            "category": self.category,
            "weights": {k: round(v, 4) for k, v in self.weights.items()},
            "contributions": {k: round(v, 4) for k, v in self.contributions.items()},
            "raw_values": self.raw_values,
        }


# ============================================================
# Core Formula
# ============================================================
def compute_ueri(values: dict, weights: dict) -> float:
    """
    Hitung UERI via weighted geometric mean.

    UERI = 1 - [ Π (1 - risk_i)^w_i ]

    Di mana `risk_i` adalah "tingkat risiko" dari tiap variabel:
        - Untuk RISK_LOW_VARS: risk = 1 - value (nilai rendah → risiko tinggi)
        - Untuk RISK_HIGH_VARS: risk = value
    """
    product = 1.0
    for var in ALL_VARS:
        v = float(values.get(var, 0.5))
        v = np.clip(v, 1e-6, 1 - 1e-6)  # hindari log(0)
        if var in RISK_LOW_VARS:
            risk = 1.0 - v
        else:
            risk = v
        w = max(float(weights.get(var, 0.0)), 0.0)
        product *= (1.0 - risk) ** w

    ueri = 1.0 - product
    return float(np.clip(ueri, 0.0, 1.0))


def classify(u: float) -> str:
    """Klasifikasi UERI → kategori."""
    if u < THRESHOLDS["AMAN"]:
        return "AMAN"
    if u < THRESHOLDS["WASPADA"]:
        return "WASPADA"
    if u < THRESHOLDS["SIAGA"]:
        return "SIAGA"
    return "BAHAYA"


# ============================================================
# Optimizer (Nelder-Mead) — adopsi dari peatfr
# ============================================================
def _objective(weights_flat: np.ndarray, X: np.ndarray, y_true: np.ndarray) -> float:
    """MSE antara UERI prediksi dan UERI observasi."""
    w = np.abs(weights_flat)
    w = w / (w.sum() + 1e-9)  # normalisasi agar Σw = 1
    weight_dict = {var: w[i] for i, var in enumerate(ALL_VARS)}

    preds = np.array([
        compute_ueri({var: row[i] for i, var in enumerate(ALL_VARS)}, weight_dict)
        for row in X
    ])
    return float(np.mean((preds - y_true) ** 2))


def optimize_weights(
    X: Sequence[Sequence[float]],
    y_true: Sequence[float],
    max_iter: int = 2000,
    tol: float = 1e-6,
) -> dict:
    """
    Nelder-Mead optimization untuk mencari bobot optimal.

    Parameters
    ----------
    X : array-like shape (n_samples, n_vars) — nilai variabel (0-1)
    y_true : array-like shape (n_samples,) — UERI observasi

    Returns
    -------
    dict bobot optimal {var: weight}
    """
    X_arr = np.asarray(X, dtype=float)
    y_arr = np.asarray(y_true, dtype=float)

    if X_arr.ndim != 2 or X_arr.shape[1] != len(ALL_VARS):
        raise ValueError(f"X harus shape (n, {len(ALL_VARS)}), dapat {X_arr.shape}")

    logger.info(f"Optimasi Nelder-Mead: {X_arr.shape[0]} sampel, {X_arr.shape[1]} variabel")
    result = minimize(
        _objective,
        x0=DEFAULT_WEIGHTS.copy(),
        args=(X_arr, y_arr),
        method="Nelder-Mead",
        options={"maxiter": max_iter, "xatol": tol, "fatol": tol, "disp": False},
    )

    w_opt = np.abs(result.x)
    w_opt = w_opt / (w_opt.sum() + 1e-9)
    weights = {var: float(w_opt[i]) for i, var in enumerate(ALL_VARS)}

    logger.success(f"Optimasi selesai | MSE={result.fun:.6f} | iter={result.nit}")
    return weights


# ============================================================
# High-level API
# ============================================================
def calculate(
    values: dict,
    weights: dict | None = None,
    with_contributions: bool = True,
) -> UERIResult:
    """
    Fungsi utama: hitung UERI + kategori + kontribusi tiap variabel.

    Parameters
    ----------
    values : dict {var_name: value} — semua dalam skala 0-1
    weights : dict opsional; jika None pakai uniform
    with_contributions : hitung kontribusi tiap variabel ke UERI
    """
    weights = weights or {v: 1 / len(ALL_VARS) for v in ALL_VARS}
    # Pastikan semua variabel ada
    for v in ALL_VARS:
        values.setdefault(v, 0.5)

    ueri = compute_ueri(values, weights)
    category = classify(ueri)

    contributions = {}
    if with_contributions:
        for var in ALL_VARS:
            v_single = {k: (values[k] if k == var else (0.5 if k in RISK_LOW_VARS else 0.5))
                        for k in ALL_VARS}
            base = compute_ueri(v_single, weights)
            contributions[var] = ueri - base

    return UERIResult(
        ueri=ueri,
        category=category,
        weights=weights,
        contributions=contributions,
        raw_values=values,
    )


if __name__ == "__main__":
    # Quick test
    demo = {
        "USAI": 0.35, "LLI": 0.40, "IAI": 0.55, "PEI": 0.60,
        "ZCEI": 0.50, "FSI": 0.45, "UOTI": 0.75, "ISI": 0.80,
    }
    res = calculate(demo)
    print(res.to_dict())

# ============================================================
# Multi-Level Dispatcher
# ============================================================
def calculate_rule_based(values: dict, config: dict) -> dict:
    """
    Rule-based scoring untuk level dusun (μR-Flag).
    Bukan weighted geometric, tapi IF-THEN sederhana → flag warna.
    """
    triggers = []
    for var in config["variables"]:
        v = float(values.get(var, 0))
        if v >= 0.7:
            triggers.append({"var": var, "label": config["var_labels"].get(var, var),
                             "severity": "CRITICAL"})
        elif v >= 0.4:
            triggers.append({"var": var, "label": config["var_labels"].get(var, var),
                             "severity": "HIGH"})

    if any(t["severity"] == "CRITICAL" for t in triggers):
        flag = "BAHAYA"
    elif any(t["severity"] == "HIGH" for t in triggers):
        flag = "SIAGA"
    elif triggers:
        flag = "WASPADA"
    else:
        flag = "AMAN"

    return {
        "index_name": config["index_name"],
        "full_name": config["full_name"],
        "flag": flag,
        "category": flag,
        "triggers": triggers,
        "raw_values": values,
    }


def calculate_for_level(
    kode: str,
    values: dict,
    level: str,
    weights: dict | None = None,
) -> dict:
    """Hitung indeks berdasarkan level wilayah."""
    from server.core.variable_config import get_config

    cfg = get_config(level)

    # Normalisasi: pastikan semua variable ada (default 0.5)
    normalized = {}
    for var in cfg["variables"]:
        normalized[var] = float(values.get(var, 0.5))

    if cfg.get("is_rule_based"):
        return calculate_rule_based(normalized, cfg)

    # Weighted geometric mean
    if weights is None:
        weights = {v: 1 / len(cfg["variables"]) for v in cfg["variables"]}
    else:
        # Filter weights hanya untuk variable yang ada
        weights = {v: weights.get(v, 0) for v in cfg["variables"]}
        total = sum(weights.values()) or 1
        weights = {k: v / total for k, v in weights.items()}

    # Custom compute (menggunakan risk_low / risk_high dari config)
    product = 1.0
    for var in cfg["variables"]:
        v = float(np.clip(normalized[var], 1e-6, 1 - 1e-6))
        if var in cfg["risk_low_vars"]:
            risk = 1.0 - v
        else:
            risk = v
        w = max(float(weights.get(var, 0)), 0.0)
        product *= (1.0 - risk) ** w

    score = float(np.clip(1.0 - product, 0.0, 1.0))
    category = classify(score)

    # Kontribusi per variable
    contributions = {}
    for var in cfg["variables"]:
        v = float(np.clip(normalized[var], 1e-6, 1 - 1e-6))
        risk = (1 - v) if var in cfg["risk_low_vars"] else v
        contributions[var] = round(float(weights[var] * (risk - 0.5)), 4)

    return {
        "kode": kode,
        "index_name": cfg["index_name"],
        "full_name": cfg["full_name"],
        "ueri": round(score, 4),
        "category": category,
        "weights": {k: round(v, 4) for k, v in weights.items()},
        "contributions": contributions,
        "raw_values": normalized,
        "level": level,
    }


def calculate_composite(kode: str, values: dict, level: str, db_session) -> dict:
    """
    Composite = Core Score + Field Adjustment.
    Return: {core, field_adjusted, flags, field_count}
    """
    from server.models import FieldObservation, CustomVariable

    core_result = calculate_for_level(kode, values, level)
    core_score = core_result.get("ueri", 0)

    # Field observations yang sudah verified
    fields = (
        db_session.query(FieldObservation, CustomVariable)
        .join(CustomVariable, FieldObservation.variable_kode == CustomVariable.kode)
        .filter(
            FieldObservation.wilayah_kode == kode,
            FieldObservation.verified == True,          # noqa: E712
            FieldObservation.rejected == False,          # noqa: E712
            CustomVariable.is_active == True,            # noqa: E712
        )
        .all()
    )

    field_flags = []
    field_adjustment = 0.0
    for obs, var in fields:
        if obs.nilai > 0:
            field_flags.append({
                "kode": var.kode,
                "nama": var.nama,
                "severity": var.severity_weight,
                "nilai": obs.nilai,
                "catatan": obs.catatan,
                "observer": obs.observer,
                "timestamp": obs.timestamp.isoformat() if obs.timestamp else None,
                "latitude": obs.latitude,
                "longitude": obs.longitude,
            })
            field_adjustment += var.severity_weight * obs.nilai * 0.1

    field_adjusted = min(core_score + field_adjustment, 1.0)

    return {
        **core_result,
        "core_score": round(core_score, 4),
        "core_category": core_result.get("category"),
        "field_adjusted_score": round(field_adjusted, 4),
        "field_adjusted_category": classify(field_adjusted),
        "field_flags": field_flags,
        "field_count": len(field_flags),
        "narrative": _build_composite_narrative(
            core_score, field_adjusted, field_flags, core_result.get("category")
        ),
    }


def _build_composite_narrative(core, adjusted, flags, core_cat) -> str:
    """Narasi ringkas untuk composite result."""
    if not flags:
        return f"Skor core {core:.3f} ({core_cat}). Tidak ada laporan lapangan aktif."

    flag_txt = ", ".join(f["nama"] for f in flags[:3])
    return (
        f"Skor core {core:.3f} ({core_cat}). "
        f"Terdapat {len(flags)} laporan lapangan aktif ({flag_txt}), "
        f"menaikkan skor menjadi {adjusted:.3f} ({classify(adjusted)})."
    )