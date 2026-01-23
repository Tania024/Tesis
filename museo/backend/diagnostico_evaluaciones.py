"""
DIAGNÓSTICO: Verificar sistema de evaluaciones

Ejecutar:
cd C:\\Users\\Tania\\Documents\\Tesis\\museo\\backend
python diagnostico_evaluaciones.py
"""

import sys
import os

print("=" * 80)
print("🔍 DIAGNÓSTICO DEL SISTEMA DE EVALUACIONES")
print("=" * 80)
print()

# 1. Verificar archivo evaluacion.py
print("📋 PASO 1: Verificar archivos")
print("-" * 80)

archivos_requeridos = [
    "models/evaluacion.py",
    "schemas/evaluacion.py",
    "routers/evaluaciones.py"
]

for archivo in archivos_requeridos:
    if os.path.exists(archivo):
        print(f"✅ {archivo}")
    else:
        print(f"❌ {archivo} - NO EXISTE")

print()

# 2. Verificar imports
print("📦 PASO 2: Verificar imports")
print("-" * 80)

try:
    from models import Evaluacion
    print("✅ Evaluacion importado correctamente")
except ImportError as e:
    print(f"❌ Error importando Evaluacion: {e}")
except Exception as e:
    print(f"❌ Error: {e}")

try:
    from schemas.evaluacion import EvaluacionCreate, EvaluacionResponse
    print("✅ Schemas importados correctamente")
except ImportError as e:
    print(f"❌ Error importando schemas: {e}")

try:
    from routers import evaluaciones
    print("✅ Router importado correctamente")
except ImportError as e:
    print(f"❌ Error importando router: {e}")

print()

# 3. Verificar tabla en BD
print("💾 PASO 3: Verificar tabla en base de datos")
print("-" * 80)

try:
    from database import engine
    from sqlalchemy import inspect
    
    inspector = inspect(engine)
    tablas = inspector.get_table_names()
    
    print(f"Tablas encontradas: {len(tablas)}")
    for tabla in sorted(tablas):
        marca = "✅" if tabla == "evaluaciones" else "  "
        print(f"{marca} {tabla}")
    
    if "evaluaciones" in tablas:
        print()
        print("✅ Tabla 'evaluaciones' existe")
        
        # Ver columnas
        columnas = inspector.get_columns("evaluaciones")
        print(f"\nColumnas de 'evaluaciones': {len(columnas)}")
        for col in columnas:
            print(f"   • {col['name']} ({col['type']})")
    else:
        print()
        print("❌ Tabla 'evaluaciones' NO existe")
        print("   Ejecuta: python crear_tabla_evaluaciones.py")

except Exception as e:
    print(f"❌ Error conectando a BD: {e}")

print()

# 4. Verificar router en main.py
print("🔌 PASO 4: Verificar router en main.py")
print("-" * 80)

if os.path.exists("main.py"):
    with open("main.py", "r", encoding="utf-8") as f:
        contenido = f.read()
    
    if "evaluaciones" in contenido:
        print("✅ 'evaluaciones' mencionado en main.py")
        
        if "include_router(evaluaciones.router)" in contenido:
            print("✅ Router registrado correctamente")
        else:
            print("⚠️ Router NO registrado (falta include_router)")
    else:
        print("❌ 'evaluaciones' NO encontrado en main.py")
else:
    print("❌ main.py no encontrado")

print()

# 5. Verificar relación en Itinerario
print("🔗 PASO 5: Verificar relación en Itinerario")
print("-" * 80)

try:
    from models import Itinerario
    
    # Verificar si tiene el atributo
    if hasattr(Itinerario, 'evaluacion'):
        print("✅ Itinerario tiene relación 'evaluacion'")
    else:
        print("❌ Itinerario NO tiene relación 'evaluacion'")
        print("   Agrega en models/itinerario.py:")
        print('   evaluacion = relationship("Evaluacion", back_populates="itinerario", uselist=False)')

except Exception as e:
    print(f"❌ Error: {e}")

print()

# 6. Resumen
print("=" * 80)
print("📊 RESUMEN")
print("=" * 80)

# Verificar qué falta
problemas = []

if not os.path.exists("models/evaluacion.py"):
    problemas.append("Crear models/evaluacion.py")

if not os.path.exists("schemas/evaluacion.py"):
    problemas.append("Crear schemas/evaluacion.py")

if not os.path.exists("routers/evaluaciones.py"):
    problemas.append("Crear routers/evaluaciones.py")

try:
    from database import engine
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tablas = inspector.get_table_names()
    if "evaluaciones" not in tablas:
        problemas.append("Crear tabla 'evaluaciones' en la BD")
except:
    problemas.append("Verificar conexión a BD")

if problemas:
    print("⚠️ PROBLEMAS ENCONTRADOS:")
    for i, problema in enumerate(problemas, 1):
        print(f"   {i}. {problema}")
    print()
    print("Sigue los pasos de la GUIA_IMPLEMENTACION_EVALUACION.md")
else:
    print("✅ TODO CORRECTO - El sistema debería funcionar")
    print()
    print("Si aún hay errores:")
    print("1. Reinicia el backend (Ctrl+C y uvicorn main:app --reload)")
    print("2. Revisa los logs del backend")
    print("3. Verifica el console del navegador")

print("=" * 80)