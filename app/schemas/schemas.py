"""
Esquemas Pydantic para validación y serialización de datos
Ley 21.719 - Protección de Datos (Chile)
"""

from pydantic import BaseModel, Field, EmailStr, validator, ConfigDict
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from uuid import UUID
from enum import Enum


# ==================== ENUMS SERIALIZABLES ====================

class EstadoPermisoEnum(str, Enum):
    ACTIVO = "ACTIVO"
    REVOCADO = "REVOCADO"
    PENDIENTE = "PENDIENTE"
    EXPIRADO = "EXPIRADO"


class EstadoSolicitudEnum(str, Enum):
    PENDIENTE = "PENDIENTE"
    APROBADA = "APROBADA"
    RECHAZADA = "RECHAZADA"
    CANCELADA = "CANCELADA"
    EXPIRADA = "EXPIRADA"


class AiFlagEnum(str, Enum):
    NONE = "NONE"
    AI_GENERATED = "AI_GENERATED"
    AI_ASSISTED = "AI_ASSISTED"
    HUMAN_REVIEWED = "HUMAN_REVIEWED"


class TipoArcoEnum(str, Enum):
    ACCESO = "ACCESO"
    RECTIFICACION = "RECTIFICACION"
    CANCELACION = "CANCELACION"
    OPOSICION = "OPOSICION"
    PORTABILIDAD = "PORTABILIDAD"
    LIMITACION = "LIMITACION"


class EstadoArcoEnum(str, Enum):
    PENDIENTE = "PENDIENTE"
    EN_PROCESO = "EN_PROCESO"
    COMPLETADA = "COMPLETADA"
    RECHAZADA = "RECHAZADA"
    PRORROGADA = "PRORROGADA"


class TipoAccesoEnum(str, Enum):
    LECTURA = "LECTURA"
    MODIFICACION = "MODIFICACION"
    ELIMINACION = "ELIMINACION"
    CREACION = "CREACION"
    TRANSFERENCIA = "TRANSFERENCIA"


# ==================== USUARIO ====================

class UsuarioBase(BaseModel):
    rut: str = Field(..., min_length=9, max_length=12, description="RUT sin puntos, con guión")
    nombre_completo: str = Field(..., min_length=3, max_length=255)
    email: EmailStr
    telefono: Optional[str] = Field(None, max_length=50)
    fecha_nacimiento: date
    tutor_id: Optional[UUID] = None


class UsuarioCreate(UsuarioBase):
    """Esquema para creación de usuario"""
    pass


class UsuarioUpdate(BaseModel):
    """Esquema para actualización parcial de usuario"""
    nombre_completo: Optional[str] = None
    email: Optional[EmailStr] = None
    telefono: Optional[str] = None
    tutor_id: Optional[UUID] = None


class UsuarioResponse(UsuarioBase):
    id: UUID
    rut_hash: str = Field(..., description="Hash SHA-256 del RUT (público para búsqueda)")
    fecha_registro: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ==================== ORGANIZACION ====================

class OrganizacionBase(BaseModel):
    rut: str = Field(..., min_length=9, max_length=12)
    razon_social: str = Field(..., min_length=3, max_length=255)
    email_dpo: EmailStr = Field(..., description="Email del Data Protection Officer")
    webhook_url_revocacion: Optional[str] = None
    modelo_prevencion_certificado: bool = False


class OrganizacionCreate(OrganizacionBase):
    pass


class OrganizacionUpdate(BaseModel):
    razon_social: Optional[str] = None
    email_dpo: Optional[EmailStr] = None
    webhook_url_revocacion: Optional[str] = None
    modelo_prevencion_certificado: Optional[bool] = None


class OrganizacionResponse(OrganizacionBase):
    id: UUID
    fecha_registro: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ==================== API KEY ====================

class OrganizacionApiKeyBase(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=100)
    fecha_expiracion: Optional[datetime] = None


class OrganizacionApiKeyCreate(OrganizacionApiKeyBase):
    pass


class OrganizacionApiKeyResponse(BaseModel):
    id: UUID
    organizacion_id: UUID
    nombre: str
    prefix: str = Field(..., description="Prefijo de la API Key (ej: cl_ly_prod_...)")
    activa: bool
    fecha_expiracion: Optional[datetime]
    fecha_creacion: datetime
    ultimo_uso: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class OrganizacionApiKeyWithSecret(OrganizacionApiKeyResponse):
    api_key_secret: str = Field(..., description="API Key completa (solo se muestra al crear)")


# ==================== ACCESO ORGANIZACION ====================

class AccesoOrganizacionBase(BaseModel):
    categoria_dato: str = Field(..., description="Categoría de dato (SALUD, BIOMETRIA, etc.)")
    finalidad: str = Field(..., min_length=10, description="Finalidad específica del uso de datos")
    fecha_expiracion: Optional[datetime] = None


class AccesoOrganizacionCreate(AccesoOrganizacionBase):
    usuario_id: UUID
    organizacion_id: UUID


class AccesoOrganizacionResponse(BaseModel):
    id: UUID
    usuario_id: UUID
    organizacion_id: UUID
    categoria_dato: str
    finalidad: str
    estado: EstadoPermisoEnum
    receipt_hash: str
    fecha_otorgamiento: datetime
    fecha_expiracion: Optional[datetime]
    fecha_revocacion: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class AccesoOrganizacionRevoke(BaseModel):
    """Esquema para revocar acceso"""
    motivo: Optional[str] = None


# ==================== SOLICITUD CONSENTIMIENTO ====================

class SolicitudConsentimientoBase(BaseModel):
    rut_ciudadano: str = Field(..., description="RUT del ciudadano")
    proposal_json: Dict[str, Any] = Field(..., description="Estructura granular de permisos")
    texto_legal_presentado: str = Field(..., min_length=50)
    request_type: str = Field(default="NORMAL", pattern="^(NORMAL|PORTABILIDAD)$")
    source_organization_id: Optional[UUID] = None


class SolicitudConsentimientoCreate(SolicitudConsentimientoBase):
    pass


class SolicitudConsentimientoResponse(BaseModel):
    id: UUID
    organizacion_id: UUID
    rut_ciudadano_hash: str
    estado: EstadoSolicitudEnum
    proposal_json: Dict[str, Any]
    ai_flag: AiFlagEnum
    texto_legal_presentado: str
    request_type: str
    source_organization_id: Optional[UUID]
    fecha_solicitud: datetime
    fecha_respuesta: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class SolicitudConsentimientoApprove(BaseModel):
    """Aprobar solicitud de consentimiento"""
    ip_cliente: Optional[str] = None


class SolicitudConsentimientoReject(BaseModel):
    """Rechazar solicitud de consentimiento"""
    motivo: str


# ==================== SOLICITUD ARCO ====================

class SolicitudArcoBase(BaseModel):
    rut_ciudadano: str = Field(..., description="RUT del ciudadano")
    tipo: TipoArcoEnum
    descripcion: Optional[str] = None
    token_evidencia_identidad: str = Field(..., description="Hash de ClaveÚnica o Firma Electrónica")


class SolicitudArcoCreate(SolicitudArcoBase):
    pass


class SolicitudArcoResponse(BaseModel):
    id: UUID
    organizacion_id: UUID
    rut_ciudadano_hash: str
    tipo: TipoArcoEnum
    estado: EstadoArcoEnum
    token_evidencia_identidad: str
    prorrogado: bool
    descripcion: Optional[str]
    fecha_solicitud: datetime
    fecha_limite_respuesta: datetime
    fecha_respuesta: Optional[datetime]
    respuesta: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)


class SolicitudArcoProcess(BaseModel):
    """Procesar solicitud ARCO"""
    estado: EstadoArcoEnum
    respuesta: str
    prorrogar: bool = False


# ==================== LOG ACCESO DATOS ====================

class LogAccesoDatosBase(BaseModel):
    tipo_acceso: TipoAccesoEnum
    categoria_dato_consultado: str
    justificacion_legal: str = Field(..., min_length=20)
    ip_origen: str
    user_agent: Optional[str] = None
    detalles_adicionales: Optional[Dict[str, Any]] = None


class LogAccesoDatosCreate(LogAccesoDatosBase):
    usuario_id: UUID
    organizacion_id: UUID


class LogAccesoDatosResponse(BaseModel):
    id: UUID
    usuario_id: UUID
    organizacion_id: UUID
    tipo_acceso: TipoAccesoEnum
    categoria_dato_consultado: str
    justificacion_legal: str
    ip_origen: str
    user_agent: Optional[str]
    fecha_acceso: datetime
    detalles_adicionales: Optional[Dict[str, Any]]
    
    model_config = ConfigDict(from_attributes=True)


class LogAccesoDatosQuery(BaseModel):
    """Filtros para consulta de logs"""
    usuario_id: Optional[UUID] = None
    organizacion_id: Optional[UUID] = None
    tipo_acceso: Optional[TipoAccesoEnum] = None
    fecha_desde: Optional[datetime] = None
    fecha_hasta: Optional[datetime] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)


# ==================== RESPUESTAS GENERALES ====================

class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    limit: int
    offset: int
    has_more: bool
