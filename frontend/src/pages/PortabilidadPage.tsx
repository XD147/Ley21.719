import { useState } from "react";
import apiClient from "../api";

export default function PortabilidadPage() {
  const [exporting, setExporting] = useState(false);
  const [downloadLink, setDownloadLink] = useState<string | null>(null);

  async function handleExport() {
    setExporting(true);
    try {
      const response = await apiClient.exportarPortabilidad("json");
      const blob = new Blob([JSON.stringify(response.datos || response, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      setDownloadLink(url);
    } catch (err) {
      console.error(err);
      alert("Error exportando datos");
    } finally {
      setExporting(false);
    }
  }

  return (
    <div className="animate-fade-in">
      <div className="page-header">
        <h1 className="page-title">Portabilidad de Datos</h1>
        <p className="page-subtitle">Exporta o importa tus datos personales (Art. 20)</p>
      </div>

      <div className="grid">
        <div className="glass-card">
          <h3 style={{ marginBottom: '16px' }}>Exportar Mis Datos</h3>
          <p style={{ color: 'var(--text-muted)', marginBottom: '24px' }}>
            Descarga una copia completa de todos los datos que esta organización tiene sobre ti en formato estructurado (JSON).
          </p>
          
          <button 
            className="btn-primary" 
            onClick={handleExport} 
            disabled={exporting}
          >
            {exporting ? 'Exportando...' : 'Exportar Datos a JSON'}
          </button>

          {downloadLink && (
            <div style={{ marginTop: '24px', background: 'rgba(16, 185, 129, 0.1)', padding: '16px', borderRadius: '8px' }}>
              <p style={{ color: 'var(--success)', marginBottom: '12px', fontWeight: 500 }}>¡Exportación completada!</p>
              <a href={downloadLink} download="mis_datos_portabilidad.json" className="btn-secondary" style={{ textDecoration: 'none', display: 'inline-block' }}>
                Descargar Archivo JSON
              </a>
            </div>
          )}
        </div>

        <div className="glass-card">
          <h3 style={{ marginBottom: '16px' }}>Importar Datos</h3>
          <p style={{ color: 'var(--text-muted)', marginBottom: '24px' }}>
            Transfiere tus datos desde otra organización a nuestra plataforma de manera segura.
          </p>
          
          <div className="form-group">
            <label className="form-label">ID Organización Origen</label>
            <input type="text" className="form-control" placeholder="Ej: org_123456" />
          </div>
          <div className="form-group">
            <label className="form-label">Archivo de Datos (JSON)</label>
            <input type="file" className="form-control" accept=".json" />
          </div>
          
          <button className="btn-secondary" style={{ marginTop: '16px' }} onClick={() => alert('Funcionalidad de importación en desarrollo')}>
            Iniciar Importación
          </button>
        </div>
      </div>
    </div>
  );
}
