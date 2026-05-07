"""
Router: Exportación Google Sheets con IA
Métricas de completitud, revisión IA de inconsistencias y exportación vía n8n.
"""

import json, os, re, unicodedata
from typing import AsyncGenerator

import httpx
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse, StreamingResponse

router = APIRouter(prefix="/sheets", tags=["Google Sheets"])

# Campos a exportar a Google Sheets (en el orden de las columnas del Sheet)
CAMPOS_SHEETS = [
    "razon_social", "representante_legal", "telefono", "email",
    "direccion", "ciudad", "departamento", "lng", "lat",
    "estado_info", "estado_legal", "num_fuentes",
    "nit", "ciiu", "website", "camara_comercio",
    "estado_matricula", "fecha_renovacion", "fecha_matricula",
]


def _get_sb():
    sb_url = os.getenv("SUPABASE_URL", "")
    sb_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY", "")
    return sb_url, sb_key


def _get_n8n_webhook():
    return os.getenv("N8N_WEBHOOK_SHEETS", "http://n8n:5678/webhook/sheets-exportar")


def _sse(d: dict) -> str:
    return f"data: {json.dumps(d, ensure_ascii=False)}\n\n"


async def _count(client: httpx.AsyncClient, url: str, headers: dict) -> int:
    r = await client.get(url, headers={**headers, "Prefer": "count=exact"}, timeout=15.0)
    return int(r.headers.get("content-range", "0/0").split("/")[-1])


@router.get("/metricas")
async def metricas():
    """Total registros, cuántos tienen lat+lng+telefono (listos para exportar), calidad %."""
    sb_url, sb_key = _get_sb()
    if not sb_url or not sb_key:
        return JSONResponse({"error": "Supabase no configurado"}, status_code=503)

    headers = {"apikey": sb_key, "Authorization": f"Bearer {sb_key}"}
    base = f"{sb_url}/rest/v1/ferreterias"

    async with httpx.AsyncClient() as client:
        total  = await _count(client, f"{base}?select=id&limit=1", headers)
        listos = await _count(
            client,
            f"{base}?select=id&lat=not.is.null&lng=not.is.null&telefono=not.is.null&limit=1",
            headers,
        )

    calidad_pct = round(listos / total * 100, 1) if total else 0
    return {"total": total, "listos": listos, "calidad_pct": calidad_pct}


def _revisar_inconsistencias(records: list[dict]) -> list[dict]:
    """Detecta inconsistencias comunes y sugiere correcciones."""
    correcciones = []

    for rec in records:
        razon = rec.get("razon_social") or ""
        tel = str(rec.get("telefono") or "")
        nit = rec.get("nit") or ""

        # Razón social en minúsculas (debería ser mayúsculas o Title Case)
        if razon and razon == razon.lower() and len(razon) > 5:
            correcciones.append({
                "nit": nit,
                "campo": "razon_social",
                "valor_original": razon,
                "valor_sugerido": razon.upper(),
                "razon": "Nombre en minúsculas",
            })

        # Teléfono con formato extraño (debe tener 7 o 10 dígitos)
        if tel:
            digits = re.sub(r"\D", "", tel)
            if digits and len(digits) not in (7, 10):
                correcciones.append({
                    "nit": nit,
                    "campo": "telefono",
                    "valor_original": tel,
                    "valor_sugerido": digits[:10],
                    "razon": f"Teléfono con {len(digits)} dígitos (esperado 7 o 10)",
                })

        # NIT con caracteres no numéricos (ignorando guión)
        if nit:
            nit_clean = re.sub(r"[^\d\-]", "", str(nit))
            if nit_clean != str(nit).strip():
                correcciones.append({
                    "nit": nit,
                    "campo": "nit",
                    "valor_original": str(nit),
                    "valor_sugerido": nit_clean,
                    "razon": "NIT con caracteres inválidos",
                })

    return correcciones[:200]  # máximo 200 correcciones por ejecución


@router.post("/preparar-ia")
async def preparar_ia(
    stream: bool = Query(True),
    limite: int = Query(5000, ge=100, le=50000),
):
    """Revisa registros de Supabase y emite correcciones IA vía SSE."""
    sb_url, sb_key = _get_sb()
    if not sb_url or not sb_key:
        return JSONResponse({"error": "Supabase no configurado"}, status_code=503)

    headers = {"apikey": sb_key, "Authorization": f"Bearer {sb_key}"}

    async def _run() -> AsyncGenerator[str, None]:
        yield _sse({"estado": "iniciando", "msg": "Consultando registros de Supabase…"})

        async with httpx.AsyncClient() as client:
            try:
                r = await client.get(
                    f"{sb_url}/rest/v1/ferreterias"
                    f"?select=nit,razon_social,telefono&limit={limite}",
                    headers=headers,
                    timeout=60.0,
                )
                records = r.json()
            except Exception as e:
                yield _sse({"estado": "error", "error": str(e)})
                return

        if not isinstance(records, list):
            yield _sse({"estado": "error", "error": "Respuesta inválida de Supabase"})
            return

        total = len(records)
        yield _sse({"estado": "analizando", "total": total, "msg": f"Analizando {total} registros…"})

        correcciones = _revisar_inconsistencias(records)

        # Emitir correcciones de a 20
        for i in range(0, len(correcciones), 20):
            lote = correcciones[i:i + 20]
            yield _sse({
                "estado": "progreso",
                "pct": round((i + len(lote)) / max(len(correcciones), 1) * 100, 1),
                "correcciones_parciales": lote,
            })

        yield _sse({
            "estado": "completado",
            "total_revisados": total,
            "total_correcciones": len(correcciones),
            "correcciones": correcciones,
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


@router.post("/exportar")
async def exportar(limite: int = Query(100000, ge=1)):
    """Envía los datos de Supabase al webhook n8n para exportar a Google Sheets."""
    sb_url, sb_key = _get_sb()
    if not sb_url or not sb_key:
        return JSONResponse({"error": "Supabase no configurado"}, status_code=503)

    n8n_url = _get_n8n_webhook()
    headers_sb = {"apikey": sb_key, "Authorization": f"Bearer {sb_key}"}
    campos = ",".join(CAMPOS_SHEETS)

    async with httpx.AsyncClient() as client:
        # Obtener datos de Supabase
        try:
            r = await client.get(
                f"{sb_url}/rest/v1/ferreterias?select={campos}&limit={limite}",
                headers=headers_sb,
                timeout=60.0,
            )
            registros = r.json()
        except Exception as e:
            return JSONResponse({"error": f"Error leyendo Supabase: {e}"}, status_code=503)

        if not isinstance(registros, list):
            return JSONResponse({"error": "Respuesta inválida de Supabase"}, status_code=503)

        # Enviar a n8n
        try:
            resp = await client.post(
                n8n_url,
                json={"registros": registros, "total": len(registros), "campos": CAMPOS_SHEETS},
                timeout=30.0,
            )
            return JSONResponse({
                "ok": True,
                "total_enviados": len(registros),
                "n8n_status": resp.status_code,
                "n8n_respuesta": resp.text[:300],
            })
        except Exception as e:
            return JSONResponse({"error": f"Error enviando a n8n: {e}"}, status_code=503)
