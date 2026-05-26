"""
Servicio de Eliminación Automática y Ciclo de Vida de Datos
Implementa principio de limitación de conservación (Ley 21.719)
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import UUID
import json
import asyncio

from app.models.cumplimiento_models import (
    PoliticaRetencionDatos, 
    EjecucionEliminacionAutomatica,
    ExportacionPortabilidad
)
from app.models.models import AccesoOrganizacion, EstadoPermiso, SolicitudArco, TipoArco


class ServicioCicloVidaDatos:
    """Gestión automática del ciclo de vida de datos personales"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def crear_politica_retencion(self, data: dict, organizacion_id: UUID) -> PoliticaRetencionDatos:
        """Crear nueva política de retención de datos"""
        
        politica = PoliticaRetencionDatos(
            organizacion_id=organizacion_id,
            nombre_politica=data["nombre_politica"],
            categoria_dato=data["categoria_dato"],
            plazo_retencion_dias=data["plazo_retencion_dias"],
            criterio_inicio_plazo=data.get("criterio_inicio_plazo", "fecha_registro"),
            accion_post_plazo=data.get("accion_post_plazo", "ELIMINAR"),
            excepciones=data.get("excepciones"),
            activa=data.get("activa", True)
        )
        
        self.db.add(politica)
        await self.db.commit()
        await self.db.refresh(politica)
        
        return politica
    
    async def listar_politicas(self, organizacion_id: UUID, 
                               activas_only: bool = True) -> List[PoliticaRetencionDatos]:
        """Listar políticas de retención de una organización"""
        
        query = select(PoliticaRetencionDatos).where(
            PoliticaRetencionDatos.organizacion_id == organizacion_id
        )
        
        if activas_only:
            query = query.where(PoliticaRetencionDatos.activa == True)
        
        result = await self.db.execute(query.order_by(PoliticaRetencionDatos.nombre_politica))
        return list(result.scalars().all())
    
    async def ejecutar_eliminacion_automatica(self, organizacion_id: UUID,
                                              politica_id: Optional[UUID] = None) -> Dict:
        """
        Ejecutar proceso de eliminación/anonimización automática
        Retorna estadísticas de la ejecución
        """
        
        # Obtener políticas a procesar
        query = select(PoliticaRetencionDatos).where(
            PoliticaRetencionDatos.organizacion_id == organizacion_id,
            PoliticaRetencionDatos.activa == True
        )
        
        if politica_id:
            query = query.where(PoliticaRetencionDatos.id == politica_id)
        
        result = await self.db.execute(query)
        politicas = list(result.scalars().all())
        
        total_procesados = 0
        total_eliminados = 0
        total_anonimizados = 0
        total_bloqueados = 0
        total_errores = 0
        errores_detalle = []
        
        fecha_inicio = datetime.now()
        
        for politica in politicas:
            try:
                # Calcular fecha límite según criterio
                fecha_limite = self._calcular_fecha_limite(politica)
                
                # Buscar accesos vencidos
                resultado = await self._procesar_accesos_vencidos(
                    politica, fecha_limite, organizacion_id
                )
                
                total_procesados += resultado["procesados"]
                total_eliminados += resultado["eliminados"]
                total_anonimizados += resultado["anonimizados"]
                total_bloqueados += resultado["bloqueados"]
                
                # Actualizar política
                politica.fecha_ultima_ejecucion = datetime.now()
                politica.registros_eliminados_total += resultado["eliminados"]
                
            except Exception as e:
                total_errores += 1
                errores_detalle.append({
                    "politica_id": str(politica.id),
                    "error": str(e)
                })
        
        duracion = (datetime.now() - fecha_inicio).total_seconds()
        
        # Registrar ejecución
        ejecucion = EjecucionEliminacionAutomatica(
            politica_id=politica_id if politica_id else politicas[0].id if politicas else None,
            organizacion_id=organizacion_id,
            registros_procesados=total_procesados,
            registros_eliminados=total_eliminados,
            registros_anonimizados=total_anonimizados,
            registros_bloqueados=total_bloqueados,
            errores_encontrados=total_errores,
            detalle_errores=errores_detalle if errores_detalle else None,
            duracion_segundos=duracion
        )
        
        self.db.add(ejecucion)
        await self.db.commit()
        
        return {
            "fecha_ejecucion": fecha_inicio.isoformat(),
            "duracion_segundos": round(duracion, 2),
            "politicas_procesadas": len(politicas),
            "registros_procesados": total_procesados,
            "registros_eliminados": total_eliminados,
            "registros_anonimizados": total_anonimizados,
            "registros_bloqueados": total_bloqueados,
            "errores": total_errores,
            "detalle_errores": errores_detalle
        }
    
    def _calcular_fecha_limite(self, politica: PoliticaRetencionDatos) -> datetime:
        """Calcular fecha límite según criterio de inicio de plazo"""
        
        ahora = datetime.now()
        
        if politica.criterio_inicio_plazo == "fecha_registro":
            return ahora - timedelta(days=politica.plazo_retencion_dias)
        elif politica.criterio_inicio_plazo == "ultima_interaccion":
            # Implementar lógica específica para última interacción
            return ahora - timedelta(days=politica.plazo_retencion_dias)
        elif politica.criterio_inicio_plazo == "fin_relacion_contractual":
            # Implementar lógica específica para fin de contrato
            return ahora - timedelta(days=politica.plazo_retencion_dias)
        else:
            return ahora - timedelta(days=politica.plazo_retencion_dias)
    
    async def _procesar_accesos_vencidos(self, politica: PoliticaRetencionDatos,
                                         fecha_limite: datetime,
                                         organizacion_id: UUID) -> Dict:
        """Procesar accesos que han vencido según política"""
        
        procesados = 0
        eliminados = 0
        anonimizados = 0
        bloqueados = 0
        
        # Buscar accesos por categoría de dato
        query = select(AccesoOrganizacion).where(
            AccesoOrganizacion.organizacion_id == organizacion_id,
            AccesoOrganizacion.categoria_dato == politica.categoria_dato,
            AccesoOrganizacion.estado == EstadoPermiso.ACTIVO
        )
        
        # Filtrar por fecha de otorgamiento (simplificado)
        # En implementación real, se necesitaría tracking de fecha de último uso
        result = await self.db.execute(query)
        accesos = list(result.scalars().all())
        
        for acceso in accesos:
            procesados += 1
            
            # Verificar si ha expirado
            if acceso.fecha_expiracion and acceso.fecha_expiracion < datetime.now():
                if politica.accion_post_plazo == "ELIMINAR":
                    acceso.estado = EstadoPermiso.REVOCADO
                    acceso.fecha_revocacion = datetime.now()
                    eliminados += 1
                elif politica.accion_post_plazo == "ANONIMIZAR":
                    # Marcar para anonimización (implementación depende del caso)
                    anonimizados += 1
                elif politica.accion_post_plazo == "BLOQUEAR":
                    acceso.estado = EstadoPermiso.REVOCADO
                    bloqueados += 1
        
        return {
            "procesados": procesados,
            "eliminados": eliminados,
            "anonimizados": anonimizados,
            "bloqueados": bloqueados
        }
    
    async def verificar_vencimientos_pendientes(self, organizacion_id: UUID) -> List[Dict]:
        """Verificar consentimientos próximos a vencer (próximos 30 días)"""
        
        fecha_hoy = datetime.now()
        fecha_proximo_vencimiento = fecha_hoy + timedelta(days=30)
        
        result = await self.db.execute(
            select(AccesoOrganizacion)
            .where(AccesoOrganizacion.organizacion_id == organizacion_id)
            .where(AccesoOrganizacion.estado == EstadoPermiso.ACTIVO)
            .where(AccesoOrganizacion.fecha_expiracion.isnot(None))
            .where(AccesoOrganizacion.fecha_expiracion <= fecha_proximo_vencimiento)
            .where(AccesoOrganizacion.fecha_expiracion >= fecha_hoy)
            .order_by(AccesoOrganizacion.fecha_expiracion)
        )
        
        accesos_por_vencer = list(result.scalars().all())
        
        return [
            {
                "id": str(acceso.id),
                "usuario_id": str(acceso.usuario_id),
                "categoria_dato": acceso.categoria_dato,
                "finalidad": acceso.finalidad[:100],
                "fecha_vencimiento": acceso.fecha_expiracion.isoformat(),
                "dias_restantes": (acceso.fecha_expiracion - fecha_hoy).days,
                "accion_recomendada": "Renovar consentimiento o preparar eliminación"
            }
            for acceso in accesos_por_vencer
        ]
    
    async def obtener_estadisticas_ciclo_vida(self, organizacion_id: UUID,
                                               periodo_dias: int = 90) -> Dict:
        """Obtener estadísticas de ciclo de vida de datos"""
        
        from sqlalchemy import func
        
        fecha_limite = datetime.now() - timedelta(days=periodo_dias)
        
        # Total ejecuciones
        result = await self.db.execute(
            select(func.count(EjecucionEliminacionAutomatica.id))
            .where(EjecucionEliminacionAutomatica.organizacion_id == organizacion_id)
            .where(EjecucionEliminacionAutomatica.fecha_ejecucion >= fecha_limite)
        )
        total_ejecuciones = result.scalar() or 0
        
        # Totales acumulados
        result = await self.db.execute(
            select(
                func.sum(EjecucionEliminacionAutomatica.registros_procesados),
                func.sum(EjecucionEliminacionAutomatica.registros_eliminados),
                func.sum(EjecucionEliminacionAutomatica.registros_anonimizados),
                func.sum(EjecucionEliminacionAutomatica.registros_bloqueados)
            )
            .where(EjecucionEliminacionAutomatica.organizacion_id == organizacion_id)
            .where(EjecucionEliminacionAutomatica.fecha_ejecucion >= fecha_limite)
        )
        
        stats = result.first()
        
        # Políticas activas
        result = await self.db.execute(
            select(func.count(PoliticaRetencionDatos.id))
            .where(PoliticaRetencionDatos.organizacion_id == organizacion_id)
            .where(PoliticaRetencionDatos.activa == True)
        )
        politicas_activas = result.scalar() or 0
        
        return {
            "periodo_dias": periodo_dias,
            "politicas_activas": politicas_activas,
            "ejecuciones_realizadas": total_ejecuciones,
            "registros_procesados": stats[0] or 0,
            "registros_eliminados": stats[1] or 0,
            "registros_anonimizados": stats[2] or 0,
            "registros_bloqueados": stats[3] or 0,
            "tasa_eliminacion": round(
                (stats[1] / max(stats[0], 1)) * 100, 2
            ) if stats[0] else 0
        }
    
    async def programar_tarea_limpieza(self, organizacion_id: UUID,
                                       frecuencia_dias: int = 7) -> Dict:
        """
        Configurar tarea programada de limpieza automática
        Nota: En producción usar Celery/RQ para tareas background
        """
        
        return {
            "mensaje": "Tarea de limpieza configurada",
            "organizacion_id": str(organizacion_id),
            "frecuencia_dias": frecuencia_dias,
            "proxima_ejecucion": (datetime.now() + timedelta(days=frecuencia_dias)).isoformat(),
            "nota": "Implementar con Celery/Redis en producción para ejecución automática"
        }
