# schemas.py
# ✅ CORREGIDO: Sin campos eliminados de la BD

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum
import json
from pydantic import field_validator, model_validator

# ============================================
# ENUMS
# ============================================

class TipoVisitanteEnum(str, Enum):
    LOCAL = "local"
    NACIONAL = "nacional"
    INTERNACIONAL = "internacional"

class TipoEntradaEnum(str, Enum):
    ESTUDIANTE = "estudiante"
    ADULTO_MAYOR = "adulto_mayor"
    GRUPO = "grupo"
    INDIVIDUAL = "individual"

class NivelDetalleEnum(str, Enum):
    RAPIDO = "rapido"
    NORMAL = "normal"
    PROFUNDO = "profundo"

class EstadoItinerarioEnum(str, Enum):
    GENERADO = "generado"
    ACTIVO = "activo"
    PAUSADO = "pausado"
    COMPLETADO = "completado"
    CANCELADO = "cancelado"

# ============================================
# SCHEMAS: VISITANTE (CORREGIDO)
# ============================================

class VisitanteBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    apellido: Optional[str] = Field(None, max_length=100)
    email: EmailStr
    telefono: Optional[str] = Field(None, max_length=20)
    pais_origen: Optional[str] = Field(None, max_length=100)
    ciudad_origen: Optional[str] = Field(None, max_length=100)
    tipo_visitante: Optional[TipoVisitanteEnum] = None
    # ✅ tipo_entrada ELIMINADO (movido a itinerarios)
    # ✅ acompanantes ELIMINADO (movido a itinerarios)
    fecha_nacimiento: Optional[date] = None

class VisitanteCreate(VisitanteBase):
    pass

class VisitanteUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    apellido: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, max_length=20)
    pais_origen: Optional[str] = Field(None, max_length=100)
    ciudad_origen: Optional[str] = Field(None, max_length=100)
    tipo_visitante: Optional[TipoVisitanteEnum] = None
    # ✅ tipo_entrada ELIMINADO
    # ✅ acompanantes ELIMINADO
    fecha_nacimiento: Optional[date] = None

class VisitanteResponse(VisitanteBase):
    id: int
    codigo_visita: Optional[str] = None
    fecha_registro: datetime
    ultima_visita: Optional[datetime] = None
    total_visitas: int
    activo: bool

    class Config:
        from_attributes = True

# ============================================
# SCHEMAS: PERFIL
# ============================================

class PerfilBase(BaseModel):
    intereses: Optional[List[str]] = Field(
        default=None,
        description="Lista de intereses: arqueologia, etnografia, aves, plantas, arte"
    )
    tiempo_disponible: Optional[int] = Field(None, ge=30, le=480, description="Minutos disponibles")
    idioma_preferido: str = Field(default="es", max_length=10)
    nivel_detalle: NivelDetalleEnum = NivelDetalleEnum.NORMAL
    incluir_descansos: bool = True

class PerfilCreate(PerfilBase):
    visitante_id: int

class PerfilUpdate(BaseModel):
    intereses: Optional[List[str]] = None
    tiempo_disponible: Optional[int] = Field(None, ge=30, le=480)
    idioma_preferido: Optional[str] = Field(None, max_length=10)
    nivel_detalle: Optional[NivelDetalleEnum] = None
    incluir_descansos: Optional[bool] = None

class PerfilResponse(PerfilBase):
    id: int
    visitante_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ============================================
# SCHEMAS: AREA (CORREGIDO)
# ============================================

class AreaBase(BaseModel):
    codigo: Optional[str] = Field(None, max_length=20)
    nombre: str = Field(..., max_length=150)
    descripcion: Optional[str] = None
    categoria: str = Field(..., max_length=50)
    subcategoria: Optional[str] = Field(None, max_length=50)
    tiempo_minimo: int = Field(default=10, ge=5)
    tiempo_maximo: int = Field(default=45, ge=10)
    capacidad_simultanea: Optional[int] = Field(None, ge=1)
    orden_recomendado: Optional[int] = None
    activa: bool = True
    requiere_guia: bool = False
    piso: int = Field(default=1, ge=1, le=5)
    # ✅ zona ELIMINADO

class AreaCreate(AreaBase):
    pass

class AreaUpdate(BaseModel):
    nombre: Optional[str] = Field(None, max_length=150)
    descripcion: Optional[str] = None
    categoria: Optional[str] = Field(None, max_length=50)
    subcategoria: Optional[str] = Field(None, max_length=50)
    tiempo_minimo: Optional[int] = Field(None, ge=5)
    tiempo_maximo: Optional[int] = Field(None, ge=10)
    capacidad_simultanea: Optional[int] = Field(None, ge=1)
    orden_recomendado: Optional[int] = None
    activa: Optional[bool] = None
    requiere_guia: Optional[bool] = None
    piso: Optional[int] = Field(None, ge=1, le=5)
    # ✅ zona ELIMINADO

class AreaResponse(AreaBase):
    id: int

    class Config:
        from_attributes = True

# ============================================
# SCHEMAS: ITINERARIO (CORREGIDO)
# ============================================

class ItinerarioBase(BaseModel):
    titulo: Optional[str] = Field(None, max_length=200)
    nivel_detalle: NivelDetalleEnum = NivelDetalleEnum.NORMAL
    # 🔥 NUEVOS CAMPOS: tipo_entrada y acompañantes
    tipo_entrada: Optional[TipoEntradaEnum] = None
    acompañantes: int = Field(default=0, ge=0)

class ItinerarioCreate(ItinerarioBase):
    perfil_id: int
    areas_seleccionadas: Optional[List[int]] = None  # IDs de áreas preferidas

class ItinerarioUpdate(BaseModel):
    estado: Optional[EstadoItinerarioEnum] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    puntuacion: Optional[int] = Field(None, ge=1, le=5)
    # ✅ comentarios ELIMINADO
    tipo_entrada: Optional[TipoEntradaEnum] = None
    acompañantes: Optional[int] = Field(None, ge=0)

class ItinerarioResponse(ItinerarioBase):
    id: int
    perfil_id: int
    descripcion: Optional[str] = None
    duracion_total: Optional[int] = None
    # ✅ distancia_estimada ELIMINADO
    estado: str
    fecha_generacion: datetime
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    puntuacion: Optional[int] = None
    modelo_ia_usado: Optional[str] = None

    class Config:
        from_attributes = True

# ============================================
# SCHEMAS: ITINERARIO DETALLE
# ============================================

class ItinerarioDetalleBase(BaseModel):
    orden: int = Field(..., ge=1)
    tiempo_sugerido: Optional[int] = Field(None, ge=5)
    
    # Campos básicos
    introduccion: Optional[str] = None
    recomendacion: Optional[str] = None
    
    # Contenido extenso generado por IA
    historia_contextual: Optional[str] = Field(None, description="Párrafo largo sobre historia y contexto")
    datos_curiosos: Optional[List[str]] = Field(None, description="Array de 4 datos curiosos")
    que_observar: Optional[List[str]] = Field(None, description="Array de 4 elementos a observar")
    puntos_clave: Optional[List[str]] = Field(None, description="Array de puntos clave")

    # Validators: Convertir strings JSON a listas
    @field_validator('datos_curiosos', 'que_observar', 'puntos_clave', mode='before')
    @classmethod
    def parse_json_strings(cls, v):
        """Convierte strings JSON a listas Python"""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return None
        return v
    
class ItinerarioDetalleCreate(ItinerarioDetalleBase):
    itinerario_id: int
    area_id: int

class ItinerarioDetalleUpdate(BaseModel):
    visitado: Optional[bool] = None
    skip: Optional[bool] = None
    tiempo_real: Optional[int] = Field(None, ge=0)
    hora_inicio: Optional[datetime] = None
    hora_fin: Optional[datetime] = None

class ItinerarioDetalleResponse(ItinerarioDetalleBase):
    id: int
    itinerario_id: int
    area_id: int
    tiempo_real: Optional[int] = None
    visitado: bool
    skip: bool
    hora_inicio: Optional[datetime] = None
    hora_fin: Optional[datetime] = None

    class Config:
        from_attributes = True

# ============================================
# SCHEMAS: HISTORIAL VISITA (CORREGIDO)
# ============================================

class HistorialVisitaBase(BaseModel):
    fecha_visita: Optional[date] = None
    hora_entrada: Optional[datetime] = None

class HistorialVisitaCreate(HistorialVisitaBase):
    visitante_id: int
    itinerario_id: Optional[int] = None

class HistorialVisitaUpdate(BaseModel):
    hora_salida: Optional[datetime] = None
    duracion_total: Optional[int] = Field(None, ge=0)
    areas_visitadas: Optional[int] = Field(None, ge=0)
    areas_completadas: Optional[int] = Field(None, ge=0)
    satisfaccion_general: Optional[int] = Field(None, ge=1, le=5)
    hora_pico: Optional[bool] = None

class HistorialVisitaResponse(HistorialVisitaBase):
    id: int
    visitante_id: int
    itinerario_id: Optional[int] = None
    hora_salida: Optional[datetime] = None
    duracion_total: Optional[int] = None
    areas_visitadas: Optional[int] = None
    areas_completadas: Optional[int] = None
    satisfaccion_general: Optional[int] = None
    hora_pico: bool

    class Config:
        from_attributes = True


# ============================================
# SCHEMAS: EVALUACION
# ============================================

class EvaluacionCreate(BaseModel):
    """Schema para crear evaluación"""
    itinerario_id: int
    calificacion_general: int = Field(..., ge=1, le=5, description="Calificación de 1 a 5")
    personalizado: bool
    buenas_decisiones: bool
    acompaniamiento: bool
    comprension: bool
    relevante: bool
    usaria_nuevamente: bool
    comentarios: Optional[str] = None

class EvaluacionResponse(BaseModel):
    """Schema para respuesta de evaluación"""
    id: int
    itinerario_id: int
    calificacion_general: int
    personalizado: bool
    buenas_decisiones: bool
    acompaniamiento: bool
    comprension: bool
    relevante: bool
    usaria_nuevamente: bool
    comentarios: Optional[str]
    fecha_creacion: datetime

    class Config:
        from_attributes = True

class EstadisticasEvaluacion(BaseModel):
    """Estadísticas agregadas de evaluaciones"""
    total_evaluaciones: int
    calificacion_promedio: float
    porcentaje_personalizado: float
    porcentaje_buenas_decisiones: float
    porcentaje_acompaniamiento: float
    porcentaje_comprension: float
    porcentaje_relevante: float
    porcentaje_usaria_nuevamente: float
    satisfaccion_general: str  # "Excelente", "Buena", "Regular", etc.

# ============================================
# SCHEMAS COMPUESTOS
# ============================================

class VisitanteConPerfil(VisitanteResponse):
    perfil: Optional[PerfilResponse] = None

class ItinerarioDetalleConArea(ItinerarioDetalleResponse):
    area: Optional[AreaResponse] = None

class ItinerarioCompleto(ItinerarioResponse):
    detalles: List[ItinerarioDetalleConArea] = []


# ============================================
# SCHEMAS PARA IA
# ============================================

class SolicitudItinerario(BaseModel):
    visitante_id: int
    tiempo_disponible: Optional[int] = Field(None, ge=30, le=480, description="Tiempo en minutos (null = sin límite)")
    intereses: List[str] = Field(..., description="Lista de intereses")
    nivel_detalle: NivelDetalleEnum = NivelDetalleEnum.NORMAL
    incluir_descansos: bool = True
    areas_evitar: Optional[List[int]] = Field(None, description="IDs de áreas a evitar")
    # 🔥 NUEVOS CAMPOS REQUERIDOS
    tipo_entrada: TipoEntradaEnum
    acompañantes: int = Field(default=0, ge=0, le=50)
    
    # Validator para validar tipo_entrada vs acompañantes
    @model_validator(mode='after')
    def validar_tipo_entrada_acompanantes(self):
        if self.tipo_entrada == TipoEntradaEnum.INDIVIDUAL and self.acompañantes > 0:
            raise ValueError('Entrada individual no puede tener acompañantes')
        if self.tipo_entrada == TipoEntradaEnum.GRUPO and self.acompañantes < 1:
            raise ValueError('Entrada de grupo debe tener al menos 1 acompañante')
        return self

class RespuestaIA(BaseModel):
    titulo: str
    descripcion: str
    duracion_total: int
    areas: List[Dict[str, Any]]  # Lista de áreas con detalles
    
# ============================================
# SCHEMAS DE RESPUESTA
# ============================================

class MensajeRespuesta(BaseModel):
    mensaje: str
    exito: bool = True
    datos: Optional[Any] = None

class ErrorRespuesta(BaseModel):
    mensaje: str
    error: str
    codigo: int