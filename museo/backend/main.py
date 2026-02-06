# main.py
# ✅ ACTUALIZADO: CORS dinámico para desarrollo y producción

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from datetime import datetime

from config import get_settings
from database import engine, Base

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

# ============================================
# LIFESPAN
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info(f"🚀 Iniciando {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"🌍 Entorno: {settings.ENVIRONMENT}")
    logger.info(f"🤖 IA Provider: {settings.AI_PROVIDER}")
    logger.info(f"🐛 Debug: {settings.DEBUG}")
    logger.info("=" * 60)
    
    # Verificar BD
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ Conexión a base de datos verificada")
    except Exception as e:
        logger.error(f"❌ Error BD: {e}")
    
    # Verificar IA
    try:
        from services.ia_service import ia_service
        estado_ia = ia_service.verificar_conexion()
        if estado_ia["conectado"]:
            logger.info(f"✅ IA conectada [{estado_ia.get('provider', '?')}] - Modelo: {estado_ia.get('modelo', '?')}")
        else:
            logger.warning(f"⚠️ IA no disponible: {estado_ia.get('error', 'Desconocido')}")
    except Exception as e:
        logger.warning(f"⚠️ No se pudo verificar IA: {e}")
    
    yield
    
    logger.info("🛑 Cerrando aplicación...")

# ============================================
# CREAR APLICACIÓN
# ============================================

app = FastAPI(
    title=settings.APP_NAME,
    description="Sistema de itinerarios personalizados con IA para el Museo Pumapungo",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# ============================================
# 🔥 CORS DINÁMICO — Lee de CORS_ORIGINS del .env
# ============================================

cors_origins = settings.CORS_ORIGINS.copy()

# Agregar FRONTEND_URL si existe y no está en la lista
if settings.FRONTEND_URL and settings.FRONTEND_URL not in cors_origins:
    cors_origins.append(settings.FRONTEND_URL)

# Siempre incluir localhost para desarrollo
localhost_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]
for origin in localhost_origins:
    if origin not in cors_origins:
        cors_origins.append(origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info(f"✅ CORS configurado para: {cors_origins}")

# ============================================
# ENDPOINTS PRINCIPALES
# ============================================

@app.get("/")
async def root():
    return {
        "mensaje": "Bienvenido al Sistema Museo Pumapungo",
        "version": settings.APP_VERSION,
        "entorno": settings.ENVIRONMENT,
        "ia_provider": settings.AI_PROVIDER,
        "documentacion": "/docs",
        "estado": "activo",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        return {
            "estado": "saludable",
            "base_datos": "conectada",
            "ia_provider": settings.AI_PROVIDER,
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
    return {
        "nombre": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "entorno": settings.ENVIRONMENT,
        "ia": {
            "provider": settings.AI_PROVIDER,
            "modelo": settings.DEEPSEEK_MODEL if settings.AI_PROVIDER == "deepseek" else settings.OLLAMA_MODEL
        },
        "api": {
            "prefix": settings.API_V1_PREFIX,
            "documentacion": "/docs"
        }
    }

# ============================================
# MANEJO DE ERRORES
# ============================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
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
# ROUTERS
# ============================================

from routers import visitantes, perfiles, areas, itinerarios, itinerario_detalles, historial, ia, auth_google, evaluaciones, certificado

app.include_router(visitantes.router, prefix=f"{settings.API_V1_PREFIX}/visitantes", tags=["Visitantes"])
app.include_router(perfiles.router, prefix=f"{settings.API_V1_PREFIX}/perfiles", tags=["Perfiles"])
app.include_router(areas.router, prefix=f"{settings.API_V1_PREFIX}/areas", tags=["Áreas del Museo"])
app.include_router(itinerarios.router, prefix=f"{settings.API_V1_PREFIX}/itinerarios", tags=["🤖 Itinerarios con IA"])
app.include_router(itinerario_detalles.router, prefix=f"{settings.API_V1_PREFIX}/detalles", tags=["Detalles de Itinerario"])
app.include_router(historial.router, prefix=f"{settings.API_V1_PREFIX}/historial", tags=["Historial de Visitas"])
app.include_router(ia.router, prefix=f"{settings.API_V1_PREFIX}/ia", tags=["Inteligencia Artificial"])
app.include_router(auth_google.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["🔐 Autenticación Google"])
app.include_router(evaluaciones.router, prefix=f"{settings.API_V1_PREFIX}/evaluaciones", tags=["Evaluaciones"])
app.include_router(certificado.router, prefix=f"{settings.API_V1_PREFIX}", tags=["Certificados"])

# ============================================
# EJECUTAR
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")