"""Pydantic schemas (request/response)."""
from __future__ import annotations
from datetime import datetime 
from typing import Optional
from pydantic import BaseModel, Field


class UERIRequest(BaseModel):
    wilayah_kode: str = Field(..., description="Kode wilayah")
    usai: float = Field(0.5, ge=0, le=1)
    lli: float = Field(0.5, ge=0, le=1)
    iai: float = Field(0.5, ge=0, le=1)
    pei: float = Field(0.5, ge=0, le=1)
    zcei: float = Field(0.5, ge=0, le=1)
    fsi: float = Field(0.5, ge=0, le=1)
    uoti: float = Field(0.5, ge=0, le=1)
    isi: float = Field(0.5, ge=0, le=1)


class UERIResponse(BaseModel):
    wilayah_kode: str
    ueri: float
    category: str
    contributions: dict
    weights: dict


class ForecastRequest(BaseModel):
    wilayah_kode: str
    series: list[float]
    horizon: int = 7


class ForecastResponse(BaseModel):
    wilayah_kode: str
    horizon: int
    method: str
    mean: list[float]
    lower: list[float]
    upper: list[float]


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# ============================================================
# Custom Variable
# ============================================================
class CustomVariableCreate(BaseModel):
    kode: str = Field(..., max_length=32)
    nama: str = Field(..., max_length=128)
    deskripsi: str | None = None
    level_target: str = "semua"
    tipe: str = "boolean"
    severity_weight: float = Field(0.5, ge=0, le=1)
    created_by: str = "anonymous"


class CustomVariableResponse(BaseModel):
    id: int
    kode: str
    nama: str
    deskripsi: str | None
    level_target: str
    tipe: str
    severity_weight: float
    is_active: bool
    is_approved: bool
    created_by: str | None

    class Config:
        from_attributes = True


class ApproveVariableRequest(BaseModel):
    approved: bool
    approved_by: str


# ============================================================
# Field Observation
# ============================================================
class FieldObservationCreate(BaseModel):
    wilayah_kode: str
    variable_kode: str
    nilai: float = 1.0
    catatan: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    observer: str = "anonymous"
    local_uuid: str | None = None


class FieldObservationResponse(BaseModel):
    id: int
    wilayah_kode: str
    variable_kode: str
    nilai: float
    catatan: str | None
    latitude: float | None
    longitude: float | None
    observer: str | None
    verified: bool
    rejected: bool
    timestamp: datetime
    local_uuid: str | None

    class Config:
        from_attributes = True


class VerifyObservationRequest(BaseModel):
    verified: bool
    verified_by: str
    rejection_reason: str | None = None


# ============================================================
# Composite / Multi-level Index
# ============================================================
class LevelIndexRequest(BaseModel):
    kode: str
    level: str
    values: dict                  # {"D-IAI": 0.65, ...}


class CompositeRequest(BaseModel):
    kode: str
    level: str
    values: dict                  # {"D-IAI": 0.65, ...}