"""Autenticación: registro, login y logout."""
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models import User
from ..security import hash_password, verify_password, make_session, COOKIE_NAME, MAX_AGE
from ..templating import templates
from ..store import save
from ..seed import bootstrap_user

router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request, db: Session = Depends(get_db)):
    if get_current_user(request, db):
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...),
          db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email.strip().lower()).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": "Correo o contraseña incorrectos."},
            status_code=401)
    resp = RedirectResponse("/", status_code=303)
    resp.set_cookie(COOKIE_NAME, make_session(user.id), max_age=MAX_AGE,
                    httponly=True, samesite="lax")
    return resp


@router.get("/register", response_class=HTMLResponse)
def register_form(request: Request, db: Session = Depends(get_db)):
    if get_current_user(request, db):
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse("register.html", {"request": request, "error": None})


@router.post("/register")
def register(request: Request, nombre: str = Form(...), email: str = Form(...),
             password: str = Form(...), db: Session = Depends(get_db)):
    email = email.strip().lower()
    if db.query(User).filter(User.email == email).first():
        return templates.TemplateResponse(
            "register.html", {"request": request, "error": "Ese correo ya está registrado."},
            status_code=400)
    if len(password) < 6:
        return templates.TemplateResponse(
            "register.html", {"request": request, "error": "La contraseña debe tener al menos 6 caracteres."},
            status_code=400)
    user = User(nombre=nombre.strip() or "Usuario", email=email,
                password_hash=hash_password(password))
    db.add(user)
    db.flush()
    bootstrap_user(db, user)
    save(db)
    resp = RedirectResponse("/", status_code=303)
    resp.set_cookie(COOKIE_NAME, make_session(user.id), max_age=MAX_AGE,
                    httponly=True, samesite="lax")
    return resp


@router.post("/logout")
@router.get("/logout")
def logout():
    resp = RedirectResponse("/login", status_code=303)
    resp.delete_cookie(COOKIE_NAME)
    return resp
