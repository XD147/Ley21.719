import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import apiClient from '../api';

export default function AuthCallbackPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get('code');
      const state = searchParams.get('state');

      if (!code || !state) {
        alert('Error: Parámetros de autenticación inválidos');
        navigate('/login');
        return;
      }

      try {
        // Determinar el tipo de autenticación por el estado o ruta
        const isSii = state.includes('sii') || window.location.pathname.includes('sii');
        
        let token;
        if (isSii) {
          token = await apiClient.loginSii(code, state);
        } else {
          token = await apiClient.loginClaveUnica(code, state);
        }

        localStorage.setItem('accessToken', token.accessToken);
        localStorage.setItem('refreshToken', token.refreshToken);
        
        navigate('/dashboard');
      } catch (error) {
        console.error('Error en autenticación:', error);
        alert('Error al completar la autenticación');
        navigate('/login');
      }
    };

    handleCallback();
  }, [searchParams, navigate]);

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h2 style={styles.title}>Completando autenticación...</h2>
        <p style={styles.text}>Por favor espera mientras verificamos tu identidad</p>
        <div style={styles.spinner}></div>
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
  },
  card: {
    background: 'white',
    borderRadius: '16px',
    padding: '40px',
    maxWidth: '400px',
    textAlign: 'center',
    boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
  },
  title: {
    fontSize: '24px',
    fontWeight: '600',
    color: '#333',
    marginBottom: '16px',
  },
  text: {
    fontSize: '14px',
    color: '#666',
    marginBottom: '24px',
  },
  spinner: {
    width: '48px',
    height: '48px',
    border: '4px solid #f3f3f3',
    borderTop: '4px solid #667eea',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
    margin: '0 auto',
  },
};
