"""Exportación de movimientos a CSV y Excel."""
import csv
import io

from openpyxl import Workbook


def _rows(transactions):
    for t in transactions:
        yield {
            "Fecha": t.fecha.isoformat(),
            "Concepto": t.concepto,
            "Tipo": t.tipo,
            "Importe": t.importe if t.tipo == "ingreso" else -t.importe,
            "Cuenta": t.account.nombre if t.account else "",
            "Categoria": t.category.nombre if t.category else "",
            "Nota": t.nota or "",
        }


HEADERS = ["Fecha", "Concepto", "Tipo", "Importe", "Cuenta", "Categoria", "Nota"]


def to_csv(transactions) -> bytes:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=HEADERS, delimiter=";")
    writer.writeheader()
    for row in _rows(transactions):
        writer.writerow(row)
    return buf.getvalue().encode("utf-8-sig")


def to_excel(transactions) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Movimientos"
    ws.append(HEADERS)
    for row in _rows(transactions):
        ws.append([row[h] for h in HEADERS])
    for i, h in enumerate(HEADERS, start=1):
        ws.column_dimensions[chr(64 + i)].width = max(12, len(h) + 4)
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()
