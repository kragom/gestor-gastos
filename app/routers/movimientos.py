"""Movimientos: listado con filtros, alta/edición/borrado y exportación."""
from datetime import date, datetime

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import require_user
from ..models import User, Account, Category, Transaction
from ..templating import templates
from ..store import save
from ..services import finance, export

router = APIRouter()


def _filtered(db: Session, user_id: int, q, tipo, cuenta, categoria, desde, hasta):
    query = db.query(Transaction).filter(Transaction.user_id == user_id)
    if q:
        query = query.filter(Transaction.concepto.ilike(f"%{q}%"))
    if tipo in ("gasto", "ingreso"):
        query = query.filter(Transaction.tipo == tipo)
    if cuenta:
        query = query.filter(Transaction.account_id == int(cuenta))
    if categoria:
        query = query.filter(Transaction.category_id == int(categoria))
    if desde:
        try:
            query = query.filter(Transaction.fecha >= date.fromisoformat(desde))
        except ValueError:
            pass
    if hasta:
        try:
            query = query.filter(Transaction.fecha <= date.fromisoformat(hasta))
        except ValueError:
            pass
    return query.order_by(Transaction.fecha.desc(), Transaction.id.desc())


@router.get("/movimientos", response_class=HTMLResponse)
def movimientos(request: Request, q: str = "", tipo: str = "", cuenta: str = "",
                categoria: str = "", desde: str = "", hasta: str = "",
                db: Session = Depends(get_db), user: User = Depends(require_user)):
    rows = _filtered(db, user.id, q, tipo, cuenta, categoria, desde, hasta).all()
    grouped = finance.transactions_grouped_by_day(rows)
    accounts = db.query(Account).filter(Account.user_id == user.id).order_by(Account.orden).all()
    categories = db.query(Category).filter(Category.user_id == user.id).order_by(Category.orden).all()
    return templates.TemplateResponse("movimientos.html", {
        "request": request, "user": user, "active": "movimientos",
        "grouped": grouped, "accounts": accounts, "categories": categories,
        "f": {"q": q, "tipo": tipo, "cuenta": cuenta, "categoria": categoria,
              "desde": desde, "hasta": hasta},
        "total": len(rows),
    })


@router.post("/movimientos/nuevo")
def crear(request: Request, concepto: str = Form(...), importe: float = Form(...),
          tipo: str = Form("gasto"), account_id: int = Form(...),
          category_id: str = Form(""), fecha: str = Form(""), nota: str = Form(""),
          es_reintegrable: str = Form(""),
          db: Session = Depends(get_db), user: User = Depends(require_user)):
    try:
        f = date.fromisoformat(fecha) if fecha else date.today()
    except ValueError:
        f = date.today()
    t = Transaction(
        user_id=user.id, account_id=account_id,
        category_id=int(category_id) if category_id else None,
        concepto=concepto.strip() or "Movimiento", importe=abs(importe), tipo=tipo,
        fecha=f, nota=nota, es_reintegrable=bool(es_reintegrable))
    db.add(t)
    save(db)
    return RedirectResponse("/movimientos", status_code=303)


@router.post("/movimientos/{tid}/editar")
def editar(tid: int, concepto: str = Form(...), importe: float = Form(...),
           tipo: str = Form("gasto"), account_id: int = Form(...),
           category_id: str = Form(""), fecha: str = Form(""), nota: str = Form(""),
           es_reintegrable: str = Form(""), reintegrado: str = Form(""),
           db: Session = Depends(get_db), user: User = Depends(require_user)):
    t = db.query(Transaction).filter(Transaction.id == tid, Transaction.user_id == user.id).first()
    if t:
        try:
            t.fecha = date.fromisoformat(fecha) if fecha else t.fecha
        except ValueError:
            pass
        t.concepto = concepto.strip() or t.concepto
        t.importe = abs(importe)
        t.tipo = tipo
        t.account_id = account_id
        t.category_id = int(category_id) if category_id else None
        t.nota = nota
        t.es_reintegrable = bool(es_reintegrable)
        t.reintegrado = bool(reintegrado)
        save(db)
    return RedirectResponse("/movimientos", status_code=303)


@router.post("/movimientos/{tid}/borrar")
def borrar(tid: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    t = db.query(Transaction).filter(Transaction.id == tid, Transaction.user_id == user.id).first()
    if t:
        db.delete(t)
        save(db)
    return RedirectResponse("/movimientos", status_code=303)


@router.get("/movimientos/export")
def export_mov(fmt: str = "csv", q: str = "", tipo: str = "", cuenta: str = "",
               categoria: str = "", desde: str = "", hasta: str = "",
               db: Session = Depends(get_db), user: User = Depends(require_user)):
    rows = _filtered(db, user.id, q, tipo, cuenta, categoria, desde, hasta).all()
    stamp = datetime.now().strftime("%Y%m%d")
    if fmt == "excel":
        data = export.to_excel(rows)
        return Response(data,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=movimientos_{stamp}.xlsx"})
    data = export.to_csv(rows)
    return Response(data, media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=movimientos_{stamp}.csv"})
