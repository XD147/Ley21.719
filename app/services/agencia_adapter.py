"""
Adapter HTTP para notificaciones a la Agencia de Protección de Datos
Ley 21.719 - Notificación de brechas de seguridad (Art. 38-40)

Implementa modo producción (API real) y fallback (correo certificado al DPO)
"""

import httpx
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class ModoNotificacion(str, Enum):
    PRODUCCION = "produccion"  # POST real a API gubernamental
    FALLBACK = "fallback"      # Correo certificado al DPO
    SANDBOX = "sandbox"        # API de pruebas del gobierno


class AgenciaAdapter:
    """
    Adaptador para notificar brechas de seguridad a la Agencia de Protección de Datos
    
    Cuando la API del gobierno esté en producción, realiza POST real con payload firmado.
    Mientras tanto, envía correo electrónico certificado al DPO con reporte PDF.
    """
    
    def __init__(self, modo: ModoNotificacion = ModoNotificacion.FALLBACK):
        self.modo = modo
        self.agencia_api_url = "https://api.agenciaprotecciondatos.cl/v1/brechas"
        self.agencia_api_sandbox = "https://sandbox-api.agenciaprotecciondatos.cl/v1/brechas"
        self.timeout_seconds = 30
        self.max_reintentos = 3
        
        # Credenciales para API gubernamental (cuando esté disponible)
        self.api_key = None  # Se obtiene de variables de entorno
        self.certificado_digital = None  # Para firma de payloads
    
    async def notificar_agencia(self, brecha_data: Dict[str, Any], db=None) -> Dict[str, Any]:
        """
        Notifica una brecha de seguridad a la Agencia de Protección de Datos
        
        Args:
            brecha_data: Diccionario con datos de la brecha
                - organizacion_rut: RUT de la organización
                - organizacion_nombre: Razón social
                - fecha_descubrimiento: Fecha/hora del descubrimiento
                - fecha_notificacion: Fecha/hora de la notificación
                - tipo_brecha: Tipo de brecha (acceso no autorizado, pérdida, etc.)
                - categoria_datos: Categorías de datos afectados
                - cantidad_afectados: Número de titulares afectados
                - descripcion: Descripción detallada del incidente
                - medidas_tomadas: Medidas correctivas implementadas
                - dpo_contacto: Contacto del DPO
            
        Returns:
            Dict con resultado de la notificación
        """
        
        logger.info(f"Notificando brecha a la Agencia (modo: {self.modo.value})")
        
        if self.modo == ModoNotificacion.PRODUCCION:
            return await self._notificar_api_produccion(brecha_data)
        
        elif self.modo == ModoNotificacion.SANDBOX:
            return await self._notificar_api_sandbox(brecha_data)
        
        else:  # FALLBACK
            return await self._notificar_fallback_correo(brecha_data, db)
    
    async def _notificar_api_produccion(self, brecha_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Realiza POST real a la API gubernamental con payload firmado digitalmente
        """
        logger.info("Enviando notificación a API de producción de la Agencia")
        
        # Preparar payload según especificación del gobierno
        payload = self._preparar_payload_firmado(brecha_data)
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'X-Firma-Digital': payload['firma_digital'],
            'X-Certificado-Serie': payload['certificado_serie'],
        }
        
        # Eliminar campos internos del payload
        payload_clean = {k: v for k, v in payload.items() 
                        if k not in ['firma_digital', 'certificado_serie']}
        
        reintentos = 0
        last_error = None
        
        while reintentos < self.max_reintentos:
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.post(
                        self.agencia_api_url,
                        json=payload_clean,
                        headers=headers
                    )
                    
                    if response.status_code == 201:
                        respuesta = response.json()
                        logger.info(f"Breach notificada exitosamente. ID: {respuesta.get('id')}")
                        
                        return {
                            'estado': 'EXITOSO',
                            'modo': 'PRODUCCION',
                            'id_agencia': respuesta.get('id'),
                            'fecha_notificacion': datetime.utcnow().isoformat(),
                            'acuse_recibo': respuesta.get('acuse_recibo'),
                            'detalle': 'Notificación recibida por la Agencia'
                        }
                    
                    elif response.status_code == 400:
                        logger.error(f"Error en payload: {response.text}")
                        return {
                            'estado': 'ERROR',
                            'modo': 'PRODUCCION',
                            'error': 'Payload inválido',
                            'detalle': response.text
                        }
                    
                    else:
                        logger.warning(f"Status code inesperado: {response.status_code}")
                        last_error = f"Status {response.status_code}: {response.text}"
                        
            except httpx.ConnectTimeout:
                last_error = "Timeout de conexión"
                logger.warning(f"Intento {reintentos + 1} fallido: {last_error}")
                
            except httpx.NetworkError as e:
                last_error = f"Error de red: {str(e)}"
                logger.warning(f"Intento {reintentos + 1} fallido: {last_error}")
            
            reintentos += 1
            if reintentos < self.max_reintentos:
                import asyncio
                await asyncio.sleep(5 * reintentos)  # Backoff exponencial
        
        # Si todos los reintentos fallan, hacer fallback a correo
        logger.error("Todos los reintentos fallaron, ejecutando fallback a correo")
        return await self._notificar_fallback_correo(brecha_data, None)
    
    async def _notificar_api_sandbox(self, brecha_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Notifica a la API de sandbox del gobierno (para testing)
        """
        logger.info("Enviando notificación a API de sandbox")
        
        payload = self._preparar_payload_firmado(brecha_data)
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key or "sandbox-token"}',
        }
        
        payload_clean = {k: v for k, v in payload.items() 
                        if k not in ['firma_digital', 'certificado_serie']}
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    self.agencia_api_sandbox,
                    json=payload_clean,
                    headers=headers
                )
                
                if response.status_code in [200, 201]:
                    respuesta = response.json()
                    logger.info(f"Sandbox: Breach notificada. ID: {respuesta.get('id')}")
                    
                    return {
                        'estado': 'EXITOSO',
                        'modo': 'SANDBOX',
                        'id_agencia': respuesta.get('id'),
                        'fecha_notificacion': datetime.utcnow().isoformat(),
                        'detalle': 'Notificación de prueba enviada a sandbox'
                    }
                else:
                    return {
                        'estado': 'ERROR',
                        'modo': 'SANDBOX',
                        'detalle': response.text
                    }
                    
        except Exception as e:
            logger.error(f"Error en sandbox: {str(e)}")
            return {
                'estado': 'ERROR',
                'modo': 'SANDBOX',
                'error': str(e)
            }
    
    async def _notificar_fallback_correo(self, brecha_data: Dict[str, Any], db=None) -> Dict[str, Any]:
        """
        Fallback: Envía correo electrónico certificado al DPO con reporte PDF adjunto
        para que lo ingrese manualmente al portal de la Agencia
        """
        logger.warning("Modo FALLBACK: Enviando correo certificado al DPO")
        
        from app.services.certificate_generator import CertificateGenerator
        from app.services.email_service import EmailService
        
        try:
            # Generar reporte PDF de la brecha
            cert_generator = CertificateGenerator()
            pdf_reporte = await cert_generator.generar_reporte_brecha(brecha_data)
            
            # Preparar contenido del correo
            asunto = f"[URGENTE] Notificación de Brecha de Seguridad - {brecha_data['organizacion_nombre']}"
            
            cuerpo_email = f"""
            Estimado(a) DPO,
            
            Se ha detectado una brecha de seguridad que debe ser notificada a la Agencia de Protección de Datos
            en un plazo máximo de 72 horas desde su descubrimiento, conforme al Art. 38 de la Ley 21.719.
            
            DETALLES DE LA BRECHA:
            ----------------------------------------
            Organización: {brecha_data['organizacion_nombre']}
            RUT: {brecha_data['organizacion_rut']}
            Fecha de descubrimiento: {brecha_data['fecha_descubrimiento']}
            Tipo de brecha: {brecha_data['tipo_brecha']}
            Categorías afectadas: {brecha_data['categoria_datos']}
            Cantidad de afectados: {brecha_data['cantidad_afectados']}
            ----------------------------------------
            
            ADJUNTO:
            - Reporte forense completo en PDF
            - Formulario pre-llenado para el portal de la Agencia
            - Evidencia documental del incidente
            
            ACCIONES REQUERIDAS:
            1. Revisar el reporte adjunto
            2. Ingresar al portal de la Agencia: https://portal.agenciaprotecciondatos.cl
            3. Completar el formulario de notificación de brechas
            4. Adjuntar este reporte como evidencia
            5. Conservar el acuse de recibo para auditoría
            
            Este correo constituye constancia de la notificación interna realizada.
            
            Saludos cordiales,
            Sistema de Cumplimiento Ley 21.719
            """
            
            # Enviar correo certificado al DPO
            email_service = EmailService()
            await email_service.enviar_correo_certificado(
                destinatario=brecha_data.get('dpo_contacto', 'dpo@organizacion.cl'),
                asunto=asunto,
                cuerpo=cuerpo_email,
                adjuntos=[
                    ('reporte_brecha.pdf', pdf_reporte, 'application/pdf'),
                ],
                prioridad='alta',
                confirmacion_lectura=True
            )
            
            logger.info("Correo certificado enviado exitosamente al DPO")
            
            return {
                'estado': 'FALLBACK_EXITOSO',
                'modo': 'CORREO_CERTIFICADO',
                'fecha_notificacion': datetime.utcnow().isoformat(),
                'destinatario': brecha_data.get('dpo_contacto'),
                'detalle': 'Correo certificado enviado al DPO con reporte PDF adjunto. '
                          'El DPO debe ingresar manualmente la notificación al portal de la Agencia.'
            }
            
        except Exception as e:
            logger.error(f"Error enviando correo de fallback: {str(e)}")
            return {
                'estado': 'ERROR_FALLBACK',
                'modo': 'CORREO_CERTIFICADO',
                'error': str(e),
                'detalle': 'No se pudo enviar el correo de fallback'
            }
    
    def _preparar_payload_firmado(self, brecha_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepara el payload JSON firmado digitalmente según especificación del gobierno
        """
        # Estructura base del payload
        payload = {
            'rut_organizacion': brecha_data['organizacion_rut'],
            'razon_social': brecha_data['organizacion_nombre'],
            'fecha_descubrimiento': brecha_data['fecha_descubrimiento'],
            'fecha_notificacion': datetime.utcnow().isoformat(),
            'tipo_brecha': brecha_data['tipo_brecha'],
            'categorias_datos_afectados': brecha_data['categoria_datos'],
            'cantidad_titulares_afectados': brecha_data['cantidad_afectados'],
            'descripcion_incidente': brecha_data['descripcion'],
            'medidas_correctivas': brecha_data['medidas_tomadas'],
            'contacto_dpo': brecha_data['dpo_contacto'],
            'nivel_riesgo': self._calcular_nivel_riesgo(brecha_data),
        }
        
        # En producción, aquí se firmaría digitalmente el payload
        # Por ahora, marcadores de posición
        payload['firma_digital'] = 'PENDIENTE_CONFIGURACION_CERTIFICADO'
        payload['certificado_serie'] = 'PENDIENTE_CONFIGURACION_CERTIFICADO'
        
        return payload
    
    def _calcular_nivel_riesgo(self, brecha_data: Dict[str, Any]) -> str:
        """
        Calcula el nivel de riesgo de la brecha (BAJO, MEDIO, ALTO, CRÍTICO)
        según cantidad de afectados y tipo de datos
        """
        cantidad = brecha_data.get('cantidad_afectados', 0)
        categorias = brecha_data.get('categoria_datos', [])
        
        # Datos sensibles incrementan nivel de riesgo
        datos_sensibles = ['SALUD', 'BIOMETRIA', 'ORIENTACION_SEXUAL', 
                          'OPINION_POLITICA', 'RELIGION', 'GENETICA']
        
        tiene_datos_sensibles = any(cat in datos_sensibles for cat in categorias)
        
        if cantidad > 10000 or (tiene_datos_sensibles and cantidad > 1000):
            return 'CRITICO'
        elif cantidad > 1000 or (tiene_datos_sensibles and cantidad > 100):
            return 'ALTO'
        elif cantidad > 100 or tiene_datos_sensibles:
            return 'MEDIO'
        else:
            return 'BAJO'
    
    async def verificar_estado_notificacion(self, id_agencia: str) -> Dict[str, Any]:
        """
        Verifica el estado de una notificación previamente enviada
        """
        if self.modo != ModoNotificacion.PRODUCCION:
            return {'estado': 'NO_DISPONIBLE', 'detalle': 'Solo disponible en modo producción'}
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(
                    f"{self.agencia_api_url}/{id_agencia}",
                    headers={'Authorization': f'Bearer {self.api_key}'}
                )
                
                if response.status_code == 200:
                    return {
                        'estado': 'VERIFICADO',
                        'datos': response.json()
                    }
                else:
                    return {
                        'estado': 'ERROR',
                        'detalle': f'Status {response.status_code}'
                    }
                    
        except Exception as e:
            return {
                'estado': 'ERROR',
                'error': str(e)
            }


# Factory para obtener instancia configurada
def get_agencia_adapter() -> AgenciaAdapter:
    """
    Factory function para obtener el adapter configurado según variables de entorno
    """
    import os
    
    modo_config = os.getenv('AGENCIA_NOTIFICACION_MODO', 'fallback').lower()
    
    if modo_config == 'produccion':
        modo = ModoNotificacion.PRODUCCION
    elif modo_config == 'sandbox':
        modo = ModoNotificacion.SANDBOX
    else:
        modo = ModoNotificacion.FALLBACK
    
    adapter = AgenciaAdapter(modo=modo)
    
    # Configurar credenciales si están disponibles
    adapter.api_key = os.getenv('AGENCIA_API_KEY')
    
    return adapter
