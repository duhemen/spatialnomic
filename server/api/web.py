"""Web dashboard routes (HTML)."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter(tags=["Web"])


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return RedirectResponse(url="/dashboard")


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/peta", response_class=HTMLResponse)
def peta(request: Request):
    return templates.TemplateResponse("peta.html", {"request": request})


@router.get("/prediksi", response_class=HTMLResponse)
def prediksi(request: Request):
    return templates.TemplateResponse("prediksi.html", {"request": request})


@router.get("/laporan", response_class=HTMLResponse)
def laporan(request: Request):
    return templates.TemplateResponse("laporan.html", {"request": request})