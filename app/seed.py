import uuid
import datetime
from sqlalchemy.orm import Session
from app.database import engine, SessionLocal, Base
from app.models.models import (
    Usuario, Organizacion, OrganizacionApiKey, AccesoOrganizacion, 
    EstadoPermiso, TipoArco, EstadoArco, SolicitudArco, 
    TipoAcceso, LogAccesoDatos
)
import hashlib

# Start DB Session
db: Session = SessionLocal()

# Asegurarse de que las tablas estén creadas
Base.metadata.create_all(bind=engine)

def hash_rut(rut: str) -> str:
    return hashlib.sha256(rut.encode()).hexdigest()

def encriptar_rut_mock(rut: str) -> str:
    # Esto es solo un mock para la encriptación
    return f"ENC_{rut}_ENC"

def seed():
    try:
        # Limpiar tablas previas (opcional, pero ayuda a que sea idempotente)
        db.query(LogAccesoDatos).delete()
        db.query(SolicitudArco).delete()
        db.query(AccesoOrganizacion).delete()
        db.query(OrganizacionApiKey).delete()
        db.query(Organizacion).delete()
        db.query(Usuario).delete()
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error limpiando DB (tablas quizas no existen aun): {e}")

    print("Insertando datos de prueba...")

    # Crear Usuario Ciudadano
    rut_ciudadano = "12345678-9"
    usuario = Usuario(
        id=uuid.uuid4(),
        rut_hash=hash_rut(rut_ciudadano),
        rut_encriptado=encriptar_rut_mock(rut_ciudadano),
        nombre_completo="Juan Pérez Ciudadano",
        email="juan.perez@example.com",
        telefono="+56912345678",
        fecha_nacimiento=datetime.datetime(1990, 1, 1)
    )
    db.add(usuario)

    # Crear Organización
    rut_org = "76543210-K"
    organizacion = Organizacion(
        id=uuid.uuid4(),
        rut=rut_org,
        razon_social="Empresa de Pruebas SPA",
        email_dpo="dpo@empresa.cl",
        modelo_prevencion_certificado=True
    )
    db.add(organizacion)

    db.commit()

    # Refrescar para obtener IDs
    db.refresh(usuario)
    db.refresh(organizacion)

    # Crear Acceso Organización
    acceso = AccesoOrganizacion(
        id=uuid.uuid4(),
        usuario_id=usuario.id,
        organizacion_id=organizacion.id,
        categoria_dato="DATOS_FINANCIEROS",
        finalidad="Evaluación crediticia para apertura de cuenta",
        estado=EstadoPermiso.ACTIVO,
        receipt_hash=hash_rut("receipt_123"),
        fecha_otorgamiento=datetime.datetime.now(datetime.timezone.utc),
        fecha_expiracion=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)
    )
    db.add(acceso)

    # Crear Solicitud ARCO
    solicitud = SolicitudArco(
        id=uuid.uuid4(),
        organizacion_id=organizacion.id,
        rut_ciudadano_hash=hash_rut(rut_ciudadano),
        tipo=TipoArco.ACCESO,
        estado=EstadoArco.EN_PROCESO,
        token_evidencia_identidad=hash_rut("token_evidencia"),
        fecha_limite_respuesta=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=10)
    )
    db.add(solicitud)

    # Crear Log de Acceso
    log = LogAccesoDatos(
        id=uuid.uuid4(),
        usuario_id=usuario.id,
        organizacion_id=organizacion.id,
        tipo_acceso=TipoAcceso.LECTURA,
        categoria_dato_consultado="DATOS_FINANCIEROS",
        justificacion_legal="Consentimiento del titular",
        ip_origen="192.168.1.100",
        fecha_acceso=datetime.datetime.now(datetime.timezone.utc)
    )
    db.add(log)

    db.commit()
    print("Datos de prueba insertados exitosamente.")
    print(f"Usuario Creado: {usuario.nombre_completo} (Email: {usuario.email}, RUT: {rut_ciudadano})")
    print(f"Organización Creada: {organizacion.razon_social} (Email: {organizacion.email_dpo}, RUT: {rut_org})")

if __name__ == "__main__":
    seed()
