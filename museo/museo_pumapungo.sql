-- ============================================
-- MUSEO PUMAPUNGO - Schema completo
-- Generado desde BD real 2026-03-11
-- Idempotente: seguro de ejecutar multiples veces
-- ============================================

BEGIN;

-- ============================================
-- TABLAS
-- ============================================

CREATE TABLE IF NOT EXISTS visitantes (
    id SERIAL PRIMARY KEY,
    codigo_visita VARCHAR(50) UNIQUE,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100),
    email VARCHAR(150) UNIQUE NOT NULL,
    telefono VARCHAR(20),
    pais_origen VARCHAR(100),
    ciudad_origen VARCHAR(100),
    tipo_visitante VARCHAR(50) CHECK (tipo_visitante IN ('local', 'nacional', 'internacional')),
    fecha_nacimiento DATE,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultima_visita TIMESTAMP,
    total_visitas INTEGER DEFAULT 0,
    activo BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS perfiles (
    id SERIAL PRIMARY KEY,
    visitante_id INTEGER UNIQUE REFERENCES visitantes(id) ON DELETE CASCADE,
    intereses TEXT[],
    tiempo_disponible INTEGER,
    idioma_preferido VARCHAR(10) DEFAULT 'es',
    nivel_detalle VARCHAR(20) CHECK (nivel_detalle IN ('rapido', 'normal', 'profundo')) DEFAULT 'normal',
    incluir_descansos BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS areas (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE,
    nombre VARCHAR(150) NOT NULL,
    descripcion TEXT,
    categoria VARCHAR(50) NOT NULL,
    subcategoria VARCHAR(50),
    tiempo_minimo INTEGER DEFAULT 10,
    tiempo_maximo INTEGER DEFAULT 45,
    capacidad_simultanea INTEGER,
    orden_recomendado INTEGER,
    activa BOOLEAN DEFAULT TRUE,
    requiere_guia BOOLEAN DEFAULT FALSE,
    piso INTEGER DEFAULT 1,
    zona VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS itinerarios (
    id SERIAL PRIMARY KEY,
    perfil_id INTEGER REFERENCES perfiles(id) ON DELETE CASCADE,
    titulo VARCHAR(200),
    descripcion TEXT,
    duracion_total INTEGER,
    estado VARCHAR(20) CHECK (estado IN (
        'generado', 'activo', 'pausado', 'completado', 'cancelado', 'en_proceso'
    )) DEFAULT 'generado',
    fecha_generacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_inicio TIMESTAMP,
    fecha_fin TIMESTAMP,
    puntuacion INTEGER CHECK (puntuacion BETWEEN 1 AND 5),
    modelo_ia_usado VARCHAR(50),
    prompt_usado TEXT,
    respuesta_ia JSONB,
    tipo_entrada VARCHAR(50) CHECK (tipo_entrada IN (
        'estudiante', 'adulto_mayor', 'grupo', 'individual'
    )),
    "acompañantes" INTEGER DEFAULT 0 CHECK ("acompañantes" >= 0)
);

CREATE TABLE IF NOT EXISTS itinerario_detalles (
    id SERIAL PRIMARY KEY,
    itinerario_id INTEGER REFERENCES itinerarios(id) ON DELETE CASCADE,
    area_id INTEGER REFERENCES areas(id),
    orden INTEGER NOT NULL,
    tiempo_sugerido INTEGER,
    tiempo_real INTEGER,
    introduccion TEXT,
    puntos_clave TEXT[],
    recomendacion TEXT,
    visitado BOOLEAN DEFAULT FALSE,
    skip BOOLEAN DEFAULT FALSE,
    hora_inicio TIMESTAMP,
    hora_fin TIMESTAMP,
    historia_contextual TEXT,
    datos_curiosos JSONB,
    que_observar JSONB
);

CREATE TABLE IF NOT EXISTS historial_visitas (
    id SERIAL PRIMARY KEY,
    visitante_id INTEGER REFERENCES visitantes(id),
    itinerario_id INTEGER REFERENCES itinerarios(id),
    fecha_visita DATE DEFAULT CURRENT_DATE,
    hora_entrada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    hora_salida TIMESTAMP,
    duracion_total INTEGER,
    areas_visitadas INTEGER,
    areas_completadas INTEGER,
    satisfaccion_general INTEGER CHECK (satisfaccion_general BETWEEN 1 AND 5),
    hora_pico BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS evaluaciones (
    id SERIAL PRIMARY KEY,
    itinerario_id INTEGER NOT NULL REFERENCES itinerarios(id),
    calificacion_general INTEGER NOT NULL,
    personalizado BOOLEAN NOT NULL,
    buenas_decisiones BOOLEAN NOT NULL,
    acompaniamiento BOOLEAN NOT NULL,
    comprension BOOLEAN NOT NULL,
    relevante BOOLEAN NOT NULL,
    usaria_nuevamente BOOLEAN NOT NULL,
    comentarios TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- INDICES
-- ============================================

CREATE INDEX IF NOT EXISTS idx_visitantes_codigo ON visitantes(codigo_visita);
CREATE INDEX IF NOT EXISTS idx_visitantes_email ON visitantes(email);
CREATE INDEX IF NOT EXISTS idx_visitantes_tipo ON visitantes(tipo_visitante);
CREATE INDEX IF NOT EXISTS idx_perfiles_intereses ON perfiles USING GIN(intereses);
CREATE INDEX IF NOT EXISTS idx_itinerarios_estado ON itinerarios(estado);
CREATE INDEX IF NOT EXISTS idx_itinerarios_fecha ON itinerarios(fecha_generacion);
CREATE INDEX IF NOT EXISTS idx_areas_categoria ON areas(categoria);
CREATE INDEX IF NOT EXISTS idx_areas_activa ON areas(activa) WHERE activa = TRUE;
CREATE INDEX IF NOT EXISTS idx_itinerario_detalles_orden ON itinerario_detalles(itinerario_id, orden);

-- ============================================
-- FUNCIONES
-- ============================================

CREATE OR REPLACE FUNCTION generar_codigo_visita()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.codigo_visita IS NULL THEN
        NEW.codigo_visita := 'PMP-' ||
                            TO_CHAR(CURRENT_DATE, 'YYYYMMDD') || '-' ||
                            LPAD(NEW.id::TEXT, 4, '0');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION actualizar_contador_visitas()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.hora_salida IS NOT NULL AND OLD.hora_salida IS NULL THEN
        UPDATE visitantes
        SET total_visitas = total_visitas + 1,
            ultima_visita = NEW.hora_salida
        WHERE id = NEW.visitante_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- TRIGGERS (drop + create para idempotencia)
-- ============================================

DROP TRIGGER IF EXISTS tr_generar_codigo ON visitantes;
CREATE TRIGGER tr_generar_codigo
    BEFORE INSERT ON visitantes
    FOR EACH ROW EXECUTE FUNCTION generar_codigo_visita();

DROP TRIGGER IF EXISTS tr_actualizar_visitas ON historial_visitas;
CREATE TRIGGER tr_actualizar_visitas
    AFTER UPDATE ON historial_visitas
    FOR EACH ROW EXECUTE FUNCTION actualizar_contador_visitas();

-- ============================================
-- VISTAS (CREATE OR REPLACE para idempotencia)
-- ============================================

CREATE OR REPLACE VIEW v_itinerarios_activos AS
SELECT
    i.id,
    (v.nombre::text || ' ' || v.apellido::text) AS visitante,
    i.titulo,
    i.estado,
    i.duracion_total,
    COUNT(id.id) AS areas_programadas,
    COUNT(CASE WHEN id.visitado = TRUE THEN 1 END) AS areas_completadas
FROM itinerarios i
JOIN perfiles p ON i.perfil_id = p.id
JOIN visitantes v ON p.visitante_id = v.id
LEFT JOIN itinerario_detalles id ON i.id = id.itinerario_id
WHERE i.estado IN ('activo', 'pausado')
  AND DATE(i.fecha_generacion) = CURRENT_DATE
GROUP BY i.id, v.nombre, v.apellido;

CREATE OR REPLACE VIEW v_preferencias_categorias AS
SELECT
    a.categoria,
    COUNT(DISTINCT p.visitante_id) AS visitantes_interesados,
    AVG(i.duracion_total) AS duracion_promedio,
    AVG(i.puntuacion) AS satisfaccion_promedio
FROM perfiles p
JOIN itinerarios i ON p.id = i.perfil_id
JOIN itinerario_detalles id ON i.id = id.itinerario_id
JOIN areas a ON id.area_id = a.id
WHERE i.estado = 'completado'
GROUP BY a.categoria
ORDER BY visitantes_interesados DESC;

-- ============================================
-- DATOS INICIALES: areas del museo
-- Solo inserta si la tabla esta vacia
-- ============================================

INSERT INTO areas (codigo, nombre, categoria, subcategoria, descripcion, tiempo_minimo, tiempo_maximo, capacidad_simultanea, orden_recomendado)
SELECT * FROM (VALUES
    ('TEMP-01', 'Exhibición Temporal',            'temporal',     NULL,        'Exhibiciones rotativas',                    10, 30, 25, 1),
    ('ARQ-01',  'Sala Arqueológica Cañari',       'arqueologia',  'cañari',    'Vestigios de la cultura Cañari preincaica', 20, 40, 25, 2),
    ('ART-01',  'Sala de Arte Colonial',          'arte',         'colonial',  'Arte religioso colonial',                   15, 30, 20, 3),
    ('ETN-01',  'Sala Etnográfica',               'etnografia',   'indigenas', 'Culturas indígenas del Ecuador',            45, 50, 30, 4),
    ('RUIN-01', 'Parque Arqueológico Pumapungo',  'arqueologia',  'exterior',  'Parque arqueológicas al aire libre',        15, 30, 50, 5),
    ('AVE-01',  'Aviario de Aves Andinas',        'aves',         'rescate',   'Aves rescatadas de la región andina',       15, 20, 20, 6),
    ('BOT-01',  'Jardín Botánico',                'plantas',      'nativas',   'Flora endémica ecuatoriana',                20, 40, 40, 7)
) AS datos(codigo, nombre, categoria, subcategoria, descripcion, tiempo_minimo, tiempo_maximo, capacidad_simultanea, orden_recomendado)
WHERE NOT EXISTS (SELECT 1 FROM areas LIMIT 1);

-- ============================================
-- COMENTARIOS
-- ============================================

COMMENT ON TABLE visitantes IS 'Registro principal de visitantes del Museo Pumapungo';
COMMENT ON TABLE perfiles IS 'Preferencias e intereses para personalizacion con IA';
COMMENT ON TABLE areas IS 'Areas fisicas y salas del museo para itinerarios';
COMMENT ON TABLE itinerarios IS 'Rutas personalizadas generadas por IA generativa';
COMMENT ON TABLE itinerario_detalles IS 'Pasos especificos de cada itinerario';
COMMENT ON TABLE historial_visitas IS 'Registro historico de visitas para analisis';
COMMENT ON TABLE evaluaciones IS 'Evaluaciones de satisfaccion del itinerario';

COMMIT;
