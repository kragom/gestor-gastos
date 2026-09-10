"""Gastos extraordinarios (previsiones)."""
from datetime import date

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import require_user
from ..models import User, Extraordinary
from ..templating import templates
from ..store import save

router = APIRouter()


@router.get("/gastos-extraordinarios", response_class=HTMLResponse)
def extraordinarios(request: Request, db: Session = Depends(get_db),
                    user: User = Depends(require_user)):
    rows = (db.query(Extraordinary).filter(Extraordinary.user_id == user.id)
            .order_by(Extraordinary.anio, Extraordinary.mes).all())
    return templates.TemplateResponse("extraordinarios.html", {
        "request": request, "user": user, "active": "extraordinarios",
        "rows": rows, "anio_actual": date.today().year, "mes_actual": date.today().month,
    })


@router.post("/gastos-extraordinarios/nuevo")
def crear(nombre: str = Form(...), mes: int = Form(...), anio: int = Form(...),
          importe: float = Form(0.0), notas: str = Form(""), repite_anual: str = Form(""),
          db: Session = Depends(get_db), user: User = Depends(require_user)):
    db.add(Extraordinary(user_id=user.id, nombre=nombre.strip() or "Previsión",
                         mes=mes, anio=anio, importe=abs(importe), notas=notas,
                         repite_anual=bool(repite_anual)))
    save(db)
    return RedirectResponse("/gastos-extraordinarios", status_code=303)


@router.post("/gastos-extraordinarios/{eid}/borrar")
def borrar(eid: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    e = db.query(Extraordinary).filter(Extraordinary.id == eid,
                                       Extraordinary.user_id == user.id).first()
    if e:
        db.delete(e)
        save(db)
    return RedirectResponse("/gastos-extraordinarios", status_code=303)
