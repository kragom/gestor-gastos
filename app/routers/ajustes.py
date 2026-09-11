"""Ajustes: perfil, apariencia, moneda."""
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import require_user
from ..models import User
from ..templating import templates
from ..store import save
from ..security import make_api_token

router = APIRouter()


@router.get("/ajustes", response_class=HTMLResponse)
def ajustes(request: Request, db: Session = Depends(get_db),
            user: User = Depends(require_user)):
    return templates.TemplateResponse("ajustes.html", {
        "request": request, "user": user, "active": "ajustes",
        "api_token": make_api_token(user.id),
        "api_base": str(request.base_url).rstrip("/"),
    })


@router.get("/ayuda", response_class=HTMLResponse)
def ayuda(request: Request, db: Session = Depends(get_db),
          user: User = Depends(require_user)):
    return templates.TemplateResponse("ayuda.html", {
        "request": request, "user": user, "active": "ayuda",
    })


@router.post("/ajustes/tema")
def set_tema(tema: str = Form(...), db: Session = Depends(get_db),
             user: User = Depends(require_user)):
    if tema in ("light", "dark", "system"):
        user.tema = tema
        save(db)
    return RedirectResponse("/ajustes", status_code=303)


@router.post("/ajustes/perfil")
def set_perfil(nombre: str = Form(...), moneda: str = Form("EUR"),
               db: Session = Depends(get_db), user: User = Depends(require_user)):
    user.nombre = nombre.strip() or user.nombre
    user.moneda = moneda
    save(db)
    return RedirectResponse("/ajustes", status_code=303)
