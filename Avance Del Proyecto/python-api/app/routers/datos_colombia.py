"""
Router: Búsqueda DatosColombia
Consulta datos.gov.co para CIIU 4663/4752 y cruza con Supabase.
"""

import json, os, uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import AsyncGenerator

import httpx
import pandas as pd
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse, StreamingResponse

from app.routers.comparar_archivo import cruzar_con_supabase

router = APIRouter(prefix="/datoscolombia", tags=["DatosColombia"])

_ESTADO_PATH = Path("/data/datoscolombia_estado.json")
_RESULTADOS: dict[str, dict] = {}  # almacén en memoria de resultados recientes

# API pública de datos.gov.co (Registro Único Empresarial - CIIU 4663/4752)
_DATOS_GOV_URL = "https://www.datos.gov.co/resource/mc5k-hxq4.json"


def _sse(d: dict) -> str:
    return f"data: {json.dumps(d, ensure_ascii=False)}\n\n"


def _leer_estado() -> dict:
    try:
        if _ESTADO_PATH.exists():
            return json.loads(_ESTADO_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {
        "ultima_ejecucion": None,
        "proxima_ejecucion": None,
        "automatizacion_activa": False,
        "total_encontrados_ultima": 0,
        "ultimo_resultado_id": None,
    }


def _guardar_estado(estado: dict):
    try:
        _ESTADO_PATH.parent.mkdir(parents=True, exist_ok=True)
        _ESTADO_PATH.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


@router.get("/estado")
async def estado():
    """Estado de la última ejecución y configuración de automatización."""
    return JSONResponse(_leer_estado())


@router.post("/activar")
async def activar_automatizacion(activo: bool = Query(...)):
    """Activa o desactiva la automatización cada 4 meses."""
    est = _leer_estado()
    est["automatizacion_activa"] = activo
    if activo and not est.get("proxima_ejecucion"):
        prox = datetime.utcnow() + timedelta(days=120)
        est["proxima_ejecucion"] = prox.strftime("%Y-%m-%d")
    _guardar_estado(est)
    return JSONResponse({"ok": True, "automatizacion_activa": activo})


@router.post("/buscar")
async def buscar(
    stream: bool = Query(True),
    limite: int = Query(1000, ge=10, le=10000),
):
    """
    Consulta datos.gov.co y cruza con Supabase.
    Emite progreso SSE y almacena el resultado para consulta posterior.
    """
    async def _run() -> AsyncGenerator[str, None]:
        yield _sse({"estado": "iniciando", "msg": "Consultando datos.gov.co…"})

        registros_gov = []
        async with httpx.AsyncClient() as client:
            for ciiu in ("4663", "4752"):
                try:
                    r = await client.get(
                        _DATOS_GOV_URL,
                        params={
                            "$where": f"codigo_ciiu_principal='{ciiu}'",
                            "$limit": str(limite // 2),
                            "$select": "razon_social,nit,codigo_ciiu_principal,municipio,fecha_matricula,estado_matricula",
                        },
                        timeout=30.0,
                    )
                    if r.status_code == 200:
                        lote = r.json()
                        if isinstance(lote, list):
                            registros_gov.extend(lote)
                except Exception as e:
                    yield _sse({"estado": "aviso", "msg": f"Error CIIU {ciiu}: {e}"})

        if not registros_gov:
            yield _sse({"estado": "completado", "encontrados": 0, "nuevos": 0, "existentes": 0})
            return

        total_gov = len(registros_gov)
        yield _sse({"estado": "progreso", "msg": f"{total_gov} registros de datos.gov.co, cruzando con Supabase…", "encontrados": total_gov})

        # Normalizar columnas para cruzar_con_supabase
        df = pd.DataFrame(registros_gov)
        col_map = {
            "municipio": "ciudad",
            "codigo_ciiu_principal": "ciiu",
        }
        df.rename(columns={k: v for k, v in col_map.items() if k in df.columns}, inplace=True)

        try:
            resultado = await cruzar_con_supabase(df)
        except Exception as e:
            yield _sse({"estado": "error", "error": f"Error al cruzar con Supabase: {e}"})
            return

        nuevos     = len(resultado["nuevas"])
        existentes = len(resultado["duplicadas"]) + len(resultado["posibles"])

        # Guardar resultado en memoria
        rid = str(uuid.uuid4())
        _RESULTADOS[rid] = resultado
        # Mantener solo los últimos 5 resultados
        if len(_RESULTADOS) > 5:
            oldest = next(iter(_RESULTADOS))
            del _RESULTADOS[oldest]

        # Actualizar estado
        est = _leer_estado()
        est["ultima_ejecucion"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        est["total_encontrados_ultima"] = total_gov
        est["ultimo_resultado_id"] = rid
        if est.get("automatizacion_activa"):
            prox = datetime.utcnow() + timedelta(days=120)
            est["proxima_ejecucion"] = prox.strftime("%Y-%m-%d")
        _guardar_estado(est)

        yield _sse({
            "estado": "completado",
            "encontrados": total_gov,
            "nuevos": nuevos,
            "existentes": existentes,
            "resultado_id": rid,
        })

    if stream:
        return StreamingResponse(
            _run(),
            media_type="text/event-stream",
            headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
        )

    last: dict = {}
    async for evt in _run():
        line = evt.strip()
        if line.startswith("data: "):
            last = json.loads(line[6:])
    return JSONResponse(last)


@router.get("/resultado/{resultado_id}")
async def obtener_resultado(resultado_id: str):
    """Retorna el resultado de una búsqueda anterior para precargar en Comparación."""
    if resultado_id not in _RESULTADOS:
        return JSONResponse({"error": "Resultado no encontrado o expirado"}, status_code=404)
    r = _RESULTADOS[resultado_id]
    return JSONResponse({
        "resultado_id": resultado_id,
        "nuevas_count": len(r["nuevas"]),
        "duplicadas_count": len(r["duplicadas"]),
        "posibles_count": len(r["posibles"]),
        **r,
    })
