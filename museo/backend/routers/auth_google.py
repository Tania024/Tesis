# routers/auth_google.py
# Endpoints de autenticación con Google OAuth
# Sistema Museo Pumapungo

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging

from database import get_db
from models import Visitante, Perfil
from services.google_auth_service import google_auth_service
from services.interest_analyzer_service import interest_analyzer

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
    return {
        "authorization_url": auth_url
    }


@router.get("/google/callback")
async def google_callback(
    code: str = Query(..., description="Código OAuth de Google"),
    perfil_id: int = Query(..., description="ID del perfil preconfigurado"),
    error: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):

    """
    Callback de Google OAuth
    """

    if error:
        raise HTTPException(status_code=400, detail=f"Error Google OAuth: {error}")

    try:
        logger.info("🔐 Procesando callback de Google OAuth...")

        # 1. Intercambiar código por token
        token_data = await google_auth_service.exchange_code_for_token(code)
        access_token = token_data["access_token"]

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

        # 3. Buscar o crear visitante (POR EMAIL)
        visitante = db.query(Visitante).filter(Visitante.email == email).first()

        if not visitante:
            visitante = Visitante(
                nombre=given_name,
                apellido=family_name,
                email=email,
                tipo_visitante="nacional"
            )
            db.add(visitante)
            db.flush()
            logger.info(f"✅ Nuevo visitante creado: {email}")
        else:
            logger.info(f"ℹ️ Visitante existente: {email}")

        # 4. Analizar intereses con IA
        datos_para_ia = {
            "pages_liked": [
                {"name": channel, "category": "YouTube"}
                for channel in youtube_data["channels"]
            ],
            "locations_visited": []
        }

        analisis_ia = await interest_analyzer.analizar_perfil_completo(
            facebook_data=datos_para_ia,
            instagram_data=None,
            nombre_visitante=visitante.nombre
        )

        intereses_finales = list(set(
            intereses_detectados_basicos + analisis_ia["intereses"]
        ))

        # 5. Crear o actualizar perfil
        perfil = db.query(Perfil).filter(
            Perfil.visitante_id == visitante.id
        ).first()

        tiempo_usuario = None 

        if not perfil:
            perfil = Perfil(
                visitante_id=visitante.id,
                intereses=intereses_finales,
                tiempo_disponible=tiempo_usuario,
                nivel_detalle=analisis_ia["nivel_detalle_sugerido"],
                incluir_descansos=True
            )
            db.add(perfil)
        else:
            perfil.intereses = intereses_finales
            perfil.tiempo_disponible = analisis_ia["tiempo_sugerido"]
            perfil.nivel_detalle = analisis_ia["nivel_detalle_sugerido"]

        db.commit()
        db.refresh(visitante)

        logger.info(f"✅ Autenticación Google completada: Visitante ID={visitante.id}")

        return {
            "message": "Autenticación exitosa con Google",
            "visitante_id": visitante.id,
            "nombre": f"{visitante.nombre} {visitante.apellido}".strip(),
            "email": visitante.email,
            "intereses_detectados": intereses_finales,
            "tiempo_sugerido": analisis_ia["tiempo_sugerido"],
            "nota": "El tiempo es una sugerencia. El usuario puede modificarlo antes de generar el itinerario.",
            "nivel_detalle": analisis_ia["nivel_detalle_sugerido"]
        }

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error en callback Google: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando autenticación: {str(e)}"
        )
