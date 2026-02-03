# models.py
# ✅ CORREGIDO: Columnas eliminadas de BD también eliminadas del código

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Date, 
    ForeignKey, CheckConstraint, ARRAY, DECIMAL
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone

from database import Base

# ============================================
# MODELO: VISITANTES (CORREGIDO)
# ============================================

class Visitante(Base):
    __tablename__ = "visitantes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo_visita = Column(String(50), unique=True, index=True)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100))
    email = Column(String(150), unique=True, nullable=False, index=True)
    telefono = Column(String(20))
    
    # Origen
    pais_origen = Column(String(100))
    ciudad_origen = Column(String(100))
    tipo_visitante = Column(String(50))  # local, nacional, internacional
    
    # ✅ tipo_entrada y acompanantes ELIMINADOS (movidos a itinerarios)
    
    # Información adicional
    fecha_nacimiento = Column(Date)
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())
    ultima_visita = Column(DateTime(timezone=True))
    
    # Seguimiento
    total_visitas = Column(Integer, default=0)
    activo = Column(Boolean, default=True)
    
    # Relaciones
    perfil = relationship("Perfil", back_populates="visitante", uselist=False, cascade="all, delete-orphan")
    historial = relationship("HistorialVisita", back_populates="visitante", cascade="all, delete-orphan")
    
    # Constraints (✅ ELIMINADO check_tipo_entrada)
    __table_args__ = (
        CheckConstraint(
            "tipo_visitante IN ('local', 'nacional', 'internacional')",
            name='check_tipo_visitante'
        ),
    )
    
    def __repr__(self):
        return f"<Visitante {self.codigo_visita}: {self.nombre} {self.apellido}>"


# ============================================
# MODELO: PERFILES
# ============================================

class Perfil(Base):
    __tablename__ = "perfiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    visitante_id = Column(Integer, ForeignKey("visitantes.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Datos para IA
    intereses = Column(ARRAY(Text))  # ['arqueologia', 'aves', 'historia']
    tiempo_disponible = Column(Integer)  # Minutos
    idioma_preferido = Column(String(10), default='es')
    
    # Preferencias de experiencia
    nivel_detalle = Column(String(20), default='normal')  # rapido, normal, profundo
    incluir_descansos = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relaciones
    visitante = relationship("Visitante", back_populates="perfil")
    itinerarios = relationship("Itinerario", back_populates="perfil", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "nivel_detalle IN ('rapido', 'normal', 'profundo')",
            name='check_nivel_detalle'
        ),
    )
    
    def __repr__(self):
        return f"<Perfil visitante_id={self.visitante_id}>"


# ============================================
# MODELO: AREAS (CORREGIDO)
# ============================================

class Area(Base):
    __tablename__ = "areas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(20), unique=True, index=True)  # ARQ-01, AVE-01
    nombre = Column(String(150), nullable=False)
    descripcion = Column(Text)
    
    # Categorización
    categoria = Column(String(50), nullable=False, index=True)  # arqueologia, aves, arte
    subcategoria = Column(String(50))  # cañari, inca, colonial
    
    # Logística
    tiempo_minimo = Column(Integer, default=10)
    tiempo_maximo = Column(Integer, default=45)
    capacidad_simultanea = Column(Integer)
    orden_recomendado = Column(Integer)
    
    # Estado
    activa = Column(Boolean, default=True, index=True)
    requiere_guia = Column(Boolean, default=False)
    
    # Ubicación
    piso = Column(Integer, default=1)
    # ✅ zona ELIMINADO
    
    # Relaciones
    detalles_itinerario = relationship("ItinerarioDetalle", back_populates="area")
    
    def __repr__(self):
        return f"<Area {self.codigo}: {self.nombre}>"


# ============================================
# MODELO: ITINERARIOS (CORREGIDO)
# ============================================

class Itinerario(Base):
    __tablename__ = "itinerarios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    perfil_id = Column(Integer, ForeignKey("perfiles.id", ondelete="CASCADE"), nullable=False)
    
    # Información general
    titulo = Column(String(200))
    descripcion = Column(Text)  # Generado por IA
    duracion_total = Column(Integer)  # Minutos
    # ✅ distancia_estimada ELIMINADO
    
    # 🔥 NUEVOS CAMPOS: Tipo de entrada y acompañantes
    tipo_entrada = Column(String(50))  # estudiante, adulto_mayor, grupo, individual
    acompañantes = Column(Integer, default=0)
    
    # Estado
    estado = Column(String(20), default='generado', index=True)
    fecha_generacion = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc) 
    )
    fecha_inicio = Column(DateTime(timezone=True), nullable=True)  
    fecha_fin = Column(DateTime(timezone=True), nullable=True)
    
    # Feedback
    puntuacion = Column(Integer)  # 1-5
    # ✅ comentarios ELIMINADO
    
    # Metadata IA
    modelo_ia_usado = Column(String(50))  # deepseek, ollama
    prompt_usado = Column(Text)
    respuesta_ia = Column(JSONB)  # Respuesta completa JSON
    
    # Relaciones
    perfil = relationship("Perfil", back_populates="itinerarios")
    detalles = relationship("ItinerarioDetalle", back_populates="itinerario", cascade="all, delete-orphan")
    historial = relationship("HistorialVisita", back_populates="itinerario")
    evaluacion = relationship("Evaluacion", back_populates="itinerario", uselist=False, cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "estado IN ('generado', 'activo', 'pausado', 'completado', 'cancelado')",
            name='check_estado'
        ),
        CheckConstraint(
            "puntuacion >= 1 AND puntuacion <= 5",
            name='check_puntuacion'
        ),
        CheckConstraint(
            "tipo_entrada IN ('estudiante', 'adulto_mayor', 'grupo', 'individual')",
            name='check_tipo_entrada_itinerario'
        ),
        CheckConstraint(
            "acompañantes >= 0",
            name='check_acompanantes'
        ),
    )
    
    def __repr__(self):
        return f"<Itinerario {self.id}: {self.titulo}>"


# ============================================
# MODELO: ITINERARIO_DETALLES
# ============================================

class ItinerarioDetalle(Base):
    __tablename__ = "itinerario_detalles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    itinerario_id = Column(Integer, ForeignKey("itinerarios.id", ondelete="CASCADE"), nullable=False)
    area_id = Column(Integer, ForeignKey("areas.id"), nullable=False)
    
    # Orden y tiempo
    orden = Column(Integer, nullable=False)
    tiempo_sugerido = Column(Integer)  # Minutos
    tiempo_real = Column(Integer)  # Minutos reales
    
    # Información contextual (generada por IA)
    introduccion = Column(Text)
    recomendacion = Column(Text)
    
    # Contenido extenso generado por IA
    historia_contextual = Column(Text)  # Párrafo largo de 5-7 líneas
    datos_curiosos = Column(JSONB)      # Array de 4 datos curiosos
    que_observar = Column(JSONB)        # Array de 4 elementos a observar
    puntos_clave = Column(ARRAY(Text))  # Array de puntos clave
    
    # Estado
    visitado = Column(Boolean, default=False)
    skip = Column(Boolean, default=False)
    
    # Tiempos
    hora_inicio = Column(DateTime(timezone=True), nullable=True)  
    hora_fin = Column(DateTime(timezone=True), nullable=True)
    
    # Relaciones
    itinerario = relationship("Itinerario", back_populates="detalles")
    area = relationship("Area", back_populates="detalles_itinerario")
    
    def __repr__(self):
        return f"<Detalle orden={self.orden} area_id={self.area_id}>"


# ============================================
# MODELO: HISTORIAL_VISITAS (CORREGIDO)
# ============================================

class HistorialVisita(Base):
    __tablename__ = "historial_visitas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    visitante_id = Column(Integer, ForeignKey("visitantes.id"), nullable=False)
    itinerario_id = Column(Integer, ForeignKey("itinerarios.id"))
    
    # Datos de la visita
    fecha_visita = Column(Date, server_default=func.current_date())
    hora_entrada = Column(DateTime(timezone=True), server_default=func.now())
    hora_salida = Column(DateTime(timezone=True))
    duracion_total = Column(Integer)  # Minutos
    
    # Métricas
    areas_visitadas = Column(Integer)
    areas_completadas = Column(Integer)
    satisfaccion_general = Column(Integer)  # 1-5
    
    # Análisis
    hora_pico = Column(Boolean, default=False)
    
    # Relaciones
    visitante = relationship("Visitante", back_populates="historial")
    itinerario = relationship("Itinerario", back_populates="historial")
    
    # ✅ Constraints ELIMINADO check_satisfaccion
    
    def __repr__(self):
        return f"<Visita {self.fecha_visita} - Visitante {self.visitante_id}>"


# ============================================
# MODELO: EVALUACION
# ============================================

class Evaluacion(Base):
    """
    Evaluación de la experiencia del visitante al finalizar el itinerario
    """
    __tablename__ = "evaluaciones"

    id = Column(Integer, primary_key=True, index=True)
    
    # Relación con itinerario
    itinerario_id = Column(Integer, ForeignKey("itinerarios.id"), nullable=False)
    
    # Calificación general (1-5)
    calificacion_general = Column(Integer, nullable=False)  # 1=😡, 2=😕, 3=😐, 4=😊, 5=🤩
    
    # Preguntas específicas (True/False = 👍/👎)
    personalizado = Column(Boolean, nullable=False)
    buenas_decisiones = Column(Boolean, nullable=False)
    acompaniamiento = Column(Boolean, nullable=False)
    comprension = Column(Boolean, nullable=False)
    relevante = Column(Boolean, nullable=False)
    usaria_nuevamente = Column(Boolean, nullable=False)
    
    # Comentarios opcionales
    comentarios = Column(Text, nullable=True)
    
    # Metadata
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    # Relación
    itinerario = relationship("Itinerario", back_populates="evaluacion")

    def __repr__(self):
        return f"<Evaluacion {self.id} - Itinerario {self.itinerario_id} - {self.calificacion_general}⭐>"