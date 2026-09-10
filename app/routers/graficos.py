"""Gráficos y análisis financiero."""
from datetime import date

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import require_user
from ..models import User
from ..templating import templates
from ..services import finance

router = APIRouter()


@router.get("/graficos", response_class=HTMLResponse)
def graficos(request: Request, anio: int | None = None,
             db: Session = Depends(get_db), user: User = Depends(require_user)):
    anio = anio or date.today().year
    start, end = date(anio, 1, 1), date(anio, 12, 31)
    dist, dist_total = finance.spend_by_category(db, user.id, start, end)
    comp = finance.year_comparison(db, user.id, anio)
    monthly = finance.last_12_months(db, user.id, date(anio, 12, 1))
    return templates.TemplateResponse("graficos.html", {
        "request": request, "user": user, "active": "graficos",
        "anio": anio, "dist": dist, "dist_total": dist_total,
        "comp": comp, "monthly": monthly,
    })
