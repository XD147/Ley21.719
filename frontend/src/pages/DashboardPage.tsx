import { useState, useEffect } from "react";
import apiClient from "../api";
import { AccesoOrganizacion } from "../types";

export default function DashboardPage() {
  const [accesos, setAccesos] = useState<AccesoOrganizacion[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const accesosData = await apiClient.getAccesosUsuario();
      setAccesos(accesosData);
    } catch (error) {
      console.error("Error loading data:", error);
    } finally {
      setLoading(false);
    }
  }

  async function handleRevocarAcceso(id: string) {
    if (!confirm("¿Estás seguro de revocar este acceso?")) return;

    try {
      await apiClient.revocarAcceso(id);
      setAccesos(
        accesos.map((a) =>
          a.id === id ? { ...a, estado: "REVOCADO" as const } : a,
        ),
      );
    } catch (error) {
      console.error("Error revocando acceso:", error);
      alert("Error al revocar el acceso");
    }
  }

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
        <h1 className="page-title">Mis Consentimientos</h1>
        <p className="page-subtitle">Gestiona las autorizaciones que has otorgado a organizaciones</p>
      </div>

      <div className="grid">
        {accesos.length === 0 ? (
          <div className="glass-card" style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '40px' }}>
            <p style={{ color: 'var(--text-muted)' }}>No has otorgado accesos a organizaciones</p>
          </div>
        ) : (
          accesos.map((acceso) => (
            <div key={acceso.id} className="glass-card">
              <div className="flex justify-between items-center mb-4">
                <h3 style={{ margin: 0, fontSize: '1.2rem' }}>{acceso.categoriaDato}</h3>
                <span className={`badge ${acceso.estado === 'ACTIVO' ? 'badge-success' : 'badge-danger'}`}>
                  {acceso.estado}
                </span>
              </div>
              <p><strong>Finalidad:</strong> {acceso.finalidad}</p>
              <p><strong>Otorgado:</strong> {new Date(acceso.fechaOtorgamiento).toLocaleDateString()}</p>
              {acceso.fechaExpiracion && (
                <p><strong>Expira:</strong> {new Date(acceso.fechaExpiracion).toLocaleDateString()}</p>
              )}
              {acceso.estado === "ACTIVO" && (
                <button
                  className="btn-danger mt-4"
                  style={{ width: '100%' }}
                  onClick={() => handleRevocarAcceso(acceso.id)}
                >
                  Revocar Acceso
                </button>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
