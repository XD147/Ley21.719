"""
Servicio de Webhooks para Notificaciones Automáticas
Ley 21.719 - Eventos de revocación, brechas y cambios de estado
"""
from datetime import datetime
from typing import List, Optional, Dict
from uuid import UUID
import hashlib
import hmac
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import Base
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text, Enum as SQLEnum, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID as PGUUID
import enum
import httpx

class TipoEventoWebhook(str, enum.Enum):
    CONSENTIMIENTO_OTORGADO = "CONSENTIMIENTO_OTORGADO"
    CONSENTIMIENTO_REVOCADO = "CONSENTIMIENTO_REVOCADO"
    ACCESO_DATOS_REALIZADO = "ACCESO_DATOS_REALIZADO"
    SOLICITUD_ARCO_RECIBIDA = "SOLICITUD_ARCO_RECIBIDA"
    SOLICITUD_ARCO_RESPONDIDA = "SOLICITUD_ARCO_RESPONDIDA"
    BRECHA_SEGURIDAD_NOTIFICADA = "BRECHA_SEGURIDAD_NOTIFICADA"
    DATOS_PORTABILIDAD_GENERADA = "DATOS_PORTABILIDAD_GENERADA"
    USUARIO_ELIMINADO = "USUARIO_ELIMINADO"

class EstadoEnvioWebhook(str, enum.Enum):
    PENDIENTE = "PENDIENTE"
    ENVIADO = "ENVIADO"
    FALLIDO = "FALLIDO"
    REINTENTANDO = "REINTENTANDO"

class RegistroWebhook(Base):
    __tablename__ = "registros_webhooks"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=func.gen_random_uuid())
    organizacion_id = Column(PGUUID(as_uuid=True), ForeignKey("organizaciones.id"), nullable=False, index=True)
    
    # Información del evento
    tipo_evento = Column(SQLEnum(TipoEventoWebhook), nullable=False)
    entidad_origen = Column(String(100))  # ej: "AccesoOrganizacion", "SolicitudArco"
    entidad_id = Column(PGUUID(as_uuid=True))
    
    # Payload
    payload = Column(JSON, nullable=False)
    signature = Column(String(256))  # HMAC-SHA256 para verificación
    
    # Intentos de envío
    url_destino = Column(String(500), nullable=False)
    estado = Column(SQLEnum(EstadoEnvioWebhook), default=EstadoEnvioWebhook.PENDIENTE)
    intentos = Column(Integer, default=0)
    max_intentos = Column(Integer, default=5)
    
    # Respuesta
    respuesta_status_code = Column(Integer)
    respuesta_body = Column(Text)
    
    # Fechas
    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False)
    fecha_envio = Column(DateTime)
    fecha_proximo_reintento = Column(DateTime)
    
    # Auditoría
    creado_por = Column(String(200))


class ServicioWebhooks:
    def __init__(self, db: AsyncSession, webhook_secret: str = ""):
        self.db = db
        self.webhook_secret = webhook_secret
    
    def generar_firma(self, payload: dict, timestamp: str) -> str:
        """Generar firma HMAC-SHA256 para verificar autenticidad del webhook"""
        mensaje = f"{timestamp}.{json.dumps(payload, sort_keys=True)}"
        firma = hmac.new(
            self.webhook_secret.encode('utf-8'),
            mensaje.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return firma
    
    async def registrar_evento(self, data: dict) -> RegistroWebhook:
        """Registrar un nuevo evento webhook"""
        timestamp = datetime.utcnow().isoformat()
        payload = {
            "id": str(data.get("entidad_id", "")),
            "tipo": data["tipo_evento"],
            "timestamp": timestamp,
            "datos": data.get("payload", {})
        }
        
        signature = self.generar_firma(payload, timestamp)
        
        registro = RegistroWebhook(
            organizacion_id=data["organizacion_id"],
            tipo_evento=data["tipo_evento"],
            entidad_origen=data.get("entidad_origen", ""),
            entidad_id=data.get("entidad_id"),
            payload=payload,
            signature=signature,
            url_destino=data["url_destino"],
            creado_por=data.get("creado_por", "")
        )
        
        self.db.add(registro)
        await self.db.commit()
        await self.db.refresh(registro)
        
        return registro
    
    async def enviar_webhook(self, registro_id: UUID) -> Dict:
        """Enviar webhook al destino configurado"""
        result = await self.db.execute(
            select(RegistroWebhook)
            .where(RegistroWebhook.id == registro_id)
        )
        registro = result.scalar_one_or_none()
        
        if not registro:
            return {"error": "Registro no encontrado"}
        
        if registro.estado == EstadoEnvioWebhook.ENVIADO:
            return {"info": "Webhook ya enviado"}
        
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": registro.signature,
            "X-Webhook-Timestamp": registro.payload.get("timestamp", ""),
            "X-Webhook-Type": registro.tipo_evento.value
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    registro.url_destino,
                    json=registro.payload,
                    headers=headers
                )
                
                registro.fecha_envio = datetime.utcnow()
                registro.respuesta_status_code = response.status_code
                registro.respuesta_body = response.text[:5000]  # Limitar tamaño
                
                if response.status_code in [200, 201, 204]:
                    registro.estado = EstadoEnvioWebhook.ENVIADO
                else:
                    registro.estado = EstadoEnvioWebhook.FALLIDO
                    registro.intentos += 1
                    
                    if registro.intentos < registro.max_intentos:
                        registro.estado = EstadoEnvioWebhook.REINTENTANDO
                        # Programar próximo reintento (exponential backoff)
                        from datetime import timedelta
                        delay_minutos = 5 * (2 ** registro.intentos)
                        registro.fecha_proximo_reintento = datetime.utcnow() + timedelta(minutes=delay_minutos)
                
                await self.db.commit()
                
                return {
                    "exitoso": response.status_code in [200, 201, 204],
                    "status_code": response.status_code,
                    "intentos": registro.intentos
                }
                
        except Exception as e:
            registro.estado = EstadoEnvioWebhook.FALLIDO
            registro.intentos += 1
            registro.respuesta_body = str(e)[:1000]
            
            if registro.intentos < registro.max_intentos:
                registro.estado = EstadoEnvioWebhook.REINTENTANDO
                from datetime import timedelta
                delay_minutos = 5 * (2 ** registro.intentos)
                registro.fecha_proximo_reintento = datetime.utcnow() + timedelta(minutes=delay_minutos)
            
            await self.db.commit()
            
            return {
                "exitoso": False,
                "error": str(e),
                "intentos": registro.intentos
            }
    
    async def obtener_pendientes_envio(self, limite: int = 100) -> List[RegistroWebhook]:
        """Obtener webhooks pendientes o que requieren reintento"""
        ahora = datetime.utcnow()
        result = await self.db.execute(
            select(RegistroWebhook)
            .where(RegistroWebhook.estado.in_([
                EstadoEnvioWebhook.PENDIENTE,
                EstadoEnvioWebhook.REINTENTANDO
            ]))
            .where(
                (RegistroWebhook.fecha_proximo_reintento.is_(None)) |
                (RegistroWebhook.fecha_proximo_reintento <= ahora)
            )
            .limit(limite)
        )
        return list(result.scalars().all())
    
    async def reenviar_fallidos(self, organizacion_id: UUID) -> int:
        """Reenviar todos los webhooks fallidos de una organización"""
        result = await self.db.execute(
            select(RegistroWebhook)
            .where(RegistroWebhook.organizacion_id == organizacion_id)
            .where(RegistroWebhook.estado == EstadoEnvioWebhook.FALLIDO)
            .where(RegistroWebhook.intentos < RegistroWebhook.max_intentos)
        )
        fallidos = list(result.scalars().all())
        
        for registro in fallidos:
            registro.estado = EstadoEnvioWebhook.REINTENTANDO
            registro.fecha_proximo_reintento = datetime.utcnow()
        
        await self.db.commit()
        
        return len(fallidos)
    
    async def obtener_historial(self, organizacion_id: UUID, limite: int = 50) -> List[RegistroWebhook]:
        """Obtener historial de webhooks enviados"""
        result = await self.db.execute(
            select(RegistroWebhook)
            .where(RegistroWebhook.organizacion_id == organizacion_id)
            .order_by(RegistroWebhook.fecha_creacion.desc())
            .limit(limite)
        )
        return list(result.scalars().all())
    
    async def verificar_firma_webhook(self, payload: dict, signature: str, timestamp: str) -> bool:
        """Verificar firma de webhook recibido (para validar webhooks entrantes)"""
        firma_esperada = self.generar_firma(payload, timestamp)
        return hmac.compare_digest(firma_esperada, signature)


# Funciones helper para disparar webhooks automáticos
async def notificar_revocacion_consentimiento(
    db: AsyncSession,
    organizacion_id: UUID,
    acceso_id: UUID,
    usuario_rut_hash: str,
    webhook_url: str
):
    """Disparar webhook cuando se revoca un consentimiento"""
    servicio = ServicioWebhooks(db)
    await servicio.registrar_evento({
        "organizacion_id": organizacion_id,
        "tipo_evento": TipoEventoWebhook.CONSENTIMIENTO_REVOCADO,
        "entidad_origen": "AccesoOrganizacion",
        "entidad_id": acceso_id,
        "payload": {
            "acceso_id": str(acceso_id),
            "usuario_rut_hash": usuario_rut_hash,
            "accion": "REVOCADO",
            "mensaje": "El usuario ha revocado el consentimiento de acceso a sus datos"
        },
        "url_destino": webhook_url
    })


async def notificar_solicitud_arco(
    db: AsyncSession,
    organizacion_id: UUID,
    solicitud_id: UUID,
    tipo_arco: str,
    webhook_url: str
):
    """Disparar webhook cuando llega nueva solicitud ARCO"""
    servicio = ServicioWebhooks(db)
    await servicio.registrar_evento({
        "organizacion_id": organizacion_id,
        "tipo_evento": TipoEventoWebhook.SOLICITUD_ARCO_RECIBIDA,
        "entidad_origen": "SolicitudArco",
        "entidad_id": solicitud_id,
        "payload": {
            "solicitud_id": str(solicitud_id),
            "tipo": tipo_arco,
            "estado": "RECIBIDA",
            "mensaje": "Nueva solicitud ARCO recibida"
        },
        "url_destino": webhook_url
    })


async def notificar_brecha_seguridad(
    db: AsyncSession,
    organizacion_id: UUID,
    brecha_id: UUID,
    nivel_riesgo: str,
    webhook_url: str
):
    """Disparar webhook cuando se notifica brecha de seguridad"""
    servicio = ServicioWebhooks(db)
    await servicio.registrar_evento({
        "organizacion_id": organizacion_id,
        "tipo_evento": TipoEventoWebhook.BRECHA_SEGURIDAD_NOTIFICADA,
        "entidad_origen": "NotificacionBrecha",
        "entidad_id": brecha_id,
        "payload": {
            "brecha_id": str(brecha_id),
            "nivel_riesgo": nivel_riesgo,
            "accion": "NOTIFICADA_AGENCIA",
            "mensaje": "Brecha de seguridad notificada a la Agencia"
        },
        "url_destino": webhook_url
    })
