"""
SpatiaNomics - Konfigurasi Terpusat
Membaca .env dan menyediakan konstanta global.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Muat .env dari root project
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Direktori
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)


class Settings:
    """Wrapper sederhana untuk konfigurasi."""

    # Environment
    ENV: str = os.getenv("SPATIANOMICS_ENV", "development")
    DEBUG: bool = ENV == "development"

    # Server
    SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", 8000))
    SERVER_BASE_URL: str = os.getenv("SERVER_BASE_URL", "http://localhost:8000")

    # Database
    DB_PATH: str = str(BASE_DIR / os.getenv("DB_PATH", "data/spatianomics.db"))

    # Auth
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-secret-ganti-di-produksi")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", 480))

    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

    # Eksternal
    NASA_FIRMS_MAP_KEY: str = os.getenv("NASA_FIRMS_MAP_KEY", "")
    CLOUDFLARE_TUNNEL_TOKEN: str = os.getenv("CLOUDFLARE_TUNNEL_TOKEN", "")


settings = Settings()