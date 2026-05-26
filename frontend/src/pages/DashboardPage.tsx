import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import apiClient from '../api';
import { AccesoOrganizacion, SolicitudArco } from '../types';

export default function DashboardPage() {
  const { user, logout } = useAuth();
  const [accesos, setAccesos] = useState<AccesoOrganizacion[]>([]);
  const [solicitudesArco, setSolicitudesArco] = useState<SolicitudArco[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'accesos' | 'arco'>('accesos');

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const [accesosData, arcoData] = await Promise.all([
        apiClient.getAccesosUsuario(),
        apiClient.getSolicitudesArco(),
      ]);
      setAccesos(accesosData);
      setSolicitudesArco(arcoData);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  }

  async function handleRevocarAcceso(id: string) {
    if (!confirm('¿Estás seguro de revocar este acceso?')) return;
    
    try {
      await apiClient.revocarAcceso(id);
      setAccesos(accesos.map(a => 
        a.id === id ? { ...a, estado: 'REVOCADO' as const } : a
      ));
    } catch (error) {
      console.error('Error revocando acceso:', error);
      alert('Error al revocar el acceso');
    }
  }

  if (loading) {
    return <div style={styles.loading}>Cargando...</div>;
  }

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <div style={styles.headerContent}>
          <h1 style={styles.logo}>Ley 21.719</h1>
          <nav style={styles.nav}>
            <button
              style={activeTab === 'accesos' ? styles.navButtonActive : styles.navButton}
              onClick={() => setActiveTab('accesos')}
            >
              Mis Accesos
            </button>
            <button
              style={activeTab === 'arco' ? styles.navButtonActive : styles.navButton}
              onClick={() => setActiveTab('arco')}
            >
              Solicitudes ARCO
            </button>
          </nav>
          <div style={styles.userInfo}>
            <span style={styles.userName}>{user?.nombreCompleto}</span>
            <button style={styles.logoutButton} onClick={logout}>
              Cerrar Sesión
            </button>
          </div>
        </div>
      </header>

      <main style={styles.main}>
        {activeTab === 'accesos' && (
          <div style={styles.section}>
            <h2 style={styles.sectionTitle}>Accesos Otorgados a Organizaciones</h2>
            {accesos.length === 0 ? (
              <p style={styles.emptyState}>No has otorgado accesos a organizaciones</p>
            ) : (
              <div style={styles.grid}>
                {accesos.map((acceso) => (
                  <div key={acceso.id} style={styles.card}>
                    <div style={styles.cardHeader}>
                      <h3 style={styles.cardTitle}>{acceso.categoriaDato}</h3>
                      <span style={getEstadoStyle(acceso.estado)}>{acceso.estado}</span>
                    </div>
                    <p style={styles.cardText}><strong>Finalidad:</strong> {acceso.finalidad}</p>
                    <p style={styles.cardText}>
                      <strong>Otorgado:</strong> {new Date(acceso.fechaOtorgamiento).toLocaleDateString()}
                    </p>
                    {acceso.fechaExpiracion && (
                      <p style={styles.cardText}>
                        <strong>Expira:</strong> {new Date(acceso.fechaExpiracion).toLocaleDateString()}
                      </p>
                    )}
                    {acceso.estado === 'ACTIVO' && (
                      <button
                        style={styles.revokeButton}
                        onClick={() => handleRevocarAcceso(acceso.id)}
                      >
                        Revocar Acceso
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'arco' && (
          <div style={styles.section}>
            <h2 style={styles.sectionTitle}>Solicitudes ARCO</h2>
            <button style={styles.newRequestButton} onClick={() => alert('Funcionalidad próximamente')}>
              + Nueva Solicitud ARCO
            </button>
            {solicitudesArco.length === 0 ? (
              <p style={styles.emptyState}>No tienes solicitudes ARCO</p>
            ) : (
              <div style={styles.grid}>
                {solicitudesArco.map((solicitud) => (
                  <div key={solicitud.id} style={styles.card}>
                    <div style={styles.cardHeader}>
                      <h3 style={styles.cardTitle}>{solicitud.tipo}</h3>
                      <span style={getEstadoArcoStyle(solicitud.estado)}>{solicitud.estado}</span>
                    </div>
                    <p style={styles.cardText}>
                      <strong>Fecha:</strong> {new Date(solicitud.fechaSolicitud).toLocaleDateString()}
                    </p>
                    <p style={styles.cardText}>
                      <strong>Límite respuesta:</strong> {new Date(solicitud.fechaLimiteRespuesta).toLocaleDateString()}
                    </p>
                    {solicitud.prorrogado && (
                      <p style={styles.warningText}>⚠️ Prorrogada</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

function getEstadoStyle(estado: string): React.CSSProperties {
  const baseStyle: React.CSSProperties = {
    padding: '4px 12px',
    borderRadius: '12px',
    fontSize: '12px',
    fontWeight: '600',
  };
  
  if (estado === 'ACTIVO') {
    return { ...baseStyle, background: '#d4edda', color: '#155724' };
  }
  return { ...baseStyle, background: '#f8d7da', color: '#721c24' };
}

function getEstadoArcoStyle(estado: string): React.CSSProperties {
  const baseStyle: React.CSSProperties = {
    padding: '4px 12px',
    borderRadius: '12px',
    fontSize: '12px',
    fontWeight: '600',
  };
  
  const colors: Record<string, { bg: string; color: string }> = {
    PENDIENTE: { bg: '#fff3cd', color: '#856404' },
    EN_PROCESO: { bg: '#cce5ff', color: '#004085' },
    COMPLETADA: { bg: '#d4edda', color: '#155724' },
    RECHAZADA: { bg: '#f8d7da', color: '#721c24' },
  };
  
  const color = colors[estado] || { bg: '#e2e3e5', color: '#383d41' };
  return { ...baseStyle, background: color.bg, color: color.color };
}

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    minHeight: '100vh',
    background: '#f5f7fa',
  },
  header: {
    background: 'white',
    borderBottom: '1px solid #e1e5eb',
    padding: '16px 24px',
  },
  headerContent: {
    maxWidth: '1200px',
    margin: '0 auto',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  logo: {
    fontSize: '24px',
    fontWeight: 'bold',
    color: '#667eea',
    margin: 0,
  },
  nav: {
    display: 'flex',
    gap: '8px',
  },
  navButton: {
    padding: '8px 16px',
    fontSize: '14px',
    fontWeight: '500',
    color: '#666',
    background: 'transparent',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
  },
  navButtonActive: {
    padding: '8px 16px',
    fontSize: '14px',
    fontWeight: '500',
    color: 'white',
    background: '#667eea',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
  },
  userInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  },
  userName: {
    fontSize: '14px',
    color: '#333',
  },
  logoutButton: {
    padding: '8px 16px',
    fontSize: '14px',
    color: '#c41230',
    background: '#fff5f5',
    border: '1px solid #fed7d7',
    borderRadius: '6px',
    cursor: 'pointer',
  },
  main: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '32px 24px',
  },
  section: {
    background: 'white',
    borderRadius: '12px',
    padding: '24px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
  },
  sectionTitle: {
    fontSize: '20px',
    fontWeight: '600',
    color: '#333',
    marginBottom: '24px',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
    gap: '16px',
  },
  card: {
    border: '1px solid #e1e5eb',
    borderRadius: '8px',
    padding: '20px',
    background: 'white',
  },
  cardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '12px',
  },
  cardTitle: {
    fontSize: '16px',
    fontWeight: '600',
    color: '#333',
    margin: 0,
  },
  cardText: {
    fontSize: '14px',
    color: '#666',
    marginBottom: '8px',
  },
  revokeButton: {
    width: '100%',
    padding: '10px',
    fontSize: '14px',
    fontWeight: '500',
    color: 'white',
    background: '#c41230',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    marginTop: '12px',
  },
  newRequestButton: {
    padding: '12px 24px',
    fontSize: '14px',
    fontWeight: '600',
    color: 'white',
    background: '#667eea',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    marginBottom: '24px',
  },
  emptyState: {
    fontSize: '14px',
    color: '#999',
    textAlign: 'center',
    padding: '40px',
  },
  warningText: {
    fontSize: '12px',
    color: '#856404',
    background: '#fff3cd',
    padding: '4px 8px',
    borderRadius: '4px',
    display: 'inline-block',
  },
  loading: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '100vh',
    fontSize: '18px',
    color: '#666',
  },
};
