"""Motor y sesión de SQLAlchemy."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from .config import DATABASE_URL

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from . import models  # noqa: F401  (registra los modelos)
    Base.metadata.create_all(bind=engine)


def migrate():
    """Migraciones ligeras para bases de datos ya existentes (SQLite)."""
    if not DATABASE_URL.startswith("sqlite"):
        return
    from sqlalchemy import text
    with engine.begin() as conn:
        cols = [r[1] for r in conn.execute(text("PRAGMA table_info(transactions)"))]
        if "cuenta_destino_id" not in cols:
            conn.execute(text(
                "ALTER TABLE transactions ADD COLUMN cuenta_destino_id INTEGER"))
