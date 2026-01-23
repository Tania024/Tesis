# main.py
# Aplicación principal FastAPI - Sistema Museo Pumapungo
# Universidad Politécnica Salesiana
# ✅ CORREGIDO: CORS configurado correctamente

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from datetime import datetime

from config import get_settings
from database import engine, Base


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cargar configuración
settings = get_settings()

# ============================================
# LIFESPAN - EVENTOS DE INICIO Y CIERRE
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestiona el ciclo de vida de la aplicación
    - startup: al iniciar
    - shutdown: al cerrar
    """
    # STARTUP
    logger.info("=" * 60)
    logger.info(f"🚀 Iniciando {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"🌍 Entorno: {settings.ENVIRONMENT}")
    logger.info(f"🐛 Debug: {settings.DEBUG}")
    logger.info(f"💾 Base de datos: {settings.DB_NAME}")
    logger.info("=" * 60)
    
    # Verificar conexión a base de datos
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ Conexión a base de datos verificada")
    except Exception as e:
        logger.error(f"❌ Error al conectar con la base de datos: {e}")
    
    # Verificar conexión con Ollama
    try:
        from services.ia_service import ia_service
        estado_ia = ia_service.verificar_conexion()
        if estado_ia["conectado"]:
            logger.info(f"✅ Ollama conectado - Modelo: {estado_ia['modelo_configurado']}")
        else:
            logger.warning(f"⚠️ Ollama no disponible: {estado_ia.get('error', 'Desconocido')}")
    except Exception as e:
        logger.warning(f"⚠️ No se pudo verificar Ollama: {e}")
    
    yield  # Aquí la aplicación está corriendo
    
    # SHUTDOWN
    logger.info("=" * 60)
    logger.info("🛑 Cerrando aplicación...")
    logger.info("=" * 60)

# ============================================
# CREAR APLICACIÓN FASTAPI
# ============================================

app = FastAPI(
    title=settings.APP_NAME,
    description="Sistema de registro y perfilado de visitantes con generación automática de itinerarios personalizados mediante IA generativa para el Museo Pumapungo",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# ============================================
# CONFIGURAR CORS - ✅ CORREGIDO
# ============================================

# IMPORTANTE: Forzamos los orígenes explícitamente en lugar de usar settings.CORS_ORIGINS
# Esto asegura que funcione sin importar el formato de la configuración
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Frontend Vite (React)
        "http://localhost:3000",  # Alternativa (Create React App)
        "http://127.0.0.1:5173",  # Alternativa con 127.0.0.1
        "http://127.0.0.1:3000",
        "http://localhost:8080",  # Alternativa (Vue/otros)
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Permite GET, POST, PUT, DELETE, PATCH, OPTIONS
    allow_headers=["*"],  # Permite todos los headers
)

logger.info("✅ CORS configurado para:")
logger.info("   • http://localhost:5173 (Frontend)")
logger.info("   • http://localhost:3000")
logger.info("   • http://127.0.0.1:5173")

# ============================================
# ENDPOINTS PRINCIPALES
# ============================================

@app.get("/")
async def root():
    """Endpoint raíz - Información del sistema"""
    return {
        "mensaje": "Bienvenido al Sistema Museo Pumapungo",
        "version": settings.APP_VERSION,
        "entorno": settings.ENVIRONMENT,
        "documentacion": "/docs",
        "estado": "activo",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Endpoint de health check - Verifica el estado del sistema"""
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        return {
            "estado": "saludable",
            "base_datos": "conectada",
            "timestamp": datetime.now().isoformat(),
            "version": settings.APP_VERSION
        }
    except Exception as e:
        logger.error(f"Health check falló: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "estado": "no_saludable",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.get("/info")
async def info():
    """Información detallada del sistema"""
    return {
        "nombre": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "entorno": settings.ENVIRONMENT,
        "base_datos": {
            "host": settings.DB_HOST,
            "puerto": settings.DB_PORT,
            "nombre": settings.DB_NAME,
            "usuario": settings.DB_USER
        },
        "api": {
            "prefix": settings.API_V1_PREFIX,
            "documentacion": "/docs",
            "redoc": "/redoc"
        },
        "ia_generativa": {
            "url": settings.OLLAMA_BASE_URL,
            "modelo": settings.OLLAMA_MODEL
        },
        "cors": {
            "origins": [
                "http://localhost:5173",
                "http://localhost:3000",
                "http://127.0.0.1:5173"
            ]
        }
    }

# ============================================
# MANEJO DE ERRORES GLOBALES
# ============================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Manejador global de excepciones"""
    logger.error(f"Error no manejado: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Error interno del servidor",
            "detalle": str(exc) if settings.DEBUG else "Contacte al administrador",
            "timestamp": datetime.now().isoformat()
        }
    )

# ============================================
# IMPORTAR Y REGISTRAR ROUTERS
# ============================================

from routers import visitantes, perfiles, areas, itinerarios, itinerario_detalles, historial, ia, auth_google, evaluaciones

# Registrar todos los routers
app.include_router(visitantes.router, prefix=f"{settings.API_V1_PREFIX}/visitantes", tags=["Visitantes"])
app.include_router(perfiles.router, prefix=f"{settings.API_V1_PREFIX}/perfiles", tags=["Perfiles"])
app.include_router(areas.router, prefix=f"{settings.API_V1_PREFIX}/areas", tags=["Áreas del Museo"])
app.include_router(itinerarios.router, prefix=f"{settings.API_V1_PREFIX}/itinerarios", tags=["🤖 Itinerarios con IA"])
app.include_router(itinerario_detalles.router, prefix=f"{settings.API_V1_PREFIX}/detalles", tags=["Detalles de Itinerario"])
app.include_router(historial.router, prefix=f"{settings.API_V1_PREFIX}/historial", tags=["Historial de Visitas"])
app.include_router(ia.router, prefix=f"{settings.API_V1_PREFIX}/ia", tags=["Inteligencia Artificial"])
app.include_router(auth_google.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["🔐 Autenticación Google (YouTube + Maps)"])
app.include_router(evaluaciones.router, prefix=f"{settings.API_V1_PREFIX}/evaluaciones", tags=["Evaluaciones"])

# ============================================
# EJECUTAR APLICACIÓN
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    logger.info("=" * 60)
    logger.info("🚀 Iniciando servidor de desarrollo")
    logger.info("=" * 60)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )