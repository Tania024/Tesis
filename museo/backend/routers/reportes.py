# routers/reportes.py
# Endpoints para descarga de reportes CSV
# Sistema Museo Pumapungo

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
import csv
import io
from datetime import datetime

from database import get_db
from models import Visitante, Itinerario, Evaluacion, Perfil, HistorialVisita

router = APIRouter()


def generar_csv(filas: list[list], encabezados: list[str]) -> StreamingResponse:
    """Genera un StreamingResponse con contenido CSV (UTF-8 con BOM para Excel)"""
    output = io.StringIO()
    # BOM para que Excel interprete UTF-8 correctamente
    output.write('\ufeff')
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(encabezados)
    for fila in filas:
        writer.writerow(fila)
    output.seek(0)

    fecha = datetime.now().strftime("%Y%m%d")
    nombre_archivo = f"reporte_{fecha}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{nombre_archivo}"',
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )


# ============================================
# REPORTE: VISITANTES
# ============================================

@router.get("/visitantes")
async def reporte_visitantes(db: Session = Depends(get_db)):
    """Descargar CSV con todos los visitantes registrados"""
    visitantes = db.query(Visitante).order_by(Visitante.fecha_registro.desc()).all()

    encabezados = [
        "ID", "Código Visita", "Nombre", "Apellido", "Email",
        "Teléfono", "País", "Ciudad", "Tipo Visitante",
        "Fecha Nacimiento", "Fecha Registro", "Total Visitas", "Activo"
    ]

    filas = []
    for v in visitantes:
        filas.append([
            v.id,
            v.codigo_visita or "",
            v.nombre or "",
            v.apellido or "",
            v.email or "",
            v.telefono or "",
            v.pais_origen or "",
            v.ciudad_origen or "",
            v.tipo_visitante or "",
            str(v.fecha_nacimiento) if v.fecha_nacimiento else "",
            str(v.fecha_registro) if v.fecha_registro else "",
            v.total_visitas or 0,
            "Sí" if v.activo else "No"
        ])

    resp = generar_csv(filas, encabezados)
    fecha = datetime.now().strftime("%Y%m%d")
    resp.headers["Content-Disposition"] = f'attachment; filename="visitantes_{fecha}.csv"'
    return resp


# ============================================
# REPORTE: EVALUACIONES
# ============================================

@router.get("/evaluaciones")
async def reporte_evaluaciones(db: Session = Depends(get_db)):
    """Descargar CSV con todas las evaluaciones y nombre del visitante"""
    evaluaciones = (
        db.query(Evaluacion, Itinerario, Perfil, Visitante)
        .join(Itinerario, Evaluacion.itinerario_id == Itinerario.id)
        .join(Perfil, Itinerario.perfil_id == Perfil.id)
        .join(Visitante, Perfil.visitante_id == Visitante.id)
        .order_by(Evaluacion.fecha_creacion.desc())
        .all()
    )

    encabezados = [
        "ID Evaluación", "Visitante", "Email", "Itinerario",
        "Calificación (1-5)", "Personalizado", "Buenas Decisiones",
        "Acompañamiento", "Comprensión", "Relevante",
        "Usaría Nuevamente", "Comentarios", "Fecha"
    ]

    def si_no(valor):
        return "Sí" if valor else "No"

    filas = []
    for ev, itin, perfil, vis in evaluaciones:
        filas.append([
            ev.id,
            f"{vis.nombre} {vis.apellido or ''}".strip(),
            vis.email or "",
            itin.titulo or f"Itinerario #{itin.id}",
            ev.calificacion_general,
            si_no(ev.personalizado),
            si_no(ev.buenas_decisiones),
            si_no(ev.acompaniamiento),
            si_no(ev.comprension),
            si_no(ev.relevante),
            si_no(ev.usaria_nuevamente),
            ev.comentarios or "",
            str(ev.fecha_creacion) if ev.fecha_creacion else ""
        ])

    resp = generar_csv(filas, encabezados)
    fecha = datetime.now().strftime("%Y%m%d")
    resp.headers["Content-Disposition"] = f'attachment; filename="evaluaciones_{fecha}.csv"'
    return resp


# ============================================
# REPORTE: RESUMEN GENERAL
# ============================================

@router.get("/resumen")
async def reporte_resumen(db: Session = Depends(get_db)):
    """Descargar CSV con resumen estadístico general del museo"""

    # Visitantes
    total_visitantes = db.query(func.count(Visitante.id)).scalar() or 0

    tipos = db.query(
        Visitante.tipo_visitante,
        func.count(Visitante.id)
    ).group_by(Visitante.tipo_visitante).all()

    # Itinerarios
    total_itinerarios = db.query(func.count(Itinerario.id)).scalar() or 0

    estados = db.query(
        Itinerario.estado,
        func.count(Itinerario.id)
    ).group_by(Itinerario.estado).all()

    duracion_prom = db.query(func.avg(Itinerario.duracion_total)).scalar()

    # Evaluaciones
    total_evaluaciones = db.query(func.count(Evaluacion.id)).scalar() or 0
    calif_prom = db.query(func.avg(Evaluacion.calificacion_general)).scalar()

    # Historial
    total_visitas_historial = db.query(func.count(HistorialVisita.id)).scalar() or 0

    encabezados = ["Métrica", "Valor"]
    filas = [
        ["Total Visitantes Registrados", total_visitantes],
    ]

    for tipo, cant in tipos:
        if tipo:
            filas.append([f"  Visitantes - {tipo.capitalize()}", cant])

    filas.extend([
        ["", ""],
        ["Total Itinerarios Generados", total_itinerarios],
    ])

    for estado, cant in estados:
        if estado:
            filas.append([f"  Itinerarios - {estado.capitalize()}", cant])

    filas.extend([
        ["Duración Promedio (min)", round(float(duracion_prom), 1) if duracion_prom else "N/A"],
        ["", ""],
        ["Total Evaluaciones", total_evaluaciones],
        ["Calificación Promedio (1-5)", round(float(calif_prom), 2) if calif_prom else "N/A"],
        ["", ""],
        ["Total Registros en Historial", total_visitas_historial],
        ["", ""],
        [f"Reporte generado el", datetime.now().strftime("%d/%m/%Y %H:%M:%S")],
    ])

    resp = generar_csv(filas, encabezados)
    fecha = datetime.now().strftime("%Y%m%d")
    resp.headers["Content-Disposition"] = f'attachment; filename="resumen_museo_{fecha}.csv"'
    return resp
