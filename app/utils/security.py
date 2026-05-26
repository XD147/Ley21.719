"""
Utilidades para encriptación y hashing - Ley 21.719
Implementa SHA-256 para hashing y AES-256 para encriptación
"""

import hashlib
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from app.config import settings


def hash_rut_sha256(rut: str) -> str:
    """
    Genera hash SHA-256 del RUT para indexación y búsqueda
    El RUT debe normalizarse antes (sin puntos, con guión, mayúsculas)
    """
    rut_normalized = rut.strip().upper()
    hash_object = hashlib.sha256(rut_normalized.encode('utf-8'))
    return hash_object.hexdigest()


def generate_encryption_key(key_str: str) -> bytes:
    """
    Deriva una clave de encriptación válida para Fernet desde una string
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'ley21719_salt_fixed',  # En producción usar salt único por entorno
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(key_str.encode()))
    return key


def encrypt_rut_aes256(rut: str, encryption_key: str = None) -> str:
    """
    Encripta el RUT usando AES-256 para almacenamiento seguro
    Retorna string en base64
    """
    if encryption_key is None:
        encryption_key = settings.encryption_key
    
    fernet = Fernet(generate_encryption_key(encryption_key))
    encrypted = fernet.encrypt(rut.encode('utf-8'))
    return base64.urlsafe_b64encode(encrypted).decode('utf-8')


def decrypt_rut_aes256(encrypted_rut: str, encryption_key: str = None) -> str:
    """
    Desencripta el RUT encriptado con AES-256
    """
    if encryption_key is None:
        encryption_key = settings.encryption_key
    
    fernet = Fernet(generate_encryption_key(encryption_key))
    encrypted_bytes = base64.urlsafe_b64decode(encrypted_rut.encode('utf-8'))
    decrypted = fernet.decrypt(encrypted_bytes)
    return decrypted.decode('utf-8')


def hash_api_key(key: str) -> str:
    """
    Genera hash SHA-256 de API Key para almacenamiento seguro
    """
    hash_object = hashlib.sha256(key.encode('utf-8'))
    return hash_object.hexdigest()


def generate_receipt_hash(data: dict, signature: str) -> str:
    """
    Genera hash del receipt (comprobante) de consentimiento
    Combina los datos del pacto con la firma digital
    """
    import json
    data_str = json.dumps(data, sort_keys=True)
    combined = f"{data_str}|{signature}"
    hash_object = hashlib.sha256(combined.encode('utf-8'))
    return hash_object.hexdigest()


def normalize_rut(rut: str) -> str:
    """
    Normaliza el RUT al formato estándar chileno
    Ej: 12.345.678-9 -> 12345678-9
    """
    rut = rut.strip().upper().replace('.', '')
    if '-' not in rut:
        body = rut[:-1]
        dv = rut[-1]
        rut = f"{body}-{dv}"
    return rut


def validate_rut(rut: str) -> bool:
    """
    Valida que el RUT sea válido según algoritmo chileno
    """
    try:
        rut = normalize_rut(rut)
        body, dv = rut.split('-')
        
        # Calcular dígito verificador esperado
        reversed_body = list(map(int, reversed(body)))
        series = [2, 3, 4, 5, 6, 7]
        sum_val = 0
        
        for i, digit in enumerate(reversed_body):
            sum_val += digit * series[i % len(series)]
        
        remainder = sum_val % 11
        dv_calculated = 11 - remainder if remainder > 0 else 0
        
        # Manejar caso especial donde dv_calculated = 11 se convierte en 0
        if dv_calculated == 11:
            dv_calculated = 0
        
        expected_dv = 'K' if dv_calculated == 10 else str(dv_calculated)
        
        return dv.upper() == expected_dv
    except Exception:
        return False
