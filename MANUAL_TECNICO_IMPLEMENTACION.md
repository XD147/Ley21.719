# Manual Técnico de Implementación - Ley 21.719 Chile

## 📋 Tabla de Contenidos

1. [Arquitectura del Sistema](#arquitectura-del-sistema)
2. [Requisitos Previos](#requisitos-previos)
3. [Configuración del Entorno](#configuración-del-entorno)
4. [Seguridad Avanzada (KMS/HSM)](#seguridad-avanzada-kmshsm)
5. [Base de Datos y Migraciones](#base-de-datos-y-migraciones)
6. [Tareas Asíncronas (Celery)](#tareas-asíncronas-celery)
7. [API Reference](#api-reference)
8. [Despliegue en Producción](#despliegue-en-producción)
9. [Monitoreo y Logs](#monitoreo-y-logs)

---

## 🏗️ Arquitectura del Sistema

### Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React + TS)                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐    │
│  │   Login     │ │  Dashboard  │ │ Derechos Ciudadanos │    │
│  │ ClaveÚnica  │ │    DPO      │ │ (Portabilidad, etc) │    │
│  └─────────────┘ └─────────────┘ └─────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  API GATEWAY (FastAPI)                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Endpoints REST (76 total)                │   │
│  │  /auth/*  /api/v1/usuarios  /api/v1/organizaciones    │   │
│  │  /api/v1/accesos  /api/v1/arcos  /api/v1/brechas      │   │
│  │  /api/v1/rat  /api/v1/eipd  /api/v1/ciudadano/*       │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
     ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
     │  PostgreSQL │ │   Redis     │ │   Celery    │
     │  (Datos)    │ │  (Cache)    │ │  (Workers)  │
     └─────────────┘ └─────────────┘ └─────────────┘
              │                               │
              ▼                               ▼
     ┌─────────────┐                 ┌─────────────┐
     │  KMS/HSM    │                 │  Lifecycle  │
     │  (Claves)   │                 │  Worker     │
     └─────────────┘                 └─────────────┘
```

### Flujo de Datos

1. **Autenticación**: Usuario → ClaveÚnica/SII OAuth2 → JWT Token
2. **Acceso a Datos**: Token válido → Validación permisos → Consulta encriptada
3. **Auditoría**: Cada acceso genera log inmutable con hash SHA-256
4. **Ciclo de Vida**: Celery worker ejecuta borrados programados automáticamente

---

## 🛠️ Requisitos Previos

### Software Requerido

- **Python**: 3.10 o superior
- **Node.js**: 18.x o superior
- **PostgreSQL**: 14.x o superior
- **Redis**: 6.x o superior
- **Docker**: 20.x (opcional para contenerización)

### Dependencias Python

```bash
pip install -r requirements.txt
```

**requirements.txt incluye:**
- `fastapi>=0.104.0` - Framework web asíncrono
- `sqlalchemy>=2.0.0` - ORM para base de datos
- `alembic>=1.12.0` - Migraciones de base de datos
- `pydantic>=2.5.0` - Validación de datos
- `cryptography>=41.0.0` - Encriptación AES-256
- `python-jose[cryptography]` - JWT tokens
- `httpx>=0.25.0` - Cliente HTTP para OAuth2
- `celery>=5.3.0` - Tareas asíncronas
- `redis>=5.0.0` - Cliente Redis
- `psycopg2-binary>=2.9.0` - Driver PostgreSQL
- `reportlab>=4.0.0` - Generación de PDFs (certificados)

### Dependencias Node.js

```bash
cd frontend
npm install
```

**package.json incluye:**
- `react@18.x` - Framework UI
- `typescript@5.x` - Tipado estático
- `axios@1.x` - Cliente HTTP
- `react-router-dom@6.x` - Enrutamiento
- `jwt-decode@4.x` - Decodificación de tokens

---

## ⚙️ Configuración del Entorno

### Archivo .env

Crear archivo `.env` en la raíz del proyecto:

```bash
# ===========================================
# CONFIGURACIÓN GENERAL
# ===========================================
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=tu_secret_key_seguro_min_32_caracteres
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000

# ===========================================
# BASE DE DATOS
# ===========================================
DATABASE_URL=postgresql://usuario:password@localhost:5432/ley21719_db
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# ===========================================
# REDIS (Celery Broker & Cache)
# ===========================================
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# ===========================================
# SEGURIDAD - ENCRIPTACIÓN
# ===========================================
# Opción 1: Local (desarrollo)
ENCRYPTION_KEY=tu_clave_maestra_32_bytes_exactamente
KMS_PROVIDER=local

# Opción 2: AWS KMS (producción)
# KMS_PROVIDER=aws_kms
# AWS_KMS_KEY_ID=arn:aws:kms:region:account:key/key-id
# AWS_ACCESS_KEY_ID=tu_access_key
# AWS_SECRET_ACCESS_KEY=tu_secret_key
# AWS_REGION=us-east-1

# Opción 3: Azure Key Vault (producción)
# KMS_PROVIDER=azure_kv
# AZURE_KV_URL=https://tu-vault.vault.azure.net/
# AZURE_CLIENT_ID=tu_client_id
# AZURE_CLIENT_SECRET=tu_client_secret
# AZURE_TENANT_ID=tu_tenant_id

# Opción 4: HashiCorp Vault (producción)
# KMS_PROVIDER=hashicorp_vault
# VAULT_URL=https://vault.tuempresa.com
# VAULT_TOKEN=tu_vault_token
# VAULT_SECRET_PATH=secret/ley21719/master-key

# ===========================================
# CLAVEÚNICA (Gobierno de Chile)
# ===========================================
CLAVEUNICA_CLIENT_ID=tu_client_id_claveunica
CLAVEUNICA_CLIENT_SECRET=tu_client_secret_claveunica
CLAVEUNICA_REDIRECT_URI=http://localhost:8000/api/v1/auth/claveunica/callback
CLAVEUNICA_ENV=sandbox  # sandbox o production

# ===========================================
# SII (Servicio de Impuestos Internos)
# ===========================================
SII_CLIENT_ID=tu_client_id_sii
SII_CLIENT_SECRET=tu_client_secret_sii
SII_REDIRECT_URI=http://localhost:8000/api/v1/auth/sii/callback
SII_ENV=sandbox  # sandbox o production

# ===========================================
# JWT CONFIGURATION
# ===========================================
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# ===========================================
# CORS CONFIGURATION
# ===========================================
CORS_ORIGINS=["http://localhost:3000","https://tudominio.cl"]

# ===========================================
# CELERY CONFIGURATION
# ===========================================
CELERY_WORKER_CONCURRENCY=4
CELERY_TASK_TIME_LIMIT=300
CELERY_TASK_SOFT_TIME_LIMIT=240

# ===========================================
# LOGGING & MONITOREO
# ===========================================
LOG_LEVEL=INFO
SENTRY_DSN=https://tu_sentry_dsn@sentry.io/tu_project_id
ENABLE_METRICS=True
```

### Variables Críticas de Producción

| Variable | Descripción | Prioridad |
|----------|-------------|-----------|
| `SECRET_KEY` | Clave para firmas JWT | 🔴 CRÍTICA |
| `ENCRYPTION_KEY` | Clave maestra AES-256 (solo si KMS_PROVIDER=local) | 🔴 CRÍTICA |
| `KMS_PROVIDER` | Proveedor de gestión de claves | 🔴 CRÍTICA |
| `DATABASE_URL` | Conexión a PostgreSQL | 🔴 CRÍTICA |
| `CLAVEUNICA_*` | Credenciales OAuth ClaveÚnica | 🟠 ALTA |
| `SII_*` | Credenciales OAuth SII | 🟠 ALTA |
| `CELERY_BROKER_URL` | Conexión a Redis para workers | 🟠 ALTA |

---

## 🔐 Seguridad Avanzada (KMS/HSM)

### Factory Pattern para Gestión de Claves

El sistema implementa un patrón factory que soporta múltiples proveedores de KMS:

```python
# app/services/kms_factory.py

class KMSProvider(Enum):
    LOCAL = "local"
    AWS_KMS = "aws_kms"
    AZURE_KV = "azure_kv"
    HASHICORP_VAULT = "hashicorp_vault"
    HSM_PKCS11 = "hsm_pkcs11"

class KeyManagementService:
    """Factory para servicios de gestión de claves"""
    
    @staticmethod
    def get_provider(provider_name: str) -> BaseKMSService:
        providers = {
            KMSProvider.LOCAL: LocalKMSService,
            KMSProvider.AWS_KMS: AWSKMSService,
            KMSProvider.AZURE_KV: AzureKVService,
            KMSProvider.HASHICORP_VAULT: HashiCorpVaultService,
            KMSProvider.HSM_PKCS11: HSMPKCS11Service,
        }
        return providers[KMSProvider(provider_name)]()
```

### Proveedores Soportados

#### 1. Local (Desarrollo)

```python
class LocalKMSService(BaseKMSService):
    """Uso exclusivo para desarrollo. NO USAR EN PRODUCCIÓN."""
    
    def encrypt(self, plaintext: str) -> str:
        key = os.getenv("ENCRYPTION_KEY").encode()
        # Implementación AES-256-CBC
        ...
    
    def decrypt(self, ciphertext: str) -> str:
        ...
```

⚠️ **Advertencia**: Nunca usar en producción. La clave reside en .env.

#### 2. AWS KMS (Producción)

```python
class AWSKMSService(BaseKMSService):
    """Integración con AWS Key Management Service"""
    
    def __init__(self):
        self.client = boto3.client(
            'kms',
            region_name=os.getenv("AWS_REGION"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
        )
        self.key_id = os.getenv("AWS_KMS_KEY_ID")
    
    def encrypt(self, plaintext: str) -> str:
        response = self.client.encrypt(
            KeyId=self.key_id,
            Plaintext=plaintext.encode('utf-8')
        )
        return base64.b64encode(response['CiphertextBlob']).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        response = self.client.decrypt(
            CiphertextBlob=base64.b64decode(ciphertext)
        )
        return response['Plaintext'].decode('utf-8')
```

**Ventajas:**
- ✅ Claves rotadas automáticamente por AWS
- ✅ Audit trail en CloudTrail
- ✅ Integración nativa con otros servicios AWS
- ✅ Cumple estándares SOC2, ISO 27001

#### 3. Azure Key Vault (Producción)

```python
class AzureKVService(BaseKMSService):
    """Integración con Azure Key Vault"""
    
    def __init__(self):
        credential = ClientSecretCredential(
            tenant_id=os.getenv("AZURE_TENANT_ID"),
            client_id=os.getenv("AZURE_CLIENT_ID"),
            client_secret=os.getenv("AZURE_CLIENT_SECRET")
        )
        self.client = CryptographyClient(
            key_identifier=os.getenv("AZURE_KV_KEY_NAME"),
            credential=credential
        )
    
    def encrypt(self, plaintext: str) -> str:
        result = self.client.encrypt(
            algorithm=EncryptionAlgorithm.rsa_oaep_256,
            plaintext=plaintext.encode('utf-8')
        )
        return base64.b64encode(result.ciphertext).decode()
```

#### 4. HashiCorp Vault (Producción)

```python
class HashiCorpVaultService(BaseKMSService):
    """Integración con HashiCorp Vault"""
    
    def __init__(self):
        self.client = hvac.Client(
            url=os.getenv("VAULT_URL"),
            token=os.getenv("VAULT_TOKEN")
        )
        self.secret_path = os.getenv("VAULT_SECRET_PATH")
    
    def get_key(self) -> bytes:
        secret = self.client.secrets.kv.v2.read_secret_version(
            path=self.secret_path
        )
        return secret['data']['data']['master_key'].encode()
```

#### 5. HSM Físico (PKCS#11) - Banca/Salud

```python
class HSMPKCS11Service(BaseKMSService):
    """Integración con HSM físico vía PKCS#11"""
    
    def __init__(self):
        self.lib = PKCS11Library(os.getenv("HSM_LIBRARY_PATH"))
        self.slot = self.lib.get_slot_list(token_present=True)[0]
        self.session = self.lib.open_session(self.slot)
        self.session.login(user_type=CKU_USER, pin=os.getenv("HSM_PIN"))
    
    def encrypt(self, plaintext: str) -> str:
        key = self.session.get_key(label=os.getenv("HSM_KEY_LABEL"))
        return key.encrypt(plaintext.encode())
```

**Casos de Uso:**
- 🏦 **Banca**: Requisito regulatorio SBIF
- 🏥 **Salud**: Datos sensibles según Ley 19.628
- 🏛️ **Gobierno**: Información clasificada

### Rotación de Claves

El sistema soporta rotación automática:

```python
# Configuración en .env
KMS_ROTATION_ENABLED=True
KMS_ROTATION_INTERVAL_DAYS=90
KMS_ROTATION_NOTIFICATION_EMAIL=dpo@tuempresa.cl
```

**Proceso de Rotación:**
1. Generar nueva clave maestra en KMS
2. Re-encriptar todos los RUTs con nueva clave
3. Mantener clave anterior por 30 días (rollback)
4. Eliminar clave antigua del KMS
5. Notificar al DPO

---

## 🗄️ Base de Datos y Migraciones

### Esquema de Base de Datos

```sql
-- Tablas principales
CREATE TABLE usuario (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rut_hash VARCHAR(64) UNIQUE NOT NULL,  -- SHA-256
    rut_encriptado TEXT NOT NULL,           -- AES-256
    nombre_completo VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    telefono VARCHAR(20),
    fecha_nacimiento DATE NOT NULL,
    tutor_id UUID REFERENCES usuario(id),
    fecha_registro TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_mayor_edad CHECK (fecha_nacimiento <= NOW() - INTERVAL '16 years')
);

CREATE TABLE organizacion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rut VARCHAR(20) UNIQUE NOT NULL,
    razon_social VARCHAR(255) NOT NULL,
    email_dpo VARCHAR(255) NOT NULL,
    webhook_url_revocacion TEXT,
    modelo_prevencion_certificado BOOLEAN DEFAULT FALSE
);

CREATE TABLE acceso_organizacion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL REFERENCES usuario(id),
    organizacion_id UUID NOT NULL REFERENCES organizacion(id),
    categoria_dato VARCHAR(50) NOT NULL,  -- SALUD, BIOMETRIA, etc.
    finalidad TEXT NOT NULL,
    estado VARCHAR(20) NOT NULL,  -- ACTIVO, REVOCADO
    receipt_hash VARCHAR(64) NOT NULL,  -- Firma digital
    fecha_otorgamiento TIMESTAMP NOT NULL,
    fecha_expiracion TIMESTAMP
);

CREATE TABLE log_acceso_datos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL REFERENCES usuario(id),
    organizacion_id UUID NOT NULL REFERENCES organizacion(id),
    tipo_acceso VARCHAR(20) NOT NULL,  -- LECTURA, MODIFICACION, ELIMINACION
    categoria_dato_consultado VARCHAR(50),
    justificacion_legal TEXT,
    ip_origen INET NOT NULL,
    fecha_acceso TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Índices críticos
CREATE INDEX idx_usuario_rut_hash ON usuario(rut_hash);
CREATE INDEX idx_log_acceso_fecha ON log_acceso_datos(fecha_acceso DESC);
CREATE INDEX idx_acceso_estado ON acceso_organizacion(estado);
```

### Migraciones con Alembic

**Estructura de carpetas:**
```
app/
├── alembic/
│   ├── versions/
│   │   ├── 001_initial_schema.py
│   │   ├── 002_add_brechas_module.py
│   │   ├── 003_add_portabilidad.py
│   │   └── ...
│   ├── env.py
│   └── script.py.mako
└── alembic.ini
```

**Comandos útiles:**

```bash
# Crear nueva migración
alembic revision --autogenerate -m "add_encargados_tratamiento"

# Aplicar migraciones
alembic upgrade head

# Revertir última migración
alembic downgrade -1

# Ver estado actual
alembic current

# Historial completo
alembic history
```

### Pool de Conexiones

Configuración optimizada para producción:

```python
# app/database.py

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,  # 10
    max_overflow=settings.DATABASE_MAX_OVERFLOW,  # 20
    pool_pre_ping=True,  # Validar conexiones antes de usar
    pool_recycle=3600,   # Reciclar cada hora
    echo=settings.DEBUG   # Log SQL en desarrollo
)
```

---

## ⚡ Tareas Asíncronas (Celery)

### Configuración de Celery

```python
# app/celery_app.py

from celery import Celery
from celery.schedules import crontab

celery_app = Celery(
    'ley21719',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Configuración de tareas
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Santiago',
    enable_utc=True,
    worker_concurrency=settings.CELERY_WORKER_CONCURRENCY,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
)

# Tareas programadas (beat)
celery_app.conf.beat_schedule = {
    # Ejecutar limpieza de datos vencidos cada día a las 3 AM
    'cleanup-expired-consents': {
        'task': 'app.services.lifecycle_worker.cleanup_expired_consents',
        'schedule': crontab(hour=3, minute=0),
    },
    # Verificar políticas de retención semanalmente
    'check-retention-policies': {
        'task': 'app.services.lifecycle_worker.check_retention_policies',
        'schedule': crontab(hour=2, minute=0, day_of_week=1),  # Lunes
    },
    # Generar reporte mensual de cumplimiento
    'monthly-compliance-report': {
        'task': 'app.services.cumplimiento_service.generate_monthly_report',
        'schedule': crontab(hour=8, minute=0, day_of_month=1),
    },
}
```

### Lifecycle Worker - Borrado Automático

```python
# app/services/lifecycle_worker.py

from celery import shared_task
from sqlalchemy import and_
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def cleanup_expired_consents(self):
    """
    Elimina o anonimiza datos cuyos consentimientos han expirado.
    Cumple con principio de limitación del plazo de conservación (Art. 6).
    """
    try:
        db = SessionLocal()
        
        # Buscar consentimientos vencidos
        expired_consents = db.query(AccesoOrganizacion).filter(
            and_(
                AccesoOrganizacion.estado == "ACTIVO",
                AccesoOrganizacion.fecha_expiracion < datetime.utcnow()
            )
        ).all()
        
        logger.info(f"Encontrados {len(expired_consents)} consentimientos vencidos")
        
        for consent in expired_consents:
            # Cambiar estado a REVOCADO
            consent.estado = "REVOCADO"
            
            # Registrar en log de auditoría
            log = LogAccesoDatos(
                usuario_id=consent.usuario_id,
                organizacion_id=consent.organizacion_id,
                tipo_acceso="ELIMINACION",
                categoria_dato_consultado=consent.categoria_dato,
                justificacion_legal="Vencimiento de consentimiento - Art. 6 Ley 21.719",
                ip_origen="SYSTEM"
            )
            db.add(log)
        
        db.commit()
        logger.info(f"Procesados {len(expired_consents)} consentimientos")
        
        return {"status": "success", "processed": len(expired_consents)}
        
    except Exception as e:
        logger.error(f"Error en cleanup: {str(e)}")
        db.rollback()
        raise self.retry(exc=e, countdown=300)  # Reintentar en 5 min
    finally:
        db.close()

@shared_task(bind=True, max_retries=3)
def check_retention_policies(self):
    """
    Verifica políticas de retención y ejecuta borrado automático.
    """
    try:
        db = SessionLocal()
        
        # Obtener políticas activas
        policies = db.query(PoliticaRetencionDatos).filter(
            PoliticaRetencionDatos.activa == True
        ).all()
        
        deleted_count = 0
        
        for policy in policies:
            # Calcular fecha límite
            cutoff_date = datetime.utcnow() - timedelta(days=policy.plazo_retencion_dias)
            
            # Identificar registros a eliminar
            if policy.tipo_dato == "ACCESOS":
                records = db.query(AccesoOrganizacion).filter(
                    AccesoOrganizacion.fecha_otorgamiento < cutoff_date,
                    AccesoOrganizacion.estado == "REVOCADO"
                ).all()
                
                for record in records:
                    # Eliminación lógica (anonimización)
                    record.receipt_hash = None
                    record.finalidad = "[ELIMINADO POR POLÍTICA DE RETENCIÓN]"
                    deleted_count += 1
        
        db.commit()
        logger.info(f"Políticas de retención: {deleted_count} registros procesados")
        
        return {"status": "success", "deleted": deleted_count}
        
    except Exception as e:
        logger.error(f"Error en retención: {str(e)}")
        db.rollback()
        raise self.retry(exc=e, countdown=600)
    finally:
        db.close()
```

### Ejecución de Workers

**Desarrollo:**
```bash
# Terminal 1: Iniciar Celery worker
celery -A app.celery_app worker --loglevel=info --concurrency=4

# Terminal 2: Iniciar Celery beat (scheduler)
celery -A app.celery_app beat --loglevel=info
```

**Producción (Docker):**
```yaml
# docker-compose.yml
services:
  celery-worker:
    build: .
    command: celery -A app.celery_app worker --loglevel=warning --concurrency=8
    environment:
      - ENVIRONMENT=production
    depends_on:
      - redis
      - postgres
  
  celery-beat:
    build: .
    command: celery -A app.celery_app beat --loglevel=warning
    environment:
      - ENVIRONMENT=production
    depends_on:
      - redis
```

### Monitoreo de Tareas

```bash
# Ver tareas en ejecución
celery -A app.celery_app inspect active

# Ver estadísticas
celery -A app.celery_app inspect stats

# Ver tareas registradas
celery -A app.celery_app inspect registered
```

---

## 📡 API Reference

### Endpoints por Módulo (76 total)

#### 🔐 Autenticación (6 endpoints)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/auth/claveunica/login` | Iniciar flujo ClaveÚnica |
| GET | `/api/v1/auth/claveunica/callback` | Callback OAuth ClaveÚnica |
| GET | `/api/v1/auth/sii/login` | Iniciar flujo SII |
| GET | `/api/v1/auth/sii/callback` | Callback OAuth SII |
| POST | `/api/v1/auth/refresh` | Refresh JWT token |
| POST | `/api/v1/auth/logout` | Invalidar sesión |

#### 👤 Usuarios (8 endpoints)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/usuarios/me` | Perfil del usuario autenticado |
| PUT | `/api/v1/usuarios/me` | Actualizar perfil |
| POST | `/api/v1/usuarios/validar-tutor` | Validar patria potestad |
| GET | `/api/v1/usuarios/mis-accesos` | Accesos otorgados por el usuario |
| DELETE | `/api/v1/usuarios/acceso/{id}` | Revocar acceso específico |
| GET | `/api/v1/usuarios/timeline-accesos` | Timeline de accesos (auditoría) |
| POST | `/api/v1/usuarios/supresion` | Derecho al olvido |
| GET | `/api/v1/usuarios/certificado-supresion/{token}` | Descargar certificado |

#### 🏢 Organizaciones (10 endpoints)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/organizaciones/me` | Perfil organización |
| PUT | `/api/v1/organizaciones/me` | Actualizar perfil |
| POST | `/api/v1/organizaciones/api-keys` | Crear API key |
| GET | `/api/v1/organizaciones/api-keys` | Listar API keys |
| DELETE | `/api/v1/organizaciones/api-keys/{id}` | Revocar API key |
| GET | `/api/v1/organizaciones/audit-report` | Reporte de auditoría |
| POST | `/api/v1/organizaciones/webhooks` | Configurar webhook |
| GET | `/api/v1/organizaciones/webhooks` | Listar webhooks |
| POST | `/api/v1/organizaciones/encargados` | Registrar encargado tratamiento |
| GET | `/api/v1/organizaciones/encargados` | Listar encargados |

#### 🔑 Derechos ARCO (12 endpoints)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/arcos` | Crear solicitud ARCO |
| GET | `/api/v1/arcos` | Listar solicitudes (ciudadano) |
| GET | `/api/v1/arcos/{id}` | Detalle solicitud |
| PUT | `/api/v1/arcos/{id}/respuesta` | Responder solicitud (organización) |
| POST | `/api/v1/arcos/{id}/prorroga` | Solicitar prórroga |
| GET | `/api/v1/arcos/estadisticas` | Métricas ARCO |
| POST | `/api/v1/portabilidad/solicitar` | Solicitar portabilidad |
| GET | `/api/v1/portabilidad/descargar/{token}` | Descargar datos (JSON/CSV/XML) |
| GET | `/api/v1/portabilidad/historial` | Historial de exportaciones |
| POST | `/api/v1/oposicion-ia` | Oponerse a decisión automatizada |
| GET | `/api/v1/oposicion-ia/{id}` | Estado impugnación |
| PUT | `/api/v1/oposicion-ia/{id}/intervencion` | Solicitar intervención humana |

#### 📊 Cumplimiento Normativo (25 endpoints)

**RAT - Registro Actividades Tratamiento:**
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/rat` | Crear registro RAT |
| GET | `/api/v1/rat` | Listar registros |
| GET | `/api/v1/rat/{id}` | Detalle registro |
| PUT | `/api/v1/rat/{id}` | Actualizar registro |
| DELETE | `/api/v1/rat/{id}` | Eliminar registro |
| GET | `/api/v1/rat/reporte` | Generar reporte PDF |

**Brechas de Seguridad:**
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/brechas` | Reportar brecha |
| GET | `/api/v1/brechas` | Listar brechas |
| GET | `/api/v1/brechas/{id}` | Detalle forense |
| POST | `/api/v1/brechas/{id}/notificar-agencia` | Notificar Agencia |
| POST | `/api/v1/brechas/{id}/notificar-afectados` | Notificar titulares |
| GET | `/api/v1/brechas/estadisticas` | Métricas de brechas |

**EIPD - Evaluación Impacto:**
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/eipd` | Crear evaluación |
| GET | `/api/v1/eipd` | Listar evaluaciones |
| GET | `/api/v1/eipd/{id}` | Detalle evaluación |
| POST | `/api/v1/eipd/{id}/dictamen` | Dictamen DPO |
| PUT | `/api/v1/eipd/{id}` | Actualizar evaluación |

**Panel DPO:**
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/dpo/dashboard` | Métricas de cumplimiento |
| GET | `/api/v1/dpo/alertas` | Alertas críticas |
| GET | `/api/v1/dpo/reporte-cumplimiento` | Reporte consolidado |
| GET | `/api/v1/dpo/calendario` | Calendario de vencimientos |

#### 🔄 Ciclo de Vida (8 endpoints)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/politicas-retencion` | Crear política |
| GET | `/api/v1/politicas-retencion` | Listar políticas |
| PUT | `/api/v1/politicas-retencion/{id}` | Actualizar política |
| DELETE | `/api/v1/politicas-retencion/{id}` | Eliminar política |
| POST | `/api/v1/ejecucion-limpieza` | Ejecutar limpieza manual |
| GET | `/api/v1/ejecucion-limpieza/historial` | Historial de ejecuciones |
| GET | `/api/v1/ejecucion-limpieza/estadisticas` | Métricas de borrado |
| POST | `/api/v1/anonimizacion-masiva` | Anonimizar dataset |

#### 🔗 Webhooks (4 endpoints)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/webhooks` | Listar webhooks configurados |
| POST | `/api/v1/webhooks` | Crear webhook |
| PUT | `/api/v1/webhooks/{id}` | Actualizar webhook |
| POST | `/api/v1/webhooks/{id}/reenviar` | Reenviar evento fallido |

#### 📜 Legal Design (3 endpoints)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/legal/traducciones` | Listar traducciones legales |
| POST | `/api/v1/legal/traducciones` | Crear traducción ciudadano |
| GET | `/api/v1/legal/texto/{id}` | Obtener texto simplificado |

### Ejemplos de Uso

#### Portabilidad de Datos

```bash
# Solicitar exportación completa
curl -X POST http://localhost:8000/api/v1/portabilidad/solicitar \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "formato": "JSON",
    "incluir_logs": true,
    "incluir_consents": true
  }'

# Respuesta:
{
  "token": "prt_abc123xyz",
  "fecha_expiracion": "2024-01-15T10:30:00Z",
  "url_descarga": "/api/v1/portabilidad/descargar/prt_abc123xyz"
}

# Descargar datos
curl -X GET http://localhost:8000/api/v1/portabilidad/descargar/prt_abc123xyz \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -o mis_datos.zip
```

#### Derecho al Olvido

```bash
# Solicitar supresión
curl -X POST http://localhost:8000/api/v1/usuarios/supresion \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "motivo": "Ejercicio de derecho ARCO - Supresión",
    "confirmacion": true
  }'

# Respuesta:
{
  "solicitud_id": "sup_xyz789",
  "fecha_ejecucion": "2024-01-15T10:30:00Z",
  "certificado_token": "cert_abc456",
  "url_certificado": "/api/v1/usuarios/certificado-supresion/cert_abc456"
}
```

---

## 🚀 Despliegue en Producción

### Docker Compose (Recomendado)

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  postgres:
    image: postgres:14-alpine
    environment:
      POSTGRES_DB: ley21719_db
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - ley21719_net
    restart: always

  redis:
    image: redis:6-alpine
    networks:
      - ley21719_net
    restart: always

  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/ley21719_db
      - REDIS_URL=redis://redis:6379/0
      - KMS_PROVIDER=${KMS_PROVIDER}
      # Variables KMS específicas según proveedor
    depends_on:
      - postgres
      - redis
    networks:
      - ley21719_net
    restart: always

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.frontend
    environment:
      - REACT_APP_API_URL=https://api.tudominio.cl
    networks:
      - ley21719_net
    restart: always

  celery-worker:
    build:
      context: .
      dockerfile: Dockerfile.backend
    command: celery -A app.celery_app worker --loglevel=warning --concurrency=8
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/ley21719_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    networks:
      - ley21719_net
    restart: always

  celery-beat:
    build:
      context: .
      dockerfile: Dockerfile.backend
    command: celery -A app.celery_app beat --loglevel=warning
    environment:
      - ENVIRONMENT=production
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
    networks:
      - ley21719_net
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend
    networks:
      - ley21719_net
    restart: always

volumes:
  postgres_data:

networks:
  ley21719_net:
    driver: bridge
```

### Kubernetes (Escalamiento Empresarial)

```yaml
# k8s/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ley21719-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: tu-registry/ley21719-backend:latest
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        - name: KMS_PROVIDER
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: kms-provider
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Checklist Pre-Producción

- [ ] **Seguridad**
  - [ ] KMS configurado (NO usar local)
  - [ ] HTTPS obligatorio (certificado SSL válido)
  - [ ] Firewall configurado (solo puertos 80/443)
  - [ ] Rate limiting activado
  - [ ] CORS restringido a dominios autorizados

- [ ] **Base de Datos**
  - [ ] Backups automáticos configurados (diarios)
  - [ ] Replicación maestro-esclavo habilitada
  - [ ] Pool de conexiones optimizado
  - [ ] Índices verificados

- [ ] **Monitoreo**
  - [ ] Sentry configurado para errores
  - [ ] Métricas de rendimiento (Prometheus/Grafana)
  - [ ] Alertas de brechas de seguridad
  - [ ] Logs centralizados (ELK Stack)

- [ ] **Cumplimiento**
  - [ ] DPO designado y contactable
  - [ ] Políticas de retención documentadas
  - [ ] Contrato de encargo con proveedores cloud
  - [ ] EIPD realizada para datos sensibles

- [ ] **Pruebas**
  - [ ] Tests de carga completados (≥1000 req/s)
  - [ ] Penetration testing realizado
  - [ ] Plan de recuperación ante desastres probado

---

## 📊 Monitoreo y Logs

### Integración con Sentry

```python
# app/main.py

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[
        FastApiIntegration(),
        SqlalchemyIntegration(),
    ],
    traces_sample_rate=0.1,  # 10% de transacciones
    environment=os.getenv("ENVIRONMENT", "development"),
    release="ley21719@1.0.0"
)
```

### Métricas Clave a Monitorear

| Métrica | Umbral Alerta | Acción |
|---------|---------------|--------|
| Latencia API p95 | >500ms | Escalar backend |
| Error rate | >1% | Investigar logs |
| Brechas reportadas | >0 | Notificar DPO inmediatamente |
| Tareas Celery fallidas | >5/hora | Revisar worker |
| Conexiones DB activas | >80% pool | Aumentar pool size |

### Dashboard Grafana (Ejemplo)

```json
{
  "dashboard": {
    "title": "Ley 21.719 - Compliance Dashboard",
    "panels": [
      {
        "title": "Solicitudes ARCO por Tipo",
        "type": "piechart",
        "targets": [
          {
            "query": "SELECT tipo, COUNT(*) FROM solicitud_arco GROUP BY tipo"
          }
        ]
      },
      {
        "title": "Accesos por Organización (24h)",
        "type": "barchart",
        "targets": [
          {
            "query": "SELECT organizacion_id, COUNT(*) FROM log_acceso_datos WHERE fecha_acceso > NOW() - INTERVAL '24 hours' GROUP BY organizacion_id"
          }
        ]
      },
      {
        "title": "Estado de Consentimientos",
        "type": "stat",
        "targets": [
          {
            "query": "SELECT estado, COUNT(*) FROM acceso_organizacion GROUP BY estado"
          }
        ]
      }
    ]
  }
}
```

### Alertas Críticas

```yaml
# alertmanager.yml
groups:
- name: ley21719_alerts
  rules:
  - alert: BrechaSeguridadReportada
    expr: brechas_totales > 0
    for: 0m
    labels:
      severity: critical
      team: legal
    annotations:
      summary: "Brecha de seguridad detectada"
      description: "Se ha reportado una brecha de seguridad. Notificar Agencia en 72h."
  
  - alert: TasaErrorAlta
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
    for: 5m
    labels:
      severity: warning
      team: devops
    annotations:
      summary: "Tasa de error HTTP 5xx elevada"
      description: "Más del 1% de requests están fallando."
  
  - alert: Consenti