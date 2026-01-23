# routers/evaluaciones.py
# 🔥 VERSIÓN SIN DEPENDENCIES (sin autenticación)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from database import get_db
from models import Evaluacion, Itinerario, Visitante, Perfil
from schemas import EvaluacionCreate, EvaluacionResponse, EstadisticasEvaluacion

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=EvaluacionResponse, status_code=status.HTTP_201_CREATED)
def crear_evaluacion(
    evaluacion: EvaluacionCreate,
    db: Session = Depends(get_db)
):
    """
    Crear evaluación de experiencia para un itinerario
    """
    try:
        logger.info(f"📊 Creando evaluación para itinerario {evaluacion.itinerario_id}")
        
        # Verificar que el itinerario existe
        itinerario = db.query(Itinerario).filter(
            Itinerario.id == evaluacion.itinerario_id
        ).first()
        
        if not itinerario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Itinerario no encontrado"
            )
        
        # Verificar si ya existe una evaluación
        evaluacion_existente = db.query(Evaluacion).filter(
            Evaluacion.itinerario_id == evaluacion.itinerario_id
        ).first()
        
        if evaluacion_existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una evaluación para este itinerario"
            )
        
        # Crear evaluación
        nueva_evaluacion = Evaluacion(
            itinerario_id=evaluacion.itinerario_id,
            calificacion_general=evaluacion.calificacion_general,
            personalizado=evaluacion.personalizado,
            buenas_decisiones=evaluacion.buenas_decisiones,
            acompaniamiento=evaluacion.acompaniamiento,
            comprension=evaluacion.comprension,
            relevante=evaluacion.relevante,
            usaria_nuevamente=evaluacion.usaria_nuevamente,
            comentarios=evaluacion.comentarios
        )
        
        db.add(nueva_evaluacion)
        db.commit()
        db.refresh(nueva_evaluacion)
        
        logger.info(f"✅ Evaluación {nueva_evaluacion.id} creada - Calificación: {nueva_evaluacion.calificacion_general}⭐")
        
        return nueva_evaluacion
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creando evaluación: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear evaluación: {str(e)}"
        )

@router.get("/itinerario/{itinerario_id}", response_model=EvaluacionResponse)
def obtener_evaluacion_itinerario(
    itinerario_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtener evaluación de un itinerario específico
    """
    evaluacion = db.query(Evaluacion).filter(
        Evaluacion.itinerario_id == itinerario_id
    ).first()
    
    if not evaluacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluación no encontrada"
        )
    
    return evaluacion

@router.get("/estadisticas", response_model=EstadisticasEvaluacion)
def obtener_estadisticas_evaluaciones(
    db: Session = Depends(get_db)
):
    """
    Obtener estadísticas agregadas de todas las evaluaciones
    (Útil para administradores y para la tesis)
    """
    evaluaciones = db.query(Evaluacion).all()
    
    if not evaluaciones:
        return EstadisticasEvaluacion(
            total_evaluaciones=0,
            calificacion_promedio=0.0,
            porcentaje_personalizado=0.0,
            porcentaje_buenas_decisiones=0.0,
            porcentaje_acompaniamiento=0.0,
            porcentaje_comprension=0.0,
            porcentaje_relevante=0.0,
            porcentaje_usaria_nuevamente=0.0,
            satisfaccion_general="Sin datos"
        )
    
    total = len(evaluaciones)
    
    # Calcular promedios
    calificacion_promedio = sum(e.calificacion_general for e in evaluaciones) / total
    
    porcentaje_personalizado = sum(1 for e in evaluaciones if e.personalizado) / total * 100
    porcentaje_buenas_decisiones = sum(1 for e in evaluaciones if e.buenas_decisiones) / total * 100
    porcentaje_acompaniamiento = sum(1 for e in evaluaciones if e.acompaniamiento) / total * 100
    porcentaje_comprension = sum(1 for e in evaluaciones if e.comprension) / total * 100
    porcentaje_relevante = sum(1 for e in evaluaciones if e.relevante) / total * 100
    porcentaje_usaria_nuevamente = sum(1 for e in evaluaciones if e.usaria_nuevamente) / total * 100
    
    # Determinar nivel de satisfacción
    if calificacion_promedio >= 4.5:
        satisfaccion = "Excelente"
    elif calificacion_promedio >= 3.5:
        satisfaccion = "Buena"
    elif calificacion_promedio >= 2.5:
        satisfaccion = "Regular"
    else:
        satisfaccion = "Necesita mejorar"
    
    return EstadisticasEvaluacion(
        total_evaluaciones=total,
        calificacion_promedio=round(calificacion_promedio, 2),
        porcentaje_personalizado=round(porcentaje_personalizado, 2),
        porcentaje_buenas_decisiones=round(porcentaje_buenas_decisiones, 2),
        porcentaje_acompaniamiento=round(porcentaje_acompaniamiento, 2),
        porcentaje_comprension=round(porcentaje_comprension, 2),
        porcentaje_relevante=round(porcentaje_relevante, 2),
        porcentaje_usaria_nuevamente=round(porcentaje_usaria_nuevamente, 2),
        satisfaccion_general=satisfaccion
    )

@router.get("/todas", response_model=List[EvaluacionResponse])
def obtener_todas_evaluaciones(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    Obtener todas las evaluaciones (para análisis)
    """
    evaluaciones = db.query(Evaluacion).offset(skip).limit(limit).all()
    return evaluaciones