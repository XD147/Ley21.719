"""
Modelos adicionales para cumplimiento completo Ley 21.719
- Gestión de Brechas de Seguridad
- Registro Actividades Tratamiento (RAT)
- Evaluaciones de Impacto (EIPD)
- Ciclo de Vida y Retención de Datos
- Portabilidad de Datos
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Text, Integer, Float
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSON, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.database import Base


# ==================== ENUMS ADICIONALES ====================

class TipoBrecha(str, enum.Enum):
    ACCESO_NO_AUTORIZADO = "ACCESO_NO_AUTORIZADO"
    PERDIDA_DATOS = "PERDIDA_DATOS"
    MODIFICACION_NO_AUTORIZADA = "MODIFICACION_NO_AUTORIZADA"
    ELIMINACION_ACCIDENTAL = "ELIMINACION_ACCIDENTAL"
    FILTRACION_INTENCIONAL = "FILTRACION_INTENCIONAL"
    RANSOMWARE = "RANSOMWARE"
    OTRO = "OTRO"


class NivelRiesgo(str, enum.Enum):
    BAJO = "BAJO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"
    MUY_ALTO = "MUY_ALTO"


class EstadoBrecha(str, enum.Enum):
    DETECTADA = "DETECTADA"
    EN_EVALUACION = "EN_EVALUACION"
    NOTIFICADA_AGENCIA = "NOTIFICADA_AGENCIA"
    NOTIFICADA_AFECTADOS = "NOTIFICADA_AFECTADOS"
    CONTENIDA = "CONTENIDA"
    CERRADA = "CERRADA"


class FinalidadTratamiento(str, enum.Enum):
    CONSENTIMIENTO = "CONSENTIMIENTO"
    CONTRATO = "CONTRATO"
    OBLIGACION_LEGAL = "OBLIGACION_LEGAL"
    INTERES_VITAL = "INTERES_VITAL"
    INTERES_PUBLICO = "INTERES_PUBLICO"
    INTERES_LEGITIMO = "INTERES_LEGITIMO"


class EstadoEIPD(str, enum.Enum):
    BORRADOR = "BORRADOR"
    EN_REVISION = "EN_REVISION"
    APROBADA = "APROBADA"
    RECHAZADA = "RECHAZADA"
    IMPLEMENTADA = "IMPLEMENTADA"
    ARCHIVADA = "ARCHIVADA"


class TipoEventoWebhook(str, enum.Enum):
    CONSENTIMIENTO_OTORGADO = "CONSENTIMIENTO_OTORGADO"
    CONSENTIMIENTO_REVOCADO = "CONSENTIMIENTO_REVOCADO"
    SOLICITUD_ARCO_RECIBIDA = "SOLICITUD_ARCO_RECIBIDA"
    SOLICITUD_ARCO_RESUELTA = "SOLICITUD_ARCO_RESUELTA"
    BRECHA_SEGURIDAD = "BRECHA_SEGURIDAD"
    VENCIMIENTO_CONSENTIMIENTO = "VENCIMIENTO_CONSENTIMIENTO"
    ELIMINACION_AUTOMATICA = "ELIMINACION_AUTOMATICA"


class EstadoWebhook(str, enum.Enum):
    PENDIENTE = "PENDIENTE"
    ENVIADO = "ENVIADO"
    FALLIDO = "FALLIDO"
    REENVIADO = "REENVIADO"


# ==================== MODELOS DE CUMPLIMIENTO ====================

class RegistroActividadesTratamiento(Base):
    """
    Registro de Actividades de Tratamiento (RAT) - Art. 27 Ley 21.719
    Obligatorio para todas las organizaciones
    """
    __tablename__ = "registros_actividades_tratamiento"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organizacion_id = Column(PGUUID(as_uuid=True), ForeignKey('organizaciones.id'), nullable=False)
    nombre_actividad = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=False)
    finalidad = Column(SQLEnum(FinalidadTratamiento), nullable=False)
    categorias_datos = Column(JSONB, nullable=False)  # ["salud", "biometria", "financiero"]
    categorias_titulares = Column(JSONB, nullable=False)  # ["clientes", "empleados", "proveedores"]
    plazo_conservacion_dias = Column(Integer, nullable=False)
    medidas_seguridad = Column(JSONB, nullable=True)  # {"encriptacion": true, "acceso_restringido": true}
    encargados_tratamiento = Column(JSONB, nullable=True)  # Lista de terceros encargados
    tiene_transferencia_internacional = Column(Boolean, default=False, nullable=False)
    paises_transferencia = Column(JSONB, nullable=True)  # ["USA", "UE"]
    base_legal = Column(Text, nullable=False)
    responsable_registro = Column(String(255), nullable=False)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    fecha_actualizacion = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relaciones
    organizacion = relationship("Organizacion", backref="registros_rat")
    
    def __repr__(self):
        return f"<Registro RAT(id={self.id}, actividad={self.nombre_actividad})>"


class NotificacionBrecha(Base):
    """
    Notificación de Brecha de Seguridad - Art. 38-40 Ley 21.719
    Debe notificarse en máximo 72 horas a la Agencia y afectados
    """
    __tablename__ = "notificaciones_brechas"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organizacion_id = Column(PGUUID(as_uuid=True), ForeignKey('organizaciones.id'), nullable=False)
    titulo = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=False)
    tipo_brecha = Column(SQLEnum(TipoBrecha), nullable=False)
    nivel_riesgo = Column(SQLEnum(NivelRiesgo), nullable=False)
    estado = Column(SQLEnum(EstadoBrecha), default=EstadoBrecha.DETECTADA, nullable=False)
    fecha_descubrimiento = Column(DateTime(timezone=True), nullable=False)
    fecha_notificacion_agencia = Column(DateTime(timezone=True), nullable=True)
    fecha_notificacion_afectados = Column(DateTime(timezone=True), nullable=True)
    numero_afectados_estimado = Column(Integer, nullable=True)
    datos_comprometidos = Column(JSONB, nullable=False)  # {"categorias": ["rut", "email"], "volumen": 1000}
    causas_brecha = Column(Text, nullable=True)
    medidas_contencion = Column(Text, nullable=True)
    creado_por = Column(String(255), nullable=False)
    cumple_plazo_72h = Column(Boolean, default=True, nullable=False)
    horas_transcurridas = Column(Float, nullable=True)
    fecha_cierre = Column(DateTime(timezone=True), nullable=True)
    
    # Relaciones
    organizacion = relationship("Organizacion", backref="brechas_seguridad")
    
    def __repr__(self):
        return f"<NotificacionBrecha(id={self.id}, titulo={self.titulo}, riesgo={self.nivel_riesgo})>"


class EvaluacionImpactoProteccionDatos(Base):
    """
    Evaluación de Impacto en Protección de Datos (EIPD/DPIA) - Art. 34
    Obligatoria para tratamientos de alto riesgo
    """
    __tablename__ = "evaluaciones_impacto_proteccion_datos"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organizacion_id = Column(PGUUID(as_uuid=True), ForeignKey('organizaciones.id'), nullable=False)
    nombre_evaluacion = Column(String(255), nullable=False)
    descripcion_procesamiento = Column(Text, nullable=False)
    necesidad_proporcionalidad = Column(Text, nullable=False)
    riesgos_identificados = Column(JSONB, nullable=False)  # [{"riesgo": "...", "probabilidad": "alta"}]
    nivel_riesgo_inicial = Column(SQLEnum(NivelRiesgo), nullable=False)
    medidas_salvaguarda = Column(JSONB, nullable=True)
    nivel_riesgo_residual = Column(SQLEnum(NivelRiesgo), nullable=True)
    requiere_eipd_obligatoria = Column(Boolean, default=False, nullable=False)
    estado = Column(SQLEnum(EstadoEIPD), default=EstadoEIPD.BORRADOR, nullable=False)
    consulta_previa_required = Column(Boolean, default=False, nullable=False)  # Si riesgo residual es muy alto
    dpo_dictamen = Column(Text, nullable=True)
    dpo_nombre = Column(String(255), nullable=True)
    fecha_aprobacion = Column(DateTime(timezone=True), nullable=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    fecha_revision = Column(DateTime(timezone=True), nullable=True)
    
    # Relaciones
    organizacion = relationship("Organizacion", backref="evaluaciones_eipd")
    
    def __repr__(self):
        return f"<EIPD(id={self.id}, nombre={self.nombre_evaluacion}, estado={self.estado})>"


class WebhookRegistro(Base):
    """
    Registro de eventos webhook enviados a organizaciones
    Para notificaciones automáticas de eventos críticos
    """
    __tablename__ = "webhooks_registros"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organizacion_id = Column(PGUUID(as_uuid=True), ForeignKey('organizaciones.id'), nullable=False)
    tipo_evento = Column(SQLEnum(TipoEventoWebhook), nullable=False)
    estado = Column(SQLEnum(EstadoWebhook), default=EstadoWebhook.PENDIENTE, nullable=False)
    url_destino = Column(String(500), nullable=False)
    payload = Column(JSONB, nullable=False)
    respuesta_http = Column(Integer, nullable=True)
    cuerpo_respuesta = Column(Text, nullable=True)
    intentos = Column(Integer, default=0, nullable=False)
    max_intentos = Column(Integer, default=3, nullable=False)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    fecha_envio = Column(DateTime(timezone=True), nullable=True)
    fecha_proximo_intento = Column(DateTime(timezone=True), nullable=True)
    error_mensaje = Column(Text, nullable=True)
    
    # Relaciones
    organizacion = relationship("Organizacion", backref="webhooks_enviados")
    
    def __repr__(self):
        return f"<WebhookRegistro(id={self.id}, tipo={self.tipo_evento}, estado={self.estado})>"


class PoliticaRetencionDatos(Base):
    """
    Políticas de retención y eliminación automática de datos
    Implementa principio de limitación de conservación
    """
    __tablename__ = "politicas_retencion_datos"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organizacion_id = Column(PGUUID(as_uuid=True), ForeignKey('organizaciones.id'), nullable=False)
    nombre_politica = Column(String(255), nullable=False)
    categoria_dato = Column(String(100), nullable=False)
    plazo_retencion_dias = Column(Integer, nullable=False)
    criterio_inicio_plazo = Column(String(255), nullable=False)  # "fecha_registro", "ultima_interaccion", etc.
    accion_post_plazo = Column(String(50), nullable=False)  # "ELIMINAR", "ANONIMIZAR", "BLOQUEAR"
    excepciones = Column(JSONB, nullable=True)  # Casos donde no aplica eliminación
    activa = Column(Boolean, default=True, nullable=False)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    fecha_ultima_ejecucion = Column(DateTime(timezone=True), nullable=True)
    registros_eliminados_total = Column(Integer, default=0, nullable=False)
    
    # Relaciones
    organizacion = relationship("Organizacion", backref="politicas_retencion")
    
    def __repr__(self):
        return f"<PoliticaRetencion(id={self.id}, nombre={self.nombre_politica})>"


class EjecucionEliminacionAutomatica(Base):
    """
    Log de ejecuciones de eliminación/anonimización automática
    Para auditoría del ciclo de vida de datos
    """
    __tablename__ = "ejecuciones_eliminacion_automatica"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    politica_id = Column(PGUUID(as_uuid=True), ForeignKey('politicas_retencion_datos.id'), nullable=False)
    organizacion_id = Column(PGUUID(as_uuid=True), ForeignKey('organizaciones.id'), nullable=False)
    fecha_ejecucion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    registros_procesados = Column(Integer, nullable=False)
    registros_eliminados = Column(Integer, default=0, nullable=False)
    registros_anonimizados = Column(Integer, default=0, nullable=False)
    registros_bloqueados = Column(Integer, default=0, nullable=False)
    errores_encontrados = Column(Integer, default=0, nullable=False)
    detalle_errores = Column(JSONB, nullable=True)
    duracion_segundos = Column(Float, nullable=True)
    
    # Relaciones
    politica = relationship("PoliticaRetencionDatos", backref="ejecuciones")
    organizacion = relationship("Organizacion")
    
    def __repr__(self):
        return f"<EjecucionEliminacion(id={self.id}, procesados={self.registros_procesados})>"


class ExportacionPortabilidad(Base):
    """
    Registro de exportaciones de portabilidad de datos
    Derecho a recibir datos en formato estructurado
    """
    __tablename__ = "exportaciones_portabilidad"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(PGUUID(as_uuid=True), ForeignKey('usuarios.id'), nullable=False)
    organizacion_id = Column(PGUUID(as_uuid=True), ForeignKey('organizaciones.id'), nullable=False)
    formato_exportacion = Column(String(20), nullable=False)  # JSON, XML, CSV
    categorias_incluidas = Column(JSONB, nullable=False)
    estado = Column(String(50), default="GENERANDO", nullable=False)  # GENERANDO, LISTO, DESCARGADO, EXPIRADO
    url_descarga_temporal = Column(String(500), nullable=True)
    token_acceso = Column(String(64), nullable=True)  # Hash para descarga segura
    fecha_solicitud = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    fecha_generacion = Column(DateTime(timezone=True), nullable=True)
    fecha_expiracion_url = Column(DateTime(timezone=True), nullable=True)
    tamaño_archivo_bytes = Column(Integer, nullable=True)
    hash_verificacion = Column(String(64), nullable=True)  # SHA-256 del archivo
    
    # Relaciones
    usuario = relationship("Usuario")
    organizacion = relationship("Organizacion")
    
    def __repr__(self):
        return f"<ExportacionPortabilidad(id={self.id}, formato={self.formato_exportacion})>"


class TraduccionLegalDesign(Base):
    """
    Traducciones de lenguaje legal a lenguaje ciudadano
    Para mejorar comprensión de consentimientos
    """
    __tablename__ = "traducciones_legal_design"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organizacion_id = Column(PGUUID(as_uuid=True), ForeignKey('organizaciones.id'), nullable=False)
    texto_legal_original = Column(Text, nullable=False)
    texto_ciudadano = Column(Text, nullable=False)
    categoria = Column(String(100), nullable=False)  # "finalidad", "derechos", "retencion"
    icono_sugerido = Column(String(50), nullable=True)
    nivel_simplificacion = Column(String(20), default="BASICO")  # BASICO, INTERMEDIO, AVANZADO
    validado_dpo = Column(Boolean, default=False, nullable=False)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relaciones
    organizacion = relationship("Organizacion")
    
    def __repr__(self):
        return f"<TraduccionLegalDesign(id={self.id}, categoria={self.categoria})>"
