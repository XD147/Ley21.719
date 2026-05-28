import { useState } from "react";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const [loginType, setLoginType] = useState<"CIUDADANO" | "ORGANIZACION" | null>(null);
  const { loginClaveUnica, loginSii } = useAuth();

  return (
    <div className="app-container" style={{ justifyContent: 'center', alignItems: 'center' }}>
      <div className="glass-card animate-fade-in" style={{ width: '100%', maxWidth: '480px', textAlign: 'center', padding: '40px' }}>
        <div style={{ marginBottom: '32px' }}>
          <h1 className="page-title" style={{ marginBottom: '8px', background: 'linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            Ley 21.719
          </h1>
          <p className="page-subtitle">Sistema de Protección de Datos Personales</p>
        </div>

        {!loginType ? (
          <div className="flex" style={{ flexDirection: 'column', gap: '16px' }}>
            <button 
              className="btn-primary" 
              style={{ padding: '16px', fontSize: '1.1rem' }}
              onClick={() => setLoginType("CIUDADANO")}
            >
              Ingresar como Ciudadano
            </button>
            <button 
              className="btn-secondary" 
              style={{ padding: '16px', fontSize: '1.1rem' }}
              onClick={() => setLoginType("ORGANIZACION")}
            >
              Ingresar como Organización
            </button>
          </div>
        ) : loginType === "CIUDADANO" ? (
          <div className="animate-fade-in flex" style={{ flexDirection: 'column', gap: '24px' }}>
            <div className="glass-panel" style={{ padding: '24px', borderRadius: '12px', background: 'rgba(79, 70, 229, 0.05)' }}>
              <h3 style={{ marginBottom: '8px' }}>Portal Ciudadano</h3>
              <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>Gestiona tus consentimientos y ejerce tus derechos ARCO.</p>
            </div>
            
            <button 
              className="btn-primary" 
              onClick={loginClaveUnica}
              style={{ padding: '16px', fontSize: '1.1rem', background: '#0f172a' }}
            >
              <img
                src="https://www.claveunica.gob.cl/img/logo-claveunica.svg"
                alt="ClaveÚnica"
                style={{ height: '24px', marginRight: '8px', filter: 'brightness(0) invert(1)' }}
              />
              Ingresar con ClaveÚnica
            </button>
            <button className="btn-secondary" onClick={() => setLoginType(null)}>
              ← Volver
            </button>
          </div>
        ) : (
          <div className="animate-fade-in flex" style={{ flexDirection: 'column', gap: '24px' }}>
            <div className="glass-panel" style={{ padding: '24px', borderRadius: '12px', background: 'rgba(14, 165, 233, 0.05)' }}>
              <h3 style={{ marginBottom: '8px' }}>Portal Organizaciones</h3>
              <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>Centro de Cumplimiento DPO y Gestión Normativa.</p>
            </div>

            <div className="form-group" style={{ textAlign: 'left' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem', color: 'var(--text-main)' }}>RUT Organización</label>
              <input 
                type="text" 
                id="rut-org"
                defaultValue="76.123.456-7"
                style={{ 
                  width: '100%', 
                  padding: '12px', 
                  borderRadius: '8px', 
                  border: '1px solid var(--surface-glass-border)',
                  background: 'rgba(255, 255, 255, 0.5)'
                }} 
              />
            </div>

            <button 
              className="btn-primary" 
              onClick={() => {
                const rut = (document.getElementById('rut-org') as HTMLInputElement).value;
                loginSii(rut);
              }}
              style={{ padding: '16px', fontSize: '1.1rem', background: '#0284c7' }}
            >
              <img
                src="https://www.sii.cl/images/logos/sii-logo.svg"
                alt="SII"
                style={{ height: '24px', marginRight: '8px', filter: 'brightness(0) invert(1)' }}
              />
              Ingresar con Clave Tributaria SII
            </button>
            <button className="btn-secondary" onClick={() => setLoginType(null)}>
              ← Volver
            </button>
          </div>
        )}

        <div style={{ marginTop: '40px', paddingTop: '20px', borderTop: '1px solid var(--surface-glass-border)' }}>
          <p style={{ fontSize: '0.8rem', margin: 0, color: 'var(--text-muted)' }}>
            Plataforma Segura GovTech - Chile
          </p>
        </div>
      </div>
    </div>
  );
}
