"""
Servicio para Registro de Actividades de Tratamiento (RAT)
Cumplimiento Art. 27 Ley 21.719
"""
from datetime import datetime, date
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.cumplimiento_models import RegistroActividadesTratamiento, FinalidadTratamiento


class ServicioRAT:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def crear_registro(self, data: dict) -> RegistroActividadesTratamiento:
        """Crear un nuevo registro de actividad de tratamiento"""
        registro = RegistroActividadesTratamiento(**data)
        self.db.add(registro)
        await self.db.commit()
        await self.db.refresh(registro)
        return registro
    
    async def obtener_por_organizacion(self, organizacion_id: UUID) -> List[RegistroActividadesTratamiento]:
        """Obtener todos los registros de una organización"""
        result = await self.db.execute(
            select(RegistroActividadesTratamiento)
            .where(RegistroActividadesTratamiento.organizacion_id == organizacion_id)
            .order_by(RegistroActividadesTratamiento.fecha_creacion.desc())
        )
        return list(result.scalars().all())
    
    async def actualizar_registro(self, registro_id: UUID, data: dict) -> Optional[RegistroActividadesTratamiento]:
        """Actualizar un registro existente"""
        result = await self.db.execute(
            select(RegistroActividadesTratamiento)
            .where(RegistroActividadesTratamiento.id == registro_id)
        )
        registro = result.scalar_one_or_none()
        
        if not registro:
            return None
        
        for key, value in data.items():
            if hasattr(registro, key):
                setattr(registro, key, value)
        
        registro.fecha_actualizacion = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(registro)
        return registro
    
    async def eliminar_registro(self, registro_id: UUID) -> bool:
        """Eliminar un registro (solo si no hay datos activos)"""
        result = await self.db.execute(
            select(RegistroActividadesTratamiento)
            .where(RegistroActividadesTratamiento.id == registro_id)
        )
        registro = result.scalar_one_or_none()
        
        if not registro:
            return False
        
        await self.db.delete(registro)
        await self.db.commit()
        return True
    
    async def generar_reporte_rat(self, organizacion_id: UUID) -> dict:
        """Generar reporte completo RAT para auditoría"""
        registros = await self.obtener_por_organizacion(organizacion_id)
        
        resumen = {
            "total_actividades": len(registros),
            "por_finalidad": {},
            "con_transferencia_internacional": 0,
            "categorias_datos_utilizadas": set(),
            "encargados_tratamiento": set()
        }
        
        for reg in registros:
            # Contar por finalidad
            finalidad = reg.finalidad.value
            resumen["por_finalidad"][finalidad] = resumen["por_finalidad"].get(finalidad, 0) + 1
            
            # Contar transferencias
            if reg.tiene_transferencia_internacional:
                resumen["con_transferencia_internacional"] += 1
            
            # Recopilar categorías
            if reg.categorias_datos:
                resumen["categorias_datos_utilizadas"].update(reg.categorias_datos)
            
            # Recopilar encargados
            if reg.encargados_tratamiento:
                for enc in reg.encargados_tratamiento:
                    if isinstance(enc, dict) and "nombre" in enc:
                        resumen["encargados_tratamiento"].add(enc["nombre"])
        
        resumen["categorias_datos_utilizadas"] = list(resumen["categorias_datos_utilizadas"])
        resumen["encargados_tratamiento"] = list(resumen["encargados_tratamiento"])
        
        return {
            "fecha_generacion": datetime.utcnow().isoformat(),
            "organizacion_id": str(organizacion_id),
            "resumen": resumen,
            "registros": [
                {
                    "id": str(r.id),
                    "nombre": r.nombre_actividad,
                    "finalidad": r.finalidad.value,
                    "categorias_datos": r.categorias_datos,
                    "tiene_transferencia": r.tiene_transferencia_internacional,
                    "fecha_creacion": r.fecha_creacion.isoformat()
                }
                for r in registros
            ]
        }
