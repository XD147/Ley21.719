import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { UserSession } from '../types';
import apiClient from '../api';

interface AuthContextType {
  user: UserSession | null;
  isLoading: boolean;
  loginClaveUnica: () => void;
  loginSii: () => void;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserSession | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadUser = async () => {
      const token = localStorage.getItem('accessToken');
      if (!token) {
        setIsLoading(false);
        return;
      }

      try {
        const response = await apiClient.get<{ usuario: UserSession }>('/auth/verify');
        setUser(response.usuario);
      } catch (error) {
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
      } finally {
        setIsLoading(false);
      }
    };

    loadUser();
  }, []);

  const loginClaveUnica = () => {
    window.location.href = '/auth/claveunica/login';
  };

  const loginSii = () => {
    window.location.href = '/auth/sii/login';
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
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
