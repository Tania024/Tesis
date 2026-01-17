DROP SCHEMA public CASCADE;
CREATE SCHEMA public;

-- ============================================
-- SCHEMA BASE DE DATOS - MUSEO PUMAPUNGO
-- Sistema de Registro y Perfilado de Visitantes
-- ============================================

-- ============================================
-- SCHEMA OPTIMIZADO - PROYECTO TITULACIÓN MUSEO PUMAPUNGO
-- ============================================
SELECT * FROM visitantes;
-- Tabla VISITANTES (completa pero práctica)
CREATE TABLE visitantes (
    id SERIAL PRIMARY KEY,
    codigo_visita VARCHAR(50) UNIQUE, -- Para QR o acceso rápido
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100),
    email VARCHAR(150) UNIQUE NOT NULL,
    telefono VARCHAR(20),
    
    -- Campos que solicitaste
    pais_origen VARCHAR(100),
    ciudad_origen VARCHAR(100),
    tipo_visitante VARCHAR(50) CHECK (tipo_visitante IN ('local', 'nacional', 'internacional')),
    tipo_entrada VARCHAR(50) CHECK (tipo_entrada IN ('estudiante', 'adulto_mayor', 'grupo', 'individual')),
    acompanantes INTEGER DEFAULT 0,
    
    -- Campos adicionales útiles
    fecha_nacimiento DATE,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultima_visita TIMESTAMP,
    
    -- Para seguimiento
    total_visitas INTEGER DEFAULT 0,
    activo BOOLEAN DEFAULT TRUE
);

-- Tabla PERFILES (simplificada para IA)
CREATE TABLE perfiles (
    id SERIAL PRIMARY KEY,
    visitante_id INTEGER UNIQUE REFERENCES visitantes(id) ON DELETE CASCADE,
    
    -- Datos para la IA
    intereses TEXT[], -- Ej: {'arqueologia', 'aves', 'historia'}
    tiempo_disponible INTEGER, -- Minutos totales
    idioma_preferido VARCHAR(10) DEFAULT 'es',
    
    -- Preferencias de experiencia
    nivel_detalle VARCHAR(20) CHECK (nivel_detalle IN ('rapido', 'normal', 'profundo')) DEFAULT 'normal',
    incluir_descansos BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla AREAS (esencial para itinerarios)
CREATE TABLE areas (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE, -- Ej: 'ARQ-01', 'AVE-01'
    nombre VARCHAR(150) NOT NULL,
    descripcion TEXT,
    
    -- Categorización
    categoria VARCHAR(50) NOT NULL, -- 'arqueologia', 'etnografia', 'aves', 'plantas', 'arte'
    subcategoria VARCHAR(50), -- 'cañari', 'inca', 'colonial'
    
    -- Logística
    tiempo_minimo INTEGER DEFAULT 10, -- Minutos mínimos sugeridos
    tiempo_maximo INTEGER DEFAULT 45, -- Minutos máximos sugeridos
    capacidad_simultanea INTEGER,
    orden_recomendado INTEGER,
    
    -- Estado
    activa BOOLEAN DEFAULT TRUE,
    requiere_guia BOOLEAN DEFAULT FALSE,
    
    -- Ubicación (para mapa interno)
    piso INTEGER DEFAULT 1,
    zona VARCHAR(50) -- 'norte', 'sur', 'exterior'
);

-- Tabla ITINERARIOS (núcleo del sistema)
CREATE TABLE itinerarios (
    id SERIAL PRIMARY KEY,
    perfil_id INTEGER REFERENCES perfiles(id) ON DELETE CASCADE,
    
    -- Información general
    titulo VARCHAR(200),
    descripcion TEXT, -- Generado por IA: "Recorrido para amantes de la arqueología..."
    duracion_total INTEGER, -- En minutos
    distancia_estimada DECIMAL(5,2), -- En metros (opcional)
    
    -- Estado y seguimiento
    estado VARCHAR(20) CHECK (estado IN ('generado', 'activo', 'pausado', 'completado', 'cancelado')) DEFAULT 'generado',
    fecha_generacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_inicio TIMESTAMP,
    fecha_fin TIMESTAMP,
    
    -- Feedback
    puntuacion INTEGER CHECK (puntuacion BETWEEN 1 AND 5),
    comentarios TEXT,
    
    -- Metadata IA
    modelo_ia_usado VARCHAR(50), -- 'deepseek', 'ollama'
    prompt_usado TEXT, -- Prompt enviado a la IA
    respuesta_ia JSONB -- Respuesta completa de la IA
);

-- Tabla ITINERARIO_DETALLES (pasos del recorrido)
CREATE TABLE itinerario_detalles (
    id SERIAL PRIMARY KEY,
    itinerario_id INTEGER REFERENCES itinerarios(id) ON DELETE CASCADE,
    area_id INTEGER REFERENCES areas(id),
    
    -- Orden y tiempo
    orden INTEGER NOT NULL,
    tiempo_sugerido INTEGER, -- Minutos para esta área
    tiempo_real INTEGER, -- Minutos reales (si se completa)
    
    -- Información contextual generada por IA
    introduccion TEXT, -- "En esta sala descubrirás..."
    puntos_clave TEXT[], -- ['Cerámica Cañari', 'Herramientas agrícolas']
    recomendacion TEXT, -- "No te pierdas la vitrina 3..."
    
    -- Estado
    visitado BOOLEAN DEFAULT FALSE,
    skip BOOLEAN DEFAULT FALSE,
    
    -- Tiempos reales
    hora_inicio TIMESTAMP,
    hora_fin TIMESTAMP
);

-- Tabla HISTORIAL_VISITAS (para analytics)
CREATE TABLE historial_visitas (
    id SERIAL PRIMARY KEY,
    visitante_id INTEGER REFERENCES visitantes(id),
    itinerario_id INTEGER REFERENCES itinerarios(id),
    
    -- Datos de la visita
    fecha_visita DATE DEFAULT CURRENT_DATE,
    hora_entrada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    hora_salida TIMESTAMP,
    duracion_total INTEGER, -- En minutos
    
    -- Métricas
    areas_visitadas INTEGER,
    areas_completadas INTEGER,
    satisfaccion_general INTEGER CHECK (satisfaccion_general BETWEEN 1 AND 5),
    
    -- Para análisis
    hora_pico BOOLEAN DEFAULT FALSE
);

-- ============================================
-- ÍNDICES (optimización)
-- ============================================
CREATE INDEX idx_visitantes_codigo ON visitantes(codigo_visita);
CREATE INDEX idx_visitantes_email ON visitantes(email);
CREATE INDEX idx_visitantes_tipo ON visitantes(tipo_visitante);
CREATE INDEX idx_perfiles_intereses ON perfiles USING GIN(intereses);
CREATE INDEX idx_itinerarios_estado ON itinerarios(estado);
CREATE INDEX idx_itinerarios_fecha ON itinerarios(fecha_generacion);
CREATE INDEX idx_areas_categoria ON areas(categoria);
CREATE INDEX idx_areas_activa ON areas(activa) WHERE activa = TRUE;
CREATE INDEX idx_itinerario_detalles_orden ON itinerario_detalles(itinerario_id, orden);

-- ============================================
-- DATOS DE EJEMPLO (Pumapungo real)
-- ============================================

-- Áreas del Museo Pumapungo (basado en investigación)
INSERT INTO areas (codigo, nombre, categoria, subcategoria, descripcion, tiempo_minimo, tiempo_maximo, capacidad_simultanea, orden_recomendado) VALUES
('ARQ-01', 'Sala Arqueológica Cañari', 'arqueologia', 'cañari', 'Vestigios de la cultura Cañari preincaica', 20, 40, 25, 1),
('ARQ-02', 'Sala Inca', 'arqueologia', 'inca', 'Ocupación Inca en la región', 15, 30, 20, 2),
('ETN-01', 'Sala Etnográfica', 'etnografia', 'indigenas', 'Culturas indígenas del Ecuador', 25, 50, 30, 3),
('AVE-01', 'Aviario de Aves Andinas', 'aves', 'rescate', 'Aves rescatadas de la región andina', 15, 25, 15, 4),
('BOT-01', 'Jardín Botánico', 'plantas', 'nativas', 'Flora endémica ecuatoriana', 20, 40, 40, 5),
('ART-01', 'Sala de Arte Colonial', 'arte', 'colonial', 'Arte religioso colonial', 15, 30, 20, 6),
('RUIN-01', 'Ruinas Pumapungo', 'arqueologia', 'exterior', 'Ruinas arqueológicas al aire libre', 30, 60, 50, 7),
('TEMP-01', 'Exhibición Temporal', 'temporal', NULL, 'Exhibiciones rotativas', 10, 30, 25, 8);

-- ============================================
-- VISTAS ÚTILES
-- ============================================

-- Vista: Visitantes con perfil completo
CREATE VIEW v_visitantes_completos AS
SELECT 
    v.id,
    v.codigo_visita,
    v.nombre || ' ' || v.apellido AS nombre_completo,
    v.email,
    v.tipo_visitante,
    v.pais_origen,
    v.ciudad_origen,
    p.intereses,
    p.tiempo_disponible,
    p.idioma_preferido,
    v.total_visitas
FROM visitantes v
LEFT JOIN perfiles p ON v.id = p.visitante_id;

-- Vista: Itinerarios activos hoy
CREATE VIEW v_itinerarios_activos AS
SELECT 
    i.id,
    v.nombre || ' ' || v.apellido AS visitante,
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

-- Vista: Preferencias por categoría (para analytics)
CREATE VIEW v_preferencias_categorias AS
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
-- FUNCIONES UTILES
-- ============================================

-- Función para generar código de visita automático
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

CREATE TRIGGER tr_generar_codigo
BEFORE INSERT ON visitantes
FOR EACH ROW EXECUTE FUNCTION generar_codigo_visita();

-- Función para actualizar total de visitas
CREATE OR REPLACE FUNCTION actualizar_contador_visitas()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.hora_salida IS NOT NULL AND OLD.hora_salida IS NULL THEN
        -- Visita completada, incrementar contador
        UPDATE visitantes 
        SET total_visitas = total_visitas + 1,
            ultima_visita = NEW.hora_salida
        WHERE id = NEW.visitante_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_actualizar_visitas
AFTER UPDATE ON historial_visitas
FOR EACH ROW EXECUTE FUNCTION actualizar_contador_visitas();

-- ============================================
-- COMENTARIOS
-- ============================================
COMMENT ON TABLE visitantes IS 'Registro principal de visitantes del Museo Pumapungo';
COMMENT ON TABLE perfiles IS 'Preferencias e intereses para personalización con IA';
COMMENT ON TABLE areas IS 'Áreas físicas y salas del museo para itinerarios';
COMMENT ON TABLE itinerarios IS 'Rutas personalizadas generadas por IA generativa';
COMMENT ON TABLE itinerario_detalles IS 'Pasos específicos de cada itinerario';
COMMENT ON TABLE historial_visitas IS 'Registro histórico de visitas para análisis';

COMMENT ON COLUMN visitantes.codigo_visita IS 'Código único para acceso rápido (QR)';
COMMENT ON COLUMN visitantes.tipo_visitante IS 'local, nacional o internacional';
COMMENT ON COLUMN visitantes.tipo_entrada IS 'Tipo de entrada según categoría';
COMMENT ON COLUMN perfiles.intereses IS 'Array de intereses para alimentar la IA';
COMMENT ON COLUMN itinerarios.respuesta_ia IS 'Respuesta completa en JSON de la IA generativa';
-- ============================================
-- FIN DEL SCHEMA
-- ============================================