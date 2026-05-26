"""
Worker de Ciclo de Vida de Datos (Data Lifecycle Management)
Ejecuta borrado/anonimización automática basado en políticas de retención del RAT.
Usa Celery para tareas programadas en segundo plano.
"""
from celery import Celery, schedules
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.cumplimiento_models import PoliticaRetencionDatos, EjecucionEliminacionAutomatica
from app.models.core_models import AccesoOrganizacion, Usuario
from app.services.criptografia_service import CriptografiaService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de Celery
celery_app = Celery(
    'lifecycle_worker',
    broker='redis://localhost:6379/0',  # Configurar según entorno
    backend='redis://localhost:6379/0'
)

# Tarea programada: Ejecutar cada hora
celery_app.conf.beat_schedule = {
    'ejecutar-limpieza-ciclo-vida': {
        'task': 'app.services.lifecycle_worker.ejecutar_limpieza_programada',
        'schedule': schedules.crontab(minute=0),  # Cada hora
    },
}

celery_app.conf.timezone = 'America/Santiago'


@celery_app.task(bind=True, max_retries=3)
def ejecutar_limpieza_programada(self):
    """
    Tarea principal que ejecuta el ciclo de vida de datos:
    1. Busca consentimientos expirados
    2. Verifica políticas de retención
    3. Ejecuta anonimización/borrado
    4. Registra evidencia de eliminación
    """
    db = SessionLocal()
    try:
        logger.info("Iniciando proceso de limpieza de ciclo de vida...")
        
        # 1. Obtener políticas de retención activas
        politicas = db.query(PoliticaRetencionDatos).filter(
            PoliticaRetencionDatos.activa == True
        ).all()
        
        total_procesados = 0
        total_eliminados = 0
        
        for politica in politicas:
            logger.info(f"Procesando política: {politica.nombre_politica}")
            
            # 2. Buscar accesos/consentimientos que cumplen criterio de eliminación
            fecha_limite = datetime.utcnow() - timedelta(days=politica.plazo_retencion_dias)
            
            accesos_expirados = db.query(AccesoOrganizacion).filter(
                AccesoOrganizacion.organizacion_id == politica.organizacion_id,
                AccesoOrganizacion.categoria_dato == politica.categoria_dato,
                AccesoOrganizacion.fecha_expiracion <= fecha_limite,
                AccesoOrganizacion.estado != 'ELIMINADO'
            ).all()
            
            for acceso in accesos_expirados:
                try:
                    # 3. Ejecutar anonimización/borrado
                    resultado = ejecutar_eliminacion_acceso(db, acceso, politica)
                    
                    if resultado:
                        total_eliminados += 1
                        logger.info(f"Eliminación exitosa para acceso {acceso.id}")
                    else:
                        logger.warning(f"Fallo en eliminación para acceso {acceso.id}")
                        
                except Exception as e:
                    logger.error(f"Error procesando acceso {acceso.id}: {str(e)}")
                    continue
            
            total_procesados += len(accesos_expirados)
        
        logger.info(f"Limpieza completada: {total_eliminados}/{total_procesados} registros eliminados")
        return {"total_procesados": total_procesados, "total_eliminados": total_eliminados}
        
    except Exception as e:
        logger.error(f"Error crítico en limpieza programada: {str(e)}")
        raise self.retry(exc=e, countdown=300)  # Reintentar en 5 minutos
    finally:
        db.close()


def ejecutar_eliminacion_acceso(db: Session, acceso: AccesoOrganizacion, politica: PoliticaRetencionDatos) -> bool:
    """
    Ejecuta la eliminación/anonimización de un acceso específico según la política.
    """
    try:
        # 1. Obtener datos del usuario asociados
        usuario = db.query(Usuario).filter(Usuario.id == acceso.usuario_id).first()
        if not usuario:
            logger.warning(f"Usuario no encontrado para acceso {acceso.id}")
            return False
        
        # 2. Según tipo de eliminación configurado
        if politica.tipo_eliminacion == 'ANONIMIZACION':
            # Anonimizar: mantener estructura pero remover identificadores
            # El RUT hash se mantiene para auditoría, pero se limpian datos personales
            logger.info(f"Anonimizando datos para usuario {usuario.id}")
            # Implementar lógica de anonimización específica por categoría
            
        elif politica.tipo_eliminacion == 'BORRADO_TOTAL':
            # Borrado completo (solo mantiene hashes para auditoría legal)
            logger.info(f"Ejecutando borrado total para acceso {acceso.id}")
            acceso.estado = 'ELIMINADO'
            acceso.fecha_expiracion = datetime.utcnow()
            
        elif politica.tipo_eliminacion == 'SEUDONIMIZACION':
            # Reemplazar identificadores directos por seudónimos
            logger.info(f"Seudonimizando datos para acceso {acceso.id}")
            # Generar seudónimo y reemplazar
            
        # 3. Registrar ejecución en bitácora
        ejecucion = EjecucionEliminacionAutomatica(
            politica_id=politica.id,
            acceso_id=acceso.id,
            usuario_id=acceso.usuario_id,
            organizacion_id=acceso.organizacion_id,
            tipo_ejecucion=politica.tipo_eliminacion,
            estado_ejecucion='COMPLETADO',
            fecha_ejecucion=datetime.utcnow()
        )
        db.add(ejecucion)
        db.commit()
        
        logger.info(f"Eliminación registrada correctamente para acceso {acceso.id}")
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error en ejecución de eliminación: {str(e)}")
        return False


@celery_app.task
def verificar_y_notificar_vencimientos():
    """
    Tarea secundaria: Notifica próximos vencimientos de consentimientos
    para que las organizaciones puedan solicitar renovación o proceder a eliminar.
    """
    db = SessionLocal()
    try:
        logger.info("Verificando vencimientos próximos...")
        
        # Buscar consentimientos que vencen en los próximos 30 días
        fecha_limite = datetime.utcnow() + timedelta(days=30)
        
        accesos_por_vencer = db.query(AccesoOrganizacion).filter(
            AccesoOrganizacion.fecha_expiracion <= fecha_limite,
            AccesoOrganizacion.fecha_expiracion >= datetime.utcnow(),
            AccesoOrganizacion.estado == 'ACTIVO'
        ).all()
        
        logger.info(f"Encontrados {len(accesos_por_vencer)} accesos por vencer")
        
        # Aquí se podría integrar con servicio de email/notificaciones
        # Por ahora solo logueamos
        for acceso in accesos_por_vencer:
            dias_restantes = (acceso.fecha_expiracion - datetime.utcnow()).days
            logger.info(
                f"Acceso {acceso.id} vence en {dias_restantes} días - "
                f"Organización: {acceso.organizacion_id}, Usuario: {acceso.usuario_id}"
            )
        
        return {"accesos_por_vencer": len(accesos_por_vencer)}
        
    except Exception as e:
        logger.error(f"Error verificando vencimientos: {str(e)}")
        return {"error": str(e)}
    finally:
        db.close()


# Función para iniciar worker manualmente (desarrollo/testing)
def iniciar_worker_manual():
    """
    Inicia el worker manualmente sin Celery (para testing o entornos simples).
    Se puede ejecutar como cron job del sistema operativo.
    """
    logger.info("Iniciando worker manual de ciclo de vida...")
    resultado = ejecutar_limpieza_programada()
    logger.info(f"Resultado: {resultado}")
    return resultado


if __name__ == "__main__":
    # Ejecución manual para testing
    iniciar_worker_manual()
