-- ========================================
-- MIGRACIÓN: Agregar campos extendidos a itinerario_detalles
-- ========================================
-- Este script agrega las columnas necesarias para el contenido extenso
-- Ejecutar en SQLite Browser o pgAdmin
Select * from itinerario_detalles;
-- 1. Agregar columna historia_contextual (texto largo)
ALTER TABLE itinerario_detalles 
ADD COLUMN historia_contextual TEXT;

-- 2. Agregar columna datos_curiosos (JSON array)
ALTER TABLE itinerario_detalles 
ADD COLUMN datos_curiosos TEXT;

-- 3. Agregar columna que_observar (JSON array)
ALTER TABLE itinerario_detalles 
ADD COLUMN que_observar TEXT;

-- 4. Agregar columna puntos_clave (JSON array) - legacy
ALTER TABLE itinerario_detalles
ADD COLUMN puntos_clave TEXT;



-- Función que se ejecuta automáticamente
CREATE OR REPLACE FUNCTION registrar_visita_automaticamente()
RETURNS TRIGGER AS $$
BEGIN
    -- Cuando se crea un itinerario
    IF (TG_OP = 'INSERT') THEN
        INSERT INTO historial_visitas (
            visitante_id,
            itinerario_id,
            fecha_visita,
            hora_entrada,
            areas_visitadas,
            hora_pico
        )
        SELECT
            p.visitante_id,
            NEW.id,
            DATE(NEW.fecha_generacion),
            NEW.fecha_generacion,
            (SELECT COUNT(*) FROM itinerario_detalles WHERE itinerario_id = NEW.id),
            (
                EXTRACT(HOUR FROM NEW.fecha_generacion) BETWEEN 10 AND 12
                OR
                EXTRACT(HOUR FROM NEW.fecha_generacion) BETWEEN 14 AND 17
            )
        FROM perfiles p
        WHERE p.id = NEW.perfil_id;
    END IF;
    
    -- Cuando se completa un itinerario
    IF (TG_OP = 'UPDATE' AND NEW.estado = 'completado' AND OLD.estado != 'completado') THEN
        UPDATE historial_visitas
        SET 
            hora_salida = CURRENT_TIMESTAMP,
            duracion_total = NEW.duracion_total,
            areas_completadas = (SELECT COUNT(*) FROM itinerario_detalles WHERE itinerario_id = NEW.id),
            satisfaccion_general = NEW.puntuacion
        WHERE itinerario_id = NEW.id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Crear trigger
DROP TRIGGER IF EXISTS trigger_registrar_visita ON itinerarios;

CREATE TRIGGER trigger_registrar_visita
    AFTER INSERT OR UPDATE ON itinerarios
    FOR EACH ROW
    EXECUTE FUNCTION registrar_visita_automaticamente();

SELECT 'Trigger creado exitosamente' AS resultado;








-- ============================================
-- MIGRACIÓN: tipo_entrada y acompañantes
-- DE: visitantes → A: itinerarios
-- ============================================

BEGIN;

-- ============================================
-- PASO 1: Agregar columnas a itinerarios
-- ============================================

ALTER TABLE itinerarios 
    ADD COLUMN tipo_entrada VARCHAR(50) 
        CHECK (tipo_entrada IN ('estudiante', 'adulto_mayor', 'grupo', 'individual')),
    ADD COLUMN acompañantes INTEGER DEFAULT 0 CHECK (acompañantes >= 0);

-- ============================================
-- PASO 2: Migrar datos existentes
-- ============================================
-- Copiar los valores de visitantes a sus itinerarios

UPDATE itinerarios i
SET 
    tipo_entrada = v.tipo_entrada,
    acompañantes = v.acompanantes
FROM perfiles p
JOIN visitantes v ON p.visitante_id = v.id
WHERE i.perfil_id = p.id
  AND v.tipo_entrada IS NOT NULL;  -- Solo si el visitante tiene datos

-- ============================================
-- PASO 3: Verificar migración
-- ============================================

-- Ver cuántos itinerarios tienen datos
SELECT 
    COUNT(*) AS total_itinerarios,
    COUNT(tipo_entrada) AS con_tipo_entrada,
    COUNT(acompañantes) AS con_acompanantes
FROM itinerarios;

-- Ver distribución de tipo_entrada
SELECT 
    tipo_entrada,
    COUNT(*) AS cantidad
FROM itinerarios
WHERE tipo_entrada IS NOT NULL
GROUP BY tipo_entrada;

-- Ver estadísticas de acompañantes
SELECT 
    MIN(acompañantes) AS min_acompañantes,
    MAX(acompañantes) AS max_acompañantes,
    AVG(acompañantes) AS promedio_acompañantes
FROM itinerarios;

-- ============================================
-- PASO 4 (OPCIONAL): Eliminar campos de visitantes
-- ============================================
-- ⚠️ SOLO SI ESTÁS SEGURO - ESTO ES IRREVERSIBLE
-- Descomenta las siguientes líneas para eliminar los campos:

/*
ALTER TABLE visitantes 
    DROP COLUMN tipo_entrada,
    DROP COLUMN acompanantes;

SELECT 'Columnas eliminadas de visitantes' AS resultado;
*/

-- Por ahora, las dejamos en visitantes como "valores por defecto"
-- para nuevos registros, pero NO las usaremos más
SELECT 'Migración completada - Columnas agregadas a itinerarios' AS resultado;

COMMIT;



-- Ver algunos registros de ejemplo
SELECT 
    id,
    titulo,
    tipo_entrada,
    acompañantes,
    estado
FROM itinerarios
LIMIT 5;