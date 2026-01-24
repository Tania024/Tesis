# diagnostico_completo.py
# Script para diagnosticar problemas con knowledge base y generación

import sys
import json
from pathlib import Path

print("=" * 60)
print("🔍 DIAGNÓSTICO DEL SISTEMA")
print("=" * 60)

# 1. Verificar museo_knowledge.json
print("\n📚 1. VERIFICANDO KNOWLEDGE BASE:")
print("-" * 60)

posibles_rutas = [
    Path("museo_knowledge.json"),
    Path("../museo_knowledge.json"),
    Path(__file__).parent.parent / "museo_knowledge.json",
]

kb_encontrado = False
for ruta in posibles_rutas:
    if ruta.exists():
        print(f"✅ Encontrado: {ruta.absolute()}")
        kb_encontrado = True
        
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                kb = json.load(f)
            
            areas = kb.get('areas', {})
            print(f"   📊 Total de áreas: {len(areas)}")
            
            for codigo, info in areas.items():
                nombre = info.get('nombre', 'Sin nombre')
                objetos = len(info.get('objetos_destacados', []))
                datos = len(info.get('datos_curiosos', []))
                temas = len(info.get('temas_principales', []))
                info_detallada = len(info.get('informacion_detallada', []))
                
                print(f"   • {codigo}: {nombre}")
                print(f"     - {objetos} objetos destacados")
                print(f"     - {datos} datos curiosos")
                print(f"     - {temas} temas principales")
                print(f"     - {info_detallada} párrafos de información detallada")
            
            break
        except Exception as e:
            print(f"   ❌ Error leyendo: {e}")
    else:
        print(f"   ⚠️ No existe: {ruta.absolute()}")

if not kb_encontrado:
    print("   ❌ PROBLEMA: No se encontró museo_knowledge.json")

# 2. Verificar ia_service.py
print("\n🔧 2. VERIFICANDO ia_service.py:")
print("-" * 60)

ia_service_path = Path("services/ia_service.py")
if ia_service_path.exists():
    print(f"✅ Encontrado: {ia_service_path.absolute()}")
    
    with open(ia_service_path, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Verificar métodos críticos
    tiene_generar = "def generar_itinerario(" in contenido
    tiene_progresivo = "def generar_itinerario_progresivo(" in contenido
    tiene_cargar_kb = "def _cargar_knowledge_base(" in contenido
    tiene_obtener_info = "def _obtener_info_area(" in contenido
    tiene_background = "def _generar_resto_areas_background(" in contenido
    
    print(f"   • generar_itinerario(): {'✅' if tiene_generar else '❌'}")
    print(f"   • generar_itinerario_progresivo(): {'✅' if tiene_progresivo else '❌'}")
    print(f"   • _cargar_knowledge_base(): {'✅' if tiene_cargar_kb else '❌'}")
    print(f"   • _obtener_info_area(): {'✅' if tiene_obtener_info else '❌'}")
    print(f"   • _generar_resto_areas_background(): {'✅' if tiene_background else '❌'}")
    
    todas_presentes = (
    tiene_generar
    and tiene_progresivo
    and tiene_cargar_kb
    and tiene_obtener_info
    and tiene_background
)

if not todas_presentes:
    print("\n   ❌ PROBLEMA: Faltan métodos críticos")

else:
    print(f"   ❌ No existe: {ia_service_path.absolute()}")

# 3. Verificar Ollama
print("\n🤖 3. VERIFICANDO OLLAMA:")
print("-" * 60)

try:
    import requests
    response = requests.get("http://localhost:11434/api/tags", timeout=5)
    if response.status_code == 200:
        print("✅ Ollama está corriendo")
        modelos = response.json().get("models", [])
        print(f"   📊 Modelos disponibles: {len(modelos)}")
        for modelo in modelos:
            print(f"   • {modelo.get('name')}")
    else:
        print("❌ Ollama no responde correctamente")
except Exception as e:
    print(f"❌ Error conectando con Ollama: {e}")

# 4. Verificar estructura de directorios
print("\n📁 4. VERIFICANDO ESTRUCTURA:")
print("-" * 60)

archivos_criticos = [
    "services/ia_service.py",
    "routers/ia.py",
    "models.py",
    "museo_knowledge.json"
]

for archivo in archivos_criticos:
    ruta = Path(archivo)
    if ruta.exists():
        tamaño = ruta.stat().st_size / 1024  # KB
        print(f"✅ {archivo} ({tamaño:.1f} KB)")
    else:
        print(f"❌ {archivo} - NO EXISTE")

print("\n" + "=" * 60)
print("📋 RESUMEN:")
print("=" * 60)

if kb_encontrado:
    print("✅ Knowledge base encontrado y con datos")
else:
    print("❌ Knowledge base NO encontrado o vacío")

print("\n💡 RECOMENDACIONES:")
print("-" * 60)

if not kb_encontrado:
    print("1. Verifica que museo_knowledge.json esté en backend/")
    print("2. El archivo debe tener el formato JSON correcto con áreas")

print("\n🔍 Revisa los logs del backend para más detalles")
print("=" * 60)