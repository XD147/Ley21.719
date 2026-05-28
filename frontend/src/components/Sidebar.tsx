import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Sidebar() {
  const { user } = useAuth();
  const location = useLocation();
  const isOrganization = user?.authProvider === "SII";

  const getMenuClass = (path: string) => {
    return `sidebar-item ${location.pathname === path ? "active" : ""}`;
  };

  return (
    <aside className="sidebar glass-panel">
      <div className="sidebar-header">
        <h2 className="sidebar-title">Ley 21.719</h2>
        <span className="badge badge-info">{isOrganization ? "Organización" : "Ciudadano"}</span>
      </div>
      
      <nav className="sidebar-nav">
        {isOrganization ? (
          <>
            <Link to="/panel-dpo" className={getMenuClass("/panel-dpo")}>Panel DPO</Link>
            <Link to="/rat" className={getMenuClass("/rat")}>Registro RAT</Link>
            <Link to="/brechas" className={getMenuClass("/brechas")}>Brechas de Seguridad</Link>
            <Link to="/eipd" className={getMenuClass("/eipd")}>Evaluaciones (EIPD)</Link>
            <Link to="/solicitudes" className={getMenuClass("/solicitudes")}>Gestión ARCO</Link>
          </>
        ) : (
          <>
            <Link to="/dashboard" className={getMenuClass("/dashboard")}>Mis Consentimientos</Link>
            <Link to="/timeline" className={getMenuClass("/timeline")}>Timeline de Accesos</Link>
            <Link to="/portabilidad" className={getMenuClass("/portabilidad")}>Portabilidad de Datos</Link>
            <Link to="/solicitudes" className={getMenuClass("/solicitudes")}>Mis Solicitudes ARCO</Link>
          </>
        )}
      </nav>
      
      <div className="sidebar-footer">
        <p style={{fontSize: '0.8rem', color: 'var(--text-muted)'}}>GovTech Secure Platform</p>
      </div>
    </aside>
  );
}
