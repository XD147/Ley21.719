"""
Servicios de negocio para Ley 21.719
Implementa lógica de negocio para usuarios, organizaciones y gestión de consentimientos
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
import uuid
import secrets

from app.models.models import (
    Usuario, Organizacion, OrganizacionApiKey, AccesoOrganizacion,
    SolicitudConsentimiento, SolicitudArco, LogAccesoDatos,
    EstadoPermiso, EstadoSolicitud, TipoArco, EstadoArco, TipoAcceso, AiFlag
)
from app.utils.security import (
    hash_rut_sha256, encrypt_rut_aes256, decrypt_rut_aes256,
    hash_api_key, generate_receipt_hash, normalize_rut, validate_rut
)
from app.utils.validators import validate_user_data, calculate_age


class UsuarioService:
    """Servicio para gestión de Usuarios"""
    
    @staticmethod
    def create(db: Session, rut: str, nombre_completo: str, email: str, 
               fecha_nacimiento: datetime, telefono: str = None, tutor_id: uuid.UUID = None) -> Usuario:
        """Crea un nuevo usuario con RUT encriptado y hasheado"""
        
        # Validar RUT
        if not validate_rut(rut):
            raise ValueError("RUT inválido")
        
        rut_normalized = normalize_rut(rut)
        rut_hash = hash_rut_sha256(rut_normalized)
        rut_encriptado = encrypt_rut_aes256(rut_normalized)
        
        # Validar edad y tutor
        validation = validate_user_data(rut_normalized, fecha_nacimiento, email)
        if not validation["valid"]:
            raise ValueError(f"Errores de validación: {validation['errors']}")
        
        if validation["requires_tutor"] and not tutor_id:
            raise ValueError("Menor de 16 años requiere tutor")
        
        # Verificar unicidad
        existing = db.query(Usuario).filter(
            or_(Usuario.rut_hash == rut_hash, Usuario.email == email)
        ).first()
        if existing:
            raise ValueError("Usuario ya registrado con este RUT o email")
        
        usuario = Usuario(
            rut_hash=rut_hash,
            rut_encriptado=rut_encriptado,
            nombre_completo=nombre_completo,
            email=email,
            telefono=telefono,
            fecha_nacimiento=fecha_nacimiento,
            tutor_id=tutor_id
        )
        
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
        return usuario
    
    @staticmethod
    def get_by_id(db: Session, usuario_id: uuid.UUID) -> Optional[Usuario]:
        return db.query(Usuario).filter(Usuario.id == usuario_id).first()
    
    @staticmethod
    def get_by_rut_hash(db: Session, rut_hash: str) -> Optional[Usuario]:
        return db.query(Usuario).filter(Usuario.rut_hash == rut_hash).first()
    
    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[Usuario]:
        return db.query(Usuario).filter(Usuario.email == email).first()
    
    @staticmethod
    def get_rut_decrypted(db: Session, usuario_id: uuid.UUID) -> Optional[str]:
        """Obtiene el RUT desencriptado (solo para operaciones autorizadas)"""
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        if usuario:
            return decrypt_rut_aes256(usuario.rut_encriptado)
        return None
    
    @staticmethod
    def update(db: Session, usuario_id: uuid.UUID, **kwargs) -> Optional[Usuario]:
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        if not usuario:
            return None
        
        for key, value in kwargs.items():
            if hasattr(usuario, key) and key not in ['id', 'rut_hash', 'rut_encriptado', 'fecha_registro']:
                setattr(usuario, value)
        
        db.commit()
        db.refresh(usuario)
        return usuario


class OrganizacionService:
    """Servicio para gestión de Organizaciones"""
    
    @staticmethod
    def create(db: Session, rut: str, razon_social: str, email_dpo: str,
               webhook_url_revocacion: str = None, modelo_prevencion_certificado: bool = False) -> Organizacion:
        """Crea una nueva organización"""
        
        # Verificar unicidad
        existing = db.query(Organizacion).filter(Organizacion.rut == rut).first()
        if existing:
            raise ValueError("Organización ya registrada con este RUT")
        
        organizacion = Organizacion(
            rut=rut,
            razon_social=razon_social,
            email_dpo=email_dpo,
            webhook_url_revocacion=webhook_url_revocacion,
            modelo_prevencion_certificado=modelo_prevencion_certificado
        )
        
        db.add(organizacion)
        db.commit()
        db.refresh(organizacion)
        return organizacion
    
    @staticmethod
    def get_by_id(db: Session, organizacion_id: uuid.UUID) -> Optional[Organizacion]:
        return db.query(Organizacion).filter(Organizacion.id == organizacion_id).first()
    
    @staticmethod
    def get_by_rut(db: Session, rut: str) -> Optional[Organizacion]:
        return db.query(Organizacion).filter(Organizacion.rut == rut).first()


class ApiKeyService:
    """Servicio para gestión de API Keys"""
    
    @staticmethod
    def create(db: Session, organizacion_id: uuid.UUID, nombre: str,
               fecha_expiracion: datetime = None) -> Tuple[OrganizacionApiKey, str]:
        """
        Crea una nueva API Key para una organización
        Retorna la API Key completa (solo se muestra una vez)
        """
        
        organizacion = db.query(Organizacion).filter(Organizacion.id == organizacion_id).first()
        if not organizacion:
            raise ValueError("Organización no encontrada")
        
        # Generar API Key única
        unique_id = secrets.token_urlsafe(32)
        api_key_secret = f"cl_ly_{unique_id}"
        api_key_hash = hash_api_key(api_key_secret)
        
        # Determinar prefijo
        prefix = "cl_ly_prod_" if not fecha_expiracion else "cl_ly_temp_"
        
        api_key = OrganizacionApiKey(
            organizacion_id=organizacion_id,
            nombre=nombre,
            prefix=prefix,
            key_hash=api_key_hash,
            activa=True,
            fecha_expiracion=fecha_expiracion
        )
        
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        
        return api_key, api_key_secret
    
    @staticmethod
    def authenticate(db: Session, api_key: str) -> Optional[OrganizacionApiKey]:
        """Autentica una API Key y retorna el registro si es válida"""
        key_hash = hash_api_key(api_key)
        
        api_key_obj = db.query(OrganizacionApiKey).filter(
            and_(
                OrganizacionApiKey.key_hash == key_hash,
                OrganizacionApiKey.activa == True
            )
        ).first()
        
        if not api_key_obj:
            return None
        
        # Verificar expiración
        if api_key_obj.fecha_expiracion and api_key_obj.fecha_expiracion < datetime.utcnow():
            return None
        
        # Actualizar último uso
        api_key_obj.ultimo_uso = datetime.utcnow()
        db.commit()
        
        return api_key_obj
    
    @staticmethod
    def revoke(db: Session, api_key_id: uuid.UUID) -> bool:
        """Revoca una API Key"""
        api_key = db.query(OrganizacionApiKey).filter(OrganizacionApiKey.id == api_key_id).first()
        if not api_key:
            return False
        
        api_key.activa = False
        db.commit()
        return True


class AccesoOrganizacionService:
    """Servicio para gestión de Accesos/Consentimientos"""
    
    @staticmethod
    def grant_access(db: Session, usuario_id: uuid.UUID, organizacion_id: uuid.UUID,
                     categoria_dato: str, finalidad: str, fecha_expiracion: datetime = None,
                     signature_data: dict = None) -> AccesoOrganizacion:
        """Otorga acceso de una organización a datos de un usuario"""
        
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        if not usuario:
            raise ValueError("Usuario no encontrado")
        
        organizacion = db.query(Organizacion).filter(Organizacion.id == organizacion_id).first()
        if not organizacion:
            raise ValueError("Organización no encontrada")
        
        # Generar receipt hash
        signature = signature_data.get('signature', 'digital_signature') if signature_data else 'digital_signature'
        receipt_hash = generate_receipt_hash({
            'usuario_id': str(usuario_id),
            'organizacion_id': str(organizacion_id),
            'categoria_dato': categoria_dato,
            'finalidad': finalidad
        }, signature)
        
        # Verificar acceso existente
        existing = db.query(AccesoOrganizacion).filter(
            and_(
                AccesoOrganizacion.usuario_id == usuario_id,
                AccesoOrganizacion.organizacion_id == organizacion_id,
                AccesoOrganizacion.categoria_dato == categoria_dato,
                AccesoOrganizacion.estado == EstadoPermiso.ACTIVO
            )
        ).first()
        
        if existing:
            raise ValueError("Ya existe un acceso activo para esta categoría de dato")
        
        acceso = AccesoOrganizacion(
            usuario_id=usuario_id,
            organizacion_id=organizacion_id,
            categoria_dato=categoria_dato,
            finalidad=finalidad,
            estado=EstadoPermiso.ACTIVO,
            receipt_hash=receipt_hash,
            fecha_expiracion=fecha_expiracion
        )
        
        db.add(acceso)
        db.commit()
        db.refresh(acceso)
        return acceso
    
    @staticmethod
    def revoke_access(db: Session, acceso_id: uuid.UUID, motivo: str = None) -> bool:
        """Revoca un acceso otorgado"""
        acceso = db.query(AccesoOrganizacion).filter(AccesoOrganizacion.id == acceso_id).first()
        if not acceso:
            return False
        
        acceso.estado = EstadoPermiso.REVOCADO
        acceso.fecha_revocacion = datetime.utcnow()
        db.commit()
        return True
    
    @staticmethod
    def get_active_accesses(db: Session, usuario_id: uuid.UUID) -> List[AccesoOrganizacion]:
        """Obtiene todos los accesos activos de un usuario"""
        return db.query(AccesoOrganizacion).filter(
            and_(
                AccesoOrganizacion.usuario_id == usuario_id,
                AccesoOrganizacion.estado == EstadoPermiso.ACTIVO
            )
        ).all()
    
    @staticmethod
    def check_access(db: Session, usuario_id: uuid.UUID, organizacion_id: uuid.UUID,
                     categoria_dato: str) -> bool:
        """Verifica si una organización tiene acceso a una categoría de dato específica"""
        acceso = db.query(AccesoOrganizacion).filter(
            and_(
                AccesoOrganizacion.usuario_id == usuario_id,
                AccesoOrganizacion.organizacion_id == organizacion_id,
                AccesoOrganizacion.categoria_dato == categoria_dato,
                AccesoOrganizacion.estado == EstadoPermiso.ACTIVO
            )
        ).first()
        
        if not acceso:
            return False
        
        # Verificar expiración
        if acceso.fecha_expiracion and acceso.fecha_expiracion < datetime.utcnow():
            acceso.estado = EstadoPermiso.EXPIRADO
            db.commit()
            return False
        
        return True


class SolicitudConsentimientoService:
    """Servicio para gestión de Solicitudes de Consentimiento"""
    
    @staticmethod
    def create_solicitud(db: Session, organizacion_id: uuid.UUID, rut_ciudadano: str,
                         proposal_json: dict, texto_legal_presentado: str,
                         request_type: str = "NORMAL", source_organization_id: uuid.UUID = None,
                         ai_flag: AiFlag = AiFlag.NONE, ip_solicitud: str = None) -> SolicitudConsentimiento:
        """Crea una nueva solicitud de consentimiento"""
        
        rut_hash = hash_rut_sha256(normalize_rut(rut_ciudadano))
        
        solicitud = SolicitudConsentimiento(
            organizacion_id=organizacion_id,
            rut_ciudadano_hash=rut_hash,
            proposal_json=proposal_json,
            texto_legal_presentado=texto_legal_presentado,
            request_type=request_type,
            source_organization_id=source_organization_id,
            ai_flag=ai_flag,
            ip_solicitud=ip_solicitud
        )
        
        db.add(solicitud)
        db.commit()
        db.refresh(solicitud)
        return solicitud
    
    @staticmethod
    def approve(db: Session, solicitud_id: uuid.UUID, usuario_id: uuid.UUID,
                ip_cliente: str = None) -> AccesoOrganizacion:
        """Aprueba una solicitud de consentimiento y crea los accesos correspondientes"""
        solicitud = db.query(SolicitudConsentimiento).filter(
            SolicitudConsentimiento.id == solicitud_id
        ).first()
        
        if not solicitud:
            raise ValueError("Solicitud no encontrada")
        
        if solicitud.estado != EstadoSolicitud.PENDIENTE:
            raise ValueError(f"Solicitud ya está en estado {solicitud.estado}")
        
        # Obtener usuario por hash
        usuario = db.query(Usuario).filter(Usuario.rut_hash == solicitud.rut_ciudadano_hash).first()
        if not usuario or usuario.id != usuario_id:
            raise ValueError("Usuario no corresponde a la solicitud")
        
        # Crear accesos desde proposal_json
        proposal = solicitud.proposal_json
        accesos_creados = []
        
        for categoria in proposal.get('categorias', []):
            acceso = AccesoOrganizacionService.grant_access(
                db=db,
                usuario_id=usuario.id,
                organizacion_id=solicitud.organizacion_id,
                categoria_dato=categoria.get('nombre'),
                finalidad=categoria.get('finalidad'),
                fecha_expiracion=categoria.get('fecha_expiracion'),
                signature_data={'ip': ip_cliente}
            )
            accesos_creados.append(acceso)
        
        solicitud.estado = EstadoSolicitud.APROBADA
        solicitud.fecha_respuesta = datetime.utcnow()
        db.commit()
        
        return accesos_creados[0] if accesos_creados else None
    
    @staticmethod
    def reject(db: Session, solicitud_id: uuid.UUID, motivo: str) -> bool:
        """Rechaza una solicitud de consentimiento"""
        solicitud = db.query(SolicitudConsentimiento).filter(
            SolicitudConsentimiento.id == solicitud_id
        ).first()
        
        if not solicitud:
            return False
        
        solicitud.estado = EstadoSolicitud.RECHAZADA
        solicitud.fecha_respuesta = datetime.utcnow()
        db.commit()
        return True


class SolicitudArcoService:
    """Servicio para gestión de Solicitudes ARCO"""
    
    @staticmethod
    def create_solicitud(db: Session, organizacion_id: uuid.UUID, rut_ciudadano: str,
                         tipo: TipoArco, token_evidencia_identidad: str,
                         descripcion: str = None) -> SolicitudArco:
        """Crea una nueva solicitud ARCO"""
        
        rut_hash = hash_rut_sha256(normalize_rut(rut_ciudadano))
        
        # Calcular fecha límite (10 días hábiles por defecto)
        fecha_limite = datetime.utcnow() + timedelta(days=15)  # Días corridos para simplificar
        
        solicitud = SolicitudArco(
            organizacion_id=organizacion_id,
            rut_ciudadano_hash=rut_hash,
            tipo=tipo,
            token_evidencia_identidad=token_evidencia_identidad,
            descripcion=descripcion,
            fecha_limite_respuesta=fecha_limite
        )
        
        db.add(solicitud)
        db.commit()
        db.refresh(solicitud)
        return solicitud
    
    @staticmethod
    def process(db: Session, solicitud_id: uuid.UUID, estado: EstadoArco,
                respuesta: str, prorrogar: bool = False) -> bool:
        """Procesa una solicitud ARCO"""
        solicitud = db.query(SolicitudArco).filter(SolicitudArco.id == solicitud_id).first()
        
        if not solicitud:
            return False
        
        if prorrogar:
            solicitud.prorrogado = True
            solicitud.estado = EstadoArco.PRORROGADA
            solicitud.fecha_limite_respuesta = datetime.utcnow() + timedelta(days=15)
        else:
            solicitud.estado = estado
            solicitud.respuesta = respuesta
            solicitud.fecha_respuesta = datetime.utcnow()
        
        db.commit()
        return True


class LogAccesoDatosService:
    """Servicio para gestión de Logs de Acceso (Auditoría)"""
    
    @staticmethod
    def log_access(db: Session, usuario_id: uuid.UUID, organizacion_id: uuid.UUID,
                   tipo_acceso: TipoAcceso, categoria_dato: str,
                   justificacion_legal: str, ip_origen: str,
                   user_agent: str = None, detalles_adicionales: dict = None) -> LogAccesoDatos:
        """Registra un acceso a datos para auditoría"""
        
        log = LogAccesoDatos(
            usuario_id=usuario_id,
            organizacion_id=organizacion_id,
            tipo_acceso=tipo_acceso,
            categoria_dato_consultado=categoria_dato,
            justificacion_legal=justificacion_legal,
            ip_origen=ip_origen,
            user_agent=user_agent,
            detalles_adicionales=detalles_adicionales
        )
        
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
    
    @staticmethod
    def get_logs(db: Session, usuario_id: uuid.UUID = None, organizacion_id: uuid.UUID = None,
                 fecha_desde: datetime = None, fecha_hasta: datetime = None,
                 limit: int = 100, offset: int = 0) -> List[LogAccesoDatos]:
        """Obtiene logs de acceso con filtros"""
        
        query = db.query(LogAccesoDatos)
        
        if usuario_id:
            query = query.filter(LogAccesoDatos.usuario_id == usuario_id)
        if organizacion_id:
            query = query.filter(LogAccesoDatos.organizacion_id == organizacion_id)
        if fecha_desde:
            query = query.filter(LogAccesoDatos.fecha_acceso >= fecha_desde)
        if fecha_hasta:
            query = query.filter(LogAccesoDatos.fecha_acceso <= fecha_hasta)
        
        query = query.order_by(LogAccesoDatos.fecha_acceso.desc())
        return query.offset(offset).limit(limit).all()
    
    @staticmethod
    def get_audit_report(db: Session, organizacion_id: uuid.UUID,
                         fecha_desde: datetime, fecha_hasta: datetime) -> dict:
        """Genera reporte de auditoría para una organización"""
        
        logs = db.query(LogAccesoDatos).filter(
            and_(
                LogAccesoDatos.organizacion_id == organizacion_id,
                LogAccesoDatos.fecha_acceso >= fecha_desde,
                LogAccesoDatos.fecha_acceso <= fecha_hasta
            )
        ).all()
        
        total_accesos = len(logs)
        accesos_por_tipo = {}
        accesos_por_categoria = {}
        
        for log in logs:
            tipo = log.tipo_acceso.value
            categoria = log.categoria_dato_consultado
            
            accesos_por_tipo[tipo] = accesos_por_tipo.get(tipo, 0) + 1
            accesos_por_categoria[categoria] = accesos_por_categoria.get(categoria, 0) + 1
        
        return {
            'total_accesos': total_accesos,
            'accesos_por_tipo': accesos_por_tipo,
            'accesos_por_categoria': accesos_por_categoria,
            'periodo': {
                'desde': fecha_desde.isoformat(),
                'hasta': fecha_hasta.isoformat()
            }
        }
