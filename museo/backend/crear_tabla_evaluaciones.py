"""
SCRIPT: Crear tabla evaluaciones (versión para models.py único)

Ejecutar:
cd C:\\Users\\Tania\\Documents\\Tesis\\museo\\backend
python crear_tabla_evaluaciones_corregido.py
"""

print("=" * 80)
print("🔨 CREANDO TABLA EVALUACIONES")
print("=" * 80)
print()

try:
    # Importar dependencias
    print("📦 Importando modelos...")
    from database import engine, Base
    # 🔥 CORREGIDO: Importar desde models.py directamente
    from models import Evaluacion, Itinerario, Visitante, Area, ItinerarioDetalle, Perfil
    
    print("✅ Modelos importados correctamente")
    print()
    
    # Crear todas las tablas
    print("🔨 Creando tablas en la base de datos...")
    Base.metadata.create_all(bind=engine)
    
    print("✅ Tablas creadas/verificadas")
    print()
    
    # Verificar que se creó
    print("🔍 Verificando tabla 'evaluaciones'...")
    from sqlalchemy import inspect
    
    inspector = inspect(engine)
    tablas = inspector.get_table_names()
    
    if "evaluaciones" in tablas:
        print("✅ Tabla 'evaluaciones' existe")
        print()
        
        # Mostrar columnas
        columnas = inspector.get_columns("evaluaciones")
        print(f"Columnas ({len(columnas)}):")
        for col in columnas:
            print(f"   • {col['name']:<25} {col['type']}")
        
        print()
        print("=" * 80)
        print("✅ ÉXITO - Tabla creada correctamente")
        print("=" * 80)
        print()
        print("Siguiente paso:")
        print("1. Registrar router en main.py (ver abajo)")
        print("2. Reiniciar backend: uvicorn main:app --reload")
        print()
        print("=" * 80)
        print("CÓDIGO PARA MAIN.PY:")
        print("=" * 80)
        print()
        print("# En main.py, busca la línea donde registras routers y agrega:")
        print("app.include_router(evaluaciones.router)")
        print()
    else:
        print("❌ Error: Tabla 'evaluaciones' no se creó")
        print("   Verifica que models.py tiene la clase Evaluacion")

except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    print()
    print("Posibles causas:")
    print("1. models.py no tiene la clase Evaluacion")
    print("2. Error de sintaxis en models.py")
    print()
    print("Tu models.py DEBE tener:")
    print("class Evaluacion(Base):")
    print("    __tablename__ = 'evaluaciones'")
    print("    ...")

except Exception as e:
    print(f"❌ Error: {e}")
    print()
    print("Verifica:")
    print("1. PostgreSQL está corriendo")
    print("2. Credenciales en .env son correctas")
    print("3. Base de datos 'museo' existe")