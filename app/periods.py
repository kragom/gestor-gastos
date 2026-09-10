"""Utilidades de periodo (mes/año) compartidas por las vistas."""
from datetime import date


def parse_period(mode: str | None, period: str | None):
    """Devuelve (mode, anio, mes|None, start, end, label)."""
    today = date.today()
    mode = mode if mode in ("month", "year") else "month"
    anio, mes = today.year, today.month
    if period:
        try:
            if mode == "month" and "-" in period:
                y, m = period.split("-")[:2]
                anio, mes = int(y), int(m)
            else:
                anio = int(period[:4])
        except (ValueError, IndexError):
            pass
    if mode == "year":
        start, end = date(anio, 1, 1), date(anio, 12, 31)
        return mode, anio, None, start, end
    from calendar import monthrange
    last = monthrange(anio, mes)[1]
    return mode, anio, mes, date(anio, mes, 1), date(anio, mes, last)


def shift_period(mode: str, anio: int, mes: int | None, delta: int):
    if mode == "year":
        return f"{anio + delta}"
    m = (mes or 1) - 1 + delta
    y = anio + m // 12
    m = m % 12 + 1
    return f"{y:04d}-{m:02d}"
