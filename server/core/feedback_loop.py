"""
Feedback Loop: System Dynamics Planologi ↔ Ekonomi
Menggantikan asumsi statis dengan relasi dinamis antar variabel.
"""
from __future__ import annotations
from dataclasses import dataclass
from loguru import logger
import numpy as np

# Matriks pengaruh antar variabel (Δ target = Σ k_ij × Δ sumber)
# Baris = variabel yang terpengaruh, Kolom = variabel pemicu
# Nilai = koefisien elastisitas (positif/negatif)
INFLUENCE_MATRIX = {
    #                  USAI  LLI   IAI   PEI   ZCEI  FSI   UOTI  ISI
    "USAI":  {       "ISI": -0.35, "UOTI": -0.20, "ZCEI": +0.15},
    "LLI":   {       "USAI": +0.40, "ISI": -0.45, "PEI": +0.25},
    "IAI":   {       "ZCEI": +0.30, "FSI": +0.25},
    "PEI":   {       "IAI": +0.35, "LLI": +0.20},
    "ZCEI":  {       "FSI": +0.40, "IAI": +0.15},
    "FSI":   {       "LLI": -0.20},  # stimulus berlebih bisa longgar
    "UOTI":  {       "USAI": -0.30, "IAI": -0.20},
    "ISI":   {       "UOTI": +0.40, "LLI": -0.30},
}


@dataclass
class LoopResult:
    new_values: dict
    deltas: dict
    iterations: int


def simulate(
    initial: dict,
    shock: dict,
    steps: int = 5,
    damping: float = 0.5,
) -> LoopResult:
    """
    Simulasi feedback loop.

    Parameters
    ----------
    initial : kondisi awal {var: value}
    shock : guncangan awal {var: delta} — mis. {"FSI": +0.2}
    steps : jumlah iterasi
    damping : faktor peredam (0-1) agar tidak meledak

    Returns
    -------
    LoopResult dengan nilai akhir + delta total
    """
    values = {k: float(v) for k, v in initial.items()}
    for k, d in shock.items():
        values[k] = np.clip(values.get(k, 0.5) + d, 0.0, 1.0)

    history = []
    for step in range(steps):
        deltas = {k: 0.0 for k in values}
        for target, sources in INFLUENCE_MATRIX.items():
            for src, coef in sources.items():
                delta_src = values[src] - 0.5  # deviasi dari netral
                deltas[target] += coef * delta_src * damping
        # update
        for k in values:
            values[k] = float(np.clip(values[k] + deltas[k], 0.0, 1.0))
        history.append(deltas.copy())

    total_delta = {k: values[k] - initial.get(k, 0.5) for k in values}
    logger.info(f"Simulasi loop: {steps} iterasi, damping={damping}")
    return LoopResult(new_values=values, deltas=total_delta, iterations=steps)