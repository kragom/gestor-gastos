"""Helper para guardar cambios y programar la sincronización con HF."""
from sqlalchemy.orm import Session

from . import persistence


def save(db: Session) -> None:
    db.commit()
    persistence.schedule_upload()
