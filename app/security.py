"""Hashing de contraseñas y sesiones firmadas por cookie."""
import bcrypt
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from .config import SECRET_KEY

_serializer = URLSafeTimedSerializer(SECRET_KEY, salt="balance-session")

COOKIE_NAME = "balance_session"
MAX_AGE = 60 * 60 * 24 * 30  # 30 días


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
