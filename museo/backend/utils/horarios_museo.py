# utils/horarios_museo.py
# Validación de horarios del Museo Pumapungo

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

# Tiempo mínimo necesario para que valga la pena visitar (30 minutos)
TIEMPO_MINIMO_VISITA = 30


def obtener_horario_dia(dia_semana: int) -> Optional[Dict]:
    """
    Obtiene el horario de un día específico
    
    Args:
        dia_semana: 0=Lunes, 1=Martes, ..., 6=Domingo
    
    Returns:
        Dict con 'apertura' y 'cierre' o None si está cerrado
    """
    return HORARIOS_MUSEO.get(dia_semana)


def obtener_nombre_dia(dia_semana: int) -> str:
    """Obtiene el nombre del día en español"""
    return DIAS_SEMANA.get(dia_semana, "Desconocido")


def validar_horario_museo(
    fecha_hora_actual: Optional[datetime] = None
) -> Tuple[bool, str, Dict]:
    """
    Valida si el museo está abierto en este momento
    
    Args:
        fecha_hora_actual: Fecha y hora a validar (None = ahora)
    
    Returns:
        Tupla de (está_abierto, mensaje, info_adicional)
    """
    if fecha_hora_actual is None:
        fecha_hora_actual = datetime.now()
    
    dia_semana = fecha_hora_actual.weekday()  # 0=Lunes, 6=Domingo
    hora_actual = fecha_hora_actual.time()
    
    nombre_dia = obtener_nombre_dia(dia_semana)
    horario_hoy = obtener_horario_dia(dia_semana)
    
    # ============================================
    # CASO 1: LUNES (CERRADO)
    # ============================================
    if horario_hoy is None:
        # Calcular próximo día de apertura (Martes)
        dias_hasta_apertura = 1  # Mañana es martes
        fecha_apertura = fecha_hora_actual + timedelta(days=dias_hasta_apertura)
        horario_manana = obtener_horario_dia(fecha_apertura.weekday())
        
        mensaje = (
            f"🚫 El Museo Pumapungo está cerrado los {nombre_dia}.\n\n"
            f"📅 **Vuelve mañana ({obtener_nombre_dia(fecha_apertura.weekday())})**\n"
            f"⏰ Horario: {horario_manana['apertura'].strftime('%H:%M')} - "
            f"{horario_manana['cierre'].strftime('%H:%M')}\n\n"
            f"📋 **Horarios completos:**\n"
            f"• Martes a Viernes: 8:00 - 17:00\n"
            f"• Sábados y Domingos: 10:00 - 16:00\n"
            f"• Lunes: Cerrado"
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
        
        mensaje = (
            f"⏰ El museo aún no está abierto.\n\n"
            f"📅 Hoy {nombre_dia} abrimos a las **{horario_hoy['apertura'].strftime('%H:%M')}**\n"
            f"🕐 Faltan aproximadamente **{int(minutos_para_abrir)} minutos** para abrir\n\n"
            f"💡 **Vuelve a las {horario_hoy['apertura'].strftime('%H:%M')}** para disfrutar tu visita\n\n"
            f"⏰ Horario de hoy: {horario_hoy['apertura'].strftime('%H:%M')} - "
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
        # Calcular próximo día de apertura
        dias_hasta_apertura = 1
        fecha_apertura = fecha_hora_actual + timedelta(days=dias_hasta_apertura)
        
        # Si mañana es lunes, saltamos al martes
        while obtener_horario_dia(fecha_apertura.weekday()) is None:
            dias_hasta_apertura += 1
            fecha_apertura = fecha_hora_actual + timedelta(days=dias_hasta_apertura)
        
        horario_manana = obtener_horario_dia(fecha_apertura.weekday())
        nombre_dia_manana = obtener_nombre_dia(fecha_apertura.weekday())
        
        mensaje = (
            f"🌙 El museo ya cerró por hoy.\n\n"
            f"📅 **Vuelve mañana ({nombre_dia_manana})**\n"
            f"⏰ Horario: {horario_manana['apertura'].strftime('%H:%M')} - "
            f"{horario_manana['cierre'].strftime('%H:%M')}\n\n"
            f"💡 Podrás disfrutar de tu visita con más tiempo"
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
    # CASO 4: ABIERTO - Calcular tiempo disponible
    # ============================================
    
    # Calcular minutos hasta el cierre
    minutos_hasta_cierre = (
        datetime.combine(fecha_hora_actual.date(), horario_hoy['cierre']) -
        datetime.combine(fecha_hora_actual.date(), hora_actual)
    ).total_seconds() / 60
    
    mensaje = (
        f"✅ El museo está abierto\n"
        f"⏰ Tienes **{int(minutos_hasta_cierre)} minutos** hasta el cierre "
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
    """
    Calcula cuántos minutos quedan hasta que cierre el museo
    
    Returns:
        Minutos disponibles (0 si está cerrado)
    """
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
    
    Args:
        duracion_solicitada: Duración que el usuario quiere (None = sin límite)
        fecha_hora_actual: Momento actual (None = ahora)
    
    Returns:
        Tupla de (puede_generar, duracion_ajustada, mensaje)
    """
    if fecha_hora_actual is None:
        fecha_hora_actual = datetime.now()
    
    # Validar que el museo esté abierto
    esta_abierto, mensaje_horario, info = validar_horario_museo(fecha_hora_actual)
    
    if not esta_abierto:
        return False, None, mensaje_horario
    
    minutos_disponibles = info['minutos_hasta_cierre']
    
    # ============================================
    # CASO 1: Menos de 30 minutos para cerrar
    # ============================================
    if minutos_disponibles < TIEMPO_MINIMO_VISITA:
        mensaje = (
            f"⏰ **El museo cerrará muy pronto** (en {minutos_disponibles} minutos)\n\n"
            f"😔 No hay tiempo suficiente para una visita significativa.\n\n"
            f"📅 **Te recomendamos volver mañana**\n"
            f"Podrás disfrutar el museo con calma y aprovechar todas las áreas.\n\n"
        )
        
        # Agregar info del siguiente día
        dias_hasta_apertura = 1
        fecha_apertura = fecha_hora_actual + timedelta(days=dias_hasta_apertura)
        
        while obtener_horario_dia(fecha_apertura.weekday()) is None:
            dias_hasta_apertura += 1
            fecha_apertura = fecha_hora_actual + timedelta(days=dias_hasta_apertura)
        
        horario_manana = obtener_horario_dia(fecha_apertura.weekday())
        nombre_dia_manana = obtener_nombre_dia(fecha_apertura.weekday())
        
        mensaje += (
            f"⏰ **Horario de mañana ({nombre_dia_manana}):**\n"
            f"{horario_manana['apertura'].strftime('%H:%M')} - "
            f"{horario_manana['cierre'].strftime('%H:%M')}"
        )
        
        return False, None, mensaje
    
    # ============================================
    # CASO 2: Sin límite de tiempo solicitado
    # ============================================
    if duracion_solicitada is None:
        # Usuario dijo "no tengo prisa" pero el museo va a cerrar
        
        # Si hay más de 240 minutos (4 horas), puede hacer recorrido completo
        if minutos_disponibles >= 240:
            mensaje = (
                f"✅ **Perfecto**\n"
                f"Tienes {minutos_disponibles} minutos hasta el cierre.\n"
                f"Te generaré el recorrido completo del museo."
            )
            return True, None, mensaje
        
        # Si hay entre 60 y 240 minutos, ofrecer recorrido parcial
        elif minutos_disponibles >= 60:
            mensaje = (
                f"⏰ **Tiempo limitado**\n\n"
                f"El museo cerrará a las {info['hora_cierre']} "
                f"(en {minutos_disponibles} minutos).\n\n"
                f"😊 No podrás ver todas las áreas, pero te crearé un itinerario "
                f"personalizado con las áreas más relevantes según tus intereses.\n\n"
                f"💡 **Tiempo disponible:** {minutos_disponibles} minutos\n"
                f"📍 **Áreas sugeridas:** Las más importantes para ti"
            )
            # Ajustar a 80% del tiempo disponible (margen de seguridad)
            duracion_ajustada = int(minutos_disponibles * 0.8)
            return True, duracion_ajustada, mensaje
        
        # Si hay menos de 60 minutos, recorrido muy breve
        else:
            mensaje = (
                f"⏰ **Tiempo muy limitado**\n\n"
                f"Solo tienes {minutos_disponibles} minutos hasta el cierre.\n\n"
                f"😊 Te crearé un recorrido breve con las áreas más destacadas "
                f"para que tu visita no sea en vano.\n\n"
                f"💡 **Recomendación:** Considera volver otro día para el recorrido completo"
            )
            duracion_ajustada = int(minutos_disponibles * 0.8)
            return True, duracion_ajustada, mensaje
    
    # ============================================
    # CASO 3: Usuario especificó tiempo
    # ============================================
    else:
        # Si el tiempo solicitado es mayor al disponible
        if duracion_solicitada > minutos_disponibles:
            # Si el exceso es menor a 15 minutos, ajustar silenciosamente
            if duracion_solicitada - minutos_disponibles <= 15:
                duracion_ajustada = int(minutos_disponibles * 0.9)
                mensaje = (
                    f"✅ **Itinerario ajustado**\n"
                    f"Te generaré un recorrido de {duracion_ajustada} minutos "
                    f"para que termines antes del cierre."
                )
                return True, duracion_ajustada, mensaje
            
            # Si el exceso es mayor, informar
            else:
                duracion_ajustada = int(minutos_disponibles * 0.8)
                mensaje = (
                    f"⏰ **Tiempo ajustado**\n\n"
                    f"Solicitaste {duracion_solicitada} minutos, pero el museo "
                    f"cerrará en {minutos_disponibles} minutos.\n\n"
                    f"😊 Te crearé un itinerario de {duracion_ajustada} minutos "
                    f"con las áreas más relevantes."
                )
                return True, duracion_ajustada, mensaje
        
        # El tiempo solicitado cabe en el disponible
        else:
            mensaje = f"✅ Hay tiempo suficiente para tu visita de {duracion_solicitada} minutos"
            return True, duracion_solicitada, mensaje


def obtener_mensaje_horarios() -> str:
    """Retorna un mensaje formateado con todos los horarios"""
    return (
        "📅 **Horarios del Museo Pumapungo:**\n\n"
        "• **Lunes:** Cerrado\n"
        "• **Martes a Viernes:** 8:00 - 17:00\n"
        "• **Sábados y Domingos:** 10:00 - 16:00\n\n"
        "🎫 Entrada gratuita"
    )