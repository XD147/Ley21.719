"""
Endpoints de autenticación con ClaveÚnica y SII
Ley 21.719 - Protección de Datos (Chile)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import secrets
from jose import JWTError

from app.database import get_db
from app.models.models import Usuario, Organizacion
from app.schemas.schemas import UsuarioResponse, OrganizacionResponse, MessageResponse
from app.services.services import UsuarioService, OrganizacionService
from app.services.auth_services import (
    claveunica_service, sii_service, auth_token_service,
    ClaveUnicaService, SiiClaveTributariaService
)
from app.utils.security import hash_rut_sha256, normalize_rut, encrypt_rut_aes256


router = APIRouter(prefix="/auth", tags=["Autenticación"])


# ==================== CLAVEÚNICA (USUARIOS) ====================

@router.get("/claveunica/login", tags=["ClaveÚnica"])
def login_claveunica(request: Request):
    """
    Inicia flujo de autenticación con ClaveÚnica
    
    Redirige al usuario al portal de ClaveÚnica del Gobierno de Chile
    """
    state = secrets.token_urlsafe(32)
    
    # Guardar state en sesión para validar callback (en producción usar Redis/session)
    request.session["claveunica_state"] = state
    
    auth_url = claveunica_service.generate_auth_url(state)
    
    return {
        "authorization_url": auth_url,
        "state": state,
        "message": "Redirigir usuario a authorization_url"
    }


@router.get("/claveunica/callback", response_model=UsuarioResponse, tags=["ClaveÚnica"])
async def callback_claveunica(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Callback de ClaveÚnica después de autenticación exitosa
    
    Procesa el código de autorización y crea/actualiza usuario
    """
    # Validar state para prevenir CSRF
    stored_state = request.session.get("claveunica_state")
    if not stored_state or stored_state != state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Estado inválido - posible ataque CSRF"
        )
    
    try:
        # Intercambiar código por token
        token_response = await claveunica_service.exchange_code_for_token(code)
        access_token = token_response.get("access_token")
        id_token = token_response.get("id_token")
        
        # Obtener información del usuario
        user_info = await claveunica_service.get_user_info(access_token)
        
        # Extraer datos del usuario
        rut = user_info.get("rut")
        nombre_completo = user_info.get("nombre", "")
        email = user_info.get("email", "")
        
        if not rut:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ClaveÚnica no retornó el RUT"
            )
        
        # Normalizar RUT
        rut_normalized = normalize_rut(rut)
        rut_hash = hash_rut_sha256(rut_normalized)
        
        # Buscar o crear usuario
        usuario = db.query(Usuario).filter(Usuario.rut_hash == rut_hash).first()
        
        if not usuario:
            # Crear nuevo usuario
            from datetime import date
            
            # Fecha de nacimiento desde ClaveÚnica (si está disponible)
            fecha_nacimiento = user_info.get("fecha_nacimiento", date(1990, 1, 1))
            if isinstance(fecha_nacimiento, str):
                fecha_nacimiento = datetime.fromisoformat(fecha_nacimiento).date()
            
            usuario = UsuarioService.create(
                db=db,
                rut=rut_normalized,
                nombre_completo=nombre_completo,
                email=email or f"{rut_hash}@claveunica.temp",
                fecha_nacimiento=fecha_nacimiento
            )
        else:
            # Actualizar información si cambió
            if usuario.nombre_completo != nombre_completo:
                usuario.nombre_completo = nombre_completo
            if email and usuario.email != email:
                usuario.email = email
            db.commit()
            db.refresh(usuario)
        
        # Generar tokens de sesión
        tokens = auth_token_service.create_session_tokens(
            user_id=str(usuario.id),
            rut_hash=rut_hash,
            auth_provider="claveunica"
        )
        
        # Guardar hash del token como evidencia de autenticación
        token_evidence = ClaveUnicaService.hash_claveunica_token(access_token)
        
        # Limpiar session state
        del request.session["claveunica_state"]
        
        # En producción, retornar solo usuario y enviar tokens por headers/cookies
        return {
            **UsuarioResponse.model_validate(usuario).model_dump(),
            "tokens": tokens,
            "token_evidence": token_evidence
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error en autenticación ClaveÚnica: {str(e)}"
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Token inválido: {str(e)}"
        )


# ==================== SII CLAVE TRIBUTARIA (ORGANIZACIONES) ====================

@router.get("/sii/login", tags=["SII"])
def login_sii(
    request: Request,
    rut_organizacion: str = Query(..., description="RUT de la organización")
):
    """
    Inicia flujo de autenticación con Clave Tributaria del SII
    
    Redirige al representante legal al portal del SII
    """
    state = secrets.token_urlsafe(32)
    
    # Guardar state y RUT para validar callback
    request.session["sii_state"] = state
    request.session["sii_rut"] = rut_organizacion
    
    auth_url = sii_service.generate_auth_url(state, rut_organizacion)
    
    return {
        "authorization_url": auth_url,
        "state": state,
        "rut_organizacion": rut_organizacion,
        "message": "Redirigir representante legal a authorization_url"
    }


@router.get("/sii/callback", response_model=OrganizacionResponse, tags=["SII"])
async def callback_sii(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Callback del SII después de autenticación exitosa
    
    Valida la organización con datos oficiales del SII
    """
    # Validar state para prevenir CSRF
    stored_state = request.session.get("sii_state")
    stored_rut = request.session.get("sii_rut")
    
    if not stored_state or stored_state != state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Estado inválido - posible ataque CSRF"
        )
    
    try:
        # Intercambiar código por token
        token_response = await sii_service.exchange_code_for_token(code, stored_rut)
        access_token = token_response.get("access_token")
        
        # Obtener información oficial de la organización desde SII
        org_info = await sii_service.get_organization_info(access_token, stored_rut)
        
        # Extraer datos de la organización
        rut = org_info.get("rut")
        razon_social = org_info.get("razon_social")
        giro = org_info.get("giro", "")
        
        # Validar DTE autorizado (opcional pero recomendado)
        dte_authorized = await sii_service.validate_dte_authorization(access_token, rut)
        
        # Buscar o crear organización
        organizacion = db.query(Organizacion).filter(Organizacion.rut == rut).first()
        
        if not organizacion:
            # Crear nueva organización con datos oficiales del SII
            organizacion = OrganizacionService.create(
                db=db,
                rut=rut,
                razon_social=razon_social,
                email_dpo="",  # Debe ser completado posteriormente
                modelo_prevencion_certificado=dte_authorized  # Usar DTE como indicador
            )
        else:
            # Actualizar información con datos oficiales del SII
            if organizacion.razon_social != razon_social:
                organizacion.razon_social = razon_social
            organizacion.modelo_prevencion_certificado = dte_authorized
            db.commit()
            db.refresh(organizacion)
        
        # Generar tokens para la organización
        tokens = auth_token_service.create_session_tokens(
            user_id=str(organizacion.id),
            rut_hash=hash_rut_sha256(rut),
            auth_provider="sii"
        )
        
        # Hash del token como evidencia
        token_evidence = SiiClaveTributariaService.hash_sii_token(access_token)
        
        # Limpiar session state
        del request.session["sii_state"]
        del request.session["sii_rut"]
        
        return {
            **OrganizacionResponse.model_validate(organizacion).model_dump(),
            "tokens": tokens,
            "token_evidence": token_evidence,
            "dte_authorized": dte_authorized,
            "giro": giro
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error en autenticación SII: {str(e)}"
        )


# ==================== GESTIÓN DE SESIÓN ====================

@router.post("/refresh", tags=["Autenticación"])
def refresh_token(
    request: dict,
    db: Session = Depends(get_db)
):
    """
    Refresca tokens de acceso usando refresh token
    
    Body esperado: {"refresh_token": "..."}
    """
    refresh_token = request.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token requerido"
        )
    
    try:
        payload = auth_token_service.verify_token(refresh_token)
        
        # Verificar que es un refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token inválido"
            )
        
        user_id = payload.get("sub")
        auth_provider = payload.get("auth_provider")
        
        # Generar nuevos tokens
        new_tokens = auth_token_service.create_session_tokens(
            user_id=user_id,
            rut_hash=payload.get("rut_hash", ""),
            auth_provider=auth_provider
        )
        
        return new_tokens
        
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token expirado o inválido: {str(e)}"
        )


@router.get("/verify", tags=["Autenticación"])
def verify_token(
    request: Request,
    token: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    Verifica un token de acceso y retorna información del usuario/organización
    """
    if not token:
        # Intentar obtener del header Authorization
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token requerido"
        )
    
    try:
        payload = auth_token_service.verify_token(token)
        
        # Verificar que es un access token
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token inválido"
            )
        
        user_id = payload.get("sub")
        auth_provider = payload.get("auth_provider")
        
        # Obtener información según proveedor
        if auth_provider == "claveunica":
            usuario = db.query(Usuario).filter(Usuario.id == user_id).first()
            if not usuario:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuario no encontrado"
                )
            return {
                "valid": True,
                "type": "usuario",
                "data": UsuarioResponse.model_validate(usuario).model_dump()
            }
        elif auth_provider == "sii":
            organizacion = db.query(Organizacion).filter(Organizacion.id == user_id).first()
            if not organizacion:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Organización no encontrada"
                )
            return {
                "valid": True,
                "type": "organizacion",
                "data": OrganizacionResponse.model_validate(organizacion).model_dump()
            }
        else:
            return {
                "valid": True,
                "payload": payload
            }
        
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido: {str(e)}"
        )


# ==================== LOGOUT ====================

@router.post("/logout", response_model=MessageResponse, tags=["Autenticación"])
def logout(request: Request):
    """
    Cierra sesión invalidando tokens en el cliente
    
    Nota: JWT tokens son stateless, el cliente debe eliminarlos
    """
    # Limpiar sesión del servidor
    request.session.clear()
    
    return MessageResponse(
        message="Sesión cerrada exitosamente",
        detail="Elimine los tokens del lado del cliente"
    )
