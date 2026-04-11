"""
Ferreterías Colombia API
Servicio Python (FastAPI + pandas) para el sistema de censo digital de Argos.

Endpoints principales:
  GET  /health          → Estado del servicio y del CSV
  GET  /estadisticas    → Resumen del dataset (para el AI Agent)
  POST /procesar-csv    → Página de registros limpios y clasificados
  GET  /consultar       → Búsqueda flexible (modo pregunta del agente)
  POST /reload-csv      → Recarga el CSV sin reiniciar Docker
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import HealthResponse
from app.routers import csv_processor, estadisticas, dashboard, sin_ubicacion


# ---------------------------------------------------------------------------
# Lifespan: pre-carga el CSV al arrancar (warm-up)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Carga el CSV en memoria al iniciar el servidor para que el primer request sea rápido."""
    try:
        df = csv_processor.get_dataframe()
        print(f"✓ CSV cargado: {len(df):,} registros desde {settings.csv_path}")
    except Exception as e:
        print(f"⚠ No se pudo pre-cargar el CSV: {e}")
        print("  El servicio arranca igual; el CSV se cargará al primer request.")
    yield
    # (cleanup al apagar — no necesario aquí)


# ---------------------------------------------------------------------------
# Aplicación FastAPI
# ---------------------------------------------------------------------------

app = FastAPI(
    title       = settings.api_title,
    version     = settings.api_version,
    description = settings.api_description,
    lifespan    = lifespan,
    docs_url    = "/docs",      # Swagger UI en http://localhost:8000/docs
    redoc_url   = "/redoc",
)

# CORS: permite llamadas desde n8n (misma red Docker) y desde el navegador si se expone el puerto
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(dashboard.router)   # debe ir primero: maneja GET /
app.include_router(csv_processor.router)
app.include_router(estadisticas.router)
app.include_router(sin_ubicacion.router)


# ---------------------------------------------------------------------------
# Endpoints raíz
# ---------------------------------------------------------------------------


@app.get("/health", response_model=HealthResponse, tags=["Sistema"])
async def health():
    """
    Verificación de estado del servicio.
    Docker usa este endpoint para el healthcheck.
    n8n puede llamarlo para confirmar que la API está disponible antes de procesar.
    """
    csv_cargado    = csv_processor._df_cache is not None
    total_registros = len(csv_processor._df_cache) if csv_cargado else 0

    return HealthResponse(
        status          = "ok",
        csv_cargado     = csv_cargado,
        total_registros = total_registros,
        csv_path        = settings.csv_path,
    )
