# config.py
# Configuración centralizada de la aplicación
# Sistema Museo Pumapungo

from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache
import os
from pathlib import Path

class Settings(BaseSettings):
    """
    Configuración de la aplicación usando Pydantic Settings.
    Lee variables de entorno desde archivo .env
    """
    
    # ============================================
    # CONFIGURACIÓN DE LA APLICACIÓN
    # ============================================
    APP_NAME: str = "Sistema Museo Pumapungo"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # ============================================
    # CONFIGURACIÓN DE BASE DE DATOS
    # ============================================
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "museo_pumapungo"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    
    # ============================================
    # CONFIGURACIÓN DE API
    # ============================================
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "secret-key-change-in-production-please"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # ============================================
    # CONFIGURACIÓN DE CORS
    # ============================================
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080"
    ]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "PATCH"]
    CORS_HEADERS: List[str] = ["*"]
    
    # ============================================
    # CONFIGURACIÓN DE IA GENERATIVA
    # ============================================
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "deepseek-r1:1.5b"
    OLLAMA_TIMEOUT: int = 120
    OLLAMA_TEMPERATURE: float = 0.7
    OLLAMA_MAX_TOKENS: int = 2000

    # ============================================
    # Google OAuth
    # ============================================
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"
    REDIRECT_URI_BASE: str = "http://localhost:8000"
    
    # ============================================
    # CONFIGURACIÓN DE LOGGING
    # ============================================
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/museo_pumapungo.log"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    
    # ============================================
    # CONFIGURACIÓN DE PAGINACIÓN
    # ============================================
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # ============================================
    # CONFIGURACIÓN DE TIMEOUTS Y LÍMITES
    # ============================================
    REQUEST_TIMEOUT: int = 30
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB
    
    # ============================================
    # CONFIGURACIÓN DE SEGURIDAD
    # ============================================
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # ============================================
    # PROPIEDADES CALCULADAS
    # ============================================
    
    @property
    def DATABASE_URL(self) -> str:
        """
        Construye la URL de conexión a PostgreSQL
        Formato: postgresql://usuario:contraseña@host:puerto/base_datos
        """
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """
        URL para conexión asíncrona (si se necesita en el futuro)
        """
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def is_development(self) -> bool:
        """Retorna True si está en modo desarrollo"""
        return self.ENVIRONMENT.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Retorna True si está en modo producción"""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_testing(self) -> bool:
        """Retorna True si está en modo testing"""
        return self.ENVIRONMENT.lower() == "testing"
    
    # ============================================
    # CONFIGURACIÓN DE PYDANTIC
    # ============================================
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        
        # Valores por defecto si no existe .env
        env_prefix = ""


# ============================================
# INSTANCIA SINGLETON DE CONFIGURACIÓN
# ============================================

@lru_cache()
def get_settings() -> Settings:
    """
    Obtiene la instancia de configuración (singleton cacheado).
    Esto asegura que solo se cargue una vez durante la ejecución.
    
    Uso:
        from config import get_settings
        settings = get_settings()
        print(settings.DB_NAME)
    """
    return Settings()


# Instancia global de configuración
settings = get_settings()


# ============================================
# FUNCIONES ÚTILES
# ============================================

def print_settings(hide_sensitive: bool = True):
    """
    Imprime la configuración actual.
    
    Args:
        hide_sensitive: Si True, oculta información sensible
    """
    s = get_settings()
    
    print("=" * 70)
    print(f"  CONFIGURACIÓN DEL SISTEMA - {s.APP_NAME}")
    print("=" * 70)
    
    print(f"\n📱 APLICACIÓN:")
    print(f"   Nombre: {s.APP_NAME}")
    print(f"   Versión: {s.APP_VERSION}")
    print(f"   Entorno: {s.ENVIRONMENT}")
    print(f"   Debug: {s.DEBUG}")
    
    print(f"\n💾 BASE DE DATOS:")
    print(f"   Host: {s.DB_HOST}:{s.DB_PORT}")
    print(f"   Nombre: {s.DB_NAME}")
    print(f"   Usuario: {s.DB_USER}")
    if not hide_sensitive:
        print(f"   Password: {s.DB_PASSWORD}")
    else:
        print(f"   Password: {'*' * len(s.DB_PASSWORD)}")
    print(f"   URL: {s.DATABASE_URL.replace(s.DB_PASSWORD, '***')}")
    
    print(f"\n🔌 API:")
    print(f"   Prefix: {s.API_V1_PREFIX}")
    if not hide_sensitive:
        print(f"   Secret Key: {s.SECRET_KEY}")
    else:
        print(f"   Secret Key: {'*' * 10}")
    print(f"   Token Expiration: {s.ACCESS_TOKEN_EXPIRE_MINUTES} min")
    
    print(f"\n🤖 IA GENERATIVA (Ollama):")
    print(f"   URL: {s.OLLAMA_BASE_URL}")
    print(f"   Modelo: {s.OLLAMA_MODEL}")
    print(f"   Timeout: {s.OLLAMA_TIMEOUT}s")
    print(f"   Temperature: {s.OLLAMA_TEMPERATURE}")
    
    print(f"\n🌐 CORS:")
    print(f"   Origins: {', '.join(s.CORS_ORIGINS)}")
    print(f"   Credentials: {s.CORS_CREDENTIALS}")
    
    print(f"\n📊 PAGINACIÓN:")
    print(f"   Tamaño por defecto: {s.DEFAULT_PAGE_SIZE}")
    print(f"   Tamaño máximo: {s.MAX_PAGE_SIZE}")
    
    print(f"\n📝 LOGGING:")
    print(f"   Nivel: {s.LOG_LEVEL}")
    print(f"   Archivo: {s.LOG_FILE}")
    
    print("\n" + "=" * 70)


def validate_settings() -> bool:
    """
    Valida que la configuración sea correcta.
    Retorna True si es válida, False en caso contrario.
    """
    s = get_settings()
    errors = []
    warnings = []
    
    # Validaciones de base de datos
    if not s.DB_NAME:
        errors.append("DB_NAME no puede estar vacío")
    
    if not s.DB_USER:
        errors.append("DB_USER no puede estar vacío")
    
    if not s.DB_PASSWORD and s.is_production:
        errors.append("DB_PASSWORD no debe estar vacío en producción")
    
    # Validaciones de producción
    if s.is_production:
        if s.SECRET_KEY == "secret-key-change-in-production-please":
            errors.append("SECRET_KEY debe cambiarse en producción")
        
        if s.DEBUG:
            warnings.append("DEBUG debe ser False en producción")
        
        if len(s.SECRET_KEY) < 32:
            warnings.append("SECRET_KEY debería tener al menos 32 caracteres")
    
    # Validaciones de rutas
    log_dir = Path(s.LOG_FILE).parent
    if not log_dir.exists():
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            warnings.append(f"Directorio de logs creado: {log_dir}")
        except Exception as e:
            errors.append(f"No se pudo crear directorio de logs: {e}")
    
    # Mostrar resultados
    if errors:
        print("\n❌ ERRORES DE CONFIGURACIÓN:")
        for error in errors:
            print(f"   • {error}")
        print()
        return False
    
    if warnings:
        print("\n⚠️ ADVERTENCIAS DE CONFIGURACIÓN:")
        for warning in warnings:
            print(f"   • {warning}")
        print()
    
    if not errors and not warnings:
        print("\n✅ Configuración válida - No se encontraron problemas")
    
    return True


def create_env_template():
    """
    Crea un archivo .env.example con plantilla de configuración
    """
    template = """# ============================================
# CONFIGURACIÓN DEL SISTEMA MUSEO PUMAPUNGO
# ============================================

# BASE DE DATOS POSTGRESQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=museo_pumapungo
DB_USER=postgres
DB_PASSWORD=tu_contraseña_aqui

# APLICACIÓN
APP_NAME=Sistema Museo Pumapungo
APP_VERSION=1.0.0
DEBUG=True
ENVIRONMENT=development

# API
API_V1_PREFIX=/api/v1
SECRET_KEY=genera-una-clave-segura-aqui
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS - Permitir estos orígenes
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# IA GENERATIVA - OLLAMA
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:1.5b
OLLAMA_TIMEOUT=120
OLLAMA_TEMPERATURE=0.7

# LOGGING
LOG_LEVEL=INFO
LOG_FILE=logs/museo_pumapungo.log

# PAGINACIÓN
DEFAULT_PAGE_SIZE=20
MAX_PAGE_SIZE=100
"""
    
    with open(".env.example", "w", encoding="utf-8") as f:
        f.write(template)
    
    print("✅ Archivo .env.example creado")
    print("   Copia este archivo a .env y configura tus valores")


def check_env_file():
    """
    Verifica si existe el archivo .env
    """
    if not os.path.exists(".env"):
        print("⚠️ ADVERTENCIA: No se encontró archivo .env")
        print("\nSe usarán los valores por defecto de config.py")
        print("\nPara crear tu archivo .env:")
        print("   1. Copia .env.example a .env")
        print("   2. O ejecuta: python config.py --create-env")
        return False
    return True


# ============================================
# SCRIPT DE PRUEBA
# ============================================

if __name__ == "__main__":
    """
    Ejecutar directamente para probar la configuración:
    python config.py
    """
    import sys
    
    # Verificar argumentos
    if len(sys.argv) > 1:
        if sys.argv[1] == "--create-env":
            create_env_template()
            sys.exit(0)
        elif sys.argv[1] == "--validate":
            check_env_file()
            validate_settings()
            sys.exit(0)
        elif sys.argv[1] == "--show":
            print_settings(hide_sensitive=False)
            sys.exit(0)
    
    # Modo normal
    print("\n" + "🔧 VERIFICACIÓN DE CONFIGURACIÓN")
    
    # Verificar .env
    check_env_file()
    
    # Mostrar configuración
    print_settings(hide_sensitive=True)
    
    # Validar
    print("\n" + "🔍 VALIDANDO CONFIGURACIÓN...")
    validate_settings()
    
    print("""
📖 USO:
   python config.py              # Mostrar configuración
   python config.py --create-env # Crear .env.example
   python config.py --validate   # Solo validar
   python config.py --show       # Mostrar todo (con passwords)
    """)