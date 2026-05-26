# Guía de Cumplimiento Normativo - Ley 21.719 Chile

**Documento dirigido a**: Abogados, DPOs (Delegados de Protección de Datos), Equipos Legales y de Compliance

**Última actualización**: Mayo 2026  
**Versión**: 2.0.0

---

## 📋 Tabla de Contenidos

1. [Introducción a la Ley 21.719](#introducción-a-la-ley-21719)
2. [Mapeo Artículo por Artículo](#mapeo-artículo-por-artículo)
3. [Derechos ARCO - Guía Completa](#derechos-arco---guía-completa)
4. [Protocolo de Brechas de Seguridad](#protocolo-de-brechas-de-seguridad)
5. [Registro de Actividades de Tratamiento (RAT)](#registro-de-actividades-de-tratamiento-rat)
6. [Evaluación de Impacto (EIPD)](#evaluación-de-impacto-eipd)
7. [Checklist de Cumplimiento](#checklist-de-cumplimiento)
8. [Plantillas y Documentos](#plantillas-y-documentos)

---

## Introducción a la Ley 21.719

### ¿Qué es la Ley 21.719?

La **Ley 21.719** establece el marco normativo para la protección de datos personales en Chile, creando la Agencia de Protección de Datos y estableciendo sanciones para su incumplimiento.

### Fecha de Entrada en Vigor

- **Publicación**: Diciembre 2024
- **Implementación gradual**: 2025-2026
- **Sanciones aplicables**: Diciembre 2026

### Principios Fundamentales

| Principio | Descripción | Cómo lo cumplimos |
|-----------|-------------|-------------------|
| **Licitud** | Tratamiento con base legal válida | Consentimiento registrado + bases legales documentadas |
| **Calidad** | Datos exactos, completos, actualizados | Validaciones automáticas + derechos ARCO |
| **Transparencia** | Información clara al titular | Legal Design + notificaciones automáticas |
| **Minimización** | Solo datos necesarios | Categorías granulares + finalidad específica |
| **Limitación plazo** | Conservación solo mientras sea necesario | Políticas retención + borrado automático |
| **Seguridad** | Protección contra accesos no autorizados | AES-256 + SHA-256 + logging completo |
| **Accountability** | Demostración del cumplimiento | RAT + EIPD + auditoría integrada |

---

## Mapeo Artículo por Artículo

### Artículos Críticos y Su Implementación

#### Art. 6 - Principios de Calidad de Datos

**Requisito Legal**: Los datos deben ser exactos, completos, pertinentes, proporcionados y actualizados.

**Implementación Técnica**:
- ✅ Validaciones de RUT chileno con dígito verificador
- ✅ Control de edad (+16 años o validación de tutor)
- ✅ Campos obligatorios vs opcionales claramente marcados
- ✅ Políticas de retención configurables por categoría

**Endpoints Relacionados**:
- `POST /api/v1/politicas-retencion` - Configurar plazos
- `GET /api/v1/ciudadano/mis-datos` - Ver datos almacenados

---

#### Art. 8 - Datos Sensibles

**Requisito Legal**: Datos sensibles (salud, biometría, orientación sexual, etc.) requieren protección reforzada.

**Implementación Técnica**:
- ✅ Categorías predefinidas: SALUD, BIOMETRIA, ORIENTACION_SEXUAL, RELIGION, etc.
- ✅ Evaluación de Impacto (EIPD) obligatoria para estas categorías
- ✅ Encriptación AES-256 para almacenamiento
- ✅ Hash SHA-256 para indexación sin exponer datos

**Endpoints Relacionados**:
- `POST /api/v1/eipd` - Crear evaluación de impacto
- `GET /api/v1/eipd/{id}` - Consultar dictamen DPO

---

#### Art. 10 - Consentimiento Informado

**Requisito Legal**: El consentimiento debe ser libre, informado, específico, inequívoco y revocable.

**Implementación Técnica**:
- ✅ Proposal JSON con estructura granular por finalidad
- ✅ Legal Design: traducción a lenguaje ciudadano
- ✅ Receipt hash con firma digital como evidencia
- ✅ Revocación en un clic (tan fácil como otorgar)

**Flujo de Consentimiento**:
```
1. Organización propone consentimiento → POST /api/v1/solicitudes-consentimiento
2. Ciudadano visualiza en lenguaje claro → GET /api/v1/consentimientos/{id}
3. Ciudadano acepta/rechaza → PUT /api/v1/consentimientos/{id}/estado
4. Sistema genera receipt hash → Automático
5. Webhook notifica a organización → Automático
```

---

#### Art. 11 - Consentimiento de Menores

**Requisito Legal**: Mayores de 14 y menores de 16 años requieren autorización de quien ejerza la patria potestad.

**Implementación Técnica**:
- ✅ Validación automática de edad (>16 años = autónomo)
- ✅ Flujo de validación de tutor para 14-16 años
- ✅ Upload de documento que acredita patria potestad
- ✅ Consentimiento dual (titular + tutor)

**Endpoints Relacionados**:
- `POST /api/v1/usuarios/validar-tutor` - Validar documentación
- `GET /api/v1/usuarios/{id}/tutores` - Listar tutores autorizados

---

#### Art. 12-17 - Derechos ARCO

**Requisito Legal**: Los titulares pueden solicitar Acceso, Rectificación, Cancelación y Oposición.

**Implementación Técnica**:
- ✅ Portal ciudadano para ejercer derechos
- ✅ Plazos automáticos de respuesta (10 días hábiles)
- ✅ Certificados generados automáticamente
- ✅ Trazabilidad completa del proceso

**Ver sección completa**: [Derechos ARCO - Guía Completa](#derechos-arco---guía-completa)

---

#### Art. 18 - Portabilidad de Datos

**Requisito Legal**: Derecho a recibir los datos en formato estructurado y transferirlos a otro responsable.

**Implementación Técnica**:
- ✅ Exportación multi-formato: JSON, XML, CSV
- ✅ Token seguro de un solo uso para transferencia
- ✅ Empaquetado completo de todos los datos del titular
- ✅ Notificación automática a organización destino

**Endpoints Relacionados**:
- `POST /api/v1/ciudadano/portabilidad/solicitar` - Iniciar proceso
- `GET /api/v1/ciudadano/portabilidad/{token}/descargar` - Descargar paquete

---

#### Art. 19-20 - Encargados de Tratamiento

**Requisito Legal**: Si se contratan terceros para procesar datos, debe existir contrato de encargo registrado.

**Implementación Técnica**:
- ✅ Registro de encargados con detalles del contrato
- ✅ Auditoría de medidas de seguridad del encargado
- ✅ Control de subcontrataciones autorizadas
- ✅ Vigencia de contratos con alertas automáticas

**Endpoints Relacionados**:
- `POST /api/v1/encargados` - Registrar nuevo encargado
- `GET /api/v1/encargados/{id}/auditoria` - Ver última auditoría

---

#### Art. 21 - Decisiones Automatizadas

**Requisito Legal**: Los titulares pueden impugnar decisiones basadas únicamente en tratamiento automatizado.

**Implementación Técnica**:
- ✅ Registro de algoritmos utilizados (AI Flag)
- ✅ Derecho a intervención humana solicitado
- ✅ Explicación de lógica aplicada
- ✅ Formulario de impugnación integrado

**Endpoints Relacionados**:
- `POST /api/v1/ciudadano/oposicion-ia` - Impugnar decisión
- `GET /api/v1/decisiones-automatizadas/{id}` - Ver detalles algoritmo

---

#### Art. 22 - Registro de Actividades de Tratamiento (RAT)

**Requisito Legal**: Todo responsable debe mantener un registro de sus actividades de tratamiento.

**Implementación Técnica**:
- ✅ RAT digital con todos los campos requeridos por ley
- ✅ Actualización automática desde consentimientos
- ✅ Reporte exportable para presentar a la Agencia
- ✅ Historial de cambios auditado

**Ver sección completa**: [Registro de Actividades de Tratamiento (RAT)](#registro-de-actividades-de-tratamiento-rat)

---

#### Art. 23 - Evaluación de Impacto (EIPD)

**Requisito Legal**: Tratamientos de alto riesgo requieren evaluación previa de impacto.

**Implementación Técnica**:
- ✅ Wizard guiado para completar EIPD
- ✅ Cuestionario de riesgos estandarizado
- ✅ Dictamen obligatorio del DPO
- ✅ Medidas de mitigación registradas

**Ver sección completa**: [Evaluación de Impacto (EIPD)](#evaluación-de-impacto-eipd)

---

#### Art. 24-27 - Notificación de Brechas

**Requisito Legal**: Las brechas de seguridad deben notificarse en 72 horas a la Agencia y afectados.

**Implementación Técnica**:
- ✅ Detección automática desde logs de acceso
- ✅ Generación de reporte forense
- ✅ Notificación simultánea a Agencia y titulares
- ✅ Plantillas pre-aprobadas para comunicación

**Ver sección completa**: [Protocolo de Brechas de Seguridad](#protocolo-de-brechas-de-seguridad)

---

#### Art. 28-30 - Transferencias Internacionales

**Requisito Legal**: Transferencias fuera de Chile requieren garantías adecuadas.

**Implementación Técnica**:
- ✅ Registro de país destinatario
- ✅ Documentación de garantías (cláusulas tipo, BCR)
- ✅ Excepciones aplicables justificadas
- ✅ Auditoría de nivel de protección del país

**Endpoints Relacionados**:
- `POST /api/v1/transferencias` - Registrar transferencia
- `GET /api/v1/transferencias/paises` - Listar países autorizados

---

## Derechos ARCO - Guía Completa

### ¿Qué son los Derechos ARCO?

ARCO son las siglas de **Acceso, Rectificación, Cancelación y Oposición**, derechos fundamentales de los titulares de datos personales.

### Ejercicio de Derechos - Paso a Paso

#### 1. Derecho de Acceso

**¿Qué permite?**: Conocer qué datos están siendo tratados, con qué finalidad y por cuánto tiempo.

**Cómo ejercerlo**:

**Para el Ciudadano**:
1. Ingresar al portal con ClaveÚnica
2. Navegar a "Mis Datos"
3. Visualizar timeline de accesos
4. Descargar reporte completo

**Para la Organización**:
1. Recibir solicitud vía endpoint `POST /api/v1/solicitudes-arco`
2. Tipo: `ACCESO`
3. Sistema notifica al DPO automáticamente
4. Responder dentro de 10 días hábiles

**Endpoint**:
```http
POST /api/v1/solicitudes-arco
Content-Type: application/json

{
  "rutCiudadanoHash": "abc123...",
  "tipo": "ACCESO",
  "descripcion": "Solicito conocer todos mis datos almacenados",
  "tokenEvidenciaIdentidad": "hash_claveunica_..."
}
```

**Respuesta Esperada**:
```json
{
  "id": "uuid-solicitud",
  "estado": "RECIBIDA",
  "fechaLimiteRespuesta": "2026-06-15T23:59:59",
  "datosEncontrados": {
    "usuario": {...},
    "accesos": [...],
    "logs": [...]
  }
}
```

---

#### 2. Derecho de Rectificación

**¿Qué permite?**: Solicitar la corrección de datos inexactos o incompletos.

**Cómo ejercerlo**:

**Para el Ciudadano**:
1. Identificar dato incorrecto en dashboard
2. Click en "Solicitar Rectificación"
3. Indicar dato correcto y adjuntar evidencia
4. Seguir estado de solicitud

**Para la Organización**:
1. Recibir solicitud con tipo `RECTIFICACION`
2. Validar evidencia adjunta
3. Aprobar rechazar con justificación
4. Notificar cambio a todos los sistemas involucrados

**Endpoint**:
```http
POST /api/v1/solicitudes-arco
{
  "tipo": "RECTIFICACION",
  "campoAfectado": "telefono",
  "valorActual": "+56912345678",
  "valorSolicitado": "+56987654321",
  "evidenciaAdjunta": "documento_hash_..."
}
```

---

#### 3. Derecho de Cancelación (Supresión)

**¿Qué permite?**: Solicitar la eliminación de datos cuando ya no sean necesarios o se retire el consentimiento.

**Cómo ejercerlo**:

**Para el Ciudadano**:
1. Ir a "Derecho al Olvido"
2. Seleccionar datos a eliminar
3. Confirmar con ClaveÚnica
4. Descargar certificado de eliminación

**Para la Organización**:
1. Recibir solicitud tipo `CANCELACION`
2. Verificar si existen obligaciones legales de conservación
3. Ejecutar borrado lógico (encriptación + marca de tiempo)
4. Conservar solo hashes para auditoría
5. Generar certificado automático

**Endpoint**:
```http
POST /api/v1/ciudadano/supresion
{
  "categorias": ["SALUD", "BIOMETRIA"],
  "motivacion": "Retiro de consentimiento",
  "certificadoRequerido": true
}
```

**Certificado de Eliminación**:
El sistema genera automáticamente un PDF con:
- Identificación del titular
- Lista de datos eliminados
- Fecha y hora de eliminación
- Hash de evidencia para verificación futura
- Firma digital del DPO

---

#### 4. Derecho de Oposición

**¿Qué permite?**: Oponeerse al tratamiento de datos para fines específicos (ej. marketing).

**Cómo ejercerlo**:

**Para el Ciudadano**:
1. Ir a "Mis Consentimientos"
2. Identificar tratamiento al que se opone
3. Click en "Oponerse"
4. Indicar motivación (opcional)

**Para la Organización**:
1. Recibir solicitud tipo `OPOSICION`
2. Evaluar si existe base legal alternativa
3. Si rechaza oposición, justificar por escrito
4. Si acepta, bloquear tratamiento inmediatamente

**Endpoint**:
```http
POST /api/v1/solicitudes-arco
{
  "tipo": "OPOSICION",
  "finalidadAfectada": "MARKETING_DIRECTO",
  "motivacion": "No deseo recibir publicidad"
}
```

---

#### 5. Derecho a la Limitación del Tratamiento

**¿Qué permite?**: Congelar temporalmente el tratamiento mientras se resuelve una controversia.

**Casos de Aplicación**:
- Titular impugna exactitud de datos (mientras se verifica)
- Tratamiento es ilícito pero titular se opone a eliminación
- Organización necesita datos para defensa de reclamaciones

**Endpoint**:
```http
POST /api/v1/ciudadano/limitar-tratamiento
{
  "motivacion": "Impugnación de exactitud",
  "duracionEstimada": "30 dias",
  "datosAfectados": ["ingresos", "profesion"]
}
```

---

#### 6. Derecho a la Portabilidad

**¿Qué permite?**: Recibir datos en formato estructurado para transferirlos a otro responsable.

**Formatos Soportados**:
- ✅ JSON (estructurado, machine-readable)
- ✅ XML (estándar interoperable)
- ✅ CSV (compatible con hojas de cálculo)

**Proceso Completo**:

**Paso 1 - Solicitud**:
```http
POST /api/v1/ciudadano/portabilidad/solicitar
{
  "organizacionDestino": "rut-empresa-destino",
  "formatoPreferido": "JSON",
  "categoriasIncluir": ["TODAS"]
}
```

**Paso 2 - Generación de Token**:
El sistema responde con:
```json
{
  "token": "port_abc123xyz789",
  "fechaExpiracion": "2026-06-01T23:59:59",
  "urlDescarga": "/api/v1/ciudadano/portabilidad/port_abc123xyz789/descargar"
}
```

**Paso 3 - Descarga**:
```http
GET /api/v1/ciudadano/portabilidad/{token}/descargar
Accept: application/json

# Retorna archivo ZIP con:
# - datos.json
# - metadata.json
# - README.txt (explicación de campos)
```

**Paso 4 - Transferencia**:
El ciudadano entrega el token a la organización destino, que importa los datos mediante:
```http
POST /api/v1/portabilidad/importar
{
  "tokenOrigen": "port_abc123xyz789",
  "consentimientoNuevo": true
}
```

---

## Protocolo de Brechas de Seguridad

### ¿Qué es una Brecha de Seguridad?

Cualquier incidente que comprometa la **confidencialidad, integridad o disponibilidad** de datos personales.

### Tipos de Brechas

| Tipo | Ejemplo | Nivel de Riesgo |
|------|---------|-----------------|
| **Confidencialidad** | Acceso no autorizado, phishing, ransomware | Alto |
| **Integridad** | Modificación no autorizada de datos | Medio-Alto |
| **Disponibilidad** | Pérdida de datos, ataque DDoS | Variable |

### Plazos Críticos

```
┌─────────────────────────────────────────────────────────┐
│  DETECCIÓN DE BRECHA (T0)                               │
│         ↓                                               │
│   Evaluación inicial (inmediato)                        │
│         ↓                                               │
│   Notificación a DPO (< 24 horas)                       │
│         ↓                                               │
│   Notificación a Agencia (< 72 horas) ⚠️ CRÍTICO        │
│         ↓                                               │
│   Notificación a afectados (sin plazo fijo, ASAP)       │
│         ↓                                               │
│   Informe final (< 30 días)                             │
└─────────────────────────────────────────────────────────┘
```

### Proceso de Notificación - Paso a Paso

#### Paso 1: Detección y Clasificación

**Automático**: El sistema detecta anomalías en logs:
- Múltiples accesos fallidos
- Acceso desde IP sospechosa
- Volumen inusual de consultas
- Acceso a datos sensibles sin justificación

**Endpoint de Reporte**:
```http
POST /api/v1/brechas
{
  "tipoBrecha": "CONFIDENCIALIDAD",
  "descripcion": "Acceso no autorizado a base de datos de usuarios",
  "categoriaDatosAfectados": ["SALUD", "IDENTIFICACION"],
  "numeroAproximadoAfectados": 1500,
  "medidasContencionInmediatas": [
    "Bloqueo de IPs sospechosas",
    "Rotación de credenciales",
    "Activación de modo auditoría reforzada"
  ]
}
```

#### Paso 2: Evaluación de Riesgo

El sistema calcula automáticamente el nivel de riesgo basado en:
- Tipo de datos comprometidos (sensibles = mayor riesgo)
- Número de afectados
- Facilidad de identificación de titulares
- Posibles consecuencias (discriminación, fraude, etc.)

**Resultado**: Riesgo BAJO, MEDIO, ALTO o MUY ALTO

#### Paso 3: Notificación a la Agencia

**Obligatorio si**: Riesgo MEDIO o superior

**Contenido Mínimo**:
```http
POST /api/v1/brechas/{id}/notificar-agencia
{
  "naturalezaBrecha": "Descripción clara y completa",
  "categoriasTitulares": "Clientes, empleados, proveedores",
  "numeroAfectados": 1500,
  "nombreDPO": "Juan Pérez",
  "emailDPO": "dpo@empresa.cl",
  "telefonoDPO": "+56 2 2345 6789",
  "consecuenciasProbables": [
    "Posible suplantación de identidad",
    "Acceso a información médica sensible"
  ],
  "medidasPropuestas": [
    "Refuerzo de controles de acceso",
    "Monitoreo reforzado por 90 días",
    "Capacitación urgente a personal"
  ]
}
```

#### Paso 4: Notificación a Afectados

**Obligatorio si**: Riesgo ALTO o MUY ALTO

**Medios Válidos**:
- Email certificado
- Carta certificada
- Notificación push en app (si existe)
- Publicación en web (si no hay contacto directo)

**Contenido Claro**:
```
ASUNTO: Importante - Incidente de seguridad de datos

Estimado/a [Nombre]:

Le informamos que ha ocurrido un incidente de seguridad que podría 
afectar sus datos personales almacenados en nuestro sistema.

¿QUÉ OCURRIÓ?
[Descripción en lenguaje ciudadano, sin tecnicismos]

¿QUÉ DATOS SE VIERON AFECTADOS?
- Nombre completo
- RUT
- Información de salud (diagnósticos, tratamientos)

¿QUÉ RIESGOS ENFRENTA?
- Posible intento de suplantación de identidad
- Acceso no autorizado a información médica

¿QUÉ HEMOS HECHO?
- Bloqueamos el acceso no autorizado
- Reforzamos nuestros sistemas de seguridad
- Notificamos a la Agencia de Protección de Datos

¿QUÉ PUEDE HACER USTED?
- Monitorear sus cuentas bancarias
- Cambiar contraseñas en otros servicios
- Estar atento a comunicaciones sospechosas

Para más información: dpo@empresa.cl o +56 2 2345 6789

Atentamente,
Equipo de Protección de Datos
```

#### Paso 5: Informe Final

Dentro de 30 días, generar informe completo con:
- Causa raíz del incidente
- Lecciones aprendidas
- Mejoras implementadas
- Plan de prevención futuro

**Endpoint**:
```http
GET /api/v1/brechas/{id}/informe-final
```

---

## Registro de Actividades de Tratamiento (RAT)

### ¿Qué es el RAT?

El **Registro de Actividades de Tratamiento** es un documento obligatorio (Art. 27) donde el responsable detalla TODOS sus tratamientos de datos personales.

### Contenido Mínimo del RAT

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| **Nombre del tratamiento** | Identificación clara | "Gestión de clientes" |
| **Finalidad** | Para qué se usan los datos | "Facturación y cobranza" |
| **Categorías de titulares** | Quiénes son los dueños de los datos | "Clientes, prospectos" |
| **Categorías de datos** | Qué tipos de datos se tratan | "Identificación, contacto, financieros" |
| **Plazo de conservación** | Cuánto tiempo se guardan | "5 años desde término de relación" |
| **Medidas de seguridad** | Cómo se protegen | "AES-256, control de acceso, logging" |
| **Transferencias** | Si se comparten con terceros | "Empresas de cobranza externa" |

### Cómo Gestionar el RAT en el Sistema

#### Crear Nueva Actividad

```http
POST /api/v1/rat
{
  "nombreTratamiento": "Gestión de Recursos Humanos",
  "finalidad": "Administración de personal, nómina, beneficios",
  "categoriasTitulares": ["EMPLEADOS", "EX_EMPLEADOS"],
  "categoriasDatos": ["IDENTIFICACION", "LABORALES", "PREVISIONALES", "SALUD"],
  "baseLegal": "CONTRATO_TRABAJO",
  "plazoConservacion": "10 años desde término de contrato",
  "medidasSeguridad": [
    "Encriptación AES-256",
    "Control de acceso por roles",
    "Backup diario encriptado"
  ],
  "transferenciasInternacionales": [],
  "encargadosTratamiento": ["Empresa_Nominas_SpA"]
}
```

#### Consultar RAT Completo

```http
GET /api/v1/rat/reporte
Accept: application/pdf

# Retorna PDF listo para presentar a la Agencia
```

#### Actualizar RAT

El RAT debe actualizarse ANTES de iniciar cualquier nuevo tratamiento:

```http
PUT /api/v1/rat/{id}
{
  "categoriasDatos": ["IDENTIFICACION", "LABORALES", "PREVISIONALES", "SALUD", "BIOMETRIA"],
  // Agregar biometría requiere nueva EIPD
}
```

### Relación RAT - EIPD

Si el RAT incluye datos sensibles o tratamientos de alto riesgo, el sistema obliga automáticamente a crear una EIPD:

```
Crear RAT
   ↓
¿Incluye datos sensibles o alto riesgo?
   ↓ SÍ
Crear EIPD (obligatorio antes de activar)
   ↓
Dictamen DPO
   ↓
RAT activo
```

---

## Evaluación de Impacto (EIPD)

### ¿Cuándo es Obligatoria la EIPD?

Según el Art. 34, la EIPD es obligatoria para:

1. ✅ Datos sensibles (salud, biometría, orientación sexual, religión, etc.)
2. ✅ Vigilancia sistemática a gran escala (CCTV, geolocalización)
3. ✅ Nuevas tecnologías (IA, machine learning, blockchain)
4. ✅ Decisiones automatizadas con efectos jurídicos
5. ✅ Combinación de bases de datos a gran escala
6. ✅ Datos de niños y adolescentes

### Proceso de EIPD en el Sistema

#### Fase 1: Descripción del Tratamiento

**Wizard Guiado**:

```http
POST /api/v1/eipd
{
  "nombreEvaluacion": "Sistema de Reconocimiento Facial - Acceso Oficinas",
  "descripcionTratamiento": "Captura de rostro para control de acceso",
  "datosSensiblesInvolucrados": ["BIOMETRIA"],
  "tecnologiaUtilizada": "Reconocimiento facial con IA",
  "volumenEstimado": "500 registros diarios",
  "periodoConservacion": "30 días desde captura"
}
```

#### Fase 2: Evaluación de Necesidad y Proporcionalidad

**Cuestionario Automático**:

El sistema presenta preguntas estandarizadas:

1. ¿Es estrictamente necesario tratar datos biométricos?
2. ¿Existen medios menos invasivos para lograr el mismo fin?
3. ¿El volumen de datos es proporcional a la finalidad?
4. ¿Se ha considerado el impacto en grupos vulnerables?

**Respuestas registradas con justificación**.

#### Fase 3: Evaluación de Riesgos

**Matriz de Riesgos**:

| Riesgo | Probabilidad | Impacto | Nivel |
|--------|--------------|---------|-------|
| Falso positivo (denegar acceso legítimo) | Media | Bajo | MEDIO |
| Falso negativo (permitir acceso no autorizado) | Baja | Alto | ALTO |
| Filtración de datos biométricos | Baja | Muy Alto | MUY ALTO |
| Discriminación por características faciales | Media | Alto | ALTO |

#### Fase 4: Medidas de Mitigación

Para cada riesgo identificado, registrar medidas:

```json
{
  "riesgo": "Filtración de datos biométricos",
  "medidas": [
    "Encriptación AES-256 en reposo y tránsito",
    "Almacenamiento separado de plantillas faciales",
    "Borrado automático a los 30 días",
    "Acceso solo para 3 personas autorizadas"
  ]
}
```

#### Fase 5: Dictamen del DPO

El DPO revisa la EIPD y emite dictamen:

```http
PUT /api/v1/eipd/{id}/dictamen
{
  "estadoDictamen": "APROBADO",
  "observaciones": "Se aprueba con condición de implementar doble factor de autenticación para administradores",
  "fechaRevision": "2026-06-01",
  "proximaRevision": "2027-06-01"
}
```

**Estados Posibles**:
- `APROBADO` - Puede iniciar tratamiento
- `APROBADO_CON_OBSERVACIONES` - Puede iniciar cumpliendo condiciones
- `RECHAZADO` - No puede iniciar tratamiento

---

## Checklist de Cumplimiento

### Checklist General - Organización

#### Documentación Legal
- [ ] Política de privacidad publicada y accesible
- [ ] Términos y condiciones actualizados
- [ ] Contratos de encargo con terceros firmados
- [ ] Registro de Actividades de Tratamiento (RAT) completo
- [ ] EIPDs aprobadas para tratamientos de alto riesgo

#### Derechos ARCO
- [ ] Canal de recepción de solicitudes habilitado
- [ ] Formatos de solicitud disponibles
- [ ] Procedimiento interno de respuesta documentado
- [ ] Registro de solicitudes y respuestas mantenido
- [ ] Plazos de respuesta monitoreados (alertas)

#### Seguridad Técnica
- [ ] Encriptación de datos sensibles (AES-256)
- [ ] Control de accesos implementado (RBAC)
- [ ] Logging de accesos activado
- [ ] Backups encriptados y probados
- [ ] Plan de respuesta a incidentes documentado

#### Capacitación
- [ ] Personal capacitado en protección de datos
- [ ] DPO designado y contactable
- [ ] Simulacro de brecha realizado anualmente

#### Auditoría
- [ ] Auditoría interna anual programada
- [ ] Métricas de cumplimiento monitoreadas
- [ ] Mejoras continuas documentadas

---

### Checklist por Proyecto

Antes de lanzar cualquier proyecto que involucre datos personales:

#### Fase de Diseño
- [ ] Privacidad desde el diseño (Privacy by Design)
- [ ] Minimización de datos aplicada
- [ ] Evaluación de riesgos preliminar

#### Fase de Desarrollo
- [ ] EIPD completada si corresponde
- [ ] Consentimientos diseñados con Legal Design
- [ ] Configuración de privacidad por defecto

#### Fase de Testing
- [ ] Pruebas de seguridad realizadas
- [ ] Vulnerabilidades corregidas
- [ ] Penetration testing aprobado

#### Fase de Lanzamiento
- [ ] RAT actualizado
- [ ] Personal capacitado
- [ ] Monitoreo activado

---

## Plantillas y Documentos

### Plantilla de Contrato de Encargo

Disponible en: `/docs/plantillas/contrato_encargo.md`

### Plantilla de Notificación de Brecha

Disponible en: `/docs/plantillas/notificacion_brecha.md`

### Plantilla de Respuesta a Solicitud ARCO

Disponible en: `/docs/plantillas/respuesta_arco.md`

### Política de Privacidad Tipo

Disponible en: `/docs/plantillas/politica_privacidad.md`

---

## Contacto y Soporte

### DPO de la Organización

Todo ciudadano puede contactar al DPO de una organización a través de:
- Email: `dpo@[organizacion].cl` (obligatorio por ley)
- Formulario web: `[URL]/contacto-dpo`

### Agencia de Protección de Datos

Si la organización no responde en plazo:
- Web: `www.agenciaprotecciondatos.cl`
- Email: `contacto@agenciaprotecciondatos.cl`
- Teléfono: `+56 2 2XXX XXXX`

---

**Fin del Documento**

*Este documento se actualiza automáticamente cuando cambian los requisitos legales o las funcionalidades del sistema.*
