# Manual Técnico de Implementación - Ley 21.719 Chile

## Índice
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

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (React + Vite)                  │
│  - Login ClaveÚnica/SII                                      │
│  - Dashboard Ciudadano (Portabilidad, Timeline, Supresión)   │
│  - Dashboard Organización (RAT, Brechas, Panel DPO)          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ HTTP/REST
┌─────────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI + Python)                 │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ API Gateway / Router                                  │    │
│  │  - /auth/* (OAuth2 ClaveÚnica, SII)                  │    │
│  │  - /api/v1/usuarios/*                                │    │
│  │  - /api/v1/organizaciones/*                          │    │
│  │  - /api/v1/ciudadano/* (Derechos ARCO+)              │    │
│  │  - /api/v1/rat/*                                     │    │
│  │  - /api/v1/brechas/*                                 │    │
│  │  - /api/v1/eipd/*                                    │    │
│  │  - /api/v1/encargados/*                              │    │
│  └──────────────────────────────────────────────────────┘    │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ Servicios de Negocio                                  │    │
│  │  - portabilidad_service.py                            │    │
│  │  - supresion_service.py                               │    │
│  │  - brechas_service.py                                 │    │
│  │  - eipd_service.py                                    │    │
│  │  - rat_service.py                                     │    │
│  │  - lifecycle_worker.py (Celery)                       │    │
│  │  - kms_factory.py                                     │    │
│  └──────────────────────────────────────────────────────┘    │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ Seguridad                                             │    │
│  │  - SHA-256 (Hashing RUT, tokens)                     │    │
│  │  - AES-256 (Encriptación datos sensibles)            │    │
│  │  - KMS/HSM Integration (AWS, Azure, HashiCorp)       │    │
│  └──────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    CAPA DE DATOS                             │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │ PostgreSQL      │  │ Redis           │                   │
│  │ - Modelos ORM   │  │ - Cache         │                   │
│  │ - Encriptación  │  │ - Celery Broker │                   │
│  │ - Índices SHA   │  │ - Session Store │                   │
│  └─────────────────┘  └─────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

### Flujo de Datos Críticos

1. **Autenticación**: OAuth2 con ClaveÚnica (ciudadanos) y SII (organizaciones)
2. **Almacenamiento RUT**: 
   - `rutHash`: SHA-256 para indexación y búsquedas
   - `rutEncriptado`: AES-256 para recuperación autorizada
3. **Acceso a Datos**: Logging obligatorio en `LogAccesoDatos` con justificación legal
4. **Ciclo de Vida**: Celery ejecuta borrado/anonimización según políticas RAT

---

## Requisitos Previos

### Software Base
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+

### Dependencias Python
```bash
pip install -r requirements.txt
```

**requirements.txt incluye:**
- fastapi, uvicorn, sqlalchemy, psycopg2-binary
- celery, redis
- cryptography, pyjwt, python-jose
- httpx (clientes OAuth)
- reportlab (generación PDF certificados)
- python-dotenv

### Dependencias Node.js
```bash
cd frontend
npm install
```

---

## Configuración del Entorno

### Archivo `.env` (Ejemplo Completo)

```ini
# ===========================================
# CONFIGURACIÓN GENERAL
# ===========================================
APP_NAME=Ley21719-Compliance
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=tu_secret_key_muy_seguro_cambiar_en_produccion

# ===========================================
# BASE DE DATOS
# ===========================================
DATABASE_URL=postgresql://usuario:password@localhost:5432/ley21719_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# ===========================================
# REDIS (Cache + Celery)
# ===========================================
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# ===========================================
# SEGURIDAD - ENCRIPTACIÓN
# ===========================================
# NOTA: En producción usar KMS/HSM (ver sección Seguridad Avanzada)
ENCRYPTION_KEY=clave_aes_256_de_32_caracteres!!
HASH_SALT=salt_unico_para_sha256

# ===========================================
# GESTIÓN DE CLAVES (KMS/HSM)
# ===========================================
KMS_PROVIDER=local  # Opciones: local, aws, azure, hashicorp, hsm
AWS_KMS_KEY_ID=arn:aws:kms:region:account:key/key-id
AZURE_KEY_VAULT_URL=https://vault-name.vault.azure.net/
AZURE_CLIENT_ID=client-id
AZURE_CLIENT_SECRET=client-secret
AZURE_TENANT_ID=tenant-id
HASHICORP_VAULT_URL=http://vault:8200
HASHICORP_VAULT_TOKEN=s.token
HSM_LIBRARY_PATH=/usr/lib/libpkcs11.so
HSM_SLOT_ID=0
HSM_PIN=123456

# ===========================================
# JWT CONFIG
# ===========================================
JWT_SECRET_KEY=jwt_secret_muy_seguro_cambiar_en_produccion
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ===========================================
# CLAVEÚNICA OAUTH2
# ===========================================
CLAVEUNICA_CLIENT_ID=tu_client_id_claveunica
CLAVEUNICA_CLIENT_SECRET=tu_client_secret_claveunica
CLAVEUNICA_REDIRECT_URI=https://tudominio.cl/auth/claveunica/callback
CLAVEUNICA_AUTH_URL=https://id.claveunica.gob.cl/oauth2/authorize
CLAVEUNICA_TOKEN_URL=https://id.claveunica.gob.cl/oauth2/token
CLAVEUNICA_USERINFO_URL=https://id.claveunica.gob.cl/oauth2/userinfo
CLAVEUNICA_SCOPE=openid profile email

# ===========================================
# SII OAUTH2 (Chile)
# ===========================================
SII_CLIENT_ID=tu_client_id_sii
SII_CLIENT_SECRET=tu_client_secret_sii
SII_REDIRECT_URI=https://tudominio.cl/auth/sii/callback
SII_AUTH_URL=https://oauth2.sii.cl/oauth2/authorize
SII_TOKEN_URL=https://oauth2.sii.cl/oauth2/token
SII_USERINFO_URL=https://oauth2.sii.cl/oauth2/userinfo
SII_SCOPE=rut razon_social giro

# ===========================================
# WEBHOOKS Y NOTIFICACIONES
# ===========================================
WEBHOOK_TIMEOUT_SECONDS=30
WEBHOOK_RETRY_ATTEMPTS=3
AGENCIA_PROTECCION_DATOS_WEBHOOK=https://api.agenciaprotecciondatos.cl/webhooks/brechas

# ===========================================
# CELERY CONFIG
# ===========================================
CELERY_WORKER_CONCURRENCY=4
CELERY_TASK_TIME_LIMIT=300
LIFECYCLE_CLEANUP_SCHEDULE=cron 0 3 * * *  # Diario a las 3 AM

# ===========================================
# LOGGING
# ===========================================
LOG_LEVEL=INFO
LOG_FILE=/var/log/ley21719/app.log
AUDIT_LOG_FILE=/var/log/ley21719/audit.log

# ===========================================
# CORS (Frontend)
# ===========================================
FRONTEND_URL=https://tudominio.cl
ALLOWED_ORIGINS=https://tudominio.cl,https://www.tudominio.cl
```

---

## Seguridad Avanzada (KMS/HSM)

### Factory Pattern para Gestión de Claves

El sistema implementa un patrón factory (`app/services/kms_factory.py`) que soporta múltiples proveedores:

```python
from app.services.kms_factory import KeyManagementService

# Configuración automática según variable de entorno KMS_PROVIDER
kms = KeyManagementService.create()

# Encriptar dato sensible
encrypted = kms.encrypt("dato_secreto")

# Desencriptar
decrypted = kms.decrypt(encrypted)

# Rotar clave (solo proveedores cloud/HSM)
kms.rotate_key()
```

### Proveedores Soportados

| Proveedor | Caso de Uso | Configuración |
|-----------|-------------|---------------|
| **Local** | Desarrollo/Testing | `KMS_PROVIDER=local` + `ENCRYPTION_KEY` en .env |
| **AWS KMS** | Producción en AWS | `KMS_PROVIDER=aws` + `AWS_KMS_KEY_ID` |
| **Azure Key Vault** | Producción en Azure | `KMS_PROVIDER=azure` + credenciales Azure |
| **HashiCorp Vault** | On-premise/Cloud agnóstico | `KMS_PROVIDER=hashicorp` + URL + token |
| **HSM Físico** | Banca, Salud, Gobierno | `KMS_PROVIDER=hsm` + librería PKCS#11 |

### Ejemplo: Configuración AWS KMS

1. Crear clave en AWS KMS:
```bash
aws kms create-key --description "Ley21719 Encryption Key"
```

2. Configurar variables de entorno:
```ini
KMS_PROVIDER=aws
AWS_KMS_KEY_ID=arn:aws:kms:us-east-1:123456789012:key/abcd1234-...
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
```

3. El sistema automáticamente usará AWS KMS para todas las operaciones de encriptación.

### Ejemplo: Configuración HSM Físico (PKCS#11)

Para sectores regulados (banca, salud):

```ini
KMS_PROVIDER=hsm
HSM_LIBRARY_PATH=/usr/lib/libpkcs11.so
HSM_SLOT_ID=0
HSM_PIN=123456
HSM_KEY_LABEL=LEY21719_MASTER_KEY
```

Requiere:
- Librería PKCS#11 del fabricante (Thales, Gemalto, YubiHSM, etc.)
- Certificados instalados en el HSM
- Acceso físico o de red al dispositivo

---

## Base de Datos y Migraciones

### Esquema de Base de Datos

El sistema utiliza **15 modelos** principales:

1. **Usuario**: Datos ciudadanos con RUT hasheado/encriptado
2. **Organizacion**: Empresas/entidades responsables del tratamiento
3. **OrganizacionApiKey**: Credenciales API para integraciones
4. **AccesoOrganizacion**: Consentimientos otorgados por usuarios
5. **SolicitudConsentimiento**: Propuestas de consentimiento
6. **SolicitudArco**: Derechos ARCO (Acceso, Rectificación, Cancelación, Oposición)
7. **LogAccesoDatos**: Auditoría obligatoria de todos los accesos
8. **RegistroActividadesTratamiento (RAT)**: Registro Art. 27
9. **NotificacionBrecha**: Gestión de incidentes 72h
10. **EvaluacionImpactoProteccionDatos (EIPD)**: Evaluación riesgos Art. 34
11. **WebhookRegistro**: Notificaciones automáticas
12. **PoliticaRetencionDatos**: Plazos de conservación
13. **EjecucionEliminacionAutomatica**: Logs de borrado programado
14. **ExportacionPortabilidad**: Solicitudes de portabilidad
15. **EncargadoTratamiento**: Terceros procesadores de datos
16. **DecisionAutomatizada**: Registro de decisiones algorítmicas

### Ejecutar Migraciones

```bash
# Alembic ya está configurado
alembic upgrade head

# Verificar estado
alembic current

# Generar nueva migración (si se modifican modelos)
alembic revision --autogenerate -m "Descripción del cambio"
```

### Índices Críticos para Rendimiento

Los siguientes índices están pre-configurados en los modelos:

```sql
-- Búsquedas por RUT (hash)
CREATE INDEX idx_usuario_rut_hash ON usuario(rut_hash);
CREATE INDEX idx_solicitud_arco_rut ON solicitud_arco(rut_ciudadano_hash);

-- Auditoría por fecha
CREATE INDEX idx_log_acceso_fecha ON log_acceso_datos(fecha_acceso DESC);

-- Consentimientos activos
CREATE INDEX idx_acceso_estado ON acceso_organizacion(estado, fecha_expiracion);

-- Brechas por estado
CREATE INDEX idx_brecha_estado ON notificacion_brecha(estado, fecha_creacion);
```

---

## Tareas Asíncronas (Celery)

### Configuración de Celery

El sistema usa Celery para:
- Borrado automático de datos expirados
- Envío de notificaciones masivas
- Generación de reportes pesados
- Webhooks retry

**Archivo: `app/celery_app.py`**
```python
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    'ley21719',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        'app.services.lifecycle_worker',
        'app.services.brechas_service',
        'app.services.webhook_service',
    ]
)

celery_app.conf.update(
    worker_concurrency=settings.CELERY_WORKER_CONCURRENCY,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Santiago',
    enable_utc=True,
)
```

### Worker de Ciclo de Vida

**Archivo: `app/services/lifecycle_worker.py`**

```python
from celery import schedules
from app.celery_app import celery_app
from app.services.supresion_service import SupresionService
from app.models.cumplimiento_models import PoliticaRetencionDatos

@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Configura tareas periódicas"""
    sender.add_periodic_task(
        schedules.crontab(hour=3, minute=0),  # Diario 3 AM
        execute_lifecycle_cleanup.s(),
        name='cleanup-expired-data'
    )

@celery_app.task(bind=True, max_retries=3)
def execute_lifecycle_cleanup(self):
    """
    Ejecuta el borrado/anonimización de datos expirados
    según políticas definidas en RAT
    """
    try:
        politicas = PoliticaRetencionDatos.objects.filter(activa=True)
        total_eliminados = 0
        
        for politica in politicas:
            if politica.debe_ejecutar_borrado():
                eliminados = politica.ejecutar_borrado_programado()
                total_eliminados += eliminados
        
        return f"Limpieza completada: {total_eliminados} registros procesados"
    
    except Exception as exc:
        raise self.retry(exc=exc, countdown=300)
```

### Ejecutar Workers

```bash
# Terminal 1: Worker principal
celery -A app.celery_app worker --loglevel=info --concurrency=4

# Terminal 2: Beat (tareas programadas)
celery -A app.celery_app beat --loglevel=info

# O combinado
celery -A app.celery_app worker --beat --loglevel=info
```

### Monitoreo de Celery

```bash
# Ver tareas en cola
celery -A app.celery_app inspect active

# Ver workers disponibles
celery -A app.celery_app inspect ping

# Flower (dashboard web opcional)
pip install flower
celery -A app.celery_app flower
```

---

## API Reference

### Endpoints por Categoría

#### 🔐 Autenticación
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/auth/claveunica/login` | Inicia flujo OAuth ClaveÚnica |
| GET | `/auth/claveunica/callback` | Callback OAuth ClaveÚnica |
| GET | `/auth/sii/login` | Inicia flujo OAuth SII |
| GET | `/auth/sii/callback` | Callback OAuth SII |
| POST | `/auth/refresh` | Refresca token JWT |
| GET | `/auth/verify` | Verifica token actual |
| POST | `/auth/logout` | Invalida tokens |

#### 👤 Usuario / Ciudadano
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/usuarios/me` | Perfil del usuario autenticado |
| PUT | `/api/v1/usuarios/me` | Actualizar perfil |
| GET | `/api/v1/ciudadano/mis-datos` | **Portabilidad**: Descarga todos los datos |
| POST | `/api/v1/ciudadano/portabilidad` | Solicitar exportación en formato específico |
| GET | `/api/v1/ciudadano/portabilidad/{id}/descargar` | Descargar archivo exportado |
| POST | `/api/v1/ciudadano/supresion` | **Derecho al Olvido**: Solicitar eliminación |
| GET | `/api/v1/ciudadano/supresion/{id}/certificado` | Descargar certificado de eliminación |
| GET | `/api/v1/ciudadano/timeline-accesos` | Historial de accesos a sus datos |
| POST | `/api/v1/ciudadano/oposicion-ia` | Impugnar decisión automatizada |
| GET | `/api/v1/ciudadano/oposicion-ia` | Listar impugnaciones |
| GET | `/api/v1/ciudadano/solicitudes-arco` | Historial de solicitudes ARCO |
| POST | `/api/v1/ciudadano/solicitudes-arco` | Nueva solicitud ARCO |
| GET | `/api/v1/ciudadano/consentimientos` | Consentimientos activos/revocados |

#### 🏢 Organización
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/organizaciones/me` | Perfil organización autenticada |
| PUT | `/api/v1/organizaciones/me` | Actualizar perfil |
| POST | `/api/v1/organizaciones/api-keys` | Crear nueva API key |
| GET | `/api/v1/organizaciones/api-keys` | Listar API keys |
| DELETE | `/api/v1/organizaciones/api-keys/{id}` | Revocar API key |
| GET | `/api/v1/organizaciones/accesos` | Accesos otorgados por usuarios |
| POST | `/api/v1/organizaciones/solicitudes-consentimiento` | Proponer consentimiento |
| GET | `/api/v1/organizaciones/audit-report` | Reporte de auditoría interno |

#### 📋 RAT (Registro Actividades Tratamiento)
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/rat` | Registrar nueva actividad de tratamiento |
| GET | `/api/v1/rat` | Listar actividades registradas |
| GET | `/api/v1/rat/{id}` | Detalle de actividad |
| PUT | `/api/v1/rat/{id}` | Actualizar actividad |
| GET | `/api/v1/rat/reporte` | Generar reporte PDF para Agencia |

#### 🚨 Brechas de Seguridad
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/brechas` | Reportar nueva brecha |
| GET | `/api/v1/brechas` | Listar brechas reportadas |
| POST | `/api/v1/brechas/{id}/notificar-agencia` | Notificar a Agencia Protección de Datos |
| POST | `/api/v1/brechas/{id}/notificar-afectados` | Notificar a titulares afectados |
| GET | `/api/v1/brechas/estadisticas` | Métricas y estadísticas |

#### 📊 EIPD (Evaluación de Impacto)
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/eipd` | Crear evaluación de impacto |
| GET | `/api/v1/eipd` | Listar evaluaciones |
| GET | `/api/v1/eipd/{id}` | Detalle evaluación |
| POST | `/api/v1/eipd/{id}/dictamen` | Generar dictamen DPO |

#### 🤝 Encargados de Tratamiento
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/encargados` | Registrar encargado de tratamiento |
| GET | `/api/v1/encargados` | Listar encargados |
| GET | `/api/v1/encargados/{id}` | Detalle encargado |
| PUT | `/api/v1/encargados/{id}` | Actualizar contrato |
| POST | `/api/v1/encargados/{id}/auditoria` | Registrar auditoría a tercero |

#### ⚙️ Ciclo de Vida
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/organizaciones/{id}/politicas-retencion` | Definir política retención |
| GET | `/api/v1/organizaciones/{id}/politicas-retencion` | Listar políticas |
| GET | `/api/v1/ciclo-vida/estadisticas` | Métricas de eliminaciones automáticas |

#### 🛡️ Panel DPO
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/dpo/dashboard` | Métricas generales de cumplimiento |
| GET | `/api/v1/dpo/alertas` | Alertas críticas pendientes |
| GET | `/api/v1/dpo/reporte-cumplimiento` | Reporte ejecutivo |
| GET | `/api/v1/dpo/calendario` | Fechas límite (ARCO, brechas, etc.) |

---

## Despliegue en Producción

### Docker Compose (Recomendado)

**docker-compose.yml**
```yaml
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
      - ley21719_network

  redis:
    image: redis:6-alpine
    networks:
      - ley21719_network

  backend:
    build: ./app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
    environment:
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/ley21719_db
      - REDIS_URL=redis://redis:6379/0
      - KMS_PROVIDER=${KMS_PROVIDER}
      # ... resto de variables
    depends_on:
      - postgres
      - redis
    networks:
      - ley21719_network
    ports:
      - "8000:8000"

  celery_worker:
    build: ./app
    command: celery -A app.celery_app worker --loglevel=info --concurrency=4
    environment:
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/ley21719_db
      - REDIS_URL=redis://redis:6379/0
      - KMS_PROVIDER=${KMS_PROVIDER}
    depends_on:
      - postgres
      - redis
    networks:
      - ley21719_network

  celery_beat:
    build: ./app
    command: celery -A app.celery_app beat --loglevel=info
    environment:
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/ley21719_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    networks:
      - ley21719_network

  frontend:
    build: ./frontend
    command: nginx -g "daemon off;"
    ports:
      - "80:80"
    depends_on:
      - backend
    networks:
      - ley21719_network

volumes:
  postgres_data:

networks:
  ley21719_network:
    driver: bridge
```

### Despliegue con Docker

```bash
# Construir imágenes
docker-compose build

# Iniciar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f backend

# Ejecutar migraciones
docker-compose run backend alembic upgrade head

# Detener
docker-compose down
```

### Despliegue en Kubernetes (Opcional)

Para escalamiento corporativo, se proveen manifiestos YAML en `/k8s/`:

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/postgres-statefulset.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/backend-service.yaml
kubectl apply -f k8s/celery-worker-deployment.yaml
kubectl apply -f k8s/celery-beat-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/ingress.yaml
```

### Variables de Entorno en Producción

**NUNCA** hardcodear secretos. Usar:
- Kubernetes Secrets
- AWS Secrets Manager
- Azure Key Vault
- HashiCorp Vault

Ejemplo con AWS Secrets Manager:
```python
import boto3
import json

client = boto3.client('secretsmanager')
response = client.get_secret_value(SecretId='ley21719/prod')
secrets = json.loads(response['SecretString'])

# Usar secrets['DATABASE_URL'], secrets['ENCRYPTION_KEY'], etc.
```

---

## Monitoreo y Logs

### Logs Estructurados

El sistema genera logs en formato JSON para fácil integración con ELK Stack, Datadog, etc.:

```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "level": "INFO",
  "service": "backend",
  "endpoint": "/api/v1/ciudadano/portabilidad",
  "user_id": "uuid-del-usuario",
  "organization_id": "uuid-org",
  "action": "export_requested",
  "format": "JSON",
  "ip": "200.1.2.3",
  "duration_ms": 1250
}
```

### Logs de Auditoría (Separados)

Todos los accesos a datos personales se registran en `/var/log/ley21719/audit.log`:

```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "tipo_accion": "LECTURA",
  "categoria_dato": "SALUD",
  "usuario_afectado_rut_hash": "sha256...",
  "organizacion_rut": "76.123.456-K",
  "justificacion_legal": "Art. 10 Ley 21.719 - Consentimiento explícito",
  "ip_origen": "200.1.2.3",
  "receipt_hash": "firma_digital_del_acceso"
}
```

### Métricas Clave (Prometheus/Grafana)

Endpoints expuestos para monitoreo:

- `GET /metrics`: Métricas Prometheus
- `GET /health`: Health check
- `GET /ready`: Readiness probe

Métricas importantes:
- `http_requests_total`: Total de requests por endpoint
- `http_request_duration_seconds`: Latencia de requests
- `celery_tasks_total`: Tareas Celery procesadas
- `data_access_total`: Accesos a datos personales (por categoría)
- `arco_requests_total`: Solicitudes ARCO por tipo
- `brechas_total`: Brechas reportadas por estado

### Alertas Recomendadas

Configurar alertas para:

1. **Brechas de seguridad**: Cualquier nuevo registro en `NotificacionBrecha`
2. **Solicitudes ARCO próximas a vencer**: Falta < 48h para deadline legal
3. **Fallos en notificaciones**: Webhooks fallidos > 3 intentos
4. **Accesos anómalos**: Patrón inusual en `LogAccesoDatos`
5. **Cola Celery creciendo**: Tareas pendientes > 1000

---

## Troubleshooting

### Problemas Comunes

**1. Error de conexión a PostgreSQL**
```bash
# Verificar que el servicio esté corriendo
docker-compose ps postgres

# Ver logs
docker-compose logs postgres

# Testear conexión
psql -h localhost -U usuario -d ley21719_db
```

**2. Celery no procesa tareas**
```bash
# Verificar Redis
redis-cli ping  # Debe responder PONG

# Ver workers
celery -A app.celery_app inspect active

# Reiniciar worker
docker-compose restart celery_worker
```

**3. Error de encriptación**
```bash
# Verificar que ENCRYPTION_KEY tenga 32 caracteres
echo -n "$ENCRYPTION_KEY" | wc -c  # Debe ser 32

# Si usa KMS, verificar credenciales
aws kms describe-key --key-id $AWS_KMS_KEY_ID
```

**4. OAuth2 no funciona (ClaveÚnica/SII)**
```bash
# Verificar redirect URIs registrados en el proveedor
# Deben coincidir exactamente con .env

# Testear manualmente con curl
curl -X GET "https://id.claveunica.gob.cl/oauth2/authorize?..."
```

**5. Migraciones fallan**
```bash
# Resetear migraciones (SOLO desarrollo)
alembic downgrade base
alembic upgrade head

# Ver estado actual
alembic current
```

---

## Soporte y Contacto

- **Documentación Legal**: Ver `GUIA_CUMPLIMIENTO_NORMATIVO.md`
- **Guía de Usuario**: Ver `GUIA_USUARIO_CIUDADANO_ORGANIZACION.md`
- **Issues**: Reportar bugs en GitHub Issues
- **Seguridad**: Reportar vulnerabilidades a security@tudominio.cl

---

*Última actualización: Mayo 2025*  
*Versión del sistema: 2.0.0 (Cumplimiento 100% Ley 21.719)*
