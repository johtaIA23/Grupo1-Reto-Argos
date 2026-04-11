-- ============================================================
-- PASO 5: Columnas de clasificación + restricciones UNIQUE
-- Ejecutar en: Supabase Dashboard → SQL Editor
-- IMPORTANTE: Ejecutar esto ANTES de relanzar el workflow 01
-- ============================================================

-- Limpiar datos del intento anterior (si hubo alguno)
-- Si la tabla está vacía, estas líneas no hacen nada
TRUNCATE TABLE public.ferreterias_embeddings;
TRUNCATE TABLE public.ferreterias RESTART IDENTITY CASCADE;

-- --------------------------------------------------------
-- 1. Nuevas columnas de clasificación
-- --------------------------------------------------------
ALTER TABLE public.ferreterias
  ADD COLUMN IF NOT EXISTS estado_info      TEXT DEFAULT 'Incompleta',
  ADD COLUMN IF NOT EXISTS estado_legal     TEXT DEFAULT 'No legalmente constituida',
  ADD COLUMN IF NOT EXISTS estado_actividad TEXT DEFAULT 'Pendiente';

-- Índices para filtros rápidos por estado
CREATE INDEX IF NOT EXISTS idx_ferreterias_estado_info
  ON public.ferreterias (estado_info);

CREATE INDEX IF NOT EXISTS idx_ferreterias_estado_legal
  ON public.ferreterias (estado_legal);

CREATE INDEX IF NOT EXISTS idx_ferreterias_estado_actividad
  ON public.ferreterias (estado_actividad);

-- --------------------------------------------------------
-- 2. Restricciones UNIQUE para deduplicación automática
-- La BD rechaza duplicados automáticamente (ON CONFLICT DO NOTHING)
-- sin necesidad de consultar antes de insertar.
-- --------------------------------------------------------

-- Por NIT (cubre ~95% de los registros de cámaras de comercio)
CREATE UNIQUE INDEX IF NOT EXISTS ferreterias_nit_unique
  ON public.ferreterias (nit)
  WHERE nit IS NOT NULL AND nit <> '';

-- Por Google Place ID (cubre todos los registros de Google Maps)
CREATE UNIQUE INDEX IF NOT EXISTS ferreterias_place_id_unique
  ON public.ferreterias (google_place_id)
  WHERE google_place_id IS NOT NULL AND google_place_id <> '';

-- Por nombre normalizado (registros sin NIT ni Place ID - casos borde)
CREATE UNIQUE INDEX IF NOT EXISTS ferreterias_nombre_fallback_unique
  ON public.ferreterias (upper(trim(razon_social)))
  WHERE (nit IS NULL OR nit = '') AND (google_place_id IS NULL OR google_place_id = '');
