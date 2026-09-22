# 🌐 SpatiaNomics

> **Urban-Economic Risk Intelligence** — Multi-resolution spatial-economic risk assessment framework for Indonesia.

[![Status](https://img.shields.io/badge/status-WIP-yellow)]()
[![Python](https://img.shields.io/badge/python-3.11-blue)]()
[![FastAPI](https://img.shields.io/badge/fastapi-0.115-green)]()
[![PyQt6](https://img.shields.io/badge/PyQt6-6.7-blue)]()
[![License](https://img.shields.io/badge/license-MIT-lightgrey)]()

---

## ⚠️ WORK IN PROGRESS

> **Status: Under active development. Not production-ready.**
>
> This repository is a **public diary** of an ongoing research & engineering project.
> APIs, schemas, and file structure **may change without notice**.
> Feel free to explore, but **do not use in production** (yet).

---

## 📖 What Is This?

**SpatiaNomics** is a client-server application for computing a **multi-resolution
spatial-economic risk index** for Indonesia, from **province level down to village (desa) level**.

The framework adapts a peatl& fire vulnerability model
([`mellygsln/peatfr`](https://github.com/mellygsln/peatfr)) to a broader
**Urban-Economic Risk Index (UERI)** — combining spatial-planning indicators
with regional-economic indicators across **7 administrative levels**.

Boundary data is sourced from [`cahyadsn/wilayah`](https://github.com/cahyadsn/wilayah)
(**91,162 records**, Kepmendagri 2025).

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│              PyQt6 Desktop Client (Data Entry)          │
│  • Field observation input                              │
│  • Supervisor verification                              │
│  • Offline-first cache                                  │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP (JSON)
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  FastAPI Server (:8000)                 │
│  • 25+ REST endpoints                                   │
│  • AI engine (ARIMA + LSTM/GRU ensemble)                │
│  • UERI calculation (Nelder-Mead optimization)          │
│  • XAI (Explainable AI)                                 │
│  • SQLite storage                                       │
└────────────────────────┬────────────────────────────────┘
                         │ HTML + REST
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  Web Dashboard (PWA)                    │
│  • Choropleth drill-down map (Leaflet)                  │
│  • KPI dashboard + charts (Chart.js)                    │
│  • Forecast with confidence interval                    │
│  • Field reports table                                  │
└─────────────────────────────────────────────────────────┘
```

---

## ✨ Current Features

| Feature | Status |
|---------|--------|
| Multi-level administrative hierarchy (7 levels) | ✅ |
| GeoJSON polygon rendering (Leaflet + drill-down) | ✅ |
| UERI engine with Nelder-Mead optimization | ✅ |
| XAI — Explainable AI with human-readable narrative | ✅ |
| ARIMA + Moving-Average ensemble forecast | ✅ |
| Field observation workflow (input → verify) | ✅ |
| Offline-first cache (client) | ✅ |
| Telegram bot integration | ✅ |
| PWA (manifest + service worker) | ✅ |
| LSTM / GRU deep learning model | 🚧 Planned |
| IoT sensor integration | 🚧 Planned |
| Cloudflare Tunnel deployment | 🚧 Planned |

---

## 🛠️ Tech Stack

**Backend**
- Python 3.11
- FastAPI + Uvicorn
- SQLAlchemy + SQLite
- Pandas, NumPy, SciPy, Statsmodels
- PyTorch (planned for LSTM/GRU)

**Client (Desktop)**
- PyQt6
- httpx
- loguru

**Web Dashboard**
- Jinja2 templates
- Leaflet.js
- Chart.js
- Vanilla JS + CSS

**DevOps**
- Anaconda environment
- Cloudflare Tunnel (planned)

---

## 🚀 Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/duhemen/spatialnomic.git
cd spatialnomic

# Buat conda environment
conda env create -f environment.yml
conda activate spatialnomic
```

### 2. Konfigurasi

```bash
cp .env.example .env
# Edit .env sesuai kebutuhan (opsional)
```

### 3. Download Data Wilayah

Unduh file dari [`cahyadsn/wilayah`](https://github.com/cahyadsn/wilayah):

```bash
mkdir -p data/raw
cd data/raw
curl.exe -L -o wilayah.sql "https://github.com/cahyadsn/wilayah/raw/refs/heads/master/db/wilayah.sql"
curl.exe -L -o wilayah_level_1_2.sql "https://github.com/cahyadsn/wilayah/raw/refs/heads/master/db/wilayah_level_1_2.sql"
```

### 4. Import Data

```bash
# Init database + seed basic
python scripts/init_db.py

# Import 91k+ wilayah
python scripts/import_boundaries.py --all

# Seed 20 field variables
python scripts/seed_field_variables.py

# Verifikasi
python scripts/check_data.py
```

### 5. Jalankan Aplikasi

**Terminal 1 — Server:**
```bash
python run_hybrid_server.py
# → http://localhost:8000
```

**Terminal 2 — Desktop Client:**
```bash
python run_client.py
```

**Buka Web Dashboard:**
```
http://localhost:8000/dashboard
```

---

## 📁 Project Structure

```
spatialnomic/
├── client/                 # PyQt6 desktop app (data entry)
│   ├── api/                # HTTP client wrapper
│   ├── core/               # Offline cache
│   └── gui/                # UI (Aurora Dark Theme)
├── server/                 # FastAPI backend
│   ├── api/                # REST routes + web routes
│   ├── core/               # Index calc, forecast, XAI
│   ├── templates/          # Jinja2 HTML
│   ├── static/             # CSS, JS, Leaflet
│   └── services/           # Telegram bot
├── data/                   # SQLite DB (gitignored)
├── scripts/                # Import & seed utilities
├── config/                 # Settings loader
└── logs/                   # Runtime logs (gitignored)
```

---

## 📚 API Endpoints

Ringkasan endpoint utama (buka `/docs` untuk lengkap):

```
GET  /api/health                          # Health check
GET  /api/wilayah/regions                 # List 7 region Indonesia
GET  /api/wilayah/geojson?level=...       # GeoJSON per level
GET  /api/wilayah/region-geojson/{key}    # GeoJSON 1 region
POST /api/ueri/calculate                  # Hitung UERI
POST /api/ueri/explain                    # XAI narasi
POST /api/forecast/run                    # Prediksi time-series
POST /api/index/composite                 # Core + field adjustment
GET  /api/custom-variable/list            # Field variables
POST /api/field-observation/create        # Input laporan lapangan
POST /api/field-observation/{id}/verify   # Verifikasi supervisor
```

---

## 🗺️ Roadmap

- [x] Phase 1 — Data foundation (91k wilayah + polygon)
- [x] Phase 2 — UERI engine + XAI
- [x] Phase 3 — Web dashboard (PWA)
- [x] Phase 4 — Desktop client (data entry)
- [x] Phase 5 — Field observation workflow
- [ ] Phase 6 — LSTM/GRU deep learning
- [ ] Phase 7 — IoT sensor integration
- [ ] Phase 8 — Cloudflare Tunnel deployment
- [ ] Phase 9 — Multi-user auth (JWT + RBAC)
- [ ] Phase 10 — Export PDF/Excel reports

---

## 🤝 Contributing

This is a **personal research project**, but feedback and suggestions are welcome.

- 🐛 Found a bug? Open an issue.
- 💡 Have an idea? Start a discussion.
- 📖 Using this for research? Let me know — always happy to hear.

---

## ⚖️ License

MIT License — see [`LICENSE`](LICENSE) file for details.

---

## 🙏 Credits

- **Boundary data**: [cahyadsn/wilayah](https://github.com/cahyadsn/wilayah) — Kepmendagri 2025
- **Boundary polygons**: [cahyadsn/wilayah_boundaries](https://github.com/cahyadsn/wilayah_boundaries)
- **Peatland fire model inspiration**: [mellygsln/peatfr](https://github.com/mellygsln/peatfr)
- **Basemap**: Esri Dark Gray Canvas
- **Maps library**: Leaflet.js
- **Charts**: Chart.js

---

## 📬 Contact

- GitHub: [@duhemen](https://github.com/duhemen)

---

<p align="center">
  <i>🌏 Top-Down Rigor. Bottom-Up Reality. Satu Peta.</i>
</p>

---