"""Presupuestos por mes y categoría."""
from datetime import date

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import require_user
from ..models import User, Budget
from ..templating import templates
from ..periods import shift_period
from ..store import save
from ..services import finance

router = APIRouter()


@router.get("/presupuestos", response_class=HTMLResponse)
def presupuestos(request: Request, period: str | None = None,
                 db: Session = Depends(get_db), user: User = Depends(require_user)):
    today = date.today()
    anio, mes = today.year, today.month
    if period and "-" in period:
        try:
            y, m = period.split("-")[:2]
            anio, mes = int(y), int(m)
        except ValueError:
            pass
    data = finance.budget_for_month(db, user.id, anio, mes)
    return templates.TemplateResponse("presupuestos.html", {
        "request": request, "user": user, "active": "presupuestos",
        "anio": anio, "mes": mes, "data": data,
        "period": f"{anio:04d}-{mes:02d}",
        "prev": shift_period("month", anio, mes, -1),
        "next": shift_period("month", anio, mes, 1),
    })


@router.post("/presupuestos/guardar")
def guardar(request: Request, anio: int = Form(...), mes: int = Form(...),
            category_id: int = Form(...), importe: float = Form(0.0),
            db: Session = Depends(get_db), user: User = Depends(require_user)):
    b = (db.query(Budget).filter(Budget.user_id == user.id, Budget.category_id == category_id,
                                 Budget.anio == anio, Budget.mes == mes).first())
    if b:
        b.importe = abs(importe)
    else:
        db.add(Budget(user_id=user.id, category_id=category_id, anio=anio, mes=mes,
                      importe=abs(importe)))
    save(db)
    return RedirectResponse(f"/presupuestos?period={anio:04d}-{mes:02d}", status_code=303)
