"""Categorías: crear, editar, reordenar, archivar."""
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import require_user
from ..models import User, Category, Transaction
from ..templating import templates
from ..store import save

router = APIRouter()


def _counts(db: Session, user_id: int):
    rows = (db.query(Transaction.category_id, func.count(Transaction.id))
            .filter(Transaction.user_id == user_id)
            .group_by(Transaction.category_id).all())
    return {cid: n for cid, n in rows}


@router.get("/categorias", response_class=HTMLResponse)
def categorias(request: Request, db: Session = Depends(get_db),
               user: User = Depends(require_user)):
    cats = (db.query(Category).filter(Category.user_id == user.id, Category.archivada == False)  # noqa: E712
            .order_by(Category.orden, Category.id).all())
    counts = _counts(db, user.id)
    gastos = [c for c in cats if c.tipo == "gasto"]
    ingresos = [c for c in cats if c.tipo == "ingreso"]
    return templates.TemplateResponse("categorias.html", {
        "request": request, "user": user, "active": "categorias",
        "gastos": gastos, "ingresos": ingresos, "counts": counts,
    })


@router.post("/categorias/nueva")
def crear(nombre: str = Form(...), tipo: str = Form("gasto"), icono: str = Form("tag"),
          color: str = Form("#1f5c46"), db: Session = Depends(get_db),
          user: User = Depends(require_user)):
    maxo = (db.query(func.coalesce(func.max(Category.orden), 0))
            .filter(Category.user_id == user.id).scalar() or 0)
    db.add(Category(user_id=user.id, nombre=nombre.strip() or "Categoría", tipo=tipo,
                    icono=icono, color=color, orden=maxo + 1))
    save(db)
    return RedirectResponse("/categorias", status_code=303)


@router.post("/categorias/{cid}/editar")
def editar(cid: int, nombre: str = Form(...), icono: str = Form("tag"),
           color: str = Form("#1f5c46"), db: Session = Depends(get_db),
           user: User = Depends(require_user)):
    c = db.query(Category).filter(Category.id == cid, Category.user_id == user.id).first()
    if c:
        c.nombre = nombre.strip() or c.nombre
        c.icono = icono
        c.color = color
        save(db)
    return RedirectResponse("/categorias", status_code=303)


@router.post("/categorias/{cid}/mover")
def mover(cid: int, dir: str = Form(...), db: Session = Depends(get_db),
          user: User = Depends(require_user)):
    c = db.query(Category).filter(Category.id == cid, Category.user_id == user.id).first()
    if c:
        cats = (db.query(Category).filter(Category.user_id == user.id, Category.tipo == c.tipo,
                                          Category.archivada == False)  # noqa: E712
                .order_by(Category.orden, Category.id).all())
        idx = next((i for i, x in enumerate(cats) if x.id == c.id), None)
        if idx is not None:
            j = idx - 1 if dir == "up" else idx + 1
            if 0 <= j < len(cats):
                cats[idx].orden, cats[j].orden = cats[j].orden, cats[idx].orden
                save(db)
    return RedirectResponse("/categorias", status_code=303)


@router.post("/categorias/{cid}/archivar")
def archivar(cid: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    c = db.query(Category).filter(Category.id == cid, Category.user_id == user.id).first()
    if c:
        c.archivada = True
        save(db)
    return RedirectResponse("/categorias", status_code=303)
