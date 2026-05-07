"""
Router: Enriquecimiento Google Maps
Find Place (Colombia bbox) + Place Details → lat/lng, ciudad, departamento, teléfono, website.
Actualiza directamente en Supabase.
"""

import asyncio
import json
import os
import re
import unicodedata
from typing import AsyncGenerator

import httpx
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse, StreamingResponse

from app.config import settings

router = APIRouter(prefix="/enriquecimiento", tags=["Enriquecimiento"])

_COLOMBIA_BBOX = "rectangle:-4.23,-81.73|13.39,-66.87"

# Centroide por cámara de comercio — da un hint geográfico a Find Place
_CAMARAS: dict[str, dict] = {
    "bogota":              {"ciudad": "Bogotá",               "departamento": "Bogotá D.C.",       "lat":  4.7110, "lng": -74.0721},
    "bogota d.c":          {"ciudad": "Bogotá",               "departamento": "Bogotá D.C.",       "lat":  4.7110, "lng": -74.0721},
    "cundinamarca":        {"ciudad": "Bogotá",               "departamento": "Cundinamarca",      "lat":  4.7110, "lng": -74.0721},
    "medellin":            {"ciudad": "Medellín",             "departamento": "Antioquia",         "lat":  6.2442, "lng": -75.5812},
    "antioquia":           {"ciudad": "Medellín",             "departamento": "Antioquia",         "lat":  6.2442, "lng": -75.5812},
    "cali":                {"ciudad": "Cali",                 "departamento": "Valle del Cauca",   "lat":  3.4516, "lng": -76.5319},
    "valle":               {"ciudad": "Cali",                 "departamento": "Valle del Cauca",   "lat":  3.4516, "lng": -76.5319},
    "barranquilla":        {"ciudad": "Barranquilla",         "departamento": "Atlántico",         "lat": 10.9685, "lng": -74.7813},
    "atlantico":           {"ciudad": "Barranquilla",         "departamento": "Atlántico",         "lat": 10.9685, "lng": -74.7813},
    "cartagena":           {"ciudad": "Cartagena",            "departamento": "Bolívar",           "lat": 10.3910, "lng": -75.4794},
    "bolivar":             {"ciudad": "Cartagena",            "departamento": "Bolívar",           "lat": 10.3910, "lng": -75.4794},
    "cucuta":              {"ciudad": "Cúcuta",               "departamento": "Norte de Santander","lat":  7.8939, "lng": -72.5078},
    "norte de santander":  {"ciudad": "Cúcuta",               "departamento": "Norte de Santander","lat":  7.8939, "lng": -72.5078},
    "bucaramanga":         {"ciudad": "Bucaramanga",          "departamento": "Santander",         "lat":  7.1193, "lng": -73.1227},
    "santander":           {"ciudad": "Bucaramanga",          "departamento": "Santander",         "lat":  7.1193, "lng": -73.1227},
    "barrancabermeja":     {"ciudad": "Barrancabermeja",      "departamento": "Santander",         "lat":  7.0648, "lng": -73.8543},
    "pereira":             {"ciudad": "Pereira",              "departamento": "Risaralda",         "lat":  4.8133, "lng": -75.6961},
    "risaralda":           {"ciudad": "Pereira",              "departamento": "Risaralda",         "lat":  4.8133, "lng": -75.6961},
    "manizales":           {"ciudad": "Manizales",            "departamento": "Caldas",            "lat":  5.0703, "lng": -75.5138},
    "caldas":              {"ciudad": "Manizales",            "departamento": "Caldas",            "lat":  5.0703, "lng": -75.5138},
    "ibague":              {"ciudad": "Ibagué",               "departamento": "Tolima",            "lat":  4.4389, "lng": -75.2322},
    "tolima":              {"ciudad": "Ibagué",               "departamento": "Tolima",            "lat":  4.4389, "lng": -75.2322},
    "armenia":             {"ciudad": "Armenia",              "departamento": "Quindío",           "lat":  4.5339, "lng": -75.6811},
    "quindio":             {"ciudad": "Armenia",              "departamento": "Quindío",           "lat":  4.5339, "lng": -75.6811},
    "villavicencio":       {"ciudad": "Villavicencio",        "departamento": "Meta",              "lat":  4.1420, "lng": -73.6266},
    "meta":                {"ciudad": "Villavicencio",        "departamento": "Meta",              "lat":  4.1420, "lng": -73.6266},
    "pasto":               {"ciudad": "Pasto",                "departamento": "Nariño",            "lat":  1.2136, "lng": -77.2811},
    "narino":              {"ciudad": "Pasto",                "departamento": "Nariño",            "lat":  1.2136, "lng": -77.2811},
    "monteria":            {"ciudad": "Montería",             "departamento": "Córdoba",           "lat":  8.7575, "lng": -75.8857},
    "cordoba":             {"ciudad": "Montería",             "departamento": "Córdoba",           "lat":  8.7575, "lng": -75.8857},
    "neiva":               {"ciudad": "Neiva",                "departamento": "Huila",             "lat":  2.9273, "lng": -75.2819},
    "huila":               {"ciudad": "Neiva",                "departamento": "Huila",             "lat":  2.9273, "lng": -75.2819},
    "valledupar":          {"ciudad": "Valledupar",           "departamento": "Cesar",             "lat": 10.4631, "lng": -73.2532},
    "cesar":               {"ciudad": "Valledupar",           "departamento": "Cesar",             "lat": 10.4631, "lng": -73.2532},
    "sincelejo":           {"ciudad": "Sincelejo",            "departamento": "Sucre",             "lat":  9.3047, "lng": -75.3978},
    "sucre":               {"ciudad": "Sincelejo",            "departamento": "Sucre",             "lat":  9.3047, "lng": -75.3978},
    "popayan":             {"ciudad": "Popayán",              "departamento": "Cauca",             "lat":  2.4448, "lng": -76.6147},
    "cauca":               {"ciudad": "Popayán",              "departamento": "Cauca",             "lat":  2.4448, "lng": -76.6147},
    "santa marta":         {"ciudad": "Santa Marta",          "departamento": "Magdalena",         "lat": 11.2408, "lng": -74.2110},
    "magdalena":           {"ciudad": "Santa Marta",          "departamento": "Magdalena",         "lat": 11.2408, "lng": -74.2110},
    "tunja":               {"ciudad": "Tunja",                "departamento": "Boyacá",            "lat":  5.5353, "lng": -73.3678},
    "boyaca":              {"ciudad": "Tunja",                "departamento": "Boyacá",            "lat":  5.5353, "lng": -73.3678},
    "sogamoso":            {"ciudad": "Sogamoso",             "departamento": "Boyacá",            "lat":  5.7172, "lng": -72.9266},
    "duitama":             {"ciudad": "Duitama",              "departamento": "Boyacá",            "lat":  5.8261, "lng": -73.0298},
    "florencia":           {"ciudad": "Florencia",            "departamento": "Caquetá",           "lat":  1.6144, "lng": -75.6062},
    "caqueta":             {"ciudad": "Florencia",            "departamento": "Caquetá",           "lat":  1.6144, "lng": -75.6062},
    "quibdo":              {"ciudad": "Quibdó",               "departamento": "Chocó",             "lat":  5.6919, "lng": -76.6583},
    "choco":               {"ciudad": "Quibdó",               "departamento": "Chocó",             "lat":  5.6919, "lng": -76.6583},
    "riohacha":            {"ciudad": "Riohacha",             "departamento": "La Guajira",        "lat": 11.5444, "lng": -72.9072},
    "guajira":             {"ciudad": "Riohacha",             "departamento": "La Guajira",        "lat": 11.5444, "lng": -72.9072},
    "mocoa":               {"ciudad": "Mocoa",                "departamento": "Putumayo",          "lat":  1.1522, "lng": -76.6479},
    "putumayo":            {"ciudad": "Mocoa",                "departamento": "Putumayo",          "lat":  1.1522, "lng": -76.6479},
    "yopal":               {"ciudad": "Yopal",                "departamento": "Casanare",          "lat":  5.3378, "lng": -72.3959},
    "casanare":            {"ciudad": "Yopal",                "departamento": "Casanare",          "lat":  5.3378, "lng": -72.3959},
    "san jose del guaviare": {"ciudad": "San José del Guaviare", "departamento": "Guaviare",      "lat":  2.5683, "lng": -72.6407},
    "guaviare":            {"ciudad": "San José del Guaviare", "departamento": "Guaviare",        "lat":  2.5683, "lng": -72.6407},
    "inirida":             {"ciudad": "Inírida",              "departamento": "Guainía",           "lat":  3.8653, "lng": -67.9239},
    "guainia":             {"ciudad": "Inírida",              "departamento": "Guainía",           "lat":  3.8653, "lng": -67.9239},
    "mitu":                {"ciudad": "Mitú",                 "departamento": "Vaupés",            "lat":  1.2534, "lng": -70.2336},
    "vaupes":              {"ciudad": "Mitú",                 "departamento": "Vaupés",            "lat":  1.2534, "lng": -70.2336},
    "puerto carreno":      {"ciudad": "Puerto Carreño",       "departamento": "Vichada",           "lat":  6.1891, "lng": -67.4847},
    "vichada":             {"ciudad": "Puerto Carreño",       "departamento": "Vichada",           "lat":  6.1891, "lng": -67.4847},
    "leticia":             {"ciudad": "Leticia",              "departamento": "Amazonas",          "lat": -4.2153, "lng": -69.9406},
    "amazonas":            {"ciudad": "Leticia",              "departamento": "Amazonas",          "lat": -4.2153, "lng": -69.9406},
    "buenaventura":        {"ciudad": "Buenaventura",         "departamento": "Valle del Cauca",   "lat":  3.8801, "lng": -77.0311},
    "palmira":             {"ciudad": "Palmira",              "departamento": "Valle del Cauca",   "lat":  3.5398, "lng": -76.3027},
    "tulua":               {"ciudad": "Tuluá",                "departamento": "Valle del Cauca",   "lat":  4.0841, "lng": -76.1946},
    "bello":               {"ciudad": "Bello",                "departamento": "Antioquia",         "lat":  6.3397, "lng": -75.5580},
    "itagui":              {"ciudad": "Itagüí",               "departamento": "Antioquia",         "lat":  6.1847, "lng": -75.5990},
    "envigado":            {"ciudad": "Envigado",             "departamento": "Antioquia",         "lat":  6.1742, "lng": -75.5919},
    "soledad":             {"ciudad": "Soledad",              "departamento": "Atlántico",         "lat": 10.9176, "lng": -74.7641},
    "girardot":            {"ciudad": "Girardot",             "departamento": "Cundinamarca",      "lat":  4.3039, "lng": -74.8051},
}


def _hint_camara(camara: str | None) -> dict | None:
    """Retorna hint de ciudad/lat/lng para una cámara de comercio. Búsqueda parcial."""
    if not camara:
        return None
    key = camara.lower().strip()
    if key in _CAMARAS:
        return _CAMARAS[key]
    for k, v in _CAMARAS.items():
        if k in key:
            return v
    return None


_NOMINATIM_UA = "Ferreterias-Colombia/1.0 (census-tool)"


async def _enrich_one_nominatim(
    client: httpx.AsyncClient,
    record: dict,
    city_cache: dict,
) -> tuple[dict, str]:
    """
    Geocodifica a nivel ciudad usando Nominatim (OpenStreetMap) — gratuito, sin API key.
    Usa city_cache para reutilizar resultados de ciudades ya consultadas (evita llamadas repetidas).
    Solo duerme 1.1s cuando hace una llamada real a Nominatim.
    """
    hint = _hint_camara(record.get("camara_comercio"))
    ciudad = (hint["ciudad"] if hint else (record.get("ciudad") or "")).strip()
    departamento = (hint["departamento"] if hint else (record.get("departamento") or "")).strip()

    if not ciudad:
        return {}, "sin_ciudad"

    cache_key = f"{ciudad}|{departamento}"

    if cache_key not in city_cache:
        query = f"{ciudad}, {departamento}, Colombia" if departamento else f"{ciudad}, Colombia"
        try:
            resp = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": query, "format": "json", "limit": 1, "countrycodes": "co", "addressdetails": 1},
                headers={"User-Agent": _NOMINATIM_UA},
                timeout=15.0,
            )
            results = resp.json()
        except Exception as e:
            city_cache[cache_key] = None
            return {}, f"error_red:{type(e).__name__}"

        # Rate limit: solo cuando hacemos llamada real
        await asyncio.sleep(1.1)

        if not results or "Colombia" not in results[0].get("display_name", ""):
            city_cache[cache_key] = None
        else:
            best = results[0]
            addr = best.get("address", {})
            city_cache[cache_key] = {
                "lat": float(best["lat"]),
                "lng": float(best["lon"]),
                "ciudad": (addr.get("city") or addr.get("town") or addr.get("village")
                           or addr.get("municipality") or ciudad),
                "departamento": addr.get("state") or departamento,
            }

    cached = city_cache[cache_key]
    if cached is None:
        return {}, "ZERO_RESULTS"

    patch: dict = {
        "geocodificado": True,
        "num_fuentes": (record.get("num_fuentes") or 0) + 1,
        "lat": cached["lat"],
        "lng": cached["lng"],
        "formatted_address": f"{cached['ciudad']}, {cached['departamento']}, Colombia",
        "ciudad": cached["ciudad"],
        "departamento": cached["departamento"],
    }
    return patch, "ok"


# ---------------------------------------------------------------------------
# Portafolio.co scraping helpers
# ---------------------------------------------------------------------------

# Palabras vacías que portafolio.co omite en el slug
# IMPORTANTE: NO se eliminan formas legales (SAS, LTDA) — portafolio las incluye sin puntos
_STOP_PORTAFOLIO = {
    "y", "de", "del", "la", "el", "los", "las",
    "un", "una", "e", "en", "a", "o", "u", "no",
}
_PORTAFOLIO_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def _slug_portafolio(nombre: str) -> str:
    """
    Convierte razon_social al slug de URL de empresas.portafolio.co.
    Regla clave: los puntos se eliminan sin espacio (S.A.S. → SAS),
    los demás chars especiales se reemplazan por espacio.
    """
    n = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    # Puntos y comas → vacío (S.A.S. → SAS, no S A S)
    n = re.sub(r"[.,]", "", n)
    # Resto de chars especiales → espacio
    n = re.sub(r"[^A-Za-z0-9\s]", " ", n)
    # Filtrar stopwords, convertir a mayúsculas
    tokens = [
        t.upper() for t in n.split()
        if t.lower() not in _STOP_PORTAFOLIO and len(t) > 0
    ]
    slug = "-".join(tokens)
    return re.sub(r"-+", "-", slug).strip("-")


async def _scrape_portafolio_telefono(
    client: httpx.AsyncClient, razon_social: str
) -> str | None:
    """
    Construye la URL de empresas.portafolio.co desde razon_social,
    hace GET y extrae el teléfono del campo itemprop="telephone".
    Devuelve el número como string de solo dígitos, o None si no lo encuentra.
    """
    slug = _slug_portafolio(razon_social)
    if not slug:
        return None

    url = f"https://empresas.portafolio.co/{slug}.html"
    try:
        r = await client.get(
            url,
            headers={"User-Agent": _PORTAFOLIO_UA},
            timeout=15.0,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return None
        # Extraer <span itemprop="telephone">XXXXXXXXXX</span>
        m = re.search(
            r'<span\s+itemprop=["\']telephone["\']>\s*([\d\s\-\+\(\)]+?)\s*</span>',
            r.text,
        )
        if m:
            digits = re.sub(r"[^\d]", "", m.group(1))
            return digits if len(digits) >= 7 else None
    except Exception:
        pass
    return None


def _get_env() -> tuple[str, str, str]:
    """Retorna (maps_key, supabase_url, supabase_key) desde env o settings."""
    maps_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    sb_url = os.environ.get("SUPABASE_URL", "") or settings.supabase_url
    # Acepta SUPABASE_SERVICE_KEY o SUPABASE_KEY (docker-compose usa el segundo)
    sb_key = (
        os.environ.get("SUPABASE_SERVICE_KEY", "")
        or os.environ.get("SUPABASE_KEY", "")
        or settings.supabase_key
    )
    return maps_key, sb_url, sb_key


@router.post("/enriquecer-google-maps")
async def enriquecer_google_maps(
    stream: bool = Query(True, description="true=SSE en tiempo real, false=JSON al finalizar"),
    full_refresh: bool = Query(False, description="true=reprocesa ciudades ya geocodificadas"),
):
    """
    Geocodifica TODAS las ferreterías agrupando por ciudad única del CSV.
    Un solo PATCH a Supabase por ciudad → ~1000 llamadas en vez de 133K.
    Tiempo estimado: 5-15 minutos para todo el dataset.
    """
    from app.routers.csv_processor import get_dataframe

    _, sb_url, sb_key = _get_env()
    if not sb_url or not sb_key:
        return JSONResponse({"error": "SUPABASE_URL / SUPABASE_SERVICE_KEY no configuradas"}, status_code=503)

    sb_write_headers = {
        "apikey": sb_key,
        "Authorization": f"Bearer {sb_key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }

    async def _run() -> AsyncGenerator[str, None]:
        geocodificados = 0
        fallidos = 0
        razones: dict[str, int] = {}

        def sse(data: dict) -> str:
            return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

        # Cámaras únicas del CSV (ciudad/depto vienen vacíos; camara_comercio tiene el valor)
        try:
            df = get_dataframe()
        except Exception as e:
            yield sse({"estado": "error", "error": f"No se pudo leer el CSV: {e}"})
            return

        if "camara_comercio" not in df.columns:
            yield sse({"estado": "error", "error": "El CSV no tiene columna camara_comercio"})
            return

        camaras_unicas = df["camara_comercio"].dropna().unique().tolist()
        total = len(camaras_unicas)
        yield sse({"estado": "iniciando", "total": total,
                   "mensaje": f"{total} cámaras de comercio únicas"})

        async with httpx.AsyncClient() as client:
            for i, camara in enumerate(camaras_unicas):
                camara = (camara or "").strip()
                if not camara:
                    fallidos += 1
                    razones["sin_camara"] = razones.get("sin_camara", 0) + 1
                    continue

                # 1. Geocodificar — primero _CAMARAS (instantáneo), luego Nominatim
                hint = _hint_camara(camara)
                if hint:
                    geo = hint
                else:
                    # Normalizar nombre de cámara para Nominatim
                    query = f"{camara.title()}, Colombia"
                    try:
                        resp = await client.get(
                            "https://nominatim.openstreetmap.org/search",
                            params={"q": query, "format": "json", "limit": 1,
                                    "countrycodes": "co", "addressdetails": 1},
                            headers={"User-Agent": _NOMINATIM_UA},
                            timeout=15.0,
                        )
                        results = resp.json()
                    except Exception:
                        fallidos += 1
                        razones["error_red"] = razones.get("error_red", 0) + 1
                        await asyncio.sleep(1.1)
                        continue

                    await asyncio.sleep(1.1)

                    if not results or "Colombia" not in results[0].get("display_name", ""):
                        fallidos += 1
                        razones["ZERO_RESULTS"] = razones.get("ZERO_RESULTS", 0) + 1
                        continue

                    best = results[0]
                    addr = best.get("address", {})
                    geo = {
                        "lat": float(best["lat"]),
                        "lng": float(best["lon"]),
                        "ciudad": (addr.get("city") or addr.get("town") or
                                   addr.get("village") or addr.get("municipality") or camara.title()),
                        "departamento": addr.get("state") or "",
                    }

                # 2. Bulk PATCH: actualiza TODOS los registros de esa cámara de una vez
                patch_data = {
                    "geocodificado": True,
                    "lat": geo["lat"],
                    "lng": geo["lng"],
                    "direccion": f"{geo['ciudad']}, {geo['departamento']}, Colombia",
                    "ciudad": geo["ciudad"],
                    "departamento": geo["departamento"],
                }
                params = {"camara_comercio": f"eq.{camara}"}
                if not full_refresh:
                    params["geocodificado"] = "eq.false"
                try:
                    await client.patch(
                        f"{sb_url}/rest/v1/ferreterias",
                        params=params,
                        headers=sb_write_headers,
                        json=patch_data,
                        timeout=60.0,
                    )
                    geocodificados += 1
                except Exception:
                    fallidos += 1
                    razones["error_patch"] = razones.get("error_patch", 0) + 1
                    continue

                procesados = i + 1
                if procesados % 5 == 0 or procesados == total:
                    yield sse({
                        "estado": "progreso",
                        "procesados": procesados,
                        "total": total,
                        "enriquecidos": geocodificados,
                        "fallidos": fallidos,
                        "pct": round(procesados / total * 100, 1),
                        "razones": razones,
                        "ciudad_actual": geo.get("ciudad", camara) if hint or True else camara,
                    })

        yield sse({
            "estado": "completado",
            "enriquecidos": geocodificados,
            "fallidos": fallidos,
            "total": total,
            "razones": razones,
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


@router.get("/debug-maps")
async def debug_maps(q: str = Query("Bogota, Bogota D.C., Colombia")):
    """Prueba Nominatim directamente y devuelve la respuesta cruda."""
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": q, "format": "json", "limit": 1, "countrycodes": "co", "addressdetails": 1},
                headers={"User-Agent": _NOMINATIM_UA},
                timeout=15.0,
            )
            data = resp.json()
        except Exception as e:
            return {"error": str(e)}
    return {"query": q, "nominatim_response": data}


@router.get("/estado-enriquecimiento")
async def estado_enriquecimiento():
    """Resumen del estado de geocodificación en Supabase."""
    _, sb_url, sb_key = _get_env()
    if not sb_url or not sb_key:
        return JSONResponse({"error": "Supabase no configurado"}, status_code=503)

    headers = {"apikey": sb_key, "Authorization": f"Bearer {sb_key}"}
    async with httpx.AsyncClient() as client:
        try:
            # Total
            r_total = await client.get(
                f"{sb_url}/rest/v1/ferreterias?select=id&limit=1",
                headers={**headers, "Prefer": "count=exact"},
                timeout=15.0,
            )
            total = int(r_total.headers.get("content-range", "0/0").split("/")[-1])

            # Geocodificados
            r_geo = await client.get(
                f"{sb_url}/rest/v1/ferreterias?select=id&geocodificado=eq.true&limit=1",
                headers={**headers, "Prefer": "count=exact"},
                timeout=15.0,
            )
            geocodificados = int(r_geo.headers.get("content-range", "0/0").split("/")[-1])
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=503)

    pendientes = total - geocodificados
    return {
        "total": total,
        "geocodificados": geocodificados,
        "pendientes": pendientes,
        "pct_completado": round(geocodificados / total * 100, 1) if total else 0,
    }


@router.post("/cargar-supabase")
async def cargar_supabase(
    stream: bool = Query(True, description="true=SSE, false=JSON al finalizar"),
    batch_size: int = Query(500, ge=50, le=2000, description="Registros por lote"),
):
    """
    Carga el CSV completo a Supabase en lotes.
    Lee el DataFrame ya procesado en memoria (get_dataframe) y hace upsert
    por razon_social ignorando duplicados.
    """
    import numpy as np
    from app.routers.csv_processor import get_dataframe

    _, sb_url, sb_key = _get_env()
    if not sb_url or not sb_key:
        return JSONResponse({"error": "SUPABASE_URL / SUPABASE_SERVICE_KEY no configuradas"}, status_code=503)

    sb_headers = {
        "apikey": sb_key,
        "Authorization": f"Bearer {sb_key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=ignore-duplicates,return=representation",
    }

    # Columnas del nuevo esquema Supabase
    _COLS = [
        "camara_comercio", "razon_social", "nit", "ciiu",
        "estado_matricula", "fecha_matricula", "fecha_renovacion",
        "representante_legal", "direccion", "ciudad", "departamento",
        "probabilidad", "lat", "lng", "estado_legal", "num_fuentes",
        "telefono", "email", "website", "estado_info", "estado_actividad",
        "geocodificado", "google_place_id",
    ]

    # Mapeo de columnas CSV con nombres especiales al esquema Supabase
    _CSV_MAP = {
        "Probabilidad venta_consumo Cemento": "probabilidad",
        "Departamento": "departamento",
        "formatted_address": "direccion",   # columna legacy del CSV → nuevo nombre
    }

    def _row_to_dict(row: dict) -> dict:
        # Aplica mapeo de nombres de columnas CSV → Supabase
        mapped = dict(row)
        for csv_col, sb_col in _CSV_MAP.items():
            if csv_col in mapped and sb_col not in mapped:
                mapped[sb_col] = mapped[csv_col]
        out = {}
        for col in _COLS:
            v = mapped.get(col)
            if v is None or (isinstance(v, float) and np.isnan(v)):
                out[col] = None
            else:
                out[col] = v
        # Columnas numéricas (probabilidad es texto ALTA/MEDIA/BAJA — excluida)
        for num_col in ("lat", "lng", "num_fuentes"):
            if out.get(num_col) is not None:
                try:
                    out[num_col] = float(out[num_col])
                except (ValueError, TypeError):
                    out[num_col] = None
        # geocodificado como bool
        geo = out.get("geocodificado")
        if geo is not None:
            out["geocodificado"] = str(geo).lower() in ("true", "1", "yes")
        return out

    async def _run() -> AsyncGenerator[str, None]:
        def sse(data: dict) -> str:
            return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

        try:
            df = get_dataframe()
        except Exception as e:
            yield sse({"estado": "error", "error": f"No se pudo leer el CSV: {e}"})
            return

        records = df.to_dict("records")
        total = len(records)
        yield sse({"estado": "iniciando", "total": total, "batch_size": batch_size})

        nuevos = 0
        duplicados = 0
        procesados = 0

        async with httpx.AsyncClient() as client:
            for start in range(0, total, batch_size):
                lote = [_row_to_dict(r) for r in records[start: start + batch_size]]
                try:
                    resp = await client.post(
                        f"{sb_url}/rest/v1/ferreterias",
                        headers=sb_headers,
                        json=lote,
                        timeout=60.0,
                    )
                    insertados = len(resp.json()) if resp.status_code in (200, 201) and resp.text.startswith("[") else 0
                    lote_nuevos = insertados
                    lote_dup = len(lote) - insertados
                except Exception as e:
                    lote_nuevos = 0
                    lote_dup = len(lote)

                nuevos += lote_nuevos
                duplicados += lote_dup
                procesados += len(lote)

                yield sse({
                    "estado": "progreso",
                    "procesados": procesados,
                    "total": total,
                    "nuevos": nuevos,
                    "duplicados": duplicados,
                    "pct": round(procesados / total * 100, 1),
                })

                await asyncio.sleep(0.1)

        yield sse({
            "estado": "completado",
            "total": total,
            "nuevos": nuevos,
            "duplicados": duplicados,
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


@router.post("/scraping-portafolio")
async def scraping_portafolio(
    limit: int = Query(100, ge=1, le=2000, description="Registros a procesar"),
    offset: int = Query(0, ge=0, description="Offset en Supabase"),
    stream: bool = Query(True, description="true=SSE, false=JSON al finalizar"),
    solo_sin_telefono: bool = Query(True, description="true=procesa solo los que no tienen teléfono"),
):
    """
    Scraping de empresas.portafolio.co para extraer el teléfono de cada ferretería.
    Construye la URL desde razon_social, hace GET y extrae <span itemprop='telephone'>.
    Actualiza Supabase con los teléfonos encontrados.
    """
    _, sb_url, sb_key = _get_env()
    if not sb_url or not sb_key:
        return JSONResponse({"error": "SUPABASE_URL / SUPABASE_SERVICE_KEY no configuradas"}, status_code=503)

    sb_read_headers = {
        "apikey": sb_key,
        "Authorization": f"Bearer {sb_key}",
    }
    sb_write_headers = {
        **sb_read_headers,
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }

    async def _run() -> AsyncGenerator[str, None]:
        encontrados = 0
        no_encontrados = 0
        total = 0

        def sse(data: dict) -> str:
            return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

        async with httpx.AsyncClient() as client:
            filtro = "&telefono=is.null" if solo_sin_telefono else ""
            url = (
                f"{sb_url}/rest/v1/ferreterias"
                f"?select=id,razon_social,num_fuentes"
                f"{filtro}&order=id.asc&limit={limit}&offset={offset}"
            )
            try:
                r = await client.get(url, headers=sb_read_headers, timeout=30.0)
                records = r.json()
            except Exception as e:
                yield sse({"estado": "error", "error": str(e)})
                return

            if not isinstance(records, list) or not records:
                yield sse({"estado": "sin_pendientes", "encontrados": 0, "no_encontrados": 0, "total": 0})
                return

            total = len(records)
            yield sse({"estado": "iniciando", "total": total, "offset": offset})

            for i, record in enumerate(records):
                rid = record.get("id")
                razon = (record.get("razon_social") or "").strip()

                tel = await _scrape_portafolio_telefono(client, razon)

                if tel:
                    try:
                        num_f = record.get("num_fuentes")
                        num_f = int(float(num_f)) if num_f is not None else 1
                        pr = await client.patch(
                            f"{sb_url}/rest/v1/ferreterias?id=eq.{rid}",
                            headers=sb_write_headers,
                            json={"telefono": tel, "num_fuentes": num_f + 1},
                            timeout=15.0,
                        )
                        if pr.status_code in (200, 201, 204):
                            encontrados += 1
                        else:
                            no_encontrados += 1
                            yield sse({"estado": "debug_patch", "status": pr.status_code,
                                       "body": pr.text[:300], "id": rid})
                    except Exception as exc:
                        no_encontrados += 1
                        yield sse({"estado": "debug_patch", "error": str(exc), "id": rid})
                else:
                    no_encontrados += 1

                if (i + 1) % 10 == 0 or (i + 1) == total:
                    yield sse({
                        "estado": "progreso",
                        "procesados": i + 1,
                        "total": total,
                        "encontrados": encontrados,
                        "no_encontrados": no_encontrados,
                        "pct": round((i + 1) / total * 100, 1),
                        "ultimo": razon[:40] if razon else "",
                    })

                # Pausa para no saturar portafolio.co (~2 req/s)
                await asyncio.sleep(0.5)

        yield sse({
            "estado": "completado",
            "encontrados": encontrados,
            "no_encontrados": no_encontrados,
            "total": total,
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


@router.post("/migrar-supabase")
async def migrar_supabase(
    stream: bool = Query(True, description="true=SSE, false=JSON al finalizar"),
    batch_size: int = Query(500, ge=50, le=2000),
):
    """
    Vacía la tabla ferreterias en Supabase y recarga el CSV completo con el nuevo esquema.
    El DROP+CREATE de la tabla debe hacerse manualmente en el SQL Editor de Supabase.
    """
    import numpy as np
    from app.routers.csv_processor import get_dataframe

    _, sb_url, sb_key = _get_env()
    if not sb_url or not sb_key:
        return JSONResponse({"error": "SUPABASE_URL / SUPABASE_SERVICE_KEY no configuradas"}, status_code=503)

    sb_delete_headers = {
        "apikey": sb_key,
        "Authorization": f"Bearer {sb_key}",
        "Prefer": "return=minimal",
    }
    sb_insert_headers = {
        **sb_delete_headers,
        "Content-Type": "application/json",
        "Prefer": "resolution=ignore-duplicates,return=representation",
    }

    _COLS_MIG = [
        "camara_comercio", "razon_social", "nit", "ciiu",
        "estado_matricula", "fecha_matricula", "fecha_renovacion",
        "representante_legal", "direccion", "ciudad", "departamento",
        "probabilidad", "lat", "lng", "estado_legal", "num_fuentes",
        "telefono", "email", "website", "estado_info", "estado_actividad",
        "geocodificado", "google_place_id",
    ]
    _CSV_MAP_MIG = {
        "Probabilidad venta_consumo Cemento": "probabilidad",
        "Departamento": "departamento",
        "formatted_address": "direccion",
    }

    def _row(row: dict) -> dict:
        mapped = dict(row)
        for csv_col, sb_col in _CSV_MAP_MIG.items():
            if csv_col in mapped and sb_col not in mapped:
                mapped[sb_col] = mapped[csv_col]
        out = {}
        for col in _COLS_MIG:
            v = mapped.get(col)
            if v is None or (isinstance(v, float) and np.isnan(v)):
                out[col] = None
            else:
                out[col] = v
        for num_col in ("lat", "lng", "num_fuentes"):
            if out.get(num_col) is not None:
                try:
                    out[num_col] = float(out[num_col])
                except (ValueError, TypeError):
                    out[num_col] = None
        geo = out.get("geocodificado")
        if geo is not None:
            out["geocodificado"] = str(geo).lower() in ("true", "1", "yes")
        return out

    async def _run() -> AsyncGenerator[str, None]:
        def sse(d: dict) -> str:
            return f"data: {json.dumps(d, ensure_ascii=False)}\n\n"

        async with httpx.AsyncClient() as client:
            # 1. Borrar todos los registros existentes
            yield sse({"estado": "borrando", "msg": "Eliminando registros existentes…"})
            try:
                await client.delete(
                    f"{sb_url}/rest/v1/ferreterias?id=not.is.null",
                    headers=sb_delete_headers,
                    timeout=60.0,
                )
            except Exception as e:
                yield sse({"estado": "error", "error": f"Error al borrar: {e}"})
                return

            # 2. Cargar CSV
            try:
                df = get_dataframe()
            except Exception as e:
                yield sse({"estado": "error", "error": f"No se pudo leer el CSV: {e}"})
                return

            records = df.to_dict("records")
            total = len(records)
            yield sse({"estado": "cargando", "total": total, "procesados": 0})

            nuevos = 0
            procesados = 0
            for start in range(0, total, batch_size):
                lote = [_row(r) for r in records[start: start + batch_size]]
                try:
                    resp = await client.post(
                        f"{sb_url}/rest/v1/ferreterias",
                        headers=sb_insert_headers,
                        json=lote,
                        timeout=60.0,
                    )
                    insertados = len(resp.json()) if resp.status_code in (200, 201) and resp.text.startswith("[") else 0
                    nuevos += insertados
                except Exception:
                    pass
                procesados += len(lote)
                yield sse({
                    "estado": "cargando",
                    "procesados": procesados,
                    "total": total,
                    "pct": round(procesados / total * 100, 1),
                })
                await asyncio.sleep(0.05)

        yield sse({"estado": "completado", "total": total, "nuevos": nuevos})

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


@router.get("/debug-portafolio")
async def debug_portafolio(razon: str = Query("FERRETERIA Y DEPOSITO LA H S.A.S.")):
    """Diagnóstico de portafolio.co: muestra slug, URL, status HTTP y teléfono encontrado."""
    slug = _slug_portafolio(razon)
    url = f"https://empresas.portafolio.co/{slug}.html"
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(
                url, headers={"User-Agent": _PORTAFOLIO_UA},
                timeout=15.0, follow_redirects=True,
            )
            status = r.status_code
            m = re.search(
                r'<span\s+itemprop=["\']telephone["\']>\s*([\d\s\-\+\(\)]+?)\s*</span>',
                r.text,
            )
            telefono = re.sub(r"[^\d]", "", m.group(1)) if m else None
        except Exception as e:
            return {"razon": razon, "slug": slug, "url": url, "error": str(e)}
    return {"razon": razon, "slug": slug, "url": url, "http_status": status, "telefono": telefono}
