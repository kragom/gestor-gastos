"""Cálculos financieros (saldos, distribución, comparativas, presupuestos)."""
from calendar import monthrange
from datetime import date

from sqlalchemy import func, and_, case
from sqlalchemy.orm import Session

from ..models import Account, Category, Transaction, Budget, Extraordinary

MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def month_bounds(anio: int, mes: int):
    last = monthrange(anio, mes)[1]
    return date(anio, mes, 1), date(anio, mes, last)


def account_balance(db: Session, account: Account) -> float:
    total = db.query(func.coalesce(func.sum(
        case((Transaction.tipo == "ingreso", Transaction.importe), else_=-Transaction.importe)
    ), 0.0)).filter(Transaction.account_id == account.id).scalar() or 0.0
    return round(account.saldo_inicial + total, 2)


def accounts_with_balance(db: Session, user_id: int):
    accounts = (db.query(Account)
                .filter(Account.user_id == user_id)
                .order_by(Account.orden, Account.id).all())
    return [(a, account_balance(db, a)) for a in accounts]


def primary_account(db: Session, user_id: int) -> Account | None:
    return (db.query(Account)
            .filter(Account.user_id == user_id, Account.tipo == "comun", Account.activa == True)  # noqa: E712
            .order_by(Account.orden, Account.id).first())


def savings_accounts(db: Session, user_id: int):
    return (db.query(Account)
            .filter(Account.user_id == user_id, Account.tipo == "ahorro")
            .order_by(Account.orden, Account.id).all())


def _period_query(db: Session, user_id: int, start: date, end: date, tipo: str | None = None):
    q = db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.fecha >= start,
        Transaction.fecha <= end,
    )
    if tipo:
        q = q.filter(Transaction.tipo == tipo)
    return q


def period_totals(db: Session, user_id: int, start: date, end: date):
    ingresos = db.query(func.coalesce(func.sum(Transaction.importe), 0.0)).filter(
        Transaction.user_id == user_id, Transaction.tipo == "ingreso",
        Transaction.fecha >= start, Transaction.fecha <= end).scalar() or 0.0
    gastos = db.query(func.coalesce(func.sum(Transaction.importe), 0.0)).filter(
        Transaction.user_id == user_id, Transaction.tipo == "gasto",
        Transaction.fecha >= start, Transaction.fecha <= end).scalar() or 0.0
    return round(ingresos, 2), round(gastos, 2), round(ingresos - gastos, 2)


def spend_by_category(db: Session, user_id: int, start: date, end: date):
    rows = (db.query(Category, func.coalesce(func.sum(Transaction.importe), 0.0).label("total"))
            .join(Transaction, Transaction.category_id == Category.id)
            .filter(Transaction.user_id == user_id, Transaction.tipo == "gasto",
                    Transaction.fecha >= start, Transaction.fecha <= end)
            .group_by(Category.id)
            .order_by(func.sum(Transaction.importe).desc()).all())
    total = sum(r.total for r in rows) or 0.0
    result = []
    for cat, amount in rows:
        pct = (amount / total * 100.0) if total else 0.0
        result.append({
            "id": cat.id, "nombre": cat.nombre, "color": cat.color,
            "icono": cat.icono, "importe": round(amount, 2), "pct": round(pct, 1),
        })
    return result, round(total, 2)


def pending_reintegrables(db: Session, user_id: int):
    rows = (db.query(Transaction)
            .filter(Transaction.user_id == user_id,
                    Transaction.es_reintegrable == True,  # noqa: E712
                    Transaction.reintegrado == False)  # noqa: E712
            .order_by(Transaction.fecha.desc()).all())
    total = sum(r.importe for r in rows)
    return rows, round(total, 2)


def budget_for_month(db: Session, user_id: int, anio: int, mes: int):
    """Presupuesto por categoría del mes: importe presupuestado vs gastado (Cuenta común)."""
    start, end = month_bounds(anio, mes)
    common = primary_account(db, user_id)
    cats = (db.query(Category)
            .filter(Category.user_id == user_id, Category.tipo == "gasto",
                    Category.archivada == False)  # noqa: E712
            .order_by(Category.orden, Category.id).all())
    items = []
    total_presupuesto = 0.0
    total_gastado = 0.0
    for cat in cats:
        b = (db.query(Budget)
             .filter(Budget.user_id == user_id, Budget.category_id == cat.id,
                     Budget.anio == anio, Budget.mes == mes).first())
        importe = b.importe if b else 0.0
        gq = db.query(func.coalesce(func.sum(Transaction.importe), 0.0)).filter(
            Transaction.user_id == user_id, Transaction.category_id == cat.id,
            Transaction.tipo == "gasto", Transaction.fecha >= start, Transaction.fecha <= end)
        if common:
            gq = gq.filter(Transaction.account_id == common.id)
        gastado = gq.scalar() or 0.0
        total_presupuesto += importe
        total_gastado += gastado
        items.append({
            "categoria": cat, "importe": round(importe, 2), "gastado": round(gastado, 2),
            "pct": round((gastado / importe * 100.0), 0) if importe else 0,
            "tiene_presupuesto": importe > 0,
        })
    return {
        "items": items,
        "presupuesto": round(total_presupuesto, 2),
        "gastado": round(total_gastado, 2),
        "disponible": round(total_presupuesto - total_gastado, 2),
    }


def year_comparison(db: Session, user_id: int, anio: int):
    def totals(y):
        start, end = date(y, 1, 1), date(y, 12, 31)
        return period_totals(db, user_id, start, end)
    cur = totals(anio)
    prev = totals(anio - 1)
    return {
        "anio": anio, "prev": anio - 1,
        "ingresos": (cur[0], prev[0]),
        "gastos": (cur[1], prev[1]),
        "balance": (cur[2], prev[2]),
    }


def last_12_months(db: Session, user_id: int, ref: date):
    data = []
    y, m = ref.year, ref.month
    seq = []
    for _ in range(12):
        seq.append((y, m))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    for (yy, mm) in reversed(seq):
        s, e = month_bounds(yy, mm)
        ing, gas, bal = period_totals(db, user_id, s, e)
        data.append({"label": f"{MESES[mm-1][:3]} {yy}", "ingresos": ing, "gastos": gas, "balance": bal})
    return data


def net_worth(db: Session, user_id: int):
    accts = accounts_with_balance(db, user_id)
    total = round(sum(b for _, b in accts), 2)
    return accts, total


def transactions_grouped_by_day(rows):
    from itertools import groupby
    grouped = []
    for day, items in groupby(rows, key=lambda t: t.fecha):
        grouped.append((day, list(items)))
    return grouped
