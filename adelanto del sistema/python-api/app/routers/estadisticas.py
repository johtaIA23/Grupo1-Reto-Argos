"""
Router: Estadísticas del dataset
Devuelve resúmenes agregados útiles para el agente y para dashboards.
"""

import httpx
from fastapi import APIRouter
from app.config import settings
from app.models import EstadisticasResponse
from app.routers.csv_processor import get_dataframe

router = APIRouter(tags=["Estadísticas"])


async def _departamentos_desde_supabase() -> dict:
    """Obtiene distribución de departamentos desde Supabase (datos enriquecidos)."""
    if not settings.supabase_url or not settings.supabase_key:
        return {}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{settings.supabase_url}/rest/v1/ferreterias"
                "?select=departamento&departamento=not.is.null",
                headers={
                    "apikey": settings.supabase_key,
                    "Authorization": f"Bearer {settings.supabase_key}",
                },
            )
        if r.status_code != 200:
            return {}
        conteos: dict[str, int] = {}
        for row in r.json():
            dep = (row.get("departamento") or "").strip()
            if dep:
                conteos[dep] = conteos.get(dep, 0) + 1
        return dict(sorted(conteos.items(), key=lambda x: x[1], reverse=True)[:20])
    except Exception:
        return {}


@router.get("/estadisticas", response_model=EstadisticasResponse)
async def estadisticas():
    """
    Resumen completo del CSV:
    - Totales por estado_info, estado_legal
    - Top departamentos (desde Supabase si está disponible, si no desde CSV)
    - Top cámaras de comercio
    - Campos de contacto disponibles
    """
    df = get_dataframe()

    # Distribuciones de clasificación
    estado_info_counts  = df["estado_info"].value_counts().to_dict()
    estado_legal_counts = df["estado_legal"].value_counts().to_dict()

    # Top departamentos — primero intenta Supabase (datos enriquecidos)
    por_departamento = await _departamentos_desde_supabase()
    if not por_departamento and "departamento" in df.columns:
        por_departamento = (
            df["departamento"]
            .dropna()
            .value_counts()
            .head(20)
            .to_dict()
        )

    # Top 20 cámaras de comercio
    por_camara = {}
    if "camara_comercio" in df.columns:
        por_camara = (
            df["camara_comercio"]
            .dropna()
            .value_counts()
            .head(20)
            .to_dict()
        )

    # Campos de contacto disponibles
    con_telefono = int(df["telefono"].notna().sum()) if "telefono" in df.columns else 0
    con_email    = int(df["email"].notna().sum())    if "email"    in df.columns else 0
    con_nit      = int(df["nit"].notna().sum())      if "nit"      in df.columns else 0

    return EstadisticasResponse(
        total_registros     = len(df),
        estado_info         = estado_info_counts,
        estado_legal        = estado_legal_counts,
        por_departamento    = por_departamento,
        por_camara_comercio = por_camara,
        con_telefono        = con_telefono,
        con_email           = con_email,
        con_nit             = con_nit,
    )
