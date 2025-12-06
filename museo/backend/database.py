# database.py
# Configuración de conexión a PostgreSQL con SQLAlchemy
# Sistema Museo Pumapungo

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging
from config import get_settings

# Obtener configuraciones
settings = get_settings()

# Configuración de logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
# CREAR ENGINE
# ============================================

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Mostrar SQL queries solo en debug
    future=True,
    pool_size=10,  # Número de conexiones en el pool
    max_overflow=20,  # Conexiones adicionales permitidas
    pool_pre_ping=True,  # Verifica conexiones antes de usarlas
    pool_recycle=3600,  # Recicla conexiones cada hora
)

# ============================================
# SESSION MAKER
# ============================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True
)

# ============================================
# BASE DECLARATIVA
# ============================================

Base = declarative_base()

# ============================================
# DEPENDENCY PARA FASTAPI
# ============================================

def get_db():
    """
    Dependency que proporciona una sesión de base de datos.
    Se usa en los endpoints de FastAPI.
    
    Uso:
        @app.get("/visitantes")
        def get_visitantes(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================
# FUNCIONES ÚTILES
# ============================================

def init_db():
    """
    Inicializa la base de datos creando todas las tablas.
    NOTA: Solo usar en desarrollo. En producción usar Alembic.
    """
    try:
        # Importar todos los modelos aquí para que SQLAlchemy los conozca
        from models import (
            Visitante, Perfil, AreaMuseo, Exhibicion, 
            Itinerario, ItinerarioDetalle, Visita, 
            OcupacionArea, PreferenciaArea
        )
        
        logger.info("Creando tablas en la base de datos...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tablas creadas exitosamente!")
        
    except Exception as e:
        logger.error(f"❌ Error al crear tablas: {str(e)}")
        raise

def drop_all_tables():
    """
    ¡CUIDADO! Elimina todas las tablas de la base de datos.
    Solo usar en desarrollo.
    """
    if not settings.is_development:
        raise Exception("⚠️ No se puede eliminar tablas en producción!")
    
    try:
        logger.warning("⚠️ Eliminando todas las tablas...")
        Base.metadata.drop_all(bind=engine)
        logger.info("✅ Tablas eliminadas exitosamente!")
    except Exception as e:
        logger.error(f"❌ Error al eliminar tablas: {str(e)}")
        raise

def check_connection():
    """
    Verifica si la conexión a la base de datos está funcionando.
    Retorna True si la conexión es exitosa, False en caso contrario.
    """
    try:
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")
            result.fetchone()
        logger.info("✅ Conexión a la base de datos exitosa!")
        return True
    except Exception as e:
        logger.error(f"❌ Error de conexión a la base de datos: {str(e)}")
        return False

def get_db_info():
    """
    Obtiene información sobre la base de datos.
    """
    try:
        with engine.connect() as connection:
            result = connection.execute("""
                SELECT version(), 
                       current_database(), 
                       current_user,
                       inet_server_addr(),
                       inet_server_port()
            """)
            row = result.fetchone()
            
            info = {
                "version": row[0],
                "database": row[1],
                "user": row[2],
                "host": str(row[3]) if row[3] else "localhost",
                "port": row[4]
            }
            
            logger.info(f"📊 Info BD: Base de datos '{info['database']}' conectada")
            return info
    except Exception as e:
        logger.error(f"❌ Error al obtener info de BD: {str(e)}")
        return None

# ============================================
# EVENTOS DE SQLALCHEMY
# ============================================

@event.listens_for(engine, "connect")
def set_postgresql_params(dbapi_conn, connection_record):
    """
    Configura parámetros de conexión cuando se establece una nueva conexión.
    """
    cursor = dbapi_conn.cursor()
    # Configurar zona horaria de Ecuador
    cursor.execute("SET timezone='America/Guayaquil'")
    # Configurar búsqueda de schemas
    cursor.execute("SET search_path TO public")
    cursor.close()
    logger.debug("Parámetros de conexión PostgreSQL configurados")

@event.listens_for(engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, params, context, executemany):
    """
    Se ejecuta antes de cada query. Útil para logging detallado.
    """
    if settings.DEBUG and logger.level == logging.DEBUG:
        logger.debug(f"Ejecutando SQL: {statement[:100]}...")

# ============================================
# CONTEXT MANAGER PARA SESIONES
# ============================================

class DatabaseSession:
    """
    Context manager para manejar sesiones de base de datos.
    
    Uso:
        with DatabaseSession() as db:
            visitante = db.query(Visitante).first()
    """
    def __enter__(self):
        self.db = SessionLocal()
        return self.db
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logger.error(f"Error en transacción: {exc_val}")
            self.db.rollback()
        self.db.close()

# ============================================
# FUNCIÓN DE INICIALIZACIÓN
# ============================================

def initialize_database(create_tables: bool = False):
    """
    Inicializa la configuración de la base de datos.
    
    Args:
        create_tables: Si True, crea las tablas (solo desarrollo)
    """
    logger.info("🔧 Inicializando configuración de base de datos...")
    logger.info(f"Entorno: {settings.ENVIRONMENT}")
    logger.info(f"Base de datos: {settings.DB_NAME} en {settings.DB_HOST}")
    
    # Verificar conexión
    if not check_connection():
        raise Exception("No se pudo conectar a la base de datos PostgreSQL")
    
    # Obtener información
    info = get_db_info()
    if info:
        logger.info(f"PostgreSQL versión: {info['version'].split()[0]}")
    
    # Crear tablas si se solicita
    if create_tables:
        if settings.is_production:
            logger.warning("⚠️ No se recomienda crear tablas automáticamente en producción")
            logger.warning("⚠️ Usa Alembic para migraciones en producción")
        init_db()
    
    logger.info("✅ Base de datos inicializada correctamente!")

# ============================================
# HEALTHCHECK
# ============================================

def healthcheck():
    """
    Verifica el estado de la base de datos.
    Retorna dict con información de salud.
    """
    try:
        with engine.connect() as connection:
            # Verificar conexión
            result = connection.execute("SELECT 1")
            result.fetchone()
            
            # Obtener estadísticas
            stats = connection.execute("""
                SELECT 
                    (SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()) as active_connections,
                    (SELECT pg_database_size(current_database())) as db_size
            """)
            row = stats.fetchone()
            
            return {
                "status": "healthy",
                "database": settings.DB_NAME,
                "active_connections": row[0],
                "database_size_mb": round(row[1] / 1024 / 1024, 2),
                "timestamp": "now()"
            }
    except Exception as e:
        logger.error(f"Healthcheck falló: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

# ============================================
# SCRIPT DE PRUEBA
# ============================================

if __name__ == "__main__":
    """
    Ejecutar este archivo directamente para probar la conexión:
    python database.py
    """
    import os
    
    print("=" * 60)
    print("PRUEBA DE CONEXIÓN A BASE DE DATOS - MUSEO PUMAPUNGO")
    print("=" * 60)
    
    # Verificar archivo .env
    if not os.path.exists(".env"):
        print("\n⚠️ ADVERTENCIA: No se encontró archivo .env")
        print("   Creando .env de ejemplo...")
        
        with open(".env", "w") as f:
            f.write("""# Configuración de Base de Datos PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=museo_pumapungo
DB_USER=postgres
DB_PASSWORD=postgres

# Configuración de la aplicación
DEBUG=True
ENVIRONMENT=development
SECRET_KEY=dev-secret-key

# IA Generativa
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:1.5b
""")
        print("   ✅ Archivo .env creado. Por favor configura tus credenciales.")
        print()
    
    # Mostrar configuración
    print(f"\n📋 Configuración actual:")
    print(f"   - Host: {settings.DB_HOST}:{settings.DB_PORT}")
    print(f"   - Base de datos: {settings.DB_NAME}")
    print(f"   - Usuario: {settings.DB_USER}")
    print(f"   - Entorno: {settings.ENVIRONMENT}")
    
    # Verificar conexión
    print(f"\n🔌 Intentando conectar a PostgreSQL...")
    if check_connection():
        print("\n✅ ¡Conexión exitosa!")
        
        # Obtener información
        info = get_db_info()
        if info:
            print(f"\n📊 Información de la base de datos:")
            print(f"   - Versión PostgreSQL: {info['version'].split()[0]}")
            print(f"   - Base de datos: {info['database']}")
            print(f"   - Usuario: {info['user']}")
            print(f"   - Host: {info['host']}")
            print(f"   - Puerto: {info['port']}")
        
        # Healthcheck
        health = healthcheck()
        if health['status'] == 'healthy':
            print(f"\n💚 Estado de salud:")
            print(f"   - Conexiones activas: {health['active_connections']}")
            print(f"   - Tamaño BD: {health['database_size_mb']} MB")
        
        # Preguntar si crear tablas
        if settings.is_development:
            respuesta = input("\n¿Deseas crear las tablas ahora? (s/n): ")
            if respuesta.lower() == 's':
                try:
                    init_db()
                    print("\n✅ ¡Tablas creadas exitosamente!")
                except Exception as e:
                    print(f"\n❌ Error al crear tablas: {str(e)}")
        
    else:
        print("\n❌ Error de conexión. Verifica:")
        print("   1. PostgreSQL está corriendo")
        print("   2. La base de datos 'museo_pumapungo' existe")
        print("      Crear con: createdb -U postgres museo_pumapungo")
        print("   3. Las credenciales en .env son correctas")
        print("   4. El puerto 5432 está disponible")
    
    print("\n" + "=" * 60)