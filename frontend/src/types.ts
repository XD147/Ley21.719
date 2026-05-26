export interface Usuario {
  id: string;
  rutHash: string;
  rutEncriptado: string;
  nombreCompleto: string;
  email: string;
  telefono?: string;
  fechaNacimiento: string;
  tutorId?: string;
  fechaRegistro: string;
}

export interface Organizacion {
  id: string;
  rut: string;
  razonSocial: string;
  emailDpo: string;
  webhookUrlRevocacion?: string;
  modeloPrevencionCertificado: boolean;
}

export interface AccesoOrganizacion {
  id: string;
  usuarioId: string;
  organizacionId: string;
  categoriaDato: string;
  finalidad: string;
  estado: 'ACTIVO' | 'REVOCADO';
  receiptHash: string;
  fechaOtorgamiento: string;
  fechaExpiracion?: string;
}

export interface SolicitudConsentimiento {
  id: string;
  organizacionId: string;
  rutCiudadanoHash: string;
  estado: 'PENDIENTE' | 'APROBADA' | 'RECHAZADA';
  proposalJson: Record<string, unknown>;
  aiFlag?: 'AI_GENERATED' | 'HUMAN_REVIEWED';
  textoLegalPresentado: string;
  requestType: 'NORMAL' | 'PORTABILIDAD';
  sourceOrganizationId?: string;
  fechaSolicitud: string;
}

export interface SolicitudArco {
  id: string;
  organizacionId: string;
  rutCiudadanoHash: string;
  tipo: 'ACCESO' | 'RECTIFICACION' | 'CANCELACION' | 'OPOSICION';
  estado: 'PENDIENTE' | 'EN_PROCESO' | 'COMPLETADA' | 'RECHAZADA';
  tokenEvidenciaIdentidad: string;
  prorrogado: boolean;
  fechaSolicitud: string;
  fechaLimiteRespuesta: string;
}

export interface LogAccesoDatos {
  id: string;
  usuarioId: string;
  organizacionId: string;
  tipoAcceso: 'LECTURA' | 'MODIFICACION' | 'ELIMINACION';
  categoriaDatoConsultado: string;
  justificacionLegal: string;
  ipOrigen: string;
  fechaAcceso: string;
}

export interface AuthToken {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
  tokenType: string;
}

export interface UserSession {
  id: string;
  rutHash: string;
  nombreCompleto: string;
  email: string;
  authProvider: 'CLAVE_UNICA' | 'SII';
}
