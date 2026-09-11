"""API para automatizaciones externas (Atajos de iOS).

Autenticación por token de larga duración (ver security.make_api_token),
enviado en la cabecera `Authorization: Bearer <token>` o como campo de
formulario `token`. Solo permite crear movimientos y leer los nombres de
cuentas y categorías; nunca borrar ni consultar el histórico.
"""
from datetime import date

from fastapi import APIRouter, Depends, Request, Form, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import User, Account, Category, Transaction
from ..security import read_api_token
from ..store import save
from ..services import finance

router = APIRouter(prefix="/api")


def _user_from_token(request: Request, db: Session, token_form: str | None) -> User:
    token = None
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        token = auth[7:].strip()
    if not token:
        token = (token_form or "").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Falta el token")
    uid = read_api_token(token)
    if not uid:
        raise HTTPException(status_code=401, detail="Token inválido o caducado")
    user = db.get(User, uid)
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return user


@router.get("/meta")
def meta(request: Request, token: str = "", db: Session = Depends(get_db)):
    """Devuelve los nombres de cuentas y categorías del usuario para que el
    Atajo pueda construir las listas de elección."""
    user = _user_from_token(request, db, token)
    accounts = (db.query(Account)
                .filter(Account.user_id == user.id, Account.activa == True)  # noqa: E712
                .order_by(Account.orden, Account.id).all())
    categories = (db.query(Category)
                  .filter(Category.user_id == user.id, Category.archivada == False)  # noqa: E712
                  .order_by(Category.orden, Category.id).all())
    return {
        "cuentas": [a.nombre for a in accounts],
        "categorias": [c.nombre for c in categories],
    }


@router.post("/quick")
def quick(request: Request,
          importe: float = Form(...),
          concepto: str = Form(""),
          tipo: str = Form("gasto"),
          categoria: str = Form(""),
          cuenta: str = Form(""),
          fecha: str = Form(""),
          token: str = Form(""),
          db: Session = Depends(get_db)):
    """Crea un movimiento rápido desde una automatización."""
    user = _user_from_token(request, db, token)

    if tipo not in ("gasto", "ingreso"):
        tipo = "gasto"

    # Cuenta: por nombre (insensible a may/min); si no, la principal.
    acc = None
    if cuenta.strip():
        acc = (db.query(Account)
               .filter(Account.user_id == user.id,
                       func.lower(Account.nombre) == cuenta.strip().lower())
               .first())
    if acc is None:
        acc = finance.primary_account(db, user.id)
    if acc is None:
        acc = (db.query(Account).filter(Account.user_id == user.id)
               .order_by(Account.orden, Account.id).first())
    if acc is None:
        raise HTTPException(status_code=400, detail="No tienes ninguna cuenta")

    # Categoría opcional, por nombre.
    cat = None
    if categoria.strip():
        cat = (db.query(Category)
               .filter(Category.user_id == user.id, Category.archivada == False,  # noqa: E712
                       func.lower(Category.nombre) == categoria.strip().lower())
               .first())

    try:
        f = date.fromisoformat(fecha) if fecha else date.today()
    except ValueError:
        f = date.today()

    t = Transaction(
        user_id=user.id, account_id=acc.id,
        category_id=cat.id if cat else None,
        concepto=concepto.strip() or ("Ingreso" if tipo == "ingreso" else "Gasto"),
        importe=abs(importe), tipo=tipo, fecha=f, nota="")
    db.add(t)
    save(db)

    return {
        "ok": True,
        "id": t.id,
        "importe": round(abs(importe), 2),
        "tipo": tipo,
        "concepto": t.concepto,
        "cuenta": acc.nombre,
        "categoria": cat.nombre if cat else None,
        "fecha": f.isoformat(),
        "saldo": finance.account_balance(db, acc),
    }
