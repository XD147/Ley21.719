from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuración del sistema Ley 21.719"""
    
    # Database
    database_url: str = "postgresql://user:password@localhost:5432/ley21719"
    
    # Security
    secret_key: str = "change-this-secret-key-in-production"
    encryption_key: str = "32-byte-encryption-key-here!!!"  # Must be 32 bytes
    jwt_secret_key: str = "jwt-secret-key-for-tokens-min-32-chars"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # API Settings
    api_v1_prefix: str = "/api/v1"
    project_name: str = "Ley 21.719 - Protección de Datos"
    
    # ClaveÚnica (Gobierno de Chile)
    claveunica_client_id: str = ""
    claveunica_client_secret: str = ""
    claveunica_redirect_uri: str = "http://localhost:8000/auth/claveunica/callback"
    claveunica_scope: str = "openid profile rut"
    
    # SII Clave Tributaria
    sii_client_id: str = ""
    sii_client_secret: str = ""
    sii_redirect_uri: str = "http://localhost:8000/auth/sii/callback"
    sii_use_sandbox: bool = True
    sii_certificate_path: Optional[str] = None
    sii_private_key_path: Optional[str] = None
    
    # Agencia Digital (Notificación Brechas)
    agencia_digital_endpoint: str = "https://api.agenciadigital.gob.cl"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
