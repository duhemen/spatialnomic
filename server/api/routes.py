"""Endpoint API SpatiaNomics."""
from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime as _dt

from server.database import get_db
from server.schemas import (
    UERIRequest, UERIResponse,
    ForecastRequest, ForecastResponse,
    CustomVariableCreate, CustomVariableResponse, ApproveVariableRequest,
    FieldObservationCreate, FieldObservationResponse, VerifyObservationRequest,
    LevelIndexRequest, CompositeRequest,
)
from server.core import index_calc, forecasting

router = APIRouter(prefix="/api", tags=["SpatiaNomics"])


# ============================================================
# HEALTH
# ============================================================
@router.get("/health")
def health():
    return {"status": "ok", "app": "SpatiaNomics", "version": "0.1.0"}


# ============================================================
# UERI
# ============================================================
@router.post("/ueri/calculate", response_model=UERIResponse)
def calc_ueri(req: UERIRequest):
    values = req.model_dump(exclude={"wilayah_kode"})
    result = index_calc.calculate(values)
    return UERIResponse(
        wilayah_kode=req.wilayah_kode,
        ueri=result.ueri,
        category=result.category,
        contributions=result.contributions,
        weights=result.weights,
    )


@router.post("/ueri/optimize")
def optimize_ueri(X: list[list[float]], y: list[float]):
    """Endpoint untuk re-optimasi bobot via Nelder-Mead."""
    try:
        weights = index_calc.optimize_weights(X, y)
        return {"weights": weights}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/ueri/explain")
def explain(req: UERIRequest):
    """XAI: penjelasan UERI lengkap + narasi bahasa manusia."""
    from server.core import explain as xai
    values = req.model_dump(exclude={"wilayah_kode"})
    exp = xai.explain_ueri(values)
    return {
        "wilayah_kode": req.wilayah_kode,
        **exp.to_dict(),
    }


@router.get("/ueri/breakdown/{kode}")
def ueri_breakdown(kode: str, db: Session = Depends(get_db)):
    """Ambil kontribusi tiap variabel ke UERI (untuk XAI panel)."""
    from server.models import Observasi
    from server.core import index_calc as _ic

    obs = (
        db.query(Observasi)
        .filter(Observasi.wilayah_kode == kode)
        .order_by(Observasi.tanggal.desc())
        .first()
    )
    if not obs:
        raise HTTPException(404, "Wilayah belum punya observasi")

    values = {
        "USAI": obs.usai, "LLI": obs.lli, "IAI": obs.iai, "PEI": obs.pei,
        "ZCEI": obs.zcei, "FSI": obs.fsi, "UOTI": obs.uoti, "ISI": obs.isi,
    }
    result = _ic.calculate(values)
    return result.to_dict()


# ============================================================
# FORECAST
# ============================================================
@router.post("/forecast/run", response_model=ForecastResponse)
def run_forecast(req: ForecastRequest):
    try:
        res = forecasting.forecast_ensemble(req.series, horizon=req.horizon)
        return ForecastResponse(
            wilayah_kode=req.wilayah_kode,
            horizon=res.horizon,
            method=res.method,
            mean=res.mean,
            lower=res.lower,
            upper=res.upper,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# WILAYAH
# ============================================================
@router.get("/wilayah/list")
def list_wilayah(level: str | None = None, db: Session = Depends(get_db)):
    from server.models import Wilayah
    q = db.query(Wilayah)
    if level:
        q = q.filter(Wilayah.level == level)
    rows = q.limit(500).all()
    return [
        {"kode": r.kode, "nama": r.nama, "level": r.level, "parent": r.parent_kode}
        for r in rows
    ]


# ============================================================
# WILAYAH GEOJSON (Polygon untuk peta)
# ============================================================
@router.get("/wilayah/geojson")
def get_geojson(
    level: str = "provinsi",
    parent: str | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    Return GeoJSON FeatureCollection untuk peta choropleth.
    Selalu output MultiPolygon depth 4 yang valid.
    UERI: dari observasi terbaru, atau deterministik dari kode wilayah.
    """
    from server.models import Wilayah, Observasi
    import json as _json
    import hashlib

    q = db.query(Wilayah).filter(Wilayah.level == level)
    if parent:
        q = q.filter(Wilayah.parent_kode == parent)
    rows = q.limit(limit).all()

    # ==========================================================
    # Helper: UERI deterministik
    # ==========================================================
    def _ueri_from_kode(kode: str):
        h = int(hashlib.md5(kode.encode()).hexdigest()[:8], 16)
        u = (h % 1000) / 1000.0
        if u < 0.3:
            cat = "AMAN"
        elif u < 0.6:
            cat = "WASPADA"
        elif u < 0.8:
            cat = "SIAGA"
        else:
            cat = "BAHAYA"
        return round(u, 4), cat

    # ==========================================================
    # Helper: Geometry Sanitizer (depth-based)
    # ==========================================================
    def _is_point(x):
        """Cek apakah x = [lng, lat] dengan angka valid."""
        return (
            isinstance(x, list) and len(x) == 2
            and isinstance(x[0], (int, float)) and not isinstance(x[0], bool)
            and isinstance(x[1], (int, float)) and not isinstance(x[1], bool)
        )

    def _clean_ring(x):
        """Bersihkan ring: hanya titik valid, minimal 4 titik, ring tertutup."""
        if not isinstance(x, list):
            return None
        pts = [p for p in x if _is_point(p)]
        if len(pts) < 4:
            return None
        if pts[0] != pts[-1]:
            pts.append(pts[0])
        return pts

    def _clean_polygon(x):
        """Bersihkan polygon: minimal 1 ring."""
        if not isinstance(x, list):
            return None
        rings = [_clean_ring(r) for r in x]
        rings = [r for r in rings if r is not None]
        return rings if rings else None

    def _to_multipolygon(coords):
        """
        Konversi apapun ke MultiPolygon depth 4 secara aman.
        Deteksi struktur dari kedalaman array, bukan label tipe.
        """
        if not isinstance(coords, list) or not coords:
            return None

        first = coords[0]
        if not isinstance(first, list):
            return None

        # CASE 1: coords = ring tunggal [pt, pt, ...]
        if _is_point(first):
            ring = _clean_ring(coords)
            if not ring:
                return None
            return [[ring]]

        # Cek elemen lebih dalam
        first_inner = first[0] if first else None
        if not isinstance(first_inner, list):
            return None

        # CASE 2: coords = list of rings (Polygon depth 3)
        if _is_point(first_inner):
            polygon = _clean_polygon(coords)
            if not polygon:
                return None
            return [polygon]

        # CASE 3: coords = list of polygons (MultiPolygon depth 4)
        polygons = [_clean_polygon(p) for p in coords]
        polygons = [p for p in polygons if p is not None]
        return polygons if polygons else None

    def _normalize_geometry(geom):
        """
        Normalize input apapun ke MultiPolygon depth 4 yang valid.
        Abaikan label type — deteksi dari struktur coordinates.
        """
        if not isinstance(geom, dict):
            return None

        coords = geom.get("coordinates")
        if not coords:
            return None

        new_coords = _to_multipolygon(coords)
        if not new_coords:
            return None

        return {
            "type": "MultiPolygon",
            "coordinates": new_coords,
        }

    # ==========================================================
    # Main loop
    # ==========================================================
    features = []
    skipped = 0
    for r in rows:
        # UERI
        obs = (
            db.query(Observasi)
            .filter(Observasi.wilayah_kode == r.kode)
            .order_by(Observasi.tanggal.desc())
            .first()
        )
        if obs and obs.ueri is not None:
            ueri = obs.ueri
            cat = obs.kategori or "WASPADA"
        else:
            ueri, cat = _ueri_from_kode(r.kode)

        # Ambil geometry
        raw_geom = None
        if r.geojson:
            try:
                raw_geom = _json.loads(r.geojson)
            except Exception:
                raw_geom = None

        # Fallback: dummy square
        if not raw_geom and r.latitude and r.longitude:
            d = 0.5
            lat, lng = r.latitude, r.longitude
            raw_geom = {
                "type": "Polygon",
                "coordinates": [[
                    [lng - d, lat - d], [lng + d, lat - d],
                    [lng + d, lat + d], [lng - d, lat + d],
                    [lng - d, lat - d],
                ]],
            }

        # Normalize
        geom = _normalize_geometry(raw_geom)
        if not geom:
            skipped += 1
            continue

        features.append({
            "type": "Feature",
            "properties": {
                "kode": r.kode,
                "nama": r.nama,
                "level": r.level,
                "ibukota": r.ibukota,
                "luas_km2": r.luas_km2,
                "penduduk": r.penduduk,
                "ueri": float(ueri),
                "category": cat,
            },
            "geometry": geom,
        })

    return {"type": "FeatureCollection", "features": features}


# ============================================================
# MULTI-LEVEL INDEX
# ============================================================
@router.get("/variable-config/{level}")
def get_variable_config(level: str):
    """Konfigurasi variabel untuk level tertentu."""
    from server.core.variable_config import get_config
    cfg = get_config(level)
    return {
        "level": level,
        "index_name": cfg["index_name"],
        "full_name": cfg["full_name"],
        "variables": cfg["variables"],
        "var_labels": cfg["var_labels"],
        "data_sources": cfg.get("data_sources", []),
        "is_rule_based": cfg.get("is_rule_based", False),
    }


@router.post("/index/calculate")
def calc_level_index(req: LevelIndexRequest):
    """Hitung indeks untuk level apapun."""
    try:
        return index_calc.calculate_for_level(req.kode, req.values, req.level)
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/index/composite")
def calc_composite(req: CompositeRequest, db: Session = Depends(get_db)):
    """Hitung composite (core + field adjustment)."""
    try:
        return index_calc.calculate_composite(req.kode, req.values, req.level, db)
    except Exception as e:
        raise HTTPException(400, str(e))


# ============================================================
# CUSTOM VARIABLES CRUD
# ============================================================
@router.get("/custom-variable/list", response_model=list[CustomVariableResponse])
def list_custom_vars(
    level: str | None = None,
    approved_only: bool = True,
    db: Session = Depends(get_db),
):
    from server.models import CustomVariable
    q = db.query(CustomVariable).filter(CustomVariable.is_active == True)  # noqa: E712
    if approved_only:
        q = q.filter(CustomVariable.is_approved == True)  # noqa: E712
    if level:
        q = q.filter(
            (CustomVariable.level_target == "semua") |
            (CustomVariable.level_target.like(f"%{level}%"))
        )
    return q.order_by(CustomVariable.nama).all()


@router.post("/custom-variable/create", response_model=CustomVariableResponse)
def create_custom_var(req: CustomVariableCreate, db: Session = Depends(get_db)):
    from server.models import CustomVariable, AuditLog
    if db.query(CustomVariable).filter(CustomVariable.kode == req.kode).first():
        raise HTTPException(400, f"Kode {req.kode} sudah ada")
    var = CustomVariable(**req.model_dump(), is_approved=False)
    db.add(var)
    db.add(AuditLog(entity="custom_variable", action="create",
                    actor=req.created_by, payload=req.model_dump_json()))
    db.commit()
    db.refresh(var)
    return var


@router.post("/custom-variable/{var_id}/approve", response_model=CustomVariableResponse)
def approve_custom_var(var_id: int, req: ApproveVariableRequest, db: Session = Depends(get_db)):
    from server.models import CustomVariable, AuditLog
    var = db.query(CustomVariable).get(var_id)
    if not var:
        raise HTTPException(404, "Variabel tidak ditemukan")
    var.is_approved = req.approved
    var.is_active = req.approved
    var.approved_by = req.approved_by
    var.approved_at = _dt.utcnow()
    db.add(AuditLog(entity="custom_variable", entity_id=var.id,
                    action="approve" if req.approved else "reject",
                    actor=req.approved_by))
    db.commit()
    db.refresh(var)
    return var


# ============================================================
# FIELD OBSERVATIONS CRUD
# ============================================================
@router.get("/field-observation/list", response_model=list[FieldObservationResponse])
def list_field_obs(
    wilayah_kode: str | None = None,
    verified_only: bool = False,
    limit: int = 200,
    db: Session = Depends(get_db),
):
    from server.models import FieldObservation
    q = db.query(FieldObservation)
    if wilayah_kode:
        q = q.filter(FieldObservation.wilayah_kode == wilayah_kode)
    if verified_only:
        q = q.filter(
            FieldObservation.verified == True,  # noqa: E712
            FieldObservation.rejected == False,  # noqa: E712
        )
    return q.order_by(FieldObservation.timestamp.desc()).limit(limit).all()


@router.post("/field-observation/create", response_model=FieldObservationResponse)
def create_field_obs(req: FieldObservationCreate, db: Session = Depends(get_db)):
    from server.models import FieldObservation, AuditLog, CustomVariable
    from loguru import logger as _log

    # Cek duplikat via local_uuid (untuk offline sync)
    if req.local_uuid:
        exist = db.query(FieldObservation).filter(
            FieldObservation.local_uuid == req.local_uuid
        ).first()
        if exist:
            return exist

    obs = FieldObservation(**req.model_dump(), verified=False, rejected=False)
    db.add(obs)
    db.add(AuditLog(entity="field_observation", action="create",
                    actor=req.observer, payload=req.model_dump_json()))
    db.commit()
    db.refresh(obs)

    # Kalau severity tinggi → trigger alert
    var = db.query(CustomVariable).filter(CustomVariable.kode == req.variable_kode).first()
    if var and var.severity_weight >= 0.9 and not obs.verified:
        from server.services.telegram_bot import notify_supervisor_new_critical
        try:
            notify_supervisor_new_critical(obs, var, db)
        except Exception as e:
            _log.warning(f"Telegram notify failed: {e}")

    return obs


@router.post("/field-observation/{obs_id}/verify", response_model=FieldObservationResponse)
def verify_field_obs(obs_id: int, req: VerifyObservationRequest, db: Session = Depends(get_db)):
    from server.models import FieldObservation, AuditLog
    obs = db.query(FieldObservation).get(obs_id)
    if not obs:
        raise HTTPException(404, "Laporan tidak ditemukan")
    obs.verified = req.verified
    obs.rejected = not req.verified
    obs.verified_by = req.verified_by
    obs.verified_at = _dt.utcnow()
    if not req.verified:
        obs.rejection_reason = req.rejection_reason
    db.add(AuditLog(entity="field_observation", entity_id=obs.id,
                    action="approve" if req.verified else "reject",
                    actor=req.verified_by,
                    payload=req.rejection_reason))
    db.commit()
    db.refresh(obs)
    return obs


@router.get("/field-observation/map")
def field_obs_map(
    parent_kode: str | None = None,
    db: Session = Depends(get_db),
):
    """Field observations untuk ditampilkan di peta (marker)."""
    from server.models import FieldObservation, CustomVariable, Wilayah
    q = db.query(FieldObservation, CustomVariable).join(
        CustomVariable, FieldObservation.variable_kode == CustomVariable.kode
    ).filter(
        FieldObservation.verified == True,   # noqa: E712
        FieldObservation.rejected == False,   # noqa: E712
    )
    if parent_kode:
        q = q.join(Wilayah, FieldObservation.wilayah_kode == Wilayah.kode).filter(
            Wilayah.parent_kode == parent_kode
        )
    rows = q.limit(500).all()
    return [{
        "id": obs.id,
        "wilayah_kode": obs.wilayah_kode,
        "variable_kode": var.kode,
        "variable_nama": var.nama,
        "severity": var.severity_weight,
        "nilai": obs.nilai,
        "catatan": obs.catatan,
        "latitude": obs.latitude,
        "longitude": obs.longitude,
        "observer": obs.observer,
        "timestamp": obs.timestamp.isoformat() if obs.timestamp else None,
    } for obs, var in rows]

# ============================================================
# REGION & DRILL-DOWN
# ============================================================
@router.get("/wilayah/regions")
def list_regions_endpoint():
    """Daftar 7 region (pulau besar) Indonesia."""
    from server.core.region_config import list_regions
    return list_regions()


@router.get("/wilayah/region-geojson/{region_key}")
def region_geojson(region_key: str):
    """
    Return GeoJSON polygon SEMUA provinsi dalam 1 region.
    Untuk tampilan awal drill-down.
    """
    from server.core.region_config import get_region
    from server.models import Wilayah, Observasi
    import json as _json
    import hashlib

    region = get_region(region_key)
    if not region:
        raise HTTPException(404, f"Region '{region_key}' tidak ditemukan")

    # Ambil provinsi berdasarkan prefix
    from server.database import SessionLocal
    db = SessionLocal()
    try:
        prefixes = region["prefixes"]
        q = db.query(Wilayah).filter(
            Wilayah.level == "provinsi",
            Wilayah.kode.in_(prefixes),
        )
        rows = q.all()

        def _ueri_from_kode(kode: str):
            h = int(hashlib.md5(kode.encode()).hexdigest()[:8], 16)
            u = (h % 1000) / 1000.0
            cat = ("AMAN" if u < 0.3 else
                   "WASPADA" if u < 0.6 else
                   "SIAGA" if u < 0.8 else "BAHAYA")
            return round(u, 4), cat

        def _is_point(x):
            return (isinstance(x, list) and len(x) == 2
                    and isinstance(x[0], (int, float)) and not isinstance(x[0], bool)
                    and isinstance(x[1], (int, float)) and not isinstance(x[1], bool))

        def _clean_ring(x):
            if not isinstance(x, list): return None
            pts = [p for p in x if _is_point(p)]
            if len(pts) < 4: return None
            if pts[0] != pts[-1]: pts.append(pts[0])
            return pts

        def _clean_polygon(x):
            if not isinstance(x, list): return None
            rings = [r for r in (_clean_ring(r) for r in x) if r]
            return rings if rings else None

        def _to_multipolygon(coords):
            if not isinstance(coords, list) or not coords: return None
            first = coords[0]
            if not isinstance(first, list): return None
            if _is_point(first):
                r = _clean_ring(coords)
                return [[r]] if r else None
            inner = first[0] if first else None
            if not isinstance(inner, list): return None
            if _is_point(inner):
                p = _clean_polygon(coords)
                return [p] if p else None
            polys = [p for p in (_clean_polygon(p) for p in coords) if p]
            return polys if polys else None

        features = []
        for r in rows:
            obs = (db.query(Observasi)
                   .filter(Observasi.wilayah_kode == r.kode)
                   .order_by(Observasi.tanggal.desc()).first())
            if obs and obs.ueri is not None:
                ueri, cat = obs.ueri, (obs.kategori or "WASPADA")
            else:
                ueri, cat = _ueri_from_kode(r.kode)

            raw = None
            if r.geojson:
                try: raw = _json.loads(r.geojson)
                except Exception: pass

            if not raw:
                continue

            coords = raw.get("coordinates")
            new_coords = _to_multipolygon(coords)
            if not new_coords: continue

            features.append({
                "type": "Feature",
                "properties": {
                    "kode": r.kode, "nama": r.nama, "level": r.level,
                    "ibukota": r.ibukota, "luas_km2": r.luas_km2,
                    "penduduk": r.penduduk, "ueri": float(ueri), "category": cat,
                },
                "geometry": {"type": "MultiPolygon", "coordinates": new_coords},
            })

        return {
            "type": "FeatureCollection",
            "features": features,
            "region": region,
        }
    finally:
        db.close()


@router.get("/wilayah/count/{kode}")
def wilayah_count_children(kode: str, db: Session = Depends(get_db)):
    """
    Hitung berapa anak wilayah dari kode ini (untuk label drill-down).
    Mis. kode='11' → berapa kabupaten di Aceh.
    """
    from server.models import Wilayah
    rows = db.query(Wilayah).filter(Wilayah.parent_kode == kode).all()

    # Kelompokkan per level
    counts = {}
    for r in rows:
        counts[r.level] = counts.get(r.level, 0) + 1

    return {
        "kode": kode,
        "children_count": len(rows),
        "breakdown": counts,
    }