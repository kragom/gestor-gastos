"""Reintegrables: gastos pendientes de reintegrar."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import require_user
from ..models import User, Transaction
from ..templating import templates
from ..store import save

router = APIRouter()


@router.get("/reintegrables", response_class=HTMLResponse)
def reintegrables(request: Request, db: Session = Depends(get_db),
                  user: User = Depends(require_user)):
    rows = (db.query(Transaction)
            .filter(Transaction.user_id == user.id, Transaction.es_reintegrable == True)  # noqa: E712
            .order_by(Transaction.reintegrado, Transaction.fecha.desc()).all())
    pendientes = [r for r in rows if not r.reintegrado]
    saldados = [r for r in rows if r.reintegrado]
    total_pend = round(sum(r.importe for r in pendientes), 2)
    total_sald = round(sum(r.importe for r in saldados), 2)
    return templates.TemplateResponse("reintegrables.html", {
        "request": request, "user": user, "active": "reintegrables",
        "pendientes": pendientes, "saldados": saldados,
        "total_pend": total_pend, "total_sald": total_sald,
    })


@router.post("/reintegrables/{tid}/toggle")
def toggle(tid: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    t = db.query(Transaction).filter(Transaction.id == tid, Transaction.user_id == user.id).first()
    if t:
        t.reintegrado = not t.reintegrado
        save(db)
    return RedirectResponse("/reintegrables", status_code=303)
