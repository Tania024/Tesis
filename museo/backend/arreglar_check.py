from database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        # Eliminar constraint antigua
        conn.execute(text("""
            ALTER TABLE itinerarios 
            DROP CONSTRAINT IF EXISTS check_estado;
        """))
        conn.commit()
        print("✅ Constraint antigua eliminada")
        
        # Agregar nueva con 'en_proceso'
        conn.execute(text("""
            ALTER TABLE itinerarios 
            ADD CONSTRAINT check_estado 
            CHECK (estado IN ('generado', 'en_proceso', 'activo', 'pausado', 'completado', 'cancelado'));
        """))
        conn.commit()
        print("✅ Constraint nueva agregada con 'en_proceso'")
        
except Exception as e:
    print(f"❌ Error: {e}")