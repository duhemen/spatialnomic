"""SQLAlchemy ORM models — SpatiaNomics."""
from __future__ import annotations
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
)
from server.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(32), default="viewer")   # admin|supervisor|petugas|viewer
    full_name = Column(String(128))
    created_at = Column(DateTime, default=datetime.utcnow)


class Wilayah(Base):
    """Batas wilayah administratif (7 level)."""
    __tablename__ = "wilayah"
    id = Column(Integer, primary_key=True, index=True)
    kode = Column(String(16), unique=True, index=True, nullable=False)
    nama = Column(String(128), nullable=False)
    level = Column(String(16), nullable=False, index=True)  # provinsi|kabupaten|kota|kecamatan|desa|kelurahan|dusun
    parent_kode = Column(String(16), index=True)

    # Koordinat & dasar
    latitude = Column(Float)
    longitude = Column(Float)
    ibukota = Column(String(128), nullable=True)
    elevasi = Column(Float, nullable=True)
    timezone = Column(Integer, nullable=True)
    luas_km2 = Column(Float, nullable=True)
    penduduk = Column(Float, nullable=True)
    path_raw = Column(Text, nullable=True)
    geojson = Column(Text, nullable=True)
    status = Column(Integer, nullable=True)

    # Level-aware metadata
    index_type = Column(String(16), nullable=True)      # P-UERI, RUERI, VRI, dst.
    available_vars = Column(Text, nullable=True)        # JSON list


class Observasi(Base):
    """Data observasi core variables (flexible JSON)."""
    __tablename__ = "observasi"
    id = Column(Integer, primary_key=True, index=True)
    wilayah_kode = Column(String(16), index=True, nullable=False)
    tanggal = Column(DateTime, index=True, nullable=False, default=datetime.utcnow)
    variabel_json = Column(Text)                        # {"D-IAI": 0.65, "D-FSI": 0.4}
    index_score = Column(Float)
    index_type = Column(String(16))
    kategori = Column(String(16))


class CustomVariable(Base):
    """Registry variabel custom (field variables)."""
    __tablename__ = "custom_variable"
    id = Column(Integer, primary_key=True, index=True)
    kode = Column(String(32), unique=True, index=True, nullable=False)
    nama = Column(String(128), nullable=False)
    deskripsi = Column(Text)
    level_target = Column(String(16), index=True)       # provinsi|kabupaten|kota|kecamatan|desa|kelurahan|dusun|semua
    tipe = Column(String(16), default="boolean")        # boolean|scale|count
    severity_weight = Column(Float, default=0.5)        # 0-1
    is_active = Column(Boolean, default=True, index=True)
    is_approved = Column(Boolean, default=False)        # butuh approval supervisor
    created_by = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_by = Column(String(64), nullable=True)
    approved_at = Column(DateTime, nullable=True)


class FieldObservation(Base):
    """Laporan lapangan dari petugas."""
    __tablename__ = "field_observation"
    id = Column(Integer, primary_key=True, index=True)
    wilayah_kode = Column(String(16), index=True, nullable=False)
    variable_kode = Column(String(32), index=True, nullable=False)
    nilai = Column(Float, default=1.0)                  # boolean: 0/1, scale: 0-1, count: n
    catatan = Column(Text)
    foto_path = Column(String(255))
    latitude = Column(Float)
    longitude = Column(Float)
    observer = Column(String(64), index=True)
    verified = Column(Boolean, default=False, index=True)
    verified_by = Column(String(64), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    rejected = Column(Boolean, default=False)
    rejection_reason = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    # Sync metadata untuk offline-first
    local_uuid = Column(String(64), unique=True, index=True)  # client-generated
    synced_at = Column(DateTime, nullable=True)


class PredictionCache(Base):
    __tablename__ = "prediction_cache"
    id = Column(Integer, primary_key=True, index=True)
    wilayah_kode = Column(String(16), index=True)
    horizon = Column(Integer)
    method = Column(String(64))
    payload = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class AlertLog(Base):
    __tablename__ = "alert_log"
    id = Column(Integer, primary_key=True, index=True)
    wilayah_kode = Column(String(16), index=True)
    index_score = Column(Float)
    index_type = Column(String(16))
    kategori = Column(String(16))
    message = Column(Text)
    sent_telegram = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    """Audit trail untuk perubahan variabel & laporan."""
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True, index=True)
    entity = Column(String(32), index=True)             # custom_variable|field_observation|wilayah
    entity_id = Column(Integer, index=True)
    action = Column(String(32))                          # create|update|delete|approve|reject
    actor = Column(String(64))
    payload = Column(Text)                               # JSON diff
    created_at = Column(DateTime, default=datetime.utcnow, index=True)