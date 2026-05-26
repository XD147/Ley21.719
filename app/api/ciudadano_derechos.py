"""
API de Derechos del Ciudadano (Ley 21.719)
Endpoints para portabilidad, supresión, timeline de accesos y oposición a IA.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import json

from app.core.database import get_db
from app.core.security import get_current_usuario
from app.models.core_models import Usuario
from app.services.portabilidad_service import PortabilidadService
from app.services.supresion_service import SupresionService

router = APIRouter(prefix="/api/v1/ciudadano", tags=["Derechos Ciudadano"])


@router.get("/mis-datos")
def obtener_mis_datos_completos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_usuario)
):
    """
    Obtiene TODOS los datos personales del ciudadano.
    Incluye información personal, consentimientos, historial de accesos y solicitudes ARCO.
    """
    try:
        datos = PortabilidadService.obtener_datos_usuario_completos(db, str(current_user.id))
        return {
            "success": True,
            "data": datos,
            "mensaje": "Datos obtenidos exitosamente"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo datos: {str(e)}")


@router.get("/portabilidad/json")
def exportar_portabilidad_json(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_usuario)
):
    """
    Exporta todos los datos en formato JSON estructurado (Art. 18).
    Listo para transferir a competidor.
    """
    try:
        json_content = PortabilidadService.exportar_json(db, str(current_user.id))
        return Response(
            content=json_content,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=portabilidad_{current_user.rut_hash}.json"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exportando JSON: {str(e)}")


@router.get("/portabilidad/csv")
def exportar_portabilidad_csv(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_usuario)
):
    """
    Exporta datos en múltiples archivos CSV por categoría.
    Retorna el primer CSV (información personal) como ejemplo.
    """
    try:
        csv_files = PortabilidadService.exportar_csv(db, str(current_user.id))
        
        # Retornamos el CSV de información personal como ejemplo
        # En frontend real, se podría descargar un ZIP con todos
        return Response(
            content=csv_files['informacion_personal.csv'],
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=informacion_personal.csv"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exportando CSV: {str(e)}")


@router.get("/portabilidad/xml")
def exportar_portabilidad_xml(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_usuario)
):
    """
    Exporta todos los datos en formato XML.
    """
    try:
        xml_content = PortabilidadService.exportar_xml(db, str(current_user.id))
        return Response(
            content=xml_content,
            media_type="application/xml",
            headers={
                "Content-Disposition": f"attachment; filename=portabilidad_{current_user.rut_hash}.xml"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exportando XML: {str(e)}")


@router.post("/portabilidad/token-transferencia")
def generar_token_transferencia(
    organizacion_destino: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_usuario)
):
    """
    Genera token seguro de un solo uso para transferencia directa a competidor.
    Válido por 24 horas.
    """
    try:
        token = PortabilidadService.generar_token_portabilidad(
            db, 
            str(current_user.id),
            organizacion_destino
        )
        return {
            "success": True,
            "token": token,
            "expires_in_hours": 24,
            "uso_unico": True,
            "mensaje": "Token generado. Comparte este token con la organización destino."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando token: {str(e)}")


@router.post("/supresion/solicitar")
def solicitar_supresion(
    motivo: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_usuario)
):
    """
    Solicita eliminación de datos personales (Derecho al Olvido, Art. 17).
    Genera certificado de eliminación descargable.
    """
    try:
        resultado = SupresionService.solicitar_supresion(
            db,
            str(current_user.id),
            current_user.rut_hash,
            motivo
        )
        return {
            "success": True,
            "solicitud_id": str(resultado['solicitud_id']),
            "certificado_disponible": resultado['certificado_generado'],
            "estado": "PROCESANDO",
            "mensaje": "Solicitud de supresión creada. Se eliminarán los datos en 10 días hábiles.",
            "fecha_ejecucion_estimada": resultado['fecha_ejecucion']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error solicitando supresión: {str(e)}")


@router.get("/supresion/estado/{solicitud_id}")
def obtener_estado_supresion(
    solicitud_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_usuario)
):
    """
    Obtiene el estado de una solicitud de supresión.
    """
    try:
        from app.models.cumplimiento_models import SolicitudSupresion
        solicitud = db.query(SolicitudSupresion).filter(
            SolicitudSupresion.id == solicitud_id,
            SolicitudSupresion.rut_ciudadano_hash == current_user.rut_hash
        ).first()
        
        if not solicitud:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada")
        
        return {
            "success": True,
            "solicitud": {
                "id": str(solicitud.id),
                "estado": solicitud.estado.value,
                "motivo": solicitud.motivo,
                "fecha_solicitud": solicitud.fecha_solicitud.isoformat(),
                "fecha_ejecucion": solicitud.fecha_ejecucion.isoformat() if solicitud.fecha_ejecucion else None,
                "certificado_generado": solicitud.certificado_generado
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error consultando estado: {str(e)}")


@router.get("/supresion/certificado/{solicitud_id}")
def descargar_certificado_supresion(
    solicitud_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_usuario)
):
    """
    Descarga certificado de eliminación de datos (PDF).
    Solo disponible si la supresión fue completada.
    """
    try:
        from app.models.cumplimiento_models import SolicitudSupresion
        solicitud = db.query(SolicitudSupresion).filter(
            SolicitudSupresion.id == solicitud_id,
            SolicitudSupresion.rut_ciudadano_hash == current_user.rut_hash
        ).first()
        
        if not solicitud:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada")
        
        if solicitud.estado.value != 'COMPLETADO':
            raise HTTPException(status_code=400, detail="Certificado no disponible. La supresión aún no se completa.")
        
        certificado_pdf = SupresionService.generar_certificado_pdf(db, str(solicitud.id))
        
        return Response(
            content=certificado_pdf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=certificado_supresion_{solicitud_id}.pdf"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error descargando certificado: {str(e)}")


@router.get("/timeline-accesos")
def obtener_timeline_accesos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_usuario)
):
    """
    Obtiene timeline cronológico de todos los accesos a los datos del ciudadano.
    Muestra: fecha, organización, tipo de acceso, dato consultado, propósito.
    """
    try:
        from app.models.core_models import LogAccesoDatos, AccesoOrganizacion
        
        # Obtener logs de acceso
        logs = db.query(LogAccesoDatos).filter(
            LogAccesoDatos.usuario_id == current_user.id
        ).order_by(LogAccesoDatos.fecha_acceso.desc()).limit(50).all()
        
        # Obtener consentimientos activos
        consentimientos = db.query(AccesoOrganizacion).filter(
            AccesoOrganizacion.usuario_id == current_user.id
        ).order_by(AccesoOrganizacion.fecha_otorgamiento.desc()).all()
        
        # Construir timeline unificado
        timeline = []
        
        for log in logs:
            timeline.append({
                "tipo_evento": "ACCESO",
                "fecha": log.fecha_acceso.isoformat() if log.fecha_acceso else None,
                "organizacion_id": str(log.organizacion_id),
                "descripcion": f"{log.tipo_acceso} de {log.categoria_dato_consultado}",
                "detalle": {
                    "tipo_acceso": log.tipo_acceso,
                    "categoria_dato": log.categoria_dato_consultado,
                    "justificacion": log.justificacion_legal,
                    "ip_origen": log.ip_origen
                }
            })
        
        for consentimiento in consentimientos:
            timeline.append({
                "tipo_evento": "CONSENTIMIENTO",
                "fecha": consentimiento.fecha_otorgamiento.isoformat() if consentimiento.fecha_otorgamiento else None,
                "organizacion_id": str(consentimiento.organizacion_id),
                "descripcion": f"Consentimiento otorgado para {consentimiento.categoria_dato}",
                "detalle": {
                    "categoria_dato": consentimiento.categoria_dato,
                    "finalidad": consentimiento.finalidad,
                    "estado": consentimiento.estado,
                    "fecha_expiracion": consentimiento.fecha_expiracion.isoformat() if consentimiento.fecha_expiracion else None
                }
            })
        
        # Ordenar por fecha descendente
        timeline.sort(key=lambda x: x['fecha'] or '', reverse=True)
        
        return {
            "success": True,
            "timeline": timeline,
            "total_eventos": len(timeline),
            "mensaje": "Timeline de accesos obtenido exitosamente"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo timeline: {str(e)}")


@router.post("/oposicion-ia")
def solicitar_oposicion_decision_automatizada(
    tipo_decision: str,
    descripcion_decision: str,
    motivo_oposicion: str,
    solicita_intervencion_humana: bool = True,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_usuario)
):
    """
    Solicita oposición a decisión automatizada y/o intervención humana (Art. 16).
    El ciudadano puede impugnar decisiones tomadas exclusivamente por algoritmos.
    """
    try:
        from app.models.decision_ia_models import DecisionAutomatizada, EstadoImpugnacion, TipoDecisionAutomatizada
        
        # Mapear tipo de decisión
        try:
            tipo_enum = TipoDecisionAutomatizada(tipo_decision.upper())
        except ValueError:
            tipo_enum = TipoDecisionAutomatizada.OTRO
        
        # Crear registro de impugnación
        decision = DecisionAutomatizada(
            usuario_id=current_user.id,
            organizacion_id=None,  # Se debería pasar como parámetro
            tipo_decision=tipo_enum,
            descripcion_decision=descripcion_decision,
            algoritmo_nombre="No especificado",  # Debería venir de la organización
            estado_impugnacion=EstadoImpugnacion.PENDIENTE,
            fecha_impugnacion=datetime.utcnow(),
            motivo_impugnacion=motivo_oposicion,
            solicitud_intervencion_humana=solicita_intervencion_humana
        )
        
        db.add(decision)
        db.commit()
        db.refresh(decision)
        
        return {
            "success": True,
            "impugnacion_id": str(decision.id),
            "estado": EstadoImpugnacion.PENDIENTE.value,
            "intervencion_humana_solicitada": solicita_intervencion_humana,
            "mensaje": "Oposición registrada. La organización debe revisar su decisión en 5 días hábiles.",
            "proximos_pasos": [
                "La organización recibirá notificación de tu impugnación",
                "Deben designar un revisor humano si lo solicitaste",
                "Tienes derecho a recibir explicación de la decisión algorítmica",
                "Plazo máximo de respuesta: 5 días hábiles"
            ]
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error registrando oposición: {str(e)}")


@router.get("/oposicion-ia/historial")
def obtener_historial_oposiciones(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_usuario)
):
    """
    Obtiene historial de oposiciones a decisiones automatizadas.
    """
    try:
        from app.models.decision_ia_models import DecisionAutomatizada
        
        decisiones = db.query(DecisionAutomatizada).filter(
            DecisionAutomatizada.usuario_id == current_user.id
        ).order_by(DecisionAutomatizada.created_at.desc()).all()
        
        historial = [
            {
                "id": str(d.id),
                "tipo_decision": d.tipo_decision.value,
                "descripcion": d.descripcion_decision,
                "estado_impugnacion": d.estado_impugnacion.value,
                "fecha_impugnacion": d.fecha_impugnacion.isoformat() if d.fecha_impugnacion else None,
                "solicito_intervencion_humana": d.solicitud_intervencion_humana,
                "decision_modificada": d.decision_final_modificada
            }
            for d in decisiones
        ]
        
        return {
            "success": True,
            "historial": historial,
            "total": len(historial)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo historial: {str(e)}")
