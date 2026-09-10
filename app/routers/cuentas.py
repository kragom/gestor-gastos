"""Cuentas: saldos, movimientos recientes, crear/archivar."""
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import require_user
from ..models import User, Account, Transaction
from ..templating import templates
from ..store import save
from ..services import finance

router = APIRouter()


@router.get("/cuentas", response_class=HTMLResponse)
def cuentas(request: Request, db: Session = Depends(get_db),
            user: User = Depends(require_user)):
    accounts = (db.query(Account).filter(Account.user_id == user.id)
                .order_by(Account.orden, Account.id).all())
    data = []
    for a in accounts:
        recientes = (db.query(Transaction).filter(Transaction.account_id == a.id)
                     .order_by(Transaction.fecha.desc(), Transaction.id.desc()).limit(3).all())
        data.append({"cuenta": a, "saldo": finance.account_balance(db, a), "recientes": recientes})
    return templates.TemplateResponse("cuentas.html", {
        "request": request, "user": user, "active": "cuentas", "data": data,
    })


@router.post("/cuentas/nueva")
def crear(nombre: str = Form(...), tipo: str = Form("otra"),
          saldo_inicial: float = Form(0.0), db: Session = Depends(get_db),
          user: User = Depends(require_user)):
    from sqlalchemy import func
    maxo = (db.query(func.coalesce(func.max(Account.orden), 0))
            .filter(Account.user_id == user.id).scalar() or 0)
    db.add(Account(user_id=user.id, nombre=nombre.strip() or "Cuenta", tipo=tipo,
                   saldo_inicial=saldo_inicial, orden=maxo + 1))
    save(db)
    return RedirectResponse("/cuentas", status_code=303)


@router.post("/cuentas/{aid}/archivar")
def archivar(aid: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    a = db.query(Account).filter(Account.id == aid, Account.user_id == user.id).first()
    if a:
        a.activa = not a.activa
        save(db)
    return RedirectResponse("/cuentas", status_code=303)


@router.post("/cuentas/{aid}/inicio")
def toggle_inicio(aid: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    a = db.query(Account).filter(Account.id == aid, Account.user_id == user.id).first()
    if a:
        a.mostrar_inicio = not a.mostrar_inicio
        save(db)
    return RedirectResponse("/cuentas", status_code=303)
