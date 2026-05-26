"""
Aplicación principal - Ley 21.719 Protección de Datos (Chile)
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base
from app.api.routes import router
from app.api.auth_routes import router as auth_router
from app.api.cumplimiento import router as cumplimiento_router
from app.api.portabilidad import router as portabilidad_router
from app.models import models  # Importar para registrar modelos


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    # Startup: Crear tablas si no existen
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown
    pass


app = FastAPI(
    title=settings.project_name,
    description="""
## Sistema de Protección de Datos - Ley 21.719 (Chile)

API REST para gestión de protección de datos personales conforme a la Ley 21.719 de Chile.

### Características principales:

* **Usuarios**: Registro y gestión de ciudadanos con RUT encriptado
* **Organizaciones**: Gestión de entidades que procesan datos personales
* **API Keys**: Autenticación segura para acceso programático
* **Consentimientos**: Gestión granular de permisos de acceso a datos
* **Solicitudes ARCO**: Ejercicio de derechos (Acceso, Rectificación, Cancelación, Oposición)
* **Auditoría**: Logging completo de accesos para accountability
* **ClaveÚnica**: Autenticación de usuarios con identidad digital del Gobierno
* **SII Clave Tributaria**: Autenticación de organizaciones con SII

### Seguridad:

* RUT hasheado con SHA-256 para indexación
* RUT encriptado con AES-256 para almacenamiento
* API Keys con hash SHA-256 (nunca se almacenan en claro)
* Firmas digitales para receipts de consentimiento
* Integración con ClaveÚnica y SII para autenticación oficial
    """,
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción especificar dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware para sesiones (requerido para OAuth callbacks)
from starlette.middleware.sessions import SessionMiddleware
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)


@app.get("/", tags=["Root"])
async def root():
    """Endpoint raíz con información de la API"""
    return {
        "message": "Ley 21.719 - Sistema de Protección de Datos",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Verifica el estado de salud de la API"""
    return {"status": "healthy"}


# Incluir routers
app.include_router(router, prefix=settings.api_v1_prefix)
app.include_router(auth_router)  # Auth routes ya tienen prefijo /auth
app.include_router(cumplimiento_router, prefix=settings.api_v1_prefix)  # Cumplimiento Ley 21.719
app.include_router(portabilidad_router)  # Portabilidad y Notificaciones (ya tiene prefijo /api/v1)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
