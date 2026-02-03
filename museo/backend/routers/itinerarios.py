# routers/itinerarios.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import logging
from datetime import datetime, timezone

from database import get_db
from models import Itinerario, Perfil, Visitante, Area, ItinerarioDetalle
from schemas import (
    ItinerarioCreate, 
    ItinerarioUpdate, 
    ItinerarioResponse,
    ItinerarioCompleto,
    SolicitudItinerario,
    ItinerarioDetalleResponse,
    ItinerarioDetalleUpdate
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
        
        # 🔥 CAMBIO: Si no hay límite de tiempo, incluir TODAS las áreas
        # Si hay límite de tiempo, filtrar por categorías de interés
        if solicitud.tiempo_disponible is not None and solicitud.intereses:
            query = query.filter(Area.categoria.in_(solicitud.intereses))
            logger.info(f"🔍 Filtrando por categorías: {solicitud.intereses}")
        elif solicitud.tiempo_disponible is None:
            logger.info(f"♾️ Sin límite de tiempo: incluyendo TODAS las áreas del museo")
        
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
            },
            tipo_entrada=solicitud.tipo_entrada,
            acompañantes=solicitud.acompañantes,
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
            
            def parse_json_field(value):
                """Convierte string JSON a lista Python"""
                if value is None:
                    return None
                if isinstance(value, str):
                    try:
                        import json
                        return json.loads(value)
                    except:
                        return None
                return value  # Ya es una lista
            
            detalle = ItinerarioDetalle(
                itinerario_id=nuevo_itinerario.id,
                area_id=area.id,
                orden=area_ia["orden"],
                tiempo_sugerido=area_ia["tiempo_sugerido"],
                introduccion=area_ia.get("introduccion", ""),
                recomendacion=area_ia.get("recomendacion", ""),
                historia_contextual=area_ia.get("historia_contextual", None),
                # 🔥 CONVERTIR strings JSON a listas
                datos_curiosos=parse_json_field(area_ia.get("datos_curiosos", None)),
                que_observar=parse_json_field(area_ia.get("que_observar", None)),
                puntos_clave=area_ia.get("puntos_clave", [])
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
# READ - ENDPOINTS ESPECÍFICOS PRIMERO
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

# ============================================
# ESTADÍSTICAS - ANTES DE /{itinerario_id}
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


@router.get("/estadisticas")
async def obtener_estadisticas_itinerarios(db: Session = Depends(get_db)):
    """
    Obtiene estadísticas generales de itinerarios para el panel administrativo
    ✅ CORREGIDO: Endpoint movido antes de /{itinerario_id}
    """
    try:
        logger.info("📊 Iniciando cálculo de estadísticas de itinerarios...")
        
        # Total de itinerarios
        total_itinerarios_raw = db.query(func.count(Itinerario.id)).scalar()
        total_itinerarios = int(total_itinerarios_raw) if total_itinerarios_raw else 0
        logger.info(f"   Total itinerarios: {total_itinerarios}")
        
        # Itinerarios por estado
        itinerarios_por_estado = {}
        try:
            estados_query = db.query(
                Itinerario.estado,
                func.count(Itinerario.id).label('cantidad')
            ).group_by(Itinerario.estado).all()
            
            for estado, cantidad in estados_query:
                if estado:
                    itinerarios_por_estado[str(estado)] = int(cantidad)
            
            logger.info(f"   Itinerarios por estado: {itinerarios_por_estado}")
        except Exception as e:
            logger.error(f"   ⚠️ Error calculando por estado: {e}")
            itinerarios_por_estado = {}
        
        # Itinerarios completados
        try:
            completados_raw = db.query(func.count(Itinerario.id)).filter(
                Itinerario.estado == 'completado'
            ).scalar()
            completados = int(completados_raw) if completados_raw else 0
            logger.info(f"   Completados: {completados}")
        except Exception as e:
            logger.error(f"   ⚠️ Error calculando completados: {e}")
            completados = 0
        
        # Itinerarios en progreso
        try:
            en_progreso_raw = db.query(func.count(Itinerario.id)).filter(
                Itinerario.estado == 'activo'
            ).scalar()
            en_progreso = int(en_progreso_raw) if en_progreso_raw else 0
            logger.info(f"   En progreso: {en_progreso}")
        except Exception as e:
            logger.error(f"   ⚠️ Error calculando en progreso: {e}")
            en_progreso = 0
        
        # Duración promedio
        try:
            duracion_promedio_raw = db.query(
                func.avg(Itinerario.duracion_total)
            ).scalar()
            
            if duracion_promedio_raw is not None:
                duracion_promedio = round(float(duracion_promedio_raw), 2)
            else:
                duracion_promedio = 0.0
            
            logger.info(f"   Duración promedio: {duracion_promedio}")
        except Exception as e:
            logger.error(f"   ⚠️ Error calculando duración promedio: {e}")
            duracion_promedio = 0.0
        
        # Puntuación promedio
        try:
            puntuacion_promedio_raw = db.query(
                func.avg(Itinerario.puntuacion)
            ).filter(
                Itinerario.puntuacion.isnot(None)
            ).scalar()
            
            if puntuacion_promedio_raw is not None:
                puntuacion_promedio = round(float(puntuacion_promedio_raw), 2)
            else:
                puntuacion_promedio = None
            
            logger.info(f"   Puntuación promedio: {puntuacion_promedio}")
        except Exception as e:
            logger.error(f"   ⚠️ Error calculando puntuación: {e}")
            puntuacion_promedio = None
        
        # Generados con IA (todos los itinerarios usan IA)
        generados_con_ia = total_itinerarios
        
        # Construir respuesta
        resultado = {
            "total_itinerarios": total_itinerarios,
            "itinerarios_por_estado": itinerarios_por_estado,
            "completados": completados,
            "en_progreso": en_progreso,
            "duracion_promedio_minutos": duracion_promedio,
            "puntuacion_promedio": puntuacion_promedio,
            "generados_con_ia": generados_con_ia
        }
        
        logger.info(f"✅ Estadísticas de itinerarios calculadas: {resultado}")
        return resultado
        
    except Exception as e:
        logger.error(f"❌ ERROR CRÍTICO en estadísticas de itinerarios: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener estadísticas de itinerarios: {str(e)}"
        )


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
    
    # 🔥 AGREGAR: Conteo de áreas para cada itinerario
    resultado = []
    for itinerario in itinerarios:
        itinerario_dict = {
            "id": itinerario.id,
            "perfil_id": itinerario.perfil_id,
            "titulo": itinerario.titulo,
            "descripcion": itinerario.descripcion,
            "duracion_total": itinerario.duracion_total,
            "estado": itinerario.estado,
            "fecha_generacion": itinerario.fecha_generacion,
            "fecha_inicio": itinerario.fecha_inicio,
            "fecha_fin": itinerario.fecha_fin,
            "puntuacion": itinerario.puntuacion,
            "modelo_ia_usado": itinerario.modelo_ia_usado,
            "tipo_entrada": itinerario.tipo_entrada,
            "acompañantes": itinerario.acompañantes,
            # 🔥 NUEVO: Conteo de áreas
            "numero_areas": len(itinerario.detalles) if itinerario.detalles else 0,
            # Incluir detalles si existen
            "detalles": itinerario.detalles
        }
        resultado.append(itinerario_dict)
    
    return {"total": len(resultado), "itinerarios": resultado}
# ============================================
# READ - ENDPOINT GENÉRICO AL FINAL
# ============================================

@router.get("/{itinerario_id}", response_model=ItinerarioCompleto)
async def obtener_itinerario(itinerario_id: int, db: Session = Depends(get_db)):
    """Obtener itinerario completo con sus detalles"""
    itinerario = db.query(Itinerario).filter(Itinerario.id == itinerario_id).first()
    if not itinerario:
        raise HTTPException(status_code=404, detail="Itinerario no encontrado")
    return itinerario


# ============================================
# UPDATE
# ============================================

@router.put("/{itinerario_id}", response_model=ItinerarioResponse)
async def actualizar_itinerario(
    itinerario_id: int,
    itinerario_update: ItinerarioUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualizar un itinerario existente.
    Útil para marcar como completado, agregar puntuación, etc.
    """
    
    # Buscar itinerario
    itinerario = db.query(Itinerario).filter(Itinerario.id == itinerario_id).first()
    
    if not itinerario:
        raise HTTPException(
            status_code=404,
            detail=f"Itinerario {itinerario_id} no encontrado"
        )
    
    # Actualizar solo los campos que vienen en el request
    if itinerario_update.estado is not None:
        itinerario.estado = itinerario_update.estado
        
        # Si se marca como completado, actualizar fecha_fin
        if itinerario_update.estado == "completado" and not itinerario.fecha_fin:
            itinerario.fecha_fin = datetime.now(timezone.utc)
    
    if itinerario_update.fecha_inicio is not None:
        itinerario.fecha_inicio = itinerario_update.fecha_inicio
    
    if itinerario_update.fecha_fin is not None:
        itinerario.fecha_fin = itinerario_update.fecha_fin
    
    if itinerario_update.puntuacion is not None:
        itinerario.puntuacion = itinerario_update.puntuacion
    
    if itinerario_update.tipo_entrada is not None:
        itinerario.tipo_entrada = itinerario_update.tipo_entrada
    
    if itinerario_update.acompañantes is not None:
        itinerario.acompañantes = itinerario_update.acompañantes
    
    # Guardar cambios
    try:
        db.commit()
        db.refresh(itinerario)
        
        logger.info(f"Itinerario {itinerario_id} actualizado: estado={itinerario.estado}")
        
        return itinerario
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error actualizando itinerario {itinerario_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error actualizando itinerario: {str(e)}"
        )


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
# ACTUALIZAR DETALLE
# ============================================

@router.patch("/detalles/{detalle_id}", response_model=ItinerarioDetalleResponse)
async def actualizar_detalle(
    detalle_id: int,
    detalle_data: ItinerarioDetalleUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualizar estado de un detalle de itinerario
    
    Permite marcar áreas como:
    - Visitadas (visitado=True)
    - Saltadas (skip=True)
    - Actualizar tiempos reales
    - Registrar hora de inicio/fin
    """
    detalle = db.query(ItinerarioDetalle).filter(ItinerarioDetalle.id == detalle_id).first()
    if not detalle:
        raise HTTPException(status_code=404, detail="Detalle no encontrado")
    
    # Actualizar campos
    for campo, valor in detalle_data.model_dump(exclude_unset=True).items():
        setattr(detalle, campo, valor)
    
    db.commit()
    db.refresh(detalle)
    
    logger.info(f"✅ Detalle actualizado: {detalle_id}")
    return detalle