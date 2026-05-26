"""
Panel DPO - Dashboard de Cumplimiento Normativo Ley 21.719
Métricas, alertas y reporting para el Delegado de Protección de Datos
"""
from datetime import datetime, timedelta
from typing import Dict, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.database import Base

class PanelDPOService:
    """Servicio para dashboard de cumplimiento del DPO"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def obtener_metricas_generales(self, organizacion_id: UUID) -> Dict:
        """Obtener métricas generales de cumplimiento"""
        # Importar modelos dinámicamente para evitar circular imports
        from app.services.rat_service import RegistroActividadesTratamiento
        from app.services.brechas_service import NotificacionBrecha, NivelRiesgo
        from app.services.eipd_service import EvaluacionImpactoProteccionDatos
        
        ahora = datetime.utcnow()
        
        # Total RAT
        rat_count = await self.db.execute(
            select(func.count(RegistroActividadesTratamiento.id))
            .where(RegistroActividadesTratamiento.organizacion_id == organizacion_id)
        )
        total_rat = rat_count.scalar() or 0
        
        # Brechas activas
        brechas_activas = await self.db.execute(
            select(func.count(NotificacionBrecha.id))
            .where(NotificacionBrecha.organizacion_id == organizacion_id)
            .where(NotificacionBrecha.estado.not_in(["CERRADA"]))
        )
        total_brechas_activas = brechas_activas.scalar() or 0
        
        # Brechas alto riesgo pendientes
        brechas_alto_riesgo = await self.db.execute(
            select(func.count(NotificacionBrecha.id))
            .where(NotificacionBrecha.organizacion_id == organizacion_id)
            .where(NotificacionBrecha.nivel_riesgo.in_(["ALTO", "MUY_ALTO"]))
            .where(NotificacionBrecha.estado.not_in(["CERRADA"]))
        )
        brechas_alto_riesgo_count = brechas_alto_riesgo.scalar() or 0
        
        # EIPD aprobadas vs pendientes
        eipd_aprobadas = await self.db.execute(
            select(func.count(EvaluacionImpactoProteccionDatos.id))
            .where(EvaluacionImpactoProteccionDatos.organizacion_id == organizacion_id)
            .where(EvaluacionImpactoProteccionDatos.estado == "APROBADA")
        )
        eipd_pendientes = await self.db.execute(
            select(func.count(EvaluacionImpactoProteccionDatos.id))
            .where(EvaluacionImpactoProteccionDatos.organizacion_id == organizacion_id)
            .where(EvaluacionImpactoProteccionDatos.estado.in_(["BORRADOR", "EN_REVISION", "REQUIERE_MITIGACION"]))
        )
        
        return {
            "fecha_consulta": ahora.isoformat(),
            "organizacion_id": str(organizacion_id),
            "rat": {
                "total_registros": total_rat,
                "estado": "COMPLETO" if total_rat > 0 else "PENDIENTE"
            },
            "brechas": {
                "activas": total_brechas_activas,
                "alto_riesgo": brechas_alto_riesgo_count,
                "requiere_atencion_inmediata": brechas_alto_riesgo_count > 0
            },
            "eipd": {
                "aprobadas": eipd_aprobadas.scalar() or 0,
                "pendientes": eipd_pendientes.scalar() or 0
            }
        }
    
    async def obtener_alertas_criticas(self, organizacion_id: UUID) -> List[Dict]:
        """Obtener alertas que requieren atención inmediata del DPO"""
        from app.services.brechas_service import NotificacionBrecha, EstadoNotificacion
        from app.services.eipd_service import EvaluacionImpactoProteccionDatos, EstadoEIPD
        
        alertas = []
        ahora = datetime.utcnow()
        
        # Alerta: Brechas fuera de plazo 72h
        brechas_fuera_plazo = await self.db.execute(
            select(NotificacionBrecha)
            .where(NotificacionBrecha.organizacion_id == organizacion_id)
            .where(NotificacionBrecha.cumple_plazo_72h == False)
            .where(NotificacionBrecha.estado != EstadoNotificacion.CERRADA)
        )
        for brecha in brechas_fuera_plazo.scalars().all():
            alertas.append({
                "tipo": "BRECHA_FUERA_PLAZO",
                "prioridad": "CRITICA",
                "id": str(brecha.id),
                "titulo": f"Brecha fuera de plazo 72h: {brecha.titulo}",
                "descripcion": f"Horas transcurridas: {brecha.horas_transcurridas}. Requiere justificación ante la Agencia.",
                "fecha_descubrimiento": brecha.fecha_descubrimiento.isoformat(),
                "accion_requerida": "Enviar notificación con justificación de retraso"
            })
        
        # Alerta: EIPD pendientes de aprobación
        eipd_pendientes = await self.db.execute(
            select(EvaluacionImpactoProteccionDatos)
            .where(EvaluacionImpactoProteccionDatos.organizacion_id == organizacion_id)
            .where(EvaluacionImpactoProteccionDatos.estado == EstadoEIPD.EN_REVISION)
        )
        for eipd in eipd_pendientes.scalars().all():
            alertas.append({
                "tipo": "EIPD_PENDIENTE_APROBACION",
                "prioridad": "ALTA",
                "id": str(eipd.id),
                "titulo": f"EIPD pendiente: {eipd.nombre_evaluacion}",
                "descripcion": "Evaluación de impacto requiere dictamen del DPO",
                "fecha_creacion": eipd.fecha_creacion.isoformat(),
                "accion_requerida": "Revisar y emitir dictamen"
            })
        
        # Alerta: EIPD con revisión vencida
        eipd_revision_vencida = await self.db.execute(
            select(EvaluacionImpactoProteccionDatos)
            .where(EvaluacionImpactoProteccionDatos.organizacion_id == organizacion_id)
            .where(EvaluacionImpactoProteccionDatos.estado == EstadoEIPD.APROBADA)
            .where(EvaluacionImpactoProteccionDatos.fecha_proxima_revision <= ahora)
        )
        for eipd in eipd_revision_vencida.scalars().all():
            alertas.append({
                "tipo": "EIPD_REVISION_VENCIDA",
                "prioridad": "MEDIA",
                "id": str(eipd.id),
                "titulo": f"EIPD requiere revisión: {eipd.nombre_evaluacion}",
                "descripcion": "La evaluación periódica está vencida",
                "fecha_vencimiento": eipd.fecha_proxima_revision.isoformat(),
                "accion_requerida": "Programar revisión periódica"
            })
        
        # Ordenar por prioridad
        prioridad_order = {"CRITICA": 0, "ALTA": 1, "MEDIA": 2, "BAJA": 3}
        alertas.sort(key=lambda x: prioridad_order.get(x["prioridad"], 4))
        
        return alertas
    
    async def generar_reporte_cumplimiento(self, organizacion_id: UUID, periodo_dias: int = 90) -> Dict:
        """Generar reporte completo de cumplimiento para la Agencia"""
        from app.services.rat_service import RegistroActividadesTratamiento, ServicioRAT
        from app.services.brechas_service import NotificacionBrecha, ServicioBrechas
        from app.services.eipd_service import EvaluacionImpactoProteccionDatos
        
        # Métricas generales
        metricas = await self.obtener_metricas_generales(organizacion_id)
        
        # Alertas
        alertas = await self.obtener_alertas_criticas(organizacion_id)
        
        # Estadísticas de brechas
        servicio_brechas = ServicioBrechas(self.db)
        estadisticas_brechas = await servicio_brechas.generar_estadisticas_brechas(organizacion_id, periodo_dias)
        
        # Resumen de EIPD
        eipd_result = await self.db.execute(
            select(EvaluacionImpactoProteccionDatos)
            .where(EvaluacionImpactoProteccionDatos.organizacion_id == organizacion_id)
            .order_by(EvaluacionImpactoProteccionDatos.fecha_creacion.desc())
            .limit(10)
        )
        eipd_recientes = [
            {
                "id": str(e.id),
                "nombre": e.nombre_evaluacion,
                "estado": e.estado.value,
                "nivel_riesgo": e.nivel_riesgo_inicial.value if e.nivel_riesgo_inicial else None,
                "fecha_creacion": e.fecha_creacion.isoformat()
            }
            for e in eipd_result.scalars().all()
        ]
        
        # Porcentaje de cumplimiento
        total_items = 4  # RAT, Brechas gestionadas, EIPD, Alertas atendidas
        items_cumplidos = 0
        
        if metricas["rat"]["total_registros"] > 0:
            items_cumplidos += 1
        
        if estadisticas_brechas["fuera_plazo_72h"] == 0:
            items_cumplidos += 1
        
        if metricas["eipd"]["pendientes"] == 0:
            items_cumplidos += 1
        
        if len([a for a in alertas if a["prioridad"] == "CRITICA"]) == 0:
            items_cumplidos += 1
        
        porcentaje_cumplimiento = (items_cumplidos / total_items) * 100
        
        return {
            "fecha_generacion": datetime.utcnow().isoformat(),
            "periodo_dias": periodo_dias,
            "organizacion_id": str(organizacion_id),
            "porcentaje_cumplimiento": round(porcentaje_cumplimiento, 2),
            "resumen_ejecutivo": {
                "estado_general": "CUMPLE" if porcentaje_cumplimiento >= 80 else "REQUIERE_ATENCION" if porcentaje_cumplimiento >= 50 else "CRITICO",
                "puntos_fortes": [],
                "areas_mejora": []
            },
            "metricas": metricas,
            "alertas_activas": alertas,
            "estadisticas_brechas": estadisticas_brechas,
            "eipd_recientes": eipd_recientes,
            "recomendaciones": self._generar_recomendaciones(metricas, alertas, estadisticas_brechas)
        }
    
    def _generar_recomendaciones(self, metricas: Dict, alertas: List, estadisticas_brechas: Dict) -> List[str]:
        """Generar recomendaciones basadas en el estado actual"""
        recomendaciones = []
        
        if metricas["rat"]["total_registros"] == 0:
            recomendaciones.append("⚠️ Crear Registro de Actividades de Tratamiento (RAT) - Obligatorio Art. 27")
        
        if estadisticas_brechas["fuera_plazo_72h"] > 0:
            recomendaciones.append(f"🚨 Regularizar {estadisticas_brechas['fuera_plazo_72h']} brechas fuera de plazo 72h")
        
        if metricas["brechas"]["alto_riesgo"] > 0:
            recomendaciones.append(f"🔴 Atender {metricas['brechas']['alto_riesgo']} brechas de alto riesgo pendientes")
        
        if metricas["eipd"]["pendientes"] > 0:
            recomendaciones.append(f"📋 Revisar {metricas['eipd']['pendientes']} EIPD pendientes de aprobación")
        
        criticas = [a for a in alertas if a["prioridad"] == "CRITICA"]
        if criticas:
            recomendaciones.append(f"❗ Atender {len(criticas)} alertas críticas inmediatamente")
        
        if not recomendaciones:
            recomendaciones.append("✅ Mantener prácticas actuales de cumplimiento normativo")
        
        return recomendaciones
    
    async def obtener_calendario_cumplimiento(self, organizacion_id: UUID, meses: int = 6) -> List[Dict]:
        """Obtener eventos próximos de cumplimiento"""
        from app.services.eipd_service import EvaluacionImpactoProteccionDatos, EstadoEIPD
        
        ahora = datetime.utcnow()
        fecha_limite = ahora + timedelta(days=meses * 30)
        
        eventos = []
        
        # EIPD con revisión próxima
        eipd_result = await self.db.execute(
            select(EvaluacionImpactoProteccionDatos)
            .where(EvaluacionImpactoProteccionDatos.organizacion_id == organizacion_id)
            .where(EvaluacionImpactoProteccionDatos.estado == EstadoEIPD.APROBADA)
            .where(EvaluacionImpactoProteccionDatos.fecha_proxima_revision <= fecha_limite)
            .where(EvaluacionImpactoProteccionDatos.fecha_proxima_revision >= ahora)
            .order_by(EvaluacionImpactoProteccionDatos.fecha_proxima_revision)
        )
        
        for eipd in eipd_result.scalars().all():
            eventos.append({
                "tipo": "REVISION_EIPD",
                "titulo": f"Revisión EIPD: {eipd.nombre_evaluacion}",
                "fecha": eipd.fecha_proxima_revision.isoformat(),
                "dias_restantes": (eipd.fecha_proxima_revision - ahora).days,
                "prioridad": "ALTA" if (eipd.fecha_proxima_revision - ahora).days < 15 else "MEDIA"
            })
        
        # Ordenar por fecha
        eventos.sort(key=lambda x: x["fecha"])
        
        return eventos
