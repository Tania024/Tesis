# config.py
# ✅ ACTUALIZADO: Soporte para Ollama (local) + DeepSeek API (producción)

from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache
import os
from pathlib import Path

class Settings(BaseSettings):
    
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
    DATABASE_URL: Optional[str] = None  # 🔥 NUEVO: Para Render (usa DATABASE_URL directo)
    
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
    # 🔥 NUEVO: PROVEEDOR DE IA (ollama o deepseek)
    # ============================================
    AI_PROVIDER: str = "ollama"  # "ollama" para local, "deepseek" para producción
    
    # ============================================
    # CONFIGURACIÓN DE OLLAMA (desarrollo local)
    # ============================================
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b"
    OLLAMA_TIMEOUT: int = 420
    OLLAMA_TEMPERATURE: float = 0.25
    OLLAMA_MAX_TOKENS: int = 4000
    
    # ============================================
    # 🔥 NUEVO: CONFIGURACIÓN DE DEEPSEEK (producción)
    # ============================================
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_MODEL: str = "deepseek-chat"
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    
    # ============================================
    # CONFIGURACIÓN GENERAL DE IA
    # ============================================
    AI_TIMEOUT: int = 420
    AI_TEMPERATURE: float = 0.25
    AI_MAX_TOKENS: int = 4000

    # ============================================
    # SMTP
    # ============================================
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USE_TLS: bool = True
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "lojanotania08@gmail.com"

    # ============================================
    # Google OAuth
    # ============================================
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"
    REDIRECT_URI_BASE: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:5173"
    
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
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024
    
    # ============================================
    # CONFIGURACIÓN DE SEGURIDAD
    # ============================================
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # ============================================
    # PROPIEDADES CALCULADAS
    # ============================================
    
    @property
    def DATABASE_URL_COMPUTED(self) -> str:
        """
        🔥 ACTUALIZADO: Si existe DATABASE_URL (Render), usarla.
        Si no, construir desde variables individuales.
        """
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_testing(self) -> bool:
        return self.ENVIRONMENT.lower() == "testing"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        env_prefix = ""


@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()