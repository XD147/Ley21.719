import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import { UserSession } from "../types";
import apiClient from "../api";

interface AuthContextType {
  user: UserSession | null;
  isLoading: boolean;
  loginClaveUnica: () => void;
  loginSii: (rut?: string) => void;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserSession | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadUser = async () => {
      const token = localStorage.getItem("accessToken");
      if (!token) {
        setIsLoading(false);
        return;
      }

      try {
        const response = await apiClient.verifySession();
        setUser(response.usuario);
      } catch (error) {
        localStorage.removeItem("accessToken");
        localStorage.removeItem("refreshToken");
      } finally {
        setIsLoading(false);
      }
    };

    loadUser();
  }, []);

  const loginClaveUnica = async () => {
    try {
      const response = await apiClient.get<{ authorization_url: string }>("/auth/claveunica/login", { baseURL: "" });
      window.location.href = response.authorization_url;
    } catch (err) {
      console.error(err);
      alert("Error de conexión con ClaveÚnica");
    }
  };

  const loginSii = async (rut?: string) => {
    try {
      const rutParam = rut || "76123456-7"; // Default para testing
      const response = await apiClient.get<{ authorization_url: string }>(`/auth/sii/login?rut_organizacion=${rutParam}`, { baseURL: "" });
      window.location.href = response.authorization_url;
    } catch (err) {
      console.error(err);
      alert("Error de conexión con SII");
    }
  };

  const logout = async () => {
    await apiClient.logout();
    setUser(null);
  };

  const value = {
    user,
    isLoading,
    loginClaveUnica,
    loginSii,
    logout,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
