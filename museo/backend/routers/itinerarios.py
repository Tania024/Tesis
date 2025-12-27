# routers/itinerarios.py
# CRUD para gestión de itinerarios personalizados con IA
# Sistema Museo Pumapungo - CON IA INTEGRADA

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import logging
from datetime import datetime

from database import get_db
from models import Itinerario, Perfil, Visitante, Area, ItinerarioDetalle
from schemas import (
    ItinerarioCreate, 
    ItinerarioUpdate, 
    ItinerarioResponse,
    ItinerarioCompleto,
    SolicitudItinerario
)
from services.ia_service import ia_service

logger = logging.getLogger(__name__)
router = APIRouter()

# ============================================
# VERIFICAR IA
# ============================================

@router.get("/ia/estado")
async def verificar_estado_ia():
    """Verificar conexión con Ollama y disponibilidad del modelo"""
    estado = ia_service.verificar_conexion()
    
    if not estado["conectado"]:
        return {
            "estado": "desconectado",
            "mensaje": "⚠️ Ollama no está corriendo o no es accesible",
            "detalles": estado
        }
    
    if not estado.get("modelo_disponible"):
        return {
            "estado": "modelo_no_disponible",
            "mensaje": f"⚠️ El modelo {estado.get('modelo_configurado')} no está instalado",
            "solucion": f"Ejecuta: ollama pull {estado.get('modelo_configurado')}",
            "detalles": estado
        }
    
    return {
        "estado": "operativo",
        "mensaje": "✅ IA lista para generar itinerarios",
        "detalles": estado
    }

# ============================================
# CREATE - Generación con IA
# ============================================

@router.post("/generar", response_model=ItinerarioResponse, status_code=status.HTTP_201_CREATED)
async def generar_itinerario_ia(
    solicitud: SolicitudItinerario,
    db: Session = Depends(get_db)
):
    """
    🤖 Generar itinerario personalizado usando IA generativa (DeepSeek/Ollama)
    
    Este endpoint:
    1. Verifica que el visitante existe
    2. Obtiene o crea su perfil
    3. Consulta áreas disponibles según intereses
    4. **Genera itinerario personalizado con IA (DeepSeek/Ollama)**
    5. Crea el itinerario y sus detalles en la BD
    """
    try:
        # 1. Verificar visitante
        visitante = db.query(Visitante).filter(Visitante.id == solicitud.visitante_id).first()
        if not visitante:
            raise HTTPException(status_code=404, detail="Visitante no encontrado")
        
        # 2. Obtener o crear perfil
        perfil = db.query(Perfil).filter(Perfil.visitante_id == solicitud.visitante_id).first()
        if not perfil:
            perfil = Perfil(
                visitante_id=solicitud.visitante_id,
                intereses=solicitud.intereses,
                tiempo_disponible=solicitud.tiempo_disponible,
                nivel_detalle=solicitud.nivel_detalle.value,
                incluir_descansos=solicitud.incluir_descansos
            )
            db.add(perfil)
            db.commit()
            db.refresh(perfil)
        
        # 3. Obtener áreas disponibles según intereses
        query = db.query(Area).filter(Area.activa == True)
        
        # Filtrar por categorías de interés
        if solicitud.intereses:
            query = query.filter(Area.categoria.in_(solicitud.intereses))
        
        # Excluir áreas no deseadas
        if solicitud.areas_evitar:
            query = query.filter(~Area.id.in_(solicitud.areas_evitar))
        
        areas_disponibles = query.order_by(Area.orden_recomendado).all()
        
        if not areas_disponibles:
            raise HTTPException(
                status_code=404, 
                detail="No hay áreas disponibles con esos criterios"
            )
        
        # Convertir áreas a diccionarios para la IA
        areas_dict = [
            {
                "id": area.id,
                "codigo": area.codigo,
                "nombre": area.nombre,
                "descripcion": area.descripcion,
                "categoria": area.categoria,
                "subcategoria": area.subcategoria,
                "tiempo_minimo": area.tiempo_minimo,
                "tiempo_maximo": area.tiempo_maximo,
                "piso": area.piso,
                "zona": area.zona
            }
            for area in areas_disponibles
        ]
        
        # 4. 🤖 GENERAR ITINERARIO CON IA
        logger.info(f"🤖 Solicitando generación de itinerario a IA para {visitante.nombre}...")
        
        nombre_completo = f"{visitante.nombre} {visitante.apellido or ''}".strip()
        
        try:
            resultado_ia = ia_service.generar_itinerario(
                visitante_nombre=nombre_completo,
                intereses=solicitud.intereses,
                tiempo_disponible=solicitud.tiempo_disponible,
                nivel_detalle=solicitud.nivel_detalle.value,
                areas_disponibles=areas_dict,
                incluir_descansos=solicitud.incluir_descansos
            )
        except Exception as e:
            logger.error(f"❌ Error al generar con IA: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error al generar itinerario con IA: {str(e)}"
            )
        
        # 5. Crear itinerario en BD
        nuevo_itinerario = Itinerario(
            perfil_id=perfil.id,
            titulo=resultado_ia["titulo"],
            descripcion=resultado_ia["descripcion"],
            duracion_total=resultado_ia["duracion_total"],
            estado='generado',
            modelo_ia_usado=resultado_ia["metadata"]["modelo"],
            prompt_usado=resultado_ia["metadata"]["prompt"],
            respuesta_ia={
                "respuesta_cruda": resultado_ia["metadata"]["respuesta_cruda"],
                "temperature": resultado_ia["metadata"]["temperature"],
                "tiempo_generacion": resultado_ia["metadata"]["tiempo_generacion"],
                "timestamp": resultado_ia["metadata"]["timestamp"]
            }
        )
        
        db.add(nuevo_itinerario)
        db.commit()
        db.refresh(nuevo_itinerario)
        
        # 6. Crear detalles del itinerario según la IA
        mapeo_areas = {area.codigo: area for area in areas_disponibles}
        
        for area_ia in resultado_ia["areas"]:
            area_codigo = area_ia["area_codigo"]
            
            if area_codigo not in mapeo_areas:
                logger.warning(f"⚠️ Área {area_codigo} no encontrada, omitiendo...")
                continue
            
            area = mapeo_areas[area_codigo]
            
            detalle = ItinerarioDetalle(
                itinerario_id=nuevo_itinerario.id,
                area_id=area.id,
                orden=area_ia["orden"],
                tiempo_sugerido=area_ia["tiempo_sugerido"],
                introduccion=area_ia.get("introduccion", ""),
                puntos_clave=area_ia.get("puntos_clave", []),
                recomendacion=area_ia.get("recomendacion", "")
            )
            db.add(detalle)
        
        db.commit()
        db.refresh(nuevo_itinerario)
        
        logger.info(f"✅ Itinerario con IA generado: ID={nuevo_itinerario.id} para visitante {solicitud.visitante_id}")
        
        return nuevo_itinerario
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error al generar itinerario: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# CREATE - Manual
# ============================================

@router.post("/", response_model=ItinerarioResponse, status_code=status.HTTP_201_CREATED)
async def crear_itinerario_manual(
    itinerario: ItinerarioCreate,
    db: Session = Depends(get_db)
):
    """Crear itinerario manualmente (sin IA)"""
    perfil = db.query(Perfil).filter(Perfil.id == itinerario.perfil_id).first()
    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    
    nuevo_itinerario = Itinerario(**itinerario.model_dump())
    db.add(nuevo_itinerario)
    db.commit()
    db.refresh(nuevo_itinerario)
    
    logger.info(f"✅ Itinerario creado manualmente: {nuevo_itinerario.id}")
    return nuevo_itinerario

# ============================================
# READ
# ============================================

@router.get("/", response_model=List[ItinerarioResponse])
async def listar_itinerarios(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    estado: Optional[str] = None,
    perfil_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Listar itinerarios con filtros"""
    query = db.query(Itinerario)
    
    if estado:
        query = query.filter(Itinerario.estado == estado)
    
    if perfil_id:
        query = query.filter(Itinerario.perfil_id == perfil_id)
    
    return query.order_by(Itinerario.fecha_generacion.desc()).offset(skip).limit(limit).all()

@router.get("/{itinerario_id}", response_model=ItinerarioCompleto)
async def obtener_itinerario(itinerario_id: int, db: Session = Depends(get_db)):
    """Obtener itinerario completo con sus detalles"""
    itinerario = db.query(Itinerario).filter(Itinerario.id == itinerario_id).first()
    if not itinerario:
        raise HTTPException(status_code=404, detail="Itinerario no encontrado")
    return itinerario

@router.get("/visitante/{visitante_id}")
async def obtener_itinerarios_visitante(
    visitante_id: int,
    db: Session = Depends(get_db)
):
    """Obtener todos los itinerarios de un visitante"""
    perfil = db.query(Perfil).filter(Perfil.visitante_id == visitante_id).first()
    if not perfil:
        return {"itinerarios": []}
    
    itinerarios = db.query(Itinerario).filter(Itinerario.perfil_id == perfil.id).all()
    return {"total": len(itinerarios), "itinerarios": itinerarios}

# ============================================
# UPDATE
# ============================================

@router.put("/{itinerario_id}", response_model=ItinerarioResponse)
async def actualizar_itinerario(
    itinerario_id: int,
    itinerario_data: ItinerarioUpdate,
    db: Session = Depends(get_db)
):
    """Actualizar estado y feedback del itinerario"""
    itinerario = db.query(Itinerario).filter(Itinerario.id == itinerario_id).first()
    if not itinerario:
        raise HTTPException(status_code=404, detail="Itinerario no encontrado")
    
    for campo, valor in itinerario_data.model_dump(exclude_unset=True).items():
        setattr(itinerario, campo, valor)
    
    db.commit()
    db.refresh(itinerario)
    logger.info(f"✅ Itinerario actualizado: {itinerario_id}")
    return itinerario

# ============================================
# DELETE
# ============================================

@router.delete("/{itinerario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_itinerario(itinerario_id: int, db: Session = Depends(get_db)):
    """Eliminar itinerario"""
    itinerario = db.query(Itinerario).filter(Itinerario.id == itinerario_id).first()
    if not itinerario:
        raise HTTPException(status_code=404, detail="Itinerario no encontrado")
    
    db.delete(itinerario)
    db.commit()
    logger.info(f"✅ Itinerario eliminado: {itinerario_id}")

# ============================================
# CONTROL DE ESTADO
# ============================================

@router.post("/{itinerario_id}/iniciar", response_model=ItinerarioResponse)
async def iniciar_itinerario(itinerario_id: int, db: Session = Depends(get_db)):
    """Marcar itinerario como iniciado"""
    itinerario = db.query(Itinerario).filter(Itinerario.id == itinerario_id).first()
    if not itinerario:
        raise HTTPException(status_code=404, detail="Itinerario no encontrado")
    
    itinerario.estado = 'activo'
    itinerario.fecha_inicio = datetime.now()
    db.commit()
    db.refresh(itinerario)
    
    logger.info(f"✅ Itinerario iniciado: {itinerario_id}")
    return itinerario

@router.post("/{itinerario_id}/completar", response_model=ItinerarioResponse)
async def completar_itinerario(itinerario_id: int, db: Session = Depends(get_db)):
    """Marcar itinerario como completado"""
    itinerario = db.query(Itinerario).filter(Itinerario.id == itinerario_id).first()
    if not itinerario:
        raise HTTPException(status_code=404, detail="Itinerario no encontrado")
    
    itinerario.estado = 'completado'
    itinerario.fecha_fin = datetime.now()
    db.commit()
    db.refresh(itinerario)
    
    logger.info(f"✅ Itinerario completado: {itinerario_id}")
    return itinerario

# ============================================
# ESTADÍSTICAS
# ============================================

@router.get("/estadisticas/general")
async def estadisticas_itinerarios(db: Session = Depends(get_db)):
    """Estadísticas generales de itinerarios"""
    total = db.query(Itinerario).count()
    
    por_estado = db.query(
        Itinerario.estado,
        func.count(Itinerario.id)
    ).group_by(Itinerario.estado).all()
    
    con_ia = db.query(Itinerario).filter(
        Itinerario.modelo_ia_usado.isnot(None)
    ).count()
    
    puntuacion_promedio = db.query(
        func.avg(Itinerario.puntuacion)
    ).filter(Itinerario.puntuacion.isnot(None)).scalar()
    
    duracion_promedio = db.query(
        func.avg(Itinerario.duracion_total)
    ).filter(Itinerario.duracion_total.isnot(None)).scalar()
    
    return {
        "total_itinerarios": total,
        "generados_con_ia": con_ia,
        "por_estado": {estado: cant for estado, cant in por_estado},
        "puntuacion_promedio": round(puntuacion_promedio, 2) if puntuacion_promedio else None,
        "duracion_promedio_minutos": round(duracion_promedio, 0) if duracion_promedio else None
    }