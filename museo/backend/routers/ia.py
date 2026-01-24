# routers/ia.py
# Router para endpoints de Inteligencia Artificial
# ✅ VERSIÓN CORREGIDA - Con validación de horarios del museo

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import requests
import time
import logging
from datetime import datetime

from config import get_settings
from database import get_db
import models
import schemas
from services.ia_service import ia_service

# 🔥 NUEVO: Import de utilidades de horarios
from utils.horarios_museo import (
    validar_horario_museo,
    ajustar_itinerario_por_tiempo,
    obtener_mensaje_horarios
)

# Configuración
router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)

# URLs para Ollama
OLLAMA_URL = f"{settings.OLLAMA_BASE_URL}/api/generate"
MODEL = settings.OLLAMA_MODEL

# ============================================
# ENDPOINT ORIGINAL - Chat Simple
# ============================================

@router.post("/chat")
def chat(prompt: str):
    """
    ✅ ENDPOINT ORIGINAL - Chat simple con Ollama
    Mantiene compatibilidad con código anterior
    """
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload)
    except Exception as e:
        return {"error": f"Error al conectar con Ollama: {e}"}

    if response.status_code != 200:
        return {
            "error": "Error comunicándose con Ollama",
            "detalle": response.text
        }

    return {"respuesta": response.json().get("response")}


# ============================================
# NUEVO - Generación Progresiva de Itinerarios
# ============================================

@router.post("/generar-itinerario-progresivo", response_model=schemas.ItinerarioCompleto)
async def generar_itinerario_progresivo(
    solicitud: schemas.SolicitudItinerario,
    db: Session = Depends(get_db)
):
    """
    🔥 NUEVO: Generación progresiva de itinerario con validación de horarios
    1. Valida que el museo esté abierto
    2. Ajusta el tiempo según disponibilidad
    3. Genera solo la primera área (30 segundos)
    4. Retorna inmediatamente para que el usuario empiece
    5. Continúa generando el resto en background
    """
    try:
        tiempo_inicio = time.time()
        logger.info(f"🚀 PROGRESIVO: Iniciado para visitante {solicitud.visitante_id}")
        
        # Validar visitante
        visitante = db.query(models.Visitante).filter(
            models.Visitante.id == solicitud.visitante_id
        ).first()
        
        if not visitante:
            raise HTTPException(status_code=404, detail="Visitante no encontrado")
        
        # ============================================
        # 🔥 NUEVO: VALIDAR HORARIO DEL MUSEO
        # ============================================
        fecha_hora_actual = datetime.now()
        
        # Validar si el museo está abierto y ajustar tiempo
        puede_generar, duracion_ajustada, mensaje_horario = ajustar_itinerario_por_tiempo(
            solicitud.tiempo_disponible,
            fecha_hora_actual
        )
        
        if not puede_generar:
            # El museo está cerrado o no hay tiempo suficiente
            logger.warning(f"⏰ No se puede generar itinerario: {mensaje_horario[:100]}")
            
            raise HTTPException(
                status_code=400,
                detail={
                    "mensaje": mensaje_horario,
                    "horarios": obtener_mensaje_horarios(),
                    "puede_continuar": False
                }
            )
        
        # Si hay un ajuste de tiempo, registrarlo
        if duracion_ajustada != solicitud.tiempo_disponible:
            logger.info(f"⏰ Tiempo ajustado: {solicitud.tiempo_disponible} -> {duracion_ajustada} min")
            if duracion_ajustada is not None:
                logger.info(f"💡 Mensaje: {mensaje_horario}")
            
            # Usar el tiempo ajustado
            tiempo_para_itinerario = duracion_ajustada
        else:
            tiempo_para_itinerario = solicitud.tiempo_disponible
        
        logger.info(f"✅ Museo abierto. Tiempo para itinerario: {tiempo_para_itinerario} min")
        
        # ============================================
        # CONTINÚA CON EL CÓDIGO ORIGINAL
        # ============================================
        
        # Obtener perfil
        perfil = db.query(models.Perfil).filter(
            models.Perfil.visitante_id == solicitud.visitante_id
        ).first()
        
        if not perfil:
            # Crear perfil temporal
            perfil = models.Perfil(
                visitante_id=solicitud.visitante_id,
                intereses=solicitud.intereses,
                tiempo_disponible=tiempo_para_itinerario,  # 🔥 CAMBIADO: Usar tiempo ajustado
                nivel_detalle=solicitud.nivel_detalle,
                incluir_descansos=solicitud.incluir_descansos
            )
            db.add(perfil)
            db.commit()
            db.refresh(perfil)
        
        # Obtener áreas disponibles
        areas_query = db.query(models.Area).filter(models.Area.activa == True)
        
        # 🔥 CORREGIDO: Solo filtrar por intereses si HAY límite de tiempo
        # Si NO hay límite, usar TODAS las áreas sin importar intereses
        if solicitud.intereses and tiempo_para_itinerario:  # 🔥 CAMBIADO: Usar tiempo_para_itinerario
            areas_query = areas_query.filter(
                models.Area.categoria.in_(solicitud.intereses)
            )
            logger.info(f"🔍 Filtrando por intereses: {solicitud.intereses}")
        elif not tiempo_para_itinerario:  # 🔥 CAMBIADO: Usar tiempo_para_itinerario
            logger.info("✅ Sin límite - NO filtrando por intereses, usando TODAS")
        
        areas_disponibles = areas_query.order_by(models.Area.orden_recomendado).all()
        
        if not areas_disponibles:
            raise HTTPException(
                status_code=400,
                detail="No hay áreas disponibles que coincidan con tus intereses"
            )
        
        # Convertir a dict para IA
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
        
        # Crear itinerario base en BD (sin detalles aún)
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
        
        logger.info(f"✅ Itinerario {nuevo_itinerario.id} creado, iniciando generación IA")
        
        # 🔥 GENERACIÓN PROGRESIVA CON TIEMPO AJUSTADO
        itinerario_resultado = ia_service.generar_itinerario_progresivo(
            visitante_nombre=visitante.nombre,
            intereses=solicitud.intereses,
            tiempo_disponible=tiempo_para_itinerario,  # 🔥 CAMBIADO: Usar tiempo ajustado
            nivel_detalle=solicitud.nivel_detalle.value,
            areas_disponibles=areas_dict,
            incluir_descansos=solicitud.incluir_descansos,
            db_session=db,
            itinerario_id=nuevo_itinerario.id
        )
        
        tiempo_fin = time.time()
        tiempo_generacion = tiempo_fin - tiempo_inicio
        
        # Actualizar itinerario con info básica
        titulo_base = itinerario_resultado.get('titulo', 'Tu recorrido personalizado')
        
        # Si hubo ajuste de tiempo, agregarlo a la descripción
        descripcion_base = itinerario_resultado.get('descripcion', '')
        if duracion_ajustada != solicitud.tiempo_disponible and mensaje_horario:
            # Agregar mensaje de ajuste al inicio de la descripción
            descripcion_base = f"⏰ {mensaje_horario}\n\n{descripcion_base}"
        
        nuevo_itinerario.titulo = titulo_base
        nuevo_itinerario.descripcion = descripcion_base
        nuevo_itinerario.duracion_total = itinerario_resultado.get('duracion_total')
        nuevo_itinerario.estado = 'generado'
        nuevo_itinerario.respuesta_ia = itinerario_resultado.get('metadata', {})
        
        # Crear detalles en BD
        for area_data in itinerario_resultado['areas']:
            # Buscar área por código
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
        
        logger.info(f"✅ Primera área lista en {tiempo_generacion:.1f}s, resto generándose en background")
        
        # Retornar itinerario completo
        return nuevo_itinerario
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error en generación progresiva: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error generando itinerario: {str(e)}"
        )


# ============================================
# NUEVO - Endpoint para verificar estado de generación
# ============================================

@router.get("/itinerario/{itinerario_id}/estado-generacion")
async def obtener_estado_generacion(
    itinerario_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtener el estado de generación progresiva de un itinerario
    Usado por el frontend para polling
    """
    try:
        # Obtener itinerario
        itinerario = db.query(models.Itinerario).filter(
            models.Itinerario.id == itinerario_id
        ).first()
        
        if not itinerario:
            raise HTTPException(status_code=404, detail="Itinerario no encontrado")
        
        # Obtener detalles
        detalles = db.query(models.ItinerarioDetalle).filter(
            models.ItinerarioDetalle.itinerario_id == itinerario_id
        ).all()
        
        total_areas = len(detalles)
        
        # Contar áreas generadas (las que NO tienen "Generando..." en introducción)
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
            "estado": itinerario.estado
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo estado: {e}")
        raise HTTPException(status_code=500, detail=str(e))