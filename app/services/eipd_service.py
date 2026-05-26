"""
Servicio de Evaluación de Impacto en Protección de Datos (EIPD)
Cumplimiento Art. 34 Ley 21.719
"""
from datetime import datetime
from typing import List, Optional, Dict
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import Base
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text, Enum as SQLEnum, JSON, Integer, Integer, Float
from sqlalchemy.dialects.postgresql import UUID as PGUUID
import enum

class NivelRiesgoEIPD(str, enum.Enum):
    BAJO = "BAJO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"
    MUY_ALTO = "MUY_ALTO"

class EstadoEIPD(str, enum.Enum):
    BORRADOR = "BORRADOR"
    EN_REVISION = "EN_REVISION"
    APROBADA = "APROBADA"
    REQUIERE_MITIGACION = "REQUIERE_MITIGACION"
    RECHAZADA = "RECHAZADA"

class CriterioAltoRiesgo(str, enum.Enum):
    EVALUACION_SISTEMATICA = "EVALUACION_SISTEMATICA"
    DATOS_SENSIBLES = "DATOS_SENSIBLES"
    VIGILANCIA_ZONAS_ACCESO = "VIGILANCIA_ZONAS_ACCESO"
    TECNOLOGIAS_NUEVAS = "TECNOLOGIAS_NUEVAS"
    DECISIONES_AUTOMATIZADAS = "DECISIONES_AUTOMATIZADAS"
    DATOS_VULNERABLES = "DATOS_VULNERABLES"
    GRAN_ESCALA = "GRAN_ESCALA"
    CRUCE_DATOS = "CRUCE_DATOS"

class EvaluacionImpactoProteccionDatos(Base):
    __tablename__ = "evaluaciones_impacto_proteccion_datos"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=func.gen_random_uuid())
    organizacion_id = Column(PGUUID(as_uuid=True), ForeignKey("organizaciones.id"), nullable=False, index=True)
    
    # Información general
    nombre_evaluacion = Column(String(200), nullable=False)
    descripcion_tratamiento = Column(Text, nullable=False)
    responsables_evaluacion = Column(JSON)  # Lista de {nombre, rol, email}
    
    # Criterios de alto riesgo (Art. 34)
    criterios_alto_riesgo = Column(JSON)  # Lista de CriterioAltoRiesgo aplicables
    requiere_eipd_obligatoria = Column(Boolean, default=False)
    justificacion_eipd = Column(Text)
    
    # Descripción del tratamiento
    finalidad_tratamiento = Column(Text, nullable=False)
    categorias_datos = Column(JSON, nullable=False)
    categorias_titulares = Column(JSON, nullable=False)
    plazo_conservacion = Column(String(200))
    
    # Necesidad y proporcionalidad
    evaluacion_necesidad = Column(Text)
    evaluacion_proporcionalidad = Column(Text)
    medidas_previas = Column(JSON)
    
    # Análisis de riesgos
    riesgos_identificados = Column(JSON)  # Lista de {descripcion, probabilidad, impacto, nivel}
    nivel_riesgo_inicial = Column(SQLEnum(NivelRiesgoEIPD))
    
    # Medidas de mitigación
    medidas_mitigacion = Column(JSON)  # Lista de {descripcion, responsable, plazo, estado}
    nivel_riesgo_residual = Column(SQLEnum(NivelRiesgoEIPD))
    
    # Consulta a interesados
    consulta_interesados_realizada = Column(Boolean, default=False)
    descripcion_consulta = Column(Text)
    resultados_consulta = Column(Text)
    
    # Revisión DPO
    dpo_nombre = Column(String(200))
    dpo_dictamen = Column(Text)
    dpo_fecha_dictamen = Column(DateTime)
    
    # Estado y aprobación
    estado = Column(SQLEnum(EstadoEIPD), default=EstadoEIPD.BORRADOR)
    fecha_aprobacion = Column(DateTime)
    aprobado_por = Column(String(200))
    
    # Revisión periódica
    fecha_proxima_revision = Column(DateTime)
    revisiones_realizadas = Column(JSON)
    
    # Auditoría
    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False)
    fecha_actualizacion = Column(DateTime, onupdate=datetime.utcnow)


class ServicioEIPD:
    # Matriz de puntuación de riesgos
    PROBABILIDAD_PUNTOS = {
        "MUY_BAJA": 1,
        "BAJA": 2,
        "MEDIA": 3,
        "ALTA": 4,
        "MUY_ALTA": 5
    }
    
    IMPACTO_PUNTOS = {
        "INSIGNIFICANTE": 1,
        "MENOR": 2,
        "MODERADO": 3,
        "SIGNIFICATIVO": 4,
        "SEVERO": 5
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def crear_evaluacion(self, data: dict) -> EvaluacionImpactoProteccionDatos:
        """Crear nueva EIPD"""
        # Determinar si requiere EIPD obligatoria
        criterios = data.get("criterios_alto_riesgo", [])
        requiere_obligatoria = len(criterios) >= 2  # 2 o más criterios = obligatoria
        
        evaluacion = EvaluacionImpactoProteccionDatos(
            requiere_eipd_obligatoria=requiere_obligatoria,
            **data
        )
        
        self.db.add(evaluacion)
        await self.db.commit()
        await self.db.refresh(evaluacion)
        
        return evaluacion
    
    async def calcular_nivel_riesgo(self, riesgos: List[Dict]) -> Dict:
        """Calcular nivel de riesgo basado en probabilidad e impacto"""
        if not riesgos:
            return {"nivel": "BAJO", "puntaje_total": 0}
        
        puntajes = []
        for riesgo in riesgos:
            prob_pts = self.PROBABILIDAD_PUNTOS.get(riesgo.get("probabilidad", "BAJA"), 2)
            impacto_pts = self.IMPACTO_PUNTOS.get(riesgo.get("impacto", "MODERADO"), 3)
            puntaje = prob_pts * impacto_pts
            puntajes.append(puntaje)
            
            # Asignar nivel individual
            if puntaje <= 4:
                riesgo["nivel"] = "BAJO"
            elif puntaje <= 9:
                riesgo["nivel"] = "MEDIO"
            elif puntaje <= 16:
                riesgo["nivel"] = "ALTO"
            else:
                riesgo["nivel"] = "MUY_ALTO"
        
        promedio = sum(puntajes) / len(puntajes) if puntajes else 0
        
        # Nivel general
        if promedio <= 4:
            nivel_general = "BAJO"
        elif promedio <= 9:
            nivel_general = "MEDIO"
        elif promedio <= 16:
            nivel_general = "ALTO"
        else:
            nivel_general = "MUY_ALTO"
        
        return {
            "nivel": nivel_general,
            "puntaje_promedio": round(promedio, 2),
            "riesgos_detalle": riesgos
        }
    
    async def agregar_medida_mitigacion(self, eipd_id: UUID, medida: Dict) -> Optional[EvaluacionImpactoProteccionDatos]:
        """Agregar medida de mitigación y recalcular riesgo residual"""
        result = await self.db.execute(
            select(EvaluacionImpactoProteccionDatos)
            .where(EvaluacionImpactoProteccionDatos.id == eipd_id)
        )
        eipd = result.scalar_one_or_none()
        
        if not eipd:
            return None
        
        medidas_actuales = eipd.medidas_mitigacion or []
        medidas_actuales.append(medida)
        eipd.medidas_mitigacion = medidas_actuales
        
        # Recalcular riesgo residual (simplificado: reducir un nivel por medida efectiva)
        if eipd.nivel_riesgo_inicial:
            mapa_redaccion = {
                "MUY_ALTO": "ALTO",
                "ALTO": "MEDIO",
                "MEDIO": "BAJO",
                "BAJO": "BAJO"
            }
            reduccion = min(len(medidas_actuales), 2)  # Máximo 2 niveles de reducción
            nivel_residual = eipd.nivel_riesgo_inicial.value
            
            for _ in range(reduccion):
                nivel_residual = mapa_redaccion.get(nivel_residual, nivel_residual)
            
            eipd.nivel_riesgo_residual = NivelRiesgoEIPD(nivel_residual)
        
        await self.db.commit()
        await self.db.refresh(eipd)
        
        return eipd
    
    async def enviar_a_revision(self, eipd_id: UUID) -> Optional[EvaluacionImpactoProteccionDatos]:
        """Enviar EIPD a revisión del DPO"""
        result = await self.db.execute(
            select(EvaluacionImpactoProteccionDatos)
            .where(EvaluacionImpactoProteccionDatos.id == eipd_id)
        )
        eipd = result.scalar_one_or_none()
        
        if not eipd:
            return None
        
        eipd.estado = EstadoEIPD.EN_REVISION
        await self.db.commit()
        await self.db.refresh(eipd)
        
        return eipd
    
    async def registrar_dictamen_dpo(
        self,
        eipd_id: UUID,
        dictamen: str,
        aprobada: bool,
        dpo_nombre: str
    ) -> Optional[EvaluacionImpactoProteccionDatos]:
        """Registrar dictamen del DPO"""
        result = await self.db.execute(
            select(EvaluacionImpactoProteccionDatos)
            .where(EvaluacionImpactoProteccionDatos.id == eipd_id)
        )
        eipd = result.scalar_one_or_none()
        
        if not eipd:
            return None
        
        eipd.dpo_nombre = dpo_nombre
        eipd.dpo_dictamen = dictamen
        eipd.dpo_fecha_dictamen = datetime.utcnow()
        
        if aprobada:
            eipd.estado = EstadoEIPD.APROBADA
            eipd.fecha_aprobacion = datetime.utcnow()
            eipd.aprobado_por = dpo_nombre
        else:
            eipd.estado = EstadoEIPD.REQUIERE_MITIGACION
        
        await self.db.commit()
        await self.db.refresh(eipd)
        
        return eipd
    
    async def programar_revision(self, eipd_id: UUID, meses: int = 12) -> Optional[EvaluacionImpactoProteccionDatos]:
        """Programar próxima revisión periódica"""
        from datetime import timedelta
        result = await self.db.execute(
            select(EvaluacionImpactoProteccionDatos)
            .where(EvaluacionImpactoProteccionDatos.id == eipd_id)
        )
        eipd = result.scalar_one_or_none()
        
        if not eipd:
            return None
        
        eipd.fecha_proxima_revision = datetime.utcnow() + timedelta(days=meses * 30)
        
        # Registrar revisión
        revisiones = eipd.revisiones_realizadas or []
        revisiones.append({
            "fecha": datetime.utcnow().isoformat(),
            "tipo": "PERIODICA",
            "proxima_revision": eipd.fecha_proxima_revision.isoformat()
        })
        eipd.revisiones_realizadas = revisiones
        
        await self.db.commit()
        await self.db.refresh(eipd)
        
        return eipd
    
    async def obtener_evaluaciones_pendientes_revision(self, organizacion_id: UUID) -> List[EvaluacionImpactoProteccionDatos]:
        """Obtener EIPD que requieren revisión"""
        ahora = datetime.utcnow()
        result = await self.db.execute(
            select(EvaluacionImpactoProteccionDatos)
            .where(EvaluacionImpactoProteccionDatos.organizacion_id == organizacion_id)
            .where(
                (EvaluacionImpactoProteccionDatos.estado == EstadoEIPD.APROBADA) &
                (EvaluacionImpactoProteccionDatos.fecha_proxima_revision <= ahora)
            )
        )
        return list(result.scalars().all())
    
    async def generar_reporte_eipd(self, eipd_id: UUID) -> Dict:
        """Generar reporte completo de EIPD para auditoría"""
        result = await self.db.execute(
            select(EvaluacionImpactoProteccionDatos)
            .where(EvaluacionImpactoProteccionDatos.id == eipd_id)
        )
        eipd = result.scalar_one_or_none()
        
        if not eipd:
            return {"error": "EIPD no encontrada"}
        
        return {
            "id": str(eipd.id),
            "nombre": eipd.nombre_evaluacion,
            "estado": eipd.estado.value,
            "requiere_obligatoria": eipd.requiere_eipd_obligatoria,
            "criterios_alto_riesgo": eipd.criterios_alto_riesgo,
            "descripcion": eipd.descripcion_tratamiento,
            "finalidad": eipd.finalidad_tratamiento,
            "categorias_datos": eipd.categorias_datos,
            "riesgos_identificados": eipd.riesgos_identificados,
            "nivel_riesgo_inicial": eipd.nivel_riesgo_inicial.value if eipd.nivel_riesgo_inicial else None,
            "medidas_mitigacion": eipd.medidas_mitigacion,
            "nivel_riesgo_residual": eipd.nivel_riesgo_residual.value if eipd.nivel_riesgo_residual else None,
            "dictamen_dpo": {
                "nombre": eipd.dpo_nombre,
                "dictamen": eipd.dpo_dictamen,
                "fecha": eipd.dpo_fecha_dictamen.isoformat() if eipd.dpo_fecha_dictamen else None
            },
            "consulta_interesados": {
                "realizada": eipd.consulta_interesados_realizada,
                "descripcion": eipd.descripcion_consulta,
                "resultados": eipd.resultados_consulta
            },
            "fecha_creacion": eipd.fecha_creacion.isoformat(),
            "fecha_aprobacion": eipd.fecha_aprobacion.isoformat() if eipd.fecha_aprobacion else None,
            "proxima_revision": eipd.fecha_proxima_revision.isoformat() if eipd.fecha_proxima_revision else None
        }
