"""
Router: Ferreterías sin ubicación en Google Maps
Consulta Supabase para registros que fueron procesados pero no tienen coordenadas.
"""

import httpx
from fastapi import APIRouter
from app.config import settings

router = APIRouter(tags=["Sin Ubicación"])


@router.get("/sin-ubicacion")
async def sin_ubicacion(
    limit: int = 50,
    offset: int = 0,
    busqueda: str = None,
    departamento: str = None,
):
    """
    Retorna ferreterías que están legalmente constituidas pero
    Google Maps no pudo geocodificarlas (geocodificado=true, lat IS NULL).
    """
    if not settings.supabase_url or not settings.supabase_key:
        return {"total": 0, "data": [], "error": "Supabase no configurado"}

    headers = {
        "apikey": settings.supabase_key,
        "Authorization": f"Bearer {settings.supabase_key}",
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # Total
            count_url = (
                f"{settings.supabase_url}/rest/v1/ferreterias"
                "?select=id"
                "&geocodificado=eq.true"
                "&lat=is.null"
            )
            if busqueda:
                count_url += f"&razon_social=ilike.*{busqueda}*"
            if departamento:
                count_url += f"&departamento=ilike.*{departamento}*"

            r_count = await client.get(
                count_url,
                headers={**headers, "Prefer": "count=exact", "Range": "0-0"},
            )
            total = int(r_count.headers.get("content-range", "0/0").split("/")[-1] or 0)

            # Datos
            data_url = (
                f"{settings.supabase_url}/rest/v1/ferreterias"
                "?select=razon_social,representante_legal,telefono,direccion,ciudad,departamento,estado_legal,camara_comercio"
                "&geocodificado=eq.true"
                "&lat=is.null"
                f"&limit={limit}&offset={offset}"
                "&order=razon_social.asc"
            )
            if busqueda:
                data_url += f"&razon_social=ilike.*{busqueda}*"
            if departamento:
                data_url += f"&departamento=ilike.*{departamento}*"

            r_data = await client.get(data_url, headers=headers)
            data = r_data.json() if r_data.status_code == 200 else []

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "data": data,
        }

    except Exception as e:
        return {"total": 0, "data": [], "error": str(e)}
