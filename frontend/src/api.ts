import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { AuthToken, Usuario, AccesoOrganizacion, SolicitudArco, LogAccesoDatos } from './types';

class ApiClient {
	private client: AxiosInstance;
	private refreshTokenPromise: Promise<string> | null = null;

	constructor() {
		this.client = axios.create({
			baseURL: '/api',
			headers: {
				'Content-Type': 'application/json',
			},
		});
		this.setupInterceptors();
	}

	private setupInterceptors(): void {
		this.client.interceptors.request.use(
			(config: InternalAxiosRequestConfig) => {
				const token = localStorage.getItem('accessToken');
				if (token && config.headers) {
					config.headers.Authorization = `Bearer ${token}`;
				}
				return config;
			},
			(error) => Promise.reject(error)
		);

		this.client.interceptors.response.use(
			(response) => response,
			async (error) => {
				const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
				if (error.response?.status === 401 && !originalRequest._retry) {
					originalRequest._retry = true;
					try {
						const newToken = await this.refreshAccessToken();
						if (originalRequest.headers) {
							originalRequest.headers.Authorization = `Bearer ${newToken}`;
						}
						return this.client(originalRequest);
					} catch (refreshError) {
						localStorage.removeItem('accessToken');
						localStorage.removeItem('refreshToken');
						window.location.href = '/login';
						return Promise.reject(refreshError);
					}
				}
				return Promise.reject(error);
			}
		);
	}

	private async refreshAccessToken(): Promise<string> {
		if (this.refreshTokenPromise) {
			return this.refreshTokenPromise;
		}
		this.refreshTokenPromise = (async () => {
			const refreshToken = localStorage.getItem('refreshToken');
			if (!refreshToken) {
				throw new Error('No refresh token available');
			}
			const response = await axios.post<AuthToken>('/auth/refresh', {
				refreshToken,
			});
			const { accessToken } = response.data;
			localStorage.setItem('accessToken', accessToken);
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
	async loginClaveUnica(code: string, state: string): Promise<AuthToken> {
		const response = await axios.post<AuthToken>('/auth/claveunica/callback', {
			code,
			state,
		});
		return response.data;
	}

	async loginSii(code: string, state: string): Promise<AuthToken> {
		const response = await axios.post<AuthToken>('/auth/sii/callback', {
			code,
			state,
		});
		return response.data;
	}

	async logout(): Promise<void> {
		try {
			await this.post('/auth/logout');
		} finally {
			localStorage.removeItem('accessToken');
			localStorage.removeItem('refreshToken');
		}
	}

	// Usuario endpoints
	getUsuarioActual() {
		return this.get<{ usuario: Usuario }>('/usuarios/me');
	}

	// AccesoOrganizacion endpoints
	getAccesosUsuario() {
		return this.get<AccesoOrganizacion[]>('/accesos/mis-accesos');
	}

	revocarAcceso(id: string) {
		return this.put(`/accesos/${id}/revocar`);
	}

	// Solicitud ARCO endpoints
	crearSolicitudArco(data: Partial<SolicitudArco>) {
		return this.post<SolicitudArco>('/solicitudes-arco', data);
	}

	getSolicitudesArco() {
		return this.get<SolicitudArco[]>('/solicitudes-arco/mis-solicitudes');
	}

	// Log endpoints (solo para organizaciones)
	getLogsAcceso(organizacionId: string, filters?: { fechaInicio?: string; fechaFin?: string }) {
		return this.get<LogAccesoDatos[]>(`/logs/${organizacionId}`, { params: filters });
	}
}

export const apiClient = new ApiClient();
export default apiClient;