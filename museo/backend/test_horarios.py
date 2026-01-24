# test_horarios.py
# Script para probar la validación de horarios sin cambiar fecha del sistema

from datetime import datetime, time, timedelta
import sys
sys.path.append('.')

from utils.horarios_museo import (
    validar_horario_museo,
    ajustar_itinerario_por_tiempo,
    obtener_mensaje_horarios,
    calcular_tiempo_disponible
)

def test_caso(nombre, fecha_hora, duracion_solicitada=None):
    """Prueba un caso específico"""
    print(f"\n{'='*70}")
    print(f"🧪 TEST: {nombre}")
    print(f"📅 Fecha/Hora simulada: {fecha_hora.strftime('%A %d/%m/%Y %H:%M')}")
    if duracion_solicitada:
        print(f"⏱️  Duración solicitada: {duracion_solicitada} minutos")
    else:
        print(f"⏱️  Duración solicitada: Sin límite (\"No tengo prisa\")")
    print(f"{'='*70}")
    
    # Validar horario
    esta_abierto, mensaje, info = validar_horario_museo(fecha_hora)
    
    print(f"\n📊 RESULTADO DE VALIDACIÓN:")
    print(f"   Estado: {'✅ ABIERTO' if esta_abierto else '❌ CERRADO'}")
    print(f"   Razón: {info.get('razon', 'N/A')}")
    
    if esta_abierto:
        print(f"   Minutos hasta cierre: {info.get('minutos_hasta_cierre', 0)}")
    
    print(f"\n💬 MENSAJE AL USUARIO:")
    print(f"   {mensaje}")
    
    # Ajustar itinerario
    puede_generar, duracion_ajustada, mensaje_ajuste = ajustar_itinerario_por_tiempo(
        duracion_solicitada,
        fecha_hora
    )
    
    print(f"\n🎯 DECISIÓN DEL SISTEMA:")
    print(f"   Puede generar: {'✅ SÍ' if puede_generar else '❌ NO'}")
    
    if puede_generar:
        if duracion_ajustada != duracion_solicitada:
            print(f"   Duración ajustada: {duracion_solicitada} -> {duracion_ajustada} minutos")
        else:
            print(f"   Duración final: {duracion_ajustada or 'Sin límite (completo)'} minutos")
        
        if duracion_ajustada is None:
            print(f"   Tipo itinerario: 🎨 COMPLETO (todas las áreas)")
        elif duracion_ajustada >= 180:
            print(f"   Tipo itinerario: 🎨 LARGO (5-7 áreas)")
        elif duracion_ajustada >= 90:
            print(f"   Tipo itinerario: 📚 MEDIO (4-5 áreas)")
        else:
            print(f"   Tipo itinerario: ⚡ BREVE (2-3 áreas)")
    
    if mensaje_ajuste and mensaje_ajuste != mensaje:
        print(f"\n💬 MENSAJE ADICIONAL:")
        print(f"   {mensaje_ajuste}")


def main():
    """Ejecuta todos los tests"""
    print("\n" + "="*70)
    print("🧪 TESTS DEL SISTEMA DE VALIDACIÓN DE HORARIOS")
    print("="*70)
    
    # CASO 1: Lunes (Cerrado)
    lunes = datetime(2026, 1, 26, 14, 0)  # Lunes 26 enero 14:00
    test_caso("Lunes 14:00 - Museo cerrado", lunes)
    
    # CASO 2: Jueves después del cierre
    jueves_tarde = datetime(2026, 1, 29, 18, 0)  # Jueves 18:00
    test_caso("Jueves 18:00 - Después del cierre", jueves_tarde)
    
    # CASO 3: Martes antes de abrir
    martes_temprano = datetime(2026, 1, 27, 7, 0)  # Martes 7:00
    test_caso("Martes 7:00 - Antes de abrir", martes_temprano)
    
    # CASO 4: Martes 16:45 - Cierra en 15 min
    martes_16_45 = datetime(2026, 1, 27, 16, 45)
    test_caso("Martes 16:45 - Sin prisa (solo 15 min)", martes_16_45, None)
    
    # CASO 5: Martes 16:00 - Cierra en 60 min
    martes_16_00 = datetime(2026, 1, 27, 16, 0)
    test_caso("Martes 16:00 - Sin prisa (60 min disponibles)", martes_16_00, None)
    
    # CASO 6: Martes 13:00 - Cierra en 240 min
    martes_13_00 = datetime(2026, 1, 27, 13, 0)
    test_caso("Martes 13:00 - Sin prisa (240 min disponibles)", martes_13_00, None)
    
    # CASO 7: Martes 15:00 con 120 min solicitados
    martes_15_00 = datetime(2026, 1, 27, 15, 0)
    test_caso("Martes 15:00 - Solicita 120 min", martes_15_00, 120)
    
    # CASO 8: Martes 15:30 con 180 min solicitados
    martes_15_30 = datetime(2026, 1, 27, 15, 30)
    test_caso("Martes 15:30 - Solicita 180 min (excede)", martes_15_30, 180)
    
    # CASO 9: Sábado antes de abrir
    sabado_temprano = datetime(2026, 1, 31, 9, 0)  # Sábado 9:00
    test_caso("Sábado 9:00 - Antes de abrir", sabado_temprano)
    
    # CASO 10: Domingo 14:00 - Cierra en 120 min
    domingo_14 = datetime(2026, 2, 1, 14, 0)  # Domingo 14:00
    test_caso("Domingo 14:00 - Sin prisa (120 min)", domingo_14, None)
    
    # CASO 11: Martes 9:00 - Horario óptimo
    martes_9 = datetime(2026, 1, 27, 9, 0)
    test_caso("Martes 9:00 - Horario óptimo", martes_9, None)
    
    print("\n" + "="*70)
    print("✅ TESTS COMPLETADOS")
    print("="*70)
    print("\n📋 HORARIOS DEL MUSEO:")
    print(obtener_mensaje_horarios())


if __name__ == "__main__":
    main()