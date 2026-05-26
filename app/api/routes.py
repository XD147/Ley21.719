"""
API REST para Ley 21.719 - Protección de Datos (Chile)
Endpoints para gestión de usuarios, organizaciones y consentimientos
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.models import Usuario, Organizacion, TipoArco, EstadoArco, TipoAcceso
from app.schemas.schemas import (
    UsuarioCreate, UsuarioResponse, UsuarioUpdate,
    OrganizacionCreate, OrganizacionResponse,
    OrganizacionApiKeyCreate, OrganizacionApiKeyResponse, OrganizacionApiKeyWithSecret,
    AccesoOrganizacionCreate, AccesoOrganizacionResponse, AccesoOrganizacionRevoke,
    SolicitudConsentimientoCreate, SolicitudConsentimientoResponse,
    SolicitudConsentimientoApprove, SolicitudConsentimientoReject,
    SolicitudArcoCreate, SolicitudArcoResponse, SolicitudArcoProcess,
    LogAccesoDatosCreate, LogAccesoDatosResponse, LogAccesoDatosQuery,
    MessageResponse
)
from app.services.services import (
    UsuarioService, OrganizacionService, ApiKeyService,
    AccesoOrganizacionService, SolicitudConsentimientoService,
    SolicitudArcoService, LogAccesoDatosService
)
from app.utils.security import hash_rut_sha256, normalize_rut


router = APIRouter()


# ==================== DEPENDENCIAS ====================

def get_current_organization(request: Request, db: Session = Depends(get_db)) -> Organizacion:
    """
    Autentica la organización mediante API Key en el header
    Header esperado: X-API-Key
    """
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key requerida"
        )
    
    api_key_obj = ApiKeyService.authenticate(db, api_key)
    if not api_key_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key inválida o expirada"
        )
    
    organizacion = OrganizacionService.get_by_id(db, api_key_obj.organizacion_id)
    if not organizacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organización no encontrada"
        )
    
    return organizacion


# ==================== USUARIOS ====================

@router.post("/usuarios", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED, tags=["Usuarios"])
def create_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    """Registra un nuevo usuario ciudadano"""
    try:
        usuario_obj = UsuarioService.create(
            db=db,
            rut=usuario.rut,
            nombre_completo=usuario.nombre_completo,
            email=usuario.email,
            fecha_nacimiento=usuario.fecha_nacimiento,
            telefono=usuario.telefono,
            tutor_id=usuario.tutor_id
        )
        return usuario_obj
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/usuarios/{usuario_id}", response_model=UsuarioResponse, tags=["Usuarios"])
def get_usuario(usuario_id: str, db: Session = Depends(get_db)):
    """Obtiene información de un usuario por ID"""
    usuario = UsuarioService.get_by_id(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return usuario


@router.get("/usuarios/email/{email}", response_model=UsuarioResponse, tags=["Usuarios"])
def get_usuario_by_email(email: str, db: Session = Depends(get_db)):
    """Obtiene información de un usuario por email"""
    usuario = UsuarioService.get_by_email(db, email)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return usuario


@router.put("/usuarios/{usuario_id}", response_model=UsuarioResponse, tags=["Usuarios"])
def update_usuario(usuario_id: str, usuario: UsuarioUpdate, db: Session = Depends(get_db)):
    """Actualiza información de un usuario"""
    usuario_obj = UsuarioService.update(db, usuario_id, **usuario.model_dump(exclude_unset=True))
    if not usuario_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return usuario_obj


# ==================== ORGANIZACIONES ====================

@router.post("/organizaciones", response_model=OrganizacionResponse, status_code=status.HTTP_201_CREATED, tags=["Organizaciones"])
def create_organizacion(organizacion: OrganizacionCreate, db: Session = Depends(get_db)):
    """Registra una nueva organización"""
    try:
        org_obj = OrganizacionService.create(
            db=db,
            rut=organizacion.rut,
            razon_social=organizacion.razon_social,
            email_dpo=organizacion.email_dpo,
            webhook_url_revocacion=organizacion.webhook_url_revocacion,
            modelo_prevencion_certificado=organizacion.modelo_prevencion_certificado
        )
        return org_obj
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/organizaciones/{organizacion_id}", response_model=OrganizacionResponse, tags=["Organizaciones"])
def get_organizacion(organizacion_id: str, db: Session = Depends(get_db)):
    """Obtiene información de una organización"""
    org = OrganizacionService.get_by_id(db, organizacion_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organización no encontrada")
    return org


# ==================== API KEYS ====================

@router.post("/organizaciones/{organizacion_id}/api-keys", response_model=OrganizacionApiKeyWithSecret, 
             status_code=status.HTTP_201_CREATED, tags=["API Keys"])
def create_api_key(organizacion_id: str, api_key: OrganizacionApiKeyCreate, db: Session = Depends(get_db)):
    """Crea una nueva API Key para una organización"""
    try:
        key_obj, secret = ApiKeyService.create(
            db=db,
            organizacion_id=organizacion_id,
            nombre=api_key.nombre,
            fecha_expiracion=api_key.fecha_expiracion
        )
        
        response = OrganizacionApiKeyWithSecret(
            id=key_obj.id,
            organizacion_id=key_obj.organizacion_id,
            nombre=key_obj.nombre,
            prefix=key_obj.prefix,
            activa=key_obj.activa,
            fecha_expiracion=key_obj.fecha_expiracion,
            fecha_creacion=key_obj.fecha_creacion,
            ultimo_uso=key_obj.ultimo_uso,
            api_key_secret=secret
        )
        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/api-keys/{api_key_id}", response_model=MessageResponse, tags=["API Keys"])
def revoke_api_key(api_key_id: str, db: Session = Depends(get_db)):
    """Revoca una API Key"""
    success = ApiKeyService.revoke(db, api_key_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API Key no encontrada")
    return MessageResponse(message="API Key revocada exitosamente")


# ==================== ACCESOS/CONSENTIMIENTOS ====================

@router.post("/accesos", response_model=AccesoOrganizacionResponse, status_code=status.HTTP_201_CREATED, tags=["Accesos"])
def grant_access(acceso: AccesoOrganizacionCreate, db: Session = Depends(get_db),
                 current_org: Organizacion = Depends(get_current_organization)):
    """Otorga acceso de una organización a datos de un usuario"""
    try:
        # Verificar que la organización autenticada corresponde a la solicitante
        if str(current_org.id) != str(acceso.organizacion_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
        
        acceso_obj = AccesoOrganizacionService.grant_access(
            db=db,
            usuario_id=acceso.usuario_id,
            organizacion_id=acceso.organizacion_id,
            categoria_dato=acceso.categoria_dato,
            finalidad=acceso.finalidad,
            fecha_expiracion=acceso.fecha_expiracion
        )
        return acceso_obj
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/usuarios/{usuario_id}/accesos", response_model=List[AccesoOrganizacionResponse], tags=["Accesos"])
def get_user_accesses(usuario_id: str, db: Session = Depends(get_db)):
    """Obtiene todos los accesos activos de un usuario"""
    return AccesoOrganizacionService.get_active_accesses(db, usuario_id)


@router.post("/accesos/{acceso_id}/revoke", response_model=MessageResponse, tags=["Accesos"])
def revoke_access(acceso_id: str, request: AccesoOrganizacionRevoke, db: Session = Depends(get_db)):
    """Revoca un acceso otorgado"""
    success = AccesoOrganizacionService.revoke_access(db, acceso_id, request.motivo)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Acceso no encontrado")
    return MessageResponse(message="Acceso revocado exitosamente")


# ==================== SOLICITUDES DE CONSENTIMIENTO ====================

@router.post("/solicitudes-consentimiento", response_model=SolicitudConsentimientoResponse,
             status_code=status.HTTP_201_CREATED, tags=["Consentimiento"])
def create_solicitud_consentimiento(solicitud: SolicitudConsentimientoCreate,
                                     request: Request, db: Session = Depends(get_db),
                                     current_org: Organizacion = Depends(get_current_organization)):
    """Crea una nueva solicitud de consentimiento"""
    try:
        if str(current_org.id) != str(solicitud.organizacion_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
        
        ip_solicitud = request.client.host if request.client else None
        
        solicitud_obj = SolicitudConsentimientoService.create_solicitud(
            db=db,
            organizacion_id=solicitud.organizacion_id,
            rut_ciudadano=solicitud.rut_ciudadano,
            proposal_json=solicitud.proposal_json,
            texto_legal_presentado=solicitud.texto_legal_presentado,
            request_type=solicitud.request_type,
            source_organization_id=solicitud.source_organization_id,
            ip_solicitud=ip_solicitud
        )
        return solicitud_obj
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/solicitudes-consentimiento/{solicitud_id}/approve", 
             response_model=AccesoOrganizacionResponse, tags=["Consentimiento"])
def approve_solicitud(solicitud_id: str, approval: SolicitudConsentimientoApprove,
                      request: Request, db: Session = Depends(get_db),
                      current_org: Organizacion = Depends(get_current_organization)):
    """Aprueba una solicitud de consentimiento"""
    # Nota: En producción, esto debería ser aprobado por el usuario, no por la org
    try:
        # Obtener usuario asociado (en producción usar autenticación del usuario)
        # Esto es simplificado para el ejemplo
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, 
                          detail="Aprobación debe ser realizada por el usuario")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/solicitudes-consentimiento/{solicitud_id}/reject", 
             response_model=MessageResponse, tags=["Consentimiento"])
def reject_solicitud(solicitud_id: str, rejection: SolicitudConsentimientoReject,
                     db: Session = Depends(get_db)):
    """Rechaza una solicitud de consentimiento"""
    success = SolicitudConsentimientoService.reject(db, solicitud_id, rejection.motivo)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada")
    return MessageResponse(message="Solicitud rechazada")


# ==================== SOLICITUDES ARCO ====================

@router.post("/solicitudes-arco", response_model=SolicitudArcoResponse,
             status_code=status.HTTP_201_CREATED, tags=["ARCO"])
def create_solicitud_arco(solicitud: SolicitudArcoCreate, request: Request,
                          db: Session = Depends(get_db),
                          current_org: Organizacion = Depends(get_current_organization)):
    """Crea una nueva solicitud ARCO (Acceso, Rectificación, Cancelación, Oposición)"""
    try:
        if str(current_org.id) != str(solicitud.organizacion_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
        
        solicitud_obj = SolicitudArcoService.create_solicitud(
            db=db,
            organizacion_id=solicitud.organizacion_id,
            rut_ciudadano=solicitud.rut_ciudadano,
            tipo=solicitud.tipo,
            token_evidencia_identidad=solicitud.token_evidencia_identidad,
            descripcion=solicitud.descripcion
        )
        return solicitud_obj
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/solicitudes-arco/{solicitud_id}/process", 
             response_model=MessageResponse, tags=["ARCO"])
def process_solicitud_arco(solicitud_id: str, process: SolicitudArcoProcess,
                           db: Session = Depends(get_db)):
    """Procesa una solicitud ARCO"""
    success = SolicitudArcoService.process(
        db=db,
        solicitud_id=solicitud_id,
        estado=process.estado,
        respuesta=process.respuesta,
        prorrogar=process.prorrogar
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada")
    return MessageResponse(message="Solicitud ARCO procesada exitosamente")


# ==================== LOGS DE AUDITORÍA ====================

@router.post("/logs-acceso", response_model=LogAccesoDatosResponse,
             status_code=status.HTTP_201_CREATED, tags=["Auditoría"])
def log_acceso(log: LogAccesoDatosCreate, request: Request,
               db: Session = Depends(get_db),
               current_org: Organizacion = Depends(get_current_organization)):
    """Registra un acceso a datos para auditoría"""
    try:
        if str(current_org.id) != str(log.organizacion_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
        
        user_agent = request.headers.get("User-Agent")
        
        log_obj = LogAccesoDatosService.log_access(
            db=db,
            usuario_id=log.usuario_id,
            organizacion_id=log.organizacion_id,
            tipo_acceso=log.tipo_acceso,
            categoria_dato=log.categoria_dato_consultado,
            justificacion_legal=log.justificacion_legal,
            ip_origen=log.ip_origen or (request.client.host if request.client else "unknown"),
            user_agent=user_agent,
            detalles_adicionales=log.detalles_adicionales
        )
        return log_obj
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/logs-acceso", response_model=List[LogAccesoDatosResponse], tags=["Auditoría"])
def get_logs(query: LogAccesoDatosQuery = Depends(), db: Session = Depends(get_db)):
    """Obtiene logs de acceso con filtros"""
    return LogAccesoDatosService.get_logs(
        db=db,
        usuario_id=query.usuario_id,
        organizacion_id=query.organizacion_id,
        fecha_desde=query.fecha_desde,
        fecha_hasta=query.fecha_hasta,
        limit=query.limit,
        offset=query.offset
    )


@router.get("/organizaciones/{organizacion_id}/audit-report", tags=["Auditoría"])
def get_audit_report(organizacion_id: str, fecha_desde: datetime, fecha_hasta: datetime,
                     db: Session = Depends(get_db)):
    """Genera reporte de auditoría para una organización"""
    return LogAccesoDatosService.get_audit_report(
        db=db,
        organizacion_id=organizacion_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )
