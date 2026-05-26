"""
Factory de Gestión de Claves (KMS/HSM)
Soporta múltiples proveedores para entornos de producción regulados.
- Local: Desarrollo/testing con archivo .env
- AWS KMS: Producción en AWS
- Azure Key Vault: Producción en Azure
- HSM Físico: Banca/Salud con PKCS#11
"""
from abc import ABC, abstractmethod
from typing import Optional
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers.aes import AESGCM
import logging

logger = logging.getLogger(__name__)


class KMSProvider(ABC):
    """Interfaz abstracta para proveedores KMS"""
    
    @abstractmethod
    def encrypt(self, plaintext: str) -> str:
        pass
    
    @abstractmethod
    def decrypt(self, ciphertext: str) -> str:
        pass
    
    @abstractmethod
    def generate_key(self) -> str:
        pass


class LocalKMS(KMSProvider):
    """
    Implementación local para desarrollo/testing.
    Usa la clave del archivo .env (NO USAR EN PRODUCCIÓN).
    """
    
    def __init__(self, encryption_key: Optional[str] = None):
        self.key = encryption_key or os.getenv("ENCRYPTION_KEY")
        if not self.key:
            # Generar clave temporal si no existe (solo desarrollo)
            self.key = Fernet.generate_key().decode()
            logger.warning("Clave de encriptación generada temporalmente. Configurar ENCRYPTION_KEY en .env")
        
        self.aes_key = self._derive_aes_key(self.key)
    
    def _derive_aes_key(self, key_str: str) -> bytes:
        """Deriva una clave AES-256 desde la clave maestra"""
        import hashlib
        return hashlib.sha256(key_str.encode()).digest()
    
    def encrypt(self, plaintext: str) -> str:
        aesgcm = AESGCM(self.aes_key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
        combined = nonce + ciphertext
        return base64.b64encode(combined).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        aesgcm = AESGCM(self.aes_key)
        combined = base64.b64decode(ciphertext)
        nonce = combined[:12]
        actual_ciphertext = combined[12:]
        plaintext = aesgcm.decrypt(nonce, actual_ciphertext, None)
        return plaintext.decode()
    
    def generate_key(self) -> str:
        return Fernet.generate_key().decode()


class AWSKMS(KMSProvider):
    """
    Integración con AWS Key Management Service.
    Requiere: boto3 y credenciales AWS configuradas.
    """
    
    def __init__(self, key_id: str, region: str = 'us-east-1'):
        try:
            import boto3
            self.kms_client = boto3.client('kms', region_name=region)
            self.key_id = key_id
            logger.info(f"AWS KMS inicializado con key_id: {key_id}")
        except ImportError:
            raise ImportError("boto3 no instalado. Ejecutar: pip install boto3")
    
    def encrypt(self, plaintext: str) -> str:
        response = self.kms_client.encrypt(
            KeyId=self.key_id,
            Plaintext=plaintext.encode('utf-8')
        )
        return base64.b64encode(response['CiphertextBlob']).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        ciphertext_blob = base64.b64decode(ciphertext)
        response = self.kms_client.decrypt(CiphertextBlob=ciphertext_blob)
        return response['Plaintext'].decode('utf-8')
    
    def generate_key(self) -> str:
        response = self.kms_client.generate_data_key(
            KeyId=self.key_id,
            KeySpec='AES_256'
        )
        return base64.b64encode(response['Plaintext']).decode()


class AzureKeyVault(KMSProvider):
    """
    Integración con Azure Key Vault.
    Requiere: azure-keyvault-keys y autenticación configurada.
    """
    
    def __init__(self, vault_url: str, key_name: str):
        try:
            from azure.keyvault.keys import KeyClient
            from azure.identity import DefaultAzureCredential
            
            credential = DefaultAzureCredential()
            self.client = KeyClient(vault_url=vault_url, credential=credential)
            self.key_name = key_name
            logger.info(f"Azure Key Vault inicializado: {vault_url}/{key_name}")
        except ImportError:
            raise ImportError("azure-keyvault-keys no instalado. Ejecutar: pip install azure-keyvault-keys azure-identity")
    
    def encrypt(self, plaintext: str) -> str:
        from azure.keyvault.keys import KeyEncryptionAlgorithm
        
        key = self.client.get_key(self.key_name)
        encrypted = self.client.client.encrypt(
            key.id,
            plaintext.encode('utf-8'),
            algorithm=KeyEncryptionAlgorithm.rsa_oaep_256
        )
        return base64.b64encode(encrypted.result).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        from azure.keyvault.keys import KeyEncryptionAlgorithm
        
        key = self.client.get_key(self.key_name)
        ciphertext_blob = base64.b64decode(ciphertext)
        decrypted = self.client.client.decrypt(
            key.id,
            ciphertext_blob,
            algorithm=KeyEncryptionAlgorithm.rsa_oaep_256
        )
        return decrypted.result.decode('utf-8')
    
    def generate_key(self) -> str:
        # Azure KV no permite exportar claves simétricas directamente
        # Se genera una clave de datos localmente
        return Fernet.generate_key().decode()


class HSM_PKCS11(KMSProvider):
    """
    Integración con HSM físico vía PKCS#11.
    Para entornos de alta seguridad (Banca, Salud).
    Requiere: libpkcs11-wrapper y configuración del HSM.
    """
    
    def __init__(self, lib_path: str, slot: int, pin: str, key_label: str):
        try:
            # Nota: La implementación real depende del HSM específico
            # Este es un skeleton para demostración
            self.lib_path = lib_path
            self.slot = slot
            self.pin = pin
            self.key_label = key_label
            
            # En producción: inicializar conexión al HSM
            # import PyKCS11
            # self.pkcs11 = PyKCS11.PyKCS11Lib()
            # self.pkcs11.load(lib_path)
            # self.session = self._iniciar_session()
            
            logger.warning(f"HSM PKCS#11 configurado (simulado): {lib_path}, slot {slot}")
            logger.warning("Para producción, implementar conexión real al HSM")
            
            # Fallback a encriptación local para demo
            self._fallback = LocalKMS()
            
        except Exception as e:
            logger.error(f"Error inicializando HSM: {str(e)}")
            self._fallback = LocalKMS()
    
    def _iniciar_session(self):
        """Inicializa sesión con el HSM"""
        # Implementación específica del HSM
        pass
    
    def encrypt(self, plaintext: str) -> str:
        # En producción: usar HSM real
        # return self._hsm_encrypt(plaintext)
        return self._fallback.encrypt(plaintext)
    
    def decrypt(self, ciphertext: str) -> str:
        # En producción: usar HSM real
        # return self._hsm_decrypt(ciphertext)
        return self._fallback.decrypt(ciphertext)
    
    def generate_key(self) -> str:
        # En producción: generar clave en HSM
        return self._fallback.generate_key()


class KMSFactory:
    """
    Factory para crear instancias de KMS según configuración.
    Uso: kms = KMSFactory.create_provider()
    """
    
    @staticmethod
    def create_provider() -> KMSProvider:
        """
        Crea el proveedor KMS basado en variable de entorno KMS_PROVIDER.
        
        Variables requeridas según proveedor:
        - LOCAL: ENCRYPTION_KEY
        - AWS_KMS: AWS_KMS_KEY_ID, AWS_REGION (opcional, default us-east-1)
        - AZURE_KV: AZURE_VAULT_URL, AZURE_KEY_NAME
        - HSM_PKCS11: HSM_LIB_PATH, HSM_SLOT, HSM_PIN, HSM_KEY_LABEL
        """
        
        provider_type = os.getenv("KMS_PROVIDER", "LOCAL").upper()
        
        logger.info(f"Inicializando proveedor KMS: {provider_type}")
        
        if provider_type == "LOCAL":
            return LocalKMS()
        
        elif provider_type == "AWS_KMS":
            key_id = os.getenv("AWS_KMS_KEY_ID")
            region = os.getenv("AWS_REGION", "us-east-1")
            if not key_id:
                raise ValueError("AWS_KMS_KEY_ID requerido para AWS KMS")
            return AWSKMS(key_id=key_id, region=region)
        
        elif provider_type == "AZURE_KV":
            vault_url = os.getenv("AZURE_VAULT_URL")
            key_name = os.getenv("AZURE_KEY_NAME")
            if not vault_url or not key_name:
                raise ValueError("AZURE_VAULT_URL y AZURE_KEY_NAME requeridos para Azure Key Vault")
            return AzureKeyVault(vault_url=vault_url, key_name=key_name)
        
        elif provider_type == "HSM_PKCS11":
            lib_path = os.getenv("HSM_LIB_PATH")
            slot = int(os.getenv("HSM_SLOT", "0"))
            pin = os.getenv("HSM_PIN")
            key_label = os.getenv("HSM_KEY_LABEL")
            if not all([lib_path, pin, key_label]):
                raise ValueError("HSM_LIB_PATH, HSM_PIN y HSM_KEY_LABEL requeridos para HSM")
            return HSM_PKCS11(lib_path=lib_path, slot=slot, pin=pin, key_label=key_label)
        
        else:
            raise ValueError(f"Proveedor KMS desconocido: {provider_type}. Opciones válidas: LOCAL, AWS_KMS, AZURE_KV, HSM_PKCS11")


# Instancia global para uso conveniente
_kms_instance: Optional[KMSProvider] = None


def get_kms() -> KMSProvider:
    """Obtiene instancia singleton del proveedor KMS"""
    global _kms_instance
    if _kms_instance is None:
        _kms_instance = KMSFactory.create_provider()
    return _kms_instance


def encrypt_data(plaintext: str) -> str:
    """Función convenience para encriptar datos"""
    return get_kms().encrypt(plaintext)


def decrypt_data(ciphertext: str) -> str:
    """Función convenience para desencriptar datos"""
    return get_kms().decrypt(ciphertext)
