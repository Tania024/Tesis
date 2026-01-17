import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Navbar from './components/Layout/Navbar';
import Footer from './components/Layout/Footer';

// Importar páginas
import Home from './pages/Home';
import Login from './pages/Login';
import AreasPage from './pages/AreasPage';
import GenerarItinerarioPage from './pages/GenerarItinerarioPage';
import MisItinerariosPage from './pages/MisItinerariosPage';
import VerItinerarioPage from './pages/VerItinerarioPage'; 
import VisitaEnProgresoPage from './pages/VisitaEnProgresoPage';
import AdminPage from './pages/AdminPage';

// Componente para rutas protegidas
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useAuth();
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
};

// Layout principal
const Layout = ({ children }) => {
  const { user, logout } = useAuth();
  
  return (
    <div className="flex flex-col min-h-screen">
      <Navbar user={user} onLogout={logout} />
      <main className="flex-grow">
        {children}
      </main>
      <Footer />
    </div>
  );
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <Layout>
          <Routes>
            {/* ============================================ */}
            {/* RUTAS PÚBLICAS */}
            {/* ============================================ */}
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route path="/areas" element={<AreasPage />} />
                        
            {/* ============================================ */}
            {/* RUTAS PROTEGIDAS - ITINERARIOS */}
            {/* ============================================ */}
            
            {/* Generar Itinerario - AMBAS RUTAS FUNCIONAN (compatibilidad) */}
            <Route
              path="/generar"
              element={
                <ProtectedRoute>
                  <GenerarItinerarioPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/generar-itinerario"
              element={
                <ProtectedRoute>
                  <GenerarItinerarioPage />
                </ProtectedRoute>
              }
            />
            
            {/* Mis Itinerarios */}
            <Route
              path="/mis-itinerarios"
              element={
                <ProtectedRoute>
                  <MisItinerariosPage />
                </ProtectedRoute>
              }
            />
            
            {/* Ver Detalle de Itinerario */}
            <Route
              path="/itinerario/:id"
              element={
                <ProtectedRoute>
                  <VerItinerarioPage />
                </ProtectedRoute>
              }
            />
            
            {/* Visita en Progreso con Mapa y Guía */}
            <Route
              path="/visita/:id"
              element={
                <ProtectedRoute>
                  <VisitaEnProgresoPage />
                </ProtectedRoute>
              }
            />
            
            {/* ============================================ */}
            {/* RUTAS PROTEGIDAS - ADMIN */}
            {/* ============================================ */}
            
            {/* Panel de Administración */}
            <Route
              path="/admin"
              element={
                <ProtectedRoute>
                  <AdminPage />
                </ProtectedRoute>
              }
            />
            
            {/* ============================================ */}
            {/* REDIRECCIÓN 404 */}
            {/* ============================================ */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Layout>
      </Router>
    </AuthProvider>
  );
}

export default App;