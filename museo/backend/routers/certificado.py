# backend/routers/certificado.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import logging

from database import get_db
from models import Itinerario, Perfil, Visitante
from config import get_settings

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)

# ============================================
# LOGO DEL MUSEO (URL PÚBLICA)
# ============================================
# ✅ CORREGIDO: URL directa de la imagen
LOGO_PUMAPUNGO_URL = "https://ibb.co/KjMqXkN9"

# ============================================
# PLANTILLA HTML DEL CERTIFICADO (DISEÑO VINTAGE PROFESIONAL)
# ============================================
CERTIFICADO_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Certificado de Visita - Museo Pumapungo</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Great+Vibes&display=swap');
        
        body {{
            font-family: 'Playfair Display', serif;
            text-align: center;
            margin: 0;
            padding: 40px 20px;
            background: linear-gradient(135deg, #f5f1e6 0%, #e8dfca 100%);
            color: #5a3e2b;
        }}
        .certificate {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 60px;
            border: 15px solid #d4b88c;
            border-radius: 10px;
            box-shadow: 0 10px 50px rgba(0,0,0,0.15);
            position: relative;
        }}
        .logo-container {{
            display: flex;
            justify-content: center;
            margin: 20px 0 40px;
        }}
        .main-logo {{
            max-width: 150px;
            height: auto;
            border: 3px solid #8b4513;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        .header {{
            font-size: 28px;
            font-weight: bold;
            color: #8b4513;
            letter-spacing: 3px;
            margin-bottom: 10px;
            text-transform: uppercase;
        }}
        .subheader {{
            font-size: 18px;
            color: #a0826d;
            margin-bottom: 30px;
        }}
        .title {{
            font-family: 'Great Vibes', cursive;
            font-size: 64px;
            font-weight: normal;
            margin: 20px 0 40px;
            color: #8b4513;
            letter-spacing: 2px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }}
        .visitor-name {{
            font-size: 48px;
            font-style: italic;
            margin: 30px 0;
            color: #5a3e2b;
            padding: 15px 0;
            border-top: 2px solid #d4b88c;
            border-bottom: 2px solid #d4b88c;
            line-height: 1.2;
        }}
        .description {{
            font-size: 20px;
            margin: 25px 0;
            line-height: 1.6;
        }}
        .date {{
            font-size: 18px;
            margin: 30px 0 20px;
            color: #7a5c46;
        }}
        .signature {{
            margin-top: 50px;
            font-style: italic;
            font-size: 24px;
            color: #5a3e2b;
            position: relative;
            padding-top: 20px;
        }}
        .signature:after {{
            content: "";
            display: block;
            width: 200px;
            height: 2px;
            background: #d4b88c;
            margin: 5px auto 0;
        }}
        .footer {{
            margin-top: 40px;
            font-size: 16px;
            color: #8b4513;
            font-weight: bold;
        }}
        .seal {{
            position: absolute;
            bottom: 30px;
            right: 40px;
            width: 100px;
            height: 100px;
            opacity: 0.7;
            transform: rotate(15deg);
            font-size: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 2px solid #8b4513;
            border-radius: 50%;
            background: rgba(212, 184, 140, 0.2);
        }}
        .qr-code {{
            margin-top: 30px;
            text-align: center;
            font-size: 14px;
            color: #a0826d;
        }}
    </style>
</head>
<body>
    <div class="certificate">
        <div class="logo-container">
            <img src="{logo_url}" alt="Logo Museo Pumapungo" class="main-logo">
        </div>
        
        <div class="header">Ministerio de Cultura y Patrimonio</div>
        <div class="subheader">Gobierno del Ecuador</div>
        
        <div class="title">Certificado de Visita</div>
        
        <p>Se otorga el presente reconocimiento a:</p>
        <div class="visitor-name">{visitor_name}</div>
        
        <p class="description">Por su visita y recorrido personalizado al <strong>MUSEO PUMAPUNGO</strong></p>
        <p class="description">Patrimonio Cultural del Ecuador • Cuenca, Ecuador</p>
        
        <div class="date">Fecha de visita: {visit_date}</div>
        
        <div class="signature">
            Director del Museo Pumapungo
        </div>
        
        <div class="footer">
            Museo Pumapungo • Calle Larga s/n y Bolívar • Cuenca, Ecuador
        </div>
        
        <div class="seal">
            AUTÉNTICO<br/>MP-2026
        </div>
        
        <div class="qr-code">
            Código de verificación: MP-{visitante_id}-{itinerario_id}
        </div>
    </div>
</body>
</html>
"""

def generar_certificado_html(visitor_name: str, visit_date: str, visitante_id: int, itinerario_id: int) -> str:
    """Genera HTML del certificado con logo real"""
    return CERTIFICADO_TEMPLATE.format(
        visitor_name=visitor_name,
        visit_date=visit_date,
        visitante_id=visitante_id,
        itinerario_id=itinerario_id,
        logo_url=LOGO_PUMAPUNGO_URL
    )

def enviar_certificado_email(email: str, visitor_name: str, html_content: str):
    """Envía certificado por email"""
    try:
        logger.info(f"📧 Preparando envío de certificado a {email}")
        
        # Validar configuración
        if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
            logger.error("❌ Configuración SMTP incompleta")
            logger.error(f"   SMTP_USERNAME: {'OK' if settings.SMTP_USERNAME else 'VACÍO'}")
            logger.error(f"   SMTP_PASSWORD: {'OK' if settings.SMTP_PASSWORD else 'VACÍO'}")
            return False
        
        msg = MIMEMultipart()
        msg['From'] = settings.SMTP_FROM_EMAIL
        msg['To'] = email
        msg['Subject'] = '🎉 Tu Certificado de Visita - Museo Pumapungo'
        
        # Cuerpo HTML del email (versión para ver en el correo)
        body_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background: #f9f5eb;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #8b4513; font-size: 28px; margin: 0;">¡Gracias por visitarnos!</h1>
                <p style="font-size: 18px; color: #5a3e2b; margin: 10px 0;">{visitor_name}</p>
            </div>
            
            <div style="background: white; border: 2px solid #d4b88c; border-radius: 10px; padding: 30px; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
                <div style="text-align: center; margin-bottom: 25px;">
                    <div style="font-size: 48px; color: #8b4513; margin: 10px 0; font-family: 'Playfair Display', serif;">CERTIFICADO</div>
                    <div style="font-size: 24px; color: #5a3e2b; font-style: italic;">de Visita</div>
                </div>
                
                <p style="font-size: 16px; line-height: 1.5; color: #5a3e2b; margin: 20px 0;">
                    Adjunto encontrarás tu certificado personalizado de visita al Museo Pumapungo en formato HTML.
                </p>
                
                <div style="background: #f8f4e9; border-left: 4px solid #d4b88c; padding: 15px; margin: 25px 0; border-radius: 0 8px 8px 0;">
                    <p style="margin: 0; font-style: italic; color: #7a5c46;">
                        "El Museo Pumapungo es un tesoro cultural que preserva la historia cañari e inca en el corazón de Cuenca"
                    </p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <div style="display: inline-block; background: #8b4513; color: white; padding: 12px 25px; border-radius: 30px; font-weight: bold; font-size: 18px;">
                        Museo Pumapungo
                    </div>
                </div>
            </div>
            
            <div style="text-align: center; color: #a0826d; font-size: 14px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0d6c9;">
                <p style="margin: 5px 0;">Ministerio de Cultura y Patrimonio • Ecuador</p>
                <p style="margin: 5px 0;">Calle Larga s/n y Bolívar • Cuenca, Ecuador</p>
            </div>
        </div>
        """
        
        msg.attach(MIMEText(body_html, 'html'))
        
        # Adjuntar certificado como HTML descargable
        part = MIMEApplication(html_content.encode('utf-8'), Name="Certificado_Pumapungo.html")
        part['Content-Disposition'] = f'attachment; filename="Certificado_Pumapungo_{visitor_name.replace(" ", "_")}.html"'
        msg.attach(part)
        
        # Enviar email
        logger.info(f"📧 Conectando a {settings.SMTP_HOST}:{settings.SMTP_PORT} con SSL")
        
        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            logger.info(f"🔑 Autenticando como {settings.SMTP_USERNAME}")
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            
            logger.info(f"📤 Enviando mensaje...")
            server.send_message(msg)
        
        logger.info(f"✅ Certificado enviado exitosamente a {email}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"❌ Error de autenticación SMTP: {str(e)}")
        logger.error(f"   Usuario: {settings.SMTP_USERNAME}")
        logger.error(f"   Host: {settings.SMTP_HOST}:{settings.SMTP_PORT}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"❌ Error SMTP: {type(e).__name__}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ Error enviando email: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

@router.post("/itinerarios/{itinerario_id}/certificado")
async def generar_y_enviar_certificado(
    itinerario_id: int,
    db: Session = Depends(get_db)
):
    """Genera y envía certificado al finalizar evaluación"""
    try:
        logger.info(f"📜 Generando certificado para itinerario {itinerario_id}")
        
        # Obtener itinerario
        itinerario = db.query(Itinerario).filter(Itinerario.id == itinerario_id).first()
        if not itinerario:
            raise HTTPException(status_code=404, detail="Itinerario no encontrado")
        
        # Obtener perfil
        perfil = db.query(Perfil).filter(Perfil.id == itinerario.perfil_id).first()
        if not perfil:
            raise HTTPException(status_code=404, detail="Perfil no encontrado")
        
        # Obtener visitante
        visitante = perfil.visitante
        if not visitante:
            raise HTTPException(status_code=404, detail="Visitante no encontrado")
        
        # Verificar email
        if not visitante.email:
            raise HTTPException(status_code=400, detail="Visitante no tiene email registrado")
        
        # Generar certificado
        visit_date = itinerario.fecha_generacion.strftime("%d de %B de %Y")
        visitor_full_name = f"{visitante.nombre} {visitante.apellido or ''}".strip()
        
        html_certificado = generar_certificado_html(
            visitor_name=visitor_full_name,
            visit_date=visit_date,
            visitante_id=visitante.id,
            itinerario_id=itinerario_id
        )
        
        # Enviar email
        email_enviado = enviar_certificado_email(
            email=visitante.email,
            visitor_name=visitor_full_name,
            html_content=html_certificado
        )
        
        if email_enviado:
            logger.info(f"✅ Certificado generado y enviado a {visitante.email}")
        else:
            logger.warning(f"⚠️ Certificado generado pero no se pudo enviar por email")
        
        return {
            "success": True,
            "message": "Certificado generado y enviado a tu email" if email_enviado else "Certificado generado (error al enviar email)",
            "email": visitante.email,
            "email_enviado": email_enviado
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error en generación de certificado: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar certificado: {str(e)}"
        )