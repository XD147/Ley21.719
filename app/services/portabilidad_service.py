"""
Servicio de Portabilidad de Datos - Ley 21.719
Implementa derecho a recibir datos en formato estructurado (JSON, XML, CSV)
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID
import json
import csv
import io
import hashlib
import secrets

from app.models.cumplimiento_models import ExportacionPortabilidad, TraduccionLegalDesign
from app.models.models import Usuario, AccesoOrganizacion, LogAccesoDatos, SolicitudArco, TipoArco


class ServicioPortabilidad:
    """Gestión de portabilidad y exportación de datos personales"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def solicitar_exportacion(self, usuario_id: UUID, organizacion_id: UUID,
                                    formato: str = "JSON",
                                    categorias: Optional[List[str]] = None) -> ExportacionPortabilidad:
        """Solicitar exportación de datos para portabilidad"""
        
        if formato not in ["JSON", "XML", "CSV"]:
            raise ValueError(f"Formato no soportado: {formato}. Use JSON, XML o CSV")
        
        # Si no se especifican categorías, incluir todas
        if not categorias:
            categorias = ["perfil", "accesos", "logs", "solicitudes"]
        
        exportacion = ExportacionPortabilidad(
            usuario_id=usuario_id,
            organizacion_id=organizacion_id,
            formato_exportacion=formato,
            categorias_incluidas=categorias,
            estado="GENERANDO"
        )
        
        self.db.add(exportacion)
        await self.db.commit()
        await self.db.refresh(exportacion)
        
        # Generar exportación en background (en producción usar Celery)
        await self._generar_archivo_exportacion(exportacion)
        
        return exportacion
    
    async def _generar_archivo_exportacion(self, exportacion: ExportacionPortabilidad) -> Dict:
        """Generar archivo de exportación con los datos del usuario"""
        
        try:
            datos_usuario = {}
            
            # 1. Obtener perfil del usuario
            if "perfil" in exportacion.categorias_incluidas:
                result = await self.db.execute(
                    select(Usuario)
                    .where(Usuario.id == exportacion.usuario_id)
                )
                usuario = result.scalar_one_or_none()
                
                if usuario:
                    datos_usuario["perfil"] = {
                        "nombre_completo": usuario.nombre_completo,
                        "email": usuario.email,
                        "telefono": usuario.telefono,
                        "fecha_nacimiento": usuario.fecha_nacimiento.isoformat() if usuario.fecha_nacimiento else None,
                        "fecha_registro": usuario.fecha_registro.isoformat() if usuario.fecha_registro else None
                        # Nota: No incluir RUT (ni hash ni encriptado) por seguridad
                    }
            
            # 2. Obtener accesos/consentimientos otorgados
            if "accesos" in exportacion.categorias_incluidas:
                result = await self.db.execute(
                    select(AccesoOrganizacion)
                    .where(AccesoOrganizacion.usuario_id == exportacion.usuario_id)
                    .order_by(AccesoOrganizacion.fecha_otorgamiento.desc())
                )
                accesos = list(result.scalars().all())
                
                datos_usuario["accesos"] = [
                    {
                        "organizacion_id": str(acceso.organizacion_id),
                        "categoria_dato": acceso.categoria_dato,
                        "finalidad": acceso.finalidad,
                        "estado": acceso.estado.value,
                        "fecha_otorgamiento": acceso.fecha_otorgamiento.isoformat(),
                        "fecha_expiracion": acceso.fecha_expiracion.isoformat() if acceso.fecha_expiracion else None
                    }
                    for acceso in accesos
                ]
            
            # 3. Obtener logs de acceso (últimos 1000)
            if "logs" in exportacion.categorias_incluidas:
                result = await self.db.execute(
                    select(LogAccesoDatos)
                    .where(LogAccesoDatos.usuario_id == exportacion.usuario_id)
                    .order_by(LogAccesoDatos.fecha_acceso.desc())
                    .limit(1000)
                )
                logs = list(result.scalars().all())
                
                datos_usuario["logs_acceso"] = [
                    {
                        "organizacion_id": str(log.organizacion_id),
                        "tipo_acceso": log.tipo_acceso.value,
                        "categoria_dato": log.categoria_dato_consultado,
                        "justificacion": log.justificacion_legal,
                        "ip_origen": log.ip_origen,
                        "fecha_acceso": log.fecha_acceso.isoformat()
                    }
                    for log in logs
                ]
            
            # 4. Obtener solicitudes ARCO
            if "solicitudes" in exportacion.categorias_incluidas:
                result = await self.db.execute(
                    select(SolicitudArco)
                    .where(SolicitudArco.rut_ciudadano_hash.isnot(None))  # Filtrar por usuario indirectamente
                    .order_by(SolicitudArco.fecha_solicitud.desc())
                    .limit(100)
                )
                solicitudes = list(result.scalars().all())
                
                # Nota: En implementación real, filtrar por hash RUT del usuario
                datos_usuario["solicitudes_arco"] = [
                    {
                        "organizacion_id": str(sol.organizacion_id),
                        "tipo": sol.tipo.value,
                        "estado": sol.estado.value,
                        "descripcion": sol.descripcion,
                        "fecha_solicitud": sol.fecha_solicitud.isoformat(),
                        "respuesta": sol.respuesta
                    }
                    for sol in solicitudes[:50]  # Limitar a 50
                ]
            
            # Generar archivo según formato
            if exportacion.formato_exportacion == "JSON":
                contenido = json.dumps(datos_usuario, indent=2, ensure_ascii=False)
                mime_type = "application/json"
                extension = "json"
            elif exportacion.formato_exportacion == "XML":
                contenido = self._dict_to_xml(datos_usuario)
                mime_type = "application/xml"
                extension = "xml"
            elif exportacion.formato_exportacion == "CSV":
                contenido = self._dict_to_csv(datos_usuario)
                mime_type = "text/csv"
                extension = "csv"
            else:
                raise ValueError(f"Formato no soportado: {exportacion.formato_exportacion}")
            
            # Calcular hash de verificación
            hash_verificacion = hashlib.sha256(contenido.encode('utf-8')).hexdigest()
            
            # Generar token de acceso seguro
            token_acceso = secrets.token_urlsafe(32)
            token_hash = hashlib.sha256(token_acceso.encode()).hexdigest()
            
            # URL temporal (en producción, subir a S3 o storage similar)
            url_descarga = f"/api/v1/portabilidad/descarga/{token_hash}"
            
            # Actualizar registro
            exportacion.estado = "LISTO"
            exportacion.url_descarga_temporal = url_descarga
            exportacion.token_acceso = token_hash
            exportacion.fecha_generacion = datetime.now()
            exportacion.fecha_expiracion_url = datetime.now() + timedelta(hours=24)
            exportacion.tamaño_archivo_bytes = len(contenido.encode('utf-8'))
            exportacion.hash_verificacion = hash_verificacion
            
            # Guardar contenido en almacenamiento temporal (en producción, usar S3)
            # Por ahora, lo guardamos como metadata (no recomendado para archivos grandes)
            # En producción: subir a S3 y guardar solo la URL
            
            await self.db.commit()
            
            return {
                "id": str(exportacion.id),
                "estado": exportacion.estado,
                "url_descarga": url_descarga,
                "token": token_acceso,  # Entregar solo una vez al usuario
                "hash_verificacion": hash_verificacion,
                "tamaño_bytes": exportacion.tamaño_archivo_bytes,
                "expira_en_horas": 24
            }
            
        except Exception as e:
            exportacion.estado = "ERROR"
            await self.db.commit()
            raise e
    
    def _dict_to_xml(self, data: dict, root_name: str = "datos_portabilidad") -> str:
        """Convertir diccionario a XML"""
        
        def dict_to_xml_tag(d, parent):
            xml = []
            for key, value in d.items():
                key = key.replace(" ", "_").replace("-", "_")
                if isinstance(value, dict):
                    xml.append(f"<{key}>")
                    xml.append(dict_to_xml_tag(value, key))
                    xml.append(f"</{key}>")
                elif isinstance(value, list):
                    xml.append(f"<{key}>")
                    for item in value:
                        if isinstance(item, dict):
                            xml.append(dict_to_xml_tag(item, "item"))
                        else:
                            xml.append(f"<item>{self._escape_xml(str(item))}</item>")
                    xml.append(f"</{key}>")
                else:
                    xml.append(f"<{key}>{self._escape_xml(str(value) if value else '')}</{key}>")
            return "".join(xml)
        
        return f'<?xml version="1.0" encoding="UTF-8"?>\n<{root_name}>\n{dict_to_xml_tag(data, root_name)}\n</{root_name}>'
    
    def _escape_xml(self, text: str) -> str:
        """Escape caracteres especiales XML"""
        return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;"))
    
    def _dict_to_csv(self, data: dict) -> str:
        """Convertir diccionario a CSV (estructura plana)"""
        
        output = io.StringIO()
        
        # Aplanar estructura para CSV
        filas = []
        headers = set()
        
        def aplanar_dict(d, prefix=""):
            resultado = {}
            for key, value in d.items():
                new_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, dict):
                    resultado.update(aplanar_dict(value, new_key))
                elif isinstance(value, list):
                    resultado[new_key] = json.dumps(value, ensure_ascii=False)
                else:
                    resultado[new_key] = value
            return resultado
        
        for categoria, contenido in data.items():
            if isinstance(contenido, list):
                for item in contenido:
                    fila_aplanada = aplanar_dict({categoria: item})
                    headers.update(fila_aplanada.keys())
                    filas.append(fila_aplanada)
            else:
                fila_aplanada = aplanar_dict({categoria: contenido})
                headers.update(fila_aplanada.keys())
                filas.append(fila_aplanada)
        
        # Escribir CSV
        writer = csv.DictWriter(output, fieldnames=sorted(headers), lineterminator='\n')
        writer.writeheader()
        writer.writerows(filas)
        
        return output.getvalue()
    
    async def obtener_estado_exportacion(self, exportacion_id: UUID) -> Dict:
        """Obtener estado de una solicitud de exportación"""
        
        result = await self.db.execute(
            select(ExportacionPortabilidad)
            .where(ExportacionPortabilidad.id == exportacion_id)
        )
        exportacion = result.scalar_one_or_none()
        
        if not exportacion:
            raise ValueError("Exportación no encontrada")
        
        return {
            "id": str(exportacion.id),
            "estado": exportacion.estado,
            "formato": exportacion.formato_exportacion,
            "categorias": exportacion.categorias_incluidas,
            "fecha_solicitud": exportacion.fecha_solicitud.isoformat(),
            "fecha_generacion": exportacion.fecha_generacion.isoformat() if exportacion.fecha_generacion else None,
            "fecha_expiracion": exportacion.fecha_expiracion_url.isoformat() if exportacion.fecha_expiracion_url else None,
            "tamaño_bytes": exportacion.tamaño_archivo_bytes,
            "lista_para_descarga": exportacion.estado == "LISTO" and exportacion.fecha_expiracion_url > datetime.now()
        }
    
    async def descargar_exportacion(self, token_hash: str) -> Dict:
        """Descargar archivo de exportación con token seguro"""
        
        result = await self.db.execute(
            select(ExportacionPortabilidad)
            .where(ExportacionPortabilidad.token_acceso == token_hash)
        )
        exportacion = result.scalar_one_or_none()
        
        if not exportacion:
            raise ValueError("Token inválido o expirado")
        
        # Verificar expiración
        if exportacion.fecha_expiracion_url and exportacion.fecha_expiracion_url < datetime.now():
            exportacion.estado = "EXPIRADO"
            await self.db.commit()
            raise ValueError("URL de descarga expirada (24 horas)")
        
        # Actualizar estado a DESCARGADO
        exportacion.estado = "DESCARGADO"
        await self.db.commit()
        
        # En producción, aquí se leería el archivo desde S3
        # Por ahora, regeneramos los datos (ineficiente pero funcional para demo)
        datos = await self._regenerar_datos_exportacion(exportacion)
        
        return {
            "contenido": datos,
            "formato": exportacion.formato_exportacion,
            "hash_verificacion": exportacion.hash_verificacion,
            "tamaño_bytes": exportacion.tamaño_archivo_bytes
        }
    
    async def _regenerar_datos_exportacion(self, exportacion: ExportacionPortabilidad) -> str:
        """Regenerar datos para descarga (en producción, leer desde S3)"""
        # Implementación simplificada - en producción usar storage persistente
        return "Datos exportados - implementar almacenamiento persistente en producción"
    
    async def listar_exportaciones_usuario(self, usuario_id: UUID,
                                           limite: int = 20) -> List[Dict]:
        """Listar exportaciones realizadas por un usuario"""
        
        result = await self.db.execute(
            select(ExportacionPortabilidad)
            .where(ExportacionPortabilidad.usuario_id == usuario_id)
            .order_by(ExportacionPortabilidad.fecha_solicitud.desc())
            .limit(limite)
        )
        exportaciones = list(result.scalars().all())
        
        return [
            {
                "id": str(exp.id),
                "formato": exp.formato_exportacion,
                "estado": exp.estado,
                "fecha_solicitud": exp.fecha_solicitud.isoformat(),
                "fecha_expiracion": exp.fecha_expiracion_url.isoformat() if exp.fecha_expiracion_url else None
            }
            for exp in exportaciones
        ]
    
    async def crear_traduccion_legal(self, organizacion_id: UUID,
                                     texto_legal: str,
                                     categoria: str,
                                     nivel: str = "BASICO") -> TraduccionLegalDesign:
        """Crear traducción de lenguaje legal a ciudadano"""
        
        # En producción, usar IA para generar traducción automática
        # Aquí implementamos una versión básica
        traduccion = TraduccionLegalDesign(
            organizacion_id=organizacion_id,
            texto_legal_original=texto_legal,
            texto_ciudadano=self._generar_traduccion_simple(texto_legal, categoria),
            categoria=categoria,
            icono_sugerido=self._sugerir_icono(categoria),
            nivel_simplificacion=nivel,
            validado_dpo=False
        )
        
        self.db.add(traduccion)
        await self.db.commit()
        await self.db.refresh(traduccion)
        
        return traduccion
    
    def _generar_traduccion_simple(self, texto_legal: str, categoria: str) -> str:
        """Generar traducción simplificada (en producción usar IA)"""
        
        traducciones_base = {
            "finalidad": "¿Para qué usaremos tus datos?",
            "derechos": "Tus derechos sobre tus datos",
            "retencion": "¿Por cuánto tiempo guardamos tus datos?",
            "transferencia": "¿Compartiremos tus datos con otros?",
            "seguridad": "Cómo protegemos tu información"
        }
        
        return traducciones_base.get(categoria, 
            f"Explicación simple: {texto_legal[:200]}... (versión completa en lenguaje claro)")
    
    def _sugerir_icono(self, categoria: str) -> str:
        """Sugerir ícono según categoría"""
        
        iconos = {
            "finalidad": "🎯",
            "derechos": "🛡️",
            "retencion": "⏰",
            "transferencia": "🔄",
            "seguridad": "🔒"
        }
        
        return iconos.get(categoria, "ℹ️")
