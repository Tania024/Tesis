# routers/ia.py
# ✅ ACTUALIZADO: Compatible con Ollama y DeepSeek

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import time
import logging
from datetime import datetime

from config import get_settings
from database import get_db
import models
import schemas
from services.ia_service import ia_service

from utils.horarios_museo import (
    validar_horario_museo,
    ajustar_itinerario_por_tiempo,
    obtener_mensaje_horarios
)

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)

# ============================================
# ENDPOINT - Chat Simple
# ============================================

@router.post("/chat")
def chat(prompt: str):
    """
    ✅ Chat simple — usa el proveedor configurado (Ollama o DeepSeek)
    """
    try:
        respuesta = ia_service._llamar_ia(prompt, max_tokens=1000, json_mode=False)
        return {"respuesta": respuesta}
    except Exception as e:
        return {"error": f"Error al conectar con IA ({ia_service.provider}): {e}"}


# ============================================
# Generación Progresiva de Itinerarios
# (Sin cambios — ya usa ia_service internamente)
# ============================================

@router.post("/generar-itinerario-progresivo", response_model=schemas.ItinerarioCompleto)
async def generar_itinerario_progresivo(
    solicitud: schemas.SolicitudItinerario,
    db: Session = Depends(get_db)
):
    """
    🔥 Generación progresiva con validación de horarios
    Funciona con Ollama (local) y DeepSeek (producción)
    """
    try:
        tiempo_inicio = time.time()
        logger.info(f"🚀 PROGRESIVO [{ia_service.provider}]: Iniciado para visitante {solicitud.visitante_id}")
        
        # Validar visitante
        visitante = db.query(models.Visitante).filter(
            models.Visitante.id == solicitud.visitante_id
        ).first()
        
        if not visitante:
            raise HTTPException(status_code=404, detail="Visitante no encontrado")
        
        # VALIDAR HORARIO DEL MUSEO
        fecha_hora_actual = datetime.now()
        
        puede_generar, duracion_ajustada, mensaje_horario = ajustar_itinerario_por_tiempo(
            solicitud.tiempo_disponible,
            fecha_hora_actual
        )
        
        if not puede_generar:
            logger.warning(f"⏰ No se puede generar itinerario: {mensaje_horario[:100]}")
            raise HTTPException(
                status_code=400,
                detail={
                    "mensaje": mensaje_horario,
                    "horarios": obtener_mensaje_horarios(),
                    "puede_continuar": False
                }
            )
        
        if duracion_ajustada != solicitud.tiempo_disponible:
            logger.info(f"⏰ Tiempo ajustado: {solicitud.tiempo_disponible} -> {duracion_ajustada} min")
            tiempo_para_itinerario = duracion_ajustada
        else:
            tiempo_para_itinerario = solicitud.tiempo_disponible
        
        logger.info(f"✅ Museo abierto. Tiempo: {tiempo_para_itinerario} min")
        
        # Obtener perfil
        perfil = db.query(models.Perfil).filter(
            models.Perfil.visitante_id == solicitud.visitante_id
        ).first()
        
        if not perfil:
            perfil = models.Perfil(
                visitante_id=solicitud.visitante_id,
                intereses=solicitud.intereses,
                tiempo_disponible=tiempo_para_itinerario,
                nivel_detalle=solicitud.nivel_detalle,
                incluir_descansos=solicitud.incluir_descansos
            )
            db.add(perfil)
            db.commit()
            db.refresh(perfil)
        
        # Obtener áreas disponibles
        areas_query = db.query(models.Area).filter(models.Area.activa == True)
        
        if solicitud.intereses and tiempo_para_itinerario:
            areas_query = areas_query.filter(
                models.Area.categoria.in_(solicitud.intereses)
            )
            logger.info(f"🔍 Filtrando por intereses: {solicitud.intereses}")
        elif not tiempo_para_itinerario:
            logger.info("✅ Sin límite - usando TODAS las áreas")
        
        areas_disponibles = areas_query.order_by(models.Area.orden_recomendado).all()
        
        if not areas_disponibles:
            raise HTTPException(
                status_code=400,
                detail="No hay áreas disponibles que coincidan con tus intereses"
            )
        
        areas_dict = [
            {
                "id": area.id,
                "codigo": area.codigo,
                "nombre": area.nombre,
                "descripcion": area.descripcion,
                "categoria": area.categoria,
                "piso": area.piso,
                "tiempo_minimo": area.tiempo_minimo,
                "tiempo_maximo": area.tiempo_maximo
            }
            for area in areas_disponibles
        ]
        
        # Crear itinerario base
        nuevo_itinerario = models.Itinerario(
            perfil_id=perfil.id,
            titulo="Generando...",
            descripcion="Preparando tu itinerario personalizado...",
            estado='en_proceso',
            modelo_ia_usado=ia_service.model
        )
        db.add(nuevo_itinerario)
        db.commit()
        db.refresh(nuevo_itinerario)
        
        logger.info(f"✅ Itinerario {nuevo_itinerario.id} creado, generando con {ia_service.provider}...")
        
        # GENERACIÓN PROGRESIVA
        itinerario_resultado = ia_service.generar_itinerario_progresivo(
            visitante_nombre=visitante.nombre,
            intereses=solicitud.intereses,
            tiempo_disponible=tiempo_para_itinerario,
            nivel_detalle=solicitud.nivel_detalle.value,
            areas_disponibles=areas_dict,
            incluir_descansos=solicitud.incluir_descansos,
            db_session=db,
            itinerario_id=nuevo_itinerario.id
        )
        
        tiempo_fin = time.time()
        tiempo_generacion = tiempo_fin - tiempo_inicio
        
        titulo_base = itinerario_resultado.get('titulo', 'Tu recorrido personalizado')
        
        descripcion_base = itinerario_resultado.get('descripcion', '')
        if duracion_ajustada != solicitud.tiempo_disponible and mensaje_horario:
            descripcion_base = f"⏰ {mensaje_horario}\n\n{descripcion_base}"
        
        nuevo_itinerario.titulo = titulo_base
        nuevo_itinerario.descripcion = descripcion_base
        nuevo_itinerario.duracion_total = itinerario_resultado.get('duracion_total')
        nuevo_itinerario.estado = 'generado'
        nuevo_itinerario.respuesta_ia = itinerario_resultado.get('metadata', {})
        
        # Crear detalles
        for area_data in itinerario_resultado['areas']:
            area = db.query(models.Area).filter(
                models.Area.codigo == area_data['area_codigo']
            ).first()
            
            if area:
                detalle = models.ItinerarioDetalle(
                    itinerario_id=nuevo_itinerario.id,
                    area_id=area.id,
                    orden=area_data['orden'],
                    tiempo_sugerido=area_data.get('tiempo_sugerido', 20),
                    introduccion=area_data.get('introduccion'),
                    recomendacion=area_data.get('recomendacion'),
                    historia_contextual=area_data.get('historia_contextual'),
                    datos_curiosos=area_data.get('datos_curiosos', []),
                    que_observar=area_data.get('que_observar', [])
                )
                db.add(detalle)
        
        db.commit()
        db.refresh(nuevo_itinerario)
        
        logger.info(f"✅ Listo en {tiempo_generacion:.1f}s [{ia_service.provider}]")
        
        return nuevo_itinerario
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error generando itinerario: {str(e)}")


# ============================================
# Estado de generación (sin cambios)
# ============================================

@router.get("/itinerario/{itinerario_id}/estado-generacion")
async def obtener_estado_generacion(
    itinerario_id: int,
    db: Session = Depends(get_db)
):
    """Obtener el estado de generación progresiva"""
    try:
        itinerario = db.query(models.Itinerario).filter(
            models.Itinerario.id == itinerario_id
        ).first()
        
        if not itinerario:
            raise HTTPException(status_code=404, detail="Itinerario no encontrado")
        
        detalles = db.query(models.ItinerarioDetalle).filter(
            models.ItinerarioDetalle.itinerario_id == itinerario_id
        ).all()
        
        total_areas = len(detalles)
        areas_generadas = sum(
            1 for d in detalles 
            if d.introduccion and "Generando contenido" not in d.introduccion
        )
        
        completado = areas_generadas == total_areas
        porcentaje = (areas_generadas / total_areas * 100) if total_areas > 0 else 0
        
        return {
            "itinerario_id": itinerario_id,
            "completado": completado,
            "areas_generadas": areas_generadas,
            "total_areas": total_areas,
            "porcentaje_completado": round(porcentaje, 1),
            "estado": itinerario.estado,
            "provider": ia_service.provider  # 🔥 NUEVO
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))