"""Movimientos: listado con filtros, alta/edición/borrado y exportación."""
from datetime import date, datetime

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import require_user
from ..models import User, Account, Category, Transaction, RecurringTransaction
from ..templating import templates
from ..store import save
from ..services import finance, export, recurring

router = APIRouter()


def _filtered(db: Session, user_id: int, q, tipo, cuenta, categoria, desde, hasta):
    query = db.query(Transaction).filter(Transaction.user_id == user_id)
    if q:
        query = query.filter(Transaction.concepto.ilike(f"%{q}%"))
    if tipo in ("gasto", "ingreso", "transferencia"):
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


@router.get("/recurrentes", response_class=HTMLResponse)
def recurrentes_page(request: Request, db: Session = Depends(get_db),
                     user: User = Depends(require_user)):
    accounts = db.query(Account).filter(Account.user_id == user.id).order_by(Account.orden).all()
    categories = db.query(Category).filter(Category.user_id == user.id).order_by(Category.orden).all()
    recurrentes = (db.query(RecurringTransaction)
                   .filter(RecurringTransaction.user_id == user.id)
                   .order_by(RecurringTransaction.activa.desc(),
                             RecurringTransaction.concepto).all())
    return templates.TemplateResponse("recurrentes.html", {
        "request": request, "user": user, "active": "recurrentes",
        "accounts": accounts, "categories": categories,
        "recurrentes": recurrentes,
    })


@router.get("/movimientos/nuevo", response_class=HTMLResponse)
def nuevo_form(request: Request, tipo: str = "gasto", embed: int = 0,
               db: Session = Depends(get_db), user: User = Depends(require_user)):
    accounts = db.query(Account).filter(Account.user_id == user.id).order_by(Account.orden).all()
    categories = db.query(Category).filter(
        Category.user_id == user.id, Category.archivada == False).order_by(Category.orden).all()  # noqa: E712
    tpl = "_movimiento_form.html" if embed else "movimiento_form.html"
    return templates.TemplateResponse(tpl, {
        "request": request, "user": user, "active": "movimientos",
        "accounts": accounts, "categories": categories, "t": None,
        "tipo_ini": tipo if tipo in ("gasto", "ingreso", "transferencia") else "gasto",
        "embed": bool(embed),
    })


@router.get("/movimientos/{tid}/editar", response_class=HTMLResponse)
def editar_form(tid: int, request: Request,
                db: Session = Depends(get_db), user: User = Depends(require_user)):
    t = db.query(Transaction).filter(
        Transaction.id == tid, Transaction.user_id == user.id).first()
    if not t:
        return RedirectResponse("/movimientos", status_code=303)
    accounts = db.query(Account).filter(Account.user_id == user.id).order_by(Account.orden).all()
    categories = db.query(Category).filter(
        Category.user_id == user.id, Category.archivada == False).order_by(Category.orden).all()  # noqa: E712
    return templates.TemplateResponse("movimiento_form.html", {
        "request": request, "user": user, "active": "movimientos",
        "accounts": accounts, "categories": categories, "t": t,
        "tipo_ini": t.tipo,
    })


@router.post("/movimientos/nuevo")
def crear(request: Request, concepto: str = Form(...), importe: float = Form(...),
          tipo: str = Form("gasto"), account_id: int = Form(...),
          category_id: str = Form(""), cuenta_destino_id: str = Form(""),
          fecha: str = Form(""), nota: str = Form(""),
          es_reintegrable: str = Form(""),
          db: Session = Depends(get_db), user: User = Depends(require_user)):
    try:
        f = date.fromisoformat(fecha) if fecha else date.today()
    except ValueError:
        f = date.today()
    if tipo == "transferencia":
        destino = int(cuenta_destino_id) if cuenta_destino_id else None
        # Una transferencia necesita una cuenta destino distinta del origen.
        if not destino or destino == account_id:
            return RedirectResponse("/movimientos", status_code=303)
        t = Transaction(
            user_id=user.id, account_id=account_id, cuenta_destino_id=destino,
            category_id=None, concepto=concepto.strip() or "Transferencia",
            importe=abs(importe), tipo="transferencia", fecha=f, nota=nota,
            es_reintegrable=False)
    else:
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
           category_id: str = Form(""), cuenta_destino_id: str = Form(""),
           fecha: str = Form(""), nota: str = Form(""),
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
        t.nota = nota
        if tipo == "transferencia":
            destino = int(cuenta_destino_id) if cuenta_destino_id else None
            if destino and destino != account_id:
                t.cuenta_destino_id = destino
            t.category_id = None
            t.es_reintegrable = False
            t.reintegrado = False
        else:
            t.cuenta_destino_id = None
            t.category_id = int(category_id) if category_id else None
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


# ---------------------------------------------------------------------------
# Movimientos recurrentes / programados
# ---------------------------------------------------------------------------

def _parse_rec_form(concepto, importe, tipo, account_id, category_id,
                    cuenta_destino_id, nota, es_reintegrable, frecuencia,
                    dia_mes, mes, fecha_inicio, fecha_fin, modo):
    try:
        ini = date.fromisoformat(fecha_inicio) if fecha_inicio else date.today()
    except ValueError:
        ini = date.today()
    fin = None
    if fecha_fin:
        try:
            fin = date.fromisoformat(fecha_fin)
        except ValueError:
            fin = None
    dia = max(1, min(31, int(dia_mes or 1)))
    frecuencia = frecuencia if frecuencia in ("mensual", "anual") else "mensual"
    modo = modo if modo in ("automatico", "propuesta") else "automatico"
    mes_val = None
    if frecuencia == "anual":
        mes_val = max(1, min(12, int(mes))) if mes else ini.month
    data = {
        "concepto": (concepto or "").strip() or "Movimiento",
        "importe": abs(importe), "tipo": tipo,
        "account_id": account_id,
        "frecuencia": frecuencia, "dia_mes": dia, "mes": mes_val,
        "fecha_inicio": ini, "fecha_fin": fin, "modo": modo,
        "nota": nota or "",
    }
    if tipo == "transferencia":
        destino = int(cuenta_destino_id) if cuenta_destino_id else None
        data["cuenta_destino_id"] = destino if destino and destino != account_id else None
        data["category_id"] = None
        data["es_reintegrable"] = False
    else:
        data["cuenta_destino_id"] = None
        data["category_id"] = int(category_id) if category_id else None
        data["es_reintegrable"] = bool(es_reintegrable)
    return data


@router.post("/recurrentes/nuevo")
def rec_crear(concepto: str = Form(...), importe: float = Form(...),
              tipo: str = Form("gasto"), account_id: int = Form(...),
              category_id: str = Form(""), cuenta_destino_id: str = Form(""),
              nota: str = Form(""), es_reintegrable: str = Form(""),
              frecuencia: str = Form("mensual"), dia_mes: str = Form("1"),
              mes: str = Form(""), fecha_inicio: str = Form(""),
              fecha_fin: str = Form(""), modo: str = Form("automatico"),
              db: Session = Depends(get_db), user: User = Depends(require_user)):
    data = _parse_rec_form(concepto, importe, tipo, account_id, category_id,
                           cuenta_destino_id, nota, es_reintegrable, frecuencia,
                           dia_mes, mes, fecha_inicio, fecha_fin, modo)
    if tipo == "transferencia" and not data["cuenta_destino_id"]:
        return RedirectResponse("/movimientos", status_code=303)
    db.add(RecurringTransaction(user_id=user.id, **data))
    save(db)
    return RedirectResponse("/movimientos", status_code=303)


@router.post("/recurrentes/{rid}/editar")
def rec_editar(rid: int, concepto: str = Form(...), importe: float = Form(...),
               tipo: str = Form("gasto"), account_id: int = Form(...),
               category_id: str = Form(""), cuenta_destino_id: str = Form(""),
               nota: str = Form(""), es_reintegrable: str = Form(""),
               frecuencia: str = Form("mensual"), dia_mes: str = Form("1"),
               mes: str = Form(""), fecha_inicio: str = Form(""),
               fecha_fin: str = Form(""), modo: str = Form("automatico"),
               db: Session = Depends(get_db), user: User = Depends(require_user)):
    rec = db.query(RecurringTransaction).filter(
        RecurringTransaction.id == rid, RecurringTransaction.user_id == user.id).first()
    if rec:
        data = _parse_rec_form(concepto, importe, tipo, account_id, category_id,
                               cuenta_destino_id, nota, es_reintegrable, frecuencia,
                               dia_mes, mes, fecha_inicio, fecha_fin, modo)
        if not (tipo == "transferencia" and not data["cuenta_destino_id"]):
            for k, v in data.items():
                setattr(rec, k, v)
            save(db)
    return RedirectResponse("/movimientos", status_code=303)


@router.post("/recurrentes/{rid}/borrar")
def rec_borrar(rid: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    rec = db.query(RecurringTransaction).filter(
        RecurringTransaction.id == rid, RecurringTransaction.user_id == user.id).first()
    if rec:
        db.delete(rec)
        save(db)
    return RedirectResponse("/movimientos", status_code=303)


@router.post("/recurrentes/{rid}/toggle")
def rec_toggle(rid: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    rec = db.query(RecurringTransaction).filter(
        RecurringTransaction.id == rid, RecurringTransaction.user_id == user.id).first()
    if rec:
        rec.activa = not rec.activa
        save(db)
    return RedirectResponse("/movimientos", status_code=303)


@router.post("/recurrentes/{rid}/confirmar")
def rec_confirmar(rid: int, fecha: str = Form(...), next: str = Form("/"),
                  db: Session = Depends(get_db), user: User = Depends(require_user)):
    rec = db.query(RecurringTransaction).filter(
        RecurringTransaction.id == rid, RecurringTransaction.user_id == user.id).first()
    if rec:
        try:
            f = date.fromisoformat(fecha)
            recurring.confirmar(db, rec, f)
        except ValueError:
            pass
    return RedirectResponse(next, status_code=303)


@router.post("/recurrentes/{rid}/descartar")
def rec_descartar(rid: int, fecha: str = Form(...), next: str = Form("/"),
                  db: Session = Depends(get_db), user: User = Depends(require_user)):
    rec = db.query(RecurringTransaction).filter(
        RecurringTransaction.id == rid, RecurringTransaction.user_id == user.id).first()
    if rec:
        try:
            f = date.fromisoformat(fecha)
            recurring.descartar(db, rec, f)
        except ValueError:
            pass
    return RedirectResponse(next, status_code=303)
