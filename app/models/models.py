"""
Modelos de datos para Ley 21.719 - Protección de Datos (Chile)
Implementa el diagrama entidad-relación especificado
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Text, LargeBinary, Integer
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.database import Base


# ==================== ENUMS ====================

class EstadoPermiso(str, enum.Enum):
    ACTIVO = "ACTIVO"
    REVOCADO = "REVOCADO"
    PENDIENTE = "PENDIENTE"
    EXPIRADO = "EXPIRADO"


class EstadoSolicitud(str, enum.Enum):
    PENDIENTE = "PENDIENTE"
    APROBADA = "APROBADA"
    RECHAZADA = "RECHAZADA"
    CANCELADA = "CANCELADA"
    EXPIRADA = "EXPIRADA"


class AiFlag(str, enum.Enum):
    NONE = "NONE"
    AI_GENERATED = "AI_GENERATED"
    AI_ASSISTED = "AI_ASSISTED"
    HUMAN_REVIEWED = "HUMAN_REVIEWED"


class TipoArco(str, enum.Enum):
    ACCESO = "ACCESO"
    RECTIFICACION = "RECTIFICACION"
    CANCELACION = "CANCELACION"
    OPOSICION = "OPOSICION"
    PORTABILIDAD = "PORTABILIDAD"
    LIMITACION = "LIMITACION"


class EstadoArco(str, enum.Enum):
    PENDIENTE = "PENDIENTE"
    EN_PROCESO = "EN_PROCESO"
    COMPLETADA = "COMPLETADA"
    RECHAZADA = "RECHAZADA"
    PRORROGADA = "PRORROGADA"


class TipoAcceso(str, enum.Enum):
    LECTURA = "LECTURA"
    MODIFICACION = "MODIFICACION"
    ELIMINACION = "ELIMINACION"
    CREACION = "CREACION"
    TRANSFERENCIA = "TRANSFERENCIA"


# ==================== MODELOS ====================

class Usuario(Base):
    """
    Modelo de Usuario según Ley 21.719
    - rutHash: SHA-256 para indexación (UK)
    - rutEncriptado: AES-256 para despliegue seguro
    - fechaNacimiento: Validación +16 años (o requiere tutorId)
    """
    __tablename__ = "usuarios"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rut_hash = Column(String(64), unique=True, index=True, nullable=False)  # SHA-256
    rut_encriptado = Column(String(256), nullable=False)  # AES-256
    nombre_completo = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    telefono = Column(String(50))
    fecha_nacimiento = Column(DateTime, nullable=False)
    tutor_id = Column(PGUUID(as_uuid=True), ForeignKey('usuarios.id'), nullable=True)
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relaciones
    tutor = relationship("Usuario", remote_side=[id], backref="tutelados")
    accesos = relationship("AccesoOrganizacion", back_populates="usuario", cascade="all, delete-orphan")
    logs_acceso = relationship("LogAccesoDatos", back_populates="usuario", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Usuario(id={self.id}, email={self.email})>"


class Organizacion(Base):
    """
    Modelo de Organización que gestiona datos personales
    - Debe tener DPO (Data Protection Officer) registrado
    - modeloPrevencionCertificado: Indica si tiene certificación de prevención
    """
    __tablename__ = "organizaciones"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rut = Column(String(20), unique=True, nullable=False, index=True)
    razon_social = Column(String(255), nullable=False)
    email_dpo = Column(String(255), nullable=False)  # Contacto Oficial Agencia
    webhook_url_revocacion = Column(String(500), nullable=True)
    modelo_prevencion_certificado = Column(Boolean, default=False, nullable=False)
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relaciones
    api_keys = relationship("OrganizacionApiKey", back_populates="organizacion", cascade="all, delete-orphan")
    accesos = relationship("AccesoOrganizacion", back_populates="organizacion", cascade="all, delete-orphan")
    solicitudes_arco = relationship("SolicitudArco", back_populates="organizacion", cascade="all, delete-orphan")
    solicitudes_consentimiento = relationship("SolicitudConsentimiento", back_populates="organizacion", cascade="all, delete-orphan", foreign_keys="[SolicitudConsentimiento.organizacion_id]")
    logs_acceso = relationship("LogAccesoDatos", back_populates="organizacion", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Organizacion(rut={self.rut}, razon_social={self.razon_social})>"


class OrganizacionApiKey(Base):
    """
    API Keys para acceso programático de organizaciones
    - prefix: Formato "cl_ly_..." para identificación rápida
    - keyHash: SHA-256 de la key completa (nunca almacenar key en claro)
    """
    __tablename__ = "organizaciones_api_keys"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organizacion_id = Column(PGUUID(as_uuid=True), ForeignKey('organizaciones.id'), nullable=False)
    nombre = Column(String(100), nullable=False)
    prefix = Column(String(20), nullable=False)  # ej: "cl_ly_prod_..."
    key_hash = Column(String(64), unique=True, nullable=False)  # SHA-256
    activa = Column(Boolean, default=True, nullable=False)
    fecha_expiracion = Column(DateTime(timezone=True), nullable=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ultimo_uso = Column(DateTime(timezone=True), nullable=True)
    
    # Relaciones
    organizacion = relationship("Organizacion", back_populates="api_keys")
    
    def __repr__(self):
        return f"<OrganizacionApiKey(id={self.id}, prefix={self.prefix})>"


class AccesoOrganizacion(Base):
    """
    Registro de consentimiento/autorización otorgada por usuario a organización
    - receiptHash: Firma digital del pacto de consentimiento
    - categoriaDato: Tipos como SALUD, BIOMETRIA, FINACIERO, etc.
    """
    __tablename__ = "accesos_organizacion"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(PGUUID(as_uuid=True), ForeignKey('usuarios.id'), nullable=False)
    organizacion_id = Column(PGUUID(as_uuid=True), ForeignKey('organizaciones.id'), nullable=False)
    categoria_dato = Column(String(100), nullable=False)  # SALUD, BIOMETRIA, etc.
    finalidad = Column(Text, nullable=False)  # Uso específico declarado
    estado = Column(SQLEnum(EstadoPermiso), default=EstadoPermiso.ACTIVO, nullable=False)
    receipt_hash = Column(String(64), nullable=False)  # Firma digital del pacto
    fecha_otorgamiento = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    fecha_expiracion = Column(DateTime(timezone=True), nullable=True)
    fecha_revocacion = Column(DateTime(timezone=True), nullable=True)
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="accesos")
    organizacion = relationship("Organizacion", back_populates="accesos")
    
    def __repr__(self):
        return f"<AccesoOrganizacion(usuario={self.usuario_id}, org={self.organizacion_id}, estado={self.estado})>"


class SolicitudConsentimiento(Base):
    """
    Solicitud de consentimiento iniciada por organización o por portabilidad
    - proposalJson: Estructura granular de los permisos solicitados
    - aiFlag: Indica si fue generada/asistida por IA
    - requestType: NORMAL (nueva) o PORTABILIDAD (desde otra org)
    """
    __tablename__ = "solicitudes_consentimiento"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organizacion_id = Column(PGUUID(as_uuid=True), ForeignKey('organizaciones.id'), nullable=False)
    rut_ciudadano_hash = Column(String(64), nullable=False, index=True)
    estado = Column(SQLEnum(EstadoSolicitud), default=EstadoSolicitud.PENDIENTE, nullable=False)
    proposal_json = Column(JSON, nullable=False)  # Estructura granular de permisos
    ai_flag = Column(SQLEnum(AiFlag), default=AiFlag.NONE, nullable=False)
    texto_legal_presentado = Column(Text, nullable=False)
    request_type = Column(String(50), default="NORMAL", nullable=False)  # NORMAL, PORTABILIDAD
    source_organization_id = Column(PGUUID(as_uuid=True), ForeignKey('organizaciones.id'), nullable=True)
    fecha_solicitud = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    fecha_respuesta = Column(DateTime(timezone=True), nullable=True)
    ip_solicitud = Column(String(45), nullable=True)
    
    # Relaciones
    organizacion = relationship("Organizacion", foreign_keys=[organizacion_id], back_populates="solicitudes_consentimiento")
    source_organization = relationship("Organizacion", foreign_keys=[source_organization_id])
    
    def __repr__(self):
        return f"<SolicitudConsentimiento(id={self.id}, rut_hash={self.rut_ciudadano_hash[:16]}...)>"


class SolicitudArco(Base):
    """
    Solicitud de derechos ARCO (Acceso, Rectificación, Cancelación, Oposición)
    - tokenEvidenciaIdentidad: Hash de ClaveÚnica o Firma Electrónica
    - prorrogado: Indica si se extendió el plazo de respuesta
    - fechaLimiteRespuesta: Calculado según tipo (generalmente 10 días hábiles)
    """
    __tablename__ = "solicitudes_arco"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organizacion_id = Column(PGUUID(as_uuid=True), ForeignKey('organizaciones.id'), nullable=False)
    rut_ciudadano_hash = Column(String(64), nullable=False, index=True)
    tipo = Column(SQLEnum(TipoArco), nullable=False)
    estado = Column(SQLEnum(EstadoArco), default=EstadoArco.PENDIENTE, nullable=False)
    token_evidencia_identidad = Column(String(64), nullable=False)  # Hash ClaveÚnica/Firma
    prorrogado = Column(Boolean, default=False, nullable=False)
    descripcion = Column(Text, nullable=True)
    fecha_solicitud = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    fecha_limite_respuesta = Column(DateTime(timezone=True), nullable=False)
    fecha_respuesta = Column(DateTime(timezone=True), nullable=True)
    respuesta = Column(Text, nullable=True)
    
    # Relaciones
    organizacion = relationship("Organizacion", back_populates="solicitudes_arco")
    
    def __repr__(self):
        return f"<SolicitudArco(tipo={self.tipo}, estado={self.estado})>"


class LogAccesoDatos(Base):
    """
    Log de auditoría de accesos a datos personales
    Obligatorio según principio de accountability de Ley 21.719
    - justificacionLegal: Base legal del acceso (consentimiento, obligación legal, etc.)
    """
    __tablename__ = "logs_acceso_datos"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(PGUUID(as_uuid=True), ForeignKey('usuarios.id'), nullable=False)
    organizacion_id = Column(PGUUID(as_uuid=True), ForeignKey('organizaciones.id'), nullable=False)
    tipo_acceso = Column(SQLEnum(TipoAcceso), nullable=False)  # LECTURA, MODIFICACION, etc.
    categoria_dato_consultado = Column(String(100), nullable=False)
    justificacion_legal = Column(Text, nullable=False)
    ip_origen = Column(String(45), nullable=False)
    user_agent = Column(String(500), nullable=True)
    fecha_acceso = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    detalles_adicionales = Column(JSON, nullable=True)
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="logs_acceso")
    organizacion = relationship("Organizacion", back_populates="logs_acceso")
    
    def __repr__(self):
        return f"<LogAccesoDatos(usuario={self.usuario_id}, tipo={self.tipo_acceso}, fecha={self.fecha_acceso})>"
