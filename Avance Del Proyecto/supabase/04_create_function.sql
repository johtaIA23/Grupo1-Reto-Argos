-- ============================================================
-- PASO 4: Funciones SQL para el sistema de censo
-- Ejecutar en: Supabase Dashboard → SQL Editor
-- ============================================================

-- --------------------------------------------------------
-- FUNCIÓN PRINCIPAL: buscar_similares
-- Busca ferreterías similares usando distancia coseno sobre embeddings.
-- Usada para deduplicación en tiempo real desde n8n.
--
-- Parámetros:
--   query_embedding  : vector(1536) generado por OpenAI
--   umbral_similitud : float entre 0 y 1 (default 0.92 = 92% similitud)
--   limite           : número máximo de resultados (default 5)
--
-- Retorna:
--   ferreteria_id  : UUID de la ferretería encontrada
--   razon_social   : nombre legal de la ferretería
--   ciudad         : ciudad donde está ubicada
--   similitud      : score de similitud (1.0 = idéntico)
-- --------------------------------------------------------
CREATE OR REPLACE FUNCTION public.buscar_similares(
    query_embedding   vector(1536),
    umbral_similitud  FLOAT DEFAULT 0.92,
    limite            INT   DEFAULT 5
)
RETURNS TABLE (
    ferreteria_id  UUID,
    razon_social   TEXT,
    ciudad         TEXT,
    similitud      FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        f.id                                         AS ferreteria_id,
        f.razon_social,
        f.ciudad,
        1 - (e.embedding <=> query_embedding)::FLOAT AS similitud
    FROM public.ferreterias_embeddings e
    JOIN public.ferreterias f ON f.id = e.ferreteria_id
    WHERE 1 - (e.embedding <=> query_embedding) >= umbral_similitud
    ORDER BY e.embedding <=> query_embedding   -- orden ascendente de distancia = mayor similitud primero
    LIMIT limite;
END;
$$;


-- --------------------------------------------------------
-- FUNCIÓN DE SOPORTE: actualizar_ciclo
-- Incrementa atómicamente los contadores de un ciclo.
-- Llamada desde n8n después de cada batch procesado.
-- --------------------------------------------------------
CREATE OR REPLACE FUNCTION public.actualizar_ciclo(
    p_ciclo_id    UUID,
    p_nuevos      INTEGER DEFAULT 0,
    p_duplicados  INTEGER DEFAULT 0
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE public.ciclos_actualizacion
    SET
        registros_nuevos = registros_nuevos + p_nuevos,
        duplicados_skip  = duplicados_skip  + p_duplicados
    WHERE id = p_ciclo_id;
END;
$$;


-- --------------------------------------------------------
-- FUNCIÓN DE SOPORTE: finalizar_ciclo
-- Marca un ciclo como completado con su fecha de fin.
-- --------------------------------------------------------
CREATE OR REPLACE FUNCTION public.finalizar_ciclo(
    p_ciclo_id UUID
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE public.ciclos_actualizacion
    SET
        fecha_fin = NOW(),
        estado    = 'completado'
    WHERE id = p_ciclo_id;
END;
$$;
