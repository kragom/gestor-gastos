from . import (
    auth, dashboard, movimientos, graficos, presupuestos,
    reintegrables, extraordinarios, categorias, cuentas, ajustes,
    keepalive, api,
)

all_routers = [
    auth.router,
    dashboard.router,
    movimientos.router,
    graficos.router,
    presupuestos.router,
    reintegrables.router,
    extraordinarios.router,
    categorias.router,
    cuentas.router,
    ajustes.router,
    keepalive.router,
    api.router,
]
