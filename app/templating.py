"""Configuración de Jinja2: plantillas, filtros e iconos."""
from datetime import date

from fastapi.templating import Jinja2Templates

from .config import BASE_DIR, APP_NAME, APP_TAGLINE
from .services.finance import MESES

templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))

# Iconos SVG (Lucide, trazo). Clave -> path(s) internos del <svg>.
ICONS = {
    "home": '<path d="M3 9.5 12 3l9 6.5"/><path d="M5 10v10h14V10"/>',
    "list": '<path d="M8 6h13M8 12h13M8 18h13"/><path d="M3 6h.01M3 12h.01M3 18h.01"/>',
    "chart": '<path d="M3 3v18h18"/><rect x="7" y="10" width="3" height="8"/><rect x="12" y="6" width="3" height="12"/><rect x="17" y="13" width="3" height="5"/>',
    "wallet": '<rect x="3" y="6" width="18" height="13" rx="2"/><path d="M16 12h.01"/><path d="M3 10h18"/>',
    "tag": '<path d="M20 12 12 20 3 11V3h8z"/><circle cx="7.5" cy="7.5" r="1.5"/>',
    "refresh": '<path d="M21 12a9 9 0 1 1-3-6.7L21 8"/><path d="M21 3v5h-5"/>',
    "calendar": '<rect x="3" y="4" width="18" height="17" rx="2"/><path d="M3 9h18M8 2v4M16 2v4"/>',
    "settings": '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M19 5l-2 2M7 17l-2 2"/>',
    "bank": '<path d="M3 21h18M4 10h16M12 3 3 8h18zM6 10v8M10 10v8M14 10v8M18 10v8"/>',
    "piggy": '<path d="M19 10c1.7 0 2 1.5 2 3s-.5 3-2 3v2h-3l-1-1H9l-1 1H5v-3a5 5 0 0 1 5-6h5c0-1 .8-2 2-2z"/><circle cx="16" cy="12" r="1"/>',
    "heart": '<path d="M12 21s-7-4.5-9-8.5C1 8 4 5 7 6c1.5.5 2.5 2 5 2s3.5-1.5 5-2c3-1 6 2 4 6.5-2 4-9 8.5-9 8.5z"/>',
    "fuel": '<rect x="4" y="4" width="9" height="16" rx="1"/><path d="M13 8h3l3 3v6a2 2 0 0 1-4 0v-3h-2"/>',
    "shield": '<path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6z"/>',
    "car": '<path d="M5 13l1.5-4.5A2 2 0 0 1 8.4 7h7.2a2 2 0 0 1 1.9 1.5L19 13v5h-2v-2H7v2H5z"/><circle cx="7.5" cy="16.5" r="1"/><circle cx="16.5" cy="16.5" r="1"/>',
    "food": '<path d="M6 3v8a2 2 0 0 0 4 0V3M8 3v18M18 3c-2 0-3 2-3 5s1 4 3 4v9"/>',
    "cat": '<path d="M4 6l2 5v7h4v-3h4v3h4v-7l2-5-4 3H8z"/><circle cx="9" cy="12" r="1"/><circle cx="15" cy="12" r="1"/>',
    "grid": '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>',
    "gift": '<rect x="3" y="8" width="18" height="4"/><path d="M5 12v9h14v-9M12 8v13M12 8S9 3 6.5 5 8 8 12 8zM12 8s3-5 5.5-3S16 8 12 8z"/>',
    "coins": '<ellipse cx="9" cy="7" rx="6" ry="3"/><path d="M3 7v5c0 1.7 2.7 3 6 3M15 12a6 3 0 1 0 0 6 6 3 0 0 0 0-6z"/>',
    "sparkles": '<path d="M12 3l1.8 4.2L18 9l-4.2 1.8L12 15l-1.8-4.2L6 9l4.2-1.8z"/><path d="M18 15l.9 2 2 .9-2 .9-.9 2-.9-2-2-.9 2-.9z"/>',
    "shopping": '<path d="M6 6h15l-1.5 9h-12z"/><path d="M6 6 5 3H3"/><circle cx="9" cy="20" r="1"/><circle cx="18" cy="20" r="1"/>',
    "briefcase": '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>',
    "receipt": '<path d="M6 3h12v18l-3-2-3 2-3-2-3 2z"/><path d="M9 8h6M9 12h6"/>',
    "transfer": '<path d="M7 4 3 8l4 4"/><path d="M3 8h14"/><path d="M17 20l4-4-4-4"/><path d="M21 16H7"/>',
    "repeat": '<path d="M17 2l4 4-4 4"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><path d="M7 22l-4-4 4-4"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "more": '<circle cx="5" cy="12" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="19" cy="12" r="1.6"/>',
    "back": '<path d="M19 12H5"/><path d="M12 19l-7-7 7-7"/>',
    "logout": '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="M16 17l5-5-5-5"/><path d="M21 12H9"/>',
    "help": '<circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 0 1 4.6 1.2c0 1.6-2.1 2-2.1 3.3"/><circle cx="12" cy="17" r="0.6"/>',
}

# Iconos ofrecidos al crear categorías
CATEGORY_ICONS = ["coins", "gift", "food", "car", "fuel", "home", "shield",
                  "calendar", "piggy", "heart", "cat", "sparkles"]


def icon_svg(name: str, size: int = 20, cls: str = "") -> str:
    path = ICONS.get(name, ICONS["tag"])
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
            f'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
            f'stroke-linecap="round" stroke-linejoin="round" class="{cls}">{path}</svg>')


def eur(value) -> str:
    try:
        v = float(value)
    except (TypeError, ValueError):
        v = 0.0
    s = f"{v:,.2f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{s} €"


def month_name(mes: int, anio: int | None = None) -> str:
    name = MESES[(mes - 1) % 12].capitalize()
    return f"{name} de {anio}" if anio else name


templates.env.filters["eur"] = eur
templates.env.filters["icon"] = icon_svg
templates.env.globals["icon"] = icon_svg
templates.env.globals["APP_NAME"] = APP_NAME
templates.env.globals["APP_TAGLINE"] = APP_TAGLINE
templates.env.globals["MESES"] = MESES
templates.env.globals["month_name"] = month_name
templates.env.globals["today"] = date.today
templates.env.globals["CATEGORY_ICONS"] = CATEGORY_ICONS


# --- Compatibilidad de firma para TemplateResponse ---
# Starlette moderno exige TemplateResponse(request, name, context). Los routers
# usan el estilo antiguo TemplateResponse(name, context). Este shim lo adapta.
_orig_template_response = templates.TemplateResponse


def _template_response(*args, **kwargs):
    if args and isinstance(args[0], str):
        name = args[0]
        context = args[1] if len(args) > 1 else kwargs.pop("context", {})
        request = context.get("request")
        return _orig_template_response(request, name, context, **kwargs)
    return _orig_template_response(*args, **kwargs)


templates.TemplateResponse = _template_response
