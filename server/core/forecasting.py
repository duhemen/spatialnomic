"""
Forecasting Engine: ARIMA + LSTM/GRU Ensemble
Adaptasi dari peatfr, untuk time-series indikator spasial-ekonomi.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from loguru import logger


@dataclass
class ForecastResult:
    horizon: int
    mean: list[float]
    lower: list[float]
    upper: list[float]
    method: str


def forecast_arima(
    series: Sequence[float],
    horizon: int = 7,
    order: tuple = (1, 1, 1),
    alpha: float = 0.05,
) -> ForecastResult:
    """ARIMA forecast dengan confidence interval."""
    y = np.asarray(series, dtype=float)
    y = y[~np.isnan(y)]
    if len(y) < 10:
        raise ValueError("Butuh minimal 10 titik data untuk ARIMA.")

    model = ARIMA(y, order=order).fit()
    fc = model.get_forecast(steps=horizon)
    mean = fc.predicted_mean.tolist()
    ci = fc.conf_int(alpha=alpha)

    logger.info(f"ARIMA{order} forecast {horizon} langkah selesai.")
    return ForecastResult(
        horizon=horizon,
        mean=[float(x) for x in mean],
        lower=[float(x) for x in ci[:, 0]],
        upper=[float(x) for x in ci[:, 1]],
        method=f"ARIMA{order}",
    )


def forecast_ensemble(
    series: Sequence[float],
    horizon: int = 7,
    weights: dict | None = None,
) -> ForecastResult:
    """
    Ensemble sederhana (bisa dikembangkan untuk LSTM/GRU).
    Saat ini: ARIMA + Moving Average, dengan bobot.
    """
    weights = weights or {"arima": 0.7, "ma": 0.3}

    arima_res = forecast_arima(series, horizon=horizon)

    # Simple MA baseline
    y = np.asarray(series, dtype=float)
    ma_val = float(np.nanmean(y[-7:]))
    ma_mean = [ma_val] * horizon

    # Gabungkan
    mean = [
        weights["arima"] * arima_res.mean[i] + weights["ma"] * ma_mean[i]
        for i in range(horizon)
    ]

    # CI tetap dari ARIMA (baseline)
    return ForecastResult(
        horizon=horizon,
        mean=mean,
        lower=arima_res.lower,
        upper=arima_res.upper,
        method="Ensemble(ARIMA+MA)",
    )