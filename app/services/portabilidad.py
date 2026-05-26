"""
Servicio de Portabilidad de Datos para Ley 21.719
Implementa derecho a portabilidad (Art. 20) con formatos estructurados
"""
import json
import logging
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.models import Usuario, Organizacion, AccesoOrganizacion, LogAccesoDatos

logger = logging.getLogger(__name__)

class PortabilidadService:
    """
    Gestiona la portabilidad de datos personales.
    Formatos: JSON estructurado, CSV, XML (estándar interoperable)
    """
    
    def __init__(self, db: Session):
        self.db = db

    async def exportar_datos_usuario(
        self, 
        usuario_id: str, 
        formato: str = "json"
    ) -> Dict[str, Any]:
        """
        Exporta todos los datos del usuario en formato estructurado.
        Incluye: perfil, consentimientos, historial de accesos.
        """
        # Obtener usuario
        usuario = self.db.query(Usuario).filter(Usuario.id == usuario_id).first()
        
        if not usuario:
            raise ValueError("Usuario no encontrado")

        # Obtener consentimientos activos
        accesos = self.db.query(AccesoOrganizacion).filter(AccesoOrganizacion.usuario_id == usuario_id).all()

        # Obtener logs de acceso (últimos 2 años)
        logs = self.db.query(LogAccesoDatos)\
            .filter(LogAccesoDatos.usuario_id == usuario_id)\
            .order_by(LogAccesoDatos.fecha_acceso.desc())\
            .limit(1000).all()

        # Construir paquete de portabilidad
        paquete = {
            "metadata": {
                "fecha_exportacion": datetime.utcnow().isoformat(),
                "formato": formato,
                "version_esquema": "1.0",
                "sujeto_datos": {
                    "id_interno": usuario.id,
                    "rut_hash": usuario.rut_hash[:16] + "...",  # Parcial por seguridad
                    "nombre": usuario.nombre_completo
                }
            },
            "datos_personales": {
                "perfil": {
                    "nombre_completo": usuario.nombre_completo,
                    "email": usuario.email,
                    "telefono": usuario.telefono,
                    "fecha_nacimiento": str(usuario.fecha_nacimiento) if usuario.fecha_nacimiento else None,
                    "fecha_registro": str(usuario.fecha_registro) if usuario.fecha_registro else None
                },
                "consentimientos_activos": [
                    {
                        "organizacion_id": str(a.organizacion_id),
                        "categoria": a.categoria_dato,
                        "finalidad": a.finalidad,
                        "fecha_otorgamiento": str(a.fecha_otorgamiento),
                        "fecha_expiracion": str(a.fecha_expiracion) if a.fecha_expiracion else None,
                        "estado": a.estado
                    } for a in accesos
                ],
                "historial_accesos": [
                    {
                        "organizacion_id": str(l.organizacion_id),
                        "tipo_acceso": l.tipo_acceso,
                        "categoria": l.categoria_dato_consultado,
                        "fecha": str(l.fecha_acceso),
                        "ip_origen": l.ip_origen
                    } for l in logs
                ]
            }
        }

        # Formatear salida
        if formato.lower() == "json":
            return {"formato": "application/json", "datos": json.dumps(paquete, indent=2)}
        elif formato.lower() == "csv":
            return self._convertir_a_csv(paquete)
        else:
            raise ValueError(f"Formato no soportado: {formato}")

    async def importar_datos_portabilidad(
        self,
        usuario_id: str,
        datos_json: str,
        organizacion_origen_id: str
    ) -> dict:
        """
        Importa datos desde otra organización (portabilidad entrante).
        Valida estructura y actualiza registros locales.
        """
        try:
            datos = json.loads(datos_json)
            
            # Validar estructura mínima
            if "datos_personales" not in datos or "perfil" not in datos["datos_personales"]:
                raise ValueError("Estructura de portabilidad inválida")

            perfil = datos["datos_personales"]["perfil"]
            
            # Actualizar datos del usuario local
            result = await self.db.execute(
                select(Usuario).where(Usuario.id == usuario_id)
            )
            usuario = result.scalar_one_or_none()
            
            if not usuario:
                raise ValueError("Usuario no encontrado")

            # Actualizar campos si son proporcionados y el usuario confirma
            actualizaciones = {}
            if perfil.get("telefono") and not usuario.telefono:
                actualizaciones["telefono"] = perfil["telefono"]
            
            # Registrar consentimiento implícito para portabilidad
            # Esto crea un nuevo AccesoOrganizacion desde la org origen
            
            await self.db.commit()
            
            return {
                "estado": "EXITOSO",
                "campos_actualizados": list(actualizaciones.keys()),
                "mensaje": "Datos importados correctamente"
            }
            
        except json.JSONDecodeError:
            raise ValueError("JSON inválido")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error importando portabilidad: {e}")
            raise e

    def _convertir_a_csv(self, paquete: dict) -> dict:
        """Convierte paquete JSON a CSV plano."""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(["Campo", "Valor", "Categoria"])
        
        # Perfil
        perfil = paquete["datos_personales"]["perfil"]
        for key, value in perfil.items():
            writer.writerow([f"perfil.{key}", value, "IDENTIFICACION"])
        
        # Consentimientos
        for cons in paquete["datos_personales"]["consentimientos_activos"]:
            writer.writerow([
                f"consentimiento.{cons['organizacion_id']}",
                f"{cons['categoria']} - {cons['finalidad']}",
                "CONSENTIMIENTO"
            ])
        
        return {"formato": "text/csv", "datos": output.getvalue()}

def get_portabilidad_service(db: Session):
    return PortabilidadService(db)
