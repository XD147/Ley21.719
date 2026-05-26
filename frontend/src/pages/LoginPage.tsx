import { useState } from 'react';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
  const { loginClaveUnica, loginSii } = useAuth();
  const [loginType, setLoginType] = useState<'ciudadano' | 'organizacion' | null>(null);

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.title}>Ley 21.719</h1>
        <h2 style={styles.subtitle}>Sistema de Protección de Datos</h2>
        
        {!loginType ? (
          <div style={styles.options}>
            <button 
              style={styles.buttonPrimary} 
              onClick={() => setLoginType('ciudadano')}
            >
              Soy Ciudadano
            </button>
            <button 
              style={styles.buttonSecondary} 
              onClick={() => setLoginType('organizacion')}
            >
              Soy Organización
            </button>
          </div>
        ) : loginType === 'ciudadano' ? (
          <div style={styles.loginOptions}>
            <h3 style={styles.sectionTitle}>Autenticación para Ciudadanos</h3>
            <p style={styles.description}>
              Ingresa con tu ClaveÚnica del Gobierno de Chile para gestionar tus datos personales
            </p>
            <button 
              style={styles.claveUnicaButton} 
              onClick={loginClaveUnica}
            >
              <img 
                src="https://www.claveunica.gob.cl/img/logo-claveunica.svg" 
                alt="ClaveÚnica" 
                style={styles.logo}
              />
              Ingresar con ClaveÚnica
            </button>
            <button 
              style={styles.backButton} 
              onClick={() => setLoginType(null)}
            >
              ← Volver
            </button>
          </div>
        ) : (
          <div style={styles.loginOptions}>
            <h3 style={styles.sectionTitle}>Autenticación para Organizaciones</h3>
            <p style={styles.description}>
              Ingresa con Clave Tributaria del SII para gestionar los datos de tu organización
            </p>
            <button 
              style={styles.siiButton} 
              onClick={loginSii}
            >
              <img 
                src="https://www.sii.cl/images/logos/sii-logo.svg" 
                alt="SII" 
                style={styles.logo}
              />
              Ingresar con Clave Tributaria SII
            </button>
            <button 
              style={styles.backButton} 
              onClick={() => setLoginType(null)}
            >
              ← Volver
            </button>
          </div>
        )}

        <div style={styles.footer}>
          <p style={styles.legalText}>
            Este sistema cumple con la Ley 21.719 de Protección de Datos Personales de Chile
          </p>
        </div>
      </div>
    </div>
  );
}

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    padding: '20px',
  },
  card: {
    background: 'white',
    borderRadius: '16px',
    padding: '40px',
    maxWidth: '500px',
    width: '100%',
    boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
  },
  title: {
    fontSize: '32px',
    fontWeight: 'bold',
    color: '#333',
    textAlign: 'center',
    marginBottom: '8px',
  },
  subtitle: {
    fontSize: '18px',
    color: '#666',
    textAlign: 'center',
    marginBottom: '32px',
  },
  options: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  buttonPrimary: {
    padding: '16px 32px',
    fontSize: '18px',
    fontWeight: '600',
    color: 'white',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'transform 0.2s',
  },
  buttonSecondary: {
    padding: '16px 32px',
    fontSize: '18px',
    fontWeight: '600',
    color: '#667eea',
    background: '#f0f0ff',
    border: '2px solid #667eea',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'transform 0.2s',
  },
  loginOptions: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '20px',
  },
  sectionTitle: {
    fontSize: '20px',
    fontWeight: '600',
    color: '#333',
    textAlign: 'center',
  },
  description: {
    fontSize: '14px',
    color: '#666',
    textAlign: 'center',
    lineHeight: '1.5',
  },
  claveUnicaButton: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '16px 32px',
    fontSize: '16px',
    fontWeight: '600',
    color: 'white',
    background: '#00b5e2',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    width: '100%',
    justifyContent: 'center',
  },
  siiButton: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '16px 32px',
    fontSize: '16px',
    fontWeight: '600',
    color: 'white',
    background: '#c41230',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    width: '100%',
    justifyContent: 'center',
  },
  logo: {
    height: '24px',
    width: 'auto',
  },
  backButton: {
    padding: '12px 24px',
    fontSize: '14px',
    color: '#666',
    background: 'transparent',
    border: '1px solid #ddd',
    borderRadius: '6px',
    cursor: 'pointer',
  },
  footer: {
    marginTop: '32px',
    paddingTop: '24px',
    borderTop: '1px solid #eee',
  },
  legalText: {
    fontSize: '12px',
    color: '#999',
    textAlign: 'center',
    lineHeight: '1.4',
  },
};
