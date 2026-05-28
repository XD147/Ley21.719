import { useState, useEffect } from "react";
import apiClient from "../api";
import { PanelDPOMetricas } from "../types";

export default function PanelDPOPage() {
  const [metricas, setMetricas] = useState<PanelDPOMetricas | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await apiClient.getPanelDPOMetricas();
        setMetricas(data);
      } catch (err) {
        console.error("Error loading metrics:", err);
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
        <h1 className="page-title">Panel de Control DPO</h1>
        <p className="page-subtitle">Monitoreo del cumplimiento normativo de Ley 21.719</p>
      </div>

      <div className="grid">
        <div className="glass-card">
          <h3 style={{ color: 'var(--text-muted)', marginBottom: '16px' }}>Nivel de Riesgo General</h3>
          <h2 style={{ fontSize: '2.5rem', color: 'var(--primary)' }}>{metricas?.nivel_riesgo_general || 'MEDIO'}</h2>
        </div>
        <div className="glass-card">
          <h3 style={{ color: 'var(--text-muted)', marginBottom: '16px' }}>Cumplimiento Global</h3>
          <h2 style={{ fontSize: '2.5rem', color: 'var(--success)' }}>{metricas?.porcentaje_cumplimiento || 85}%</h2>
        </div>
        <div className="glass-card">
          <h3 style={{ color: 'var(--text-muted)', marginBottom: '16px' }}>Brechas Activas</h3>
          <h2 style={{ fontSize: '2.5rem', color: metricas?.brechas_activas ? 'var(--danger)' : 'var(--success)' }}>
            {metricas?.brechas_activas || 0}
          </h2>
        </div>
        <div className="glass-card">
          <h3 style={{ color: 'var(--text-muted)', marginBottom: '16px' }}>Solicitudes ARCO Pendientes</h3>
          <h2 style={{ fontSize: '2.5rem', color: 'var(--warning)' }}>{metricas?.solicitudes_arco_pendientes || 0}</h2>
        </div>
      </div>
      
      <div className="mt-4 glass-card" style={{ padding: '32px' }}>
        <h2 style={{ marginBottom: '16px' }}>Próximos Pasos Recomendados</h2>
        <ul style={{ paddingLeft: '20px', color: 'var(--text-muted)', lineHeight: '1.8' }}>
          <li>Revisar Evaluación de Impacto (EIPD) pendiente de aprobación en el sistema de Recursos Humanos.</li>
          <li>Actualizar el Registro de Actividades de Tratamiento (RAT) del nuevo proveedor Cloud.</li>
          <li>Verificar webhook de revocación de consentimientos que falló recientemente.</li>
        </ul>
      </div>
    </div>
  );
}
