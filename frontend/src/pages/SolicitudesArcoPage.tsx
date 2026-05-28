import { useState, useEffect } from "react";
import apiClient from "../api";
import { SolicitudArco } from "../types";

export default function SolicitudesArcoPage() {
  const [solicitudes, setSolicitudes] = useState<SolicitudArco[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await apiClient.getSolicitudesArco();
        setSolicitudes(data);
      } catch (err) {
        console.error("Error loading solicitudes:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center" style={{ minHeight: '50vh' }}>
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="animate-fade-in">
      <div className="page-header flex justify-between items-center">
        <div>
          <h1 className="page-title">Solicitudes ARCO</h1>
          <p className="page-subtitle">Acceso, Rectificación, Cancelación y Oposición</p>
        </div>
        <button className="btn-primary" onClick={() => alert('Próximamente: Crear nueva solicitud ARCO')}>
          + Nueva Solicitud
        </button>
      </div>

      <div className="grid">
        {solicitudes.length === 0 ? (
          <div className="glass-card" style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '40px' }}>
            <p style={{ color: 'var(--text-muted)' }}>No tienes solicitudes ARCO registradas.</p>
          </div>
        ) : (
          solicitudes.map((solicitud) => (
            <div key={solicitud.id} className="glass-card">
              <div className="flex justify-between items-center mb-4">
                <h3 style={{ margin: 0, fontSize: '1.2rem' }}>{solicitud.tipo}</h3>
                <span className={`badge ${
                  solicitud.estado === 'COMPLETADA' ? 'badge-success' : 
                  solicitud.estado === 'RECHAZADA' ? 'badge-danger' : 
                  solicitud.estado === 'EN_PROCESO' ? 'badge-info' : 'badge-warning'
                }`}>
                  {solicitud.estado}
                </span>
              </div>
              <p><strong>Organización ID:</strong> {solicitud.organizacionId}</p>
              <p><strong>Fecha Solicitud:</strong> {new Date(solicitud.fechaSolicitud).toLocaleDateString()}</p>
              <p><strong>Límite Respuesta:</strong> {new Date(solicitud.fechaLimiteRespuesta).toLocaleDateString()}</p>
              
              {solicitud.prorrogado && (
                <div style={{ marginTop: '16px', background: 'rgba(245, 158, 11, 0.1)', padding: '8px 12px', borderRadius: '8px', color: 'var(--warning)', fontSize: '0.9rem' }}>
                  ⚠️ El plazo de respuesta ha sido prorrogado por la organización.
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
