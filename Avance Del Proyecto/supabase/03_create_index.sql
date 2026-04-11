-- ============================================================
-- PASO 3: Crear índice vectorial IVFFlat para búsqueda semántica
-- ⚠️  IMPORTANTE: Ejecutar este script DESPUÉS de cargar el CSV
--     El índice IVFFlat necesita al menos 1000 filas para ser útil.
--     Con menos filas, PostgreSQL hará un seq scan igualmente.
-- ============================================================

-- Índice IVFFlat con similitud coseno
-- lists=100 es adecuado para ~1M vectores. Para 48k registros,
-- un valor de lists=50 también es razonable.
CREATE INDEX IF NOT EXISTS idx_embeddings_ivfflat
ON public.ferreterias_embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- ============================================================
-- OPCIONAL: Ajuste de parámetro ivfflat.probes para sesión
-- Un valor mayor = más precisión, más lento (default: 1)
-- Ejecutar en la sesión donde se hacen las búsquedas:
-- ============================================================
-- SET ivfflat.probes = 10;
