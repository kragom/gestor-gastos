"""Hashing de contraseñas y sesiones firmadas por cookie."""
import bcrypt
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from .config import SECRET_KEY

_serializer = URLSafeTimedSerializer(SECRET_KEY, salt="balance-session")
_api_serializer = URLSafeTimedSerializer(SECRET_KEY, salt="balance-api")

COOKIE_NAME = "balance_session"
MAX_AGE = 60 * 60 * 24 * 30  # 30 días
API_MAX_AGE = 60 * 60 * 24 * 365 * 5  # ~5 años


def _to_bytes(password: str) -> bytes:
    # bcrypt solo admite hasta 72 bytes
    return password.encode("utf-8")[:72]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_to_bytes(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_to_bytes(password), hashed.encode("utf-8"))
    except Exception:
        return False


def make_session(user_id: int) -> str:
    return _serializer.dumps({"uid": user_id})


def read_session(token: str):
    try:
        data = _serializer.loads(token, max_age=MAX_AGE)
        return data.get("uid")
    except (BadSignature, SignatureExpired, Exception):
        return None


def make_api_token(user_id: int) -> str:
    """Token de larga duración para automatizaciones (Atajos de iOS).
    Firmado con SECRET_KEY; no se almacena en la base de datos."""
    return _api_serializer.dumps({"uid": user_id})


def read_api_token(token: str):
    try:
        data = _api_serializer.loads(token, max_age=API_MAX_AGE)
        return data.get("uid")
    except (BadSignature, SignatureExpired, Exception):
        return None
