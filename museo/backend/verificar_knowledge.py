# verificar_knowledge.py
# Script para ver QUÉ contiene el museo_knowledge.json actual

import json
from pathlib import Path

print("="*60)
print("🔍 VERIFICANDO museo_knowledge.json")
print("="*60)

json_path = Path("../museo_knowledge.json")

if not json_path.exists():
    print("❌ NO existe museo_knowledge.json")
    exit(1)

# Tamaño
tamaño = json_path.stat().st_size
print(f"\n📊 Tamaño: {tamaño:,} bytes ({tamaño/1024:.1f} KB)")

if tamaño < 30000:  # Menos de 30 KB
    print("⚠️ PROBLEMA: Tamaño muy pequeño (debería ser ~35-40 KB)")

# Leer contenido
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Verificar estructura
print(f"\n📋 Estructura:")
print(f"   - Museo: {data.get('museo', 'N/A')}")
print(f"   - Total áreas en JSON: {len(data.get('areas', {}))}")

# Analizar cada área
print(f"\n🔍 Contenido por área:")
print("="*60)

for codigo, info in data.get('areas', {}).items():
    nombre = info.get('nombre', 'Sin nombre')
    objetos = len(info.get('objetos_destacados', []))
    datos = len(info.get('datos_curiosos', []))
    temas = len(info.get('temas_principales', []))
    info_det = len(info.get('informacion_detallada', []))
    descripcion_len = len(info.get('descripcion', ''))
    historia_len = len(info.get('historia', ''))
    
    print(f"\n{codigo}: {nombre}")
    print(f"   Objetos destacados: {objetos}")
    print(f"   Datos curiosos: {datos}")
    print(f"   Temas principales: {temas}")
    print(f"   Información detallada: {info_det} párrafos")
    print(f"   Descripción: {descripcion_len} chars")
    print(f"   Historia: {historia_len} chars")
    
    # Mostrar primer dato curioso como ejemplo
    if datos > 0:
        primer_dato = info['datos_curiosos'][0]
        print(f"   Ejemplo dato: {primer_dato[:80]}...")
    else:
        print(f"   ❌ SIN datos curiosos")
    
    # Verificar si tiene información detallada
    if info_det == 0:
        print(f"   ❌ SIN información detallada")
    
    total_chars = descripcion_len + historia_len + sum(len(p) for p in info.get('informacion_detallada', []))
    print(f"   Total contenido: ~{total_chars:,} chars")

print("\n" + "="*60)
print("📊 RESUMEN:")
print("="*60)

total_objetos = sum(len(a.get('objetos_destacados', [])) for a in data.get('areas', {}).values())
total_datos = sum(len(a.get('datos_curiosos', [])) for a in data.get('areas', {}).values())
total_temas = sum(len(a.get('temas_principales', [])) for a in data.get('areas', {}).values())
total_info = sum(len(a.get('informacion_detallada', [])) for a in data.get('areas', {}).values())

print(f"Total objetos destacados: {total_objetos}")
print(f"Total datos curiosos: {total_datos}")
print(f"Total temas: {total_temas}")
print(f"Total párrafos info detallada: {total_info}")

print("\n💡 RECOMENDACIONES:")
print("="*60)

if tamaño < 30000:
    print("❌ El archivo es DEMASIADO PEQUEÑO")
    print("   → Reemplázalo con museo_knowledge_CORREGIDO.json")

if total_datos < 30:
    print("❌ Muy pocos datos curiosos")
    print("   → El archivo no tiene suficiente información")

if total_info < 30:
    print("❌ Muy pocos párrafos detallados")
    print("   → Necesitas más información de tus PDFs")

print("\n" + "="*60)