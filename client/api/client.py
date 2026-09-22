"""HTTP Client ke FastAPI server."""
from __future__ import annotations
import time
import httpx
from loguru import logger
from client.config import SERVER_URL, REQUEST_TIMEOUT


class SpatiaNomicsClient:
    def __init__(self, base_url: str = SERVER_URL, max_retries: int = 3):
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self._client = httpx.Client(base_url=self.base_url, timeout=REQUEST_TIMEOUT)

    def _request(self, method: str, url: str, **kwargs):
        """Request dengan retry otomatis kalau koneksi drop."""
        last_exc = None
        for attempt in range(self.max_retries):
            try:
                r = self._client.request(method, url, **kwargs)
                r.raise_for_status()
                return r
            except (httpx.ConnectError, httpx.ReadError, httpx.RemoteProtocolError) as e:
                last_exc = e
                logger.debug(f"Request gagal (attempt {attempt+1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(1.5)
            except httpx.HTTPStatusError:
                raise  # 4xx/5xx: langsung raise, jangan retry
        raise last_exc

    def health(self) -> dict:
        return self._request("GET", "/api/health").json()

    def calculate_ueri(self, payload: dict) -> dict:
        return self._request("POST", "/api/ueri/calculate", json=payload).json()

    def explain_ueri(self, payload: dict) -> dict:
        return self._request("POST", "/api/ueri/explain", json=payload).json()

    def forecast(self, wilayah_kode: str, series: list[float], horizon: int = 7) -> dict:
        return self._request("POST", "/api/forecast/run", json={
            "wilayah_kode": wilayah_kode, "series": series, "horizon": horizon,
        }).json()

    def list_wilayah(self, level: str | None = None) -> list[dict]:
        params = {"level": level} if level else {}
        return self._request("GET", "/api/wilayah/list", params=params).json()

    def get_geojson(self, level: str = "provinsi", limit: int = 100) -> dict:
        return self._request("GET", "/api/wilayah/geojson",
                             params={"level": level, "limit": limit}).json()

    # ============ Multi-Level Index ============
    def get_variable_config(self, level: str) -> dict:
        return self._request("GET", f"/api/variable-config/{level}").json()

    def calculate_level_index(self, kode: str, level: str, values: dict) -> dict:
        return self._request("POST", "/api/index/calculate", json={
            "kode": kode, "level": level, "values": values,
        }).json()

    def calculate_composite(self, kode: str, level: str, values: dict) -> dict:
        return self._request("POST", "/api/index/composite", json={
            "kode": kode, "level": level, "values": values,
        }).json()

    # ============ Custom Variables ============
    def list_custom_variables(self, level: str | None = None, approved_only: bool = True) -> list[dict]:
        params = {"approved_only": approved_only}
        if level:
            params["level"] = level
        return self._request("GET", "/api/custom-variable/list", params=params).json()

    def create_custom_variable(self, payload: dict) -> dict:
        return self._request("POST", "/api/custom-variable/create", json=payload).json()

    # ============ Field Observations ============
    def create_field_observation(self, payload: dict) -> dict:
        return self._request("POST", "/api/field-observation/create", json=payload).json()

    def list_field_observations(self, wilayah_kode: str | None = None,
                                 verified_only: bool = False) -> list[dict]:
        params = {"verified_only": verified_only}
        if wilayah_kode:
            params["wilayah_kode"] = wilayah_kode
        return self._request("GET", "/api/field-observation/list", params=params).json()

    def verify_field_observation(self, obs_id: int, verified: bool,
                                  verified_by: str, reason: str | None = None) -> dict:
        return self._request("POST", f"/api/field-observation/{obs_id}/verify", json={
            "verified": verified, "verified_by": verified_by,
            "rejection_reason": reason,
        }).json()

    def get_field_observations_map(self, parent_kode: str | None = None) -> list[dict]:
        params = {}
        if parent_kode:
            params["parent_kode"] = parent_kode
        return self._request("GET", "/api/field-observation/map", params=params).json()

    def close(self):
        self._client.close()

    # ============ Region API ============
    def get_regions(self) -> list[dict]:
        """Ambil daftar 7 region Indonesia."""
        return self._request("GET", "/api/wilayah/regions").json()

    def get_region_geojson(self, region_key: str) -> dict:
        """GeoJSON semua provinsi dalam 1 region."""
        return self._request("GET", f"/api/wilayah/region-geojson/{region_key}").json()

    def get_geojson_children(self, parent_kode: str, level: str, limit: int = 500) -> dict:
        """GeoJSON anak wilayah dari parent tertentu."""
        return self._request("GET", "/api/wilayah/geojson",
                             params={"parent": parent_kode, "level": level, "limit": limit}).json()

    def count_children(self, kode: str) -> dict:
        """Hitung anak wilayah."""
        return self._request("GET", f"/api/wilayah/count/{kode}").json()