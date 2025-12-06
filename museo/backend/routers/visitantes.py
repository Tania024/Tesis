# routers/visitantes.py
# CRUD para gestión de visitantes
# Sistema Museo Pumapungo

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
import logging

from database import get_db
from models import Visitante
from schemas import (
    VisitanteCreate, 
    VisitanteUpdate, 
    VisitanteResponse,
    VisitanteConPerfil
)

logger = logging.getLogger(__name__)
router = APIRouter()

# ============================================
# CREATE
# ============================================

@router.post("/", response_model=VisitanteResponse, status_code=status.HTTP_201_CREATED)
async def crear_visitante(visitante: VisitanteCreate, db: Session = Depends(get_db)):
    """Crear un nuevo visitante (código de visita se genera automáticamente)"""
    try:
        # Verificar email único
        if db.query(Visitante).filter(Visitante.email == visitante.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El email {visitante.email} ya está registrado"
            )
        
        nuevo_visitante = Visitante(**visitante.model_dump())
        db.add(nuevo_visitante)
        db.commit()
        db.refresh(nuevo_visitante)
        
        logger.info(f"✅ Visitante creado: {nuevo_visitante.codigo_visita}")
        return nuevo_visitante
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error al crear visitante: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# READ
# ============================================

@router.get("/", response_model=List[VisitanteResponse])
async def listar_visitantes(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    buscar: Optional[str] = None,
    tipo_visitante: Optional[str] = None,
    activo: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Listar visitantes con paginación y filtros"""
    query = db.query(Visitante)
    
    if buscar:
        patron = f"%{buscar}%"
        query = query.filter(or_(
            Visitante.nombre.ilike(patron),
            Visitante.apellido.ilike(patron),
            Visitante.email.ilike(patron),
            Visitante.codigo_visita.ilike(patron)
        ))
    
    if tipo_visitante:
        query = query.filter(Visitante.tipo_visitante == tipo_visitante)
    
    if activo is not None:
        query = query.filter(Visitante.activo == activo)
    
    return query.order_by(Visitante.fecha_registro.desc()).offset(skip).limit(limit).all()

@router.get("/{visitante_id}", response_model=VisitanteConPerfil)
async def obtener_visitante(visitante_id: int, db: Session = Depends(get_db)):
    """Obtener visitante por ID (incluye perfil si existe)"""
    visitante = db.query(Visitante).filter(Visitante.id == visitante_id).first()
    if not visitante:
        raise HTTPException(status_code=404, detail="Visitante no encontrado")
    return visitante

@router.get("/codigo/{codigo_visita}", response_model=VisitanteResponse)
async def obtener_por_codigo(codigo_visita: str, db: Session = Depends(get_db)):
    """Buscar por código de visita (útil para QR)"""
    visitante = db.query(Visitante).filter(Visitante.codigo_visita == codigo_visita).first()
    if not visitante:
        raise HTTPException(status_code=404, detail="Código no encontrado")
    return visitante

@router.get("/email/{email}", response_model=VisitanteResponse)
async def obtener_por_email(email: str, db: Session = Depends(get_db)):
    """Buscar por email"""
    visitante = db.query(Visitante).filter(Visitante.email == email).first()
    if not visitante:
        raise HTTPException(status_code=404, detail="Email no encontrado")
    return visitante

# ============================================
# UPDATE
# ============================================

@router.put("/{visitante_id}", response_model=VisitanteResponse)
async def actualizar_visitante(
    visitante_id: int, 
    visitante_data: VisitanteUpdate, 
    db: Session = Depends(get_db)
):
    """Actualizar información del visitante"""
    visitante = db.query(Visitante).filter(Visitante.id == visitante_id).first()
    if not visitante:
        raise HTTPException(status_code=404, detail="Visitante no encontrado")
    
    # Verificar email único si se actualiza
    if visitante_data.email and visitante_data.email != visitante.email:
        if db.query(Visitante).filter(
            Visitante.email == visitante_data.email,
            Visitante.id != visitante_id
        ).first():
            raise HTTPException(status_code=400, detail="Email ya registrado")
    
    for campo, valor in visitante_data.model_dump(exclude_unset=True).items():
        setattr(visitante, campo, valor)
    
    db.commit()
    db.refresh(visitante)
    logger.info(f"✅ Visitante actualizado: {visitante.codigo_visita}")
    return visitante

# ============================================
# DELETE
# ============================================

@router.delete("/{visitante_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_visitante(visitante_id: int, db: Session = Depends(get_db)):
    """Eliminar visitante (CASCADE elimina perfil, itinerarios, etc.)"""
    visitante = db.query(Visitante).filter(Visitante.id == visitante_id).first()
    if not visitante:
        raise HTTPException(status_code=404, detail="Visitante no encontrado")
    
    codigo = visitante.codigo_visita
    db.delete(visitante)
    db.commit()
    logger.info(f"✅ Visitante eliminado: {codigo}")

# ============================================
# ESTADÍSTICAS
# ============================================

@router.get("/estadisticas/resumen")
async def estadisticas_visitantes(db: Session = Depends(get_db)):
    """Estadísticas generales de visitantes"""
    total = db.query(Visitante).count()
    activos = db.query(Visitante).filter(Visitante.activo == True).count()
    
    por_tipo = db.query(
        Visitante.tipo_visitante,
        func.count(Visitante.id).label('cantidad')
    ).group_by(Visitante.tipo_visitante).all()
    
    por_entrada = db.query(
        Visitante.tipo_entrada,
        func.count(Visitante.id).label('cantidad')
    ).group_by(Visitante.tipo_entrada).all()
    
    return {
        "total_visitantes": total,
        "visitantes_activos": activos,
        "por_tipo_visitante": {tipo: cant for tipo, cant in por_tipo if tipo},
        "por_tipo_entrada": {tipo: cant for tipo, cant in por_entrada if tipo},
        "total_visitas_realizadas": db.query(func.sum(Visitante.total_visitas)).scalar() or 0
    }

@router.post("/{visitante_id}/desactivar", response_model=VisitanteResponse)
async def desactivar_visitante(visitante_id: int, db: Session = Depends(get_db)):
    """Desactivar visitante (soft delete)"""
    visitante = db.query(Visitante).filter(Visitante.id == visitante_id).first()
    if not visitante:
        raise HTTPException(status_code=404, detail="Visitante no encontrado")
    
    visitante.activo = False
    db.commit()
    db.refresh(visitante)
    logger.info(f"✅ Visitante desactivado: {visitante.codigo_visita}")
    return visitante