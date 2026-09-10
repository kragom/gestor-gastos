"""Modelos de datos."""
from datetime import date, datetime

from sqlalchemy import (
    String, Integer, Float, Boolean, Date, DateTime, ForeignKey, Text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(120), default="Usuario")
    password_hash: Mapped[str] = mapped_column(String(255))
    moneda: Mapped[str] = mapped_column(String(8), default="EUR")
    tema: Mapped[str] = mapped_column(String(16), default="system")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    accounts: Mapped[list["Account"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    categories: Mapped[list["Category"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Account(Base):
    __tablename__ = "accounts"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    nombre: Mapped[str] = mapped_column(String(120))
    tipo: Mapped[str] = mapped_column(String(20), default="comun")  # comun | ahorro | otra
    saldo_inicial: Mapped[float] = mapped_column(Float, default=0.0)
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
    # Si la cuenta se muestra en el bloque "Saldos actuales" del inicio y suma
    # en el patrimonio líquido total de esa sección.
    mostrar_inicio: Mapped[bool] = mapped_column(Boolean, default=True)
    orden: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="accounts")
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="account", foreign_keys="Transaction.account_id")


class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    nombre: Mapped[str] = mapped_column(String(120))
    tipo: Mapped[str] = mapped_column(String(16), default="gasto")  # gasto | ingreso
    icono: Mapped[str] = mapped_column(String(40), default="tag")
    color: Mapped[str] = mapped_column(String(16), default="#1f5c46")
    orden: Mapped[int] = mapped_column(Integer, default=0)
    archivada: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="categories")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="category")


class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), index=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    # Cuenta destino: solo se usa en transferencias (dinero que sale de account_id
    # y entra en cuenta_destino_id). No cuenta como gasto ni como ingreso.
    cuenta_destino_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    concepto: Mapped[str] = mapped_column(String(200))
    importe: Mapped[float] = mapped_column(Float)  # siempre positivo
    tipo: Mapped[str] = mapped_column(String(16), default="gasto")  # gasto | ingreso | transferencia
    fecha: Mapped[date] = mapped_column(Date, index=True, default=date.today)
    nota: Mapped[str] = mapped_column(Text, default="")
    es_reintegrable: Mapped[bool] = mapped_column(Boolean, default=False)
    reintegrado: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="transactions")
    account: Mapped["Account"] = relationship(
        back_populates="transactions", foreign_keys=[account_id])
    cuenta_destino: Mapped["Account"] = relationship(foreign_keys=[cuenta_destino_id])
    category: Mapped["Category"] = relationship(back_populates="transactions")

    @property
    def signed(self) -> float:
        return self.importe if self.tipo == "ingreso" else -self.importe


class Budget(Base):
    __tablename__ = "budgets"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), index=True)
    anio: Mapped[int] = mapped_column(Integer, index=True)
    mes: Mapped[int] = mapped_column(Integer, index=True)
    importe: Mapped[float] = mapped_column(Float, default=0.0)
    es_plantilla: Mapped[bool] = mapped_column(Boolean, default=False)


class Extraordinary(Base):
    __tablename__ = "extraordinary"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    nombre: Mapped[str] = mapped_column(String(160))
    mes: Mapped[int] = mapped_column(Integer)
    anio: Mapped[int] = mapped_column(Integer)
    importe: Mapped[float] = mapped_column(Float, default=0.0)
    notas: Mapped[str] = mapped_column(Text, default="")
    repite_anual: Mapped[bool] = mapped_column(Boolean, default=False)


class MonthClose(Base):
    __tablename__ = "month_close"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    anio: Mapped[int] = mapped_column(Integer)
    mes: Mapped[int] = mapped_column(Integer)
    cerrado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
