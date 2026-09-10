---
title: Balance
emoji: 💶
colorFrom: green
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
---

# Balance · Tu economía, con claridad.

Aplicación de finanzas personales multiusuario (FastAPI + SQLite + PWA).

## Secciones
Inicio, Movimientos, Gráficos, Presupuestos, Reintegrables, Gastos extraordinarios,
Categorías, Cuentas y Ajustes.

## Persistencia
El fichero SQLite se sincroniza con un **HF Dataset privado** (`HF_DATASET_REPO`).
Al arrancar se descarga la base de datos y tras cada escritura se sube (con debounce).

> Nota: la sincronización mediante un único fichero SQLite es sencilla pero frágil
> ante escrituras concurrentes de muchos usuarios a la vez. Suficiente para uso
> personal / familiar.

## Variables de entorno (Secrets del Space)
| Variable | Descripción |
|----------|-------------|
| `SECRET_KEY` | Clave para firmar las cookies de sesión |
| `HF_TOKEN` | Token con permiso de escritura al dataset |
| `HF_DATASET_REPO` | p.ej. `hectorpc19/balance-db` |

Opcionales: `HF_DB_FILENAME` (por defecto `balance.db`), `SYNC_DEBOUNCE_SECONDS`,
`BALANCE_DATA_DIR`.

## Usuario demo
`demo@balance.local` / `demo1234` (se crea automáticamente al arrancar).

## Ejecutar en local
```bash
pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --reload
```
