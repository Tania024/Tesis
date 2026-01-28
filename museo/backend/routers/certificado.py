# backend/routers/certificates.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from io import BytesIO
from weasyprint import HTML
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime

from database import get_db
from models import Itinerario, Visitante
from config import get_settings

router = APIRouter()
settings = get_settings()

# ============================================
# PLANTILLA HTML DEL CERTIFICADO
# ============================================
CERTIFICATE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Certificado de Visita - Museo Pumapungo</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Great+Vibes&display=swap');
        
        body {
            font-family: 'Playfair Display', serif;
            text-align: center;
            margin: 0;
            padding: 40px 20px;
            background: linear-gradient(135deg, #f5f1e6 0%, #e8dfca 100%);
            color: #5a3e2b;
        }
        .certificate {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 60px;
            border: 15px solid #d4b88c;
            border-radius: 10px;
            box-shadow: 0 10px 50px rgba(0,0,0,0.15);
            position: relative;
        }
        .header {
            font-size: 28px;
            font-weight: bold;
            color: #8b4513;
            letter-spacing: 3px;
            margin-bottom: 10px;
            text-transform: uppercase;
        }
        .subheader {
            font-size: 18px;
            color: #a0826d;
            margin-bottom: 30px;
        }
        .title {
            font-family: 'Great Vibes', cursive;
            font-size: 64px;
            font-weight: normal;
            margin: 20px 0 40px;
            color: #8b4513;
            letter-spacing: 2px;
        }
        .visitor-name {
            font-size: 48px;
            font-style: italic;
            margin: 30px 0;
            color: #5a3e2b;
            padding: 15px 0;
            border-top: 2px solid #d4b88c;
            border-bottom: 2px solid #d4b88c;
            line-height: 1.2;
        }
        .description {
            font-size: 20px;
            margin: 25px 0;
            line-height: 1.6;
        }
        .date {
            font-size: 18px;
            margin: 30px 0 20px;
            color: #7a5c46;
        }
        .signature {
            margin-top: 50px;
            font-style: italic;
            font-size: 24px;
            color: #5a3e2b;
            position: relative;
            padding-top: 20px;
        }
        .signature:after {
            content: "";
            display: block;
            width: 200px;
            height: 2px;
            background: #d4b88c;
            margin: 5px auto 0;
        }
        .footer {
            margin-top: 40px;
            font-size: 16px;
            color: #8b4513;
            font-weight: bold;
        }
        .seal {
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
        }
    </style>
</head>
<body>
    <div class="certificate">
        <div class="header">Ministerio de Cultura y Patrimonio</div>
        <div class="subheader">Gobierno del Ecuador</div>
        
        <div class="title">CERTIFICADO DE VISITA</div>
        
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
    </div>
</body>
</html>
'''

def generate_certificate_pdf(visitor_name: str, visit_date: str) -> bytes:
    """Genera PDF del certificado"""
    html_content = CERTIFICATE_TEMPLATE.format(
        visitor_name=visitor_name,
        visit_date=visit_date
    )
    
    # Generar PDF con WeasyPrint
    pdf = HTML(string=html_content).write_pdf()
    return pdf

def send_certificate_email(email: str, visitor_name: str, pdf_content: bytes):
    """Envía certificado por email"""
    msg = MIMEMultipart()
    msg['From'] = settings.SMTP_FROM_EMAIL
    msg['To'] = email
    msg['Subject'] = '🎉 Tu Certificado de Visita - Museo Pumapungo'
    
    # Cuerpo del email en HTML
    body = f'''
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #8b4513; font-size: 28px;">¡Gracias por visitarnos!</h1>
            <p style="font-size: 18px; color: #5a3e2b;">{visitor_name}</p>
        </div>
        
        <div style="background: #f8f4e9; border-left: 4px solid #d4b88c; padding: 20px; border-radius: 0 8px 8px 0; margin: 25px 0;">
            <h2 style="color: #8b4513; margin-top: 0;">✨ Tu Certificado de Visita</h2>
            <p>Adjunto encontrarás tu certificado personalizado de visita al Museo Pumapungo.</p>
            <p>¡Esperamos verte pronto de nuevo!</p>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <div style="display: inline-block; background: #8b4513; color: white; padding: 15px 30px; border-radius: 30px; font-weight: bold; font-size: 18px;">
                Museo Pumapungo
            </div>
        </div>
        
        <div style="text-align: center; color: #a0826d; font-size: 14px; margin-top: 40px; border-top: 1px solid #e0d6c9; padding-top: 20px;">
            <p>Ministerio de Cultura y Patrimonio • Ecuador</p>
            <p>Calle Larga s/n y Bolívar • Cuenca, Ecuador</p>
        </div>
    </div>
    '''
    
    msg.attach(MIMEText(body, 'html'))
    
    # Adjuntar PDF
    part = MIMEApplication(pdf_content, Name=f"Certificado_Pumapungo_{visitor_name}.pdf")
    part['Content-Disposition'] = f'attachment; filename="Certificado_Pumapungo_{visitor_name}.pdf"'
    msg.attach(part)
    
    # Enviar email
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)
        print(f"✅ Certificado enviado a {email}")
    except Exception as e:
        print(f"❌ Error enviando email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error enviando certificado: {str(e)}")

@router.post("/itinerarios/{itinerario_id}/certificado")
async def generar_certificado(
    itinerario_id: int,
    db: Session = Depends(get_db)
):
    """Genera y envía certificado al finalizar evaluación"""
    # Obtener itinerario y visitante
    itinerario = db.query(Itinerario).filter(Itinerario.id == itinerario_id).first()
    if not itinerario:
        raise HTTPException(status_code=404, detail="Itinerario no encontrado")
    
    visitante = db.query(Visitante).filter(Visitante.id == itinerario.visitante_id).first()
    if not visitante:
        raise HTTPException(status_code=404, detail="Visitante no encontrado")
    
    # Generar PDF
    visit_date = itinerario.creado_en.strftime("%d de %B de %Y")
    pdf_content = generate_certificate_pdf(
        visitor_name=f"{visitante.nombre} {visitante.apellido}".strip(),
        visit_date=visit_date
    )
    
    # Enviar por email
    if not visitante.email:
        raise HTTPException(status_code=400, detail="Visitante no tiene email registrado")
    
    send_certificate_email(
        email=visitante.email,
        visitor_name=f"{visitante.nombre} {visitante.apellido}".strip(),
        pdf_content=pdf_content
    )
    
    return {
        "success": True,
        "message": "Certificado generado y enviado exitosamente",
        "email": visitante.email
    }