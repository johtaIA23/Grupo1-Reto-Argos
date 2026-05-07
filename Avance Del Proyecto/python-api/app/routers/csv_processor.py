"""
Router: Procesamiento de CSV con pandas
Carga el CSV de ferreterías, lo limpia, clasifica y sirve en páginas.
El DataFrame se cachea en memoria: se lee UNA sola vez del disco.
"""

import csv as _csv

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from app.config import settings
from app.models import (
    ConsultaRequest,
    ConsultaResponse,
    Ferreteria,
    ProcesarCSVRequest,
    ProcesarCSVResponse,
)

router = APIRouter(tags=["CSV"])

# Cache global del DataFrame (None hasta el primer request o carga explícita)
_df_cache: pd.DataFrame | None = None


# ---------------------------------------------------------------------------
# Funciones internas
# ---------------------------------------------------------------------------

def get_dataframe() -> pd.DataFrame:
    """Devuelve el DataFrame cacheado, cargándolo si aún no existe."""
    global _df_cache
    if _df_cache is None:
        _df_cache = _cargar_y_limpiar_csv()
    return _df_cache


def invalidar_cache() -> None:
    """Fuerza recarga del CSV en el siguiente request."""
    global _df_cache
    _df_cache = None


def _cargar_y_limpiar_csv() -> pd.DataFrame:
    """
    Lee el CSV con pandas, normaliza columnas, aplica clasificación.
    Retorna un DataFrame limpio y listo para servir.
    """
    try:
        # Auto-detectar encoding y separador
        _enc = "utf-8-sig"
        try:
            with open(settings.csv_path, "r", encoding="utf-8-sig") as _f:
                _sample = _f.read(4096)
        except UnicodeDecodeError:
            _enc = "latin-1"
            with open(settings.csv_path, "r", encoding="latin-1") as _f:
                _sample = _f.read(4096)
        try:
            _dialect = _csv.Sniffer().sniff(_sample, delimiters=",;\t|")
            _sep = _dialect.delimiter
        except _csv.Error:
            _sep = ","

        df = pd.read_csv(
            settings.csv_path,
            encoding=_enc,
            sep=_sep,
            dtype=str,               # todo como texto, evita conversiones automáticas
            keep_default_na=False,   # las celdas vacías quedan como "" no NaN
            na_values=["NULL", "null", "0000-00-00", "N/A", "n/a"],
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=503,
            detail=f"CSV no encontrado en {settings.csv_path}. "
                   "Verifica que el archivo esté en la carpeta 'data/'.",
        )

    # ── Normalizar nombres de columnas ──────────────────────────────────────
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    # ── Limpiar valores de texto ────────────────────────────────────────────
    cols_texto = [
        "camara_comercio", "razon_social", "nit", "numero_identificacion",
        "organizacion_juridica", "estado_matricula", "representante_legal",
        "primer_nombre", "primer_apellido", "nombre_comercial",
        "direccion", "ciudad", "municipio", "departamento",
        "telefono", "email", "website", "sitio_web",
    ]
    for col in cols_texto:
        if col in df.columns:
            df[col] = (
                df[col]
                .str.strip()
                .replace("", np.nan)   # cadena vacía → NaN
            )

    # ── Consolidar columnas alternativas ────────────────────────────────────
    if "nit" in df.columns and "numero_identificacion" in df.columns:
        df["nit"] = df["nit"].fillna(df["numero_identificacion"])

    if "ciudad" in df.columns and "municipio" in df.columns:
        df["ciudad"] = df["ciudad"].fillna(df["municipio"])

    if "website" in df.columns and "sitio_web" in df.columns:
        df["website"] = df["website"].fillna(df["sitio_web"])

    # ── Construir representante_legal desde partes si está vacío ────────────
    if "representante_legal" in df.columns:
        mask = df["representante_legal"].isna()
        nombre_col   = df.get("primer_nombre",   pd.Series(dtype=str))
        apellido_col = df.get("primer_apellido", pd.Series(dtype=str))
        df.loc[mask, "representante_legal"] = (
            nombre_col.fillna("").str.strip() + " " +
            apellido_col.fillna("").str.strip()
        ).str.strip().replace("", np.nan)

    # ── Estado matrícula por defecto ────────────────────────────────────────
    if "estado_matricula" in df.columns:
        df["estado_matricula"] = df["estado_matricula"].fillna("ACTIVA")
    else:
        df["estado_matricula"] = "ACTIVA"

    # ── Parseo de fechas ────────────────────────────────────────────────────
    for col_fecha in ["fecha_matricula", "fecha_renovacion"]:
        if col_fecha in df.columns:
            df[col_fecha] = (
                pd.to_datetime(df[col_fecha], errors="coerce", dayfirst=True)
                .dt.strftime("%Y-%m-%d")
            )
            df[col_fecha] = df[col_fecha].replace("NaT", np.nan)

    # ── Eliminar registros sin nombre ───────────────────────────────────────
    if "razon_social" not in df.columns:
        raise HTTPException(
            status_code=500,
            detail="El CSV no tiene columna 'razon_social'. Revisa el formato del archivo.",
        )
    df = df.dropna(subset=["razon_social"])
    df = df[df["razon_social"].str.strip() != ""]

    # ── Clasificación (vectorizada con numpy, muy rápido) ───────────────────
    tiene_nombre    = df["razon_social"].notna()
    tiene_direccion = df["direccion"].notna() if "direccion" in df.columns else pd.Series(False, index=df.index)
    tiene_telefono  = df["telefono"].notna()  if "telefono"  in df.columns else pd.Series(False, index=df.index)

    df["estado_info"] = np.where(
        tiene_nombre & tiene_direccion & tiene_telefono,
        "Completa",
        "Incompleta",
    )

    tiene_nit      = df["nit"].notna() if "nit" in df.columns else pd.Series(False, index=df.index)
    matricula_ok   = df["estado_matricula"] == "ACTIVA"

    df["estado_legal"] = np.where(
        tiene_nit | matricula_ok,
        "Legalmente constituida",
        "No legalmente constituida",
    )

    df["estado_actividad"] = "Pendiente"
    df["fuente"]           = "camara_comercio"

    return df.reset_index(drop=True)


def _fila_a_ferreteria(row: dict) -> Ferreteria:
    """Convierte una fila del DataFrame (dict) al modelo Ferreteria."""
    def val(key: str):
        v = row.get(key)
        return None if (v is None or (isinstance(v, float) and np.isnan(v))) else str(v)

    return Ferreteria(
        camara_comercio      = val("camara_comercio"),
        razon_social         = val("razon_social") or "",
        nit                  = val("nit"),
        organizacion_juridica = val("organizacion_juridica"),
        estado_matricula     = val("estado_matricula"),
        fecha_matricula      = val("fecha_matricula"),
        fecha_renovacion     = val("fecha_renovacion"),
        representante_legal  = val("representante_legal"),
        nombre_comercial     = val("nombre_comercial"),
        direccion            = val("direccion"),
        ciudad               = val("ciudad"),
        departamento         = val("departamento"),
        telefono             = val("telefono"),
        email                = val("email"),
        website              = val("website"),
        estado_info          = val("estado_info") or "Incompleta",
        estado_legal         = val("estado_legal") or "No legalmente constituida",
        estado_actividad     = val("estado_actividad") or "Pendiente",
        fuente               = val("fuente") or "camara_comercio",
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/procesar-csv", response_model=ProcesarCSVResponse)
async def procesar_csv(req: ProcesarCSVRequest):
    """
    Devuelve una página del CSV procesado con pandas.
    El agente de n8n llama este endpoint en bucle incrementando 'offset'
    hasta que 'tiene_mas' sea false.
    """
    df = get_dataframe()
    total = len(df)

    # Filtros opcionales
    resultado = df.copy()
    if req.filtro_ciudad:
        resultado = resultado[
            resultado["ciudad"].str.contains(req.filtro_ciudad, case=False, na=False)
        ]
    if req.filtro_departamento:
        resultado = resultado[
            resultado["departamento"].str.contains(req.filtro_departamento, case=False, na=False)
        ]

    # Paginación
    pagina = resultado.iloc[req.offset : req.offset + req.limit]
    tiene_mas = (req.offset + req.limit) < len(resultado)

    registros = [_fila_a_ferreteria(row) for row in pagina.to_dict("records")]

    return ProcesarCSVResponse(
        total_registros      = total,
        registros_en_pagina  = len(registros),
        offset               = req.offset,
        limit                = req.limit,
        tiene_mas            = tiene_mas,
        data                 = registros,
    )


@router.get("/consultar", response_model=ConsultaResponse)
async def consultar(
    ciudad: str = None,
    departamento: str = None,
    estado_info: str = None,
    estado_legal: str = None,
    camara_comercio: str = None,
    busqueda: str = None,
    limit: int = 50,
    offset: int = 0,
):
    """
    Consulta flexible para el modo pregunta/respuesta del agente.
    Filtra por cualquier combinación de campos.
    Ejemplos:
      /consultar?ciudad=Medellín&estado_info=Incompleta
      /consultar?departamento=Antioquia&limit=10
      /consultar?busqueda=ferretería central
    """
    df = get_dataframe()
    resultado = df.copy()

    if ciudad:
        resultado = resultado[
            resultado["ciudad"].str.contains(ciudad, case=False, na=False)
        ]
    if departamento:
        resultado = resultado[
            resultado["departamento"].str.contains(departamento, case=False, na=False)
        ]
    if estado_info:
        resultado = resultado[resultado["estado_info"] == estado_info]
    if estado_legal:
        resultado = resultado[resultado["estado_legal"] == estado_legal]
    if camara_comercio:
        resultado = resultado[
            resultado["camara_comercio"].str.contains(camara_comercio, case=False, na=False)
        ]
    if busqueda:
        resultado = resultado[
            resultado["razon_social"].str.contains(busqueda, case=False, na=False)
        ]

    total_encontrados = len(resultado)
    pagina = resultado.iloc[offset : offset + limit]
    registros = [_fila_a_ferreteria(row) for row in pagina.to_dict("records")]

    return ConsultaResponse(
        total_encontrados   = total_encontrados,
        registros_en_pagina = len(registros),
        data                = registros,
    )


class ConsultaPostBody(BaseModel):
    ciudad: str | None = None
    departamento: str | None = None
    estado_info: str | None = None
    estado_legal: str | None = None
    camara_comercio: str | None = None
    busqueda: str | None = None
    limit: int = 20
    offset: int = 0


@router.post("/consultar", response_model=ConsultaResponse)
async def consultar_post(body: ConsultaPostBody):
    """POST equivalente de GET /consultar. Acepta los mismos filtros en JSON body.
    Usado por el AI Agent para evitar problemas de schema con Groq."""
    return await consultar(
        ciudad=body.ciudad,
        departamento=body.departamento,
        estado_info=body.estado_info,
        estado_legal=body.estado_legal,
        camara_comercio=body.camara_comercio,
        busqueda=body.busqueda,
        limit=body.limit,
        offset=body.offset,
    )


@router.post("/reload-csv")
async def reload_csv():
    """Fuerza la recarga del CSV desde disco (sin reiniciar Docker)."""
    invalidar_cache()
    df = get_dataframe()
    return {
        "status":          "recargado",
        "total_registros": len(df),
        "csv_path":        settings.csv_path,
    }


@router.get("/export-rtm")
async def export_rtm():
    """
    Exporta el CSV en formato JSON compatible con el dashboard RTM.
    Devuelve todos los registros con los campos que necesita el RTM.
    """
    df = get_dataframe().copy()

    # Detectar columna de probabilidad
    prob_col = next(
        (c for c in df.columns if "probabilidad" in c.lower() and "cemento" in c.lower()),
        next((c for c in df.columns if "probabilidad" in c.lower()), None),
    )
    if prob_col and prob_col != "probabilidad_cemento":
        df["probabilidad_cemento"] = df[prob_col]

    # Campos que necesita el RTM (en orden)
    campos = [
        "camara_comercio", "razon_social", "nit", "estado_matricula",
        "fecha_matricula", "fecha_renovacion", "representante_legal",
        "ciudad", "departamento", "telefono", "email",
        "lat", "lng", "estado_info", "estado_legal", "estado_actividad",
        "num_fuentes", "formatted_address", "probabilidad_cemento",
    ]
    cols = [c for c in campos if c in df.columns]
    result = df[cols].copy()
    result.insert(0, "id", df.index.astype(str))

    # lat/lng como float (vienen como string del CSV)
    for col in ("lat", "lng", "num_fuentes"):
        if col in result.columns:
            result[col] = pd.to_numeric(result[col], errors="coerce")

    # NaN → None para JSON válido
    result = result.where(result.notna(), other=None)

    json_str = result.to_json(orient="records", force_ascii=False)
    return Response(
        content=json_str,
        media_type="application/json",
        headers={"Access-Control-Allow-Origin": "*"},
    )


@router.get("/export-rtm-supabase")
async def export_rtm_supabase():
    """
    Exporta datos desde Supabase en el formato JSON que espera el dashboard RTM.
    Muestra los datos enriquecidos (con lat/lng, teléfono, ciudad, etc.).
    """
    import json as _json
    import os

    import httpx

    supabase_url = os.getenv("SUPABASE_URL", settings.supabase_url)
    supabase_key = os.getenv("SUPABASE_KEY", os.getenv("SUPABASE_SERVICE_KEY", settings.supabase_key))
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
    }

    select_cols = (
        "camara_comercio,razon_social,nit,estado_matricula,fecha_matricula,"
        "fecha_renovacion,representante_legal,ciudad,departamento,telefono,"
        "email,lat,lng,estado_info,estado_legal,num_fuentes,probabilidad,direccion"
    )

    all_rows: list[dict] = []
    page = 0
    page_size = 1000
    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            r = await client.get(
                f"{supabase_url}/rest/v1/ferreterias",
                headers={
                    **headers,
                    "Range": f"{page * page_size}-{(page + 1) * page_size - 1}",
                    "Prefer": "count=none",
                },
                params={"select": select_cols, "order": "razon_social.asc"},
            )
            if r.status_code not in (200, 206):
                return Response(
                    content=_json.dumps({"error": f"Supabase {r.status_code}: {r.text[:200]}"}),
                    media_type="application/json",
                    status_code=502,
                )
            batch = r.json()
            if not batch:
                break
            all_rows.extend(batch)
            if len(batch) < page_size:
                break
            page += 1

    result = [
        {
            "id": str(i),
            "camara_comercio":     row.get("camara_comercio"),
            "razon_social":        row.get("razon_social"),
            "nit":                 row.get("nit"),
            "estado_matricula":    row.get("estado_matricula"),
            "fecha_matricula":     row.get("fecha_matricula"),
            "fecha_renovacion":    row.get("fecha_renovacion"),
            "representante_legal": row.get("representante_legal"),
            "ciudad":              row.get("ciudad"),
            "departamento":        row.get("departamento"),
            "telefono":            row.get("telefono"),
            "email":               row.get("email"),
            "lat":                 row.get("lat"),
            "lng":                 row.get("lng"),
            "estado_info":         row.get("estado_info"),
            "estado_legal":        row.get("estado_legal"),
            "num_fuentes":         row.get("num_fuentes"),
            "formatted_address":   row.get("direccion"),
            "probabilidad_cemento": row.get("probabilidad"),
        }
        for i, row in enumerate(all_rows)
    ]

    return Response(
        content=_json.dumps(result, ensure_ascii=False),
        media_type="application/json",
        headers={"Access-Control-Allow-Origin": "*"},
    )
