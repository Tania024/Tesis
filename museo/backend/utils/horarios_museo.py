# utils/horarios_museo.py
# ✅ CON INFORMACIÓN COMPLETA DE DÍAS HÁBILES

from datetime import datetime, time, timedelta
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# ============================================
# HORARIOS DEL MUSEO PUMAPUNGO
# ============================================

HORARIOS_MUSEO = {
    0: None,  # Lunes: Cerrado
    1: {"apertura": time(8, 0), "cierre": time(17, 0)},   # Martes
    2: {"apertura": time(8, 0), "cierre": time(17, 0)},   # Miércoles
    3: {"apertura": time(8, 0), "cierre": time(17, 0)},   # Jueves
    4: {"apertura": time(8, 0), "cierre": time(17, 0)},   # Viernes
    5: {"apertura": time(10, 0), "cierre": time(16, 0)},  # Sábado
    6: {"apertura": time(10, 0), "cierre": time(16, 0)},  # Domingo
}

DIAS_SEMANA = {
    0: "Lunes",
    1: "Martes",
    2: "Miércoles",
    3: "Jueves",
    4: "Viernes",
    5: "Sábado",
    6: "Domingo"
}

TIEMPO_MINIMO_VISITA = 30


def obtener_horario_dia(dia_semana: int) -> Optional[Dict]:
    """Obtiene el horario de un día específico"""
    return HORARIOS_MUSEO.get(dia_semana)


def obtener_nombre_dia(dia_semana: int) -> str:
    """Obtiene el nombre del día en español"""
    return DIAS_SEMANA.get(dia_semana, "Desconocido")


def formatear_tiempo_espera(minutos: int) -> str:
    """Convierte minutos a formato legible"""
    if minutos >= 60:
        horas = int(minutos // 60)
        mins = int(minutos % 60)
        
        if mins > 0:
            return f"{horas} hora{'s' if horas > 1 else ''} y {mins} minuto{'s' if mins != 1 else ''}"
        else:
            return f"{horas} hora{'s' if horas > 1 else ''}"
    else:
        return f"{int(minutos)} minuto{'s' if minutos != 1 else ''}"


def obtener_horarios_completos() -> str:
    """
    Retorna los horarios completos del museo formateados
    """
    return (
        "📅 Horarios del museo:\n\n"
        "• Lunes: Cerrado\n"
        "• Martes a Viernes: 08:00 - 17:00\n"
        "• Sábado y Domingo: 10:00 - 16:00"
    )


def validar_horario_museo(
    fecha_hora_actual: Optional[datetime] = None
) -> Tuple[bool, str, Dict]:
    """
    Valida si el museo está abierto en este momento
    """
    if fecha_hora_actual is None:
        fecha_hora_actual = datetime.now()
    
    dia_semana = fecha_hora_actual.weekday()
    hora_actual = fecha_hora_actual.time()
    
    nombre_dia = obtener_nombre_dia(dia_semana)
    horario_hoy = obtener_horario_dia(dia_semana)
    
    # ============================================
    # CASO 1: LUNES (CERRADO)
    # ============================================
    if horario_hoy is None:
        dias_hasta_apertura = 1
        fecha_apertura = fecha_hora_actual + timedelta(days=dias_hasta_apertura)
        horario_manana = obtener_horario_dia(fecha_apertura.weekday())
        
        mensaje = (
            f"🚫 El museo está cerrado los {nombre_dia}\n\n"
            f"📅 Te recomendamos volver mañana ({obtener_nombre_dia(fecha_apertura.weekday())})\n\n"
            f"Podrás disfrutar el museo con calma y aprovechar todas las áreas.\n\n"
            f"🕐 Horario de mañana ({obtener_nombre_dia(fecha_apertura.weekday())}): "
            f"{horario_manana['apertura'].strftime('%H:%M')} - {horario_manana['cierre'].strftime('%H:%M')}\n\n"
            f"{obtener_horarios_completos()}"
        )
        
        return False, mensaje, {
            "razon": "cerrado_lunes",
            "dia_actual": nombre_dia,
            "proxima_apertura": fecha_apertura.strftime("%Y-%m-%d"),
            "horario_manana": {
                "apertura": horario_manana['apertura'].strftime('%H:%M'),
                "cierre": horario_manana['cierre'].strftime('%H:%M')
            }
        }
    
    # ============================================
    # CASO 2: ANTES DE LA APERTURA
    # ============================================
    if hora_actual < horario_hoy['apertura']:
        minutos_para_abrir = (
            datetime.combine(fecha_hora_actual.date(), horario_hoy['apertura']) -
            datetime.combine(fecha_hora_actual.date(), hora_actual)
        ).total_seconds() / 60
        
        tiempo_texto = formatear_tiempo_espera(minutos_para_abrir)
        
        mensaje = (
            f"⏰ El museo aún no está abierto\n\n"
            f"📅 Hoy {nombre_dia} abrimos a las {horario_hoy['apertura'].strftime('%H:%M')}\n\n"
            f"🕐 Faltan aproximadamente {tiempo_texto}\n\n"
            f"💡 Vuelve más tarde para disfrutar tu visita\n\n"
            f"📋 Horario de hoy: {horario_hoy['apertura'].strftime('%H:%M')} - "
            f"{horario_hoy['cierre'].strftime('%H:%M')}"
        )
        
        return False, mensaje, {
            "razon": "antes_apertura",
            "dia_actual": nombre_dia,
            "hora_apertura": horario_hoy['apertura'].strftime('%H:%M'),
            "hora_cierre": horario_hoy['cierre'].strftime('%H:%M'),
            "minutos_para_abrir": int(minutos_para_abrir)
        }
    
    # ============================================
    # CASO 3: DESPUÉS DEL CIERRE
    # ============================================
    if hora_actual >= horario_hoy['cierre']:
        dias_hasta_apertura = 1
        fecha_apertura = fecha_hora_actual + timedelta(days=dias_hasta_apertura)
        
        while obtener_horario_dia(fecha_apertura.weekday()) is None:
            dias_hasta_apertura += 1
            fecha_apertura = fecha_hora_actual + timedelta(days=dias_hasta_apertura)
        
        horario_manana = obtener_horario_dia(fecha_apertura.weekday())
        nombre_dia_manana = obtener_nombre_dia(fecha_apertura.weekday())
        
        mensaje = (
            f"🌙 El museo ya cerró por hoy\n\n"
            f"📅 Te recomendamos volver mañana ({nombre_dia_manana})\n\n"
            f"Podrás disfrutar el museo con más tiempo para explorar.\n\n"
            f"🕐 Horario de mañana ({nombre_dia_manana}): "
            f"{horario_manana['apertura'].strftime('%H:%M')} - {horario_manana['cierre'].strftime('%H:%M')}\n\n"
            f"{obtener_horarios_completos()}"
        )
        
        return False, mensaje, {
            "razon": "despues_cierre",
            "dia_actual": nombre_dia,
            "hora_cierre": horario_hoy['cierre'].strftime('%H:%M'),
            "proxima_apertura": fecha_apertura.strftime("%Y-%m-%d"),
            "horario_manana": {
                "apertura": horario_manana['apertura'].strftime('%H:%M'),
                "cierre": horario_manana['cierre'].strftime('%H:%M')
            }
        }
    
    # ============================================
    # CASO 4: ABIERTO
    # ============================================
    minutos_hasta_cierre = (
        datetime.combine(fecha_hora_actual.date(), horario_hoy['cierre']) -
        datetime.combine(fecha_hora_actual.date(), hora_actual)
    ).total_seconds() / 60
    
    mensaje = (
        f"✅ El museo está abierto\n\n"
        f"⏰ Tienes {int(minutos_hasta_cierre)} minutos hasta el cierre "
        f"({horario_hoy['cierre'].strftime('%H:%M')})"
    )
    
    return True, mensaje, {
        "razon": "abierto",
        "dia_actual": nombre_dia,
        "hora_apertura": horario_hoy['apertura'].strftime('%H:%M'),
        "hora_cierre": horario_hoy['cierre'].strftime('%H:%M'),
        "minutos_hasta_cierre": int(minutos_hasta_cierre)
    }


def calcular_tiempo_disponible(
    fecha_hora_actual: Optional[datetime] = None
) -> int:
    """Calcula cuántos minutos quedan hasta que cierre el museo"""
    if fecha_hora_actual is None:
        fecha_hora_actual = datetime.now()
    
    esta_abierto, _, info = validar_horario_museo(fecha_hora_actual)
    
    if not esta_abierto:
        return 0
    
    return info.get('minutos_hasta_cierre', 0)


def ajustar_itinerario_por_tiempo(
    duracion_solicitada: Optional[int],
    fecha_hora_actual: Optional[datetime] = None
) -> Tuple[bool, Optional[int], str]:
    """
    Ajusta la duración del itinerario según el tiempo disponible
    """
    if fecha_hora_actual is None:
        fecha_hora_actual = datetime.now()
    
    esta_abierto, mensaje_horario, info = validar_horario_museo(fecha_hora_actual)
    
    if not esta_abierto:
        return False, None, mensaje_horario
    
    minutos_disponibles = info['minutos_hasta_cierre']
    
    # ============================================
    # CASO 1: Menos de 30 minutos para cerrar
    # ============================================
    if minutos_disponibles < TIEMPO_MINIMO_VISITA:
        dias_hasta_apertura = 1
        fecha_apertura = fecha_hora_actual + timedelta(days=dias_hasta_apertura)
        
        while obtener_horario_dia(fecha_apertura.weekday()) is None:
            dias_hasta_apertura += 1
            fecha_apertura = fecha_hora_actual + timedelta(days=dias_hasta_apertura)
        
        horario_manana = obtener_horario_dia(fecha_apertura.weekday())
        nombre_dia_manana = obtener_nombre_dia(fecha_apertura.weekday())
        
        mensaje = (
            f"🚫 El museo cerrará muy pronto (en {minutos_disponibles} minutos)\n\n"
            f"😔 No hay tiempo suficiente para una visita significativa\n\n"
            f"📅 Te recomendamos volver en otro momento\n\n"
            f"Podrás disfrutar el museo con calma y aprovechar todas las áreas.\n\n"
            f"🕐 Horario de mañana ({nombre_dia_manana}): "
            f"{horario_manana['apertura'].strftime('%H:%M')} - {horario_manana['cierre'].strftime('%H:%M')}\n\n"
            f"{obtener_horarios_completos()}"
        )
        
        return False, None, mensaje
    
    # ============================================
    # CASO 2: Sin límite de tiempo solicitado
    # ============================================
    if duracion_solicitada is None:
        if minutos_disponibles >= 240:
            mensaje = (
                f"✅ Tiempo suficiente\n\n"
                f"Tienes {minutos_disponibles} minutos hasta el cierre.\n\n"
                f"Te generaré el recorrido completo del museo."
            )
            return True, None, mensaje
        
        elif minutos_disponibles >= 60:
            duracion_ajustada = int(minutos_disponibles * 0.8)
            mensaje = (
                f"⏰ Tiempo limitado\n\n"
                f"El museo cerrará a las {info['hora_cierre']} (en {minutos_disponibles} minutos).\n\n"
                f"😊 No podrás ver todas las áreas, pero te crearé un itinerario personalizado con las más relevantes.\n\n"
                f"💡 Tiempo disponible: {minutos_disponibles} minutos\n\n"
                f"📍 Áreas sugeridas: Las más importantes para ti"
            )
            return True, duracion_ajustada, mensaje
        
        else:
            duracion_ajustada = int(minutos_disponibles * 0.8)
            mensaje = (
                f"⏰ Tiempo muy limitado\n\n"
                f"Solo tienes {minutos_disponibles} minutos hasta el cierre.\n\n"
                f"😊 Te crearé un recorrido breve con las áreas más destacadas.\n\n"
                f"💡 Recomendación: Considera volver otro día para el recorrido completo"
            )
            return True, duracion_ajustada, mensaje
    
    # ============================================
    # CASO 3: Usuario especificó tiempo
    # ============================================
    else:
        if duracion_solicitada > minutos_disponibles:
            if duracion_solicitada - minutos_disponibles <= 15:
                duracion_ajustada = int(minutos_disponibles * 0.9)
                mensaje = (
                    f"✅ Itinerario ajustado\n\n"
                    f"Te generaré un recorrido de {duracion_ajustada} minutos para que termines antes del cierre."
                )
                return True, duracion_ajustada, mensaje
            
            else:
                duracion_ajustada = int(minutos_disponibles * 0.8)
                mensaje = (
                    f"⏰ Tiempo ajustado\n\n"
                    f"Solicitaste {duracion_solicitada} minutos, pero el museo cerrará en {minutos_disponibles} minutos.\n\n"
                    f"😊 Te crearé un itinerario de {duracion_ajustada} minutos con las áreas más relevantes."
                )
                return True, duracion_ajustada, mensaje
        
        else:
            mensaje = f"✅ Hay tiempo suficiente para tu visita de {duracion_solicitada} minutos"
            return True, duracion_solicitada, mensaje


def obtener_mensaje_horarios() -> str:
    """Retorna un mensaje formateado con todos los horarios"""
    return (
        "📅 Horarios del Museo Pumapungo:\n\n"
        "• Lunes: Cerrado\n\n"
        "• Martes a Viernes: 08:00 - 17:00\n\n"
        "• Sábados y Domingos: 10:00 - 16:00\n\n"
        "🎫 Entrada gratuita"
    )