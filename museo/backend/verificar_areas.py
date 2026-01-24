# verificar_areas.py
# Script para verificar y activar todas las áreas del museo

from database import SessionLocal
from models import Area

def verificar_areas():
    db = SessionLocal()
    
    try:
        # Obtener TODAS las áreas (activas e inactivas)
        todas_areas = db.query(Area).all()
        
        print(f"\n📊 TOTAL DE ÁREAS EN BD: {len(todas_areas)}")
        print("=" * 60)
        
        # Mostrar estado de cada área
        activas = 0
        inactivas = 0
        
        for area in todas_areas:
            estado = "✅ ACTIVA" if area.activa else "❌ INACTIVA"
            print(f"{area.codigo:10} | {area.nombre:35} | {estado}")
            
            if area.activa:
                activas += 1
            else:
                inactivas += 1
        
        print("=" * 60)
        print(f"✅ Activas: {activas}")
        print(f"❌ Inactivas: {inactivas}")
        print(f"📊 Total: {len(todas_areas)}")
        
        # Si hay áreas inactivas, ofrecer activarlas
        if inactivas > 0:
            print(f"\n⚠️ Hay {inactivas} áreas INACTIVAS")
            respuesta = input("\n¿Quieres activar TODAS las áreas? (s/n): ")
            
            if respuesta.lower() == 's':
                for area in todas_areas:
                    if not area.activa:
                        area.activa = True
                        print(f"✅ Activando: {area.codigo} - {area.nombre}")
                
                db.commit()
                print(f"\n🎉 ¡Todas las {len(todas_areas)} áreas están ACTIVAS ahora!")
            else:
                print("\n❌ No se activaron las áreas")
        else:
            print(f"\n✅ Todas las áreas ya están activas")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    verificar_areas()