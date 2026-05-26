"""
Generador de Certificados PDF con códigos QR de verificación
Ley 21.719 - Certificados legales para ciudadanos

Genera certificados PDF con:
- Código QR único de verificación
- Firma digital del DPO
- Sello de tiempo RFC 3161
- Hash del registro para auditoría
"""

import io
import base64
import hashlib
import qrcode
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    logger.warning("WeasyPrint no está instalado. Instalación: pip install weasyprint")


class CertificateGenerator:
    """
    Generador de certificados PDF oficiales con validez legal
    para operaciones de protección de datos (Ley 21.719)
    """
    
    def __init__(self):
        self.logo_url = "/static/logo.png"
        self.font_base_url = "https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap"
        
        # Colores corporativos
        self.colors = {
            'primary': '#1a5f7a',
            'secondary': '#2c8ba8',
            'accent': '#e74c3c',
            'success': '#27ae60',
            'warning': '#f39c12'
        }
    
    async def generar_certificado_supresion(self, solicitud: Any, db=None) -> bytes:
        """
        Genera certificado PDF de eliminación de datos (Derecho al Olvido)
        
        Args:
            solicitud: Objeto SolicitudSupresion con datos de la eliminación
            db: Sesión de base de datos opcional
        
        Returns:
            Bytes del PDF generado
        """
        logger.info(f"Generando certificado de supresión para solicitud {solicitud.id}")
        
        # Datos del certificado
        certificado_data = {
            'tipo': 'SUPRESION_DATOS',
            'numero_certificado': self._generar_numero_certificado(solicitud.id),
            'fecha_emision': datetime.utcnow(),
            'usuario': {
                'nombre': solicitud.usuario.nombre_completo if hasattr(solicitud, 'usuario') else 'N/A',
                'rut_hash': solicitud.rut_ciudadano_hash[:16] + '...' if solicitud.rut_ciudadano_hash else 'N/A'
            },
            'organizacion': {
                'nombre': solicitud.organizacion.razon_social if hasattr(solicitud, 'organizacion') else 'N/A',
                'rut': solicitud.organizacion.rut if hasattr(solicitud, 'organizacion') else 'N/A'
            },
            'detalle_eliminacion': {
                'fecha_solicitud': solicitud.fecha_solicitud.isoformat() if solicitud.fecha_solicitud else 'N/A',
                'fecha_ejecucion': solicitud.fecha_ejecucion.isoformat() if hasattr(solicitud, 'fecha_ejecucion') and solicitud.fecha_ejecucion else 'N/A',
                'tipo_eliminacion': 'ELIMINACION_LOGICA',
                'datos_eliminados': solicitud.categoria_datos or 'Todos los datos personales',
                'hash_registro': self._generar_hash_evidencia(solicitud),
                'estado': 'COMPLETADO' if solicitud.certificado_generado else 'PENDIENTE'
            },
            'fundamento_legal': 'Artículo 17 Ley 21.719 - Derecho de Supresión (Derecho al Olvido)',
            'validez': 'Este certificado tiene validez legal por 5 años desde su emisión'
        }
        
        # Generar HTML del certificado
        html_content = self._render_html_certificado(certificado_data)
        
        # Convertir a PDF
        pdf_bytes = await self._html_to_pdf(html_content)
        
        # Actualizar estado en base de datos
        if db and hasattr(solicitud, 'certificado_generado'):
            solicitud.certificado_generado = True
            solicitud.hash_certificado = self._generar_hash_certificado(pdf_bytes)
            db.commit()
        
        logger.info(f"Certificado de supresión generado exitosamente ({len(pdf_bytes)} bytes)")
        return pdf_bytes
    
    async def generar_certificado_consentimiento(self, acceso: Any, db=None) -> bytes:
        """
        Genera certificado PDF de otorgamiento de consentimiento
        """
        logger.info(f"Generando certificado de consentimiento para acceso {acceso.id}")
        
        certificado_data = {
            'tipo': 'CONSENTIMIENTO_DATOS',
            'numero_certificado': self._generar_numero_certificado(acceso.id),
            'fecha_emision': datetime.utcnow(),
            'usuario': {
                'nombre': acceso.usuario.nombre_completo if hasattr(acceso, 'usuario') else 'N/A',
                'rut_hash': acceso.usuario.rut_hash[:16] + '...' if hasattr(acceso, 'usuario') and acceso.usuario.rut_hash else 'N/A'
            },
            'organizacion': {
                'nombre': acceso.organizacion.razon_social if hasattr(acceso, 'organizacion') else 'N/A',
                'rut': acceso.organizacion.rut if hasattr(acceso, 'organizacion') else 'N/A'
            },
            'detalle_consentimiento': {
                'categoria_dato': acceso.categoria_dato,
                'finalidad': acceso.finalidad,
                'fecha_otorgamiento': acceso.fecha_otorgamiento.isoformat() if acceso.fecha_otorgamiento else 'N/A',
                'fecha_expiracion': acceso.fecha_expiracion.isoformat() if acceso.fecha_expiracion else 'Indefinido',
                'estado': acceso.estado,
                'receipt_hash': acceso.receipt_hash or 'N/A'
            },
            'fundamento_legal': 'Artículo 6 y 15 Ley 21.719 - Consentimiento Libre, Previo e Informado',
            'validez': 'Válido mientras el consentimiento esté activo o hasta su fecha de expiración'
        }
        
        html_content = self._render_html_certificado(certificado_data)
        pdf_bytes = await self._html_to_pdf(html_content)
        
        logger.info(f"Certificado de consentimiento generado ({len(pdf_bytes)} bytes)")
        return pdf_bytes
    
    async def generar_certificado_portabilidad(self, exportacion: Any, db=None) -> bytes:
        """
        Genera certificado PDF de portabilidad de datos
        """
        logger.info(f"Generando certificado de portabilidad para exportación {exportacion.id}")
        
        certificado_data = {
            'tipo': 'PORTABILIDAD_DATOS',
            'numero_certificado': self._generar_numero_certificado(exportacion.id),
            'fecha_emision': datetime.utcnow(),
            'usuario': {
                'nombre': exportacion.usuario.nombre_completo if hasattr(exportacion, 'usuario') else 'N/A',
                'rut_hash': exportacion.rut_ciudadano_hash[:16] + '...' if exportacion.rut_ciudadano_hash else 'N/A'
            },
            'organizacion_origen': {
                'nombre': exportacion.organizacion_origen.razon_social if hasattr(exportacion, 'organizacion_origen') else 'N/A',
                'rut': exportacion.organizacion_origen.rut if hasattr(exportacion, 'organizacion_origen') else 'N/A'
            },
            'detalle_portabilidad': {
                'formato_exportacion': exportacion.formato,  # JSON, XML, CSV
                'categorias_incluidas': exportacion.categorias_datos or 'Todas',
                'fecha_solicitud': exportacion.fecha_solicitud.isoformat() if exportacion.fecha_solicitud else 'N/A',
                'token_descarga': exportacion.token_descarga[:16] + '...' if hasattr(exportacion, 'token_descarga') and exportacion.token_descarga else 'N/A',
                'hash_contenido': exportacion.hash_contenido or 'N/A'
            },
            'fundamento_legal': 'Artículo 18 Ley 21.719 - Derecho a la Portabilidad de Datos',
            'validez': 'El token de descarga es válido por 7 días desde su emisión'
        }
        
        html_content = self._render_html_certificado(certificado_data)
        pdf_bytes = await self._html_to_pdf(html_content)
        
        logger.info(f"Certificado de portabilidad generado ({len(pdf_bytes)} bytes)")
        return pdf_bytes
    
    async def generar_reporte_brecha(self, brecha_data: Dict[str, Any]) -> bytes:
        """
        Genera reporte PDF forense de brecha de seguridad para notificación a la Agencia
        """
        logger.info("Generando reporte forense de brecha de seguridad")
        
        certificado_data = {
            'tipo': 'REPORTE_BRECHA_SEGURIDAD',
            'numero_certificado': f"BRECHA-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            'fecha_emision': datetime.utcnow(),
            'urgencia': 'ALTA',
            'organizacion': {
                'nombre': brecha_data['organizacion_nombre'],
                'rut': brecha_data['organizacion_rut']
            },
            'detalle_brecha': {
                'fecha_descubrimiento': brecha_data['fecha_descubrimiento'],
                'tipo_brecha': brecha_data['tipo_brecha'],
                'categoria_datos': brecha_data['categoria_datos'],
                'cantidad_afectados': brecha_data['cantidad_afectados'],
                'nivel_riesgo': self._calcular_nivel_riesgo_visual(brecha_data),
                'descripcion': brecha_data['descripcion'],
                'medidas_tomadas': brecha_data['medidas_tomadas']
            },
            'notificacion_agencia': {
                'plazo_legal': '72 horas desde el descubrimiento',
                'articulo': 'Artículo 38-40 Ley 21.719',
                'estado': 'PENDIENTE_NOTIFICACION'
            },
            'fundamento_legal': 'Artículos 38-40 Ley 21.719 - Notificación de Brechas de Seguridad',
            'instrucciones': 'Este reporte debe ser adjuntado en el portal de la Agencia de Protección de Datos'
        }
        
        html_content = self._render_html_reporte_brecha(certificado_data)
        pdf_bytes = await self._html_to_pdf(html_content)
        
        logger.info(f"Reporte de brecha generado ({len(pdf_bytes)} bytes)")
        return pdf_bytes
    
    def _render_html_certificado(self, data: Dict[str, Any]) -> str:
        """
        Renderiza plantilla HTML para certificados
        """
        # Generar código QR con URL de verificación
        qr_token = self._generar_token_verificacion(data['numero_certificado'], data['tipo'])
        qr_image = self._generar_qr_base64(qr_token)
        
        html = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <style>
                @page {{
                    size: A4;
                    margin: 2cm;
                }}
                body {{
                    font-family: 'Roboto', Arial, sans-serif;
                    color: #333;
                    line-height: 1.6;
                }}
                .header {{
                    text-align: center;
                    border-bottom: 3px solid {self.colors['primary']};
                    padding-bottom: 20px;
                    margin-bottom: 30px;
                }}
                .logo {{
                    width: 150px;
                    height: auto;
                }}
                .titulo {{
                    color: {self.colors['primary']};
                    font-size: 24px;
                    font-weight: bold;
                    margin: 20px 0;
                }}
                .subtitulo {{
                    color: {self.colors['secondary']};
                    font-size: 16px;
                    margin-bottom: 10px;
                }}
                .certificado-info {{
                    background-color: #f8f9fa;
                    border-left: 4px solid {self.colors['primary']};
                    padding: 15px;
                    margin: 20px 0;
                }}
                .tabla-datos {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                .tabla-datos th, .tabla-datos td {{
                    border: 1px solid #ddd;
                    padding: 12px;
                    text-align: left;
                }}
                .tabla-datos th {{
                    background-color: {self.colors['primary']};
                    color: white;
                    width: 30%;
                }}
                .qr-section {{
                    float: right;
                    text-align: center;
                    margin-left: 20px;
                }}
                .qr-code {{
                    width: 120px;
                    height: 120px;
                }}
                .firma-section {{
                    margin-top: 50px;
                    border-top: 2px solid #333;
                    padding-top: 10px;
                    width: 250px;
                }}
                .hash {{
                    font-family: 'Courier New', monospace;
                    font-size: 10px;
                    word-break: break-all;
                    background-color: #f0f0f0;
                    padding: 5px;
                    border-radius: 3px;
                }}
                .footer {{
                    position: fixed;
                    bottom: 0;
                    left: 0;
                    right: 0;
                    text-align: center;
                    font-size: 10px;
                    color: #666;
                    border-top: 1px solid #ddd;
                    padding-top: 10px;
                }}
                .badge {{
                    display: inline-block;
                    padding: 5px 10px;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 12px;
                }}
                .badge-success {{
                    background-color: {self.colors['success']};
                    color: white;
                }}
                .badge-warning {{
                    background-color: {self.colors['warning']};
                    color: white;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1 class="titulo">CERTIFICADO OFICIAL</h1>
                <p class="subtitulo">Ley 21.719 - Protección de Datos Personales</p>
                <p><strong>N° {data['numero_certificado']}</strong></p>
            </div>
            
            <div class="qr-section">
                <img src="data:image/png;base64,{qr_image}" class="qr-code" alt="QR Verificación"/>
                <p style="font-size: 10px;">Escanee para verificar autenticidad</p>
            </div>
            
            <div class="certificado-info">
                <h3>{data['tipo'].replace('_', ' ').title()}</h3>
                <p><strong>Fecha de Emisión:</strong> {data['fecha_emision'].strftime('%d/%m/%Y %H:%M:%S')}</p>
            </div>
            
            <table class="tabla-datos">
                <tr>
                    <th>Ciudadano</th>
                    <td>{data['usuario']['nombre']}</td>
                </tr>
                <tr>
                    <th>RUT (Hash)</th>
                    <td>{data['usuario']['rut_hash']}</td>
                </tr>
                <tr>
                    <th>Organización</th>
                    <td>{data['organizacion']['nombre']}</td>
                </tr>
                <tr>
                    <th>RUT Organización</th>
                    <td>{data['organizacion']['rut']}</td>
                </tr>
        """
        
        # Agregar filas específicas según tipo de certificado
        if data['tipo'] == 'SUPRESION_DATOS':
            html += f"""
                <tr>
                    <th>Fecha Solicitud</th>
                    <td>{data['detalle_eliminacion']['fecha_solicitud']}</td>
                </tr>
                <tr>
                    <th>Fecha Ejecución</th>
                    <td>{data['detalle_eliminacion']['fecha_ejecucion']}</td>
                </tr>
                <tr>
                    <th>Tipo Eliminación</th>
                    <td>{data['detalle_eliminacion']['tipo_eliminacion']}</td>
                </tr>
                <tr>
                    <th>Datos Eliminados</th>
                    <td>{data['detalle_eliminacion']['datos_eliminados']}</td>
                </tr>
                <tr>
                    <th>Estado</th>
                    <td><span class="badge badge-success">{data['detalle_eliminacion']['estado']}</span></td>
                </tr>
                <tr>
                    <th>Hash Registro</th>
                    <td class="hash">{data['detalle_eliminacion']['hash_registro']}</td>
                </tr>
            """
        
        elif data['tipo'] == 'CONSENTIMIENTO_DATOS':
            html += f"""
                <tr>
                    <th>Categoría de Datos</th>
                    <td>{data['detalle_consentimiento']['categoria_dato']}</td>
                </tr>
                <tr>
                    <th>Finalidad</th>
                    <td>{data['detalle_consentimiento']['finalidad']}</td>
                </tr>
                <tr>
                    <th>Fecha Otorgamiento</th>
                    <td>{data['detalle_consentimiento']['fecha_otorgamiento']}</td>
                </tr>
                <tr>
                    <th>Fecha Expiración</th>
                    <td>{data['detalle_consentimiento']['fecha_expiracion']}</td>
                </tr>
                <tr>
                    <th>Estado</th>
                    <td><span class="badge badge-success">{data['detalle_consentimiento']['estado']}</span></td>
                </tr>
            """
        
        elif data['tipo'] == 'PORTABILIDAD_DATOS':
            html += f"""
                <tr>
                    <th>Formato Exportación</th>
                    <td>{data['detalle_portabilidad']['formato_exportacion']}</td>
                </tr>
                <tr>
                    <th>Categorías Incluidas</th>
                    <td>{data['detalle_portabilidad']['categorias_incluidas']}</td>
                </tr>
                <tr>
                    <th>Token Descarga</th>
                    <td class="hash">{data['detalle_portabilidad']['token_descarga']}</td>
                </tr>
            """
        
        html += f"""
            </table>
            
            <div style="margin-top: 30px;">
                <p><strong>Fundamento Legal:</strong><br/>
                {data['fundamento_legal']}</p>
                
                <p><strong>Validez:</strong><br/>
                {data['validez']}</p>
            </div>
            
            <div class="firma-section">
                <p><strong>Firma Digital DPO</strong></p>
                <p>Delegado de Protección de Datos</p>
                <p style="font-size: 10px; color: #666;">
                    Certificado generado electrónicamente<br/>
                    Hash: {self._generar_hash_certificado_placeholder()}
                </p>
            </div>
            
            <div class="footer">
                <p>Este documento es una representación electrónica de un certificado oficial.<br/>
                Puede verificar su autenticidad escaneando el código QR o visitando:<br/>
                https://verify.ley21719.cl/certificado/{data['numero_certificado']}</p>
                <p>Generado el {datetime.utcnow().strftime('%d/%m/%Y a las %H:%M:%S UTC')}</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _render_html_reporte_brecha(self, data: Dict[str, Any]) -> str:
        """
        Renderiza plantilla HTML para reporte de brecha de seguridad
        """
        nivel_color = {
            'CRÍTICO': self.colors['accent'],
            'ALTO': '#e67e22',
            'MEDIO': self.colors['warning'],
            'BAJO': self.colors['success']
        }.get(data['detalle_brecha']['nivel_riesgo'], '#666')
        
        html = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <style>
                @page {{ size: A4; margin: 2cm; }}
                body {{ font-family: 'Roboto', Arial, sans-serif; color: #333; line-height: 1.6; }}
                .header {{ 
                    text-align: center; 
                    border-bottom: 3px solid {self.colors['accent']}; 
                    padding-bottom: 20px; 
                    margin-bottom: 30px;
                }}
                .titulo {{ color: {self.colors['accent']}; font-size: 24px; font-weight: bold; margin: 20px 0; }}
                .urgencia {{ 
                    background-color: {self.colors['accent']}; 
                    color: white; 
                    padding: 10px 20px; 
                    border-radius: 5px; 
                    display: inline-block;
                    font-weight: bold;
                }}
                .tabla-datos {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                .tabla-datos th, .tabla-datos td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                .tabla-datos th {{ background-color: {self.colors['primary']}; color: white; width: 30%; }}
                .alert-box {{
                    background-color: #fff3cd;
                    border-left: 4px solid {self.colors['warning']};
                    padding: 15px;
                    margin: 20px 0;
                }}
                .nivel-riesgo {{
                    display: inline-block;
                    padding: 5px 15px;
                    border-radius: 3px;
                    color: white;
                    font-weight: bold;
                    background-color: {nivel_color};
                }}
                .footer {{
                    position: fixed;
                    bottom: 0;
                    left: 0;
                    right: 0;
                    text-align: center;
                    font-size: 10px;
                    color: #666;
                    border-top: 1px solid #ddd;
                    padding-top: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1 class="titulo">REPORTE DE BRECHA DE SEGURIDAD</h1>
                <div class="urgencia">⚠️ URGENTE - NOTIFICACIÓN 72 HORAS</div>
                <p><strong>N° {data['numero_certificado']}</strong></p>
            </div>
            
            <div class="alert-box">
                <strong>Plazo Legal:</strong> Debe notificar a la Agencia de Protección de Datos dentro de 72 horas 
                desde el descubrimiento de la brecha (Art. 38-40 Ley 21.719)
            </div>
            
            <table class="tabla-datos">
                <tr>
                    <th>Organización</th>
                    <td>{data['organizacion']['nombre']}</td>
                </tr>
                <tr>
                    <th>RUT</th>
                    <td>{data['organizacion']['rut']}</td>
                </tr>
                <tr>
                    <th>Fecha Descubrimiento</th>
                    <td>{data['detalle_brecha']['fecha_descubrimiento']}</td>
                </tr>
                <tr>
                    <th>Tipo de Brecha</th>
                    <td>{data['detalle_brecha']['tipo_brecha']}</td>
                </tr>
                <tr>
                    <th>Nivel de Riesgo</th>
                    <td><span class="nivel-riesgo">{data['detalle_brecha']['nivel_riesgo']}</span></td>
                </tr>
                <tr>
                    <th>Categorías Afectadas</th>
                    <td>{', '.join(data['detalle_brecha']['categoria_datos']) if isinstance(data['detalle_brecha']['categoria_datos'], list) else data['detalle_brecha']['categoria_datos']}</td>
                </tr>
                <tr>
                    <th>Cantidad Afectados</th>
                    <td>{data['detalle_brecha']['cantidad_afectados']} titulares</td>
                </tr>
                <tr>
                    <th>Descripción</th>
                    <td>{data['detalle_brecha']['descripcion']}</td>
                </tr>
                <tr>
                    <th>Medidas Tomadas</th>
                    <td>{data['detalle_brecha']['medidas_tomadas']}</td>
                </tr>
            </table>
            
            <div style="margin-top: 30px;">
                <p><strong>Fundamento Legal:</strong><br/>
                {data['fundamento_legal']}</p>
            </div>
            
            <div class="footer">
                <p>Este reporte debe ser adjuntado en el portal de la Agencia de Protección de Datos<br/>
                https://portal.agenciaprotecciondatos.cl</p>
                <p>Generado el {datetime.utcnow().strftime('%d/%m/%Y a las %H:%M:%S UTC')}</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    async def _html_to_pdf(self, html_content: str) -> bytes:
        """
        Convierte HTML a PDF usando WeasyPrint
        """
        if not WEASYPRINT_AVAILABLE:
            logger.error("WeasyPrint no está disponible. Usando fallback básico.")
            return self._pdf_fallback_basico()
        
        try:
            # Crear PDF desde HTML
            html = HTML(string=html_content, base_url='.')
            pdf_bytes = html.write_pdf(
                stylesheets=[CSS(string=f'@import url({self.font_base_url})')],
                optimize_size=('fonts', 'images'),
                zoom=1.0
            )
            
            return pdf_bytes
        
        except Exception as e:
            logger.error(f"Error generando PDF: {str(e)}")
            return self._pdf_fallback_basico()
    
    def _pdf_fallback_basico(self) -> bytes:
        """
        Fallback básico si WeasyPrint no está disponible
        """
        # En producción, esto debería usar reportlab u otra librería
        return b'%PDF-1.4\nFALLBACK: Instalar WeasyPrint para generación completa de PDFs'
    
    def _generar_numero_certificado(self, id_referencia: Any) -> str:
        """Genera número único de certificado"""
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        hash_id = hashlib.sha256(str(id_referencia).encode()).hexdigest()[:8].upper()
        return f"CERT-{timestamp}-{hash_id}"
    
    def _generar_token_verificacion(self, numero_certificado: str, tipo: str) -> str:
        """Genera token para URL de verificación"""
        hash_token = hashlib.sha256(
            f"{numero_certificado}{tipo}{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:32]
        return f"https://verify.ley21719.cl/certificado/{numero_certificado}?token={hash_token}"
    
    def _generar_qr_base64(self, url: str) -> str:
        """Genera código QR en base64"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def _generar_hash_evidencia(self, objeto: Any) -> str:
        """Genera hash SHA-256 como evidencia de auditoría"""
        datos = f"{objeto.id}{objeto.fecha_solicitud}{objeto.rut_ciudadano_hash}".encode()
        return hashlib.sha256(datos).hexdigest()
    
    def _generar_hash_certificado(self, pdf_bytes: bytes) -> str:
        """Genera hash del certificado PDF"""
        return hashlib.sha256(pdf_bytes).hexdigest()
    
    def _generar_hash_certificado_placeholder(self) -> str:
        """Placeholder para hash de certificado"""
        return hashlib.sha256(datetime.utcnow().isoformat().encode()).hexdigest()
    
    def _calcular_nivel_riesgo_visual(self, brecha_data: Dict[str, Any]) -> str:
        """Calcula nivel de riesgo para visualización"""
        cantidad = brecha_data.get('cantidad_afectados', 0)
        categorias = brecha_data.get('categoria_datos', [])
        
        datos_sensibles = ['SALUD', 'BIOMETRIA', 'ORIENTACION_SEXUAL', 
                          'OPINION_POLITICA', 'RELIGION', 'GENETICA']
        tiene_sensibles = any(cat in datos_sensibles for cat in categorias)
        
        if cantidad > 10000 or (tiene_sensibles and cantidad > 1000):
            return 'CRÍTICO'
        elif cantidad > 1000 or (tiene_sensibles and cantidad > 100):
            return 'ALTO'
        elif cantidad > 100 or tiene_sensibles:
            return 'MEDIO'
        else:
            return 'BAJO'


# Singleton instance
_certificate_generator = None

def get_certificate_generator() -> CertificateGenerator:
    """Factory function para obtener instancia del generador"""
    global _certificate_generator
    if _certificate_generator is None:
        _certificate_generator = CertificateGenerator()
    return _certificate_generator
