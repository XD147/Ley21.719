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
  estado: "ACTIVO" | "REVOCADO";
  receiptHash: string;
  fechaOtorgamiento: string;
  fechaExpiracion?: string;
}
export interface SolicitudConsentimiento {
  id: string;
  organizacionId: string;
  rutCiudadanoHash: string;
  estado: "PENDIENTE" | "APROBADA" | "RECHAZADA";
  proposalJson: Record<string, unknown>;
  aiFlag?: "AI_GENERATED" | "HUMAN_REVIEWED";
  textoLegalPresentado: string;
  requestType: "NORMAL" | "PORTABILIDAD";
  sourceOrganizationId?: string;
  fechaSolicitud: string;
}
export interface SolicitudArco {
  id: string;
  organizacionId: string;
  rutCiudadanoHash: string;
  tipo: "ACCESO" | "RECTIFICACION" | "CANCELACION" | "OPOSICION";
  estado: "PENDIENTE" | "EN_PROCESO" | "COMPLETADA" | "RECHAZADA";
  tokenEvidenciaIdentidad: string;
  prorrogado: boolean;
  fechaSolicitud: string;
  fechaLimiteRespuesta: string;
}
export interface LogAccesoDatos {
  id: string;
  usuarioId: string;
  organizacionId: string;
  tipoAcceso: "LECTURA" | "MODIFICACION" | "ELIMINACION";
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
  authProvider: "CLAVE_UNICA" | "SII";
}

/* GovTech Extra Types */
export interface RAT {
  id: string;
  nombre: string;
  descripcion: string;
  finalidad: string;
  categorias_datos: string[];
  tiene_transferencia_internacional: boolean;
  fecha_creacion: string;
}

export interface Brecha {
  id: string;
  titulo: string;
  tipo_brecha: string;
  nivel_riesgo: string;
  estado: string;
  cumple_plazo_72h: boolean;
  horas_transcurridas: number;
  fecha_descubrimiento: string;
}

export interface EIPD {
  id: string;
  nombre: string;
  estado: string;
  nivel_riesgo_inicial: string | null;
  nivel_riesgo_residual: string | null;
  fecha_creacion: string;
}

export interface PanelDPOMetricas {
  total_titulares: number;
  solicitudes_arco_pendientes: number;
  brechas_activas: number;
  nivel_riesgo_general: string;
  porcentaje_cumplimiento: number;
}
