"""
Configuración centralizada de Celery para tareas asíncronas
Ley 21.719 - Protección de Datos Chile
"""

from celery import Celery, Task
from celery.schedules import crontab
from datetime import timedelta
import os

# Configuración de Celery
celery_app = Celery(
    'ley21719',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    include=[
        'app.workers.lifecycle_worker',
        'app.workers.brechas_worker',
        'app.workers.reportes_worker',
    ]
)

# Configuración por defecto
celery_app.conf.update(
    # Serialización
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Timezone
    timezone='America/Santiago',
    enable_utc=True,
    
    # Reintentos
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_retry_delay=60,
    task_max_retries=3,
    
    # Concurrencia
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Logging
    worker_hijack_root_logger=False,
    worker_log_level='INFO',
)


# Tareas programadas (Celery Beat)
celery_app.conf.beat_schedule = {
    # Ejecutar eliminación automática diariamente a las 02:00 AM
    'ejecutar-eliminacion-automatica': {
        'task': 'app.workers.lifecycle_worker.ejecutar_eliminacion_automatica',
        'schedule': crontab(hour=2, minute=0),
        'args': (),
    },
    
    # Verificar consentimientos expirados cada hora
    'verificar-consentimientos-expirados': {
        'task': 'app.workers.lifecycle_worker.verificar_consentimientos_expirados',
        'schedule': crontab(minute=0),  # Cada hora en punto
        'args': (),
    },
    
    # Enviar reporte diario de brechas pendientes a las 08:00 AM
    'reporte-diario-brechas': {
        'task': 'app.workers.brechas_worker.enviar_reporte_diario',
        'schedule': crontab(hour=8, minute=0),
        'args': (),
    },
    
    # Generar reporte mensual de cumplimiento el día 1 a las 09:00 AM
    'reporte-mensual-cumplimiento': {
        'task': 'app.workers.reportes_worker.generar_reporte_mensual',
        'schedule': crontab(day_of_month=1, hour=9, minute=0),
        'args': (),
    },
    
    # Limpiar logs antiguos semanalmente (domingo 03:00 AM)
    'limpiar-logs-antiguos': {
        'task': 'app.workers.lifecycle_worker.limpiar_logs_antiguos',
        'schedule': crontab(day_of_week=0, hour=3, minute=0),
        'args': (90,),  # Logs mayores a 90 días
    },
}


# Contexto de aplicación para tareas
class ContextTask(Task):
    def run(self, *args, **kwargs):
        from app.main import get_db
        from app.core.database import SessionLocal
        
        db = SessionLocal()
        try:
            return super().run(*args, db=db, **kwargs)
        finally:
            db.close()


celery_app.Task = ContextTask


# Handlers de señales para logging
@celery_app.signal('task_prerun')
def task_prerun_handler(task_id, task, *args, **kwargs):
    """Log antes de ejecutar tarea"""
    import logging
    logger = logging.getLogger('celery.tasks')
    logger.info(f"Iniciando tarea: {task.name} [ID: {task_id}]")


@celery_app.signal('task_postrun')
def task_postrun_handler(task_id, task, *args, **kwargs):
    """Log después de ejecutar tarea"""
    import logging
    logger = logging.getLogger('celery.tasks')
    logger.info(f"Tarea completada: {task.name} [ID: {task_id}]")


@celery_app.signal('task_failure')
def task_failure_handler(sender=None, exception=None, *args, **kwargs):
    """Log cuando falla una tarea"""
    import logging
    logger = logging.getLogger('celery.tasks')
    logger.error(f"Tarea fallida: {sender.name} [ID: {sender.request.id}] - Error: {str(exception)}")
    
    # Notificar al DPO si es tarea crítica
    if sender.name in [
        'app.workers.lifecycle_worker.ejecutar_eliminacion_automatica',
        'app.workers.brechas_worker.notificar_agencia',
    ]:
        from app.services.email_service import EmailService
        email_service = EmailService()
        email_service.enviar_alerta_critica(
            asunto=f"Fallo crítico en tarea: {sender.name}",
            mensaje=f"La tarea {sender.name} falló con error: {str(exception)}",
            destinatarios=['dpo@organizacion.cl']
        )


if __name__ == '__main__':
    # Para pruebas locales
    celery_app.start()
