"""
SCRIPT DE VERIFICACION: Verifica que ia_service.py este correcto

EJECUTAR:
cd C:\\Users\\Tania\\Documents\\Tesis\\museo\\backend\\services
python verificar_ia_service.py
"""

import sys
import os

def verificar_archivo():
    print("=" * 80)
    print("🔍 VERIFICACION DE ia_service.py")
    print("=" * 80)
    print()
    
    # Verificar que existe
    if not os.path.exists("ia_service.py"):
        print("❌ ERROR: No se encuentra ia_service.py")
        print("   Ruta esperada: services/ia_service.py")
        return False
    
    print("✅ Archivo encontrado")
    
    # Leer archivo
    try:
        with open("ia_service.py", "r", encoding="utf-8") as f:
            contenido = f.read()
    except Exception as e:
        print(f"❌ Error leyendo archivo: {e}")
        return False
    
    print(f"✅ Archivo leído ({len(contenido)} caracteres)")
    print()
    
    # Verificaciones
    print("🔍 VERIFICANDO SINTAXIS:")
    print()
    
    # 1. Importaciones
    if "import requests" in contenido:
        print("✅ import requests")
    else:
        print("❌ Falta: import requests")
    
    if "import json" in contenido:
        print("✅ import json")
    else:
        print("❌ Falta: import json")
    
    if "from config import get_settings" in contenido:
        print("✅ from config import get_settings")
    else:
        print("❌ Falta: from config import get_settings")
    
    print()
    
    # 2. Clase
    if "class IAGenerativaService:" in contenido:
        print("✅ Clase IAGenerativaService definida")
    else:
        print("❌ Falta: class IAGenerativaService")
    
    print()
    
    # 3. Métodos importantes
    metodos = [
        "__init__",
        "_construir_prompt_itinerario",
        "generar_itinerario",
        "_extraer_json",
        "_validar_itinerario"
    ]
    
    print("🔍 METODOS:")
    for metodo in metodos:
        if f"def {metodo}" in contenido:
            print(f"✅ {metodo}")
        else:
            print(f"❌ Falta: {metodo}")
    
    print()
    
    # 4. Variable crítica
    print("🔍 VARIABLES CRITICAS:")
    if "prompt = " in contenido:
        print("✅ Variable 'prompt' se asigna")
    else:
        print("❌ No se encuentra asignacion de 'prompt'")
    
    if "ia_service = IAGenerativaService()" in contenido:
        print("✅ Instancia global ia_service")
    else:
        print("❌ Falta: ia_service = IAGenerativaService()")
    
    print()
    
    # 5. Intentar importar
    print("🔍 PROBANDO IMPORTACION:")
    try:
        # Agregar directorio al path
        sys.path.insert(0, os.path.dirname(os.path.abspath("ia_service.py")))
        
        # Intentar importar
        import ia_service as ia_mod
        
        print("✅ Importacion exitosa")
        
        # Verificar clase
        if hasattr(ia_mod, 'IAGenerativaService'):
            print("✅ Clase IAGenerativaService accesible")
        else:
            print("❌ Clase IAGenerativaService no encontrada")
        
        # Verificar instancia
        if hasattr(ia_mod, 'ia_service'):
            print("✅ Instancia ia_service accesible")
            
            # Verificar métodos
            servicio = ia_mod.ia_service
            if hasattr(servicio, 'generar_itinerario'):
                print("✅ Metodo generar_itinerario accesible")
            else:
                print("❌ Metodo generar_itinerario no encontrado")
        else:
            print("❌ Instancia ia_service no encontrada")
    
    except SyntaxError as e:
        print(f"❌ ERROR DE SINTAXIS: {e}")
        print(f"   Linea {e.lineno}: {e.text}")
        return False
    
    except Exception as e:
        print(f"❌ Error al importar: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    print("=" * 80)
    print("✅ VERIFICACION COMPLETADA")
    print("=" * 80)
    print()
    print("El archivo parece estar correcto.")
    print()
    
    return True

if __name__ == "__main__":
    exito = verificar_archivo()
    
    if exito:
        print("✅ TODO BIEN - Puedes usar ia_service.py")
        print()
        print("SIGUIENTE PASO:")
        print("1. Reinicia el backend:")
        print("   uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        print()
        print("2. Intenta generar un itinerario")
    else:
        print("❌ HAY PROBLEMAS - Revisa los errores arriba")
        print()
        print("SOLUCION:")
        print("1. Descarga de nuevo el archivo ia_service_CORREGIDO.py")
        print("2. Renombralo a ia_service.py")
        print("3. Ejecuta este script de nuevo")