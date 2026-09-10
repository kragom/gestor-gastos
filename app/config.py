"""Configuración leída de variables de entorno."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # carpeta balance/

# Directorio de datos (en HF Spaces suele ser escribible /data o el propio repo)
DATA_DIR = Path(os.getenv("BALANCE_DATA_DIR", str(BASE_DIR / "data")))
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Ruta del fichero SQLite
DB_PATH = Path(os.getenv("BALANCE_DB_PATH", str(DATA_DIR / "balance.db")))

# URL SQLAlchemy: por defecto SQLite; permite Postgres si se define DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH.as_posix()}")

# Clave para firmar cookies de sesión
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")

# Persistencia en HuggingFace Dataset privado (opcional)
HF_TOKEN = os.getenv("HF_TOKEN")
HF_DATASET_REPO = os.getenv("HF_DATASET_REPO")  # p.ej. "hectorpc19/balance-db"
HF_DB_FILENAME = os.getenv("HF_DB_FILENAME", "balance.db")

# Segundos de espera para agrupar escrituras antes de subir a HF
SYNC_DEBOUNCE_SECONDS = float(os.getenv("SYNC_DEBOUNCE_SECONDS", "4"))

APP_NAME = "Balance"
APP_TAGLINE = "Tu economía, con claridad."
DEFAULT_CURRENCY = os.getenv("DEFAULT_CURRENCY", "EUR")
