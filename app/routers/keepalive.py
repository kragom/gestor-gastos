"""Mantenimiento del keep-alive: actualizar el token de GitHub desde la web.

El usuario pega un nuevo Personal Access Token (PAT) de GitHub y la app lo
usa para (1) guardarlo como secret cifrado del repositorio y (2) relanzar el
workflow keep-alive. El token NO se almacena en la aplicación: se usa solo
durante la petición.
"""
import base64

import requests
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from ..config import GITHUB_REPO
from ..db import get_db
from ..deps import require_user
from ..models import User
from ..templating import templates

router = APIRouter()

API = "https://api.github.com"
SECRET_NAME = "KEEPALIVE_PAT"
WORKFLOW = "keepalive.yml"


def _headers(token: str) -> dict:
    return {"Authorization": f"token {token}",
            "Accept": "application/vnd.github+json"}


@router.get("/mantenimiento", response_class=HTMLResponse)
def mantenimiento(request: Request, ok: str = "", err: str = "", exp: str = "",
                  db: Session = Depends(get_db), user: User = Depends(require_user)):
    return templates.TemplateResponse("mantenimiento.html", {
        "request": request, "user": user, "active": "mantenimiento",
        "repo": GITHUB_REPO, "ok": ok, "err": err, "exp": exp,
    })


@router.post("/mantenimiento/token")
def actualizar_token(token: str = Form(...),
                     db: Session = Depends(get_db), user: User = Depends(require_user)):
    token = token.strip()
    if not token:
        return RedirectResponse("/mantenimiento?err=Token+vac%C3%ADo", status_code=303)
    try:
        # 1. Validar el token y leer su caducidad
        u = requests.get(f"{API}/user", headers=_headers(token), timeout=20)
        if u.status_code != 200:
            return RedirectResponse(
                "/mantenimiento?err=Token+no+v%C3%A1lido+o+sin+permisos", status_code=303)
        exp = u.headers.get("github-authentication-token-expiration", "")

        # 2. Obtener la clave pública del repo y cifrar el token
        pk = requests.get(f"{API}/repos/{GITHUB_REPO}/actions/secrets/public-key",
                          headers=_headers(token), timeout=20)
        if pk.status_code != 200:
            return RedirectResponse(
                "/mantenimiento?err=Sin+acceso+a+los+secrets+(revisa+permisos+repo)",
                status_code=303)
        pkj = pk.json()
        from nacl import encoding, public
        pub = public.PublicKey(pkj["key"].encode(), encoding.Base64Encoder())
        sealed = public.SealedBox(pub).encrypt(token.encode())
        enc = base64.b64encode(sealed).decode()

        # 3. Guardar/actualizar el secret
        s = requests.put(
            f"{API}/repos/{GITHUB_REPO}/actions/secrets/{SECRET_NAME}",
            headers=_headers(token),
            json={"encrypted_value": enc, "key_id": pkj["key_id"]}, timeout=20)
        if s.status_code not in (201, 204):
            return RedirectResponse(
                "/mantenimiento?err=No+se+pudo+guardar+el+secret", status_code=303)

        # 4. Relanzar el workflow keep-alive
        requests.post(
            f"{API}/repos/{GITHUB_REPO}/actions/workflows/{WORKFLOW}/dispatches",
            headers=_headers(token), json={"ref": "main"}, timeout=20)

        from urllib.parse import quote
        return RedirectResponse(
            f"/mantenimiento?ok=1&exp={quote(exp)}", status_code=303)
    except Exception as e:  # noqa: BLE001
        from urllib.parse import quote
        return RedirectResponse(
            f"/mantenimiento?err={quote('Error: ' + str(e)[:120])}", status_code=303)
