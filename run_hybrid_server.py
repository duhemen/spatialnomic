"""
SpatiaNomics - Hybrid Server Runner
Hanya nonton folder server/, config/ — tidak client/
"""
import subprocess
import sys
from config.settings import settings


def main():
    print(f"🚀 Menjalankan SpatiaNomics Server di http://{settings.SERVER_HOST}:{settings.SERVER_PORT}")
    print(f"   Mode: {'DEBUG (auto-reload)' if settings.DEBUG else 'PRODUCTION'}")
    
    cmd = [
        sys.executable, "-m", "uvicorn",
        "server.main:app",
        "--host", settings.SERVER_HOST,
        "--port", str(settings.SERVER_PORT),
    ]
    
    # ⭐ Hanya nonton folder server/ dan config/ — JANGAN client/
    if settings.DEBUG:
        cmd.extend([
            "--reload",
            "--reload-dir", "server",
            "--reload-dir", "config",
        ])
    
    subprocess.run(cmd)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Server dihentikan. Sampai jumpa!")