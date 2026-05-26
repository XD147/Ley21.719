# Ley 21.719 - Sistema de Protección de Datos (Chile)

## Estructura del Proyecto

```
app/
├── __init__.py
├── main.py              # Aplicación FastAPI principal
├── config.py            # Configuración y variables de entorno
├── database.py          # Conexión a base de datos SQLAlchemy
├── models/
│   ├── __init__.py
│   └── models.py        # Modelos SQLAlchemy (Usuario, Organizacion, etc.)
├── schemas/
│   ├── __init__.py
│   └── schemas.py       # Esquemas Pydantic para validación
├── services/
│   ├── __init__.py
│   └── services.py      # Lógica de negocio
├── api/
│   ├── __init__.py
│   └── routes.py        # Endpoints REST API
└── utils/
    ├── __init__.py
    ├── security.py      # Encriptación, hashing (SHA-256, AES-256)
    └── validators.py    # Validaciones (RUT, edad, etc.)
```

## Instalación

```bash
pip install -r requirements.txt
```

## Configuración

Crear archivo `.env` en la raíz del proyecto:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/ley21719
SECRET_KEY=tu_clave_secreta_muy_segura
ENCRYPTION_KEY=tu_clave_de_encriptacion_32_bytes_aqui
```

## Ejecución

```bash
# Desarrollo
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Producción
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Documentación API

Una vez ejecutando, acceder a:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Endpoints Principales

### Usuarios
- `POST /api/v1/usuarios` - Registrar nuevo usuario
- `GET /api/v1/usuarios/{id}` - Obtener usuario
- `PUT /api/v1/usuarios/{id}` - Actualizar usuario

### Organizaciones
- `POST /api/v1/organizaciones` - Registrar organización
- `POST /api/v1/organizaciones/{id}/api-keys` - Crear API Key

### Accesos/Consentimientos
- `POST /api/v1/accesos` - Otorgar acceso
- `GET /api/v1/usuarios/{id}/accesos` - Listar accesos
- `POST /api/v1/accesos/{id}/revoke` - Revocar acceso

### Solicitudes ARCO
- `POST /api/v1/solicitudes-arco` - Crear solicitud ARCO
- `POST /api/v1/solicitudes-arco/{id}/process` - Procesar solicitud

### Auditoría
- `POST /api/v1/logs-acceso` - Registrar acceso
- `GET /api/v1/logs-acceso` - Consultar logs

## Características de Seguridad

### RUT (Rol Único Tributario)
- **Hash SHA-256**: Para indexación y búsqueda (campo `rut_hash`)
- **Encriptado AES-256**: Para almacenamiento seguro (campo `rut_encriptado`)
- Nunca se almacena el RUT en texto plano

### API Keys
- Formato: `cl_ly_[unique_id]`
- Hash SHA-256 almacenado en BD
- La key completa solo se muestra una vez al crear
- Soporte para expiración y revocación

### Consentimientos
- Receipt hash con firma digital
- Categorías granulares de datos (SALUD, BIOMETRIA, etc.)
- Finalidad específica requerida
- Estados: ACTIVO, REVOCADO, EXPIRADO

### Auditoría (Accountability)
- Log obligatorio de todos los accesos
- Justificación legal requerida
- IP de origen y user agent
- Reportes de auditoría por período

## Modelo de Datos

El sistema implementa el siguiente diagrama entidad-relación:

```
Usuario      ||--o{ AccesoOrganizacion       : "otorga"
Usuario      ||--o{ LogAccesoDatos           : "genera"
Organizacion ||--o{ OrganizacionApiKey       : "posee"
Organizacion ||--o{ AccesoOrganizacion       : "recibe"
Organizacion ||--o{ SolicitudArco            : "gestiona"
Organizacion ||--o{ SolicitudConsentimiento  : "propone"
Organizacion ||--o{ LogAccesoDatos           : "audita"
```

## Requisitos Ley 21.719

Este sistema cumple con los siguientes aspectos de la ley:

1. **Consentimiento informado**: Registro granular de permisos
2. **Derechos ARCO**: Implementación completa de solicitudes
3. **Portabilidad**: Soporte para transferencia entre organizaciones
4. **Accountability**: Logging completo de accesos
5. **Seguridad**: Encriptación de datos sensibles
6. **Minimización**: Solo datos necesarios por finalidad
7. **Plazos**: Control de fechas límite para respuestas ARCO

## Tests

```bash
pytest tests/ -v
```

## Migraciones

Usando Alembic:

```bash
alembic init migrations
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

## Licencia

MIT License
