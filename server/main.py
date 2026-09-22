"""
SpatiaNomics - FastAPI Server Entry Point
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger

from config.settings import settings, BASE_DIR
from server.database import init_db
from server.api.routes import router as api_router
from server.api.web import router as web_router


# ============================================================
# 1. Inisialisasi app
# ============================================================
app = FastAPI(
    title="SpatiaNomics API",
    description="Urban-Economic Risk Index & Spatial Forecasting Engine",
    version="0.1.0",
)


# ============================================================
# 2. Middleware
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# 3. Static files & templates
# ============================================================
static_dir = BASE_DIR / "server" / "static"
templates_dir = BASE_DIR / "server" / "templates"
static_dir.mkdir(parents=True, exist_ok=True)
templates_dir.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Daftarkan templates ke module web
from server.api import web as _web_module  # noqa: E402
_web_module.templates = Jinja2Templates(directory=str(templates_dir))


# ============================================================
# 4. Routers
# ============================================================
app.include_router(api_router)
app.include_router(web_router)


# ============================================================
# 5. Event handlers
# ============================================================
@app.on_event("startup")
def _startup():
    logger.info("🚀 SpatiaNomics server starting...")
    init_db()
    logger.success(f"DB initialized at {settings.DB_PATH}")


# ============================================================
# 6. Root endpoint (fallback API check)
# ============================================================
@app.get("/api")
def api_root():
    return {
        "app": "SpatiaNomics",
        "docs": "/docs",
        "dashboard": "/dashboard",
        "version": "0.1.0",
    }