"""
Endpoints API para funcionalidades avanzadas Ley 21.719
- Portabilidad de Datos
- Ciclo de Vida y Eliminación Automática
- Legal Design (Traducciones)
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.database import get_db
from app.models.models import Organizacion, Usuario
from app.services.portabilidad_service import PortabilidadService
from app.services.ciclo_vida_service import ServicioCicloVidaDatos
from app.api.routes import get_current_organization, get_current_usuario as get_current_user

router = APIRouter(tags=["portabilidad-ciclo-vida"])


# ==================== PORTABILIDAD DE DATOS ====================

@router.post("/portabilidad/solicitar", response_model=dict, status_code=status.HTTP_201_CREATED)
async def solicitar_exportacion_portabilidad(
    formato: str = "JSON",
    categorias: Optional[List[str]] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    current_org: Organizacion = Depends(get_current_organization)
):
    """
    Solicitar exportación de datos personales para portabilidad
    Formatos soportados: JSON, XML, CSV
    """
    servicio = PortabilidadService(db)
    
    try:
        exportacion = await servicio.solicitar_exportacion(
            usuario_id=current_user.id,
            organizacion_id=current_org.id,
            formato=formato.upper(),
            categorias=categorias
        )
        
        return {
            "id": str(exportacion.id),
            "estado": exportacion.estado,
            "formato": exportacion.formato_exportacion,
            "mensaje": "Exportación generada. Use el token para descargar.",
            "expira_en_horas": 24
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando exportación: {str(e)}")


@router.get("/portabilidad/estado/{exportacion_id}")
async def obtener_estado_exportacion(
    exportacion_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener estado de una solicitud de exportación"""
    servicio = PortabilidadService(db)
    
    try:
        estado = await servicio.obtener_estado_exportacion(exportacion_id)
        return estado
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/portabilidad/descarga/{token_hash}")
async def descargar_exportacion(
    token_hash: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Descargar archivo de exportación con token seguro
    El token expira en 24 horas
    """
    servicio = PortabilidadService(db)
    
    try:
        resultado = await servicio.descargar_exportacion(token_hash)
        
        headers = {
            "Content-Disposition": f'attachment; filename="portabilidad_datos.{resultado["formato"].lower()}"',
            "X-Verification-Hash": resultado["hash_verificacion"],
            "X-File-Size": str(resultado["tamaño_bytes"])
        }
        
        return Response(
            content=resultado["contenido"],
            media_type=f"application/{resultado['formato'].lower()}",
            headers=headers
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/portabilidad/historial")
async def listar_exportaciones_usuario(
    limite: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar historial de exportaciones realizadas por el usuario"""
    servicio = PortabilidadService(db)
    exportaciones = await servicio.listar_exportaciones_usuario(current_user.id, limite)
    
    return {
        "total": len(exportaciones),
        "exportaciones": exportaciones
    }


# ==================== LEGAL DESIGN ====================

@router.post("/legal-design/traduccion", response_model=dict, status_code=status.HTTP_201_CREATED)
async def crear_traduccion_legal(
    texto_legal: str,
    categoria: str,
    nivel: str = "BASICO",
    db: AsyncSession = Depends(get_db),
    current_org: Organizacion = Depends(get_current_organization)
):
    """
    Crear traducción de lenguaje legal a lenguaje ciudadano
    Categorías: finalidad, derechos, retencion, transferencia, seguridad
    """
    servicio = PortabilidadService(db)
    
    if categoria not in ["finalidad", "derechos", "retencion", "transferencia", "seguridad"]:
        raise HTTPException(
            status_code=400,
            detail="Categoría inválida. Use: finalidad, derechos, retencion, transferencia, seguridad"
        )
    
    traduccion = await servicio.crear_traduccion_legal(
        organizacion_id=current_org.id,
        texto_legal=texto_legal,
        categoria=categoria,
        nivel=nivel
    )
    
    return {
        "id": str(traduccion.id),
        "categoria": traduccion.categoria,
        "icono": traduccion.icono_sugerido,
        "texto_ciudadano": traduccion.texto_ciudadano,
        "nivel_simplificacion": traduccion.nivel_simplificacion,
        "validado_dpo": traduccion.validado_dpo,
        "mensaje": "Traducción creada. Requiere validación del DPO antes de usar."
    }


@router.get("/legal-design/traducciones")
async def listar_traducciones(
    categoria: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_org: Organizacion = Depends(get_current_organization)
):
    """Listar traducciones de legal design de la organización"""
    from sqlalchemy import select
    from app.models.cumplimiento_models import TraduccionLegalDesign
    
    query = select(TraduccionLegalDesign).where(
        TraduccionLegalDesign.organizacion_id == current_org.id
    )
    
    if categoria:
        query = query.where(TraduccionLegalDesign.categoria == categoria)
    
    result = await self.db.execute(query.order_by(TraduccionLegalDesign.fecha_creacion.desc()))
    traducciones = list(result.scalars().all())
    
    return [
        {
            "id": str(t.id),
            "categoria": t.categoria,
            "icono": t.icono_sugerido,
            "texto_ciudadano": t.texto_ciudadano[:200],
            "nivel": t.nivel_simplificacion,
            "validado": t.validado_dpo,
            "fecha_creacion": t.fecha_creacion.isoformat()
        }
        for t in traducciones
    ]


# ==================== CICLO DE VIDA DE DATOS ====================

@router.post("/ciclo-vida/politica", response_model=dict, status_code=status.HTTP_201_CREATED)
async def crear_politica_retencion(
    nombre_politica: str,
    categoria_dato: str,
    plazo_retencion_dias: int,
    criterio_inicio_plazo: str = "fecha_registro",
    accion_post_plazo: str = "ELIMINAR",
    excepciones: Optional[dict] = None,
    db: AsyncSession = Depends(get_db),
    current_org: Organizacion = Depends(get_current_organization)
):
    """
    Crear política de retención y eliminación automática
    Acciones post-plazo: ELIMINAR, ANONIMIZAR, BLOQUEAR
    """
    servicio = ServicioCicloVidaDatos(db)
    
    if accion_post_plazo not in ["ELIMINAR", "ANONIMIZAR", "BLOQUEAR"]:
        raise HTTPException(
            status_code=400,
            detail="Acción inválida. Use: ELIMINAR, ANONIMIZAR, BLOQUEAR"
        )
    
    politica = await servicio.crear_politica_retencion(
        data={
            "nombre_politica": nombre_politica,
            "categoria_dato": categoria_dato,
            "plazo_retencion_dias": plazo_retencion_dias,
            "criterio_inicio_plazo": criterio_inicio_plazo,
            "accion_post_plazo": accion_post_plazo,
            "excepciones": excepciones,
            "activa": True
        },
        organizacion_id=current_org.id
    )
    
    return {
        "id": str(politica.id),
        "nombre": politica.nombre_politica,
        "categoria": politica.categoria_dato,
        "plazo_dias": politica.plazo_retencion_dias,
        "accion_post_plazo": politica.accion_post_plazo,
        "activa": politica.activa
    }


@router.get("/ciclo-vida/politicas")
async def listar_politicas_retencion(
    activas_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_org: Organizacion = Depends(get_current_organization)
):
    """Listar políticas de retención de la organización"""
    servicio = ServicioCicloVidaDatos(db)
    politicas = await servicio.listar_politicas(current_org.id, activas_only)
    
    return [
        {
            "id": str(p.id),
            "nombre": p.nombre_politica,
            "categoria": p.categoria_dato,
            "plazo_dias": p.plazo_retencion_dias,
            "criterio_inicio": p.criterio_inicio_plazo,
            "accion_post_plazo": p.accion_post_plazo,
            "activa": p.activa,
            "ultima_ejecucion": p.fecha_ultima_ejecucion.isoformat() if p.fecha_ultima_ejecucion else None,
            "registros_eliminados_total": p.registros_eliminados_total
        }
        for p in politicas
    ]


@router.post("/ciclo-vida/ejecutar-limpieza")
async def ejecutar_eliminacion_automatica(
    politica_id: Optional[UUID] = None,
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
    current_org: Organizacion = Depends(get_current_organization)
):
    """
    Ejecutar proceso de eliminación/anonimización automática
    Puede ejecutarse para todas las políticas o una específica
    """
    servicio = ServicioCicloVidaDatos(db)
    
    resultado = await servicio.ejecutar_eliminacion_automatica(
        organizacion_id=current_org.id,
        politica_id=politica_id
    )
    
    return {
        "mensaje": "Proceso de limpieza completado",
        "detalle": resultado
    }


@router.get("/ciclo-vida/vencimientos-pendientes")
async def verificar_vencimientos_pendientes(
    db: AsyncSession = Depends(get_db),
    current_org: Organizacion = Depends(get_current_organization)
):
    """
    Verificar consentimientos próximos a vencer (próximos 30 días)
    Útil para planificación de renovaciones o eliminaciones
    """
    servicio = ServicioCicloVidaDatos(db)
    vencimientos = await servicio.verificar_vencimientos_pendientes(current_org.id)
    
    return {
        "fecha_consulta": datetime.now().isoformat(),
        "ventana_dias": 30,
        "total_por_vencer": len(vencimientos),
        "vencimientos": vencimientos
    }


@router.get("/ciclo-vida/estadisticas")
async def obtener_estadisticas_ciclo_vida(
    periodo_dias: int = 90,
    db: AsyncSession = Depends(get_db),
    current_org: Organizacion = Depends(get_current_organization)
):
    """Obtener estadísticas de ciclo de vida y eliminaciones automáticas"""
    servicio = ServicioCicloVidaDatos(db)
    estadisticas = await servicio.obtener_estadisticas_ciclo_vida(current_org.id, periodo_dias)
    
    return estadisticas


@router.post("/ciclo-vida/programar-limpieza")
async def programar_tarea_limpieza(
    frecuencia_dias: int = 7,
    db: AsyncSession = Depends(get_db),
    current_org: Organizacion = Depends(get_current_organization)
):
    """
    Configurar tarea programada de limpieza automática
    Nota: En producción implementar con Celery/Redis
    """
    servicio = ServicioCicloVidaDatos(db)
    configuracion = await servicio.programar_tarea_limpieza(current_org.id, frecuencia_dias)
    
    return configuracion
