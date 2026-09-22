"""
Imputation Module
Adopsi dari pendekatan `peatfr` (mellygsln/peatfr) untuk mengisi
data time-series yang bolong (missing values) di lapangan.

Metode:
- KNN Imputation (untuk data spasial/tabular)
- Spline Interpolation (untuk time-series)
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.impute import KNNImputer
from scipy.interpolate import CubicSpline
from loguru import logger


class TimeSeriesImputer:
    """Imputer hybrid: KNN untuk cross-sectional, Spline untuk longitudinal."""

    def __init__(self, knn_neighbors: int = 5, method: str = "hybrid"):
        self.knn_neighbors = knn_neighbors
        self.method = method  # "knn" | "spline" | "hybrid"
        self._knn: KNNImputer | None = None

    def fit_transform(
        self,
        df: pd.DataFrame,
        time_col: str = "date",
        group_col: str | None = None,
    ) -> pd.DataFrame:
        """
        Parameters
        ----------
        df : DataFrame dengan kolom numerik + time_col (+ group_col opsional)
        time_col : nama kolom waktu
        group_col : kolom grouping (mis. region_id) untuk spline per-region
        """
        df = df.copy()
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        logger.info(f"Imputasi pada {len(num_cols)} kolom numerik, metode={self.method}")

        if self.method in ("knn", "hybrid"):
            self._knn = KNNImputer(n_neighbors=self.knn_neighbors)
            df[num_cols] = self._knn.fit_transform(df[num_cols])

        if self.method in ("spline", "hybrid") and time_col in df.columns:
            df = self._spline_fill(df, num_cols, time_col, group_col)

        return df

    def _spline_fill(
        self,
        df: pd.DataFrame,
        num_cols: list[str],
        time_col: str,
        group_col: str | None,
    ) -> pd.DataFrame:
        """Spline cubic per grup (jika ada) untuk smoothing time-series."""
        df = df.sort_values(time_col)
        groups = df.groupby(group_col) if group_col else [(None, df)]

        for _, g in groups:
            x = np.arange(len(g))
            for col in num_cols:
                y = g[col].values
                mask = ~np.isnan(y)
                if mask.sum() < 4:
                    continue  # spline butuh minimal 4 titik
                try:
                    cs = CubicSpline(x[mask], y[mask], extrapolate=True)
                    y_filled = cs(x)
                    df.loc[g.index, col] = y_filled
                except Exception as e:
                    logger.warning(f"Spline gagal di kolom {col}: {e}")
        return df