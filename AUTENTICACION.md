# Ley 21.719 - Sistema de Protección de Datos (Chile)

## Integración con ClaveÚnica y SII

Este sistema implementa autenticación oficial para:
- **Usuarios**: ClaveÚnica del Gobierno de Chile
- **Organizaciones**: Clave Tributaria del SII

## Configuración

### Variables de entorno (.env)

```bash
# Base de datos
DATABASE_URL=postgresql://user:password@localhost:5432/ley21719

# Seguridad
SECRET_KEY=tu-secret-key-seguro-min-32-caracteres
ENCRYPTION_KEY=tu-clave-de-encriptacion-32-bytes
JWT_SECRET_KEY=tu-jwt-secret-key-min-32-caracteres

# ClaveÚnica (obtener en https://claveunica.gob.cl)
CLAVEUNICA_CLIENT_ID=tu-client-id
CLAVEUNICA_CLIENT_SECRET=tu-client-secret
CLAVEUNICA_REDIRECT_URI=http://localhost:8000/auth/claveunica/callback
CLAVEUNICA_SCOPE=openid profile rut

# SII Clave Tributaria (obtener en https://www.sii.cl)
SII_CLIENT_ID=tu-client-id
SII_CLIENT_SECRET=tu-client-secret
SII_REDIRECT_URI=http://localhost:8000/auth/sii/callback
SII_USE_SANDBOX=true
SII_CERTIFICATE_PATH=/ruta/al/certificado.pem
SII_PRIVATE_KEY_PATH=/ruta/a/llave-privada.pem
```

## Endpoints de Autenticación

### ClaveÚnica (Usuarios)

#### 1. Iniciar sesión con ClaveÚnica
```http
GET /auth/claveunica/login
```

**Respuesta:**
```json
{
  "authorization_url": "https://claveunica.gov.cl/oauth2/authorize?...",
  "state": "random-state-token",
  "message": "Redirigir usuario a authorization_url"
}
```

**Flujo:**
1. Redirigir usuario a `authorization_url`
2. Usuario se autentica en portal ClaveÚnica
3. ClaveÚnica redirige a `/auth/claveunica/callback?code=XXX&state=YYY`

#### 2. Callback de ClaveÚnica
```http
GET /auth/claveunica/callback?code={code}&state={state}
```

**Respuesta exitosa:**
```json
{
  "id": "uuid-del-usuario",
  "rut_hash": "sha256-hash-del-rut",
  "nombre_completo": "Juan Pérez",
  "email": "juan@example.com",
  "tokens": {
    "access_token": "jwt-access-token",
    "refresh_token": "jwt-refresh-token",
    "token_type": "bearer",
    "expires_in": 1800
  },
  "token_evidence": "hash-del-token-como-evidencia"
}
```

### SII Clave Tributaria (Organizaciones)

#### 1. Iniciar sesión con SII
```http
GET /auth/sii/login?rut_organizacion=76.123.456-K
```

**Respuesta:**
```json
{
  "authorization_url": "https://maui.sii.cl/oauth/authorize?...",
  "state": "random-state-token",
  "rut_organizacion": "76.123.456-K",
  "message": "Redirigir representante legal a authorization_url"
}
```

#### 2. Callback del SII
```http
GET /auth/sii/callback?code={code}&state={state}
```

**Respuesta exitosa:**
```json
{
  "id": "uuid-de-la-organizacion",
  "rut": "76.123.456-K",
  "razon_social": "Empresa SpA",
  "email_dpo": "dpo@empresa.cl",
  "tokens": {
    "access_token": "jwt-access-token",
    "refresh_token": "jwt-refresh-token",
    "token_type": "bearer",
    "expires_in": 1800
  },
  "dte_authorized": true,
  "giro": "Servicios tecnológicos"
}
```

### Gestión de Sesión

#### Refresh Token
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "jwt-refresh-token"
}
```

#### Verificar Token
```http
GET /auth/verify?token={access_token}
# O usar header Authorization: Bearer {token}
```

#### Logout
```http
POST /auth/logout
```

## Ejemplo de Uso con FastAPI

### Frontend - Login con ClaveÚnica

```javascript
// 1. Iniciar flujo de login
async function iniciarLoginClaveUnica() {
  const response = await fetch('/auth/claveunica/login');
  const data = await response.json();
  
  // Redirigir usuario a ClaveÚnica
  window.location.href = data.authorization_url;
}

// 2. Manejar callback (en la página de callback)
async function manejarCallback(code, state) {
  const response = await fetch(`/auth/claveunica/callback?code=${code}&state=${state}`);
  
  if (response.ok) {
    const userData = await response.json();
    
    // Guardar tokens
    localStorage.setItem('access_token', userData.tokens.access_token);
    localStorage.setItem('refresh_token', userData.tokens.refresh_token);
    
    // Redirigir a dashboard
    window.location.href = '/dashboard';
  }
}
```

### Backend - Usar token para acceder a endpoints protegidos

```python
import httpx

access_token = "jwt-access-token-obtenido"

# Crear acceso a datos
response = httpx.post(
    "http://localhost:8000/api/v1/accesos",
    json={
        "usuario_id": "uuid-usuario",
        "organizacion_id": "uuid-organizacion",
        "categoria_dato": "SALUD",
        "finalidad": "Diagnóstico médico"
    },
    headers={
        "Authorization": f"Bearer {access_token}",
        "X-API-Key": "cl_ly_api-key-de-organizacion"
    }
)
```

## Consideraciones de Seguridad

### Evidencia de Autenticación

Cada autenticación genera un `token_evidence` que es el hash SHA-256 del token recibido desde ClaveÚnica/SII. Este hash debe almacenarse como:
- Comprobante de identidad válida
- Evidencia para auditorías de la Agencia de Protección de Datos
- Referencia en solicitudes ARCO

### Protección CSRF

El parámetro `state` se usa para prevenir ataques CSRF:
1. Se genera un token aleatorio antes de redirigir
2. Se valida en el callback que el state coincida
3. Se elimina después de validar

### Tokens JWT

Los tokens internos tienen:
- **Access Token**: 30 minutos de validez
- **Refresh Token**: 7 días de validez
- Algoritmo: HS256
- Claims incluidos: `sub`, `rut_hash`, `auth_provider`, `exp`, `type`

## Endpoints Existentes (API v1)

Además de autenticación, el sistema incluye:

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/v1/usuarios` | POST | Registrar usuario |
| `/api/v1/organizaciones` | POST | Registrar organización |
| `/api/v1/organizaciones/{id}/api-keys` | POST | Crear API Key |
| `/api/v1/accesos` | POST | Otorgar consentimiento |
| `/api/v1/solicitudes-consentimiento` | POST | Solicitar consentimiento |
| `/api/v1/solicitudes-arco` | POST | Crear solicitud ARCO |
| `/api/v1/logs-acceso` | POST | Registrar log de auditoría |

## Documentación Interactiva

Una vez ejecutado el servidor:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Ejecución

```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con credenciales reales

# Ejecutar migraciones (si usa Alembic)
alembic upgrade head

# Iniciar servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Notas Importantes

1. **Producción**: Cambiar todas las URLs de sandbox a producción
2. **Certificados SII**: Requiere certificado digital válido para producción
3. **Secretos**: Nunca commitear el archivo `.env` al repositorio
4. **HTTPS**: En producción, todos los endpoints deben usar HTTPS
5. **Logs**: Implementar logging de auditoría para todos los accesos
