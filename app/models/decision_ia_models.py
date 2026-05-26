"""
Modelos para oposición a decisiones automatizadas y perfilamiento (Art. 16 Ley 21.719)
Protección del ciudadano contra juicios exclusivamente algorítmicos.
"""
from sqlalchemy import Column, String, Boolean, ForeignKey, Text, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base
from datetime import datetime

class TipoDecisionAutomatizada(enum.Enum):
    CREDITICIO = "CREDITICIO"  # Scoring crediticio
    LABORAL = "LABORAL"  # Selección de personal
    SEGUROS = "SEGUROS"  # Cálculo de primas/riesgos
    PUBLICIDAD = "PUBLICIDAD"  # Perfilamiento publicitario
    SALUD = "SALUD"  # Diagnóstico o tratamiento automatizado
    OTRO = "OTRO"

class EstadoImpugnacion(enum.Enum):
    PENDIENTE = "PENDIENTE"
    EN_REVISION = "EN_REVISION"
    INTERVENCION_HUMANA_SOLICITADA = "INTERVENCION_HUMANA_SOLICITADA"
    RESUELTA_FAVORABLE = "RESUELTA_FAVORABLE"
    RESUELTA_DESFAVORABLE = "RESUELTA_DESFAVORABLE"
    RECHAZADA = "RECHAZADA"

class DecisionAutomatizada(Base):
    __tablename__ = "decisiones_automatizadas"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False, index=True)
    organizacion_id = Column(UUID(as_uuid=True), ForeignKey("organizaciones.id"), nullable=False, index=True)
    
    # Información de la decisión
    tipo_decision = Column(SQLEnum(TipoDecisionAutomatizada), nullable=False)
    descripcion_decision = Column(Text, nullable=False)  # Qué se decidió (ej: "Crédito denegado")
    
    # Algoritmo utilizado (transparencia Art. 16)
    algoritmo_nombre = Column(String, nullable=False)
    algoritmo_version = Column(String)
    algoritmo_descripcion = Column(Text)  # Explicación en lenguaje claro de cómo funciona
    factores_principales = Column(Text)  # Principales variables que incidieron en la decisión
    
    # Datos utilizados
    categorias_datos_utilizados = Column(Text)  # JSON array como texto: ["historial_crediticio", "ingresos"]
    fecha_decision = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Derechos del titular (Art. 16)
    derecho_impugnar_disponible = Column(Boolean, default=True)
    intervencion_humana_disponible = Column(Boolean, default=True)
    
    # Impugnación del ciudadano
    estado_impugnacion = Column(SQLEnum(EstadoImpugnacion), default=EstadoImpugnacion.PENDIENTE)
    fecha_impugnacion = Column(DateTime)
    motivo_impugnacion = Column(Text)
    solicitud_intervencion_humana = Column(Boolean, default=False)
    
    # Revisión humana
    revisor humano_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"))  # ID del revisor humano
    fecha_revision_humana = Column(DateTime)
    conclusion_revision = Column(Text)
    decision_final_modificada = Column(Boolean, default=False)
    nueva_decision_descripcion = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relaciones
    usuario = relationship("Usuario", foreign_keys=[usuario_id], back_populates="decisiones_automatizadas")
    organizacion = relationship("Organizacion", back_populates="decisiones_automatizadas")
    revisor = relationship("Usuario", foreign_keys=[revisor_humano_id])


# Nota: Se deben agregar las relaciones inversas en los modelos Usuario y Organizacion
# Esto se puede hacer dinámicamente o actualizando los modelos core
