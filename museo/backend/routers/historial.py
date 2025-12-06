# routers/historial.py
# CRUD para gestión de historial de visitas
# Sistema Museo Pumapungo

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import datetime, date, timedelta
import logging

from database import get_db
from models import HistorialVisita, Visitante, Itinerario
from schemas import (
    HistorialVisitaCreate,
    HistorialVisitaUpdate,
    HistorialVisitaResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()

# ============================================
# CREATE
# ============================================

@router.post("/", response_model=HistorialVisitaResponse, status_code=status.HTTP_201_CREATED)
async def registrar_entrada(visita: HistorialVisitaCreate, db: Session = Depends(get_db)):
    """Registrar entrada de visitante al museo"""
    # Verificar visitante
    visitante = db.query(Visitante).filter(Visitante.id == visita.visitante_id).first()
    if not visitante:
        raise HTTPException(status_code=404, detail="Visitante no encontrado")
    
    # Verificar itinerario si se proporciona
    if visita.itinerario_id:
        itinerario = db.query(Itinerario).filter(Itinerario.id == visita.itinerario_id).first()
        if not itinerario:
            raise HTTPException(status_code=404, detail="Itinerario no encontrado")
    
    nueva_visita = HistorialVisita(**visita.model_dump())
    db.add(nueva_visita)
    db.commit()
    db.refresh(nueva_visita)
    
    logger.info(f"✅ Entrada registrada para visitante {visita.visitante_id}")
    return nueva_visita

# ============================================
# READ
# ============================================

@router.get("/", response_model=List[HistorialVisitaResponse])
async def listar_visitas(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    visitante_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Listar historial de visitas con filtros"""
    query = db.query(HistorialVisita)
    
    if visitante_id:
        query = query.filter(HistorialVisita.visitante_id == visitante_id)
    
    if fecha_desde:
        query = query.filter(HistorialVisita.fecha_visita >= fecha_desde)
    
    if fecha_hasta:
        query = query.filter(HistorialVisita.fecha_visita <= fecha_hasta)
    
    return query.order_by(HistorialVisita.hora_entrada.desc()).offset(skip).limit(limit).all()

@router.get("/{visita_id}", response_model=HistorialVisitaResponse)
async def obtener_visita(visita_id: int, db: Session = Depends(get_db)):
    """Obtener registro de visita específico"""
    visita = db.query(HistorialVisita).filter(HistorialVisita.id == visita_id).first()
    if not visita:
        raise HTTPException(status_code=404, detail="Visita no encontrada")
    return visita

@router.get("/visitante/{visitante_id}/historial")
async def obtener_historial_visitante(
    visitante_id: int,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Obtener historial completo de un visitante"""
    visitante = db.query(Visitante).filter(Visitante.id == visitante_id).first()
    if not visitante:
        raise HTTPException(status_code=404, detail="Visitante no encontrado")
    
    visitas = db.query(HistorialVisita).filter(
        HistorialVisita.visitante_id == visitante_id
    ).order_by(HistorialVisita.hora_entrada.desc()).limit(limit).all()
    
    return {
        "visitante_id": visitante_id,
        "nombre": f"{visitante.nombre} {visitante.apellido}",
        "total_visitas": len(visitas),
        "visitas": visitas
    }

# ============================================
# UPDATE
# ============================================

@router.put("/{visita_id}", response_model=HistorialVisitaResponse)
async def actualizar_visita(
    visita_id: int,
    visita_data: HistorialVisitaUpdate,
    db: Session = Depends(get_db)
):
    """Actualizar registro de visita (registrar salida, feedback, etc.)"""
    visita = db.query(HistorialVisita).filter(HistorialVisita.id == visita_id).first()
    if not visita:
        raise HTTPException(status_code=404, detail="Visita no encontrada")
    
    for campo, valor in visita_data.model_dump(exclude_unset=True).items():
        setattr(visita, campo, valor)
    
    # Calcular duración si se registra salida
    if visita.hora_salida and visita.hora_entrada:
        duracion = (visita.hora_salida - visita.hora_entrada).total_seconds() / 60
        visita.duracion_total = int(duracion)
    
    db.commit()
    db.refresh(visita)
    logger.info(f"✅ Visita actualizada: {visita_id}")
    return visita

# ============================================
# DELETE
# ============================================

@router.delete("/{visita_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_visita(visita_id: int, db: Session = Depends(get_db)):
    """Eliminar registro de visita"""
    visita = db.query(HistorialVisita).filter(HistorialVisita.id == visita_id).first()
    if not visita:
        raise HTTPException(status_code=404, detail="Visita no encontrada")
    
    db.delete(visita)
    db.commit()
    logger.info(f"✅ Visita eliminada: {visita_id}")

# ============================================
# CONTROL DE VISITA
# ============================================

@router.post("/{visita_id}/registrar-salida")
async def registrar_salida(
    visita_id: int,
    satisfaccion: Optional[int] = Query(None, ge=1, le=5),
    comentarios: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Registrar salida del visitante"""
    visita = db.query(HistorialVisita).filter(HistorialVisita.id == visita_id).first()
    if not visita:
        raise HTTPException(status_code=404, detail="Visita no encontrada")
    
    if visita.hora_salida:
        raise HTTPException(status_code=400, detail="La salida ya fue registrada")
    
    visita.hora_salida = datetime.now()
    
    # Calcular duración
    duracion = (visita.hora_salida - visita.hora_entrada).total_seconds() / 60
    visita.duracion_total = int(duracion)
    
    # Registrar feedback
    if satisfaccion:
        visita.satisfaccion_general = satisfaccion
    if comentarios:
        visita.comentarios = comentarios
    
    db.commit()
    db.refresh(visita)
    
    # Actualizar contador del visitante
    visitante = db.query(Visitante).filter(Visitante.id == visita.visitante_id).first()
    if visitante:
        visitante.total_visitas += 1
        visitante.ultima_visita = visita.hora_salida
        db.commit()
    
    logger.info(f"✅ Salida registrada para visita {visita_id} - Duración: {visita.duracion_total} min")
    
    return {
        "mensaje": "Salida registrada exitosamente",
        "duracion_minutos": visita.duracion_total,
        "hora_salida": visita.hora_salida
    }

# ============================================
# ESTADÍSTICAS Y REPORTES
# ============================================

@router.get("/estadisticas/hoy")
async def estadisticas_hoy(db: Session = Depends(get_db)):
    """Estadísticas del día actual"""
    hoy = date.today()
    
    visitas_hoy = db.query(HistorialVisita).filter(
        HistorialVisita.fecha_visita == hoy
    ).all()
    
    visitas_activas = sum(1 for v in visitas_hoy if not v.hora_salida)
    visitas_completadas = sum(1 for v in visitas_hoy if v.hora_salida)
    
    duracion_promedio = None
    if visitas_completadas > 0:
        duraciones = [v.duracion_total for v in visitas_hoy if v.duracion_total]
        if duraciones:
            duracion_promedio = sum(duraciones) / len(duraciones)
    
    return {
        "fecha": hoy,
        "total_visitas": len(visitas_hoy),
        "visitas_activas": visitas_activas,
        "visitas_completadas": visitas_completadas,
        "duracion_promedio_minutos": round(duracion_promedio, 0) if duracion_promedio else None
    }

@router.get("/estadisticas/semana")
async def estadisticas_semana(db: Session = Depends(get_db)):
    """Estadísticas de la última semana"""
    hoy = date.today()
    hace_7_dias = hoy - timedelta(days=7)
    
    visitas = db.query(HistorialVisita).filter(
        and_(
            HistorialVisita.fecha_visita >= hace_7_dias,
            HistorialVisita.fecha_visita <= hoy
        )
    ).all()
    
    # Agrupar por día
    por_dia = {}
    for visita in visitas:
        dia = visita.fecha_visita.strftime("%Y-%m-%d")
        por_dia[dia] = por_dia.get(dia, 0) + 1
    
    satisfaccion_promedio = None
    satisfacciones = [v.satisfaccion_general for v in visitas if v.satisfaccion_general]
    if satisfacciones:
        satisfaccion_promedio = sum(satisfacciones) / len(satisfacciones)
    
    return {
        "periodo": f"{hace_7_dias} a {hoy}",
        "total_visitas": len(visitas),
        "visitas_por_dia": por_dia,
        "satisfaccion_promedio": round(satisfaccion_promedio, 2) if satisfaccion_promedio else None
    }

@router.get("/estadisticas/horas-pico")
async def horas_pico(db: Session = Depends(get_db)):
    """Identificar horas pico de visitas"""
    # Obtener últimas 30 visitas
    visitas = db.query(HistorialVisita).order_by(
        HistorialVisita.hora_entrada.desc()
    ).limit(100).all()
    
    horas = {}
    for visita in visitas:
        hora = visita.hora_entrada.hour
        horas[hora] = horas.get(hora, 0) + 1
    
    # Ordenar por cantidad
    horas_ordenadas = sorted(horas.items(), key=lambda x: x[1], reverse=True)
    
    return {
        "horas_mas_concurridas": [
            {"hora": f"{h}:00", "cantidad": c}
            for h, c in horas_ordenadas[:5]
        ]
    }