# routers/historial.py
# CRUD para gestión de historial de visitas
# Sistema Museo Pumapungo
# ✅ MODIFICADO PARA ADMINPAGE

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract, desc
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
# ESTADÍSTICAS PARA ADMINPAGE
# ============================================

@router.get("/estadisticas/hoy")
async def estadisticas_hoy(db: Session = Depends(get_db)):
    """
    Estadísticas del día actual para AdminPage
    ✅ MODIFICADO: Devuelve formato esperado por AdminPage
    """
    try:
        hoy = date.today()
        
        # Visitantes únicos de hoy
        visitantes_hoy = db.query(
            func.count(func.distinct(HistorialVisita.visitante_id))
        ).filter(
            HistorialVisita.fecha_visita == hoy
        ).scalar() or 0
        
        # Itinerarios activos hoy
        itinerarios_activos = db.query(func.count(Itinerario.id)).filter(
            Itinerario.estado == 'activo',
            func.date(Itinerario.fecha_inicio) == hoy
        ).scalar() or 0
        
        # Hora promedio de entrada (calculada de visitas de hoy)
        hora_entrada_promedio = None
        visitas_hoy = db.query(HistorialVisita.hora_entrada).filter(
            HistorialVisita.fecha_visita == hoy,
            HistorialVisita.hora_entrada.isnot(None)
        ).all()
        
        if visitas_hoy:
            horas = [v.hora_entrada.hour + v.hora_entrada.minute/60.0 for v in visitas_hoy if v.hora_entrada]
            if horas:
                promedio_decimal = sum(horas) / len(horas)
                hora = int(promedio_decimal)
                minuto = int((promedio_decimal - hora) * 60)
                hora_entrada_promedio = f"{hora:02d}:{minuto:02d}"
        
        # Duración promedio de visitas hoy
        duracion_promedio = db.query(func.avg(HistorialVisita.duracion_total)).filter(
            HistorialVisita.fecha_visita == hoy,
            HistorialVisita.duracion_total.isnot(None)
        ).scalar() or 0
        
        # ✅ FORMATO QUE ADMINPAGE ESPERA
        return {
            "visitantes_hoy": visitantes_hoy,
            "itinerarios_activos": itinerarios_activos,
            "hora_entrada_promedio": hora_entrada_promedio,
            "duracion_promedio_minutos": round(float(duracion_promedio), 2) if duracion_promedio else 0
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de hoy: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al obtener estadísticas del día"
        )


@router.get("/estadisticas/horas-pico")
async def horas_pico(db: Session = Depends(get_db)):
    """
    Identificar horas pico de visitas para AdminPage
    ✅ MODIFICADO: Devuelve array directo con "visitantes" en lugar de objeto
    """
    try:
        # Obtener las 5 horas con más visitas
        horas_pico = db.query(
            extract('hour', HistorialVisita.hora_entrada).label('hora'),
            func.count(HistorialVisita.id).label('visitantes')
        ).filter(
            HistorialVisita.hora_entrada.isnot(None)
        ).group_by(
            extract('hour', HistorialVisita.hora_entrada)
        ).order_by(
            desc('visitantes')
        ).limit(5).all()
        
        # ✅ DEVOLVER ARRAY DIRECTO (no objeto)
        # ✅ USAR "visitantes" (no "cantidad")
        resultado = [
            {
                "hora": f"{int(hora):02d}:00",
                "visitantes": visitantes
            }
            for hora, visitantes in horas_pico
        ]
        
        return resultado
        
    except Exception as e:
        logger.error(f"Error obteniendo horas pico: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al obtener horas pico"
        )


# ============================================
# ESTADÍSTICAS ADICIONALES (ORIGINALES)
# ============================================

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


@router.get("/estadisticas/mes")
async def estadisticas_mes(db: Session = Depends(get_db)):
    """Estadísticas del último mes"""
    hoy = date.today()
    hace_30_dias = hoy - timedelta(days=30)
    
    visitas = db.query(HistorialVisita).filter(
        and_(
            HistorialVisita.fecha_visita >= hace_30_dias,
            HistorialVisita.fecha_visita <= hoy
        )
    ).all()
    
    # Calcular estadísticas
    total_visitas = len(visitas)
    
    # Visitantes únicos
    visitantes_unicos = len(set(v.visitante_id for v in visitas))
    
    # Satisfacción promedio
    satisfaccion_promedio = None
    satisfacciones = [v.satisfaccion_general for v in visitas if v.satisfaccion_general]
    if satisfacciones:
        satisfaccion_promedio = sum(satisfacciones) / len(satisfacciones)
    
    # Duración promedio
    duracion_promedio = None
    duraciones = [v.duracion_total for v in visitas if v.duracion_total]
    if duraciones:
        duracion_promedio = sum(duraciones) / len(duraciones)
    
    return {
        "periodo": f"{hace_30_dias} a {hoy}",
        "total_visitas": total_visitas,
        "visitantes_unicos": visitantes_unicos,
        "satisfaccion_promedio": round(satisfaccion_promedio, 2) if satisfaccion_promedio else None,
        "duracion_promedio_minutos": round(duracion_promedio, 2) if duracion_promedio else None
    }