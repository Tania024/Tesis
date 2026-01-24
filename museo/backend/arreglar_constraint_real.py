from database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        # Listar todos los constraints primero
        result = conn.execute(text("""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'itinerarios' 
            AND constraint_type = 'CHECK';
        """))
        
        constraints = [row[0] for row in result]
        print(f"📋 Constraints encontrados: {constraints}")
        
        # Eliminar TODOS los constraints CHECK de estado
        for constraint_name in constraints:
            if 'estado' in constraint_name.lower() or 'check' in constraint_name.lower():
                try:
                    conn.execute(text(f"""
                        ALTER TABLE itinerarios 
                        DROP CONSTRAINT IF EXISTS {constraint_name};
                    """))
                    conn.commit()
                    print(f"✅ Eliminado: {constraint_name}")
                except Exception as e:
                    print(f"⚠️ No se pudo eliminar {constraint_name}: {e}")
        
        # Agregar constraint nuevo con nombre explícito
        conn.execute(text("""
            ALTER TABLE itinerarios 
            ADD CONSTRAINT itinerarios_estado_check 
            CHECK (estado IN ('generado', 'en_proceso', 'activo', 'pausado', 'completado', 'cancelado'));
        """))
        conn.commit()
        print("✅ Constraint nuevo agregado con 'en_proceso'")
        
        # Verificar
        result = conn.execute(text("""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'itinerarios' 
            AND constraint_type = 'CHECK';
        """))
        
        nuevos = [row[0] for row in result]
        print(f"✅ Constraints finales: {nuevos}")
        
except Exception as e:
    print(f"❌ Error: {e}")