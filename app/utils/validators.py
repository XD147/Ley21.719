from app.utils.security import hash_rut_sha256, encrypt_rut_aes256, validate_rut, normalize_rut
from datetime import date


def validate_age(fecha_nacimiento: date, min_age: int = 16) -> bool:
    """
    Valida que la persona tenga la edad mínima requerida (por defecto 16 años)
    Según Ley 21.719, menores de 16 requieren tutor
    """
    today = date.today()
    age = today.year - fecha_nacimiento.year - ((today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
    return age >= min_age


def calculate_age(fecha_nacimiento: date) -> int:
    """Calcula la edad actual de una persona"""
    today = date.today()
    age = today.year - fecha_nacimiento.year - ((today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
    return age


def validate_user_data(rut: str, fecha_nacimiento: date, email: str) -> dict:
    """
    Valida los datos básicos de un usuario según requisitos Ley 21.719
    Retorna dict con validaciones y errores
    """
    errors = []
    warnings = []
    
    # Validar RUT
    if not validate_rut(rut):
        errors.append("RUT inválido")
    
    # Validar edad
    age = calculate_age(fecha_nacimiento)
    if age < 16:
        warnings.append("Menor de 16 años: se requiere tutorId")
    elif age < 18:
        warnings.append("Menor de 18 años: consentimiento puede requerir validación adicional")
    
    # Validar email (básico)
    if not email or '@' not in email:
        errors.append("Email inválido")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "age": age,
        "requires_tutor": age < 16
    }
