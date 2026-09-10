"""Sincronización del fichero SQLite con un HF Dataset privado.

- Al arrancar: descarga balance.db del dataset (si existe).
- Tras escrituras: sube balance.db con un debounce para agrupar cambios.

Si no hay HF_TOKEN / HF_DATASET_REPO configurados, todo funciona en local
sin sincronización (modo desarrollo).
"""
import shutil
import threading
import time
from pathlib import Path

from . import config

_lock = threading.Lock()
_timer: threading.Timer | None = None
_enabled = bool(config.HF_TOKEN and config.HF_DATASET_REPO)


def enabled() -> bool:
    return _enabled


def pull_db() -> None:
    """Descarga la base de datos del dataset al arrancar."""
    if not _enabled:
        return
    try:
        from huggingface_hub import hf_hub_download
        local = hf_hub_download(
            repo_id=config.HF_DATASET_REPO,
            filename=config.HF_DB_FILENAME,
            repo_type="dataset",
            token=config.HF_TOKEN,
        )
        config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(local, config.DB_PATH)
        print(f"[persistence] DB descargada de {config.HF_DATASET_REPO}")
    except Exception as e:  # noqa: BLE001
        print(f"[persistence] No se pudo descargar la DB (se usará una nueva): {e}")


def _do_upload() -> None:
    with _lock:
        if not config.DB_PATH.exists():
            return
        try:
            from huggingface_hub import HfApi
            api = HfApi(token=config.HF_TOKEN)
            api.upload_file(
                path_or_fileobj=str(config.DB_PATH),
                path_in_repo=config.HF_DB_FILENAME,
                repo_id=config.HF_DATASET_REPO,
                repo_type="dataset",
                commit_message="update balance.db",
            )
            print("[persistence] DB subida a HF Dataset")
        except Exception as e:  # noqa: BLE001
            print(f"[persistence] Error subiendo la DB: {e}")


def schedule_upload() -> None:
    """Programa una subida con debounce; agrupa varias escrituras seguidas."""
    global _timer
    if not _enabled:
        return
    if _timer is not None:
        _timer.cancel()
    _timer = threading.Timer(config.SYNC_DEBOUNCE_SECONDS, _do_upload)
    _timer.daemon = True
    _timer.start()


def flush() -> None:
    """Fuerza una subida inmediata (p.ej. al cerrar la app)."""
    global _timer
    if not _enabled:
        return
    if _timer is not None:
        _timer.cancel()
        _timer = None
    _do_upload()
