"""
Middleware de validación de edad y consentimiento parental
Ley 21.719 - Protección de menores de 16 años (Art. 6)

Decorador @require_parental_consent para interceptar solicitudes de usuarios menores
"""

from functools import wraps
from fastapi import Request, HTTPException, Depends
from datetime import datetime, timedelta
from typing import Optional, Callable
import logging

logger = logging.getLogger(__name__)


class AgeValidationError(Exception):
    """Excepción personalizada para errores de validación de edad"""
    pass


def require_parental_consent(f: Callable) -> Callable:
    """
    Decorador que valida si el usuario tiene edad suficiente (>16 años)
    o si cuenta con consentimiento parental validado para menores de 14-16 años.
    
    Para menores de 14 años, no se permite el tratamiento de datos bajo ninguna circunstancia
    excepto casos excepcionales definidos por ley (ej. interés superior del niño).
    
    Uso:
        @app.post("/api/v1/datos/sensibles")
        @require_parental_consent
        async def crear_dato_sensible(request: Request, data: DatosSchema):
            ...
    """
    
    @wraps(f)
    async def wrapper(*args, request: Request, **kwargs):
        from app.core.database import SessionLocal
        from app.models.usuario import Usuario
        from app.models.cumplimiento_models import ValidacionTutorLegal
        from sqlalchemy import and_
        
        db = SessionLocal()
        
        try:
            # Obtener usuario autenticado del contexto
            usuario_id = getattr(request.state, 'usuario_id', None)
            
            if not usuario_id:
                raise HTTPException(
                    status_code=401,
                    detail="Usuario no autenticado"
                )
            
            # Buscar usuario en base de datos
            usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
            
            if not usuario:
                raise HTTPException(
                    status_code=404,
                    detail="Usuario no encontrado"
                )
            
            # Calcular edad del usuario
            edad = calcular_edad(usuario.fecha_nacimiento)
            
            logger.info(f"Validando edad - Usuario {usuario.id}: {edad} años")
            
            # Caso 1: Usuario mayor de 16 años - puede consentir por sí mismo
            if edad >= 16:
                logger.info(f"Usuario {usuario.id} es mayor de 16 años. Acceso permitido.")
                return await f(*args, request=request, **kwargs)
            
            # Caso 2: Usuario entre 14-16 años - requiere consentimiento parental
            elif 14 <= edad < 16:
                logger.info(f"Usuario {usuario.id} tiene {edad} años. Verificando consentimiento parental...")
                
                # Buscar validación de tutor legal activa y vigente
                validacion_tutor = db.query(ValidacionTutorLegal).filter(
                    and_(
                        ValidacionTutorLegal.usuario_id == usuario_id,
                        ValidacionTutorLegal.estado == 'APROBADO',
                        ValidacionTutorLegal.fecha_vigencia > datetime.utcnow()
                    )
                ).first()
                
                if validacion_tutor:
                    logger.info(f"Consentimiento parental válido encontrado para usuario {usuario.id}")
                    
                    # Agregar información del tutor al contexto de la request
                    request.state.tutor_legal = validacion_tutor
                    request.state.consentimiento_parental = True
                    
                    return await f(*args, request=request, **kwargs)
                else:
                    logger.warning(f"Usuario {usuario.id} ({edad} años) no tiene consentimiento parental válido")
                    
                    raise HTTPException(
                        status_code=403,
                        detail={
                            "codigo": "CONSENTIMIENTO_PARENTAL_REQUERIDO",
                            "mensaje": f"Los usuarios entre 14 y 16 años requieren consentimiento parental validado.",
                            "edad_usuario": edad,
                            "accion_requerida": "Completar flujo de validación de tutor legal",
                            "endpoint_validacion": "/api/v1/usuarios/validar-tutor"
                        }
                    )
            
            # Caso 3: Usuario menor de 14 años - prohibido tratamiento (con excepciones muy limitadas)
            else:  # edad < 14
                logger.warning(f"Usuario {usuario.id} es menor de 14 años ({edad} años). Tratamiento prohibido.")
                
                # Verificar si existe excepción legal (ej. interés superior del niño)
                excepcion_legal = db.query(ValidacionTutorLegal).filter(
                    and_(
                        ValidacionTutorLegal.usuario_id == usuario_id,
                        ValidacionTutorLegal.estado == 'APROBADO_EXCEPCION_LEGAL',
                        ValidacionTutorLegal.fecha_vigencia > datetime.utcnow()
                    )
                ).first()
                
                if excepcion_legal:
                    logger.info(f"Excepción legal aprobada para usuario {usuario.id}")
                    request.state.tutor_legal = excepcion_legal
                    request.state.excepcion_legal = True
                    return await f(*args, request=request, **kwargs)
                else:
                    raise HTTPException(
                        status_code=403,
                        detail={
                            "codigo": "EDAD_MINIMA_NO_CUMPLIDA",
                            "mensaje": "El tratamiento de datos de menores de 14 años está prohibido, "
                                      "excepto en casos excepcionales definidos por ley.",
                            "edad_usuario": edad,
                            "edad_minima": 14,
                            "fundamento_legal": "Ley 21.719 Art. 6 - Protección especial de menores"
                        }
                    )
        
        except AgeValidationError as e:
            logger.error(f"Error de validación de edad: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=str(e)
            )
        
        except HTTPException:
            raise
        
        except Exception as e:
            logger.error(f"Error inesperado en validación de edad: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Error interno en validación de edad"
            )
        
        finally:
            db.close()
    
    return wrapper


def calcular_edad(fecha_nacimiento: datetime) -> int:
    """
    Calcula la edad en años a partir de la fecha de nacimiento
    
    Args:
        fecha_nacimiento: Fecha de nacimiento del usuario
    
    Returns:
        Edad en años cumplidos
    """
    today = datetime.today()
    edad = today.year - fecha_nacimiento.year
    
    # Ajustar si aún no ha cumplido años este año
    if (today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
        edad -= 1
    
    return edad


def validar_fecha_nacimiento(fecha_nacimiento: datetime) -> bool:
    """
    Valida que la fecha de nacimiento sea razonable (no futura, no mayor a 120 años)
    
    Args:
        fecha_nacimiento: Fecha a validar
    
    Returns:
        True si es válida, False si no
    """
    today = datetime.today()
    
    # No puede ser fecha futura
    if fecha_nacimiento > today:
        return False
    
    # No puede ser mayor a 120 años
    fecha_limite = today.replace(year=today.year - 120)
    if fecha_nacimiento < fecha_limite:
        return False
    
    return True


async def verificar_tutor_activo(usuario_id: str, db=None) -> Optional[dict]:
    """
    Verifica si un usuario menor tiene un tutor legal activo
    
    Args:
        usuario_id: ID del usuario
        db: Sesión de base de datos
    
    Returns:
        Dict con información del tutor si existe, None si no
    """
    from app.core.database import SessionLocal
    from app.models.cumplimiento_models import ValidacionTutorLegal
    
    if db is None:
        db = SessionLocal()
    
    try:
        validacion = db.query(ValidacionTutorLegal).filter(
            ValidacionTutorLegal.usuario_id == usuario_id,
            ValidacionTutorLegal.estado.in_(['APROBADO', 'APROBADO_EXCEPCION_LEGAL']),
            ValidacionTutorLegal.fecha_vigencia > datetime.utcnow()
        ).first()
        
        if validacion:
            return {
                'tutor_id': validacion.tutor_id,
                'nombre_tutor': validacion.nombre_tutor,
                'rut_tutor': validacion.rut_tutor,
                'parentesco': validacion.parentesco,
                'fecha_aprobacion': validacion.fecha_aprobacion,
                'fecha_vigencia': validacion.fecha_vigencia,
                'estado': validacion.estado,
                'documento_verificado': validacion.documento_verificado
            }
        
        return None
    
    finally:
        if db is not None:
            db.close()


# Middleware opcional para aplicar automáticamente a rutas específicas
class ParentalConsentMiddleware:
    """
    Middleware de FastAPI que valida consentimiento parental para rutas configuradas
    """
    
    def __init__(self, app, excluded_paths: list = None):
        self.app = app
        self.excluded_paths = excluded_paths or [
            '/api/v1/usuarios/validar-tutor',
            '/api/v1/usuarios/registro',
            '/docs',
            '/openapi.json'
        ]
    
    async def __call__(self, scope, receive, send):
        from starlette.middleware.base import BaseHTTPMiddleware
        from starlette.responses import JSONResponse
        
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        
        path = scope['path']
        
        # Excluir paths que no requieren validación
        if any(path.startswith(excluded) for excluded in self.excluded_paths):
            return await self.app(scope, receive, send)
        
        # Para otras rutas, la validación se hace mediante el decorador
        return await self.app(scope, receive, send)
