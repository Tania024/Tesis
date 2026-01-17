# routers/areas.py
# CRUD para gestión de áreas del museo
# Sistema Museo Pumapungo

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import logging

from database import get_db
from models import Area
from schemas import AreaCreate, AreaUpdate, AreaResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# ============================================
# CREATE
# ============================================

@router.post("/", response_model=AreaResponse, status_code=status.HTTP_201_CREATED)
async def crear_area(area: AreaCreate, db: Session = Depends(get_db)):
    """Crear nueva área del museo"""
    # Verificar código único
    if area.codigo and db.query(Area).filter(Area.codigo == area.codigo).first():
        raise HTTPException(status_code=400, detail=f"El código {area.codigo} ya existe")
    
    nueva_area = Area(**area.model_dump())
    db.add(nueva_area)
    db.commit()
    db.refresh(nueva_area)
    
    logger.info(f"✅ Área creada: {nueva_area.codigo} - {nueva_area.nombre}")
    return nueva_area

# ============================================
# READ
# ============================================

@router.get("/", response_model=List[AreaResponse])
async def listar_areas(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    categoria: Optional[str] = None,
    activa: Optional[bool] = True,
    db: Session = Depends(get_db)
):
    """Listar áreas del museo con filtros"""
    query = db.query(Area)
    
    if categoria:
        query = query.filter(Area.categoria == categoria)
    
    if activa is not None:
        query = query.filter(Area.activa == activa)
    
    return query.order_by(Area.orden_recomendado).offset(skip).limit(limit).all()

@router.get("/{area_id}", response_model=AreaResponse)
async def obtener_area(area_id: int, db: Session = Depends(get_db)):
    """Obtener área por ID"""
    area = db.query(Area).filter(Area.id == area_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Área no encontrada")
    return area

@router.get("/codigo/{codigo}", response_model=AreaResponse)
async def obtener_area_por_codigo(codigo: str, db: Session = Depends(get_db)):
    """Obtener área por código (ej: ARQ-01)"""
    area = db.query(Area).filter(Area.codigo == codigo).first()
    if not area:
        raise HTTPException(status_code=404, detail="Código no encontrado")
    return area

# ============================================
# UPDATE
# ============================================

@router.put("/{area_id}", response_model=AreaResponse)
async def actualizar_area(
    area_id: int,
    area_data: AreaUpdate,
    db: Session = Depends(get_db)
):
    """Actualizar información de un área"""
    area = db.query(Area).filter(Area.id == area_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Área no encontrada")
    
    for campo, valor in area_data.model_dump(exclude_unset=True).items():
        setattr(area, campo, valor)
    
    db.commit()
    db.refresh(area)
    logger.info(f"✅ Área actualizada: {area.codigo}")
    return area

# ============================================
# DELETE
# ============================================

@router.delete("/{area_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_area(area_id: int, db: Session = Depends(get_db)):
    """Eliminar área"""
    area = db.query(Area).filter(Area.id == area_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Área no encontrada")
    
    db.delete(area)
    db.commit()
    logger.info(f"✅ Área eliminada: {area.codigo}")

# ============================================
# ENDPOINTS ESPECIALES
# ============================================

@router.get("/categorias/listar")
async def listar_categorias(db: Session = Depends(get_db)):
    """Obtener todas las categorías disponibles"""
    categorias = db.query(Area.categoria, func.count(Area.id)).group_by(Area.categoria).all()
    
    return {
        "categorias": [
            {"nombre": cat, "cantidad_areas": cant}
            for cat, cant in categorias
        ]
    }

@router.get("/recorrido/sugerido")
async def obtener_recorrido_sugerido(db: Session = Depends(get_db)):
    """Obtener recorrido sugerido por orden recomendado"""
    areas = db.query(Area).filter(Area.activa == True).order_by(Area.orden_recomendado).all()
    
    duracion_total = sum(a.tiempo_minimo for a in areas if a.tiempo_minimo)
    
    return {
        "total_areas": len(areas),
        "duracion_estimada_minutos": duracion_total,
        "recorrido": [
            {
                "orden": a.orden_recomendado,
                "codigo": a.codigo,
                "nombre": a.nombre,
                "tiempo_sugerido": a.tiempo_minimo
            }
            for a in areas
        ]
    }

@router.post("/{area_id}/activar", response_model=AreaResponse)
async def activar_area(area_id: int, db: Session = Depends(get_db)):
    """Activar un área desactivada"""
    area = db.query(Area).filter(Area.id == area_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Área no encontrada")
    
    area.activa = True
    db.commit()
    db.refresh(area)
    logger.info(f"✅ Área activada: {area.codigo}")
    return area

@router.post("/{area_id}/desactivar", response_model=AreaResponse)
async def desactivar_area(area_id: int, db: Session = Depends(get_db)):
    """Desactivar un área temporalmente"""
    area = db.query(Area).filter(Area.id == area_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Área no encontrada")
    
    area.activa = False
    db.commit()
    db.refresh(area)
    logger.info(f"✅ Área desactivada: {area.codigo}")
    return area