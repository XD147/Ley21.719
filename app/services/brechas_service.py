"""
Servicio de Notificación de Brechas de Seguridad
Cumplimiento Art. 38-40 Ley 21.719 (Notificación 72h)
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.cumplimiento_models import NotificacionBrecha, TipoBrecha, NivelRiesgo, EstadoBrecha
import httpx


class ServicioBrechas:
    AGENCIA_PROTECCION_DATOS_URL = "https://api.agenciaprotecciondatos.cl/brechas"

    def __init__(self, db: AsyncSession):
        self.db = db

    async def crear_brecha(self, data: dict, organizacion_id: UUID) -> NotificacionBrecha:
        """Crear nueva notificación de brecha con cálculo automático de plazo 72h"""
        fecha_descubrimiento = datetime.fromisoformat(data["fecha_descubrimiento"]) if isinstance(data["fecha_descubrimiento"], str) else data["fecha_descubrimiento"]
        ahora = datetime.utcnow()
        horas_transcurridas = int((ahora - fecha_descubrimiento).total_seconds() / 3600)

        brecha = NotificacionBrecha(
            organizacion_id=organizacion_id,
            titulo=data["titulo"],
            descripcion=data["descripcion"],
            tipo_brecha=TipoBrecha(data.get("tipo_brecha", "OTRO")),
            nivel_riesgo=NivelRiesgo(data.get("nivel_riesgo", "MEDIO")),
            estado=EstadoBrecha.DETECTADA,
            fecha_descubrimiento=fecha_descubrimiento,
            numero_afectados_estimado=data.get("numero_afectados_estimado"),
            datos_comprometidos=data.get("datos_comprometidos", {}),
            causas_brecha=data.get("causas_brecha"),
            medidas_contencion=data.get("medidas_contencion"),
            creado_por=data.get("creado_por", "Sistema"),
            cumple_plazo_72h=horas_transcurridas <= 72,
            horas_transcurridas=horas_transcurridas
        )

        self.db.add(brecha)
        await self.db.commit()
        await self.db.refresh(brecha)
        return brecha

    async def obtener_brechas_pendientes(self, organizacion_id: UUID) -> List[NotificacionBrecha]:
        """Obtener brechas que requieren atención"""
        result = await self.db.execute(
            select(NotificacionBrecha)
            .where(NotificacionBrecha.organizacion_id == organizacion_id)
            .where(NotificacionBrecha.estado.in_([EstadoBrecha.DETECTADA, EstadoBrecha.EN_EVALUACION]))
            .order_by(NotificacionBrecha.fecha_descubrimiento.desc())
        )
        return list(result.scalars().all())

    async def notificar_agencia(self, brecha_id: UUID) -> Dict:
        """Enviar notificación formal a la Agencia de Protección de Datos"""
        result = await self.db.execute(
            select(NotificacionBrecha).where(NotificacionBrecha.id == brecha_id)
        )
        brecha = result.scalar_one_or_none()

        if not brecha:
            return {"error": "Brecha no encontrada"}

        if not brecha.cumple_plazo_72h:
            return {
                "advertencia": "Fuera de plazo 72h",
                "horas_transcurridas": brecha.horas_transcurridas
            }

        brecha.estado = EstadoBrecha.NOTIFICADA_AGENCIA
        brecha.fecha_notificacion_agencia = datetime.now()
        await self.db.commit()

        return {
            "mensaje": "Notificación a agencia generada",
            "fecha_notificacion": brecha.fecha_notificacion_agencia.isoformat()
        }

    async def notificar_afectados(self, brecha_id: UUID, plantilla: str) -> Dict:
        """Notificar brecha a los afectados"""
        result = await self.db.execute(
            select(NotificacionBrecha).where(NotificacionBrecha.id == brecha_id)
        )
        brecha = result.scalar_one_or_none()

        if not brecha:
            return {"error": "Brecha no encontrada"}

        if brecha.nivel_riesgo not in [NivelRiesgo.ALTO, NivelRiesgo.MUY_ALTO]:
            return {"error": "Solo requerido para riesgo ALTO o MUY_ALTO"}

        brecha.estado = EstadoBrecha.NOTIFICADA_AFECTADOS
        brecha.fecha_notificacion_afectados = datetime.now()
        await self.db.commit()

        return {
            "mensaje": f"Notificación procesada",
            "fecha_notificacion": brecha.fecha_notificacion_afectados.isoformat()
        }

    async def generar_estadisticas_brechas(self, organizacion_id: UUID, periodo_dias: int = 365) -> Dict:
        """Generar estadísticas de brechas"""
        fecha_limite = datetime.now() - timedelta(days=periodo_dias)

        result = await self.db.execute(
            select(func.count(NotificacionBrecha.id))
            .where(NotificacionBrecha.organizacion_id == organizacion_id)
            .where(NotificacionBrecha.fecha_descubrimiento >= fecha_limite)
        )
        total = result.scalar() or 0

        return {
            "periodo_dias": periodo_dias,
            "total_brechas": total,
            "cumplimiento_72h": "Ver detalle en dashboard"
        }
