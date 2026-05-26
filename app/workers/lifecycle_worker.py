"""
Worker de Celery para gestión del ciclo de vida de datos
Ley 21.719 - Eliminación automática y retención de datos
"""

from app.core.celery_app import celery_app
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def ejecutar_eliminacion_automatica(self, db=None):
    """
    Tarea programada diariamente para eliminar/anonimizar datos
    según políticas de retención definidas en el RAT
    
    Se ejecuta a las 02:00 AM hora de Chile
    """
    from app.core.database import SessionLocal
    from app.models.cumplimiento_models import PoliticaRetencionDatos, EjecucionEliminacionAutomatica
    from app.models.usuario import Usuario
    from app.models.acceso import AccesoOrganizacion
    from sqlalchemy import and_
    
    if db is None:
        db = SessionLocal()
    
    try:
        logger.info("Iniciando proceso de eliminación automática de datos")
        
        # Obtener todas las políticas de retención activas
        politicas = db.query(PoliticaRetencionDatos).filter(
            PoliticaRetencionDatos.activa == True
        ).all()
        
        resultados = {
            'usuarios_eliminados': 0,
            'accesos_revocados': 0,
            'datos_anonimizados': 0,
            'errores': []
        }
        
        for politica in politicas:
            fecha_limite = datetime.utcnow() - timedelta(days=politica.dias_retencion)
            
            try:
                if politica.tipo_dato == 'USUARIO_INACTIVO':
                    # Eliminar usuarios inactivos más allá del plazo de retención
                    usuarios_a_eliminar = db.query(Usuario).filter(
                        and_(
                            Usuario.fecha_registro < fecha_limite,
                            Usuario.id.notin_(
                                db.query(AccesoOrganizacion.usuario_id).distinct()
                            )
                        )
                    ).limit(politica.lote_maximo or 1000).all()
                    
                    for usuario in usuarios_a_eliminar:
                        # Eliminación lógica: mantener solo hashes para auditoría
                        usuario.rut_encriptado = None
                        usuario.nombre_completo = 'ELIMINADO_AUTOMATICAMENTE'
                        usuario.email = f'eliminado_{usuario.id}@deleted.local'
                        usuario.telefono = None
                        usuario.fecha_nacimiento = None
                        
                        # Registrar ejecución
                        ejecucion = EjecucionEliminacionAutomatica(
                            politica_id=politica.id,
                            tipo_ejecucion='ELIMINACION_LOGICA',
                            cantidad_registros=1,
                            estado='COMPLETADO',
                            detalle=f'Usuario {usuario.id} eliminado por política de retención'
                        )
                        db.add(ejecucion)
                        resultados['usuarios_eliminados'] += 1
                    
                    db.commit()
                    logger.info(f"Usuarios eliminados: {len(usuarios_a_eliminar)}")
                
                elif politica.tipo_dato == 'CONSENTIMIENTO_EXPIRADO':
                    # Revocar accesos con consentimiento expirado
                    accesos_a_revocar = db.query(AccesoOrganizacion).filter(
                        and_(
                            AccesoOrganizacion.fecha_expiracion < fecha_limite,
                            AccesoOrganizacion.estado == 'ACTIVO'
                        )
                    ).limit(politica.lote_maximo or 1000).all()
                    
                    for acceso in accesos_a_revocar:
                        acceso.estado = 'REVOCADO'
                        
                        # Registrar ejecución
                        ejecucion = EjecucionEliminacionAutomatica(
                            politica_id=politica.id,
                            tipo_ejecucion='REVOCACION_ACCESO',
                            cantidad_registros=1,
                            estado='COMPLETADO',
                            detalle=f'Acceso {acceso.id} revocado por expiración de consentimiento'
                        )
                        db.add(ejecucion)
                        resultados['accesos_revocados'] += 1
                    
                    db.commit()
                    logger.info(f"Accesos revocados: {len(accesos_a_revocar)}")
                
                elif politica.tipo_dato == 'LOGS_ANTIGUOS':
                    # Anonimizar logs antiguos (implementación en limpiar_logs_antiguos)
                    pass
                    
            except Exception as e:
                logger.error(f"Error procesando política {politica.id}: {str(e)}")
                resultados['errores'].append({
                    'politica_id': politica.id,
                    'error': str(e)
                })
                db.rollback()
                
                # Reintentar si es error transitorio
                if 'deadlock' in str(e).lower() or 'timeout' in str(e).lower():
                    raise self.retry(exc=e, countdown=300)  # Reintentar en 5 minutos
        
        # Resumen final
        logger.info(f"Proceso completado - Resultados: {resultados}")
        
        # Notificar al DPO si hubo errores críticos
        if len(resultados['errores']) > 0:
            from app.services.email_service import EmailService
            email_service = EmailService()
            email_service.enviar_alerta_critica(
                asunto="Errores en eliminación automática de datos",
                mensaje=f"Se encontraron {len(resultados['errores'])} errores durante el proceso de eliminación automática.\n\n"
                        f"Resultados:\n"
                        f"- Usuarios eliminados: {resultados['usuarios_eliminados']}\n"
                        f"- Accesos revocados: {resultados['accesos_revocados']}\n"
                        f"- Errores: {len(resultados['errores'])}",
                destinatarios=['dpo@organizacion.cl']
            )
        
        return resultados
        
    except Exception as e:
        logger.error(f"Error crítico en eliminación automática: {str(e)}")
        db.rollback()
        raise
    finally:
        if db is not None:
            db.close()


@celery_app.task(bind=True, max_retries=2)
def verificar_consentimientos_expirados(self, db=None):
    """
    Verifica hourly consentimientos próximos a expirar
    y envía notificaciones preventivas
    
    Se ejecuta cada hora en punto
    """
    from app.core.database import SessionLocal
    from app.models.acceso import AccesoOrganizacion
    from datetime import timedelta
    from sqlalchemy import and_
    
    if db is None:
        db = SessionLocal()
    
    try:
        logger.info("Verificando consentimientos próximos a expirar")
        
        # Consentimientos que expiran en los próximos 7 días
        fecha_proxima_expiracion = datetime.utcnow() + timedelta(days=7)
        
        consentimientos_pendientes = db.query(AccesoOrganizacion).filter(
            and_(
                AccesoOrganizacion.estado == 'ACTIVO',
                AccesoOrganizacion.fecha_expiracion <= fecha_proxima_expiracion,
                AccesoOrganizacion.fecha_expiracion > datetime.utcnow()
            )
        ).all()
        
        notificados = 0
        for acceso in consentimientos_pendientes:
            # Enviar notificación al usuario
            from app.services.email_service import EmailService
            email_service = EmailService()
            
            dias_restantes = (acceso.fecha_expiracion - datetime.utcnow()).days
            
            email_service.enviar_notificacion(
                destinatario=acceso.usuario.email,
                asunto=f"Tu consentimiento con {acceso.organizacion.razon_social} expira en {dias_restantes} días",
                template='consentimiento_expiracion',
                context={
                    'usuario': acceso.usuario,
                    'organizacion': acceso.organizacion,
                    'dias_restantes': dias_restantes,
                    'categoria_dato': acceso.categoria_dato,
                    'finalidad': acceso.finalidad,
                    'fecha_expiracion': acceso.fecha_expiracion
                }
            )
            
            notificados += 1
        
        logger.info(f"Notificaciones enviadas: {notificados}")
        return {'notificados': notificados}
        
    except Exception as e:
        logger.error(f"Error verificando consentimientos: {str(e)}")
        raise self.retry(exc=e, countdown=60)
    finally:
        if db is not None:
            db.close()


@celery_app.task(bind=True, max_retries=2)
def limpiar_logs_antiguos(self, dias_antiguedad: int = 90, db=None):
    """
    Limpia/anonimiza logs de acceso mayores a N días
    
    Se ejecuta semanalmente (domingo 03:00 AM)
    """
    from app.core.database import SessionLocal
    from app.models.log_acceso import LogAccesoDatos
    from datetime import timedelta
    
    if db is None:
        db = SessionLocal()
    
    try:
        logger.info(f"Limpiando logs antiguos (> {dias_antiguedad} días)")
        
        fecha_limite = datetime.utcnow() - timedelta(days=dias_antiguedad)
        
        # Contar logs a eliminar
        logs_a_eliminar = db.query(LogAccesoDatos).filter(
            LogAccesoDatos.fecha_acceso < fecha_limite
        ).limit(10000).all()
        
        cantidad_eliminada = len(logs_a_eliminar)
        
        # Eliminación física de logs antiguos
        for log in logs_a_eliminar:
            db.delete(log)
        
        db.commit()
        
        logger.info(f"Logs eliminados: {cantidad_eliminada}")
        return {'logs_eliminados': cantidad_eliminada}
        
    except Exception as e:
        logger.error(f"Error limpiando logs: {str(e)}")
        db.rollback()
        raise self.retry(exc=e, countdown=120)
    finally:
        if db is not None:
            db.close()
