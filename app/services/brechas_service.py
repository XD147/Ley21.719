"""
Servicio de Notificación de Brechas de Seguridad
Cumplimiento Art. 38-40 Ley 21.719 (Notificación 72h)
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import Base
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text, Enum as SQLEnum, JSON, Integer, Integer
from sqlalchemy.dialects.postgresql import UUID as PGUUID
import enum
import httpx

class TipoBrecha(str, enum.Enum):
    ACCESO_NO_AUTORIZADO = "ACCESO_NO_AUTORIZADO"
    PERDIDA_CONFIDENCIALIDAD = "PERDIDA_CONFIDENCIALIDAD"
    PERDIDA_INTEGRIDAD = "PERDIDA_INTEGRIDAD"
    PERDIDA_DISPONIBILIDAD = "PERDIDA_DISPONIBILIDAD"
    ELIMINACION_ACCIDENTAL = "ELIMINACION_ACCIDENTAL"

class NivelRiesgo(str, enum.Enum):
    BAJO = "BAJO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"
    MUY_ALTO = "MUY_ALTO"

class EstadoNotificacion(str, enum.Enum):
    BORRADOR = "BORRADOR"
    ENVIADA_AGENCIA = "ENVIADA_AGENCIA"
    ENVIADA_AFECTADOS = "ENVIADA_AFECTADOS"
    CERRADA = "CERRADA"
    REQUERIDA_INFO_ADICIONAL = "REQUERIDA_INFO_ADICIONAL"

class NotificacionBrecha(Base):
    __tablename__ = "notificaciones_brechas"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=func.gen_random_uuid())
    organizacion_id = Column(PGUUID(as_uuid=True), ForeignKey("organizaciones.id"), nullable=False, index=True)
    
    # Información básica
    titulo = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=False)
    tipo_brecha = Column(SQLEnum(TipoBrecha), nullable=False)
    nivel_riesgo = Column(SQLEnum(NivelRiesgo), nullable=False)
    
    # Fechas críticas
    fecha_descubrimiento = Column(DateTime, nullable=False)
    fecha_notificacion_agencia = Column(DateTime)  # Debe ser <= 72h desde descubrimiento
    fecha_notificacion_afectados = Column(DateTime)
    
    # Plazo legal
    horas_transcurridas = Column(Integer)  # Calculado al crear
    cumple_plazo_72h = Column(Boolean)
    
    # Datos afectados
    categorias_datos_afectados = Column(JSON)  # Lista de categorías
    numero_aproximado_afectados = Column(Integer)
    criterios_determinar_afectados = Column(Text)
    
    # Causas y consecuencias
    causas_brecha = Column(Text)
    consecuencias_probables = Column(Text)
    medidas_mitigacion = Column(JSON)  # Lista de medidas tomadas
    
    # Contacto DPO
    nombre_dpo = Column(String(200))
    email_dpo = Column(String(200))
    telefono_dpo = Column(String(50))
    
    # Evidencia
    evidencia_adjunta = Column(JSON)  # URLs o hashes de documentos
    informe_tecnico = Column(Text)
    
    # Estado y seguimiento
    estado = Column(SQLEnum(EstadoNotificacion), default=EstadoNotificacion.BORRADOR)
    comentarios_agencia = Column(Text)
    fecha_cierre = Column(DateTime)
    
    # Auditoría
    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False)
    fecha_actualizacion = Column(DateTime, onupdate=datetime.utcnow)
    creado_por = Column(String(200))


class ServicioBrechas:
    AGENCIA_PROTECCION_DATOS_URL = "https://api.agenciaprotecciondatos.cl/brechas"  # URL ficticia
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def crear_brecha(self, data: dict, organizacion_id: UUID) -> NotificacionBrecha:
        """Crear nueva notificación de brecha con cálculo automático de plazo 72h"""
        fecha_descubrimiento = datetime.fromisoformat(data["fecha_descubrimiento"]) if isinstance(data["fecha_descubrimiento"], str) else data["fecha_descubrimiento"]
        ahora = datetime.utcnow()
        horas_transcurridas = int((ahora - fecha_descubrimiento).total_seconds() / 3600)
        
        brecha = NotificacionBrecha(
            organizacion_id=organizacion_id,
            horas_transcurridas=horas_transcurridas,
            cumple_plazo_72h=horas_transcurridas <= 72,
            **{k: v for k, v in data.items() if k != "fecha_descubrimiento"}
        )
        brecha.fecha_descubrimiento = fecha_descubrimiento
        
        self.db.add(brecha)
        await self.db.commit()
        await self.db.refresh(brecha)
        
        return brecha
    
    async def obtener_brechas_pendientes(self, organizacion_id: UUID) -> List[NotificacionBrecha]:
        """Obtener brechas que requieren atención"""
        result = await self.db.execute(
            select(NotificacionBrecha)
            .where(NotificacionBrecha.organizacion_id == organizacion_id)
            .where(NotificacionBrecha.estado.not_in([EstadoNotificacion.CERRADA]))
            .order_by(NotificacionBrecha.fecha_descubrimiento.desc())
        )
        return list(result.scalars().all())
    
    async def marcar_enviada_agencia(self, brecha_id: UUID) -> Optional[NotificacionBrecha]:
        """Marcar brecha como enviada a la Agencia"""
        result = await self.db.execute(
            select(NotificacionBrecha)
            .where(NotificacionBrecha.id == brecha_id)
        )
        brecha = result.scalar_one_or_none()
        
        if not brecha:
            return None
        
        brecha.fecha_notificacion_agencia = datetime.utcnow()
        brecha.estado = EstadoNotificacion.ENVIADA_AGENCIA
        await self.db.commit()
        await self.db.refresh(brecha)
        
        return brecha
    
    async def notificar_agencia(self, brecha_id: UUID) -> Dict:
        """Enviar notificación formal a la Agencia de Protección de Datos"""
        result = await self.db.execute(
            select(NotificacionBrecha)
            .where(NotificacionBrecha.id == brecha_id)
        )
        brecha = result.scalar_one_or_none()
        
        if not brecha:
            return {"error": "Brecha no encontrada"}
        
        if not brecha.cumple_plazo_72h:
            return {
                "advertencia": "Fuera de plazo 72h",
                "horas_transcurridas": brecha.horas_transcurridas,
                "justificacion_requerida": True
            }
        
        # Preparar payload para API Agencia
        payload = {
            "organizacion_rut": brecha.organizacion_id,
            "tipo_brecha": brecha.tipo_brecha.value,
            "nivel_riesgo": brecha.nivel_riesgo.value,
            "fecha_descubrimiento": brecha.fecha_descubrimiento.isoformat(),
            "descripcion": brecha.descripcion,
            "afectados_aproximados": brecha.numero_aproximado_afectados,
            "medidas_mitigacion": brecha.medidas_mitigacion,
            "contacto_dpo": {
                "nombre": brecha.nombre_dpo,
                "email": brecha.email_dpo
            }
        }
        
        # Simular envío a Agencia (en producción usar httpx real)
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(self.AGENCIA_PROTECCION_DATOS_URL, json=payload)
        
        # Marcar como enviada
        brecha.fecha_notificacion_agencia = datetime.utcnow()
        brecha.estado = EstadoNotificacion.ENVIADA_AGENCIA
        await self.db.commit()
        
        return {
            "exitoso": True,
            "fecha_notificacion": brecha.fecha_notificacion_agencia.isoformat(),
            "numero_seguimiento": str(brecha.id)[:8].upper()
        }
    
    async def notificar_afectados(self, brecha_id: UUID, plantilla: str) -> Dict:
        """Notificar a los afectados cuando el riesgo es alto"""
        result = await self.db.execute(
            select(NotificacionBrecha)
            .where(NotificacionBrecha.id == brecha_id)
        )
        brecha = result.scalar_one_or_none()
        
        if not brecha:
            return {"error": "Brecha no encontrada"}
        
        if brecha.nivel_riesgo not in [NivelRiesgo.ALTO, NivelRiesgo.MUY_ALTO]:
            return {"info": "Notificación a afectados no requerida para este nivel de riesgo"}
        
        # Generar lista de afectados (en producción integrar con sistema de notificaciones)
        afectados = {
            "numero_total": brecha.numero_aproximado_afectados,
            "categorias": brecha.categorias_datos_afectados,
            "plantilla_utilizada": plantilla,
            "fecha_notificacion": datetime.utcnow().isoformat()
        }
        
        brecha.fecha_notificacion_afectados = datetime.utcnow()
        brecha.estado = EstadoNotificacion.ENVIADA_AFECTADOS
        await self.db.commit()
        
        return {
            "exitoso": True,
            "afectados_notificados": afectados
        }
    
    async def cerrar_brecha(self, brecha_id: UUID, comentarios: str = "") -> Optional[NotificacionBrecha]:
        """Cerrar notificación de brecha"""
        result = await self.db.execute(
            select(NotificacionBrecha)
            .where(NotificacionBrecha.id == brecha_id)
        )
        brecha = result.scalar_one_or_none()
        
        if not brecha:
            return None
        
        brecha.estado = EstadoNotificacion.CERRADA
        brecha.fecha_cierre = datetime.utcnow()
        brecha.comentarios_agencia = comentarios
        await self.db.commit()
        await self.db.refresh(brecha)
        
        return brecha
    
    async def generar_estadisticas_brechas(self, organizacion_id: UUID, periodo_dias: int = 365) -> Dict:
        """Generar estadísticas de brechas para reporting"""
        fecha_desde = datetime.utcnow() - timedelta(days=periodo_dias)
        
        result = await self.db.execute(
            select(NotificacionBrecha)
            .where(NotificacionBrecha.organizacion_id == organizacion_id)
            .where(NotificacionBrecha.fecha_descubrimiento >= fecha_desde)
        )
        brechas = list(result.scalars().all())
        
        estadisticas = {
            "periodo_dias": periodo_dias,
            "total_brechas": len(brechas),
            "por_tipo": {},
            "por_nivel_riesgo": {},
            "fuera_plazo_72h": 0,
            "notificadas_agencia": 0,
            "notificadas_afectados": 0,
            "tiempo_promedio_respuesta_horas": 0
        }
        
        tiempos_respuesta = []
        
        for brecha in brechas:
            # Por tipo
            tipo = brecha.tipo_brecha.value
            estadisticas["por_tipo"][tipo] = estadisticas["por_tipo"].get(tipo, 0) + 1
            
            # Por nivel
            nivel = brecha.nivel_riesgo.value
            estadisticas["por_nivel_riesgo"][nivel] = estadisticas["por_nivel_riesgo"].get(nivel, 0) + 1
            
            # Fuera de plazo
            if not brecha.cumple_plazo_72h:
                estadisticas["fuera_plazo_72h"] += 1
            
            # Notificadas
            if brecha.fecha_notificacion_agencia:
                estadisticas["notificadas_agencia"] += 1
                tiempos_respuesta.append(brecha.horas_transcurridas)
            
            if brecha.fecha_notificacion_afectados:
                estadisticas["notificadas_afectados"] += 1
        
        if tiempos_respuesta:
            estadisticas["tiempo_promedio_respuesta_horas"] = sum(tiempos_respuesta) / len(tiempos_respuesta)
        
        return estadisticas
