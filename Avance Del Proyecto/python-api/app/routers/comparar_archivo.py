"""
Router: Comparación de Archivos CSV contra Supabase
Clasifica registros de un CSV nuevo como: nuevas / duplicadas / posibles duplicadas.
"""

import io, json, os, unicodedata
from typing import AsyncGenerator

import httpx
import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

router = APIRouter(prefix="/comparar", tags=["Comparación"])


def _get_sb():
    sb_url = os.getenv("SUPABASE_URL", "")
    sb_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY", "")
    return sb_url, sb_key


def _norm(s: str) -> str:
    """Normaliza texto: minúsculas, sin tildes, sin caracteres especiales."""
    if not s:
        return ""
    s = s.lower().strip()
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def _similitud(a: str, b: str) -> float:
    """Similitud simple por palabras comunes / total palabras."""
    wa = set(_norm(a).split())
    wb = set(_norm(b).split())
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / max(len(wa), len(wb))


async def cruzar_con_supabase(df_nuevo: pd.DataFrame) -> dict:
    """
    Cruza un DataFrame con los registros de Supabase.
    Retorna dict con listas: nuevas, duplicadas, posibles.
    """
    sb_url, sb_key = _get_sb()
    headers = {"apikey": sb_key, "Authorization": f"Bearer {sb_key}"}

    # Obtener todos los registros de Supabase (paginado de a 1000)
    sb_records = []
    offset = 0
    async with httpx.AsyncClient() as client:
        while True:
            r = await client.get(
                f"{sb_url}/rest/v1/ferreterias"
                f"?select=razon_social,nit,fecha_matricula,ciudad&limit=1000&offset={offset}",
                headers=headers,
                timeout=30.0,
            )
            lote = r.json() if r.status_code == 200 else []
            if not isinstance(lote, list) or not lote:
                break
            sb_records.extend(lote)
            if len(lote) < 1000:
                break
            offset += 1000

    # Índices para búsqueda rápida
    sb_por_nit: dict[str, list[dict]] = {}
    for rec in sb_records:
        nit = str(rec.get("nit") or "").strip()
        if nit:
            sb_por_nit.setdefault(nit, []).append(rec)

    nuevas, duplicadas, posibles = [], [], []

    for _, fila in df_nuevo.iterrows():
        nit = str(fila.get("nit") or "").strip()
        razon = str(fila.get("razon_social") or fila.get("nombre") or "").strip()
        fecha = str(fila.get("fecha_matricula") or "").strip()
        ciudad = str(fila.get("ciudad") or "").strip()
        estado = str(fila.get("estado_matricula") or "ACTIVA").strip()

        entrada = {
            "razon_social": razon,
            "nit": nit,
            "ciudad": ciudad,
            "fecha_matricula": fecha,
            "estado": estado,
        }

        if nit and nit in sb_por_nit:
            coincidencias = sb_por_nit[nit]
            # Buscar si alguna coincidencia tiene misma fecha_matricula
            dup_exacta = any(
                str(c.get("fecha_matricula") or "").replace("-", "") == fecha.replace("-", "")
                for c in coincidencias
            )
            if dup_exacta:
                duplicadas.append(entrada)
            else:
                # Mismo NIT pero fecha diferente → posible duplicada
                mejor = coincidencias[0]
                entrada["coincide_con"] = {
                    "razon_social": mejor.get("razon_social", ""),
                    "nit": nit,
                    "ciudad": mejor.get("ciudad", ""),
                    "fecha_matricula": str(mejor.get("fecha_matricula") or ""),
                }
                posibles.append(entrada)
        elif razon:
            # Sin NIT: verificar similitud por nombre
            mejor_sim = 0.0
            mejor_rec = None
            for rec in sb_records[:5000]:  # limitar búsqueda
                sim = _similitud(razon, rec.get("razon_social") or "")
                if sim > mejor_sim:
                    mejor_sim = sim
                    mejor_rec = rec
            if mejor_sim >= 0.80 and mejor_rec:
                entrada["coincide_con"] = {
                    "razon_social": mejor_rec.get("razon_social", ""),
                    "nit": str(mejor_rec.get("nit") or ""),
                    "ciudad": mejor_rec.get("ciudad", ""),
                    "fecha_matricula": str(mejor_rec.get("fecha_matricula") or ""),
                }
                posibles.append(entrada)
            else:
                nuevas.append(entrada)
        else:
            nuevas.append(entrada)

    return {"nuevas": nuevas, "duplicadas": duplicadas, "posibles": posibles}


def _leer_csv(contenido: bytes) -> pd.DataFrame:
    """Intenta leer CSV con distintos separadores y encodings."""
    for enc in ("utf-8-sig", "latin-1"):
        for sep in (";", ",", "\t"):
            try:
                df = pd.read_csv(io.BytesIO(contenido), sep=sep, encoding=enc, dtype=str, low_memory=False)
                if len(df.columns) > 1:
                    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
                    return df
            except Exception:
                continue
    raise ValueError("No se pudo leer el CSV con los encodings/separadores conocidos")


@router.post("/subir")
async def subir_csv(archivo: UploadFile = File(...)):
    """Recibe un CSV, lo cruza con Supabase y devuelve clasificación en 3 categorías."""
    sb_url, sb_key = _get_sb()
    if not sb_url or not sb_key:
        raise HTTPException(status_code=503, detail="Supabase no configurado")

    contenido = await archivo.read()
    try:
        df = _leer_csv(contenido)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Normalizar columnas comunes
    col_map = {
        "nombre": "razon_social",
        "razon social": "razon_social",
        "fecha matricula": "fecha_matricula",
    }
    df.rename(columns=col_map, inplace=True)

    resultado = await cruzar_con_supabase(df)
    return JSONResponse({
        "total": len(df),
        "nuevas_count": len(resultado["nuevas"]),
        "duplicadas_count": len(resultado["duplicadas"]),
        "posibles_count": len(resultado["posibles"]),
        **resultado,
    })


@router.get("/descargar/{categoria}")
async def descargar_csv(categoria: str):
    """Descarga como CSV los resultados de una categoría: nuevas, duplicadas o posibles."""
    # Este endpoint es limitado — la lógica real requiere estado de sesión.
    # Para uso real, el frontend debe hacer POST /subir primero y usar el JSON devuelto.
    raise HTTPException(
        status_code=400,
        detail="Descarga directa no soportada sin sesión. Use el JSON de /comparar/subir "
               "y genere el CSV en el cliente, o use /comparar/exportar con body JSON.",
    )


@router.post("/exportar/{categoria}")
async def exportar_csv(categoria: str, datos: list[dict]):
    """Convierte una lista JSON a CSV descargable."""
    if categoria not in ("nuevas", "duplicadas", "posibles"):
        raise HTTPException(status_code=400, detail="Categoría inválida")
    if not datos:
        raise HTTPException(status_code=400, detail="Lista vacía")

    df = pd.DataFrame(datos)
    buf = io.StringIO()
    df.to_csv(buf, index=False, sep=";", encoding="utf-8-sig")
    buf.seek(0)

    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=ferreterias_{categoria}.csv"},
    )
