import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";

import Layout from "./components/Layout";
import LoginPage from "./pages/LoginPage";
import AuthCallbackPage from "./pages/AuthCallbackPage";
import DashboardPage from "./pages/DashboardPage";
import PanelDPOPage from "./pages/PanelDPOPage";
import BrechasPage from "./pages/BrechasPage";
import PortabilidadPage from "./pages/PortabilidadPage";
import TimelineAccesosPage from "./pages/TimelineAccesosPage";
import SolicitudesArcoPage from "./pages/SolicitudesArcoPage";

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "100vh" }}>
        <div className="spinner"></div>
      </div>
    );
  }

  return isAuthenticated ? <>{children}</> : <Navigate to="/login" />;
}

function AppRoutes() {
  const { user } = useAuth();
  const isOrganization = user?.authProvider === "SII";

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/auth/callback" element={<AuthCallbackPage />} />
      
      {/* Protected Routes wrapped in Layout */}
      <Route
        path="/*"
        element={
          <PrivateRoute>
            <Layout>
              <Routes>
                {/* Redirect logic based on role */}
                <Route path="/" element={<Navigate to={isOrganization ? "/panel-dpo" : "/dashboard"} replace />} />
                
                {/* Ciudadano Routes */}
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/timeline" element={<TimelineAccesosPage />} />
                <Route path="/portabilidad" element={<PortabilidadPage />} />
                
                {/* Organizacion Routes */}
                <Route path="/panel-dpo" element={<PanelDPOPage />} />
                <Route path="/brechas" element={<BrechasPage />} />
                <Route path="/rat" element={<div className="animate-fade-in"><h1 className="page-title">Registro RAT</h1><p>Próximamente...</p></div>} />
                <Route path="/eipd" element={<div className="animate-fade-in"><h1 className="page-title">Evaluaciones EIPD</h1><p>Próximamente...</p></div>} />
                
                {/* Shared Routes */}
                <Route path="/solicitudes" element={<SolicitudesArcoPage />} />
                
                {/* Catch all inside Layout */}
                <Route path="*" element={<Navigate to={isOrganization ? "/panel-dpo" : "/dashboard"} replace />} />
              </Routes>
            </Layout>
          </PrivateRoute>
        }
      />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
