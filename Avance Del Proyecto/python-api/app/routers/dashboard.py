"""
Router: Dashboard web
Sirve el HTML del dashboard ensamblado desde partes independientes y
expone /opciones para los filtros de la tabla y /static/dashboard.css.
"""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, Response

from app.routers.csv_processor import get_dataframe

router = APIRouter(tags=["Dashboard"])

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
_PARTS_DIR     = _TEMPLATES_DIR / "parts"
_STATIC_DIR    = Path(__file__).parent.parent / "static"


def _part(name: str) -> str:
    """Lee un archivo de la carpeta parts/."""
    return (_PARTS_DIR / name).read_text(encoding="utf-8")


def _build_dashboard() -> str:
    """Ensambla el HTML completo uniendo la base con cada sección."""
    html = (_TEMPLATES_DIR / "dashboard_base.html").read_text(encoding="utf-8")
    partes = {
        "<!--SIDEBAR-->":        _part("sidebar.html"),
        "<!--TOPBAR-->":         _part("topbar.html"),
        "<!--SECCION_RESUMEN-->":  _part("seccion_resumen.html"),
        "<!--SECCION_DATOS-->":    _part("seccion_datos.html"),
        "<!--SECCION_AGENTE-->":   _part("seccion_agente.html"),
        "<!--SECCION_PROCESOS-->":      _part("seccion_procesos.html"),
        "<!--SECCION_SIN_UBICACION-->": _part("seccion_sin_ubicacion.html"),
        "<!--SCRIPTS-->":               _part("scripts.html"),
    }
    for placeholder, contenido in partes.items():
        html = html.replace(placeholder, contenido)
    return html


# ── Rutas ─────────────────────────────────────────────────────

@router.get("/static/dashboard.css", include_in_schema=False)
async def dashboard_css():
    """Sirve el CSS del dashboard como archivo estático."""
    css = (_STATIC_DIR / "dashboard.css").read_text(encoding="utf-8")
    return Response(content=css, media_type="text/css")


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def dashboard():
    """Sirve el dashboard HTML ensamblado desde sus partes."""
    return HTMLResponse(content=_build_dashboard())


@router.get("/opciones", tags=["Dashboard"])
async def opciones():
    """
    Devuelve los valores únicos para rellenar los desplegables de filtros.
    Retorna los top 200 departamentos y ciudades más frecuentes (ordenados).
    """
    df = get_dataframe()

    departamentos: list[str] = []
    if "departamento" in df.columns:
        departamentos = (
            df["departamento"]
            .dropna()
            .value_counts()
            .head(200)
            .index
            .sort_values()
            .tolist()
        )

    ciudades: list[str] = []
    if "ciudad" in df.columns:
        ciudades = (
            df["ciudad"]
            .dropna()
            .value_counts()
            .head(200)
            .index
            .sort_values()
            .tolist()
        )

    camaras: list[str] = []
    if "camara_comercio" in df.columns:
        camaras = (
            df["camara_comercio"]
            .dropna()
            .value_counts()
            .head(50)
            .index
            .sort_values()
            .tolist()
        )

    return {
        "departamentos": departamentos,
        "ciudades": ciudades,
        "camaras_comercio": camaras,
    }
