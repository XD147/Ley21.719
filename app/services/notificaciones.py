"""
Servicio de Notificaciones Seguras para Ley 21.719
Notificación de brechas a Agencia Digital y afectados (Art. 38-40)
"""
import logging
from typing import List, Optional
from datetime import datetime
import httpx
from app.config import settings
from app.models.models import LogAccesoDatos

logger = logging.getLogger(__name__)

class NotificacionSeguraService:
    """
    Gestiona notificaciones obligatorias de brechas de seguridad.
    Requiere canal seguro y evidencia de envío.
    """
    
    def __init__(self):
        self.agencia_endpoint = settings.agencia_digital_endpoint
        self.timeout = 30.0

    async def notificar_brecha_agencia(
        self, 
        brecha_id: str, 
        descripcion: str, 
        datos_afectados: List[str],
        medidas_tomadas: str,
        organizacion_rut: str
    ) -> dict:
        """
        Notifica brecha a la Agencia Digital dentro de las 72h.
        Retorna acuse de recibo oficial.
        """
        payload = {
            "id_brecha_interna": brecha_id,
            "rut_notificante": organizacion_rut,
            "fecha_notificacion": datetime.utcnow().isoformat(),
            "descripcion_hechos": descripcion,
            "categorias_datos": datos_afectados,
            "medidas_mitigacion": medidas_tomadas,
            "nivel_riesgo": self._calcular_riesgo(datos_afectados)
        }

        try:
            # Simulación de envío a API Agencia Digital
            # En producción: Certificado digital obligatorio
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.agencia_endpoint}/api/v1/brechas/reporte",
                    json=payload,
                    timeout=self.timeout,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                
                registro_log = {
                    "tipo": "NOTIFICACION_AGENCIA",
                    "estado": "EXITOSO",
                    "id_expediente_agencia": response.json().get("id_expediente"),
                    "fecha": datetime.utcnow()
                }
                logger.info(f"Notificación Agencia exitosa: {registro_log}")
                return registro_log
                
        except Exception as e:
            logger.error(f"Fallo notificación Agencia: {str(e)}")
            # Reintentar cola asíncrona en producción
            return {"estado": "FALLIDO", "error": str(e)}

    async def notificar_afectados(
        self,
        usuarios_afectados: List[dict],
        brecha_descripcion: str,
        recomendaciones: str,
        organizacion_nombre: str
    ) -> int:
        """
        Notifica a los usuarios afectados cuando hay alto riesgo.
        Lenguaje claro y sin tecnicismos (Art. 39).
        """
        enviados = 0
        for usuario in usuarios_afectados:
            try:
                # En producción: Usar servicio de email transaccional cifrado
                mensaje = f"""
                ESTIMADO/A {usuario.get('nombre', 'CIUDADANO')}:
                
                La organización {organizacion_nombre} informa un incidente de seguridad.
                
                HECHOS: {brecha_descripcion}
                DATOS COMPROMETIDOS: {', '.join(usuario.get('datos_afectados', []))}
                
                RECOMENDACIONES:
                {recomendaciones}
                
                Puede ejercer sus derechos ARCO contactando a nuestro DPO.
                """
                
                # Simular envío
                logger.info(f"Enviando notificación a {usuario.get('email')}")
                enviados += 1
                
                # Registrar log de notificación para auditoría
                await self._registrar_log_notificacion(usuario.get('id'), organizacion_nombre)
                
            except Exception as e:
                logger.error(f"Error notificando a {usuario.get('email')}: {e}")
        
        return enviados

    def _calcular_riesgo(self, datos_afectados: List[str]) -> str:
        """Calcula nivel de riesgo según tipo de dato (Art. 38)."""
        datos_alto_riesgo = ["SALUD", "BIOMETRIA", "FINANCIERO", "CONDUCTA"]
        if any(dato in datos_afectados for dato in datos_alto_riesgo):
            return "ALTO"
        elif len(datos_afectados) > 1000:
            return "MEDIO_ALTO"
        return "MEDIO"

    async def _registrar_log_notificacion(self, usuario_id: str, organizacion: str):
        """Registra evidencia de notificación al afectado."""
        # Implementación de persistencia de evidencia
        pass

notificacion_service = NotificacionSeguraService()
