from pydantic import BaseModel
from typing import Optional, List


class Ferreteria(BaseModel):
    camara_comercio: Optional[str] = None
    razon_social: str
    nit: Optional[str] = None
    organizacion_juridica: Optional[str] = None
    estado_matricula: Optional[str] = None
    fecha_matricula: Optional[str] = None
    fecha_renovacion: Optional[str] = None
    representante_legal: Optional[str] = None
    nombre_comercial: Optional[str] = None
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    departamento: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    estado_info: str       # "Completa" | "Incompleta"
    estado_legal: str      # "Legalmente constituida" | "No legalmente constituida"
    estado_actividad: str  # "Pendiente"
    fuente: str = "camara_comercio"


class ProcesarCSVRequest(BaseModel):
    offset: int = 0
    limit: int = 500
    filtro_ciudad: Optional[str] = None
    filtro_departamento: Optional[str] = None


class ProcesarCSVResponse(BaseModel):
    total_registros: int
    registros_en_pagina: int
    offset: int
    limit: int
    tiene_mas: bool
    data: List[Ferreteria]


class ConsultaRequest(BaseModel):
    ciudad: Optional[str] = None
    departamento: Optional[str] = None
    estado_info: Optional[str] = None
    estado_legal: Optional[str] = None
    camara_comercio: Optional[str] = None
    busqueda: Optional[str] = None  # búsqueda libre por nombre
    limit: int = 50
    offset: int = 0


class ConsultaResponse(BaseModel):
    total_encontrados: int
    registros_en_pagina: int
    data: List[Ferreteria]


class EstadisticasResponse(BaseModel):
    total_registros: int
    estado_info: dict
    estado_legal: dict
    por_departamento: dict
    por_camara_comercio: dict
    con_telefono: int
    con_email: int
    con_nit: int


class HealthResponse(BaseModel):
    status: str
    csv_cargado: bool
    total_registros: int
    csv_path: str
