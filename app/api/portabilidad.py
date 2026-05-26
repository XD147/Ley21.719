"""
API de Portabilidad y Notificaciones para Ley 21.719
Endpoints para exportación/importación de datos y notificaciones de brechas
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.api.routes import get_current_usuario, get_current_organization
from app.services.portabilidad import get_portabilidad_service
from app.services.notificaciones import notificacion_service
from app.models.models import Usuario, Organizacion
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Portabilidad y Notificaciones"])

# === Modelos Pydantic ===

class ExportarDatosRequest(BaseModel):
    formato: str = Field(default="json", description="json, csv")
    incluir_historial: bool = True

class ImportarDatosRequest(BaseModel):
    datos_json: str
    organizacion_origen_id: str
    confirmar_actualizacion: bool = True

class NotificarBrechaRequest(BaseModel):
    descripcion: str
    datos_afectados: List[str]
    medidas_tomadas: str
    notificar_afectados: bool = False
    recomendaciones: Optional[str] = None

class UsuariosAfectadosRequest(BaseModel):
    usuario_ids: List[str]
    brecha_descripcion: str
    recomendaciones: str

# === Endpoints de Portabilidad (Art. 20) ===

@router.post("/portabilidad/exportar")
async def exportar_datos_personales(
    request: ExportarDatosRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario)
):
    """
    Exporta todos los datos personales del usuario en formato estructurado.
    Derecho a la portabilidad (Art. 20 Ley 21.719).
    """
    try:
        service = get_portabilidad_service(db)
        resultado = await service.exportar_datos_usuario(
            usuario_id=str(usuario.id),
            formato=request.formato
        )
        
        return {
            "estado": "EXITOSO",
            "formato": resultado["formato"],
            "datos": resultado["datos"],
            "mensaje": f"Exportación completada con {len(resultado['datos'])} caracteres"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error exportando datos: {e}")
        raise HTTPException(status_code=500, detail="Error interno al exportar datos")

@router.post("/portabilidad/importar")
async def importar_datos_portabilidad(
    request: ImportarDatosRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario)
):
    """
    Importa datos desde otra organización (portabilidad entrante).
    Requiere confirmación explícita del usuario.
    """
    if not request.confirmar_actualizacion:
        raise HTTPException(
            status_code=400, 
            detail="Debe confirmar la actualización de datos"
        )
    
    try:
        service = get_portabilidad_service(db)
        resultado = await service.importar_datos_portabilidad(
            usuario_id=str(usuario.id),
            datos_json=request.datos_json,
            organizacion_origen_id=request.organizacion_origen_id
        )
        
        return {
            "estado": "EXITOSO",
            **resultado
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error importando datos: {e}")
        raise HTTPException(status_code=500, detail="Error interno al importar datos")

@router.get("/portabilidad/formato-estandar")
async def obtener_formato_estandar():
    """
    Retorna el esquema JSON estándar para portabilidad.
    Útil para que organizaciones se preparen para recibir datos.
    """
    return {
        "version": "1.0",
        "schema": {
            "metadata": {
                "fecha_exportacion": "ISO8601",
                "formato": "json|csv|xml",
                "version_esquema": "1.0",
                "sujeto_datos": {
                    "id_interno": "UUID",
                    "rut_hash": "SHA256 parcial",
                    "nombre": "string"
                }
            },
            "datos_personales": {
                "perfil": {"nombre_completo", "email", "telefono", "fecha_nacimiento"},
                "consentimientos_activos": [{"organizacion_id", "categoria", "finalidad"}],
                "historial_accesos": [{"organizacion_id", "tipo_acceso", "fecha"}]
            }
        }
    }

# === Endpoints de Notificación de Brechas (Art. 38-40) ===

@router.post("/brechas/notificar-agencia")
async def notificar_brecha_agencia_endpoint(
    request: NotificarBrechaRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    organizacion: Organizacion = Depends(get_current_organization)
):
    """
    Notifica brecha de seguridad a la Agencia Digital dentro de 72h.
    Obligatorio cuando hay riesgo para derechos de personas (Art. 38).
    """
    # Generar ID único de brecha (en producción usar UUID)
    import uuid
    brecha_id = str(uuid.uuid4())
    
    resultado = await notificacion_service.notificar_brecha_agencia(
        brecha_id=brecha_id,
        descripcion=request.descripcion,
        datos_afectados=request.datos_afectados,
        medidas_tomadas=request.medidas_tomadas,
        organizacion_rut=organizacion.rut
    )
    
    if resultado.get("estado") == "FALLIDO":
        # Reintentar en background
        background_tasks.add_task(
            notificacion_service.notificar_brecha_agencia,
            brecha_id,
            request.descripcion,
            request.datos_afectados,
            request.medidas_tomadas,
            organizacion.rut
        )
        return {
            "estado": "ENCOLADO_REINTENTO",
            "brecha_id": brecha_id,
            "mensaje": "Notificación falló, reintentando en background"
        }
    
    return {
        "estado": "NOTIFICADO",
        "brecha_id": brecha_id,
        "acuse_recibo": resultado
    }

@router.post("/brechas/notificar-afectados")
async def notificar_usuarios_afectados(
    request: UsuariosAfectadosRequest,
    db: Session = Depends(get_db),
    organizacion: Organizacion = Depends(get_current_organization)
):
    """
    Notifica a usuarios afectados por brecha de seguridad.
    Obligatorio cuando hay alto riesgo (Art. 39).
    Lenguaje claro sin tecnicismos.
    """
    # Obtener detalles de usuarios
    from sqlalchemy import select
    result = await db.execute(
        select(Usuario).where(Usuario.id.in_(request.usuario_ids))
    )
    usuarios = result.scalars().all()
    
    if len(usuarios) != len(request.usuario_ids):
        raise HTTPException(
            status_code=400, 
            detail="Algunos usuarios no encontrados"
        )
    
    # Preparar lista para notificación
    usuarios_para_notificar = [
        {
            "id": str(u.id),
            "nombre": u.nombre_completo,
            "email": u.email,
            "datos_afectados": ["EMAIL", "NOMBRE"]  # Personalizar según caso
        }
        for u in usuarios
    ]
    
    enviados = await notificacion_service.notificar_afectados(
        usuarios_afectados=usuarios_para_notificar,
        brecha_descripcion=request.brecha_descripcion,
        recomendaciones=request.recomendaciones,
        organizacion_nombre=organizacion.razon_social
    )
    
    return {
        "estado": "COMPLETADO",
        "usuarios_notificados": enviados,
        "total_solicitados": len(request.usuario_ids)
    }

@router.get("/brechas/guia-notificacion")
async def obtener_guia_notificacion():
    """
    Guía rápida para notificación de brechas según nivel de riesgo.
    Basado en Art. 38-40 Ley 21.719.
    """
    return {
        "nivel_riesgo_alto": {
            "ejemplos": ["Datos salud", "Biométricos", "Financieros", "Conducta sexual"],
            "notificar_agencia": True,
            "notificar_afectados": True,
            "plazo_horas": 72
        },
        "nivel_riesgo_medio": {
            "ejemplos": ["Email + Nombre", "Teléfono", "Dirección"],
            "notificar_agencia": True,
            "notificar_afectados": "Solo si no hay cifrado",
            "plazo_horas": 72
        },
        "excepciones_no_notificar": [
            "Datos cifrados con clave no comprometida",
            "Medidas posteriores eliminan riesgo",
            "Requeriría esfuerzo desproporcionado (publicidad masiva)"
        ],
        "contenido_minimo_notificacion": [
            "Descripción clara de hechos",
            "Categorías de datos afectados",
            "Recomendaciones para protegerse",
            "Contacto DPO para más información"
        ]
    }
