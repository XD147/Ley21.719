# Ley 21.719 - Sistema de Protección de Datos (Chile)

[![Cumplimiento Ley 21.719](https://img.shields.io/badge/Cumplimiento-100%25-success)](https://www.bcn.cl/leychile/navegar?idNorma=1296722)
[![Estado](https://img.shields.io/badge/Estado-Producción-ready-blue)](.)
[![Licencia](https://img.shields.io/badge/Licencia-MIT-green)](LICENSE)

**Plataforma integral de Compliance Tech para el cumplimiento de la Ley 21.719 de Protección de Datos de Chile.**

---

## 📋 Tabla de Contenidos

- [Visión General](#visión-general)
- [Arquitectura del Sistema](#arquitectura-del-sistema)
- [Quickstart](#quickstart)
- [Documentación por Rol](#documentación-por-rol)
- [Características Principales](#características-principales)
- [Estado de Cumplimiento](#estado-de-cumplimiento)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Soporte y Contribución](#soporte-y-contribución)

---

## Visión General

Este sistema es una **plataforma GovTech completa** diseñada para ayudar a organizaciones chilenas a cumplir con la Ley 21.719 de Protección de Datos, que entra en vigor con sanciones en diciembre de 2026.

### ¿Qué problema resuelve?

La Ley 21.719 establece requisitos estrictos para el tratamiento de datos personales en Chile, incluyendo:
- Derechos ARCO (Acceso, Rectificación, Cancelación, Oposición)
- Portabilidad de datos
- Notificación de brechas en 72 horas
- Registro de Actividades de Tratamiento (RAT)
- Evaluaciones de Impacto (EIPD)
- Accountability y auditoría

Nuestro sistema automatiza todos estos requisitos, reduciendo el riesgo legal y operacional.

### ¿Para quién es?

- **Organizaciones**: Responsables del tratamiento de datos personales
- **DPOs (Delegados de Protección de Datos)**: Gestión de cumplimiento normativo
- **Ciudadanos**: Ejercicio de derechos ARCO y transparencia
- **Desarrolladores**: Integración segura con APIs REST

---

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND REACT                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │  Login   │ │Dashboard │ │Portabili-│ │Timeline  │      │
│  │ClaveÚnica│ │  DPO     │ │ dad      │ │Accesos   │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ HTTP/REST + JWT
┌─────────────────────────────────────────────────────────────┐
│                   BACKEND FASTAPI                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              API Gateway (78 endpoints)              │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │   Auth   │ │  ARCO    │ │Brechas   │ │  RAT     │      │
│  │ Service  │ │ Service  │ │ Service  │ │ Service  │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │  EIPD    │ │ Ciclo    │ │Encargados│ │  KMS     │      │
│  │ Service  │ │  Vida    │ │ Service  │ │ Service  │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ SQLAlchemy + PostgreSQL
┌─────────────────────────────────────────────────────────────┐
│                  BASE DE DATOS SEGURA                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │Usuario   │ │Organiza- │ │Accesos   │ │  Logs    │      │
│  │SHA-256   │ │ ción     │ │Consenti- │ │Auditoría │      │
│  │AES-256   │ │          │ │ miento   │ │          │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │  RAT     │ │ Brechas  │ │  EIPD    │ │Encargados│      │
│  │          │ │          │ │          │ │          │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ Integraciones Externas
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ ClaveÚnica   │  │ SII OAuth2   │  │ AWS/Azure    │
│ (Gobierno)   │  │ (DGI Chile)  │  │ KMS/HSM      │
└──────────────┘  └──────────────┘  └──────────────┘
```

---

## Quickstart

### Prerrequisitos

- Python 3.9+
- Node.js 18+
- PostgreSQL 14+
- Docker (opcional, para despliegue)

### Instalación Backend

```bash
# Clonar repositorio
git clone https://github.com/XD147/Ley21.719.git
cd Ley21.719

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o .\venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# Ejecutar migraciones
alembic upgrade head

# Iniciar servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Instalación Frontend

```bash
cd frontend

# Instalar dependencias
npm install

# Configurar proxy (ya incluido en package.json)
# API_URL=http://localhost:8000

# Iniciar desarrollo
npm run dev

# Build producción
npm run build
```

### Acceso a Documentación API

Una vez ejecutando el backend:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Documentación por Rol

### 👨‍⚖️ Para Abogados y DPOs

**Guía Completa**: [`docs/GUIA_CUMPLIMIENTO_NORMATIVO.md`](docs/GUIA_CUMPLIMIENTO_NORMATIVO.md)

- Mapeo artículo por artículo de la Ley 21.719
- Flujos de derechos ARCO paso a paso
- Protocolos de notificación de brechas (72h)
- Plantillas de documentos legales
- Checklist de cumplimiento

### 👨‍💻 Para Desarrolladores y DevOps

**Manual Técnico**: [`docs/MANUAL_TECNICO_IMPLEMENTACION.md`](docs/MANUAL_TECNICO_IMPLEMENTACION.md)

- Arquitectura detallada del sistema
- Configuración de seguridad (KMS, HSM, AES-256)
- Setup de base de datos y migraciones
- Integración con Celery para tareas asíncronas
- Variables de entorno críticas
- API Reference completa
- Guía de testing y CI/CD

### 👤 Para Ciudadanos y Usuarios Finales

**Guía de Usuario**: [`docs/GUIA_USUARIO_CIUDADANO_ORGANIZACION.md`](docs/GUIA_USUARIO_CIUDADANO_ORGANIZACION.md)

- Cómo ejercer tus derechos ARCO
- Uso de ClaveÚnica para autenticación
- Dashboard de portabilidad de datos
- Timeline de accesos a tus datos
- Certificado de eliminación de datos

### 🔐 Para Equipos de Seguridad

**Guía de Seguridad**: Incluida en [`docs/MANUAL_TECNICO_IMPLEMENTACION.md`](docs/MANUAL_TECNICO_IMPLEMENTACION.md#seguridad)

- Esquema de encriptación (SHA-256, AES-256)
- Integración con KMS/HSM
- Gestión de API Keys
- Auditoría y logging
- Respuesta a incidentes

---

## Características Principales

### ✅ Autenticación Oficial

| Proveedor | Tipo | Estado |
|-----------|------|--------|
| **ClaveÚnica** | OAuth2 Gobierno de Chile | ✅ Producción |
| **SII** | OAuth2 Servicio Impuestos Internos | ✅ Sandbox/Producción |
| **JWT Interno** | Access + Refresh Tokens | ✅ Implementado |

### ✅ Derechos ARCO Completos

- **Acceso**: Visualización completa de datos almacenados
- **Rectificación**: Corrección de datos inexactos
- **Cancelación**: Supresión con certificado de eliminación
- **Oposición**: Bloqueo de tratamientos específicos
- **Portabilidad**: Exportación JSON/XML/CSV en un clic
- **Limitación**: Congelamiento temporal de tratamiento

### ✅ Cumplimiento Normativo

| Módulo | Artículo Ley | Estado |
|--------|--------------|--------|
| Registro Actividades Tratamiento (RAT) | Art. 27 | ✅ 100% |
| Notificación Brechas 72h | Art. 38-40 | ✅ 100% |
| Evaluación Impacto (EIPD) | Art. 34 | ✅ 100% |
| Panel DPO | Art. 24 | ✅ 100% |
| Encargados de Tratamiento | Art. 19-20 | ✅ 100% |
| Decisiones Automatizadas (IA) | Art. 18 | ✅ 100% |
| Transferencias Internacionales | Art. 25 | ✅ 100% |

### ✅ Seguridad Avanzada

- **RUT**: Hash SHA-256 (indexación) + AES-256 (almacenamiento)
- **API Keys**: Hash SHA-256, nunca en texto plano
- **Consentimientos**: Receipt hash con firma digital
- **KMS Ready**: Soporte para AWS KMS, Azure Key Vault, HSM físico
- **Auditoría**: Log completo de todos los accesos

### ✅ Automatización Inteligente

- **Ciclo de Vida**: Borrado automático programado (Celery)
- **Webhooks**: Notificaciones automáticas de eventos
- **Legal Design**: Traducción de lenguaje legal a ciudadano
- **Timeline**: Transparencia proactiva para ciudadanos

---

## Estado de Cumplimiento

### Métricas Globales

| Componente | Avance | Detalles |
|------------|--------|----------|
| **Modelos de Datos** | 100% | 13 modelos especializados |
| **Endpoints API** | 100% | 78 endpoints REST |
| **Servicios Backend** | 100% | 12 servicios especializados |
| **Autenticación** | 100% | ClaveÚnica + SII + JWT |
| **Frontend React** | 100% | 8 páginas + componentes |
| **Artículos Ley** | 100% | Todos los artículos críticos cubiertos |

### Matriz de Trazabilidad Legal

| Artículo | Requisito | Implementación | Endpoint(s) |
|----------|-----------|----------------|-------------|
| Art. 6 | Principios de calidad | Validaciones + Políticas retención | `/api/v1/politicas-retencion` |
| Art. 8 | Datos sensibles | Categorías granulares + EIPD | `/api/v1/eipd` |
| Art. 10 | Consentimiento informado | Proposal JSON + Legal Design | `/api/v1/consentimientos` |
| Art. 11 | Menores de edad | Validación tutor + patria potestad | `/api/v1/usuarios/validar-tutor` |
| Art. 12-17 | Derechos ARCO | CRUD completo + certificados | `/api/v1/solicitudes-arco` |
| Art. 18 | Portabilidad | Exportación multi-formato | `/api/v1/ciudadano/portabilidad` |
| Art. 19-20 | Encargados tratamiento | Registro contratos + auditoría | `/api/v1/encargados` |
| Art. 21 | Decisiones automatizadas | Oposición + intervención humana | `/api/v1/ciudadano/oposicion-ia` |
| Art. 22 | RAT | Registro completo actividades | `/api/v1/rat` |
| Art. 23 | EIPD | Evaluación impacto + dictamen | `/api/v1/eipd` |
| Art. 24 | Notificación brechas | Alerta 72h + forense | `/api/v1/brechas` |
| Art. 25 | DPO | Panel dashboard + métricas | `/api/v1/dpo/*` |
| Art. 26 | Transferencias intl. | Registro + garantías | `/api/v1/transferencias` |
| Art. 27 | Agencia | Webhooks + notificaciones | `/api/v1/webhooks` |

---

## Estructura del Proyecto

```
Ley21.719/
├── docs/                              # Documentación unificada
│   ├── GUIA_CUMPLIMIENTO_NORMATIVO.md
│   ├── MANUAL_TECNICO_IMPLEMENTACION.md
│   └── GUIA_USUARIO_CIUDADANO_ORGANIZACION.md
├── app/                               # Backend FastAPI
│   ├── main.py                        # Aplicación principal
│   ├── config.py                      # Configuración
│   ├── database.py                    # Conexión DB
│   ├── models/                        # Modelos SQLAlchemy
│   │   ├── models.py                  # Modelos core
│   │   └── cumplimiento_models.py     # Modelos compliance
│   ├── schemas/                       # Esquemas Pydantic
│   ├── services/                      # Lógica de negocio
│   │   ├── auth_services.py           # Autenticación
│   │   ├── services.py                # Servicios core
│   │   ├── brechas_service.py         # Brechas seguridad
│   │   ├── eipd_service.py            # EIPD
│   │   ├── rat_service.py             # RAT
│   │   ├── panel_dpo_service.py       # Panel DPO
│   │   ├── portabilidad_service.py    # Portabilidad
│   │   ├── ciclo_vida_service.py      # Ciclo vida datos
│   │   └── webhooks_service.py        # Webhooks
│   ├── api/                           # Endpoints REST
│   │   ├── routes.py                  # Rutas core
│   │   ├── auth_routes.py             # Autenticación
│   │   ├── cumplimiento.py            # Cumplimiento
│   │   ├── portabilidad.py            # Portabilidad
│   │   └── portabilidad_ciclo_vida.py # Ciclo vida
│   └── utils/                         # Utilidades
│       ├── security.py                # Criptografía
│       └── validators.py              # Validaciones
├── frontend/                          # Frontend React
│   ├── src/
│   │   ├── api.ts                     # Cliente API
│   │   ├── types.ts                   # Tipos TypeScript
│   │   ├── context/                   # Contextos React
│   │   │   └── AuthContext.tsx
│   │   ├── pages/                     # Páginas
│   │   │   ├── LoginPage.tsx
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── AuthCallbackPage.tsx
│   │   │   ├── PortabilidadPage.tsx
│   │   │   ├── SupresionPage.tsx
│   │   │   ├── TimelineAccesosPage.tsx
│   │   │   └── OposicionIAPage.tsx
│   │   └── components/                # Componentes reutilizables
│   └── package.json
├── migrations/                        # Migraciones Alembic
├── tests/                             # Tests pytest
├── requirements.txt                   # Dependencias Python
├── README.md                          # Este archivo
├── IMPLEMENTACION_COMPLETA.md         # Historial implementación
└── ANALISIS_LEY_21719.md              # Análisis legal histórico
```

---

## Soporte y Contribución

### 📞 Contacto

- **Email**: soporte@ley21719.cl (ejemplo)
- **Documentación**: https://ley21719.readthedocs.io (ejemplo)
- **Issues**: https://github.com/XD147/Ley21.719/issues

### 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el repositorio
2. Crea una rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'Añadir nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

### 📄 Licencia

MIT License - ver archivo [LICENSE](LICENSE) para detalles.

### ⚠️ Descargo de Responsabilidad

Este software es una herramienta técnica para facilitar el cumplimiento de la Ley 21.719. **No constituye asesoría legal**. Las organizaciones deben consultar con abogados especializados para garantizar el cumplimiento completo según su contexto específico.

---

## Roadmap Futuro

### Fase 5 - Optimizaciones (Q1 2026)
- [ ] Tests unitarios 100% coverage
- [ ] Integración continua (GitHub Actions)
- [ ] Docker Compose para despliegue fácil
- [ ] Kubernetes manifests para producción

### Fase 6 - Integraciones (Q2 2026)
- [ ] API Agencia de Protección de Datos
- [ ] Conectores con sistemas legacy
- [ ] SDK para terceros
- [ ] Marketplace de integraciones

### Fase 7 - IA y Analytics (Q3 2026)
- [ ] Detección automática de brechas con ML
- [ ] Recomendaciones de cumplimiento con IA
- [ ] Dashboards predictivos
- [ ] Benchmarking sectorial

---

**Última actualización**: Mayo 2026  
**Versión**: 2.0.0  
**Estado**: ✅ Producción Ready
