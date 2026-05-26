"""
Servicio de Evaluación de Impacto en Protección de Datos (EIPD)
Cumplimiento Art. 34 Ley 21.719
"""
from datetime import datetime
from typing import List, Optional, Dict
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.cumplimiento_models import EvaluacionImpactoProteccionDatos, EstadoEIPD, NivelRiesgo


class ServicioEIPD:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def crear_evaluacion(self, data: dict) -> EvaluacionImpactoProteccionDatos:
        """Crear nueva EIPD"""
        evaluacion = EvaluacionImpactoProteccionDatos(
            organizacion_id=data["organizacion_id"],
            nombre_evaluacion=data["nombre_evaluacion"],
            descripcion_procesamiento=data.get("descripcion", ""),
            necesidad_proporcionalidad=data.get("necesidad_proporcionalidad", ""),
            riesgos_identificados=data.get("riesgos", []),
            nivel_riesgo_inicial=NivelRiesgo(data.get("nivel_riesgo_inicial", "MEDIO")),
            medidas_salvaguarda=data.get("medidas", []),
            requiere_eipd_obligatoria=data.get("requiere_obligatoria", False)
        )
        
        self.db.add(evaluacion)
        await self.db.commit()
        await self.db.refresh(evaluacion)
        return evaluacion

    async def generar_reporte_eipd(self, eipd_id: UUID) -> Dict:
        """Generar reporte completo de EIPD"""
        result = await self.db.execute(
            select(EvaluacionImpactoProteccionDatos).where(EvaluacionImpactoProteccionDatos.id == eipd_id)
        )
        eipd = result.scalar_one_or_none()
        
        if not eipd:
            return {"error": "EIPD no encontrada"}
        
        return {
            "id": str(eipd.id),
            "nombre": eipd.nombre_evaluacion,
            "estado": eipd.estado.value,
            "nivel_riesgo_inicial": eipd.nivel_riesgo_inicial.value,
            "nivel_riesgo_residual": eipd.nivel_riesgo_residual.value if eipd.nivel_riesgo_residual else None,
            "dictamen_dpo": eipd.dpo_dictamen,
            "fecha_creacion": eipd.fecha_creacion.isoformat()
        }

    async def registrar_dictamen_dpo(self, eipd_id: UUID, dictamen: str, 
                                     aprobada: bool, dpo_nombre: str) -> Optional[EvaluacionImpactoProteccionDatos]:
        """Registrar dictamen del DPO"""
        result = await self.db.execute(
            select(EvaluacionImpactoProteccionDatos).where(EvaluacionImpactoProteccionDatos.id == eipd_id)
        )
        eipd = result.scalar_one_or_none()
        
        if not eipd:
            return None
        
        eipd.dpo_dictamen = dictamen
        eipd.dpo_nombre = dpo_nombre
        eipd.estado = EstadoEIPD.APROBADA if aprobada else EstadoEIPD.RECHAZADA
        if aprobada:
            eipd.fecha_aprobacion = datetime.now()
        
        await self.db.commit()
        await self.db.refresh(eipd)
        return eipd
