import { useState, useEffect } from "react";
import apiClient from "../api";
import { LogAccesoDatos } from "../types";

export default function TimelineAccesosPage() {
  const [logs, setLogs] = useState<LogAccesoDatos[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        // As a citizen, we mock getting the logs using a known org ID or the backend endpoint should provide it.
        // For demonstration we will pass a placeholder. The real API implementation might differ.
        const response = await apiClient.getLogsAcceso('mi-org-id');
        setLogs(response);
      } catch (err) {
        console.error(err);
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
      <div className="page-header">
        <h1 className="page-title">Timeline de Accesos</h1>
        <p className="page-subtitle">Auditoría completa de quién ha accedido a tus datos</p>
      </div>

      <div className="glass-card">
        {logs.length === 0 ? (
          <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '40px' }}>
            No hay registros de acceso recientes a tus datos o el endpoint retornó vacío.
          </p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {logs.map(log => (
              <div key={log.id} style={{ display: 'flex', gap: '16px', borderBottom: '1px solid var(--surface-glass-border)', paddingBottom: '24px' }}>
                <div style={{ 
                  minWidth: '48px', height: '48px', borderRadius: '50%', 
                  background: 'rgba(79, 70, 229, 0.1)', color: 'var(--primary)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontWeight: 'bold'
                }}>
                  {log.tipoAcceso.charAt(0)}
                </div>
                <div>
                  <h4 style={{ margin: '0 0 4px 0', fontSize: '1.1rem' }}>{log.tipoAcceso} a {log.categoriaDatoConsultado}</h4>
                  <p style={{ margin: '0 0 8px 0', color: 'var(--text-muted)' }}>{new Date(log.fechaAcceso).toLocaleString()}</p>
                  <p style={{ margin: 0 }}><strong>Justificación:</strong> {log.justificacionLegal}</p>
                  <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>IP: {log.ipOrigen} | Org ID: {log.organizacionId}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
