"""Despliegue de Balance en HuggingFace.

EJECUTA ESTE SCRIPT DESDE UNA RED CON ACCESO A huggingface.co
(no funciona tras el proxy corporativo de Ford, que bloquea el dominio).

Qué hace:
  1. Crea (si no existe) el Dataset privado para la base de datos.
  2. Crea/convierte el Space a tipo Docker (privado).
  3. Sube todo el código al Space.
  4. Configura los Secrets del Space (SECRET_KEY, HF_TOKEN, HF_DATASET_REPO).

Uso:
  pip install huggingface_hub
  set HF_TOKEN=hf_xxx           (Windows)   |  export HF_TOKEN=hf_xxx  (Linux/Mac)
  python deploy.py

Variables opcionales (por si cambian los nombres):
  HF_USER          (por defecto: hectorpc19)
  HF_SPACE_REPO    (por defecto: <HF_USER>/balance)
  HF_DATASET_REPO  (por defecto: <HF_USER>/balance-db)
"""
import os
import secrets
import sys
from pathlib import Path

from huggingface_hub import HfApi

HERE = Path(__file__).resolve().parent

HF_USER = os.getenv("HF_USER", "hectorpc19")
TOKEN = os.getenv("HF_TOKEN")
SPACE_REPO = os.getenv("HF_SPACE_REPO", f"{HF_USER}/balance")
DATASET_REPO = os.getenv("HF_DATASET_REPO", f"{HF_USER}/balance-db")

# Ficheros/carpetas que NO se suben al Space.
IGNORE = ["__pycache__", "*.pyc", "data/*", "*.db", ".env", ".venv/*",
          "venv/*", "deploy.py", ".git/*"]


def main() -> int:
    if not TOKEN:
        print("ERROR: define la variable de entorno HF_TOKEN antes de ejecutar.")
        return 1

    api = HfApi(token=TOKEN)
    who = api.whoami()
    print(f"Autenticado como: {who.get('name')}")

    # 1) Dataset privado para la base de datos ---------------------------------
    print(f"\n[1/4] Asegurando Dataset privado {DATASET_REPO} ...")
    api.create_repo(repo_id=DATASET_REPO, repo_type="dataset",
                    private=True, exist_ok=True)
    print("      OK")

    # 2) Space Docker privado --------------------------------------------------
    print(f"\n[2/4] Asegurando Space Docker {SPACE_REPO} ...")
    try:
        api.create_repo(repo_id=SPACE_REPO, repo_type="space",
                        space_sdk="docker", private=True, exist_ok=True)
    except Exception as e:  # noqa: BLE001
        # En cuentas sin PRO, CREAR un Space Docker devuelve 402. Si el Space ya
        # existe, se convierte a Docker subiendo el README (sdk: docker) abajo.
        print(f"      Aviso: no se pudo crear (se asume que ya existe): {e}")
    # Si el Space existía con otro SDK, el README (sdk: docker) que subimos
    # a continuación lo convierte a Docker.
    print("      OK")

    # 3) Subida del código -----------------------------------------------------
    print(f"\n[3/4] Subiendo código a {SPACE_REPO} ...")
    api.upload_folder(
        repo_id=SPACE_REPO,
        repo_type="space",
        folder_path=str(HERE),
        ignore_patterns=IGNORE,
        commit_message="Deploy Balance (FastAPI + Docker)",
    )
    print("      OK")

    # 4) Secrets ---------------------------------------------------------------
    print(f"\n[4/4] Configurando Secrets del Space ...")
    secret_key = os.getenv("SECRET_KEY") or secrets.token_urlsafe(48)
    api.add_space_secret(SPACE_REPO, "SECRET_KEY", secret_key)
    api.add_space_secret(SPACE_REPO, "HF_TOKEN", TOKEN)
    api.add_space_secret(SPACE_REPO, "HF_DATASET_REPO", DATASET_REPO)
    print("      OK")

    print("\n=======================================================")
    print(f"  Despliegue lanzado. Abre:  https://huggingface.co/spaces/{SPACE_REPO}")
    print("  El Space tardará unos minutos en construir la imagen Docker.")
    print("  Usuario demo: demo@balance.local / demo1234")
    print("=======================================================")
    print("\nRECUERDA: regenera tu HF_TOKEN si lo compartiste en texto plano.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
