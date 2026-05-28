import axios, { AxiosInstance, InternalAxiosRequestConfig } from "axios";
import {
  AuthToken,
  Usuario,
  UserSession,
  AccesoOrganizacion,
  SolicitudArco,
  LogAccesoDatos,
  RAT,
  Brecha,
  EIPD,
  PanelDPOMetricas
} from "./types";

class ApiClient {
  private client: AxiosInstance;
  private refreshTokenPromise: Promise<string> | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: "/api/v1", // Updated to v1 where applicable, but wait, previous was just /api. The backend actually uses various prefixes. In `routes.py` and `auth_routes.py` they are mapped. Let's use standard prefix, assuming the proxy handles it or we match the backend.
      headers: {
        "Content-Type": "application/json",
      },
    });
    
    // Some routes in the old code used /api, some /api/v1. I'll stick to the base and prefix properly.
    this.client.defaults.baseURL = "/api";
    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = localStorage.getItem("accessToken");
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error),
    );

    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & {
          _retry?: boolean;
        };
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          try {
            const newToken = await this.refreshAccessToken();
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${newToken}`;
            }
            return this.client(originalRequest);
          } catch (refreshError) {
            localStorage.removeItem("accessToken");
            localStorage.removeItem("refreshToken");
            window.location.href = "/login";
            return Promise.reject(refreshError);
          }
        }
        return Promise.reject(error);
      },
    );
  }

  private async refreshAccessToken(): Promise<string> {
    if (this.refreshTokenPromise) {
      return this.refreshTokenPromise;
    }
    this.refreshTokenPromise = (async () => {
      const refreshToken = localStorage.getItem("refreshToken");
      if (!refreshToken) {
        throw new Error("No refresh token available");
      }
      const response = await axios.post<AuthToken>("/auth/refresh", {
        refreshToken,
      });
      const { accessToken } = response.data;
      localStorage.setItem("accessToken", accessToken);
      return accessToken;
    })();
    try {
      return await this.refreshTokenPromise;
    } finally {
      this.refreshTokenPromise = null;
    }
  }

  get<T>(url: string, config?: object): Promise<T> {
    return this.client.get<T>(url, config).then((res) => res.data);
  }

  post<T>(url: string, data?: unknown, config?: object): Promise<T> {
    return this.client.post<T>(url, data, config).then((res) => res.data);
  }

  put<T>(url: string, data?: unknown, config?: object): Promise<T> {
    return this.client.put<T>(url, data, config).then((res) => res.data);
  }

  delete<T>(url: string, config?: object): Promise<T> {
    return this.client.delete<T>(url, config).then((res) => res.data);
  }

  // Auth endpoints
  async verifySession(): Promise<{ usuario: UserSession }> {
    const token = localStorage.getItem("accessToken");
    const response = await axios.get("/auth/verify", {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    });
    
    const { type, data } = response.data;
    
    const session: UserSession = {
      id: data.id,
      rutHash: data.rut_hash || data.rut || "",
      nombreCompleto: data.nombre_completo || data.razon_social || "Usuario",
      email: data.email || data.email_dpo || "",
      authProvider: type === "usuario" ? "CLAVE_UNICA" : "SII"
    };

    return { usuario: session };
  }

  async loginClaveUnica(code: string, state: string): Promise<AuthToken> {
    const response = await axios.post<AuthToken>("/auth/claveunica/callback", {
      code,
      state,
    });
    return response.data;
  }

  async loginSii(code: string, state: string): Promise<AuthToken> {
    const response = await axios.post<AuthToken>("/auth/sii/callback", {
      code,
      state,
    });
    return response.data;
  }

  async logout(): Promise<void> {
    try {
      const token = localStorage.getItem("accessToken");
      if (token) {
        await axios.post("/auth/logout", {}, {
          headers: { Authorization: `Bearer ${token}` }
        });
      }
    } catch (e) {
      console.error(e);
    } finally {
      localStorage.removeItem("accessToken");
      localStorage.removeItem("refreshToken");
    }
  }

  // Usuario endpoints
  getUsuarioActual() {
    return this.get<{ usuario: Usuario }>("/usuarios/me");
  }

  // AccesoOrganizacion endpoints
  getAccesosUsuario() {
    return this.get<AccesoOrganizacion[]>("/accesos/mis-accesos");
  }

  revocarAcceso(id: string) {
    return this.put(`/accesos/${id}/revocar`);
  }

  // Solicitud ARCO endpoints
  crearSolicitudArco(data: Partial<SolicitudArco>) {
    return this.post<SolicitudArco>("/solicitudes-arco", data);
  }

  getSolicitudesArco() {
    return this.get<SolicitudArco[]>("/solicitudes-arco/mis-solicitudes");
  }

  // Log endpoints (para organizaciones o ciudadanos según corresponda)
  getLogsAcceso(
    organizacionId: string,
    filters?: { fechaInicio?: string; fechaFin?: string },
  ) {
    return this.get<LogAccesoDatos[]>(`/logs/${organizacionId}`, {
      params: filters,
    });
  }

  // ==================== FUNCIONALIDADES GOVTECH (LEY 21.719) ====================

  // Portabilidad (Ciudadanos)
  exportarPortabilidad(formato: string = "json") {
    // Portabilidad is mapped under /api/v1 prefix in portabilidad.py
    return this.post<any>("/v1/portabilidad/exportar", { formato });
  }

  importarPortabilidad(datosJson: string, organizacionOrigenId: string) {
    return this.post<any>("/v1/portabilidad/importar", { 
      datos_json: datosJson, 
      organizacion_origen_id: organizacionOrigenId, 
      confirmar_actualizacion: true 
    });
  }

  // Panel DPO (Organizaciones)
  getPanelDPOMetricas() {
    return this.get<PanelDPOMetricas>("/panel-dpo/metricas");
  }

  getPanelDPOAlertas() {
    return this.get<any[]>("/panel-dpo/alertas");
  }

  // RAT: Registro Actividades Tratamiento (Organizaciones)
  getRATs() {
    return this.get<RAT[]>("/rat");
  }

  crearRAT(data: any) {
    return this.post<RAT>("/rat", data);
  }

  // Brechas de Seguridad (Organizaciones)
  getBrechas() {
    return this.get<Brecha[]>("/brechas");
  }

  reportarBrecha(data: any) {
    return this.post<Brecha>("/brechas", data);
  }

  notificarBrechaAgencia(brechaId: string) {
    return this.post(`/brechas/${brechaId}/notificar-agencia`);
  }

  // EIPD: Evaluación de Impacto (Organizaciones)
  getEIPDs() {
    return this.get<EIPD[]>("/eipd");
  }

  crearEIPD(data: any) {
    return this.post<EIPD>("/eipd", data);
  }
}

export const apiClient = new ApiClient();
export default apiClient;
