# routers/perfiles.py
# CRUD para gestión de perfiles de visitantes
# Sistema Museo Pumapungo

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from database import get_db
from models import Perfil, Visitante
from schemas import PerfilCreate, PerfilUpdate, PerfilResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# ============================================
# CREATE
# ============================================

@router.post("/", response_model=PerfilResponse, status_code=status.HTTP_201_CREATED)
async def crear_perfil(perfil: PerfilCreate, db: Session = Depends(get_db)):
    """Crear perfil de un visitante"""
    # Verificar que el visitante existe
    visitante = db.query(Visitante).filter(Visitante.id == perfil.visitante_id).first()
    if not visitante:
        raise HTTPException(status_code=404, detail="Visitante no encontrado")
    
    # Verificar que no tenga perfil ya
    if db.query(Perfil).filter(Perfil.visitante_id == perfil.visitante_id).first():
        raise HTTPException(status_code=400, detail="El visitante ya tiene un perfil")
    
    nuevo_perfil = Perfil(**perfil.model_dump())
    db.add(nuevo_perfil)
    db.commit()
    db.refresh(nuevo_perfil)
    
    logger.info(f"✅ Perfil creado para visitante {perfil.visitante_id}")
    return nuevo_perfil

# ============================================
# READ
# ============================================

@router.get("/", response_model=List[PerfilResponse])
async def listar_perfiles(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Listar todos los perfiles con paginación"""
    return db.query(Perfil).offset(skip).limit(limit).all()

@router.get("/{perfil_id}", response_model=PerfilResponse)
async def obtener_perfil(perfil_id: int, db: Session = Depends(get_db)):
    """Obtener perfil por ID"""
    perfil = db.query(Perfil).filter(Perfil.id == perfil_id).first()
    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    return perfil

@router.get("/visitante/{visitante_id}", response_model=PerfilResponse)
async def obtener_perfil_por_visitante(visitante_id: int, db: Session = Depends(get_db)):
    """Obtener perfil de un visitante específico"""
    perfil = db.query(Perfil).filter(Perfil.visitante_id == visitante_id).first()
    if not perfil:
        raise HTTPException(status_code=404, detail="El visitante no tiene perfil")
    return perfil

# ============================================
# UPDATE
# ============================================

@router.put("/{perfil_id}", response_model=PerfilResponse)
async def actualizar_perfil(
    perfil_id: int,
    perfil_data: PerfilUpdate,
    db: Session = Depends(get_db)
):
    """Actualizar perfil existente"""
    perfil = db.query(Perfil).filter(Perfil.id == perfil_id).first()
    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    
    for campo, valor in perfil_data.model_dump(exclude_unset=True).items():
        setattr(perfil, campo, valor)
    
    db.commit()
    db.refresh(perfil)
    logger.info(f"✅ Perfil actualizado: {perfil_id}")
    return perfil

# ============================================
# DELETE
# ============================================

@router.delete("/{perfil_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_perfil(perfil_id: int, db: Session = Depends(get_db)):
    """Eliminar perfil"""
    perfil = db.query(Perfil).filter(Perfil.id == perfil_id).first()
    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    
    db.delete(perfil)
    db.commit()
    logger.info(f"✅ Perfil eliminado: {perfil_id}")

# ============================================
# ENDPOINTS ESPECIALES
# ============================================

@router.get("/buscar/intereses")
async def buscar_por_intereses(
    interes: str = Query(..., description="Interés a buscar"),
    db: Session = Depends(get_db)
):
    """Buscar perfiles que contengan un interés específico"""
    # Usar operador ANY de PostgreSQL para buscar en array
    perfiles = db.query(Perfil).filter(
        Perfil.intereses.contains([interes])
    ).all()
    
    return {
        "interes_buscado": interes,
        "total_encontrados": len(perfiles),
        "perfiles": [{"id": p.id, "visitante_id": p.visitante_id} for p in perfiles]
    }

@router.get("/estadisticas/intereses")
async def estadisticas_intereses(db: Session = Depends(get_db)):
    """Estadísticas de intereses más populares"""
    perfiles = db.query(Perfil).all()
    
    # Contar intereses
    contador_intereses = {}
    for perfil in perfiles:
        if perfil.intereses:
            for interes in perfil.intereses:
                contador_intereses[interes] = contador_intereses.get(interes, 0) + 1
    
    # Ordenar por popularidad
    intereses_ordenados = sorted(
        contador_intereses.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    return {
        "total_perfiles": len(perfiles),
        "intereses_populares": [
            {"interes": interes, "cantidad": cant}
            for interes, cant in intereses_ordenados
        ]
    }