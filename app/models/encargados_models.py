"""
Modelos para gestión de Encargados de Tratamiento y Terceros (Art. 28 LGPD / Ley 21.719)
Gestión de contratos de encargo y auditoría de subcontrataciones.
"""
from sqlalchemy import Column, String, Boolean, ForeignKey, Text, Date, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base
from datetime import date

class TipoEncargado(enum.Enum):
    CLOUD_PROVIDER = "CLOUD_PROVIDER"  # AWS, Azure, Google Cloud
    PROCESAMIENTO_DATOS = "PROCESAMIENTO_DATOS"  # Call centers, BPO
    PAGOS = "PAGOS"  # Pasarelas de pago
    ANALITICA = "ANALITICA"  # Servicios de analytics
    OTRO = "OTRO"

class EstadoContrato(enum.Enum):
    VIGENTE = "VIGENTE"
    VENCIDO = "VENCIDO"
    SUSPENDIDO = "SUSPENDIDO"
    TERMINADO = "TERMINADO"

class EncargadoTratamiento(Base):
    __tablename__ = "encargados_tratamiento"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    organizacion_id = Column(UUID(as_uuid=True), ForeignKey("organizaciones.id"), nullable=False, index=True)
    
    # Datos del Encargado
    rut_encargado = Column(String, nullable=False, index=True)  # RUT del tercero
    razon_social = Column(String, nullable=False)
    email_contacto = Column(String, nullable=False)
    pais_sede = Column(String, nullable=False)  # Para transferencias internacionales
    
    # Clasificación
    tipo_servicio = Column(SQLEnum(TipoEncargado), nullable=False)
    descripcion_servicio = Column(Text)
    
    # Contrato y Cumplimiento
    fecha_inicio_contrato = Column(Date, nullable=False)
    fecha_termino_contrato = Column(Date)
    estado_contrato = Column(SQLEnum(EstadoContrato), default=EstadoContrato.VIGENTE)
    
    # Cláusulas contractuales obligatorias (Art. 28)
    tiene_clausulas_confidencialidad = Column(Boolean, default=False)
    tiene_clausulas_seguridad = Column(Boolean, default=False)
    tiene_clausulas_borrado = Column(Boolean, default=False)
    permite_subcontratacion = Column(Boolean, default=False)
    
    # Auditoría
    ultima_auditoria_fecha = Column(Date)
    ultima_auditoria_resultado = Column(String)  # APROBADO, OBSERVADO, RECHAZADO
    medidas_seguridad_descripcion = Column(Text)
    
    # Metadata
    created_at = Column(Date, nullable=False)
    updated_at = Column(Date)

    # Relaciones
    organizacion = relationship("Organizacion", back_populates="encargados")
    subcontrataciones = relationship("Subcontratacion", back_populates="encargado", cascade="all, delete-orphan")


class Subcontratacion(Base):
    """Registro de subcontratados por el Encargado (requiere autorización expresa)"""
    __tablename__ = "subcontrataciones"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    encargado_id = Column(UUID(as_uuid=True), ForeignKey("encargados_tratamiento.id"), nullable=False)
    
    nombre_subcontratado = Column(String, nullable=False)
    rut_subcontratado = Column(String)
    servicio_especifico = Column(String, nullable=False)
    pais_operacion = Column(String, nullable=False)
    
    autorizado_por_org = Column(Boolean, default=False)  # La organización dueña de los datos debe autorizar
    fecha_autorizacion = Column(Date)
    
    encargado = relationship("EncargadoTratamiento", back_populates="subcontrataciones")

# Actualizar modelo Organizacion para incluir relación
# Nota: Esto se haría en app/models/core_models.py si existiera, 
# pero lo manejaremos vía relación dinámica en los servicios si es necesario.
