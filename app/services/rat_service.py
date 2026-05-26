"""
Servicio para Registro de Actividades de Tratamiento (RAT)
Cumplimiento Art. 27 Ley 21.719
"""
from datetime import datetime, date
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import Base
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text, Enum as SQLEnum, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID as PGUUID
import enum

class FinalidadTratamiento(str, enum.Enum):
    EJECUCION_CONTRATO = "EJECUCION_CONTRATO"
    CUMPLIMIENTO_LEGAL = "CUMPLIMIENTO_LEGAL"
    INTERES_LEGITIMO = "INTERES_LEGITIMO"
    CONSENTIMIENTO = "CONSENTIMIENTO"
    DATOS_PUBLICOS = "DATOS_PUBLICOS"

class CategoriaDatoPersonal(str, enum.Enum):
    IDENTIFICACION = "IDENTIFICACION"
    CONTACTO = "CONTACTO"
    LABORAL = "LABORAL"
    ECONOMICO = "ECONOMICO"
    SALUD = "SALUD"
    BIOMETRICO = "BIOMETRICO"
    SENSIBLE = "SENSIBLE"

class DestinatarioTipo(str, enum.Enum):
    ENCARGADO_TRATAMIENTO = "ENCARGADO_TRATAMIENTO"
    TERCERO_AUTORIZADO = "TERCERO_AUTORIZADO"
    AUTORIDAD_PUBLICA = "AUTORIDAD_PUBLICA"
    TRANSFERENCIA_INTERNACIONAL = "TRANSFERENCIA_INTERNACIONAL"
    SIN_DESTINATARIO = "SIN_DESTINATARIO"

class RegistroActividadesTratamiento(Base):
    __tablename__ = "registros_actividades_tratamiento"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=func.gen_random_uuid())
    organizacion_id = Column(PGUUID(as_uuid=True), ForeignKey("organizaciones.id"), nullable=False, index=True)
    
    # Información del tratamiento
    nombre_actividad = Column(String(200), nullable=False)
    descripcion = Column(Text)
    finalidad = Column(SQLEnum(FinalidadTratamiento), nullable=False)
    categorias_datos = Column(JSON, nullable=False)  # Lista de CategoriaDatoPersonal
    categorias_titulares = Column(JSON, nullable=False)  # Clientes, empleados, proveedores, etc.
    
    # Plazos de conservación
    plazo_conservacion_dias = Column(Integer)
    criterio_eliminar = Column(Text)
    
    # Medidas de seguridad
    medidas_seguridad = Column(JSON)  # Encriptación, pseudonimización, control acceso, etc.
    
    # Transferencias internacionales
    tiene_transferencia_internacional = Column(Boolean, default=False)
    paises_destino = Column(JSON)  # Lista de países
    garantias_transferencia = Column(Text)  # Cláusulas estándar, decisiones adecuación, etc.
    
    # Encargados de tratamiento
    encargados_tratamiento = Column(JSON)  # Lista de {nombre, rut, servicio}
    
    # Base legal
    base_legal = Column(Text, nullable=False)
    documento_referencia = Column(String(500))  # Contrato, política, etc.
    
    # Auditoría
    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False)
    fecha_actualizacion = Column(DateTime, onupdate=datetime.utcnow)
    responsable_registro = Column(String(200))  # Nombre del DPO o responsable


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
