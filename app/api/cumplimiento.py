"""
Endpoints API para funcionalidades completas Ley 21.719
RAT, Brechas, Webhooks, EIPD y Panel DPO
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.database import get_db
from app.models.models import Organizacion
from app.services.rat_service import ServicioRAT, RegistroActividadesTratamiento
from app.services.brechas_service import ServicioBrechas, NotificacionBrecha
from app.services.webhooks_service import ServicioWebhooks, notificar_revocacion_consentimiento, notificar_solicitud_arco, notificar_brecha_seguridad
from app.services.eipd_service import ServicioEIPD, EvaluacionImpactoProteccionDatos
from app.services.panel_dpo_service import PanelDPOService
from app.api.routes import get_current_organization

router = APIRouter(tags=["cumplimiento-ley-21719"])

# ==================== RAT (Registro Actividades Tratamiento) ====================

@router.post("/rat", response_model=dict, status_code=status.HTTP_201_CREATED)
async def crear_registro_rat(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_org: Organizacion = Depends(get_current_organization)
):
    """Crear nuevo registro de actividad de tratamiento (Art. 27)"""
    servicio = ServicioRAT(db)
    
    # Agregar organizacion_id del usuario autenticado
    data["organizacion_id"] = current_org.id
    data["responsable_registro"] = current_org.razon_social if current_org.razon_social else "Desconocido"
    
    registro = await servicio.crear_registro(data)
    
    return {
        "id": str(registro.id),
        "nombre": registro.nombre_actividad,
        "finalidad": registro.finalidad.value,
        "fecha_creacion": registro.fecha_creacion.isoformat()
    }


@router.get("/rat", response_model=List[dict])
async def listar_rat(
    db: AsyncSession = Depends(get_db),
    current_org: Organizacion = Depends(get_current_organization)
):
    """Listar todos los registros RAT de la organización"""
    servicio = ServicioRAT(db)
    registros = await servicio.obtener_por_organizacion(current_org.id)
    
    return [
        {
            "id": str(r.id),
            "nombre": r.nombre_actividad,
            "descripcion": r.descripcion,
            "finalidad": r.finalidad.value,
            "categorias_datos": r.categorias_datos,
            "tiene_transferencia_internacional": r.tiene_transferencia_internacional,
            "fecha_creacion": r.fecha_creacion.isoformat()
        }
        for r in registros
    ]


@router.get("/rat/{registro_id}")
async def obtener_rat(
    registro_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_org: Organizacion = Depends(get_current_organization)
):
    """Obtener detalle de registro RAT"""
    servicio = ServicioRAT(db)
    registro = await servicio.obtener_por_organizacion(current_org.id)
    registro_found = next((r for r in registro if str(r.id) == str(registro_id)), None)
    
    if not registro_found:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    
    return {
        "id": str(registro_found.id),
        "nombre": registro_found.nombre_actividad,
        "descripcion": registro_found.descripcion,
        "finalidad": registro_found.finalidad.value,
        "categorias_datos": registro_found.categorias_datos,
        "categorias_titulares": registro_found.categorias_titulares,
        "plazo_conservacion_dias": registro_found.plazo_conservacion_dias,
        "medidas_seguridad": registro_found.medidas_seguridad,
        "encargados_tratamiento": registro_found.encargados_tratamiento,
        "base_legal": registro_found.base_legal
    }


@router.get("/rat/reporte")
async def generar_reporte_rat(
    db: AsyncSession = Depends(get_db),
    current_org: Organizacion = Depends(get_current_organization)
):
    """Generar reporte completo RAT para auditoría"""
    servicio = ServicioRAT(db)
    return await servicio.generar_reporte_rat(current_org.id)


# ==================== BRECHAS DE SEGURIDAD ====================

@router.post("/brechas", response_model=dict, status_code=status.HTTP_201_CREATED)
async def crear_notificacion_brecha(
    data: dict,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_org: Organizacion = Depends(get_current_organization)
):
    """Crear notificación de brecha de seguridad (Art. 38-40)"""
    servicio = ServicioBrechas(db)
    
    data["creado_por"] = current_org.razon_social if current_org.razon_social else "Desconocido"
    brecha = await servicio.crear_brecha(data, current_org.id)
    
    # Si el riesgo es ALTO o MUY_ALTO, notificar automáticamente
    if brecha.nivel_riesgo.value in ["ALTO", "MUY_ALTO"]:
        organizacion = {"webhookUrlRevocacion": current_org.webhookUrlRevocacion}
        if organizacion and organizacion.get("webhookUrlRevocacion"):
            background_tasks.add_task(
                notificar_brecha_seguridad,
                db,
                current_org.id,
                brecha.id,
                brecha.nivel_riesgo.value,
                organizacion["webhookUrlRevocacion"]
            )
    
    return {
        "id": str(brecha.id),
        "titulo": brecha.titulo,
        "nivel_riesgo": brecha.nivel_riesgo.value,
        "cumple_plazo_72h": brecha.cumple_plazo_72h,
        "horas_transcurridas": brecha.horas_transcurridas,
        "estado": brecha.estado.value
    }


@router.get("/brechas")
async def listar_brechas(
    estado: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_org: Organizacion = Depends(get_current_organization)
):
    """Listar notificaciones de brechas"""
    servicio = ServicioBrechas(db)
    
    if estado == "PENDIENTES":
        brechas = await servicio.obtener_brechas_pendientes(current_org.id)
    else:
        # Obtener todas (implementar filtro por organización en el servicio)
        brechas = []
    
    return [
        {
            "id": str(b.id),
            "titulo": b.titulo,
            "tipo_brecha": b.tipo_brecha.value,
            "nivel_riesgo": b.nivel_riesgo.value,
            "estado": b.estado.value,
            "cumple_plazo_72h": b.cumple_plazo_72h,
            "horas_transcurridas": b.horas_transcurridas,
            "fecha_descubrimiento": b.fecha_descubrimiento.isoformat()
        }
        for b in brechas
    ]


@router.post("/brechas/{brecha_id}/notificar-agencia")
async def notificar_brecha_a_agencia(
    brecha_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_org: Organizacion = Depends(get_current_organization)
):
    """Enviar notificación formal a la Agencia de Protección de Datos"""
    servicio = ServicioBrechas(db)
    resultado = await servicio.notificar_agencia(brecha_id)
    
    if "error" in resultado:
        raise HTTPException(status_code=400, detail=resultado["error"])
    
    return resultado


@router.post("/brechas/{brecha_id}/notificar-afectados")
async def notificar_brecha_a_afectados(
    brecha_id: UUID,
    plantilla: str,
    db: AsyncSession = Depends(get_db),
    current_org: Organizacion = Depends(get_current_organization)
):
    """Notificar brecha a los afectados (requiere riesgo ALTO/MUY_ALTO)"""
    servicio = ServicioBrechas(db)
    resultado = await servicio.notificar_afectados(brecha_id, plantilla)
    
    if "error" in resultado:
        raise HTTPException(status_code=400, detail=resultado["error"])
    
    return resultado


@router.get("/brechas/estadisticas")
async def obtener_estadisticas_brechas(
    periodo_dias: int = 365,
    db: AsyncSession = Depends(get_db),
    current_org: Organizacion = Depends(get_current_organization)
):
    """Obtener estadísticas de brechas"""
    servicio = ServicioBrechas(db)
    return await servicio.generar_estadisticas_brechas(current_org.id, periodo_dias)


# ==================== WEBHOOKS ====================

@router.get("/webhooks")
async def listar_webhooks(
    limite: int = 50,
    db: AsyncSession = Depends(get_db),
    current_org: Organizacion = Depends(get_current_organization)
):
    """Listar historial de webhooks enviados"""
    servicio = ServicioWebhooks(db)
    webhooks = await servicio.obtener_historial(current_org.id, limite)
    
    return [
        {
            "id": str(w.id),
            "tipo_evento": w.tipo_evento.value,
            "estado": w.estado.value,
            "url_destino": w.url_destino,
            "intentos": w.intentos,
            "fecha_creacion": w.fecha_creacion.isoformat(),
            "fecha_envio": w.fecha_envio.isoformat() if w.fecha_envio else None
        }
        for w in webhooks
    ]


@router.post("/webhooks/{registro_id}/reenviar")
async def reenviar_webhook(
    registro_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_org: Organizacion = Depends(get_current_organization)
):
    """Reenviar webhook fallido"""
    servicio = ServicioWebhooks(db)
    return await servicio.enviar_webhook(registro_id)


# ==================== EIPD (Evaluación de Impacto) ====================

@router.post("/eipd", response_model=dict, status_code=status.HTTP_201_CREATED)
async def crear_evaluacion_impacto(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_org: Organizacion = Depends(get_current_organization)
):
    """Crear nueva Evaluación de Impacto en Protección de Datos (Art. 34)"""
    servicio = ServicioEIPD(db)
    data["organizacion_id"] = current_org.id
    
    evaluacion = await servicio.crear_evaluacion(data)
    
    return {
        "id": str(evaluacion.id),
        "nombre": evaluacion.nombre_evaluacion,
        "requiere_obligatoria": evaluacion.requiere_eipd_obligatoria,
        "estado": evaluacion.estado.value,
        "fecha_creacion": evaluacion.fecha_creacion.isoformat()
    }


@router.get("/eipd")
async def listar_eipd(
    db: AsyncSession = Depends(get_db),
    current_org: Organizacion = Depends(get_current_organization)
):
    """Listar evaluaciones de impacto"""
    from sqlalchemy import select
    from app.services.eipd_service import EvaluacionImpactoProteccionDatos
    
    result = await db.execute(
        select(EvaluacionImpactoProteccionDatos)
        .where(EvaluacionImpactoProteccionDatos.organizacion_id == current_org.id)
        .order_by(EvaluacionImpactoProteccionDatos.fecha_creacion.desc())
    )
    evaluaciones = list(result.scalars().all())
    
    return [
        {
            "id": str(e.id),
            "nombre": e.nombre_evaluacion,
            "estado": e.estado.value,
            "nivel_riesgo_inicial": e.nivel_riesgo_inicial.value if e.nivel_riesgo_inicial else None,
            "nivel_riesgo_residual": e.nivel_riesgo_residual.value if e.nivel_riesgo_residual else None,
            "fecha_creacion": e.fecha_creacion.isoformat()
        }
        for e in evaluaciones
    ]


@router.get("/eipd/{eipd_id}")
async def obtener_eipd_detalle(
    eipd_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_org: Organizacion = Depends(get_current_organization)
):
    """Obtener detalle completo de EIPD"""
    servicio = ServicioEIPD(db)
    return await servicio.generar_reporte_eipd(eipd_id)


@router.post("/eipd/{eipd_id}/dictamen-dpo")
async def registrar_dictamen_dpo(
    eipd_id: UUID,
    dictamen: str,
    aprobada: bool,
    dpo_nombre: str,
    db: AsyncSession = Depends(get_db),
    current_org: Organizacion = Depends(get_current_organization)
):
    """Registrar dictamen del DPO sobre EIPD"""
    servicio = ServicioEIPD(db)
    resultado = await servicio.registrar_dictamen_dpo(eipd_id, dictamen, aprobada, dpo_nombre)
    
    if not resultado:
        raise HTTPException(status_code=404, detail="EIPD no encontrada")
    
    return {
        "id": str(resultado.id),
        "estado": resultado.estado.value,
        "dictamen_dpo": resultado.dpo_dictamen,
        "fecha_aprobacion": resultado.fecha_aprobacion.isoformat() if resultado.fecha_aprobacion else None
    }


# ==================== PANEL DPO ====================

@router.get("/panel-dpo/metricas")
async def obtener_metricas_panel_dpo(
    db: AsyncSession = Depends(get_db),
    current_org: Organizacion = Depends(get_current_organization)
):
    """Obtener métricas generales del panel DPO"""
    servicio = PanelDPOService(db)
    return await servicio.obtener_metricas_generales(current_org.id)


@router.get("/panel-dpo/alertas")
async def obtener_alertas_dpo(
    db: AsyncSession = Depends(get_db),
    current_org: Organizacion = Depends(get_current_organization)
):
    """Obtener alertas críticas que requieren atención del DPO"""
    servicio = PanelDPOService(db)
    return await servicio.obtener_alertas_criticas(current_org.id)


@router.get("/panel-dpo/reporte-cumplimiento")
async def generar_reporte_cumplimiento(
    periodo_dias: int = 90,
    db: AsyncSession = Depends(get_db),
    current_org: Organizacion = Depends(get_current_organization)
):
    """Generar reporte completo de cumplimiento normativo"""
    servicio = PanelDPOService(db)
    return await servicio.generar_reporte_cumplimiento(current_org.id, periodo_dias)


@router.get("/panel-dpo/calendario")
async def obtener_calendario_cumplimiento(
    meses: int = 6,
    db: AsyncSession = Depends(get_db),
    current_org: Organizacion = Depends(get_current_organization)
):
    """Obtener calendario de eventos de cumplimiento próximos"""
    servicio = PanelDPOService(db)
    return await servicio.obtener_calendario_cumplimiento(current_org.id, meses)
