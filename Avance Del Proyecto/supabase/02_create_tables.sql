-- ============================================================
-- PASO 2: Crear tablas del sistema de censo digital
-- Ejecutar en: Supabase Dashboard → SQL Editor
-- Requisito previo: haber ejecutado 01_enable_pgvector.sql
-- ============================================================

-- --------------------------------------------------------
-- TABLA PRINCIPAL: ferreterias
-- Registro maestro de cada ferretería en Colombia
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.ferreterias (
    -- Identificador único
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Datos de cámara de comercio
    camara_comercio       TEXT,
    razon_social          TEXT NOT NULL,
    nit                   TEXT,
    organizacion_juridica TEXT,
    estado_matricula      TEXT DEFAULT 'ACTIVA',
    fecha_matricula       DATE,
    fecha_renovacion      DATE,
    representante_legal   TEXT,

    -- Datos de contacto y ubicación (se enriquecen desde Google Maps)
    nombre_comercial      TEXT,
    direccion             TEXT,
    ciudad                TEXT,
    departamento          TEXT,
    telefono              TEXT,
    whatsapp              TEXT,
    email                 TEXT,
    website               TEXT,

    -- Geolocalización
    lat                   DOUBLE PRECISION,
    lng                   DOUBLE PRECISION,
    google_place_id       TEXT,
    google_rating         NUMERIC(2, 1),

    -- Metadatos del sistema
    fuente                TEXT DEFAULT 'camara_comercio',
    fecha_creacion        TIMESTAMPTZ DEFAULT NOW(),
    fecha_actualizacion   TIMESTAMPTZ DEFAULT NOW(),
    ciclo_actualizacion   INTEGER DEFAULT 1
);

-- Índices útiles para la tabla ferreterias
CREATE INDEX IF NOT EXISTS idx_ferreterias_razon_social ON public.ferreterias (razon_social);
CREATE INDEX IF NOT EXISTS idx_ferreterias_nit ON public.ferreterias (nit);
CREATE INDEX IF NOT EXISTS idx_ferreterias_ciudad ON public.ferreterias (ciudad);
CREATE INDEX IF NOT EXISTS idx_ferreterias_camara ON public.ferreterias (camara_comercio);

-- Trigger para actualizar fecha_actualizacion automáticamente
CREATE OR REPLACE FUNCTION update_fecha_actualizacion()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_actualizacion = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_ferreterias_updated
    BEFORE UPDATE ON public.ferreterias
    FOR EACH ROW EXECUTE FUNCTION update_fecha_actualizacion();


-- --------------------------------------------------------
-- TABLA DE EMBEDDINGS: ferreterias_embeddings
-- Almacena el vector semántico de cada ferretería
-- Se usa para deduplicación por similitud (RAG)
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.ferreterias_embeddings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ferreteria_id   UUID NOT NULL REFERENCES public.ferreterias(id) ON DELETE CASCADE,
    embedding       vector(1536) NOT NULL,   -- OpenAI text-embedding-3-small produce 1536 dimensiones
    texto_fuente    TEXT,                     -- Texto original usado para generar el embedding
    creado_en       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_embeddings_ferreteria_id ON public.ferreterias_embeddings (ferreteria_id);


-- --------------------------------------------------------
-- TABLA DE AUDITORÍA: ciclos_actualizacion
-- Registra cada corrida del sistema (carga CSV o búsqueda Google)
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.ciclos_actualizacion (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    numero_ciclo     INTEGER NOT NULL,
    fecha_inicio     TIMESTAMPTZ DEFAULT NOW(),
    fecha_fin        TIMESTAMPTZ,
    registros_nuevos INTEGER DEFAULT 0,
    duplicados_skip  INTEGER DEFAULT 0,
    estado           TEXT DEFAULT 'en_proceso'
);
