"""Datos por defecto para usuarios nuevos y usuario demo."""
from datetime import date

from sqlalchemy.orm import Session

from .db import SessionLocal, init_db
from .models import User, Account, Category, Transaction
from .security import hash_password

DEFAULT_CATEGORIES = [
    ("Comida", "gasto", "food", "#3f8f5b"),
    ("Coche", "gasto", "car", "#3b82f6"),
    ("Gasolina", "gasto", "fuel", "#e0a419"),
    ("Seguros", "gasto", "shield", "#6366f1"),
    ("Casa", "gasto", "home", "#8b5cf6"),
    ("Ocio", "gasto", "sparkles", "#ec4899"),
    ("Compras", "gasto", "gift", "#ef4444"),
    ("Otros", "gasto", "grid", "#6b7280"),
    ("Nómina", "ingreso", "coins", "#1f5c46"),
]


def bootstrap_user(db: Session, user: User) -> None:
    """Crea cuentas y categorías por defecto para un usuario recién creado."""
    db.add(Account(user_id=user.id, nombre="Cuenta común", tipo="comun",
                   saldo_inicial=0.0, orden=0))
    db.add(Account(user_id=user.id, nombre="Ahorros / Inversión", tipo="ahorro",
                   saldo_inicial=0.0, orden=1))
    for i, (nombre, tipo, icono, color) in enumerate(DEFAULT_CATEGORIES):
        db.add(Category(user_id=user.id, nombre=nombre, tipo=tipo,
                        icono=icono, color=color, orden=i))
    db.flush()


def seed_demo(db: Session) -> None:
    """Crea el usuario demo con datos de ejemplo si no existe."""
    if db.query(User).filter(User.email == "demo@balance.local").first():
        return
    user = User(nombre="Usuario Demo", email="demo@balance.local",
                password_hash=hash_password("demo1234"))
    db.add(user)
    db.flush()

    comun = Account(user_id=user.id, nombre="Cuenta común", tipo="comun",
                    saldo_inicial=2686.75, orden=0)
    ahorro = Account(user_id=user.id, nombre="Ahorros / Inversión", tipo="ahorro",
                     saldo_inicial=11920.94, orden=1)
    db.add_all([comun, ahorro])
    db.flush()

    cats = {}
    demo_cats = [
        ("Michis", "gasto", "cat", "#c08457"),
        ("Placas", "gasto", "grid", "#6b7280"),
        ("Comida", "gasto", "food", "#3f8f5b"),
        ("Coche", "gasto", "car", "#3b82f6"),
        ("Otros", "gasto", "grid", "#9ca3af"),
        ("Seguros", "gasto", "shield", "#6366f1"),
        ("Gasolina", "gasto", "fuel", "#e0a419"),
        ("Donaciones", "gasto", "heart", "#ef4444"),
        ("Reintegrables", "gasto", "refresh", "#8b5cf6"),
        ("Nómina", "ingreso", "coins", "#1f5c46"),
    ]
    for i, (nombre, tipo, icono, color) in enumerate(demo_cats):
        c = Category(user_id=user.id, nombre=nombre, tipo=tipo, icono=icono, color=color, orden=i)
        db.add(c)
        db.flush()
        cats[nombre] = c

    def gasto(concepto, importe, cat, dia, cuenta=comun, reint=False):
        db.add(Transaction(user_id=user.id, account_id=cuenta.id,
                           category_id=cats[cat].id, concepto=concepto, importe=importe,
                           tipo="gasto", fecha=date(2026, 9, dia), es_reintegrable=reint))

    def ingreso(concepto, importe, dia, cuenta=comun):
        db.add(Transaction(user_id=user.id, account_id=cuenta.id,
                           category_id=cats["Nómina"].id, concepto=concepto, importe=importe,
                           tipo="ingreso", fecha=date(2026, 9, dia)))

    ingreso("Nómina septiembre", 2200.00, 1)
    ingreso("Ingreso extra", 1447.78, 3)
    gasto("Sobres natsbi", 96.00, "Michis", 8)
    gasto("Shein", 18.55, "Otros", 8)
    gasto("Consum charter", 4.98, "Comida", 7)
    gasto("Gasto", 139.35, "Coche", 7)
    gasto("Normal, parches ojeras Ana", 3.60, "Reintegrables", 5, reint=True)
    gasto("Michis pienso", 310.73, "Michis", 4)
    gasto("Placas solares", 161.69, "Placas", 4)
    gasto("Comida mensual", 141.57, "Comida", 3)
    gasto("Seguro coche", 66.17, "Seguros", 2)
    gasto("Gasolina", 63.32, "Gasolina", 2)
    gasto("Donación ONG", 46.00, "Donaciones", 2)
    gasto("Otros varios", 96.47, "Otros", 6)
    gasto("Farmacia Ana", 15.00, "Reintegrables", 3, reint=True)
    gasto("Regalo compartido", 11.59, "Reintegrables", 1, reint=True)

    db.flush()


def run():
    init_db()
    db = SessionLocal()
    try:
        seed_demo(db)
        db.commit()
        print("Seed completado. Usuario demo: demo@balance.local / demo1234")
    finally:
        db.close()


if __name__ == "__main__":
    run()
