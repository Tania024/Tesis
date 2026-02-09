# backend/routers/auth_google.py
# Endpoints de autenticación con Google OAuth
# Sistema Museo Pumapungo

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
import logging
from urllib.parse import urlencode

from database import get_db
from models import Visitante, Perfil
from services.google_auth_service import google_auth_service
from services.interest_analyzer_service import interest_analyzer
from config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()

# ============================================
# GOOGLE OAUTH FLOW
# ============================================

@router.get("/google/login")
async def google_login():
    """
    Inicia el flujo de autenticación con Google
    """
    auth_url = google_auth_service.get_authorization_url()
    logger.info("🔗 Redirigiendo a Google OAuth...")
    return RedirectResponse(url=auth_url)


@router.get("/google/callback")
async def google_callback(
    code: str = Query(..., description="Código OAuth de Google"),
    error: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Callback de Google OAuth
    ✅ CORREGIDO: Elimina duplicación, agrega datos_completos, limpia URL
    """

    if error:
        logger.error(f"❌ Error OAuth de Google: {error}")
        settings = get_settings()
        frontend_url = settings.FRONTEND_URL.rstrip('/') or "http://localhost:5173"
        return RedirectResponse(
            url=f"{frontend_url}/login?error={error}"
        )

    try:
        logger.info("🔐 Procesando callback de Google OAuth...")
        logger.info(f"📝 Code recibido: {code[:20]}...")

        # 1. Intercambiar código por token
        token_data = await google_auth_service.exchange_code_for_token(code)
        access_token = token_data["access_token"]
        logger.info("✅ Token obtenido exitosamente")

        # 2. Obtener datos del usuario
        user_data = await google_auth_service.extract_user_interests(access_token)

        profile = user_data["profile"]
        youtube_data = user_data["youtube"]
        intereses_detectados_basicos = user_data["intereses_detectados"]

        email = profile["email"]
        name = profile["name"]
        given_name = profile.get("given_name", name.split()[0])
        family_name = profile.get("family_name", "")

        logger.info(f"📊 Usuario Google: {email}")
        logger.info(f"📺 Canales YouTube: {len(youtube_data['channels'])}")

        # 3. Buscar o crear visitante (POR EMAIL)
        visitante = db.query(Visitante).filter(Visitante.email == email).first()

        if not visitante:
            visitante = Visitante(
                nombre=given_name,
                apellido=family_name,
                email=email
            )
            db.add(visitante)
            db.flush()
            logger.info(f"✅ Nuevo visitante creado: {email} (ID: {visitante.id})")
        else:
            logger.info(f"ℹ️ Visitante existente: {email} (ID: {visitante.id})")

        # ✅ VERIFICAR SI TIENE DATOS COMPLETOS
        datos_completos = all([
            visitante.pais_origen is not None,
            visitante.ciudad_origen is not None,
            visitante.tipo_visitante is not None,
        ])

        # 4. Analizar intereses con IA
        datos_para_ia = {
            "pages_liked": [
                {"name": channel, "category": "YouTube"}
                for channel in youtube_data["channels"]
            ],
            "locations_visited": []
        }

        logger.info("🤖 Analizando intereses con IA...")
        analisis_ia = await interest_analyzer.analizar_perfil_completo(
            facebook_data=datos_para_ia,
            instagram_data=None,
            nombre_visitante=visitante.nombre
        )

        intereses_finales = list(set(
            intereses_detectados_basicos + analisis_ia["intereses"]
        ))

        logger.info(f"✅ Intereses detectados: {', '.join(intereses_finales)}")

        # 5. Crear o actualizar perfil
        perfil = db.query(Perfil).filter(
            Perfil.visitante_id == visitante.id
        ).first()

        tiempo_usuario = analisis_ia.get("tiempo_sugerido", 90)

        if not perfil:
            perfil = Perfil(
                visitante_id=visitante.id,
                intereses=intereses_finales,
                tiempo_disponible=tiempo_usuario,
                nivel_detalle=analisis_ia.get("nivel_detalle_sugerido", "medio"),
                incluir_descansos=True
            )
            db.add(perfil)
            logger.info(f"✅ Perfil creado para visitante ID: {visitante.id}")
        else:
            perfil.intereses = intereses_finales
            perfil.tiempo_disponible = tiempo_usuario
            perfil.nivel_detalle = analisis_ia.get("nivel_detalle_sugerido", "medio")
            logger.info(f"✅ Perfil actualizado para visitante ID: {visitante.id}")

        db.commit()
        db.refresh(visitante)
        db.refresh(perfil)

        logger.info(f"✅ Autenticación Google completada: Visitante ID={visitante.id}")

        # 6. ✅ REDIRIGIR AL FRONTEND con los datos
        settings = get_settings()
        frontend_url = (settings.FRONTEND_URL or "http://localhost:5173").rstrip('/')  # ✅ QUITAR BARRA FINAL
        
        # Preparar parámetros para el frontend
        params = {
            "visitante_id": visitante.id,
            "nombre": f"{visitante.nombre} {visitante.apellido}".strip(),
            "email": visitante.email,
            "success": "true",
            "datos_completos": "true" if datos_completos else "false"
        }
        
        redirect_url = f"{frontend_url}/login?{urlencode(params)}"
        logger.info(f"↩️ Redirigiendo al frontend: {redirect_url}")
        
        return RedirectResponse(url=redirect_url)

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error en callback Google: {e}", exc_info=True)
        
        # Redirigir al frontend con error
        settings = get_settings()
        frontend_url = (settings.FRONTEND_URL or "http://localhost:5173").rstrip('/')
        return RedirectResponse(
            url=f"{frontend_url}/login?error=auth_failed&detail={str(e)}"
        )