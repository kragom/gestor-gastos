"""Aplicación FastAPI Balance."""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from .config import BASE_DIR
from .db import init_db, migrate, SessionLocal
from . import persistence
from .seed import seed_demo
from .routers import all_routers


@asynccontextmanager
async def lifespan(app: FastAPI):
    persistence.pull_db()
    init_db()
    migrate()
    db = SessionLocal()
    try:
        if os.getenv("SEED_DEMO", "0") == "1":
            seed_demo(db)
            db.commit()
    finally:
        db.close()
    yield
    persistence.flush()


app = FastAPI(title="Balance", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "static")), name="static")

for r in all_routers:
    app.include_router(r)


@app.exception_handler(307)
async def redirect_login(request: Request, exc):  # noqa: ANN001
    return RedirectResponse("/login", status_code=303)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}
