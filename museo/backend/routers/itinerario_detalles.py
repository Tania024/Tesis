# routers/itinerario_detalles.py
# CRUD para gestión de detalles de itinerarios
# Sistema Museo Pumapungo

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
import logging
from datetime import datetime

from database import get_db
from models import ItinerarioDetalle, Itinerario, Area
from schemas import (
    ItinerarioDetalleCreate,
    ItinerarioDetalleUpdate,
    ItinerarioDetalleResponse,
    ItinerarioDetalleConArea
)

logger = logging.getLogger(__name__)
router = APIRouter()

# ============================================
# CREATE
# ============================================

@router.post("/", response_model=ItinerarioDetalleResponse, status_code=status.HTTP_201_CREATED)
async def crear_detalle(detalle: ItinerarioDetalleCreate, db: Session = Depends(get_db)):
    """Agregar detalle a un itinerario"""
    # Verificar que el itinerario existe
    itinerario = db.query(Itinerario).filter(Itinerario.id == detalle.itinerario_id).first()
    if not itinerario:
        raise HTTPException(status_code=404, detail="Itinerario no encontrado")
    
    # Verificar que el área existe
    area = db.query(Area).filter(Area.id == detalle.area_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Área no encontrada")
    
    nuevo_detalle = ItinerarioDetalle(**detalle.model_dump())
    db.add(nuevo_detalle)
    db.commit()
    db.refresh(nuevo_detalle)
    
    logger.info(f"✅ Detalle creado para itinerario {detalle.itinerario_id}")
    return nuevo_detalle

# ============================================
# READ
# ============================================

@router.get("/itinerario/{itinerario_id}", response_model=List[ItinerarioDetalleConArea])
async def listar_detalles_itinerario(
    itinerario_id: int,
    db: Session = Depends(get_db)
):
    """Obtener todos los detalles de un itinerario ordenados"""
    detalles = db.query(ItinerarioDetalle).filter(
        ItinerarioDetalle.itinerario_id == itinerario_id
    ).order_by(ItinerarioDetalle.orden).all()
    
    if not detalles:
        raise HTTPException(status_code=404, detail="No se encontraron detalles")
    
    return detalles

@router.get("/{detalle_id}", response_model=ItinerarioDetalleResponse)
async def obtener_detalle(detalle_id: int, db: Session = Depends(get_db)):
    """Obtener un detalle específico"""
    detalle = db.query(ItinerarioDetalle).filter(ItinerarioDetalle.id == detalle_id).first()
    if not detalle:
        raise HTTPException(status_code=404, detail="Detalle no encontrado")
    return detalle

# ============================================
# UPDATE
# ============================================

@router.put("/{detalle_id}", response_model=ItinerarioDetalleResponse)
async def actualizar_detalle(
    detalle_id: int,
    detalle_data: ItinerarioDetalleUpdate,
    db: Session = Depends(get_db)
):
    """Actualizar detalle (marca como visitado, tiempo real, etc.)"""
    detalle = db.query(ItinerarioDetalle).filter(ItinerarioDetalle.id == detalle_id).first()
    if not detalle:
        raise HTTPException(status_code=404, detail="Detalle no encontrado")
    
    for campo, valor in detalle_data.model_dump(exclude_unset=True).items():
        setattr(detalle, campo, valor)
    
    db.commit()
    db.refresh(detalle)
    logger.info(f"✅ Detalle actualizado: {detalle_id}")
    return detalle

# ============================================
# DELETE
# ============================================

@router.delete("/{detalle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_detalle(detalle_id: int, db: Session = Depends(get_db)):
    """Eliminar detalle de itinerario"""
    detalle = db.query(ItinerarioDetalle).filter(ItinerarioDetalle.id == detalle_id).first()
    if not detalle:
        raise HTTPException(status_code=404, detail="Detalle no encontrado")
    
    db.delete(detalle)
    db.commit()
    logger.info(f"✅ Detalle eliminado: {detalle_id}")

# ============================================
# CONTROL DE VISITA
# ============================================

@router.post("/{detalle_id}/iniciar")
async def iniciar_visita_area(detalle_id: int, db: Session = Depends(get_db)):
    """Marcar inicio de visita a un área"""
    detalle = db.query(ItinerarioDetalle).filter(ItinerarioDetalle.id == detalle_id).first()
    if not detalle:
        raise HTTPException(status_code=404, detail="Detalle no encontrado")
    
    detalle.hora_inicio = datetime.now()
    db.commit()
    db.refresh(detalle)
    
    logger.info(f"✅ Visita iniciada en área: {detalle.area_id}")
    return {"mensaje": "Visita iniciada", "hora_inicio": detalle.hora_inicio}

@router.post("/{detalle_id}/completar")
async def completar_visita_area(detalle_id: int, db: Session = Depends(get_db)):
    """Marcar área como visitada y calcular tiempo real"""
    detalle = db.query(ItinerarioDetalle).filter(ItinerarioDetalle.id == detalle_id).first()
    if not detalle:
        raise HTTPException(status_code=404, detail="Detalle no encontrado")
    
    if not detalle.hora_inicio:
        raise HTTPException(status_code=400, detail="No se ha iniciado la visita")
    
    detalle.hora_fin = datetime.now()
    detalle.visitado = True
    
    # Calcular tiempo real en minutos
    duracion = (detalle.hora_fin - detalle.hora_inicio).total_seconds() / 60
    detalle.tiempo_real = int(duracion)
    
    db.commit()
    db.refresh(detalle)
    
    logger.info(f"✅ Visita completada en área: {detalle.area_id} ({detalle.tiempo_real} min)")
    return {
        "mensaje": "Visita completada",
        "tiempo_real_minutos": detalle.tiempo_real,
        "hora_fin": detalle.hora_fin
    }

@router.post("/{detalle_id}/omitir")
async def omitir_area(detalle_id: int, db: Session = Depends(get_db)):
    """Marcar área como omitida (skip)"""
    detalle = db.query(ItinerarioDetalle).filter(ItinerarioDetalle.id == detalle_id).first()
    if not detalle:
        raise HTTPException(status_code=404, detail="Detalle no encontrado")
    
    detalle.skip = True
    db.commit()
    db.refresh(detalle)
    
    logger.info(f"⏭️ Área omitida: {detalle.area_id}")
    return {"mensaje": "Área omitida"}

# ============================================
# PROGRESO
# ============================================

@router.get("/itinerario/{itinerario_id}/progreso")
async def obtener_progreso(itinerario_id: int, db: Session = Depends(get_db)):
    """Obtener progreso del itinerario"""
    detalles = db.query(ItinerarioDetalle).filter(
        ItinerarioDetalle.itinerario_id == itinerario_id
    ).all()
    
    if not detalles:
        raise HTTPException(status_code=404, detail="Itinerario sin detalles")
    
    total = len(detalles)
    visitados = sum(1 for d in detalles if d.visitado)
    omitidos = sum(1 for d in detalles if d.skip)
    pendientes = total - visitados - omitidos
    
    porcentaje = (visitados / total * 100) if total > 0 else 0
    
    return {
        "total_areas": total,
        "visitadas": visitados,
        "omitidas": omitidos,
        "pendientes": pendientes,
        "porcentaje_completado": round(porcentaje, 1)
    }



@router.patch("/{detalle_id}/reactivar", response_model=ItinerarioDetalleResponse)
def reactivar_area(
    detalle_id: int,
    db: Session = Depends(get_db)
):
    """
    Reactivar un área que fue saltada (quitar el skip)
    """
    detalle = db.query(ItinerarioDetalle).filter(
        ItinerarioDetalle.id == detalle_id
    ).first()
    
    if not detalle:
        raise HTTPException(status_code=404, detail="Detalle no encontrado")
    
    # Reactivar el área (quitar skip y visitado)
    detalle.skip = False
    detalle.visitado = False
    detalle.hora_fin = None
    
    db.commit()
    db.refresh(detalle)
    
    logger.info(f"✅ Área {detalle_id} reactivada")
    
    return detalle


@router.patch("/{detalle_id}/desmarcar", response_model=ItinerarioDetalleResponse)
def desmarcar_area(
    detalle_id: int,
    db: Session = Depends(get_db)
):
    """
    Desmarcar un área como visitada (volver a estado pendiente)
    """
    detalle = db.query(ItinerarioDetalle).filter(
        ItinerarioDetalle.id == detalle_id
    ).first()
    
    if not detalle:
        raise HTTPException(status_code=404, detail="Detalle no encontrado")
    
    # Desmarcar como visitado
    detalle.visitado = False
    detalle.hora_fin = None
    detalle.tiempo_real = None
    
    db.commit()
    db.refresh(detalle)
    
    logger.info(f"✅ Área {detalle_id} desmarcada")
    
    return detalle