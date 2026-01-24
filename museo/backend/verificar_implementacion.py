# verificar_implementacion.py
# Script para verificar que la implementación de horarios esté correcta

import os
import sys

def verificar_estructura():
    """Verifica que la estructura de archivos sea correcta"""
    print("\n" + "="*70)
    print("🔍 VERIFICANDO ESTRUCTURA DE ARCHIVOS")
    print("="*70 + "\n")
    
    archivos_requeridos = [
        ("utils/", "Carpeta utils"),
        ("utils/__init__.py", "Archivo __init__.py"),
        ("utils/horarios_museo.py", "Módulo de horarios"),
        ("routers/ia.py", "Router de IA"),
    ]
    
    errores = []
    
    for archivo, descripcion in archivos_requeridos:
        existe = os.path.exists(archivo)
        simbolo = "✅" if existe else "❌"
        print(f"{simbolo} {descripcion}: {archivo}")
        
        if not existe:
            errores.append(f"Falta: {archivo}")
    
    if errores:
        print(f"\n❌ ERRORES ENCONTRADOS:")
        for error in errores:
            print(f"   • {error}")
        return False
    else:
        print(f"\n✅ Estructura de archivos correcta")
        return True


def verificar_imports():
    """Verifica que los imports estén correctos en ia.py"""
    print("\n" + "="*70)
    print("🔍 VERIFICANDO IMPORTS EN routers/ia.py")
    print("="*70 + "\n")
    
    try:
        with open("routers/ia.py", "r", encoding="utf-8") as f:
            contenido = f.read()
        
        imports_requeridos = [
            ("from datetime import datetime", "Import de datetime"),
            ("from utils.horarios_museo import", "Import de utilidades de horarios"),
            ("validar_horario_museo", "Función validar_horario_museo"),
            ("ajustar_itinerario_por_tiempo", "Función ajustar_itinerario_por_tiempo"),
            ("obtener_mensaje_horarios", "Función obtener_mensaje_horarios"),
        ]
        
        errores = []
        
        for texto_buscar, descripcion in imports_requeridos:
            existe = texto_buscar in contenido
            simbolo = "✅" if existe else "❌"
            print(f"{simbolo} {descripcion}")
            
            if not existe:
                errores.append(f"Falta import: {descripcion}")
        
        if errores:
            print(f"\n❌ ERRORES ENCONTRADOS:")
            for error in errores:
                print(f"   • {error}")
            return False
        else:
            print(f"\n✅ Imports correctos")
            return True
            
    except FileNotFoundError:
        print(f"❌ No se encontró el archivo routers/ia.py")
        return False
    except Exception as e:
        print(f"❌ Error al leer archivo: {e}")
        return False


def verificar_validacion():
    """Verifica que el bloque de validación esté presente"""
    print("\n" + "="*70)
    print("🔍 VERIFICANDO BLOQUE DE VALIDACIÓN")
    print("="*70 + "\n")
    
    try:
        with open("routers/ia.py", "r", encoding="utf-8") as f:
            contenido = f.read()
        
        validaciones_requeridas = [
            ("fecha_hora_actual = datetime.now()", "Obtener fecha/hora actual"),
            ("ajustar_itinerario_por_tiempo(", "Llamada a ajustar_itinerario_por_tiempo"),
            ("puede_generar, duracion_ajustada, mensaje_horario", "Variables de resultado"),
            ("if not puede_generar:", "Verificación de puede_generar"),
            ("tiempo_para_itinerario", "Variable tiempo_para_itinerario"),
        ]
        
        errores = []
        
        for texto_buscar, descripcion in validaciones_requeridas:
            existe = texto_buscar in contenido
            simbolo = "✅" if existe else "❌"
            print(f"{simbolo} {descripcion}")
            
            if not existe:
                errores.append(f"Falta: {descripcion}")
        
        # Verificar que NO haya código duplicado
        filtrado_intereses = contenido.count("if solicitud.intereses and")
        
        if filtrado_intereses > 2:  # Solo debe aparecer 1 vez en el código de filtrado
            print(f"⚠️  ADVERTENCIA: Código de filtrado aparece {filtrado_intereses} veces (debería ser 1)")
            errores.append(f"Código duplicado: filtrado por intereses aparece {filtrado_intereses} veces")
        else:
            print(f"✅ No hay código duplicado de filtrado")
        
        if errores:
            print(f"\n❌ ERRORES ENCONTRADOS:")
            for error in errores:
                print(f"   • {error}")
            return False
        else:
            print(f"\n✅ Bloque de validación correcto")
            return True
            
    except FileNotFoundError:
        print(f"❌ No se encontró el archivo routers/ia.py")
        return False
    except Exception as e:
        print(f"❌ Error al leer archivo: {e}")
        return False


def verificar_reemplazos():
    """Verifica que se hayan reemplazado solicitud.tiempo_disponible correctamente"""
    print("\n" + "="*70)
    print("🔍 VERIFICANDO REEMPLAZOS DE tiempo_disponible")
    print("="*70 + "\n")
    
    try:
        with open("routers/ia.py", "r", encoding="utf-8") as f:
            contenido = f.read()
        
        # Contar usos de tiempo_para_itinerario
        usos_tiempo_para = contenido.count("tiempo_para_itinerario")
        
        # Contar usos problemáticos de solicitud.tiempo_disponible
        # (excluir el de la comparación if duracion_ajustada != solicitud.tiempo_disponible)
        lineas = contenido.split('\n')
        usos_problemáticos = 0
        
        for i, linea in enumerate(lineas, 1):
            if "solicitud.tiempo_disponible" in linea:
                # Es OK si es en la comparación o en ajustar_itinerario_por_tiempo
                if "duracion_ajustada != solicitud.tiempo_disponible" in linea:
                    continue
                if "ajustar_itinerario_por_tiempo(" in linea:
                    continue
                
                # Es problemático
                usos_problemáticos += 1
                print(f"⚠️  Línea {i}: {linea.strip()}")
        
        print(f"\n📊 Estadísticas:")
        print(f"   • tiempo_para_itinerario: {usos_tiempo_para} usos")
        print(f"   • solicitud.tiempo_disponible problemático: {usos_problemáticos} usos")
        
        if usos_tiempo_para >= 4 and usos_problemáticos == 0:
            print(f"\n✅ Reemplazos correctos")
            return True
        else:
            print(f"\n❌ ERRORES:")
            if usos_tiempo_para < 4:
                print(f"   • Faltan usos de tiempo_para_itinerario (esperado: ≥4, encontrado: {usos_tiempo_para})")
            if usos_problemáticos > 0:
                print(f"   • Hay {usos_problemáticos} usos problemáticos de solicitud.tiempo_disponible")
            return False
            
    except FileNotFoundError:
        print(f"❌ No se encontró el archivo routers/ia.py")
        return False
    except Exception as e:
        print(f"❌ Error al leer archivo: {e}")
        return False


def main():
    """Ejecuta todas las verificaciones"""
    print("\n" + "="*70)
    print("🧪 VERIFICADOR DE IMPLEMENTACIÓN - SISTEMA DE HORARIOS")
    print("="*70)
    
    resultados = []
    
    # Ejecutar verificaciones
    resultados.append(("Estructura de archivos", verificar_estructura()))
    resultados.append(("Imports", verificar_imports()))
    resultados.append(("Bloque de validación", verificar_validacion()))
    resultados.append(("Reemplazos", verificar_reemplazos()))
    
    # Resumen
    print("\n" + "="*70)
    print("📊 RESUMEN DE VERIFICACIÓN")
    print("="*70 + "\n")
    
    todas_correctas = True
    
    for nombre, resultado in resultados:
        simbolo = "✅" if resultado else "❌"
        print(f"{simbolo} {nombre}")
        if not resultado:
            todas_correctas = False
    
    print("\n" + "="*70)
    
    if todas_correctas:
        print("✅ ¡IMPLEMENTACIÓN CORRECTA!")
        print("="*70)
        print("\n💡 Próximos pasos:")
        print("   1. Reinicia el backend: python main.py")
        print("   2. Prueba generar un itinerario")
        print("   3. Verifica logs para ver mensajes de horarios")
        print("   4. Opcional: Ejecuta python test_horarios.py para probar escenarios")
        return 0
    else:
        print("❌ HAY ERRORES EN LA IMPLEMENTACIÓN")
        print("="*70)
        print("\n💡 Revisa los errores arriba y corrige:")
        print("   • Asegúrate de tener todos los archivos")
        print("   • Verifica que los imports estén correctos")
        print("   • Revisa que el bloque de validación esté presente")
        print("   • Confirma que los reemplazos sean correctos")
        return 1


if __name__ == "__main__":
    sys.exit(main())