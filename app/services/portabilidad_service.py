"""
Servicio de Portabilidad de Datos (Art. 18 Ley 21.719)
Permite al ciudadano exportar todos sus datos en formatos estándar.
"""
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
import json
import csv
import io
from typing import List, Dict, Any
from app.models.models import Usuario, AccesoOrganizacion, LogAccesoDatos, SolicitudArco
from app.services.kms_factory import decrypt_data


class PortabilidadService:
    
    @staticmethod
    def obtener_datos_usuario_completos(db: Session, usuario_id: str) -> Dict[str, Any]:
        """
        Obtiene TODOS los datos del usuario para portabilidad.
        Incluye: información personal, consentimientos, logs de acceso, solicitudes ARCO.
        """
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        if not usuario:
            raise ValueError(f"Usuario {usuario_id} no encontrado")
        
        # Desencriptar RUT para exportación (solo el titular puede verlo)
        rut_desencriptado = decrypt_data(usuario.rut_encriptado)
        
        # Obtener todos los accesos/consentimientos
        accesos = db.query(AccesoOrganizacion).filter(
            AccesoOrganizacion.usuario_id == usuario_id
        ).all()
        
        # Obtener logs de acceso (quién ha visto sus datos)
        logs = db.query(LogAccesoDatos).filter(
            LogAccesoDatos.usuario_id == usuario_id
        ).order_by(LogAccesoDatos.fecha_acceso.desc()).limit(100).all()
        
        # Obtener solicitudes ARCO
        solicitudes_arco = db.query(SolicitudArco).filter(
            SolicitudArco.rut_ciudadano_hash == usuario.rut_hash
        ).all()
        
        # Estructurar datos para exportación
        datos_exportacion = {
            "metadata": {
                "fecha_exportacion": datetime.utcnow().isoformat(),
                "version_formato": "1.0",
                "ley_aplicable": "Ley 21.719 Chile",
                "titular": {
                    "id": str(usuario.id),
                    "rut": rut_desencriptado,
                    "nombre_completo": usuario.nombre_completo,
                    "email": usuario.email,
                    "telefono": usuario.telefono,
                    "fecha_nacimiento": usuario.fecha_nacimiento.isoformat() if usuario.fecha_nacimiento else None,
                    "fecha_registro": usuario.fecha_registro.isoformat() if usuario.fecha_registro else None
                }
            },
            "consentimientos": [
                {
                    "id": str(acceso.id),
                    "organizacion_id": str(acceso.organizacion_id),
                    "categoria_dato": acceso.categoria_dato,
                    "finalidad": acceso.finalidad,
                    "estado": acceso.estado,
                    "fecha_otorgamiento": acceso.fecha_otorgamiento.isoformat() if acceso.fecha_otorgamiento else None,
                    "fecha_expiracion": acceso.fecha_expiracion.isoformat() if acceso.fecha_expiracion else None,
                    "receipt_hash": acceso.receipt_hash
                }
                for acceso in accesos
            ],
            "historial_accesos": [
                {
                    "id": str(log.id),
                    "organizacion_id": str(log.organizacion_id),
                    "tipo_acceso": log.tipo_acceso,
                    "categoria_dato_consultado": log.categoria_dato_consultado,
                    "justificacion_legal": log.justificacion_legal,
                    "ip_origen": log.ip_origen,
                    "fecha_acceso": log.fecha_acceso.isoformat() if log.fecha_acceso else None
                }
                for log in logs
            ],
            "solicitudes_arco": [
                {
                    "id": str(solicitud.id),
                    "organizacion_id": str(solicitud.organizacion_id),
                    "tipo": solicitud.tipo.value,
                    "estado": solicitud.estado.value,
                    "fecha_solicitud": solicitud.fecha_solicitud.isoformat() if solicitud.fecha_solicitud else None,
                    "fecha_limite_respuesta": solicitud.fecha_limite_respuesta.isoformat() if solicitud.fecha_limite_respuesta else None,
                    "prorrogado": solicitud.prorrogado
                }
                for solicitud in solicitudes_arco
            ]
        }
        
        return datos_exportacion
    
    @staticmethod
    def exportar_json(db: Session, usuario_id: str) -> str:
        """Exporta datos en formato JSON estructurado"""
        datos = PortabilidadService.obtener_datos_usuario_completos(db, usuario_id)
        return json.dumps(datos, indent=2, ensure_ascii=False)
    
    @staticmethod
    def exportar_csv(db: Session, usuario_id: str) -> Dict[str, str]:
        """
        Exporta datos en múltiples archivos CSV por categoría.
        Retorna diccionario con nombre_archivo: contenido_csv
        """
        datos = PortabilidadService.obtener_datos_usuario_completos(db, usuario_id)
        archivos_csv = {}
        
        # CSV de información personal
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['campo', 'valor'])
        titular = datos['metadata']['titular']
        for key, value in titular.items():
            writer.writerow([key, value])
        archivos_csv['informacion_personal.csv'] = output.getvalue()
        
        # CSV de consentimientos
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['id', 'organizacion_id', 'categoria_dato', 'finalidad', 'estado', 'fecha_otorgamiento', 'fecha_expiracion'])
        for consentimiento in datos['consentimientos']:
            writer.writerow([
                consentimiento['id'],
                consentimiento['organizacion_id'],
                consentimiento['categoria_dato'],
                consentimiento['finalidad'],
                consentimiento['estado'],
                consentimiento['fecha_otorgamiento'],
                consentimiento['fecha_expiracion']
            ])
        archivos_csv['consentimientos.csv'] = output.getvalue()
        
        # CSV de historial de accesos
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['id', 'organizacion_id', 'tipo_acceso', 'categoria_dato', 'justificacion', 'ip_origen', 'fecha_acceso'])
        for acceso in datos['historial_accesos']:
            writer.writerow([
                acceso['id'],
                acceso['organizacion_id'],
                acceso['tipo_acceso'],
                acceso['categoria_dato_consultado'],
                acceso['justificacion_legal'],
                acceso['ip_origen'],
                acceso['fecha_acceso']
            ])
        archivos_csv['historial_accesos.csv'] = output.getvalue()
        
        # CSV de solicitudes ARCO
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['id', 'organizacion_id', 'tipo', 'estado', 'fecha_solicitud', 'fecha_limite', 'prorrogado'])
        for solicitud in datos['solicitudes_arco']:
            writer.writerow([
                solicitud['id'],
                solicitud['organizacion_id'],
                solicitud['tipo'],
                solicitud['estado'],
                solicitud['fecha_solicitud'],
                solicitud['fecha_limite_respuesta'],
                solicitud['prorrogado']
            ])
        archivos_csv['solicitudes_arco.csv'] = output.getvalue()
        
        return archivos_csv
    
    @staticmethod
    def exportar_xml(db: Session, usuario_id: str) -> str:
        """Exporta datos en formato XML"""
        datos = PortabilidadService.obtener_datos_usuario_completos(db, usuario_id)
        
        xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml_lines.append('<portabilidad_datos ley="21.719" pais="Chile">')
        
        # Metadata
        xml_lines.append('  <metadata>')
        xml_lines.append(f'    <fecha_exportacion>{datos["metadata"]["fecha_exportacion"]}</fecha_exportacion>')
        xml_lines.append(f'    <version_formato>{datos["metadata"]["version_formato"]}</version_formato>')
        
        # Titular
        xml_lines.append('    <titular>')
        for key, value in datos['metadata']['titular'].items():
            if value is not None:
                xml_lines.append(f'      <{key}>{value}</{key}>')
        xml_lines.append('    </titular>')
        xml_lines.append('  </metadata>')
        
        # Consentimientos
        xml_lines.append('  <consentimientos>')
        for cons in datos['consentimientos']:
            xml_lines.append('    <consentimiento>')
            for key, value in cons.items():
                if value is not None:
                    xml_lines.append(f'      <{key}>{value}</{key}>')
            xml_lines.append('    </consentimiento>')
        xml_lines.append('  </consentimientos>')
        
        # Historial accesos
        xml_lines.append('  <historial_accesos>')
        for acceso in datos['historial_accesos']:
            xml_lines.append('    <acceso>')
            for key, value in acceso.items():
                if value is not None:
                    xml_lines.append(f'      <{key}>{value}</{key}>')
            xml_lines.append('    </acceso>')
        xml_lines.append('  </historial_accesos>')
        
        # Solicitudes ARCO
        xml_lines.append('  <solicitudes_arco>')
        for sol in datos['solicitudes_arco']:
            xml_lines.append('    <solicitud>')
            for key, value in sol.items():
                if value is not None:
                    xml_lines.append(f'      <{key}>{value}</{key}>')
            xml_lines.append('    </solicitud>')
        xml_lines.append('  </solicitudes_arco>')
        
        xml_lines.append('</portabilidad_datos>')
        
        return '\n'.join(xml_lines)
    
    @staticmethod
    def generar_token_portabilidad(db: Session, usuario_id: str, organizacion_destino: str = None) -> str:
        """
        Genera token seguro de un solo uso para transferencia directa a competidor.
        El token permite descargar los datos una sola vez dentro de las próximas 24 horas.
        """
        import hashlib
        import secrets
        
        # Generar token único
        token_secreto = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token_secreto.encode()).hexdigest()
        
        # En producción, guardar este token en BD con:
        # - usuario_id
        # - organizacion_destino (opcional, para restringir)
        # - fecha_expiracion (24 horas)
        # - usado (boolean)
        
        # Por ahora retornamos el token directamente
        # En implementación real, se debería persistir en tabla TokenPortabilidad
        return token_secreto
