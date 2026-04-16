-- Agrega columna num_fuentes para contabilizar cuántas fuentes aportaron datos a cada registro.
-- 1 = solo CSV inicial
-- 2 = CSV + Google Maps encontró coordenadas
-- 3 = CSV + Maps + Portafolio encontró teléfono/email
-- 4 = CSV + Maps + Portafolio + Einforma encontró algo adicional

ALTER TABLE ferreterias
ADD COLUMN IF NOT EXISTS num_fuentes INTEGER DEFAULT 1;
