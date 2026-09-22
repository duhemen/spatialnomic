"""
Konfigurasi variabel per level administrasi SpatiaNomics.
7 level × 7 indeks.
"""
from __future__ import annotations

# ============================================================
# Konfigurasi 7 Level
# ============================================================
LEVEL_CONFIG = {
    "provinsi": {
        "index_name": "P-UERI",
        "full_name": "Provincial Urban-Economic Risk Index",
        "variables": ["P-USAI", "P-LLI", "P-IAI", "P-PEI",
                      "P-ZCEI", "P-FSI", "P-UOTI", "P-ISI"],
        "var_labels": {
            "P-USAI": "Urban Space Availability",
            "P-LLI":  "Liquidity & Economic Flow",
            "P-IAI":  "Infrastructure Access",
            "P-PEI":  "Productivity & Employment",
            "P-ZCEI": "Spatial Planning Quality",
            "P-FSI":  "Fiscal Capacity",
            "P-UOTI": "Urbanization Pressure",
            "P-ISI":  "Inflation Pressure",
        },
        "data_sources": ["BPS", "Bank Indonesia", "Kemendagri", "KLHK"],
        "risk_low_vars":  ["P-USAI", "P-LLI", "P-IAI", "P-PEI", "P-ZCEI", "P-FSI"],
        "risk_high_vars": ["P-UOTI", "P-ISI"],
    },
    "kabupaten": {
        "index_name": "RUERI",
        "full_name": "Rural Urban-Economic Risk Index",
        "variables": ["K-USAI", "K-LLI", "K-IAI", "K-PEI",
                      "K-ZCEI", "K-FSI", "K-ECI", "K-ISI"],
        "var_labels": {
            "K-USAI": "Land Use Balance",
            "K-LLI":  "Local Economic Vitality",
            "K-IAI":  "Rural Infrastructure Access",
            "K-PEI":  "Agricultural/Industrial Productivity",
            "K-ZCEI": "Zoning Compliance",
            "K-FSI":  "Fiscal Transfer",
            "K-ECI":  "Environmental Carrying",
            "K-ISI":  "Regional Inflation",
        },
        "data_sources": ["BPS", "Kemendagri", "Kemenkeu", "KLHK"],
        "risk_low_vars":  ["K-USAI", "K-LLI", "K-IAI", "K-PEI", "K-ZCEI", "K-FSI"],
        "risk_high_vars": ["K-ECI", "K-ISI"],
    },
    "kota": {
        "index_name": "UUERI",
        "full_name": "Urban Urban-Economic Risk Index",
        "variables": ["T-USAI", "T-LLI", "T-IAI", "T-PEI",
                      "T-ZCEI", "T-FSI", "T-UOTI", "T-ISI"],
        "var_labels": {
            "T-USAI": "Urban Density Balance",
            "T-LLI":  "Urban Economic Flow",
            "T-IAI":  "Urban Infrastructure",
            "T-PEI":  "Urban Productivity",
            "T-ZCEI": "Zoning Quality",
            "T-FSI":  "City Fiscal Capacity",
            "T-UOTI": "Urban Overcrowding & Traffic",
            "T-ISI":  "Urban Inflation",
        },
        "data_sources": ["BPS Kota", "BI", "Pemkot"],
        "risk_low_vars":  ["T-USAI", "T-LLI", "T-IAI", "T-PEI", "T-ZCEI", "T-FSI"],
        "risk_high_vars": ["T-UOTI", "T-ISI"],
    },
    "kecamatan": {
        "index_name": "CERI",
        "full_name": "Community Economic Risk Index",
        "variables": ["C-IAI", "C-PEI", "C-FSI", "C-USAI", "C-SVI", "C-ISI"],
        "var_labels": {
            "C-IAI":  "Service Accessibility",
            "C-PEI":  "Local Livelihood",
            "C-FSI":  "Development Fund",
            "C-USAI": "Land Use Change",
            "C-SVI":  "Social Vulnerability",
            "C-ISI":  "Local Price Index",
        },
        "data_sources": ["KemenDesa", "BPS Kec", "Kemenkeu", "Kemensos"],
        "risk_low_vars":  ["C-IAI", "C-PEI", "C-FSI", "C-USAI"],
        "risk_high_vars": ["C-SVI", "C-ISI"],
    },
    "desa": {
        "index_name": "VRI",
        "full_name": "Village Resilience Index",
        "variables": ["D-IAI", "D-FSI", "D-USAI", "D-SVI", "D-ECI"],
        "var_labels": {
            "D-IAI":  "Village Infrastructure",
            "D-FSI":  "Village Fund (Dana Desa)",
            "D-USAI": "Village Land Use",
            "D-SVI":  "Social Vulnerability",
            "D-ECI":  "Environmental Carrying",
        },
        "data_sources": ["SDGs Desa", "Siskeudes", "KLHK", "Kemensos"],
        "risk_low_vars":  ["D-IAI", "D-FSI", "D-USAI"],
        "risk_high_vars": ["D-SVI", "D-ECI"],
    },
    "kelurahan": {
        "index_name": "UCRI",
        "full_name": "Urban Community Resilience Index",
        "variables": ["L-IAI", "L-FSI", "L-UOTI", "L-SVI", "L-ISI"],
        "var_labels": {
            "L-IAI":  "Urban Service Access",
            "L-FSI":  "Urban Village Fund",
            "L-UOTI": "Micro Density",
            "L-SVI":  "Social Vulnerability",
            "L-ISI":  "Urban Cost of Living",
        },
        "data_sources": ["Pemkot", "APBD Kota", "DTKS", "BPS"],
        "risk_low_vars":  ["L-IAI", "L-FSI"],
        "risk_high_vars": ["L-UOTI", "L-SVI", "L-ISI"],
    },
    "dusun": {
        "index_name": "μR-Flag",
        "full_name": "Micro Risk Flag",
        "variables": ["M-DR", "M-ACC", "M-DD"],
        "var_labels": {
            "M-DR":  "Disaster Risk",
            "M-ACC": "Access Flag",
            "M-DD":  "Direct Data",
        },
        "data_sources": ["BPBD", "Warga", "RT/RW"],
        "is_rule_based": True,  # Tidak pakai weighted geometric
        "risk_low_vars":  [],
        "risk_high_vars": ["M-DR", "M-ACC", "M-DD"],
    },
}


def get_config(level: str) -> dict:
    """Ambil konfigurasi level. Fallback ke 'desa' kalau tidak ketemu."""
    return LEVEL_CONFIG.get(level, LEVEL_CONFIG["desa"])


def get_index_name(level: str) -> str:
    return get_config(level)["index_name"]