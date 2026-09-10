"""Dashboard / Inicio."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import require_user
from ..models import User, Account, Transaction, MonthClose
from ..templating import templates
from ..periods import parse_period, shift_period
from ..store import save
from ..services import finance

router = APIRouter()


def savings_income(db: Session, user_id: int, start, end) -> float:
    # Ingresos directos a cuentas de ahorro.
    directo = (db.query(func.coalesce(func.sum(Transaction.importe), 0.0))
               .join(Account, Account.id == Transaction.account_id)
               .filter(Transaction.user_id == user_id, Account.tipo == "ahorro",
                       Transaction.tipo == "ingreso",
                       Transaction.fecha >= start, Transaction.fecha <= end)
               .scalar() or 0.0)
    # Transferencias que entran en cuentas de ahorro (aportaciones al ahorro).
    transferido = (db.query(func.coalesce(func.sum(Transaction.importe), 0.0))
                   .join(Account, Account.id == Transaction.cuenta_destino_id)
                   .filter(Transaction.user_id == user_id, Account.tipo == "ahorro",
                           Transaction.tipo == "transferencia",
                           Transaction.fecha >= start, Transaction.fecha <= end)
                   .scalar() or 0.0)
    return round(directo + transferido, 2)


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, mode: str = "month", period: str | None = None,
              db: Session = Depends(get_db), user: User = Depends(require_user)):
    m, anio, mes, start, end = parse_period(mode, period)

    accts, patrimonio = finance.net_worth(db, user.id)
    home_rows, home_total = finance.home_accounts(db, user.id)

    ingresos, gastos, balance = finance.period_totals(db, user.id, start, end)
    ahorro = savings_income(db, user.id, start, end)

    dist, dist_total = finance.spend_by_category(db, user.id, start, end)
    _, reint_total = finance.pending_reintegrables(db, user.id)
    reint_rows, _ = finance.pending_reintegrables(db, user.id)

    budget = None
    if mes:
        budget = finance.budget_for_month(db, user.id, anio, mes)

    period_str = period or (f"{anio:04d}-{mes:02d}" if mes else f"{anio}")
    cerrado = False
    if mes:
        cerrado = db.query(MonthClose).filter(
            MonthClose.user_id == user.id, MonthClose.anio == anio,
            MonthClose.mes == mes).first() is not None

    return templates.TemplateResponse("dashboard.html", {
        "request": request, "user": user, "active": "inicio",
        "mode": m, "anio": anio, "mes": mes, "period": period_str,
        "prev": shift_period(m, anio, mes, -1), "next": shift_period(m, anio, mes, 1),
        "accts": accts, "patrimonio": patrimonio,
        "home_rows": home_rows, "home_total": home_total,
        "ingresos": ingresos, "gastos": gastos, "balance": balance, "ahorro": ahorro,
        "dist": dist, "dist_total": dist_total,
        "reint_total": reint_total, "reint_count": len(reint_rows),
        "budget": budget, "cerrado": cerrado,
    })


@router.post("/cerrar-mes")
def cerrar_mes(anio: int, mes: int, db: Session = Depends(get_db),
               user: User = Depends(require_user)):
    existing = db.query(MonthClose).filter(
        MonthClose.user_id == user.id, MonthClose.anio == anio, MonthClose.mes == mes).first()
    if existing:
        db.delete(existing)
    else:
        db.add(MonthClose(user_id=user.id, anio=anio, mes=mes))
    save(db)
    return RedirectResponse(f"/?mode=month&period={anio:04d}-{mes:02d}", status_code=303)
