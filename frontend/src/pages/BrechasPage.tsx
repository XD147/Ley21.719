import { useState, useEffect } from "react";
import apiClient from "../api";
import { Brecha } from "../types";

export default function BrechasPage() {
  const [brechas, setBrechas] = useState<Brecha[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await apiClient.getBrechas();
        setBrechas(data);
      } catch (err) {
        console.error("Error loading brechas:", err);
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
          <h1 className="page-title">Gestión de Brechas</h1>
          <p className="page-subtitle">Registro y notificación de incidentes de seguridad (Art. 38)</p>
        </div>
        <button className="btn-danger" onClick={() => alert('Abre un formulario para notificar un incidente de seguridad.')}>
          + Reportar Incidente
        </button>
      </div>

      <div className="grid">
        {brechas.length === 0 ? (
           <div className="glass-card" style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '40px' }}>
            <p style={{ color: 'var(--text-muted)' }}>No se han registrado incidentes de seguridad.</p>
          </div>
        ) : (
          brechas.map((b) => (
            <div key={b.id} className="glass-card" style={{ borderLeft: b.nivel_riesgo === 'ALTO' ? '4px solid var(--danger)' : 'none' }}>
              <div className="flex justify-between items-center mb-4">
                <h3 style={{ margin: 0, fontSize: '1.2rem' }}>{b.titulo}</h3>
                <span className={`badge ${b.estado === 'CERRADA' ? 'badge-success' : 'badge-danger'}`}>
                  {b.estado}
                </span>
              </div>
              <p><strong>Nivel de Riesgo:</strong> {b.nivel_riesgo}</p>
              <p><strong>Fecha Descubrimiento:</strong> {new Date(b.fecha_descubrimiento).toLocaleString()}</p>
              <p><strong>Tipo:</strong> {b.tipo_brecha}</p>
              {!b.cumple_plazo_72h && b.estado !== 'CERRADA' && (
                <p style={{ color: 'var(--danger)', fontSize: '0.9rem', marginTop: '16px', fontWeight: 600 }}>
                  ⚠️ Plazo de notificación de 72h excedido
                </p>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
