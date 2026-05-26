from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuración del sistema Ley 21.719"""
    
    # Database
    database_url: str = "postgresql://user:password@localhost:5432/ley21719"
    
    # Security
    secret_key: str = "change-this-secret-key-in-production"
    encryption_key: str = "32-byte-encryption-key-here!!!"  # Must be 32 bytes
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # API Settings
    api_v1_prefix: str = "/api/v1"
    project_name: str = "Ley 21.719 - Protección de Datos"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
