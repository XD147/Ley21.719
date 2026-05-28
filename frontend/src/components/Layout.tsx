import { ReactNode } from "react";
import Sidebar from "./Sidebar";
import { useAuth } from "../context/AuthContext";

export default function Layout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();

  return (
    <div className="app-container animate-fade-in">
      <Sidebar />
      <main className="main-content">
        <header className="flex justify-between items-center mb-4 glass-panel" style={{ padding: '16px 24px', borderRadius: '12px' }}>
          <div>
            <span style={{ fontWeight: 500, color: 'var(--text-main)' }}>Hola, {user?.nombreCompleto}</span>
          </div>
          <button onClick={logout} className="btn-secondary">Cerrar Sesión</button>
        </header>
        
        <div className="page-content">
          {children}
        </div>
      </main>
    </div>
  );
}
