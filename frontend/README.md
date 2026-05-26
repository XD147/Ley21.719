# Frontend Ley 21.719 - Protección de Datos

Frontend React para el sistema de gestión de protección de datos según la Ley 21.719 de Chile.

## Características

- **Autenticación con ClaveÚnica**: Login para ciudadanos usando el sistema oficial del Gobierno de Chile
- **Autenticación con SII**: Login para organizaciones usando Clave Tributaria
- **Gestión de Accesos**: Visualiza y revoca accesos otorgados a organizaciones
- **Solicitudes ARCO**: Gestiona solicitudes de Acceso, Rectificación, Cancelación y Oposición
- **Diseño Responsivo**: Interfaz moderna y adaptable a diferentes dispositivos

## Instalación

```bash
cd frontend
npm install
```

## Configuración

El frontend está configurado para conectarse al backend en `http://localhost:8000`. El proxy de Vite redirige automáticamente las peticiones `/api` y `/auth` al backend.

Si necesitas cambiar la URL del backend, edita `vite.config.ts`:

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://tu-backend:8000',
      changeOrigin: true,
    },
    '/auth': {
      target: 'http://tu-backend:8000',
      changeOrigin: true,
    }
  }
}
```

## Desarrollo

```bash
npm run dev
```

El servidor se iniciará en `http://localhost:3000`

## Build de Producción

```bash
npm run build
npm run preview
```

## Estructura de Archivos

```
frontend/
├── src/
│   ├── api.ts              # Cliente API con axios e interceptores
│   ├── types.ts            # Definiciones TypeScript
│   ├── App.tsx             # Componente principal con routing
│   ├── main.tsx            # Punto de entrada
│   ├── index.css           # Estilos globales
│   ├── context/
│   │   └── AuthContext.tsx # Contexto de autenticación
│   ├── pages/
│   │   ├── LoginPage.tsx          # Página de login
│   │   ├── DashboardPage.tsx      # Dashboard principal
│   │   └── AuthCallbackPage.tsx   # Callback OAuth
│   └── components/        # Componentes reutilizables (futuro)
├── index.html
├── package.json
├── tsconfig.json
├── tsconfig.node.json
└── vite.config.ts
```

## Flujo de Autenticación

### Ciudadanos (ClaveÚnica)
1. Usuario selecciona "Soy Ciudadano"
2. Click en "Ingresar con ClaveÚnica"
3. Redirección a `https://accounts.claveunica.gob.cl/oauth2/authorize`
4. Usuario autentica en portal gubernamental
5. Redirección de vuelta a `/auth/callback?code=xxx&state=xxx`
6. Frontend exchange code por tokens JWT
7. Redirección a `/dashboard`

### Organizaciones (SII)
1. Usuario selecciona "Soy Organización"
2. Click en "Ingresar con Clave Tributaria SII"
3. Redirección a OAuth del SII
4. Representante legal autentica
5. Callback con código de autorización
6. Obtención de tokens JWT
7. Acceso al dashboard organizacional

## Endpoints Consumidos

### Autenticación
- `GET /auth/claveunica/login` - Inicia flujo ClaveÚnica
- `POST /auth/claveunica/callback` - Callback OAuth
- `GET /auth/sii/login` - Inicia flujo SII
- `POST /auth/sii/callback` - Callback OAuth
- `POST /auth/refresh` - Refresca access token
- `GET /auth/verify` - Verifica token actual
- `POST /auth/logout` - Cierra sesión

### Usuario
- `GET /usuarios/me` - Obtiene perfil del usuario

### Accesos
- `GET /accesos/mis-accesos` - Lista accesos otorgados
- `PUT /accesos/:id/revocar` - Revoca acceso

### Solicitudes ARCO
- `GET /solicitudes-arco/mis-solicitudes` - Lista solicitudes
- `POST /solicitudes-arco` - Crea nueva solicitud

## Seguridad

- **Tokens JWT**: Access tokens (30 min) + Refresh tokens (7 días)
- **Auto-refresh**: Renovación automática de tokens expirados
- **Protección CSRF**: State parameter en flujos OAuth
- **HTTPS**: Requerido en producción para OAuth

## Dependencias

- React 18.3.1
- React Router DOM 6.26.0
- Axios 1.7.2
- TypeScript 5.5.3
- Vite 5.4.0

## Consideraciones Ley 21.719

Este frontend implementa los requisitos de transparencia y control establecidos en la ley:

1. **Consentimiento Granular**: Los usuarios pueden ver exactamente qué datos han compartido
2. **Revocación Simple**: Un click para revocar cualquier acceso
3. **Ejercicio de Derechos ARCO**: Interfaz intuitiva para solicitar derechos
4. **Transparencia**: Información clara sobre finalidad y categorías de datos
