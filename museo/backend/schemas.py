# schemas.py
# Schemas Pydantic para validación de datos
# Sistema Museo Pumapungo - Versión Simplificada

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum

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
# SCHEMAS: VISITANTE
# ============================================

class VisitanteBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    apellido: Optional[str] = Field(None, max_length=100)
    email: EmailStr
    telefono: Optional[str] = Field(None, max_length=20)
    pais_origen: Optional[str] = Field(None, max_length=100)
    ciudad_origen: Optional[str] = Field(None, max_length=100)
    tipo_visitante: Optional[TipoVisitanteEnum] = None
    tipo_entrada: Optional[TipoEntradaEnum] = None
    acompanantes: int = Field(default=0, ge=0)
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
    tipo_entrada: Optional[TipoEntradaEnum] = None
    acompanantes: Optional[int] = Field(None, ge=0)
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
    tiempo_disponible: Optional[int] = Field(None, ge=30, le=360, description="Minutos disponibles")
    idioma_preferido: str = Field(default="es", max_length=10)
    nivel_detalle: NivelDetalleEnum = NivelDetalleEnum.NORMAL
    incluir_descansos: bool = True

class PerfilCreate(PerfilBase):
    visitante_id: int

class PerfilUpdate(BaseModel):
    intereses: Optional[List[str]] = None
    tiempo_disponible: Optional[int] = Field(None, ge=30, le=360)
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
# SCHEMAS: AREA
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
    zona: Optional[str] = Field(None, max_length=50)

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
    zona: Optional[str] = Field(None, max_length=50)

class AreaResponse(AreaBase):
    id: int

    class Config:
        from_attributes = True

# ============================================
# SCHEMAS: ITINERARIO
# ============================================

class ItinerarioBase(BaseModel):
    titulo: Optional[str] = Field(None, max_length=200)
    nivel_detalle: NivelDetalleEnum = NivelDetalleEnum.NORMAL

class ItinerarioCreate(ItinerarioBase):
    perfil_id: int
    areas_seleccionadas: Optional[List[int]] = None  # IDs de áreas preferidas

class ItinerarioUpdate(BaseModel):
    estado: Optional[EstadoItinerarioEnum] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    puntuacion: Optional[int] = Field(None, ge=1, le=5)
    comentarios: Optional[str] = None

class ItinerarioResponse(ItinerarioBase):
    id: int
    perfil_id: int
    descripcion: Optional[str] = None
    duracion_total: Optional[int] = None
    distancia_estimada: Optional[float] = None
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
    introduccion: Optional[str] = None
    puntos_clave: Optional[List[str]] = None
    recomendacion: Optional[str] = None

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
# SCHEMAS: HISTORIAL VISITA
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
# SCHEMAS COMPUESTOS
# ============================================

class VisitanteConPerfil(VisitanteResponse):
    perfil: Optional[PerfilResponse] = None

class ItinerarioCompleto(ItinerarioResponse):
    detalles: List[ItinerarioDetalleResponse] = []
    
class ItinerarioDetalleConArea(ItinerarioDetalleResponse):
    area: Optional[AreaResponse] = None

# ============================================
# SCHEMAS PARA IA
# ============================================

class SolicitudItinerario(BaseModel):
    visitante_id: int
    tiempo_disponible: int = Field(..., ge=30, le=360, description="Tiempo en minutos")
    intereses: List[str] = Field(..., description="Lista de intereses")
    nivel_detalle: NivelDetalleEnum = NivelDetalleEnum.NORMAL
    incluir_descansos: bool = True
    areas_evitar: Optional[List[int]] = Field(None, description="IDs de áreas a evitar")

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