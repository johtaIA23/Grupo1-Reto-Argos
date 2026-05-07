"""
Router: Limpieza IA
Métricas de calidad de datos en Supabase y limpieza de duplicados por NIT.
"""

import json, os
from typing import AsyncGenerator

import httpx
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse, StreamingResponse

router = APIRouter(prefix="/limpieza", tags=["Limpieza IA"])


def _get_sb():
    sb_url = os.getenv("SUPABASE_URL", "")
    sb_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY", "")
    return sb_url, sb_key


def _sse(d: dict) -> str:
    return f"data: {json.dumps(d, ensure_ascii=False)}\n\n"


async def _count(client: httpx.AsyncClient, url: str, headers: dict) -> int:
    r = await client.get(
        url,
        headers={**headers, "Prefer": "count=exact"},
        timeout=15.0,
    )
    return int(r.headers.get("content-range", "0/0").split("/")[-1])


@router.get("/metricas")
async def metricas():
    """Consulta métricas de calidad en Supabase: sin teléfono, sin email, sin NIT, duplicados."""
    sb_url, sb_key = _get_sb()
    if not sb_url or not sb_key:
        return JSONResponse({"error": "Supabase no configurado"}, status_code=503)

    headers = {"apikey": sb_key, "Authorization": f"Bearer {sb_key}"}
    base = f"{sb_url}/rest/v1/ferreterias"

    async with httpx.AsyncClient() as client:
        total       = await _count(client, f"{base}?select=id&limit=1", headers)
        sin_tel     = await _count(client, f"{base}?select=id&telefono=is.null&limit=1", headers)
        sin_email   = await _count(client, f"{base}?select=id&email=is.null&limit=1", headers)
        sin_nit     = await _count(client, f"{base}?select=id&nit=is.null&limit=1", headers)

        # Duplicados: NITs que aparecen más de una vez
        try:
            r_nits = await client.get(
                f"{base}?select=nit&nit=not.is.null&limit=100000",
                headers=headers,
                timeout=30.0,
            )
            nits = [row["nit"] for row in r_nits.json() if row.get("nit")]
            from collections import Counter
            conteos = Counter(nits)
            dup_grupos = sum(1 for v in conteos.values() if v > 1)
            dup_registros = sum(v - 1 for v in conteos.values() if v > 1)
        except Exception:
            dup_grupos = 0
            dup_registros = 0

    return {
        "total": total,
        "sin_telefono": sin_tel,
        "sin_email": sin_email,
        "sin_nit": sin_nit,
        "duplicados_grupos": dup_grupos,
        "duplicados_registros": dup_registros,
    }


@router.post("/ejecutar")
async def ejecutar_limpieza(
    stream: bool = Query(True, description="true=SSE, false=JSON al finalizar"),
):
    """
    Limpieza IA: elimina duplicados por NIT conservando el registro con fecha_renovacion más reciente.
    """
    sb_url, sb_key = _get_sb()
    if not sb_url or not sb_key:
        return JSONResponse({"error": "Supabase no configurado"}, status_code=503)

    headers_r = {"apikey": sb_key, "Authorization": f"Bearer {sb_key}"}
    headers_w = {
        **headers_r,
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }
    base = f"{sb_url}/rest/v1/ferreterias"

    async def _run() -> AsyncGenerator[str, None]:
        eliminados = 0
        procesados = 0

        async with httpx.AsyncClient() as client:
            # Obtener todos los registros con NIT (id, nit, fecha_renovacion)
            yield _sse({"estado": "iniciando", "msg": "Cargando registros de Supabase…"})
            try:
                r = await client.get(
                    f"{base}?select=id,nit,fecha_renovacion&nit=not.is.null&limit=200000",
                    headers=headers_r,
                    timeout=60.0,
                )
                records = r.json()
            except Exception as e:
                yield _sse({"estado": "error", "error": str(e)})
                return

            if not isinstance(records, list):
                yield _sse({"estado": "error", "error": "Respuesta inválida de Supabase"})
                return

            # Agrupar por NIT
            from collections import defaultdict
            grupos: dict[str, list[dict]] = defaultdict(list)
            for rec in records:
                grupos[rec["nit"]].append(rec)

            dup_grupos = [(nit, recs) for nit, recs in grupos.items() if len(recs) > 1]
            total_grupos = len(dup_grupos)

            if total_grupos == 0:
                yield _sse({"estado": "completado", "msg": "No hay duplicados", "eliminados": 0})
                return

            yield _sse({"estado": "iniciando", "total": total_grupos, "msg": f"{total_grupos} grupos duplicados encontrados"})

            for i, (nit, recs) in enumerate(dup_grupos):
                # Ordenar por fecha_renovacion descendente; conservar el primero
                def _fecha(r):
                    f = str(r.get("fecha_renovacion") or "")
                    return f if f else "0000-00-00"
                recs_sorted = sorted(recs, key=_fecha, reverse=True)
                conservar_id = recs_sorted[0]["id"]
                eliminar_ids = [r["id"] for r in recs_sorted[1:]]

                for eid in eliminar_ids:
                    try:
                        await client.delete(
                            f"{base}?id=eq.{eid}",
                            headers=headers_w,
                            timeout=15.0,
                        )
                        eliminados += 1
                    except Exception:
                        pass

                procesados += 1
                pct = round(procesados / total_grupos * 100, 1)
                if procesados % 10 == 0 or procesados == total_grupos:
                    yield _sse({
                        "estado": "progreso",
                        "procesados": procesados,
                        "total": total_grupos,
                        "eliminados": eliminados,
                        "pct": pct,
                    })

        yield _sse({
            "estado": "completado",
            "eliminados": eliminados,
            "grupos_procesados": procesados,
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
