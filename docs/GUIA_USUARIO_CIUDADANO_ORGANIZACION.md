# Guía de Usuario - Ley 21.719 Chile

## Índice
1. [Introducción](#introducción)
2. [Para Ciudadanos](#para-ciudadanos)
   - [Registro y Login con ClaveÚnica](#registro-y-login-con-claveúnica)
   - [Dashboard Personal](#dashboard-personal)
   - [Ejercer Derecho a la Portabilidad](#ejercer-derecho-a-la-portabilidad)
   - [Derecho al Olvido (Supresión)](#derecho-al-olvido-supresión)
   - [Timeline de Accesos](#timeline-de-accesos)
   - [Oposición a Decisiones Automatizadas](#oposición-a-decisiones-automatizadas)
   - [Solicitudes ARCO](#solicitudes-arco)
3. [Para Organizaciones](#para-organizaciones)
   - [Registro y Login con SII](#registro-y-login-con-sii)
   - [Panel de Administración](#panel-de-administración)
   - [Gestión de Consentimientos](#gestión-de-consentimientos)
   - [RAT - Registro de Actividades](#rat---registro-de-actividades)
   - [Gestión de Brechas](#gestión-de-brechas)
   - [Panel DPO](#panel-dpo)
   - [Encargados de Tratamiento](#encargados-de-tratamiento)
4. [Preguntas Frecuentes](#preguntas-frecuentes)
5. [Glosario Legal](#glosario-legal)

---

## Introducción

La **Ley 21.719** de Protección de Datos Personales de Chile establece nuevos derechos para los ciudadanos y obligaciones para las organizaciones que tratan datos personales. Este sistema permite ejercer esos derechos de forma digital, segura y transparente.

### ¿Qué es esta plataforma?

Es un sistema de cumplimiento normativo (Compliance Tech) que permite:

**Para Ciudadanos:**
- ✅ Controlar quién tiene acceso a tus datos personales
- ✅ Descargar todos tus datos en formato portable (JSON, CSV, XML)
- ✅ Solicitar la eliminación de tus datos (Derecho al Olvido)
- ✅ Ver historial completo de accesos a tu información
- ✅ Impugnar decisiones tomadas por algoritmos/IA
- ✅ Ejercer derechos ARCO (Acceso, Rectificación, Cancelación, Oposición)

**Para Organizaciones:**
- ✅ Gestionar consentimientos de usuarios de forma legal
- ✅ Mantener el Registro de Actividades de Tratamiento (RAT)
- ✅ Reportar y notificar brechas de seguridad en 72 horas
- ✅ Evaluar impacto de tratamientos de datos sensibles (EIPD)
- ✅ Auditar terceros procesadores de datos
- ✅ Automatizar borrado de datos expirados

---

## Para Ciudadanos

### Registro y Login con ClaveÚnica

#### ¿Qué es ClaveÚnica?
ClaveÚnica es el sistema de identificación digital del Gobierno de Chile que te permite acceder a servicios online de forma segura usando tu RUT y una contraseña única.

#### Pasos para registrarte:

1. **Ingresa a la plataforma**
   - Abre tu navegador y ve a `https://tudominio.cl`

2. **Selecciona "Iniciar Sesión"**
   - Haz clic en el botón **"ClaveÚnica"** (azul, con escudo de Chile)

3. **Autenticación en sitio del Registro Civil**
   - Serás redirigido al sitio oficial del Registro Civil
   - Ingresa tu RUT (sin puntos ni guión)
   - Ingresa tu ClaveÚnica
   - Si no tienes ClaveÚnica, haz clic en "Solicitar ClaveÚnica" y sigue las instrucciones

4. **Autorizar compartir datos**
   - La plataforma solicitará permiso para obtener tu nombre, email y RUT verificado
   - Haz clic en **"Autorizar"**

5. **¡Listo!**
   - Serás redirigido a tu dashboard personal
   - Tu cuenta se crea automáticamente con identidad verificada

#### Seguridad:
- ✅ Tu RUT está hasheado con SHA-256 (no se almacena en texto plano)
- ✅ Los datos sensibles están encriptados con AES-256
- ✅ Sesiones expiran después de 30 minutos de inactividad

---

### Dashboard Personal

Al ingresar, verás tu panel de control con:

```
┌─────────────────────────────────────────────────────┐
│  👤 Hola, [Tu Nombre]                                │
│                                                     │
│  📊 Resumen de tu huella digital                    │
│  ┌─────────────┬─────────────┬─────────────┐       │
│  │ Empresas    │ Consentim.  │ Accesos     │       │
│  │ que tienen  │ Activos     │ últimos     │       │
│  │ tus datos   │             │ 30 días     │       │
│  ├─────────────┼─────────────┼─────────────┤       │
│  │     12      │     8       │    45       │       │
│  └─────────────┴─────────────┴─────────────┘       │
│                                                     │
│  ⚡ Accesos Rápidos                                 │
│  [📥 Descargar mis datos] [🗑️ Eliminar cuenta]     │
│  [📅 Ver timeline] [⚖️ Nueva solicitud ARCO]        │
│                                                     │
│  🔔 Notificaciones Recientes                        │
│  • Empresa X accedió a tus datos de salud (ayer)   │
│  • Tu solicitud de portabilidad está lista         │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

### Ejercer Derecho a la Portabilidad

#### ¿Qué es la portabilidad de datos?
La Ley 21.719 te permite solicitar una copia completa de todos los datos que una organización tiene sobre ti, en un formato estructurado y legible por máquinas, para transferirlos a otro proveedor si lo deseas.

#### Pasos para descargar tus datos:

1. **Ve a "Portabilidad"**
   - En tu dashboard, haz clic en **"📥 Descargar mis datos"**

2. **Selecciona la organización**
   - Elige de qué empresa/institución quieres descargar tus datos
   - Ejemplo: "Banco XYZ", "Clínica ABC", "Retail DEF"

3. **Elige el formato**
   - **JSON**: Recomendado para uso técnico o transferencia automática
   - **CSV**: Ideal para abrir en Excel o Google Sheets
   - **XML**: Formato estándar para sistemas empresariales

4. **Selecciona categorías de datos (opcional)**
   - ☑️ Datos de identificación (nombre, RUT, contacto)
   - ☑️ Datos financieros (si aplica)
   - ☑️ Datos de salud (si aplica)
   - ☑️ Historial de transacciones
   - ☑️ Consentimientos otorgados
   - ☑️ Logs de accesos

5. **Confirma la solicitud**
   - Haz clic en **"Solicitar Exportación"**
   - Recibirás un email cuando esté listo (generalmente < 5 minutos)

6. **Descarga el archivo**
   - Vuelve a la sección "Portabilidad"
   - Haz clic en **"📥 Descargar"** junto a tu solicitud
   - El archivo tendrá un token de seguridad de un solo uso

#### ¿Qué incluye el archivo?

**Ejemplo en JSON:**
```json
{
  "metadata": {
    "ciudadano_rut_hash": "sha256_abc123...",
    "organizacion_rut": "76.123.456-K",
    "fecha_exportacion": "2025-01-15T10:30:00Z",
    "token_seguridad": "xyz789..."
  },
  "datos_personales": {
    "identificacion": {
      "nombre_completo": "Juan Pérez González",
      "fecha_nacimiento": "1985-05-20",
      "email": "juan.perez@email.com",
      "telefono": "+56912345678"
    },
    "consentimientos": [
      {
        "categoria": "SALUD",
        "finalidad": "Diagnóstico médico",
        "fecha_otorgamiento": "2024-06-15",
        "estado": "ACTIVO"
      }
    ],
    "transacciones": [...],
    "accesos_terceros": [...]
  }
}
```

#### Transferir a un competidor:
1. Descarga tus datos en formato JSON
2. Ve al sitio web del nuevo proveedor
3. Busca opción "Importar datos desde competidor"
4. Sube el archivo JSON
5. ¡Listo! Tus datos se migran automáticamente

---

### Derecho al Olvido (Supresión)

#### ¿Qué es el derecho al olvido?
Es tu derecho a solicitar la eliminación de tus datos personales cuando ya no son necesarios, retiras tu consentimiento, o han pasado los plazos legales de conservación.

#### ⚠️ Importante:
La eliminación puede ser **parcial** o **total**, pero existen excepciones legales donde la organización debe conservar ciertos datos (ej: facturas electrónicas por 6 años según ley tributaria).

#### Pasos para solicitar supresión:

1. **Ve a "Eliminar mis datos"**
   - En tu dashboard, haz clic en **"🗑️ Derecho al Olvido"**

2. **Selecciona el tipo de eliminación**
   - **Eliminación Parcial**: Borrara categorías específicas
   - **Eliminación Total**: Solicita borrar todos los datos posibles

3. **Si es parcial, elige categorías**
   - ☐ Datos de contacto (email, teléfono)
   - ☐ Historial de navegación
   - ☐ Preferencias y perfilamiento
   - ☐ Datos de ubicación
   - ☐ Otros (especificar)

4. **Motivo de la solicitud (opcional)**
   - "Ya no soy cliente"
   - "Retiro mi consentimiento"
   - "Los datos ya no son necesarios"
   - "Opposición al tratamiento"
   - Otro motivo

5. **Confirma con tu ClaveÚnica**
   - Por seguridad, deberás re-autenticarte
   - Esto evita eliminaciones accidentales o maliciosas

6. **Recibe el Certificado de Eliminación**
   - Inmediatamente después de procesarse, podrás descargar un **Certificado PDF** que acredita la eliminación
   - Este certificado tiene validez legal ante la Agencia de Protección de Datos

#### ¿Qué pasa después?

```
┌─────────────────────────────────────────────────────┐
│  CERTIFICADO DE ELIMINACIÓN DE DATOS               │
│  Ley 21.719 - Artículo 17                          │
│                                                     │
│  Fecha: 15 de enero de 2025                         │
│  Ciudadano: Juan Pérez González                    │
│  RUT Hash: sha256_abc123...                        │
│  Organización: Banco XYZ SpA                       │
│  RUT Organización: 76.123.456-K                    │
│                                                     │
│  CATEGORÍAS ELIMINADAS:                            │
│  ✅ Datos de contacto                               │
│  ✅ Historial de navegación                         │
│  ✅ Perfilamiento comercial                         │
│                                                     │
│  DATOS CONSERVADOS (por obligación legal):         │
│  ⚠️ Facturas electrónicas (Ley Tributaria Art. 56) │
│  ⚠️ Hash de auditoría (Ley 21.719 Art. 28)         │
│                                                     │
│  Firma Digital: [HASH_CERTIFICADO]                 │
│  Código de Verificación: ABC123XYZ                 │
│  Validar en: https://tudominio.cl/verificar        │
│                                                     │
└─────────────────────────────────────────────────────┘
```

#### Plazos de respuesta:
- **Máximo legal**: 30 días corridos
- **Promedio plataforma**: 24-48 horas
- Recibirás notificación por email cuando se complete

---

### Timeline de Accesos

#### ¿Por qué es importante?
La Ley 21.719 exige transparencia proactiva. Tienes derecho a saber **quién**, **cuándo**, **por qué** y **qué datos** ha accedido cualquier organización.

#### Cómo ver tu timeline:

1. **Ve a "Timeline de Accesos"**
   - En tu dashboard, haz clic en **"📅 Ver timeline"**

2. **Visualización cronológica**
   - Verás una línea de tiempo interactiva con todos los accesos

```
┌─────────────────────────────────────────────────────┐
│  📅 TIMELINE DE ACCESOS A TUS DATOS                │
│                                                     │
│  Enero 2025                                         │
│  ────────────────────────────────────────────────   │
│                                                     │
│  🏥 15 Ene, 10:30                                   │
│     Clínica ABC                                     │
│     📂 Datos accedidos: Historia clínica, exámenes  │
│     🎯 Finalidad: Diagnóstico médico                │
│     👨‍⚕️ Profesional: Dr. María González            │
│     ✅ Base legal: Consentimiento explícito         │
│                                                     │
│  🏦 12 Ene, 16:45                                   │
│     Banco XYZ                                       │
│     📂 Datos accedidos: Ingresos, historial crediticio│
│     🎯 Finalidad: Evaluación préstamo hipotecario   │
│     ✅ Base legal: Ejecución de contrato            │
│                                                     │
│  🛒 10 Ene, 09:15                                   │
│     Retail DEF                                      │
│     📂 Datos accedidos: Email, preferencias         │
│     🎯 Finalidad: Envío catálogo promocional        │
│     ⚠️ ¿No reconoces este acceso? [Reportar]        │
│                                                     │
│  Diciembre 2024                                     │
│  ────────────────────────────────────────────────   │
│  ... (más accesos)                                  │
│                                                     │
│  [⬇️ Descargar reporte completo en PDF]             │
│                                                     │
└─────────────────────────────────────────────────────┘
```

3. **Filtros disponibles**
   - Por fecha (rango personalizado)
   - Por organización
   - Por categoría de dato (salud, financiero, etc.)
   - Por tipo de acceso (lectura, modificación, eliminación)

4. **Reportar acceso no reconocido**
   - Si ves un acceso que no autorizaste, haz clic en **"⚠️ Reportar"**
   - Se generará automáticamente una denuncia ante la Agencia de Protección de Datos

#### ¿Qué información muestra cada acceso?
- **Fecha y hora exacta** del acceso
- **Organización** que accedió (con RUT verificado)
- **Categorías de datos** consultados
- **Finalidad específica** del acceso
- **Base legal** que justifica el acceso (consentimiento, contrato, obligación legal, etc.)
- **Profesional o sistema** que realizó el acceso
- **IP de origen** (para auditoría forense si es necesario)

---

### Oposición a Decisiones Automatizadas

#### ¿Qué son las decisiones automatizadas?
Son decisiones tomadas únicamente por algoritmos o sistemas de IA sin intervención humana significativa. Ejemplos:
- Rechazo automático de un crédito bancario
- Segmentación publicitaria basada en perfilamiento
- scoring crediticio automatizado
- filtrado de currículums por IA

#### Tus derechos (Art. 16 Ley 21.719):
1. **Ser informado** que una decisión fue tomada por un algoritmo
2. **Conocer la lógica** detrás de la decisión (explicabilidad)
3. **Solicitar intervención humana** para revisar la decisión
4. **Impugnar** la decisión si consideras que es injusta o discriminatoria

#### Cómo impugnar una decisión automatizada:

1. **Ve a "Decisiones Automatizadas"**
   - En tu dashboard, haz clic en **"⚖️ Impugnar decisión IA"**

2. **Selecciona la decisión a impugnar**
   - Verás listado de decisiones algorítmicas que te afectan
   - Ejemplo: "Crédito rechazado - Banco XYZ - 10 Ene 2025"

3. **Solicita intervención humana**
   - Marca la opción: **"☑️ Solicito revisión por persona humana"**
   - La organización tiene 10 días hábiles para responder

4. **Proporciona contexto adicional (opcional)**
   - Explica por qué consideras incorrecta la decisión
   - Adjunta documentos de respaldo si es necesario

5. **Recibe respuesta**
   - La organización debe responder con:
     - Explicación de la lógica del algoritmo
     - Resultado de la revisión humana
     - Posible rectificación de la decisión

#### Ejemplo de impugnación:

```
┌─────────────────────────────────────────────────────┐
│  IMPUGNACIÓN DE DECISIÓN AUTOMATIZADA              │
│  Folio: IMP-2025-00123                             │
│                                                     │
│  Ciudadano: Juan Pérez González                    │
│  Organización: Banco XYZ SpA                       │
│  Decisión impugnada: Rechazo de crédito            │
│  Fecha decisión: 10 de enero de 2025               │
│  Algoritmo: CreditScoring v3.2                     │
│                                                     │
│  SOLICITUD:                                        │
│  ☑️ Intervención humana requerida                  │
│  ☑️ Explicación de lógica algorítmica              │
│  ☑️ Revisión de datos utilizados                   │
│                                                     │
│  ARGUMENTOS DEL CIUDADANO:                         │
│  "El algoritmo no consideró mis ingresos          │
│   adicionales por trabajo independiente que        │
│   declaro en impuestos. Adjunto Formulario 22     │
│   del SII como respaldo."                          │
│                                                     │
│  ESTADO: En revisión                               │
│  Fecha límite respuesta: 24 de enero de 2025       │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

### Solicitudes ARCO

#### ¿Qué son los derechos ARCO?
Son los derechos básicos de protección de datos:
- **A**cceso: Saber qué datos tienen sobre ti
- **R**ectificación: Corregir datos incorrectos
- **C**ancelación: Eliminar datos (similar al olvido)
- **O**posición: Oponte a ciertos usos de tus datos

#### Cómo ejercer derechos ARCO:

1. **Ve a "Solicitudes ARCO"**
   - En tu dashboard, haz clic en **"⚖️ Nueva solicitud ARCO"**

2. **Selecciona el tipo de derecho**
   - 🔍 **Acceso**: "Quiero saber qué datos tienen sobre mí"
   - ✏️ **Rectificación**: "Este dato está incorrecto, corríjanlo"
   - 🗑️ **Cancelación**: "Eliminen este dato específico"
   - 🚫 **Oposición**: "No quiero que usen mis datos para X finalidad"

3. **Completa los detalles**
   - Organización destinataria
   - Datos específicos afectados
   - Justificación de la solicitud
   - Documentación de respaldo (si aplica)

4. **Envía la solicitud**
   - La organización tiene **30 días corridos** para responder
   - Puedes hacer seguimiento del estado en tu dashboard

5. **Si no responden o rechazan injustificadamente**
   - La plataforma genera automáticamente una denuncia ante la Agencia de Protección de Datos

---

## Para Organizaciones

### Registro y Login con SII

#### ¿Qué es el SII?
El Servicio de Impuestos Internos (SII) es la autoridad tributaria de Chile. Su sistema OAuth2 permite verificar oficialmente la identidad de empresas y sus representantes legales.

#### Pasos para registrar tu organización:

1. **Ingresa a la plataforma**
   - Ve a `https://tudominio.cl/organizaciones`

2. **Selecciona "Registrar Organización"**
   - Haz clic en el botón **"SII - Identidad Empresarial"**

3. **Autenticación en sitio del SII**
   - Serás redirigido al portal del SII
   - Ingresa con tu **Clave Tributaria** (RUT + contraseña)
   - O usa tu **Certificado Digital** si tienes uno

4. **Selecciona la empresa a representar**
   - Si representas múltiples empresas, elige cuál registrar
   - El sistema verificará automáticamente que eres representante legal

5. **Completa información del DPO**
   - Ingresa los datos del Delegado de Protección de Datos (DPO)
   - Email oficial de contacto para la Agencia de Protección de Datos
   - Esta información es **obligatoria** según Art. 28 Ley 21.719

6. **¡Organización registrada!**
   - Recibirás credenciales API para integraciones
   - Podrás comenzar a gestionar consentimientos y RAT

#### Seguridad:
- ✅ RUT de la organización verificado oficialmente con el SII
- ✅ Representación legal validada automáticamente
- ✅ API Keys encriptadas con SHA-256

---

### Panel de Administración

Al ingresar como organización, verás:

```
┌─────────────────────────────────────────────────────┐
│  🏢 [Razón Social de la Empresa]                    │
│  RUT: 76.123.456-K | DPO: dpo@empresa.cl           │
│                                                     │
│  📊 Estado de Cumplimiento                          │
│  ┌─────────────────────────────────────────────┐   │
│  │ ████████████░░░░░░░░  75% Completado        │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  ⚠️ Alertas Críticas                                │
│  • 2 solicitudes ARCO próximas a vencer (48h)      │
│  • 1 brecha de seguridad pendiente de notificación │
│                                                     │
│  📋 Módulos Principales                             │
│  [📝 RAT] [🔐 Consentimientos] [🚨 Brechas]        │
│  [📊 EIPD] [🤝 Encargados] [🛡️ Panel DPO]          │
│                                                     │
│  📈 Métricas del Mes                                │
│  • Consentimientos activos: 1,245                  │
│  • Solicitudes ARCO recibidas: 18                  │
│  • Accesos a datos registrados: 3,456              │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

### Gestión de Consentimientos

#### ¿Por qué es importante?
El consentimiento es la base legal más común para tratar datos personales. La Ley 21.719 exige que sea:
- **Libre**: Sin coerción o condicionamiento
- **Informado**: El ciudadano entiende claramente para qué usa sus datos
- **Específico**: Para finalidades concretas (no "usos generales")
- **Indubitable**: Debe quedar registro fehaciente

#### Crear propuesta de consentimiento:

1. **Ve a "Consentimientos"**
   - En el panel, haz clic en **"🔐 Nuevo Consentimiento"**

2. **Define categorías de datos**
   - Selecciona qué datos necesitas:
     - ☐ Identificación básica (nombre, RUT, email)
     - ☐ Datos de contacto (teléfono, dirección)
     - ☐ Datos financieros (ingresos, historial crediticio)
     - ☐ Datos de salud (diagnósticos, tratamientos)
     - ☐ Datos biométricos (huella, reconocimiento facial)
     - ☐ Ubicación geográfica
     - ☐ Otros (especificar)

3. **Establece finalidades específicas**
   - ❌ Mal: "Para mejorar nuestros servicios"
   - ✅ Bien: "Para enviar resultados de exámenes médicos por email"
   - ✅ Bien: "Para procesar pago de cuotas mensuales"
   - ✅ Bien: "Para diagnóstico y tratamiento médico"

4. **Configura vigencia**
   - ¿El consentimiento tiene fecha de expiración?
   - Ejemplo: "Vence en 2 años" o "Indefinido hasta revocación"

5. **Redacta en lenguaje claro (Legal Design)**
   - La plataforma incluye asistente de redacción clara
   - Evita tecnicismos legales innecesarios
   - Usa íconos y resúmenes visuales

6. **Genera hash de evidencia**
   - El sistema crea automáticamente un receipt hash (firma digital)
   - Este hash prueba el contenido exacto presentado al ciudadano

#### Ejemplo de consentimiento bien redactado:

```
┌─────────────────────────────────────────────────────┐
│  💙 AUTORIZACIÓN DE TRATAMIENTO DE DATOS           │
│  Clínica ABC SpA - RUT 76.123.456-K                │
│                                                     │
│  👋 Hola, [Nombre del Paciente]                    │
│                                                     │
│  📋 ¿Qué datos necesitamos?                         │
│  ┌─────────────────────────────────────────────┐   │
│  │ 🏥 Datos de Salud                           │   │
│  │    - Diagnósticos médicos                   │   │
│  │    - Resultados de exámenes                 │   │
│  │    - Historial de tratamientos              │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  🎯 ¿Para qué los usaremos?                         │
│  ┌─────────────────────────────────────────────┐   │
│  │ • Realizar diagnóstico médico preciso       │   │
│  │ • Programar tratamientos adecuados          │   │
│  │ • Enviar resultados por email seguro        │   │
│  │ • Mantener registro clínico obligatorio     │   │
│  │                                             │   │
│  │ ❌ NO usaremos tus datos para:              │   │
│  │    • Publicidad comercial                   │   │
│  │    • Venta a terceros                       │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  ⏰ ¿Por cuánto tiempo?                             │
│  Conservaremos tus datos mientras seas paciente    │
│  + 10 años (obligación legal de registros médicos)│
│                                                     │
│  🔒 ¿Quién tiene acceso?                            │
│  Solo personal médico autorizado y tú mismo        │
│  mediante portal de paciente con ClaveÚnica        │
│                                                     │
│  ✅ ACEPTAR    ❌ RECHAZAR                         │
│                                                     │
│  Receipt Hash: sha256_abc123xyz...                 │
│  Fecha: 15 de enero de 2025, 10:30                 │
│                                                     │
└─────────────────────────────────────────────────────┘
```

#### Revocación de consentimiento:
- Los ciudadanos pueden revocar en cualquier momento
- La plataforma notifica automáticamente a la organización
- Debes cesar el tratamiento inmediatamente (excepto datos con obligación legal de conservación)

---

### RAT - Registro de Actividades

#### ¿Qué es el RAT?
El **Registro de Actividades de Tratamiento (RAT)** es obligatorio según Art. 27 de la Ley 21.719. Es un documento interno que registra TODOS los tratamientos de datos personales que realiza tu organización.

#### ¿Cuándo actualizar el RAT?
- Al iniciar operaciones (registro inicial)
- Al crear nuevos productos/servicios que usen datos
- Al cambiar proveedores (encargados de tratamiento)
- Mínimo: Revisión anual obligatoria

#### Registrar actividad de tratamiento:

1. **Ve a "RAT"**
   - En el panel, haz clic en **"📝 Nueva Actividad"**

2. **Completa información requerida**:

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| **Responsable** | ¿Quién trata los datos? | Clínica ABC SpA |
| **Finalidad** | ¿Por qué se tratan? | Diagnóstico y tratamiento médico |
| **Categorías de datos** | ¿Qué datos se usan? | Salud, identificación, contacto |
| **Categorías de titulares** | ¿De quiénes son los datos? | Pacientes, trabajadores |
| **Destinatarios** | ¿Quiénes reciben los datos? | ISAPREs, Ministerio de Salud |
| **Transferencias internacionales** | ¿Salen de Chile? | No / Sí (especificar país) |
| **Plazo de conservación** | ¿Cuánto se guardan? | 10 años post último contacto |
| **Medidas de seguridad** | ¿Cómo se protegen? | Encriptación AES-256, acceso con MFA |

3. **Adjunta documentación**
   - Políticas de privacidad relacionadas
   - Contratos con encargados de tratamiento
   - EIPD si aplica (datos sensibles a gran escala)

4. **Guarda y firma digitalmente**
   - El DPO debe aprobar cada registro
   - Se genera hash de integridad del documento

#### Generar reporte para la Agencia:

La plataforma permite exportar el RAT completo en formato PDF listo para presentar ante la Agencia de Protección de Datos en caso de fiscalización:

```
┌─────────────────────────────────────────────────────┐
│  REGISTRO DE ACTIVIDADES DE TRATAMIENTO            │
│  Ley 21.719 - Artículo 27                          │
│                                                     │
│  ORGANIZACIÓN: Clínica ABC SpA                     │
│  RUT: 76.123.456-K                                 │
│  DPO: María González López                         │
│  Email DPO: dpo@clinicaabc.cl                      │
│  Fecha de emisión: 15 de enero de 2025             │
│                                                     │
│  ACTIVIDAD #1: GESTIÓN CLÍNICA DE PACIENTES        │
│  ────────────────────────────────────────────────  │
│  Finalidad: Diagnóstico, tratamiento y seguimiento │
│  Categorías de datos: Salud, identificación        │
│  Titulares: Pacientes adultos y menores            │
│  Destinatarios: ISAPREs, FONASA, MSP               │
│  Transferencias internacionales: No                │
│  Plazo conservación: 10 años                       │
│  Medidas seguridad: Encriptación, MFA, auditoría   │
│  Base legal: Consentimiento + obligación legal     │
│                                                     │
│  ACTIVIDAD #2: NÓMINA DE TRABAJADORES              │
│  ────────────────────────────────────────────────  │
│  ... (más actividades)                             │
│                                                     │
│  FIRMA DIGITAL DPO: [HASH_FIRMA]                   │
│  CÓDIGO VERIFICACIÓN: XYZ789ABC                    │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

### Gestión de Brechas

#### ¿Qué es una brecha de seguridad?
Una brecha es cualquier incidente que comprometa la **confidencialidad**, **integridad** o **disponibilidad** de datos personales. Ejemplos:
- Hackeo de base de datos
- Email enviado a destinatario equivocado
- Laptop robada con datos de clientes
- Acceso no autorizado de empleado

#### Plazos críticos (Art. 38-40):

```
┌─────────────────────────────────────────────────────┐
│  ⏰ CRONOGRAMA DE NOTIFICACIÓN DE BRECHAS          │
│                                                     │
│  🚨 OCURRE LA BRECHA (Hora 0)                      │
│     • Detectas acceso no autorizado                │
│     • Sistema genera alerta automática             │
│                                                     │
│  ⏱️  Hora 0-24: EVALUACIÓN INTERNA                 │
│     • Clasificar gravedad (baja/media/alta)        │
│     • Identificar datos y titulares afectados      │
│     • Contener la brecha                           │
│                                                     │
│  ⏱️  Hora 24-72: NOTIFICACIÓN AGENCIA ⚠️          │
│     • PLAZO MÁXIMO: 72 horas desde detección       │
│     • Notificar a Agencia de Protección de Datos   │
│     • Incluir: naturaleza, datos afectados,        │
│       medidas correctivas, DPO de contacto         │
│                                                     │
│  ⏱️  Hora 72+: NOTIFICACIÓN A AFECTADOS 👤        │
│     • Si hay ALTO RIESGO para derechos             │
│     • Informar en lenguaje claro                   │
│     • Recomendar medidas de protección             │
│                                                     │
│  📅 Días siguientes: DOCUMENTACIÓN                 │
│     • Registrar todo en bitácora de brechas        │
│     • Actualizar RAT si corresponde                │
│     • Implementar mejoras preventivas              │
│                                                     │
└─────────────────────────────────────────────────────┘
```

#### Reportar brecha en la plataforma:

1. **Ve a "Brechas de Seguridad"**
   - En el panel, haz clic en **"🚨 Nueva Brecha"**

2. **Clasifica la gravedad**
   - **Baja**: Sin impacto significativo en titulares
   - **Media**: Posible molestia o inconveniente
   - **Alta**: Riesgo de discriminación, fraude, daño reputacional

3. **Describe el incidente**
   - Fecha y hora de detección
   - Tipo de brecha (acceso no autorizado, pérdida, divulgación)
   - Volumen aproximado de afectados
   - Categorías de datos comprometidos

4. **La plataforma genera automáticamente**:
   - 📄 Reporte para la Agencia (formato oficial)
   - 📧 Email para notificar a afectados (plantilla legal)
   - 📊 Ficha técnica para auditoría interna

5. **Notifica con un clic**
   - **Botón "Notificar a Agencia"**: Envía reporte oficial
   - **Botón "Notificar a Afectados"**: Envía emails masivos

#### Seguimiento de brechas:

```
┌─────────────────────────────────────────────────────┐
│  🚨 BRECHA #BRE-2025-0042                          │
│  Estado: 🔴 ABIERTA - En investigación             │
│                                                     │
│  DETALLES:                                         │
│  Fecha detección: 15 de enero de 2025, 08:30      │
│  Tipo: Acceso no autorizado por vulnerabilidad     │
│  Gravedad: ALTA                                    │
│  Afectados estimados: 1,245 clientes               │
│  Datos comprometidos: Email, teléfono, RUT         │
│                                                     │
│  ACCIONES TOMADAS:                                 │
│  ✅ Contenida la brecha (15 Ene, 09:15)            │
│  ✅ Notificada a Agencia (15 Ene, 14:30) ✓         │
│  ⏳ Pendiente notificar a afectados                │
│  ⏳ Investigación forense en curso                 │
│                                                     │
│  PRÓXIMOS PASOS:                                   │
│  • Notificar a afectados antes de 18 Ene (72h)    │
│  • Publicar comunicado en website                 │
│  • Reforzar medidas de seguridad                   │
│                                                     │
│  [📧 Enviar notificación a afectados]              │
│  [📄 Descargar informe forense]                    │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

### Panel DPO

#### ¿Qué es el DPO?
El **Delegado de Protección de Datos (DPO)** es el responsable interno de asegurar el cumplimiento de la Ley 21.719. Su designación es **obligatoria** para ciertas organizaciones (tratamiento de datos sensibles a gran escala, organismos públicos, etc.).

#### Funciones del DPO en la plataforma:

1. **Dashboard de cumplimiento**
   - Vista general del estado de cumplimiento
   - Alertas críticas prioritarias
   - Métricas clave (KPIs)

2. **Aprobación de tratamientos**
   - Revisar y aprobar nuevos consentimientos
   - Validar EIPD antes de lanzar productos
   - Autorizar transferencias internacionales

3. **Gestión de solicitudes ARCO**
   - Monitorear plazos de respuesta
   - Revisar casos complejos
   - Generar respuestas estandarizadas

4. **Reportes ejecutivos**
   - Informes mensuales a directorio
   - Preparación para fiscalizaciones
   - Benchmarking vs industria

#### Acceso al Panel DPO:

```
┌─────────────────────────────────────────────────────┐
│  🛡️ PANEL DEL DELEGADO DE PROTECCIÓN DE DATOS     │
│  DPO: María González López                         │
│  Última conexión: Hoy, 09:15                       │
│                                                     │
│  📊 MÉTRICAS GENERALES                             │
│  ┌──────────────┬──────────────┬──────────────┐   │
│  │ Nivel        │ Solicitudes  │ Brechas      │   │
│  │ Cumplimiento │ ARCO pend.   │ activas      │   │
│  ├──────────────┼──────────────┼──────────────┤   │
│  │    87%       │     5        │     2        │   │
│  └──────────────┴──────────────┴──────────────┘   │
│                                                     │
│  ⚠️ ALERTAS CRÍTICAS (Requieren atención)          │
│  ┌─────────────────────────────────────────────┐   │
│  │ 🔴 Solicitud ARCO vence en 24h              │   │
│  │    - Juan Pérez vs Banco XYZ                │   │
│  │    - Tipo: Acceso completo                  │   │
│  │    [Ver caso] [Extender plazo]              │   │
│  ├─────────────────────────────────────────────┤   │
│  │ 🟠 Brecha sin notificar a afectados         │   │
│  │    - BRE-2025-0042                          │   │
│  │    - Vence en 18 horas                      │   │
│  │    [Notificar ahora]                        │   │
│  ├─────────────────────────────────────────────┤   │
│  │ 🟡 EIPD pendiente de aprobación             │   │
│  │    - Proyecto: Biometría Facial             │   │
│  │    - Solicitante: Gerencia TI               │   │
│  │    [Revisar EIPD]                           │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  📅 CALENDARIO LEGAL                               │
│  • 20 Ene: Vencimiento 3 solicitudes ARCO         │
│  • 25 Ene: Revisión trimestral RAT                │
│  • 01 Feb: Capacitación obligatoria equipo        │
│  • 15 Feb: Auditoría externa programada           │
│                                                     │
│  📋 ACCESOS RÁPIDOS                                │
│  [Aprobar Consentimientos] [Revisar EIPD]         │
│  [Reporte Agencia] [Capacitaciones]               │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

### Encargados de Tratamiento

#### ¿Qué es un encargado de tratamiento?
Es un **tercero** que procesa datos personales **por cuenta del responsable**. Ejemplos:
- Servicios cloud (AWS, Azure, Google Cloud)
- Pasarelas de pago (Stripe, Transbank, MercadoPago)
- Call centers externos
- Servicios de nómina outsourcing
- Plataformas de email marketing

#### Obligaciones legales (Art. 28):
1. **Contrato de encargo**: Documento escrito que establece:
   - Instrucciones precisas de tratamiento
   - Medidas de seguridad obligatorias
   - Prohibición de usar datos para otros fines
   - Obligación de confidencialidad
   - Cooperación en solicitudes ARCO
   - Notificación inmediata de brechas

2. **Auditoría**: El responsable puede (y debe) auditar al encargado

3. **Subcontratación**: El encargado no puede subcontratar sin autorización

#### Registrar encargado en la plataforma:

1. **Ve a "Encargados de Tratamiento"**
   - En el panel, haz clic en **"🤝 Nuevo Encargado"**

2. **Completa información del tercero**:
   - Razón social y RUT
   - País de operación (importante para transferencias internacionales)
   - Servicios que presta (ej: "hosting de base de datos")
   - Categorías de datos que procesará
   - Medidas de seguridad certificadas (ISO 27001, SOC2, etc.)

3. **Sube contrato de encargo**
   - La plataforma incluye plantilla legal pre-aprobada
   - Personaliza según necesidades específicas
   - Ambas partes firman digitalmente

4. **Configura auditorías periódicas**
   - Frecuencia recomendada: Anual mínimo
   - La plataforma genera recordatorios automáticos

#### Dashboard de encargados:

```
┌─────────────────────────────────────────────────────┐
│  🤝 ENCARGADOS DE TRATAMIENTO                      │
│  Total registrados: 12                             │
│  Auditorías pendientes: 3                          │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │ AWS LATIN AMERICA INC.                       │  │
│  │ 🌐 País: Chile (datos residen en Chile)      │  │
│  │ 📂 Datos: Todos (hosting infraestructura)    │  │
│  │ 🔒 Certificaciones: ISO 27001, SOC2 Type II  │  │
│  │ 📅 Contrato vigente hasta: Dic 2026          │  │
│  │ 🔍 Última auditoría: Mar 2024 ✅ Aprobada    │  │
│  │ 📅 Próxima auditoría: Mar 2025               │  │
│  │ [Ver contrato] [Agendar auditoría]           │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │ STRIPE INC.                                  │  │
│  │ 🌐 País: EE.UU. (transferencia internacional)│  │
│  │ 📂 Datos: Financieros (tarjetas crédito)     │  │
│  │ 🔒 Certificaciones: PCI-DSS Level 1          │  │
│  │ 📅 Contrato vigente hasta: Jun 2025          │  │
│  │ 🔍 Última auditoría: Ene 2024 ✅ Aprobada    │  │
│  │ ⚠️ Próxima auditoría: VENCIDA (Ene 2025)    │  │
│  │ [Ver contrato] [⚠️ Agendar urgente]          │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  [+ Agregar nuevo encargado]                       │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Preguntas Frecuentes

### Para Ciudadanos

**❓ ¿Es gratuito ejercer mis derechos?**  
✅ Sí, totalmente gratuito. La Ley 21.719 prohíbe cobrar por ejercer derechos ARCO.

**❓ ¿Cuánto tiempo tienen para responder mis solicitudes?**  
⏱️ Máximo 30 días corridos para ARCO y portabilidad. Para supresión, depende de la complejidad pero generalmente < 48 horas.

**❓ ¿Qué pasa si la organización no responde?**  
🚨 La plataforma genera automáticamente una denuncia ante la Agencia de Protección de Datos. Además, puedes reclamar directamente en www.agenciaprotecciondatos.cl.

**❓ ¿Puedo ejercer derechos por mis hijos menores?**  
👶 Sí, si eres padre/madre o tutor legal. El sistema valida tu patria potestad mediante registro civil.

**❓ ¿Mis datos están seguros en esta plataforma?**  
🔒 Sí, usamos encriptación AES-256, hashing SHA-256 para RUT, autenticación oficial con ClaveÚnica, y auditamos todos los accesos.

**❓ ¿Puedo eliminar mi cuenta de esta plataforma?**  
🗑️ Sí, pero ten en cuenta que esto solo elimina tu cuenta del portal, no de las organizaciones donde has otorgado consentimientos. Para eso debes ejercer derecho al olvido con cada organización por separado.

---

### Para Organizaciones

**❓ Quiénes están obligados a cumplir esta ley?**  
📋 Todas las organizaciones (públicas y privadas) que traten datos personales de personas en Chile, sin importar dónde esté ubicada la empresa.

**❓ Cuándo debo designar un DPO?**  
👤 Es obligatorio si:
- Eres organismo público
- Tratas datos sensibles a gran escala
- Tu actividad principal es tratar datos para perfilamiento
- La Agencia te lo solicita

**❓ Qué multas hay por incumplimiento?**  
💰 Hasta 25.000 UTM (aprox. $1.5 billones de pesos chilenos en 2025), dependiendo de la gravedad.

**❓ ¿Debo registrar todas mis actividades de tratamiento?**  
✅ Sí, el RAT debe ser exhaustivo. Incluye incluso tratamientos pequeños o aparentemente inocuos.

**❓ ¿Cómo manejo datos de empleados?**  
👔 Aplica la misma ley. Necesitas consentimiento o base legal alternativa (ej: ejecución de contrato laboral).

**❓ ¿Qué pasa con datos que obtuve antes de la ley?**  
📅 Tienes un plazo de adecuación (generalmente 6 meses desde entrada en vigor). Debes regularizar consentimientos antiguos.

---

## Glosario Legal

| Término | Definición |
|---------|------------|
| **Titular** | Persona natural dueña de los datos personales |
| **Responsable** | Organización que decide por qué y cómo tratar datos |
| **Encargado** | Tercero que trata datos por cuenta del responsable |
| **Tratamiento** | Cualquier operación con datos (recoger, usar, almacenar, eliminar, etc.) |
| **Consentimiento** | Manifestación libre, informada y específica de voluntad |
| **Datos sensibles** | Origen racial, ideología, religión, salud, vida sexual, biometría |
| **Disociación** | Procedimiento que imposibilita identificar al titular |
| **Seudonimización** | Reemplazar datos identificadores por seudónimos |
| **Perfilamiento** | Tratamiento automatizado para analizar/predecir comportamiento |
| **Transferencia internacional** | Enviar datos a país distinto de Chile |
| **Brecha de seguridad** | Compromiso de confidencialidad, integridad o disponibilidad |
| **EIPD** | Evaluación de Impacto en Protección de Datos (DPIA en inglés) |
| **RAT** | Registro de Actividades de Tratamiento |

---

## Soporte y Contacto

### Para Ciudadanos:
- 📧 Email: ayuda@tudominio.cl
- 📞 Teléfono: +56 2 2XXX XXXX (lunes a viernes, 9:00-18:00)
- 💬 Chat en vivo: Disponible en esquina inferior derecha

### Para Organizaciones:
- 📧 Email: empresas@tudominio.cl
- 📞 Teléfono: +56 2 2XXX XXXX opción 2
- 🎓 Capacitaciones: Agenda sesiones gratuitas en [calendario.tudominio.cl](https://calendario.tudominio.cl)

### Agencia de Protección de Datos:
- 🌐 Website: www.agenciaprotecciondatos.cl
- 📧 Denuncias: denuncias@agenciaprotecciondatos.cl
- 📞 Teléfono: +56 2 2XXX XXXX

---

*Última actualización: Mayo 2025*  
*Versión de la guía: 2.0.0*  
*Ley 21.719 - Protección de Datos Personales de Chile*
