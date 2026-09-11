"""Generación de movimientos recurrentes / programados.

Se dispara bajo demanda al cargar el Inicio (no hay scheduler y en Render free
el servicio se duerme). El proceso es idempotente: se apoya en
`RecurringTransaction.ultima_generacion` para no duplicar y para ponerse al día
(catch-up) si han pasado varios periodos.
"""
from __future__ import annotations

import calendar
from datetime import date

from sqlalchemy.orm import Session

from ..models import RecurringTransaction, Transaction, User
from ..store import save


def _ultimo_dia(anio: int, mes: int) -> int:
    return calendar.monthrange(anio, mes)[1]


def _ajusta(anio: int, mes: int, dia: int) -> date:
    """Fecha real ajustando el día al último del mes si se pasa (ej. 31 feb)."""
    return date(anio, mes, min(dia, _ultimo_dia(anio, mes)))


def _sig_mes(anio: int, mes: int) -> tuple[int, int]:
    return (anio + 1, 1) if mes == 12 else (anio, mes + 1)


def _ocurrencias(rec: RecurringTransaction, hasta: date) -> list[date]:
    """Fechas vencidas (<= hasta) aún no procesadas para esta plantilla."""
    if not rec.activa:
        return []
    inicio = rec.fecha_inicio
    fin = min(hasta, rec.fecha_fin) if rec.fecha_fin else hasta
    if fin < inicio:
        return []

    fechas: list[date] = []
    if rec.frecuencia == "mensual":
        anio, mes = inicio.year, inicio.month
        # La primera ocurrencia es en el mes de inicio si su día ya llegó,
        # si no, el mes siguiente.
        primera = _ajusta(anio, mes, rec.dia_mes)
        if primera < inicio:
            anio, mes = _sig_mes(anio, mes)
        while True:
            f = _ajusta(anio, mes, rec.dia_mes)
            if f > fin:
                break
            if f >= inicio:
                fechas.append(f)
            anio, mes = _sig_mes(anio, mes)
    elif rec.frecuencia == "anual":
        mes = rec.mes or inicio.month
        anio = inicio.year
        primera = _ajusta(anio, mes, rec.dia_mes)
        if primera < inicio:
            anio += 1
        while True:
            f = _ajusta(anio, mes, rec.dia_mes)
            if f > fin:
                break
            if f >= inicio:
                fechas.append(f)
            anio += 1

    # Filtrar las ya procesadas.
    if rec.ultima_generacion:
        fechas = [f for f in fechas if f > rec.ultima_generacion]
    return fechas


def _crear_tx(db: Session, rec: RecurringTransaction, f: date) -> Transaction:
    if rec.tipo == "transferencia":
        t = Transaction(
            user_id=rec.user_id, account_id=rec.account_id,
            cuenta_destino_id=rec.cuenta_destino_id, category_id=None,
            concepto=rec.concepto, importe=abs(rec.importe),
            tipo="transferencia", fecha=f, nota=rec.nota, es_reintegrable=False)
    else:
        t = Transaction(
            user_id=rec.user_id, account_id=rec.account_id,
            category_id=rec.category_id, concepto=rec.concepto,
            importe=abs(rec.importe), tipo=rec.tipo, fecha=f, nota=rec.nota,
            es_reintegrable=bool(rec.es_reintegrable))
    db.add(t)
    return t


def generar(db: Session, user: User, hoy: date | None = None) -> list[dict]:
    """Procesa las plantillas del usuario.

    - modo `automatico`: crea las transacciones vencidas y avanza
      `ultima_generacion`.
    - modo `propuesta`: NO crea nada; devuelve las ocurrencias pendientes para
      que el usuario las confirme/descarte desde el inicio.

    Devuelve la lista de pendientes: [{"rec": RecurringTransaction, "fecha": date}].
    """
    hoy = hoy or date.today()
    recs = (db.query(RecurringTransaction)
            .filter(RecurringTransaction.user_id == user.id,
                    RecurringTransaction.activa == True)  # noqa: E712
            .all())
    pendientes: list[dict] = []
    cambios = False
    for rec in recs:
        fechas = _ocurrencias(rec, hoy)
        if not fechas:
            continue
        if rec.modo == "automatico":
            for f in fechas:
                _crear_tx(db, rec, f)
            rec.ultima_generacion = fechas[-1]
            cambios = True
        else:  # propuesta
            for f in fechas:
                pendientes.append({"rec": rec, "fecha": f})
    if cambios:
        save(db)
    pendientes.sort(key=lambda p: p["fecha"])
    return pendientes


def confirmar(db: Session, rec: RecurringTransaction, f: date) -> None:
    """Crea la transacción de una ocurrencia propuesta y avanza el puntero."""
    _crear_tx(db, rec, f)
    if not rec.ultima_generacion or f > rec.ultima_generacion:
        rec.ultima_generacion = f
    save(db)


def descartar(db: Session, rec: RecurringTransaction, f: date) -> None:
    """Salta una ocurrencia propuesta sin crearla, avanzando el puntero."""
    if not rec.ultima_generacion or f > rec.ultima_generacion:
        rec.ultima_generacion = f
    save(db)
