"""
Script de Verificación - Proyecto Museo Pumapungo
Soporte para PostgreSQL + pg8000
"""
import sys
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from models import Itinerario, ItinerarioDetalle, Area 

# Configuración
DB_URL = "postgresql+pg8000://postgres:1234@localhost:5432/museo"

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine)

def verificar_itinerario(itinerario_id: int):
    db = SessionLocal()
    try:
        # Inspeccionamos la tabla para ver qué columnas existen realmente
        inspector = inspect(engine)
        columnas = [c['name'] for c in inspector.get_columns('itinerario_detalles')]
        
        itinerario = db.query(Itinerario).filter(Itinerario.id == itinerario_id).first()
        if not itinerario:
            print(f"❌ Itinerario #{itinerario_id} no encontrado.")
            return

        print("\n" + "=" * 80)
        print(f"📋 REVISIÓN TÉCNICA - ITINERARIO #{itinerario.id}: {itinerario.titulo}")
        print("=" * 80)
        
        detalles = db.query(ItinerarioDetalle).filter(ItinerarioDetalle.itinerario_id == itinerario_id).all()
        
        for i, d in enumerate(detalles, 1):
            area = db.query(Area).filter(Area.id == d.area_id).first()
            print(f"\n{i}. Sala: {area.nombre if area else '???'}")
            
            # Verificamos cada columna solo si existe en la BD
            print(f"   - introduccion:  {'✅' if d.introduccion else '❌'}")
            
            if 'historia_contextual' in columnas:
                print(f"   - historia IA:   {'✅' if d.historia_contextual else '❌'}")
            else:
                print(f"   - historia IA:   ⚠️ COLUMNA NO EXISTE EN BD")
                
            if 'datos_curiosos' in columnas:
                print(f"   - curiosidades:  {'✅' if d.datos_curiosos else '❌'}")
            
            if 'que_observar' in columnas:
                print(f"   - que observar:  {'✅' if d.que_observar else '❌'}")

        print("\n" + "=" * 80)
        if 'historia_contextual' not in columnas:
            print("💡 ACCIÓN REQUERIDA: Ejecuta el ALTER TABLE en pgAdmin para agregar las columnas.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        verificar_itinerario(int(sys.argv[1]))