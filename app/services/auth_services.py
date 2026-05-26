"""
Servicios de integración con ClaveÚnica (Gobierno de Chile) y Clave Tributaria (SII)
Para autenticación de usuarios y organizaciones según Ley 21.719
"""

import hashlib
import base64
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from urllib.parse import urlencode
import httpx
from jose import jwt, JWTError
from app.config import settings


class ClaveUnicaService:
    """
    Servicio de integración con ClaveÚnica del Gobierno de Chile
    https://ayuda.claveunica.gob.cl/
    
    Permite autenticar ciudadanos chilenos usando su ClaveÚnica
    """
    
    # URLs de producción (cambiar a sandbox para desarrollo)
    BASE_URL = "https://claveunica.gov.cl"
    OAUTH_URL = f"{BASE_URL}/oauth2/authorize"
    TOKEN_URL = f"{BASE_URL}/oauth2/token"
    USERINFO_URL = f"{BASE_URL}/api/userinfo"
    
    def __init__(self):
        self.client_id = settings.claveunica_client_id
        self.client_secret = settings.claveunica_client_secret
        self.redirect_uri = settings.claveunica_redirect_uri
        self.scope = settings.claveunica_scope or "openid profile rut"
    
    def generate_auth_url(self, state: str) -> str:
        """
        Genera la URL de autorización para redirigir al usuario a ClaveÚnica
        
        Args:
            state: Token único para prevenir CSRF
            
        Returns:
            URL completa para redirección
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": self.scope,
            "state": state,
            "acr_values": "nivel3"  # Nivel de seguridad requerido
        }
        return f"{self.OAUTH_URL}?{urlencode(params)}"
    
    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        Intercambia el código de autorización por un token de acceso
        
        Args:
            code: Código de autorización recibido en el callback
            
        Returns:
            Diccionario con access_token, refresh_token, etc.
            
        Raises:
            ValueError: Si el intercambio falla
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                raise ValueError(f"Error al obtener token: {response.text}")
            
            return response.json()
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Obtiene información del usuario autenticado desde ClaveÚnica
        
        Args:
            access_token: Token de acceso válido
            
        Returns:
            Datos del usuario incluyendo RUT, nombre, email
            
        Raises:
            ValueError: Si la petición falla
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.USERINFO_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                }
            )
            
            if response.status_code != 200:
                raise ValueError(f"Error al obtener información del usuario: {response.text}")
            
            user_data = response.json()
            
            # Validar que el RUT esté presente
            if "rut" not in user_data:
                raise ValueError("ClaveÚnica no retornó el RUT del usuario")
            
            return user_data
    
    def verify_token(self, id_token: str) -> Dict[str, Any]:
        """
        Verifica y decodifica el ID Token JWT
        
        Args:
            id_token: JWT token recibido desde ClaveÚnica
            
        Returns:
            Payload del token verificado
            
        Raises:
            JWTError: Si el token es inválido
        """
        try:
            payload = jwt.decode(
                id_token,
                self.client_secret,
                algorithms=["HS256"],
                audience=self.client_id,
                issuer=self.BASE_URL
            )
            return payload
        except JWTError as e:
            raise JWTError(f"Token inválido: {str(e)}")
    
    @staticmethod
    def hash_claveunica_token(token: str) -> str:
        """
        Genera hash SHA-256 del token de ClaveÚnica para usar como evidencia
        
        Args:
            token: Token de acceso o ID token
            
        Returns:
            Hash hexadecimal del token
        """
        return hashlib.sha256(token.encode('utf-8')).hexdigest()


class SiiClaveTributariaService:
    """
    Servicio de integración con Clave Tributaria del SII (Servicio de Impuestos Internos)
    Para autenticación de empresas y organizaciones
    
    Nota: El SII requiere certificado digital para producción
    """
    
    # URLs del SII
    BASE_URL_PRODUCCION = "https://www.sii.cl"
    BASE_URL_SANDBOX = "https://maui.sii.cl"
    API_URL = f"{BASE_URL_SANDBOX}/api"
    OAUTH_TOKEN_URL = f"{BASE_URL_SANDBOX}/oauth/token"
    
    def __init__(self, use_sandbox: bool = True):
        self.use_sandbox = use_sandbox
        self.base_url = self.BASE_URL_SANDBOX if use_sandbox else self.BASE_URL_PRODUCCION
        self.client_id = settings.sii_client_id
        self.client_secret = settings.sii_client_secret
        self.certificate_path = settings.sii_certificate_path
        self.private_key_path = settings.sii_private_key_path
    
    def generate_auth_url(self, state: str, rut_organizacion: str) -> str:
        """
        Genera URL para autenticación con Clave Tributaria
        
        Args:
            state: Token para prevenir CSRF
            rut_organizacion: RUT de la organización que se autentica
            
        Returns:
            URL completa para redirección
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": settings.sii_redirect_uri,
            "response_type": "code",
            "scope": "rut razon_social giro",
            "state": state,
            "rut": rut_organizacion
        }
        return f"{self.base_url}/oauth/authorize?{urlencode(params)}"
    
    async def exchange_code_for_token(self, code: str, rut_organizacion: str) -> Dict[str, Any]:
        """
        Intercambia código por token de acceso del SII
        
        Args:
            code: Código de autorización
            rut_organizacion: RUT de la organización
            
        Returns:
            Token de acceso y datos asociados
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.OAUTH_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": settings.sii_redirect_uri,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "rut": rut_organizacion
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                raise ValueError(f"SII Error: {response.text}")
            
            return response.json()
    
    async def get_organization_info(self, access_token: str, rut: str) -> Dict[str, Any]:
        """
        Obtiene información oficial de la organización desde el SII
        
        Args:
            access_token: Token de acceso del SII
            rut: RUT de la organización
            
        Returns:
            Datos oficiales: razón social, giro, estado, etc.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.API_URL}/empresa/{rut}",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                }
            )
            
            if response.status_code != 200:
                raise ValueError(f"SII API Error: {response.text}")
            
            org_data = response.json()
            
            # Validar datos requeridos
            required_fields = ["rut", "razon_social", "giro"]
            for field in required_fields:
                if field not in org_data:
                    raise ValueError(f"SII no retornó campo requerido: {field}")
            
            return org_data
    
    async def validate_dte_authorization(self, access_token: str, rut: str) -> bool:
        """
        Valida que la organización tenga DTE autorizado (indicador de formalidad)
        
        Args:
            access_token: Token de acceso
            rut: RUT de la organización
            
        Returns:
            True si tiene DTE autorizado
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.API_URL}/dte/authorized/{rut}",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("authorized", False)
            
            return False
    
    @staticmethod
    def hash_sii_token(token: str) -> str:
        """
        Genera hash del token del SII para evidencia de autenticación
        
        Args:
            token: Token de acceso del SII
            
        Returns:
            Hash SHA-256 del token
        """
        return hashlib.sha256(token.encode('utf-8')).hexdigest()
    
    def sign_request_with_certificate(self, data: str) -> str:
        """
        Firma una petición usando el certificado digital del SII
        
        Requiere configuración de certificado .p12 o .pem
        
        Args:
            data: Datos a firmar
            
        Returns:
            Firma en base64
        """
        # Implementación depende del formato del certificado
        # Esto es un placeholder para implementación con cryptography
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.backends import default_backend
        
        if not self.private_key_path:
            raise ValueError("Certificado privado no configurado")
        
        with open(self.private_key_path, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None,
                backend=default_backend()
            )
        
        signature = private_key.sign(
            data.encode('utf-8'),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        
        return base64.b64encode(signature).decode('utf-8')


class AuthTokenService:
    """
    Servicio para gestión de tokens de sesión JWT internos
    """
    
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    
    def create_access_token(self, data: dict, expires_delta: timedelta = None) -> str:
        """Crea un token de acceso JWT"""
        to_encode = data.copy()
        
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire, "type": "access"})
        
        encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=self.ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: dict) -> str:
        """Crea un token de refresco JWT"""
        to_encode = data.copy()
        
        expire = datetime.utcnow() + timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        
        encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=self.ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verifica y decodifica un token JWT"""
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[self.ALGORITHM])
            return payload
        except JWTError as e:
            raise JWTError(f"Token inválido: {str(e)}")
    
    def create_session_tokens(self, user_id: str, rut_hash: str, auth_provider: str) -> Dict[str, Any]:
        """
        Crea par de tokens (access + refresh) para una sesión
        
        Args:
            user_id: ID del usuario
            rut_hash: Hash del RUT para referencia
            auth_provider: Proveedor de autenticación (claveunica, sii, local)
            
        Returns:
            Diccionario con access_token, refresh_token y metadata
        """
        access_token = self.create_access_token({
            "sub": user_id,
            "rut_hash": rut_hash,
            "auth_provider": auth_provider
        })
        
        refresh_token = self.create_refresh_token({
            "sub": user_id,
            "auth_provider": auth_provider
        })
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }


# Instancias globales
claveunica_service = ClaveUnicaService()
sii_service = SiiClaveTributariaService(use_sandbox=settings.sii_use_sandbox)
auth_token_service = AuthTokenService()
